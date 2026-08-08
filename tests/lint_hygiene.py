#!/usr/bin/env python3
"""Cheap repository hygiene. No interpreter beyond the standard library.

Each check exists because its absence shipped somewhere in this portfolio.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "dist", "build", ".mypy_cache",
             ".ruff_cache", ".pytest_cache", "data"}
DEV_PATH = re.compile(r"(/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+/)")

# A term-level guard cannot distinguish use from mention, so the documents that
# define the guarded pattern are exempt by name. Third instance of this class in
# sprint 2 (F2, F3, F4 in docs/METHODOLOGY.md); named rather than patched twice.
PATTERN_DEFINING_DOCS = {"ENGINEERING.md", "lint_hygiene.py"}


def _tracked_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not SKIP_DIRS & set(path.relative_to(ROOT).parts)
    ]


def check_no_patch_artefacts(files: list[Path]) -> list[str]:
    """Transfer artefacts committed by reflex."""
    return [
        f"transfer artefact tracked: {path.relative_to(ROOT)}"
        for path in files
        if path.suffix in {".patch", ".diff"}
    ]


def check_no_developer_paths(files: list[Path]) -> list[str]:
    """Absolute developer paths in tracked source."""
    problems: list[str] = []
    for path in files:
        if path.suffix not in {".py", ".toml", ".md", ".yml", ".yaml", ".cfg"}:
            continue
        if path.name in PATTERN_DEFINING_DOCS:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if DEV_PATH.search(line):
                problems.append(f"developer path at {path.relative_to(ROOT)}:{number}")
    return problems


def check_version_agreement() -> list[str]:
    """pyproject, package and changelog must state the same version."""
    problems: list[str] = []
    with (ROOT / "pyproject.toml").open("rb") as handle:
        declared = tomllib.load(handle)["project"]["version"]

    init = (ROOT / "mavo" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init)
    if match is None:
        problems.append("mavo/__init__.py declares no __version__")
    elif match.group(1) != declared:
        problems.append(f"__version__ {match.group(1)} != pyproject {declared}")

    changelog = ROOT / "CHANGELOG.md"
    if changelog.exists():
        headings = re.findall(r"^##\s*\[?([0-9][0-9A-Za-z.\-]*)\]?", changelog.read_text(), re.M)
        if not headings:
            problems.append("CHANGELOG.md has no versioned heading")
        elif headings[0] != declared:
            problems.append(f"CHANGELOG top entry {headings[0]} != pyproject {declared}")
    return problems


def main() -> int:
    """Run every hygiene check. Returns a process exit code."""
    files = _tracked_files()
    problems = (
        check_no_patch_artefacts(files)
        + check_no_developer_paths(files)
        + check_version_agreement()
    )
    for problem in problems:
        print(f"lint-hygiene: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"lint-hygiene: {len(files)} files clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
