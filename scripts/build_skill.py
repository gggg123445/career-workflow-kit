"""Build the same self-contained skill directory users get from `skill install`."""
import argparse
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from careerflow.skills import install


def build(output):
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="careerflow-build-") as temp:
        root = Path(temp) / "career-workflow"
        install(root)
        license_file = Path(__file__).resolve().parents[1] / "LICENSE"
        (root / "LICENSE").write_bytes(license_file.read_bytes())
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(root.rglob("*")):
                if file.is_file():
                    info = zipfile.ZipInfo(file.relative_to(root.parent).as_posix(), (2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    archive.writestr(info, file.read_bytes())
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(build(args.output))
