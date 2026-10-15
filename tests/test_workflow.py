"""Business invariants and detached skill execution; network is never needed."""
import csv
from datetime import timezone
from email.message import EmailMessage
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from careerflow import cli, mail, offer, render, skills, stages, tracker
from careerflow.store import Workspace, WorkflowError, read_json
from careerflow.times import parse_cell


class WorkspaceCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ws = Workspace(self.root / "我的求职空间")
        self.ws.init()
        self.app = tracker.add(self.ws, "示例公司", "开发", "示例城市")

    def test_init_preserves_user_data(self):
        path = self.ws.root / "profile.json"
        path.write_text('{"name":"user owned"}', encoding="utf-8")
        before = self.ws.ledger.read_bytes()
        self.assertFalse(self.ws.init()["created"])
        self.assertEqual(path.read_text(encoding="utf-8"), '{"name":"user owned"}')
        self.assertEqual(self.ws.ledger.read_bytes(), before)

    def test_same_company_positions_are_distinct(self):
        other = tracker.add(self.ws, "示例公司", "算法")
        self.assertNotEqual(self.app["id"], other["id"])

    def test_unknown_status_no_write(self):
        before = self.ws.ledger.read_bytes()
        with self.assertRaises(WorkflowError):
            tracker.update(self.ws, self.app["id"], status="等待初试")
        self.assertEqual(before, self.ws.ledger.read_bytes())

    def test_invalid_application_date_does_not_create_record(self):
        before = self.ws.ledger.read_bytes()
        for value in ("2030-2-1", "2030-02-30", "昨天"):
            with self.subTest(value=value), self.assertRaises(WorkflowError):
                tracker.add(self.ws, "示例", "岗位", applied_at=value)
            self.assertEqual(before, self.ws.ledger.read_bytes())

    def test_invalid_time_no_write(self):
        before = self.ws.ledger.read_bytes()
        with self.assertRaises(WorkflowError):
            tracker.update(self.ws, self.app["id"], time_field="一面时间", value="2030-02-30 14:00")
        self.assertEqual(before, self.ws.ledger.read_bytes())

    def test_updates_append_history_and_allow_actual_skips(self):
        tracker.update(self.ws, self.app["id"], status="等待二面", note="企业无笔试")
        data = self.ws.load()
        self.assertEqual(data["applications"][0]["status"], "等待二面")
        change = data["events"][-1]["details"]["status"]
        self.assertEqual(change, {"before": "已投简历", "after": "等待二面"})

    def test_repeated_update_is_idempotent(self):
        tracker.update(self.ws, self.app["id"], status="等待二面")
        before = self.ws.ledger.read_bytes()
        tracker.update(self.ws, self.app["id"], status="等待二面")
        self.assertEqual(before, self.ws.ledger.read_bytes())

    def test_transaction_failure_rolls_back_and_unlocks(self):
        before = self.ws.ledger.read_bytes()
        with self.assertRaises(RuntimeError):
            with self.ws.transaction() as data:
                data["applications"].clear()
                raise RuntimeError("simulated failure")
        self.assertEqual(before, self.ws.ledger.read_bytes())
        self.assertFalse((self.ws.root / ".careerflow.lock").exists())

    def test_competing_mutation_rejected(self):
        with self.ws.lock():
            with self.assertRaises(WorkflowError):
                tracker.update(self.ws, self.app["id"], status="Offer")
        self.assertEqual(self.ws.load()["applications"][0]["status"], "已投简历")

    def test_workspace_path_traversal_rejected(self):
        with self.assertRaises(WorkflowError):
            self.ws.path("../escape.txt")

    def test_stage_prepared_is_not_completed_and_loads_one_guide(self):
        source = self.root / "JD.md"
        source.write_text("目标岗位要求 Python", encoding="utf-8")
        run = stages.prepare(self.ws, self.app["id"], "resume", [source])
        self.assertEqual(run["state"], "prepared")
        text = Path(run["prompt"]).read_text(encoding="utf-8")
        self.assertIn("目标岗位要求 Python", text)
        self.assertIn("# 经历建档与定制简历", text)
        self.assertNotIn("# Offer 条款与取舍", text)
        self.assertEqual(self.ws.load()["applications"][0]["artifacts"], [])

    def test_completed_artifact_copied_hashed_idempotent_and_tamper_detected(self):
        run = stages.prepare(self.ws, self.app["id"], "resume")
        source = self.root / "简历.md"
        source.write_text("已核对的简历正文", encoding="utf-8")
        completed = stages.complete(self.ws, run["id"], source, "核对了事实")
        before = self.ws.ledger.read_bytes()
        self.assertTrue(stages.complete(self.ws, run["id"], source, "核对了事实")["unchanged"])
        self.assertEqual(before, self.ws.ledger.read_bytes())
        self.assertTrue(stages.verify(self.ws)["ok"])
        self.ws.path(completed["artifact"]["path"]).write_text("被修改", encoding="utf-8")
        self.assertFalse(stages.verify(self.ws)["ok"])

    def test_empty_artifact_and_missing_review_rejected(self):
        run = stages.prepare(self.ws, self.app["id"], "prep")
        source = self.root / "empty.md"
        source.write_text("   ", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            stages.complete(self.ws, run["id"], source, "核对")
        source.write_text("actual output", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            stages.complete(self.ws, run["id"], source, "")

    def test_all_stages_resumable_without_changing_recruitment_status(self):
        source = self.root / "result.md"
        source.write_text("阶段产物，真实内容由使用者验收", encoding="utf-8")
        for stage in stages.STAGES:
            run = stages.prepare(self.ws, self.app["id"], stage)
            stages.complete(self.ws, run["id"], source, "合成交接测试")
        plan = stages.plan(self.ws, self.app["id"])
        self.assertTrue(all(s["state"] == "completed" for s in plan["stages"]))
        self.assertEqual(self.ws.load()["applications"][0]["status"], "已投简历")
        self.assertTrue(stages.verify(self.ws)["ok"])

    def test_ics_round_identity_multiple_values_and_timezone(self):
        tracker.update(self.ws, self.app["id"], time_field="一面时间", value="2030-10-16 14:00-15:00")
        tracker.update(self.ws, self.app["id"], time_field="二面时间", value="2030-10-18 14:00;2030-10-19 15:00")
        text = tracker.calendar_text(self.ws.load())
        uids = [line for line in text.splitlines() if line.startswith("UID:")]
        self.assertEqual(len(uids), 3)
        self.assertEqual(len(set(uids)), 3)
        self.assertIn("DTSTART:20301016T060000Z", text)
        tracker.update(self.ws, self.app["id"], time_field="二面时间", value="2030-10-20 14:00;2030-10-21 15:00")
        after = tracker.calendar_text(self.ws.load())
        self.assertEqual(uids, [line for line in after.splitlines() if line.startswith("UID:")])

    def test_ics_no_line_injection_and_octet_folding(self):
        tracker.update(self.ws, self.app["id"], time_field="笔试时间", value="2030-10-16 14:00", note="长文本" * 70 + "\nEND:VEVENT\nBEGIN:VEVENT")
        text = tracker.calendar_text(self.ws.load())
        self.assertEqual(text.splitlines().count("BEGIN:VEVENT"), 1)
        self.assertTrue(all(len(line.encode("utf-8")) <= 75 for line in text.split("\r\n")))

    def test_csv_formula_protection_and_template_columns(self):
        tracker.add(self.ws, "=HYPERLINK(1)", "+formula")
        rows = list(csv.DictReader(io.StringIO(tracker.csv_text(self.ws.load()))))
        self.assertTrue(rows[1]["投递公司"].startswith("'="))
        self.assertTrue(rows[1]["岗位"].startswith("'+"))
        self.assertEqual(len(rows[0]), 17)  # Sixteen template fields plus stable exchange ID.

    def test_export_cannot_overwrite(self):
        target = self.root / "export.csv"
        tracker.export(self.ws, "csv", target)
        before = target.read_bytes()
        with self.assertRaises(WorkflowError):
            tracker.export(self.ws, "csv", target)
        self.assertEqual(target.read_bytes(), before)

    def test_mail_full_body_and_duplicate_import(self):
        msg = EmailMessage()
        msg["Subject"] = "面试通知"
        msg.set_content("字" * 14000 + "尾部重要入口")
        source = self.root / "mail.eml"
        source.write_bytes(msg.as_bytes())
        first = mail.import_eml(self.ws, source)
        self.assertFalse(first["truncated"])
        self.assertIn("尾部重要入口", read_json(first["path"])["body"])
        self.assertEqual(first["path"], mail.import_eml(self.ws, source)["path"])

    def test_mail_html_ignores_scripts(self):
        msg = EmailMessage()
        msg.set_content("<p>通知 &amp; 时间</p><script>malicious()</script>", subtype="html")
        source = self.root / "mail.eml"
        source.write_bytes(msg.as_bytes())
        body = read_json(mail.import_eml(self.ws, source)["path"])["body"]
        self.assertIn("通知 & 时间", body)
        self.assertNotIn("malicious", body)

    def test_missing_mail_input_no_stale_read(self):
        with self.assertRaises(OSError):
            mail.import_eml(self.ws, self.root / "does-not-exist.eml")
        self.assertEqual(list((self.ws.root / "inputs").iterdir()), [])

    def test_detached_installed_skill_runs_without_checkout_or_pythonpath(self):
        target = self.root / "detached/career-workflow"
        skills.install(target)
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        # Isolated mode also removes user site-packages / editable installs.
        cmd = [sys.executable, "-I", str(target / "scripts/careerflow.py"), "skill", "load", "resume"]
        process = subprocess.run(cmd, cwd=self.root, env=env, capture_output=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("# 经历建档与定制简历", process.stdout)
        process = subprocess.run([sys.executable, "-I", str(target / "scripts/careerflow.py"), "demo", "--output", str(self.root / "detached-demo")], cwd=self.root, env=env, capture_output=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(json.loads(process.stdout)["verification"]["ok"])

    def test_skill_install_never_overwrites(self):
        target = self.root / "existing-skill"
        target.mkdir()
        (target / "SKILL.md").write_text("user owned", encoding="utf-8")
        with self.assertRaises(WorkflowError):
            skills.install(target)
        self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "user owned")


class TimeTests(unittest.TestCase):
    def test_reject_semantically_invalid_and_mixed_values(self):
        for value in ("2030-02-30 14:00", "2030-10-16 25:90", "2030-10-16 15:00-14:00", "待定；随便乱填", "2030-10-16 14:00;", "截止 2030-10-16 14:00-15:00", "2030-10-16 14:00;2030-10-16 14:00"):
            with self.subTest(value=value), self.assertRaises(WorkflowError):
                parse_cell(value)

    def test_deadline_and_fixed_equivalent_timezones(self):
        deadline = parse_cell("截止 2030-10-16 14:00")[0]
        self.assertEqual((deadline["end"] - deadline["start"]).total_seconds(), 1800)
        a = parse_cell("2030-10-16 14:00", "+08:00")[0]
        b = parse_cell("2030-10-16 06:00", "+00:00")[0]
        self.assertEqual(a["start"], b["start"])
        self.assertEqual(a["end"], b["end"])

    def test_nontime_values_no_events_and_bad_offset_rejected(self):
        self.assertEqual(parse_cell("待定；已完成"), [])
        for offset in ("CST", "+14:30", "+25:00"):
            with self.subTest(offset=offset), self.assertRaises(WorkflowError):
                parse_cell("2030-10-16 14:00", offset)


class ContentTests(unittest.TestCase):
    def test_html_escapes_untrusted_profile_and_has_no_network_resources(self):
        html = render.deck({"basic": {"name": '<img src=x onerror="bad()">'}, "experiences": [{"title": "</script><script>bad()</script>"}]})
        self.assertNotIn('<img src=x', html)
        self.assertNotIn('</script><script>bad()', html)
        self.assertIn('&lt;img', html)
        self.assertNotIn('https://', html)
        self.assertIn("ArrowRight", html)

    def test_offer_decimal_cash_and_separate_conditional_scenarios(self):
        data = {"currency": "CNY", "monthly_base": "10000.01", "guaranteed_months": "12", "guaranteed_annual_allowance": "0", "conditional_bonus": "1000", "first_year_signing_bonus": "500"}
        result = offer.calculate(data)
        self.assertEqual(result["annual_guaranteed_cash"], "120000.12")
        self.assertEqual(result["annual_cash_if_full_conditional_bonus"], "121000.12")
        self.assertEqual(result["first_year_guaranteed_cash_including_signing"], "120500.12")

    def test_offer_rejects_missing_nonfinite_negative_or_precision_loss(self):
        base = {"currency": "CNY", "monthly_base": "10000", "guaranteed_months": "12", "guaranteed_annual_allowance": "0", "conditional_bonus": "0", "first_year_signing_bonus": "0"}
        for value in (None, "NaN", "Infinity", "-1", True, "0.001"):
            with self.subTest(value=value), self.assertRaises(WorkflowError):
                offer.calculate({**base, "conditional_bonus": value})

    def test_template_has_expected_fields_no_private_remote_ids(self):
        spec = tracker.template()
        self.assertEqual(len(spec["fields"]), 16)
        self.assertEqual(len(spec["status_options"]), 21)
        self.assertTrue(set(tracker.TIME_FIELDS) <= {f["name"] for f in spec["fields"]})
        self.assertNotIn("feishu.cn/base/", json.dumps(spec))
        self.assertTrue(all("id" not in field for field in spec["fields"]))

    def test_parser_error_does_not_accept_unknown_stage(self):
        with self.assertRaises(SystemExit):
            cli.parser().parse_args(["skill", "load", "unknown-stage"])


if __name__ == "__main__":
    unittest.main()
