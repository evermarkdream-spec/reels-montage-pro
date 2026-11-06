#!/usr/bin/env python3
"""Install dependencies in this student project; --check only reports prerequisites."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    missing = [tool for tool in ("node", "npm", "ffmpeg", "ffprobe") if not shutil.which(tool)]
    if sys.version_info < (3, 11):
        missing.append("Python 3.11+")
    if missing:
        parser.error("Install prerequisites first: " + ", ".join(missing))
    if args.check:
        print("Prerequisites found. No files changed.")
        return
    python = ROOT / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(ROOT / ".venv")
    commands = [
        [sys.executable, "-c", "print('Preparing student project')"],
        [shutil.which("npm"), "ci"],
        [str(python), "-m", "pip", "install", "-r", "requirements.txt"],
        [shutil.which("node"), "scripts/ensure-generated.cjs"],
    ]
    for command in commands:
        if sys.platform == "win32" and str(command[0]).lower().endswith(".cmd"):
            command = ["cmd", "/c", *command]
        subprocess.run(command, cwd=ROOT, check=True)
    print("READY. Import: .venv/bin/python scripts/import-video.py /path/to/video.mp4")
    print("On Windows use .venv\\Scripts\\python.exe. Studio: npm run dev")

if __name__ == "__main__":
    main()
