#!/usr/bin/env python3
"""Prepare a separate student project, install the skill, then install dependencies."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", type=Path, required=True)
    p.add_argument("--agent", choices=("codex", "claude-code"), default="codex")
    p.add_argument("--prepare-only", action="store_true",
                   help="Copy files only; do not claim dependencies are ready.")
    args = p.parse_args()
    project = args.project.expanduser().resolve()
    marker = project / ".montage-install.json"
    if project == ROOT or ROOT in project.parents:
        p.error("Choose a working folder outside the downloaded skill.")
    state = {"schema": 1, "agent": args.agent, "status": "prepared"}
    if project.exists():
        if not marker.is_file():
            p.error("Existing unrelated folder: choose a new project name. Nothing overwritten.")
        state = json.loads(marker.read_text(encoding="utf-8"))
        if state.get("schema") != 1 or state.get("agent") != args.agent:
            p.error("This folder belongs to another installation. Nothing overwritten.")
    else:
        subprocess.run([sys.executable, str(ROOT / "scripts/bootstrap.py"), str(project)], check=True)
        marker.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    folder = ".agents" if args.agent == "codex" else ".claude"
    installed = project / folder / "skills/reels-montage-pro/SKILL.md"
    if not installed.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts/install.py"),
                        "--project", str(project), "--agent", args.agent], check=True)
    if args.prepare_only:
        print(f"PREPARED (dependencies not checked): {project}")
        return
    subprocess.run([sys.executable, str(project / "scripts/setup.py"), "--check"], check=True)
    subprocess.run([sys.executable, str(project / "scripts/setup.py")], check=True)
    state["status"] = "ready"
    marker.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"READY: {project}\nRead {installed} and continue in this project.")
    print("If no video is provided, ask: Пришлите исходный ролик — смонтирую в стиле «Монтаж ТОП».")


if __name__ == "__main__":
    main()
