#!/usr/bin/env python3
"""Mermaid blocks must parse on the forge, and diagrams must be mermaid.

A semicolon inside a statement breaks rendering, and the markdown stays valid, so
every local check passes while the diagram is invisible. Only a lint catches it.

The second check was added in 0.19.2.0 after a deployment diagram shipped as
ASCII art in `docs/WEBAPP.md`. Four documents already carried mermaid, so the
convention existed and had no reader; the first document written by somebody who
had not read those four broke it, which is the shape a convention takes when it
lives only in the files that happen to follow it. An ASCII diagram does not
render on a phone, cannot be diffed meaningfully, and drifts out of alignment
the moment a name gets longer.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)
ANY_BLOCK = re.compile(r"```(\w*)\n(.*?)```", re.S)
# An arrow that is not part of a longer operator: the shape of a hand-drawn
# flow. `-->` and `->` catch the common cases; `>=`, `->>` and shell redirects
# are deliberately excluded so that command examples do not trip the check.
ARROW = re.compile(r"(?<![-<>=|/])(-->|->|\u2192)(?![->])")
# Prefixes that mark a line as a command rather than a diagram edge.
COMMAND = ("#", "$", "python", "make", "git", "pip", "curl", "rm", "tar",
           "rsync", "shasum", "cd", "ls", "sudo", "systemctl", "nginx", "echo")


def problems_in(text: str, name: str) -> list[str]:
    """Report offending lines inside mermaid fences."""
    found: list[str] = []
    for block in BLOCK.findall(text):
        for number, line in enumerate(block.splitlines(), 1):
            stripped = line.strip()
            if ";" in stripped and not stripped.startswith("%%"):
                found.append(f"{name}: semicolon in mermaid statement, block line {number}")
    return found


def ascii_diagrams_in(text: str, name: str) -> list[str]:
    """Report code blocks that look like a diagram drawn by hand.

    Heuristic and deliberately narrow: a non-mermaid block containing a line
    with a bare arrow that is not a shell command. A false positive is cheap
    to silence by making the block mermaid, which is what the rule asks for
    anyway; a false negative ships a diagram nobody can read on a phone.
    """
    found: list[str] = []
    for language, body in ANY_BLOCK.findall(text):
        if language == "mermaid":
            continue
        for number, line in enumerate(body.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(COMMAND):
                continue
            if ARROW.search(stripped):
                found.append(
                    f"{name}: block line {number} looks like an ASCII diagram; "
                    f"diagrams are mermaid (ENGINEERING, Diagrams)"
                )
                break
    return found


def main() -> int:
    """Scan README and docs. Returns a process exit code."""
    targets = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    problems: list[str] = []
    for path in targets:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            problems += problems_in(text, path.name)
            problems += ascii_diagrams_in(text, path.name)
    for problem in problems:
        print(f"lint-mermaid: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"lint-mermaid: {len(targets)} documents clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
