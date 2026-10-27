#!/usr/bin/env python3
"""Install the Dreamcast skills and their shared reference without overwriting files."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

FOLDERS = ("dreamcast-dev", "dreamcast-asset", "dreamcast-model-check", "dreamcast-texture", "dreamcast-reference")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path, help="destination skills directory")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    target = args.target.expanduser()
    conflicts = [target / name for name in FOLDERS if (target / name).exists() or (target / name).is_symlink()]
    if conflicts:
        parser.exit(1, "Destination already exists; nothing installed:\n" + "\n".join(map(str, conflicts)) + "\n")
    missing = [source / name for name in FOLDERS if not (source / name).is_dir()]
    if missing:
        parser.exit(1, "Source folder missing; nothing installed:\n" + "\n".join(map(str, missing)) + "\n")
    target.mkdir(parents=True, exist_ok=True)
    for name in FOLDERS:
        shutil.copytree(source / name, target / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        print(f"Installed {target / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
