"""Progressive skill loading and self-contained folder installation."""
from importlib.resources import files
from pathlib import Path
import shutil
import tempfile

from . import __version__
from .stages import STAGES, guide
from .store import WorkflowError


def catalog():
    return {"name": "career-workflow", "version": __version__, "stages": [{"id": name, **spec} for name, spec in STAGES.items()], "loading": "Load SKILL.md first, then only the selected stage reference."}


def load(stage=None):
    if stage:
        return guide(stage)
    return files("careerflow").joinpath("skill/SKILL.md").read_text(encoding="utf-8")


def install(destination):
    """TARGET is the exact new skill folder, never a host-specific implicit path."""
    target = Path(destination).expanduser().resolve()
    if target.exists():
        raise WorkflowError("Skill destination exists; install into a new version folder and switch explicitly")
    source = Path(__file__).parent
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="careerflow-skill-", dir=target.parent) as temp:
        staging = Path(temp) / "career-workflow"
        shutil.copytree(source / "skill", staging, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        # Include the runtime so installation does not depend on this repository or pip.
        shutil.copytree(source, staging / "scripts/_runtime/careerflow", ignore=shutil.ignore_patterns("skill", "__pycache__", "*.pyc"))
        # The runtime reads its selected guides through package resources.
        shutil.copytree(source / "skill", staging / "scripts/_runtime/careerflow/skill", ignore=shutil.ignore_patterns("scripts", "__pycache__", "*.pyc"))
        staging.rename(target)
    return {"path": str(target), "name": "career-workflow", "version": __version__, "runtime_bundled": True, "note": "宿主的技能发现和热重载取决于宿主；安装器不修改其他全局配置。"}
