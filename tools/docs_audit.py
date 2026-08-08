#!/usr/bin/env python3
"""Documentation consistency audit.

Pins in STATUS.json must match what the tree and the documents declare. A
version marker that drifts past a bump is the specific failure this catches: the
README says one thing, the package says another, and both look plausible.

Convention borrowed from `pirx/tools/docs_audit.py`.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _status() -> dict[str, object]:
    with (ROOT / "STATUS.json").open(encoding="utf-8") as handle:
        result: dict[str, object] = json.load(handle)
    return result


def check_version_pins(status: dict[str, object]) -> list[str]:
    """STATUS.json, pyproject, the package and the changelog agree."""
    problems: list[str] = []
    pinned = status["version"]

    with (ROOT / "pyproject.toml").open("rb") as handle:
        declared = tomllib.load(handle)["project"]["version"]
    if declared != pinned:
        problems.append(f"pyproject version {declared} != STATUS.json {pinned}")

    init = (ROOT / "mavo" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init)
    if match and match.group(1) != pinned:
        problems.append(f"__version__ {match.group(1)} != STATUS.json {pinned}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = re.findall(r"^##\s*([0-9][0-9A-Za-z.\-]*)", changelog, re.M)
    if headings and headings[0] != pinned:
        problems.append(f"CHANGELOG head {headings[0]} != STATUS.json {pinned}")

    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", str(pinned)):
        problems.append(f"version {pinned} is not four-segment; the portfolio uses X.Y.Z.W")
    return problems


def check_every_shipped_sprint_has_a_regression_file(status: dict[str, object]) -> list[str]:
    """A sprint declared shipped has the regression file that proves it."""
    sprints = status["shipped_sprints"]
    assert isinstance(sprints, list)
    return [
        f"sprint {number} declared shipped but tests/test_sprint{number}.py is missing"
        for number in sprints
        if not (ROOT / f"tests/test_sprint{number}.py").exists()
    ]


def check_threat_model_numbering(status: dict[str, object]) -> list[str]:
    """Threat rows are numbered MT1..MTn with no gaps, and the count is pinned."""
    text = (ROOT / "docs" / "THREAT-MODEL.md").read_text(encoding="utf-8")
    found = sorted({int(number) for number in re.findall(r"\bMT(\d+)\b", text)})
    problems: list[str] = []
    if not found:
        return ["docs/THREAT-MODEL.md has no numbered MT rows"]
    expected = list(range(1, found[-1] + 1))
    missing = sorted(set(expected) - set(found))
    if missing:
        problems.append(f"threat model numbering has gaps: MT{missing}")
    if len(found) != status["threat_model_rows"]:
        problems.append(
            f"threat model has {len(found)} rows, STATUS.json pins {status['threat_model_rows']}"
        )
    return problems


def check_harness_catalogue(status: dict[str, object]) -> list[str]:
    """Every catalogued attack has a test, and the count is pinned."""
    catalogue = ROOT / "tests" / "harness" / "CATALOGUE.md"
    if not catalogue.exists():
        return ["tests/harness/CATALOGUE.md is missing"]
    text = catalogue.read_text(encoding="utf-8")
    rows = sorted({int(number) for number in re.findall(r"\bA(\d+)\b", text)})
    tests = (ROOT / "tests" / "harness" / "test_attacks.py").read_text(encoding="utf-8")
    problems = [f"A{number} is catalogued but has no test" for number in rows
                if f"def test_a{number}_" not in tests]
    if len(rows) != status["harness_attacks"]:
        problems.append(
            f"catalogue has {len(rows)} attacks, STATUS.json pins {status['harness_attacks']}"
        )
    return problems


def main() -> int:
    """Run every audit. Returns a process exit code."""
    status = _status()
    problems = (
        check_version_pins(status)
        + check_every_shipped_sprint_has_a_regression_file(status)
        + check_threat_model_numbering(status)
        + check_harness_catalogue(status)
    )
    for problem in problems:
        print(f"docs-audit: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"docs-audit: pins hold at {status['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
