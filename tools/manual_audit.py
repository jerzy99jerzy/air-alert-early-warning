#!/usr/bin/env python3
"""Manual audit: the operator's manual may not drift from the code.

A manual that falls behind is worse than no manual, because it is believed.
Moved out of the general domain lint into its own tool so it can be a separate
CI job, matching `pirx/tools/manual_audit.py`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUAL = ROOT / "docs" / "MANUAL.md"
MARKERS = ("BUILT", "PARTIAL", "NOT BUILT", "NARRATIVE")


def check_every_command_documented() -> list[str]:
    """Every CLI subcommand has a section."""
    sys.path.insert(0, str(ROOT))
    from mavo.cli import build_parser

    text = MANUAL.read_text(encoding="utf-8")
    commands = sorted(
        {
            name
            for choices in (getattr(action, "choices", None) for action in build_parser()._actions)
            if isinstance(choices, dict)
            for name in choices
        }
    )
    return [f"`mavo {name}` has no section in docs/MANUAL.md" for name in commands
            if f"`mavo {name}`" not in text]


def check_sections_declare_a_kind() -> list[str]:
    """Every numbered section says whether it describes present behaviour."""
    problems: list[str] = []
    for line in MANUAL.read_text(encoding="utf-8").splitlines():
        if re.match(r"^#{2,3} \d", line) and not any(marker in line for marker in MARKERS):
            problems.append(f"section without a status marker: {line.strip()}")
    return problems


def check_gate_thresholds_match_the_code() -> list[str]:
    """Thresholds quoted in the manual are the ones the code enforces."""
    sys.path.insert(0, str(ROOT))
    from mavo.baserate import MAX_P_VALUE, MIN_LIFT_LOWER_BOUND, MIN_RECALL

    text = MANUAL.read_text(encoding="utf-8")
    problems: list[str] = []
    for label, value in (
        ("recall", f"{MIN_RECALL:.2f}"),
        ("lift lower bound", f"{MIN_LIFT_LOWER_BOUND:.2f}"),
        ("p-value", f"{MAX_P_VALUE:.2f}"),
    ):
        if value not in text:
            problems.append(f"manual does not quote the enforced {label} threshold {value}")
    return problems


def main() -> int:
    """Run every manual check. Returns a process exit code."""
    if not MANUAL.exists():
        print("manual-audit: docs/MANUAL.md is missing", file=sys.stderr)
        return 1
    problems = (
        check_every_command_documented()
        + check_sections_declare_a_kind()
        + check_gate_thresholds_match_the_code()
    )
    for problem in problems:
        print(f"manual-audit: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("manual-audit: the manual matches the code")
    return 0


if __name__ == "__main__":
    sys.exit(main())
