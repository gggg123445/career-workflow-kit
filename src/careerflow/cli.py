"""All CLI commands are local; no vendor account or network is required."""
import argparse
import json
from pathlib import Path
import sys

from . import __version__, mail, offer, render, skills, stages, tracker
from .store import Workspace, WorkflowError, atomic_json


def parser():
    root = argparse.ArgumentParser(prog="careerflow", description="Local-first career workflow / 本地优先求职工作流")
    root.add_argument("--version", action="version", version=__version__)
    root.add_argument("--workspace", default="workspace", help="Workspace directory (default: ./workspace); put before subcommand")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Create empty workspace; never overwrite existing data")
    commands.add_parser("template", help="Print portable campus-tracker schema")
    add = commands.add_parser("add", help="Create an application with a stable ID")
    add.add_argument("--company", required=True)
    add.add_argument("--position", required=True)
    add.add_argument("--city", default="")
    add.add_argument("--status", default="已投简历")
    add.add_argument("--applied-at", default="")
    commands.add_parser("list", help="List applications")
    update = commands.add_parser("update", help="Append an explicit, validated ledger update")
    update.add_argument("application")
    update.add_argument("--status")
    update.add_argument("--time-field", choices=tracker.TIME_FIELDS)
    update.add_argument("--value")
    update.add_argument("--offset", default="+08:00", help="ISO offset; for negative values use --offset=-05:00")
    update.add_argument("--note")
    commands.add_parser("stats", help="Descriptive distributions; no inferred funnel")
    commands.add_parser("verify", help="Check artifact references and hashes")
    plan = commands.add_parser("plan", help="Inspect the seven-stage workflow for one application")
    plan.add_argument("application")
    export = commands.add_parser("export", help="Write CSV or ICS without touching external services")
    export.add_argument("kind", choices=("csv", "ics"))
    export.add_argument("--output", required=True)
    stage = commands.add_parser("stage", help="Prepare and complete resumable task packets")
    sub = stage.add_subparsers(dest="action", required=True)
    sub.add_parser("list")
    prepare = sub.add_parser("prepare")
    prepare.add_argument("stage", choices=stages.STAGES)
    prepare.add_argument("--application", required=True)
    prepare.add_argument("--input", action="append", default=[], help="UTF-8 text/Markdown/JSON input; repeatable")
    complete = sub.add_parser("complete")
    complete.add_argument("run")
    complete.add_argument("--artifact", required=True)
    complete.add_argument("--note", required=True)
    skill = commands.add_parser("skill", help="Discover, progressively load or install the portable skill")
    sub = skill.add_subparsers(dest="action", required=True)
    sub.add_parser("catalog")
    load = sub.add_parser("load")
    load.add_argument("stage", nargs="?", choices=stages.STAGES)
    install = sub.add_parser("install")
    install.add_argument("--target", required=True, help="Exact NEW skill directory")
    ren = commands.add_parser("render", help="Render factual drafts; no invented tailoring or scoring")
    ren.add_argument("kind", choices=("resume", "intro"))
    ren.add_argument("--output", required=True)
    eml = commands.add_parser("mail-import", help="Import a local .eml, preserving full body")
    eml.add_argument("file")
    calc = commands.add_parser("offer-calc", help="Calculate only explicit pre-tax cash scenarios")
    calc.add_argument("file", help="JSON: currency, monthly_base, guaranteed_months, guaranteed_annual_allowance, conditional_bonus, first_year_signing_bonus (all amounts required, zero explicit)")
    demo = commands.add_parser("demo", help="Create and exercise a synthetic workflow, no network")
    demo.add_argument("--output", required=True, help="Exact NEW demo workspace")
    return root


def demo(destination):
    path = Path(destination).expanduser().resolve()
    if path.exists():
        raise WorkflowError("Demo destination must not exist")
    ws = Workspace(path)
    ws.init()
    profile = {"schema_version": "1.0", "basic": {"name": "示例候选人"}, "headline": "以下全部为虚构演示材料", "education": [], "skills": ["Python", "SQL"], "experiences": [{"id": "demo-project", "title": "示例数据整理工具", "actions": ["实现 CSV 校验和本地报表"], "results": ["功能性结果：支持错误行定位；未提供性能指标"]}]}
    atomic_json(ws.root / "profile.json", profile)
    app = tracker.add(ws, "示例科技（虚构）", "软件工程师", "示例城市")
    source = ws.root / "inputs/demo.md"
    source.write_text("虚构演示。JD：Python、SQL；一面待安排。\n面试回忆：Q 为什么采用 CSV？A 数据规模小，便于人工检查。\nOffer：月薪与奖金待补，不作薪资结论。\n", encoding="utf-8")
    for stage in stages.STAGES:
        run = stages.prepare(ws, app["id"], stage, [source])
        artifact = ws.root / "inputs" / (stage + "-demo.md")
        artifact.write_text("# " + stages.STAGES[stage]["title"] + " · 演示交接\n\n仅验证任务准备、产物登记和关联流程。未执行真实研究、生成或专业评价。\n\n业务完成标准：" + stages.STAGES[stage]["output"] + "。当前均待真实输入及内容验收。\n", encoding="utf-8")
        stages.complete(ws, run["id"], artifact, "合成材料；仅验收流程交接，不代表该业务阶段已完成")
    tracker.update(ws, app["id"], time_field="一面时间", value="2030-10-16 14:00-15:00")
    tracker.update(ws, app["id"], time_field="二面时间", value="2030-10-18 14:00;2030-10-19 15:00")
    tracker.export(ws, "csv", ws.root / "exports/applications.csv")
    tracker.export(ws, "ics", ws.root / "exports/calendar.ics")
    render.render(ws, "resume", ws.root / "exports/resume.md")
    render.render(ws, "intro", ws.root / "exports/intro.html")
    return {"workspace": str(ws.root), "application_id": app["id"], "verification": stages.verify(ws), "synthetic": True, "note": "七阶段任务交接的冒烟测试，不是七项内容生成质量验收。"}


def dispatch(args):
    ws = Workspace(args.workspace)
    if args.command == "init":
        return ws.init()
    if args.command == "template":
        return tracker.template()
    if args.command == "add":
        return tracker.add(ws, args.company, args.position, args.city, args.status, args.applied_at)
    if args.command == "list":
        return ws.load()["applications"]
    if args.command == "update":
        return tracker.update(ws, args.application, args.status, args.time_field, args.value, args.offset, args.note)
    if args.command == "stats":
        return tracker.stats(ws.load())
    if args.command == "verify":
        return stages.verify(ws)
    if args.command == "plan":
        return stages.plan(ws, args.application)
    if args.command == "export":
        return tracker.export(ws, args.kind, args.output)
    if args.command == "stage":
        if args.action == "list":
            return stages.STAGES
        if args.action == "prepare":
            return stages.prepare(ws, args.application, args.stage, args.input)
        return stages.complete(ws, args.run, args.artifact, args.note)
    if args.command == "skill":
        if args.action == "catalog":
            return skills.catalog()
        if args.action == "load":
            return skills.load(args.stage)
        return skills.install(args.target)
    if args.command == "render":
        return render.render(ws, args.kind, args.output)
    if args.command == "mail-import":
        return mail.import_eml(ws, args.file)
    if args.command == "offer-calc":
        return offer.from_file(args.file)
    if args.command == "demo":
        return demo(args.output)
    raise WorkflowError("Unknown command")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    try:
        result = dispatch(args)
        if isinstance(result, str):
            print(result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 1 if isinstance(result, dict) and result.get("ok") is False else 0
    except (WorkflowError, OSError, UnicodeError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
