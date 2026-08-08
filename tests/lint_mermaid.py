#!/usr/bin/env python3
"""Mermaid blocks must parse on the forge.

A semicolon inside a statement breaks rendering, and the markdown stays valid, so
every local check passes while the diagram is invisible. Only a lint catches it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)


def problems_in(text: str, name: str) -> list[str]:
    """Report offending lines inside mermaid fences."""
    found: list[str] = []
    for block in BLOCK.findall(text):
        for number, line in enumerate(block.splitlines(), 1):
            stripped = line.strip()
            if ";" in stripped and not stripped.startswith("%%"):
                found.append(f"{name}: semicolon in mermaid statement, block line {number}")
    return found


def main() -> int:
    """Scan README and docs. Returns a process exit code."""
    targets = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
    problems: list[str] = []
    for path in targets:
        if path.exists():
            problems += problems_in(path.read_text(encoding="utf-8"), path.name)
    for problem in problems:
        print(f"lint-mermaid: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"lint-mermaid: {len(targets)} documents clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
