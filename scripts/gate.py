"""Fail the build if a target is missed. This is the ship gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    data = ROOT / "data" / "accounts.json"
    conv = ROOT / "evals" / "conversations"
    if not data.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_accounts.py")], check=True, cwd=ROOT)
    if not any(conv.glob("*.json")):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_conversations.py")], check=True, cwd=ROOT)
    report = subprocess.run([sys.executable, str(ROOT / "scripts" / "write_report.py")], cwd=ROOT)
    if report.returncode != 0:
        return report.returncode
    tests = subprocess.run(
        [sys.executable, "-m", "pytest", "evals", "-q"],
        cwd=ROOT,
    )
    return tests.returncode


if __name__ == "__main__":
    raise SystemExit(main())
