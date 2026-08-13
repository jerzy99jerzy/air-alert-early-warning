#!/usr/bin/env python3
"""Invariants specific to this repository.

These substitute for a second pair of eyes: a single maintainer cannot notice a
structural claim going stale, so the structure is asserted.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_baserate_is_top_level() -> list[str]:
    """The null model stays visible in the tree rather than folded into a helper."""
    if not (ROOT / "mavo" / "baserate.py").exists():
        return ["mavo/baserate.py is missing; the null model must be a top-level module"]
    return []


def check_single_namespace() -> list[str]:
    """Exactly one importable top-level package."""
    candidates = [
        path.name
        for path in ROOT.iterdir()
        if path.is_dir() and (path / "__init__.py").exists()
    ]
    if candidates != ["mavo"]:
        return [f"expected exactly one top-level package 'mavo', found {candidates}"]
    return []


def check_every_sprint_has_a_regression_file() -> list[str]:
    """Sprints declared shipped in STATUS.json have a regression file.

    Previously this scraped the changelog for the word "sprint", which meant a
    sentence naming future work failed the build. Shipped is a fact recorded in
    STATUS.json, not a word appearing in prose.
    """
    import json

    status = ROOT / "STATUS.json"
    if not status.exists():
        return ["STATUS.json is missing"]
    sprints = {str(number) for number in json.loads(status.read_text())["sprint_test_files"]}
    missing = [
        number
        for number in sorted(sprints)
        if not (ROOT / f"tests/test_sprint{number}.py").exists()
    ]
    return [f"sprint {number} has no tests/test_sprint{number}.py" for number in missing]


def check_docs_case_convention() -> list[str]:
    """Design documents uppercase, generated artefacts lowercase."""
    problems: list[str] = []
    for path in sorted((ROOT / "docs").glob("*.md")):
        stem = path.stem
        if stem.startswith("report"):
            continue
        if stem != stem.upper():
            problems.append(f"docs/{path.name} is a design document and must be UPPERCASE.md")
    return problems


def check_the_pipeline_does_not_import_its_reader() -> list[str]:
    """No module under `mavo/` may import `tools.progress`.

    `docs/OBSERVABILITY.md` section 6 asks for this and the last acceptance
    criterion in section 9 says it is a lint rather than an intention. The
    reason is not layering hygiene: a progress indicator wired into the run
    would be a second statement about where the run is, and the first thing it
    would do is disagree with the log. One writer, one record, one direction.
    """
    problems = []
    for module in sorted((ROOT / "mavo").rglob("*.py")):
        text = module.read_text(encoding="utf-8")
        if "tools.progress" in text or "from tools import progress" in text:
            problems.append(
                f"{module.relative_to(ROOT)} imports the run log's reader; the "
                "pipeline writes the record and never reads it back"
            )
    return problems


def main() -> int:
    """Run every domain invariant. Returns a process exit code."""
    problems = (
        check_baserate_is_top_level()
        + check_single_namespace()
        + check_every_sprint_has_a_regression_file()
        + check_docs_case_convention()
        + check_the_pipeline_does_not_import_its_reader()
    )
    for problem in problems:
        print(f"lint-domain: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("lint-domain: invariants hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
