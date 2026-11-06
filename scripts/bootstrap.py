#!/usr/bin/env python3
"""Copy the bundled project to a new workspace. Never merge or overwrite."""
import argparse
from pathlib import Path
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / "assets" / "montage-project"
    target = args.destination.expanduser().resolve()
    if target.exists():
        parser.error("Destination already exists. Choose a new folder; existing projects are not overwritten.")
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("node_modules", ".venv*", ".models", "out", "__pycache__", "*.pyc"))
    print(f"Project copied: {target}")
    print("Next: python scripts/setup.py (from the new project folder)")

if __name__ == "__main__":
    main()
