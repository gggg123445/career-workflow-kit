"""Strict, explicit time input shared by records and calendar export."""
from datetime import datetime, timedelta
import re

from .store import WorkflowError

TIME_FIELDS = ("测评时间", "笔试时间", "一面时间", "二面时间", "三面时间")
NON_TIMES = ("待定", "无", "无需", "已完成", "不限时")
PATTERN = re.compile(r"(?P<deadline>截止 )?(?P<date>\d{4}-\d{2}-\d{2}) (?P<start>\d{2}:\d{2})(?:-(?P<end>\d{2}:\d{2}))?")


def parse_cell(value, offset="+08:00"):
    """Return zero or more aware intervals; reject the entire cell on any bad part."""
    if not isinstance(value, str):
        raise WorkflowError("Time cells must be strings")
    if not re.fullmatch(r"[+-](?:0\d|1[0-4]):[0-5]\d", offset) or (offset[1:3] == "14" and offset[-2:] != "00"):
        raise WorkflowError("Timezone must be a fixed ISO offset in -14:00..+14:00")
    if not value.strip():
        return []
    result = []
    for part in re.split(r"[;；]", value):
        part = part.strip()
        if part in NON_TIMES:
            continue
        match = PATTERN.fullmatch(part)
        if not match:
            raise WorkflowError(f"Unsupported time: {part!r}; use YYYY-MM-DD HH:MM[-HH:MM] or 截止 YYYY-MM-DD HH:MM")
        try:
            start = datetime.fromisoformat(match["date"] + "T" + match["start"] + offset)
            if match["deadline"]:
                if match["end"]:
                    raise WorkflowError("Deadline cannot include a range")
                end = start
                start -= timedelta(minutes=30)
            else:
                end = datetime.fromisoformat(match["date"] + "T" + match["end"] + offset) if match["end"] else start + timedelta(hours=1)
                if end <= start:
                    raise WorkflowError("End must be later than start; split overnight intervals explicitly")
        except ValueError as exc:
            raise WorkflowError(f"Invalid date/time: {part}") from exc
        result.append({"start": start, "end": end, "deadline": bool(match["deadline"]), "original": part})
    if len({(v["start"], v["end"], v["deadline"]) for v in result}) != len(result):
        raise WorkflowError("Duplicate intervals in one cell")
    return result
