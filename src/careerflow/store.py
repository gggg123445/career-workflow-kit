"""Local storage with exclusive mutation locks and atomic ledger replacement."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid


class WorkflowError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def identifier(prefix):
    return prefix + "-" + uuid.uuid4().hex[:16]


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read JSON: {path}: {exc}") from exc


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Workspace:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.ledger = self.root / "applications.json"

    def load(self):
        data = read_json(self.ledger)
        if not isinstance(data, dict) or data.get("schema_version") != "1.0":
            raise WorkflowError("Unsupported workspace schema; initialize a new workspace or migrate explicitly")
        for key in ("applications", "runs", "events"):
            if not isinstance(data.get(key), list):
                raise WorkflowError(f"Invalid ledger collection: {key}")
        return data

    @contextmanager
    def lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / ".careerflow.lock"
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise WorkflowError("Workspace locked. If an earlier process crashed, verify it stopped before removing .careerflow.lock") from exc
        try:
            with os.fdopen(fd, "w", encoding="ascii") as stream:
                stream.write(str(os.getpid()))
            yield
        finally:
            path.unlink(missing_ok=True)

    @contextmanager
    def transaction(self):
        with self.lock():
            data = self.load()
            original = deepcopy(data)
            yield data
            if data != original:
                data["revision"] += 1
                atomic_json(self.ledger, data)

    def init(self):
        with self.lock():
            if self.ledger.exists():
                self.load()
                return {"workspace": str(self.root), "created": False}
            for directory in ("inputs", "runs", "artifacts", "exports"):
                (self.root / directory).mkdir(exist_ok=True)
            defaults = {
                "profile.json": {"schema_version": "1.0", "basic": {"name": "", "email": ""}, "headline": "", "education": [], "experiences": [], "skills": [], "publications": []},
                "targets.json": {"schema_version": "1.0", "cities": [], "job_families": [], "constraints": [], "decision_weights": {}},
            }
            for filename, data in defaults.items():
                if not (self.root / filename).exists():
                    atomic_json(self.root / filename, data)
            atomic_json(self.ledger, {"schema_version": "1.0", "revision": 0, "applications": [], "runs": [], "events": []})
            # Ignore everything by default if a workspace is created within any Git repository.
            if not (self.root / ".gitignore").exists():
                (self.root / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
        return {"workspace": str(self.root), "created": True}

    def path(self, relative):
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root):
            raise WorkflowError("Workspace path escapes root")
        return target

    @staticmethod
    def application(data, app_id):
        for app in data["applications"]:
            if app["id"] == app_id:
                return app
        raise WorkflowError(f"Unknown application: {app_id}")

    @staticmethod
    def run(data, run_id):
        for run in data["runs"]:
            if run["id"] == run_id:
                return run
        raise WorkflowError(f"Unknown run: {run_id}")

    @staticmethod
    def event(data, app_id, kind, details):
        data["events"].append({"id": identifier("evt"), "application_id": app_id, "at": now(), "kind": kind, "details": details})
