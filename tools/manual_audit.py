#!/usr/bin/env python3
"""Manual audit: the operator's manual may not drift from the code.

A manual that falls behind is worse than no manual, because it is believed.
Moved out of the general domain lint into its own tool so it can be a separate
CI job, matching `pirx/tools/manual_audit.py`.
"""

from __future__ import annotations

import contextlib
import io
import re
import shlex
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


def check_every_option_documented() -> list[str]:
    """Every CLI option has a row in the manual.

    `check_every_command_documented` above asserts that each subcommand has a
    section, which is the shape of the manual rather than its contents: four
    options were absent from `docs/MANUAL.md` while that check was green
    (`rso --category`, `rso --page`, `report --feed`, `report --interval`).
    An option nobody documented is an option nobody uses, and `--feed` is the
    file the consumer's history panel reads.
    """
    sys.path.insert(0, str(ROOT))
    from mavo.cli import build_parser

    text = MANUAL.read_text(encoding="utf-8")
    problems: list[str] = []
    for action in build_parser()._actions:
        choices = getattr(action, "choices", None)
        if not isinstance(choices, dict):
            continue
        for name, sub in choices.items():
            for option in sub._actions:
                for flag in option.option_strings:
                    if flag in ("-h", "--help"):
                        continue
                    if f"`{flag}`" not in text:
                        problems.append(
                            f"`mavo {name} {flag}` has no row in docs/MANUAL.md"
                        )
    return problems


#: Fenced blocks whose first line starts with one of these are executed and
#: compared against the line below it.
#:
#: **Deliberately one entry.** `mavo collect --stub` reads a file and writes
#: nothing. Every other command either reaches the network or creates
#: something: `report --store` and `fixture` construct an `EventStore`, which
#: makes the directory it was pointed at, so an audit that ran them would
#: write into the tree it is auditing and would pass on the second run for a
#: reason that has nothing to do with the manual. A check with a side effect
#: is a check that changes its own answer.
RUNNABLE = ("mavo collect --stub",)

#: Tokens that differ between two correct runs and are compared as their
#: shape rather than their value. A transcript is pinned for the counts it
#: reports, which is the part that drifted; failing it on a clock would teach
#: a reader to regenerate the block instead of reading it.
VOLATILE = (
    re.compile(r"latency=[0-9.]+s"),
    re.compile(r"\d{4}-\d{2}-\d{2}T[0-9:]+(?:\+00:00|Z)"),
)


def _comparable(line: str) -> str:
    """One transcript line with its volatile tokens masked."""
    for pattern in VOLATILE:
        line = pattern.sub("<varies>", line)
    return line.strip()


def check_transcripts_reproduce() -> list[str]:
    """A transcript in the manual is executed, not trusted.

    **The reason this exists.** Section 4.5 printed
    `messages=3 parsed=2 unparsed=1` from a run of the pre-sprint-7 parser,
    which read oblast names out of prose. The tree has resolved areas by
    hashtag since 0.11.0.0 and the same command produced
    `messages=3 parsed=0 unparsed=3` for twenty-eight releases while
    `manual-audit` reported that the manual matched the code. It matched the
    code's *shape*: every command had a section and every section had a marker.
    A manual that falls behind is worse than no manual because it is believed,
    and the first thing a reader believes is the output block.

    Only the first line of a transcript is compared. The rest is prose about
    the line, and a check that demanded the whole block would fail on a
    reformatted paragraph and teach its reader to regenerate rather than to
    look.
    """
    text = MANUAL.read_text(encoding="utf-8")
    problems: list[str] = []
    for block in re.findall(r"^```\n(.*?)^```", text, re.S | re.M):
        lines = [line for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        command, expected = lines[0].strip(), lines[1].strip()
        if not any(command.startswith(prefix) for prefix in RUNNABLE):
            continue
        if expected.startswith("mavo "):
            # A block holding two commands and no output. Nothing to compare,
            # and reading the second command as the first one's output is how
            # a check invents a failure.
            continue
        argv = shlex.split(command)[1:]
        sys.path.insert(0, str(ROOT))
        from mavo.cli import main as cli_main

        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                cli_main(argv)
        except SystemExit:  # pragma: no cover - argparse refusing an argument
            problems.append(f"transcript `{command}` did not run")
            continue
        produced = buffer.getvalue().splitlines()
        first = _comparable(produced[0]) if produced else ""
        if first != _comparable(expected):
            problems.append(
                f"transcript for `{command}` prints {first!r}, "
                f"the manual shows {_comparable(expected)!r}"
            )
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
        + check_every_option_documented()
        + check_transcripts_reproduce()
    )
    for problem in problems:
        print(f"manual-audit: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("manual-audit: the manual matches the code")
    return 0


if __name__ == "__main__":
    sys.exit(main())
