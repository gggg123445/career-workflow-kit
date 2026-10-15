"""Offline .eml import: preserve full decoded body, never touch a mailbox."""
from email import policy
from email.parser import BytesParser
import hashlib
from html.parser import HTMLParser
from pathlib import Path

from .store import WorkflowError, atomic_json, now


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("br", "p", "div", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def import_eml(ws, filename):
    ws.load()
    raw = Path(filename).read_bytes()
    if len(raw) > 25_000_000:
        raise WorkflowError("EML exceeds 25 MB; provide the relevant message separately")
    message = BytesParser(policy=policy.default).parsebytes(raw)
    part = message.get_body(preferencelist=("plain", "html"))
    if part is None:
        raise WorkflowError("No readable text body in EML")
    body = part.get_content()
    if not isinstance(body, str):
        raise WorkflowError("Body is not text")
    if part.get_content_type() == "text/html":
        parser = TextOnly()
        parser.feed(body)
        body = "".join(parser.parts)
    sha = hashlib.sha256(raw).hexdigest()
    path = ws.path("inputs/mail-" + sha + ".json")
    if not path.exists():
        atomic_json(path, {"schema_version": "1.0", "sha256": sha, "imported_at": now(), "subject": str(message.get("subject", "")), "from": str(message.get("from", "")), "date": str(message.get("date", "")), "body": body, "truncated": False, "source": "local_eml"})
    return {"path": str(path), "sha256": sha, "body_characters": len(body), "truncated": False, "note": "仅导入本地文件；未推断公司、轮次、状态或更新任何台账。"}
