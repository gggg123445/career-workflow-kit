"""Local canonical ledger and explicit, lossless template interchange."""
import csv
from datetime import datetime, timezone
from importlib.resources import files
import io
import json
from pathlib import Path
import re

from .store import WorkflowError, identifier, now
from .times import TIME_FIELDS, parse_cell


def template():
    return json.loads(files("careerflow").joinpath("resources/campus-tracker.json").read_text(encoding="utf-8"))


def add(ws, company, position, city="", status="已投简历", applied_at=""):
    if not company.strip() or not position.strip():
        raise WorkflowError("Company and position must be nonempty")
    if status not in template()["status_options"]:
        raise WorkflowError("Unknown status; inspect careerflow template")
    if applied_at:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", applied_at):
            raise WorkflowError("Applied date must be YYYY-MM-DD")
        try:
            datetime.strptime(applied_at, "%Y-%m-%d")
        except ValueError as exc:
            raise WorkflowError("Applied date must be YYYY-MM-DD") from exc
    with ws.transaction() as data:
        app = {"id": identifier("app"), "company": company.strip(), "position": position.strip(), "city": city.strip(), "status": status, "applied_at": applied_at, "times": {}, "notes": "", "url": "", "email_summary": "", "ai_status": "", "salary_notes": "", "parent_id": "", "artifacts": [], "created_at": now()}
        data["applications"].append(app)
        ws.event(data, app["id"], "created", {"status": status})
    return app


def update(ws, app_id, status=None, time_field=None, value=None, offset="+08:00", note=None):
    if status is not None and status not in template()["status_options"]:
        raise WorkflowError("Unknown template status")
    if time_field is not None:
        if time_field not in TIME_FIELDS:
            raise WorkflowError("Unknown time field")
        parse_cell(value, offset)
    if status is None and time_field is None and note is None:
        raise WorkflowError("Empty update")
    with ws.transaction() as data:
        app = ws.application(data, app_id)
        changes = {}
        if status is not None and status != app["status"]:
            changes["status"] = {"before": app["status"], "after": status}
            app["status"] = status
        if time_field is not None:
            before = app["times"].get(time_field)
            after = {"value": value, "offset": offset}
            if before != after:
                changes[time_field] = {"before": before, "after": after}
                app["times"][time_field] = after
        if note and note.strip():
            app["notes"] = (app["notes"] + "\n" + note.strip()).strip()
            changes["note_appended"] = note.strip()
        if changes:
            ws.event(data, app_id, "updated", changes)
    return app


def csv_text(data):
    fields = template()["fields"]
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=["application_id"] + [f["name"] for f in fields])
    writer.writeheader()
    for app in data["applications"]:
        row = {"application_id": app["id"], "投递公司": app["company"], "岗位": app["position"], "城市": app["city"], "投递状态": app["status"], "投递时间": app["applied_at"], "备注": app["notes"], "网址链接": app["url"], "邮件总结要点": app["email_summary"], "AI状态判断": app["ai_status"], "薪资情况": app["salary_notes"], "父记录": app["parent_id"]}
        row.update({name: app["times"].get(name, {}).get("value", "") for name in TIME_FIELDS})
        # Spreadsheet formula injection protection at this output boundary.
        writer.writerow({k: "'" + str(v) if str(v).lstrip().startswith(("=", "+", "-", "@")) else v for k, v in row.items()})
    return out.getvalue()


def escape_ics(value):
    return str(value).replace("\\", "\\\\").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")


def fold_ics(line):
    result, part = [], ""
    for char in line:
        if len((part + char).encode("utf-8")) > 75:
            result.append(part)
            part = " "
        part += char
    return "\r\n".join(result + [part])


def calendar_text(data):
    """One stable UID per application/round/slot, never company-title matching."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//career-workflow-kit//CareerFlow//EN", "CALSCALE:GREGORIAN"]
    for app in data["applications"]:
        for field in TIME_FIELDS:
            cell = app["times"].get(field)
            if not cell:
                continue
            for index, interval in enumerate(parse_cell(cell["value"], cell["offset"])):
                # Slot order is identity within a multi-value cell; do not reorder it when rescheduling.
                uid = f"{app['id']}-{TIME_FIELDS.index(field)}-{index}@career-workflow-kit"
                title = f"{app['company']} · {app['position']} · {field.removesuffix('时间')}" + ("截止" if interval["deadline"] else "")
                utc = lambda dt: dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                lines.extend(["BEGIN:VEVENT", "UID:" + uid, "DTSTAMP:" + stamp, f"SEQUENCE:{data['revision']}", "DTSTART:" + utc(interval["start"]), "DTEND:" + utc(interval["end"]), "SUMMARY:" + escape_ics(title), "DESCRIPTION:" + escape_ics(app["notes"] + "\n" + app["url"]), "BEGIN:VALARM", "TRIGGER:-PT30M", "ACTION:DISPLAY", "DESCRIPTION:Career event reminder", "END:VALARM", "END:VEVENT"])
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold_ics(line) for line in lines) + "\r\n"


def stats(data):
    statuses, cities = {}, {}
    for app in data["applications"]:
        statuses[app["status"]] = statuses.get(app["status"], 0) + 1
        city = app["city"] or "未填写"
        cities[city] = cities.get(city, 0) + 1
    return {"total": len(data["applications"]), "by_status": statuses, "by_city": cities, "small_sample": len(data["applications"]) < 10, "note": "描述性统计；不从当前状态推断历史漏斗或成功概率。"}


def export(ws, kind, destination):
    data = ws.load()
    path = Path(destination).expanduser().resolve()
    if path.exists():
        raise WorkflowError("Export target already exists; choose a new path")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = csv_text(data) if kind == "csv" else calendar_text(data)
    with path.open("x", encoding="utf-8-sig" if kind == "csv" else "utf-8", newline="") as stream:
        stream.write(text)
    return {"path": str(path), "format": kind}
