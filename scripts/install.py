#!/usr/bin/env python3
"""Install the complete local skill in one project. Never overwrite an installation."""
import argparse
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ("SKILL.md", "STUDENT_GUIDE.md", "START_HERE.html", "CREDITS.md")
DIRECTORIES = ("agents", "assets", "references", "scripts")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--agent", required=True, choices=("codex", "claude-code"))
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    if not project.is_dir():
        parser.error("Project folder must already exist; create or bootstrap it first.")
    folder = ".agents" if args.agent == "codex" else ".claude"
    target = project / folder / "skills" / "reels-montage-pro"
    if target.exists() or target.is_symlink():
        parser.error(f"Already installed at {target}. Existing files were not changed.")
    for name in FILES + DIRECTORIES:
        if not (ROOT / name).exists():
            parser.error(f"Incomplete download: missing {name}. Download the entire repository.")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".montage-install-", dir=target.parent))
    try:
        for name in FILES:
            shutil.copy2(ROOT / name, staging / name)
        for name in DIRECTORIES:
            shutil.copytree(ROOT / name, staging / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    print(f"Installed complete skill: {target}")
    print("Read SKILL.md now. If the skill menu has not refreshed, reopen the project/chat.")


if __name__ == "__main__":
    main()
