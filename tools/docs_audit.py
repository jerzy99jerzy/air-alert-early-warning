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


def check_contents_anchors_resolve() -> list[str]:
    """Every in-document link points at a heading that exists.

    Six documents now carry a contents index, which is six new surfaces for
    class-1 drift: a renamed section leaves a link that renders as a link and
    goes nowhere. GitHub's anchor rules are reimplemented here rather than
    assumed, and the reimplementation is the risk this check carries.
    """
    problems: list[str] = []
    for document in sorted(ROOT.glob("docs/*.md")) + [ROOT / "README.md"]:
        text = document.read_text(encoding="utf-8")
        headings = {
            "#" + re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")
            for heading in re.findall(r"^#{1,4} (.+)$", text, re.M)
        }
        for link in set(re.findall(r"\]\((#[a-z0-9-]+)\)", text)):
            if link not in headings:
                problems.append(f"{document.name} links to {link}, which is not a heading in it")
    return problems


def check_measured_block_is_recomputed(status: dict[str, object]) -> list[str]:
    """Two fields in STATUS.json that are results, not counts, are re-derived.

    `candidate_rules_passing_gate` sat at 0 for three releases after D-014 made
    it 1, and nothing noticed: the badge checks cover counts of files and rows,
    and this block is the one place the repository states an *outcome*. Same
    class as F31, in the block a reader is most likely to quote.

    Only the two fields that can be recomputed cheaply and deterministically are
    checked here. The rest of the block stays a typed claim, which is stated so
    the guarantee is not read as wider than it is.
    """
    import sys as _sys
    _sys.path.insert(0, str(ROOT))
    from mavo.baserate import gate
    from mavo.cli import DEFAULT_POLICY
    from mavo.evaluate import run_policy, run_rule
    from mavo.rules import CANDIDATE_RULES
    from mavo.sources.fixture import generate_history

    nights = generate_history(weeks=208)
    passing = sum(
        1 for rule_id, rule in CANDIDATE_RULES.items()
        if gate(run_rule(rule_id, rule, nights).assessment).passes
    )
    rate = run_policy(DEFAULT_POLICY, nights).combined.assessment.alarm_rate_per_week
    measured = status.get("measured", {})
    assert isinstance(measured, dict)
    problems: list[str] = []
    if measured.get("candidate_rules_passing_gate") != passing:
        problems.append(
            f"candidate_rules_passing_gate recomputes to {passing}, "
            f"STATUS.json states {measured.get('candidate_rules_passing_gate')}"
        )
    pinned_rate = float(measured.get("policy_combined_alarms_per_week", -1))
    if rate is not None and abs(pinned_rate - rate) > 0.005:
        problems.append(
            f"policy_combined_alarms_per_week recomputes to {rate:.2f}, "
            f"STATUS.json states {measured.get('policy_combined_alarms_per_week')}"
        )
    return problems


def check_statistics_match_the_tree(status: dict[str, object]) -> list[str]:
    """The size block in STATUS.json is recomputed, not remembered.

    The README says these numbers are measured at each release and pinned. That
    sentence was true of the intent and false of the mechanism: nothing checked
    them, and at 0.6.2.0 all four rows were a release or two stale while reading
    as authoritative. F31's shape exactly, in the one block that describes the
    repository to a reader who will not open it.

    Counted definition, stated because a count without one drifts by
    reinterpretation: `.py` files under the package, `tests/` and `tools/`
    recursively, and for documentation every `.md` under `docs/` recursively
    plus the top-level authored markdown and the harness catalogue.
    """
    top_level_docs = ["README.md", "CHANGELOG.md", "ENGINEERING.md", "SECURITY.md",
                      "TODO.md", "CONTRIBUTING.md"]
    groups = {
        "package": sorted((ROOT / "mavo").rglob("*.py")),
        "test": sorted((ROOT / "tests").rglob("*.py")),
        "tool": sorted((ROOT / "tools").rglob("*.py")),
        "documentation": (
            sorted((ROOT / "docs").rglob("*.md"))
            + [ROOT / name for name in top_level_docs]
            + [ROOT / "tests" / "harness" / "CATALOGUE.md"]
        ),
    }
    statistics = status.get("statistics", {})
    assert isinstance(statistics, dict)
    problems: list[str] = []
    for label, paths in groups.items():
        present = [path for path in paths if path.exists()]
        counted = {
            f"{label}_files": len(present),
            f"{label}_lines": sum(
                len(path.read_text(encoding="utf-8").splitlines()) for path in present
            ),
        }
        for key, value in counted.items():
            if statistics.get(key) != value:
                problems.append(
                    f"{key} is {value} in the tree, STATUS.json pins {statistics.get(key)}"
                )
    return problems


