#!/usr/bin/env python3
"""Skill launcher: bundled runtime first, checkout runtime second, installed package last."""
from pathlib import Path
import sys

location = Path(__file__).resolve()
for candidate in (location.parent / "_runtime", location.parents[3]):
    if (candidate / "careerflow/__init__.py").is_file():
        sys.path.insert(0, str(candidate))
        break

from careerflow.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