def check_readme_links_resolve() -> list[str]:
    """Every relative link in the README points at something that exists.

    The documentation table is the map a reader uses before they trust anything
    else, and a dead link there is a claim about the repository that the
    repository does not honour. Cheap to check, and the alternative is finding
    out from someone else's browser.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    problems: list[str] = []
    for target in re.findall(r"\]\((?!https?://|#)([^)]+)\)", readme):
        if not (ROOT / target).exists():
            problems.append(f"README links to {target}, which does not exist")
    return problems


def check_every_document_is_pinned(status: dict[str, object]) -> list[str]:
    """Every document in the tree appears in the ``documents`` block, and vice versa.

    The block was a hand-maintained list that nothing compared against the tree,
    so a document could be added and be invisible to this gate: its version
    marker could drift, or it could carry no marker at all, and every check here
    would still pass. A pin nobody checks is the same shape as a README claim the
    code does not implement, which is the one thing this repository says it will
    not ship (F66). Raised by the reader of `docs/reviews/0.11.1.0.md` on the
    release that added that very document.

    Top-level documents are deliberately out of scope: they are versioned by the
    release rather than by a marker of their own.
    """
    documents = status.get("documents")
    if not isinstance(documents, dict):
        return ["STATUS.json has no documents block"]
    on_disk = {
        str(path.relative_to(ROOT)) for path in sorted((ROOT / "docs").rglob("*.md"))
    }
    pinned = set(documents)
    problems = [
        f"{name} is in the tree and not pinned in STATUS.json"
        for name in sorted(on_disk - pinned)
    ]
    problems += [
        f"{name} is pinned in STATUS.json and not in the tree"
        for name in sorted(pinned - on_disk)
    ]
    return problems


def check_defect_count_is_pinned(status: dict[str, object]) -> list[str]:
    """The defect badge equals the count of F-entries in the methodology.

    Added in 0.6.0.0 when the review landed three entries at once: the badge is
    typed by hand, and a hand-typed count drifts on exactly the release that
    adds entries. The pin is checked against the document, and the badge against
    the pin, so all three agree or the gate says which one is lying.
    """
    entries = len(re.findall(r"^### F\d+", (ROOT / "docs" / "METHODOLOGY.md")
                             .read_text(encoding="utf-8"), re.M))
    pinned = status.get("defects_logged")
    problems: list[str] = []
    if pinned != entries:
        problems.append(f"METHODOLOGY has {entries} F-entries, STATUS.json pins {pinned}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if f"defects%20logged-{pinned}-" not in readme:
        problems.append(f"README defect badge does not match STATUS.json pin {pinned}")
    return problems


def check_badges_match_the_pins(status: dict[str, object]) -> list[str]:
    """Static badge values agree with STATUS.json.

    A live CI badge tells the truth by construction. A static one is a claim
    typed by hand, which is the shape of F31: a measurement block updated field
    by field until the flattering field is the stale one. Coverage is the one
    that would embarrass this repository most, so it is checked first.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    measured = status["measured"]
    assert isinstance(measured, dict)
    statistics = status.get("statistics", {})
    assert isinstance(statistics, dict)

    expected = {
        "tests": f"tests-{measured['tests_passing']}-",
        "coverage": f"coverage-{measured['coverage_percent']:.2f}%25-",
        "harness": f"harness-{status['harness_attacks']}%20attacks",
        "mutations": f"{measured['harness_mutations_killed']}%20mutation--verified",
        "runtime dependencies":
            f"runtime%20dependencies-{statistics.get('runtime_dependencies', 0)}-",
    }
    return [
        f"README badge for {label} does not match STATUS.json (expected {fragment!r})"
        for label, fragment in expected.items()
        if fragment not in readme
    ]


def check_cited_tests_exist() -> list[str]:
    """Every ``file.py::test_name`` cited in documentation resolves to a test.

    F42. `docs/THREAT-MODEL.md` cited a test measuring MT8 that has never existed
    in this repository under that name, and it survived three releases because
    nothing resolves a citation. A threat row naming a test that does not exist
    is a control that nobody is measuring while the table says otherwise, which
    is the same class as a README claim the tree does not implement.
    """
    problems: list[str] = []
    pattern = re.compile(r"([a-z_0-9]+\.py)::(test_[a-z_0-9]+)")
    for document in sorted(ROOT.glob("docs/*.md")) + [
        ROOT / "README.md",
        ROOT / "tests" / "harness" / "CATALOGUE.md",
    ]:
        if not document.exists():
            continue
        for filename, test_name in pattern.findall(document.read_text(encoding="utf-8")):
            candidates = list((ROOT / "tests").rglob(filename))
            if not candidates:
                problems.append(f"{document.name} cites {filename}, which does not exist")
                continue
            if not any(f"def {test_name}(" in path.read_text(encoding="utf-8")
                       for path in candidates):
                problems.append(f"{document.name} cites {filename}::{test_name}, which does not")
    return problems


def main() -> int:
    """Run every audit. Returns a process exit code."""
    status = _status()
    problems = (
        check_version_pins(status)
        + check_every_shipped_sprint_has_a_regression_file(status)
        + check_threat_model_numbering(status)
        + check_harness_catalogue(status)
        + check_cited_tests_exist()
        + check_readme_links_resolve()
        + check_every_document_is_pinned(status)
        + check_defect_count_is_pinned(status)
        + check_statistics_match_the_tree(status)
        + check_measured_block_is_recomputed(status)
        + check_badges_match_the_pins(status)
        + check_contents_anchors_resolve()
    )
    for problem in problems:
        print(f"docs-audit: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"docs-audit: pins hold at {status['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
