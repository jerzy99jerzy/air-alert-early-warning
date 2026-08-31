#!/usr/bin/env python3
"""Every derived figure, computed once and written to both places that hold it.

**Why this exists, and it is not tidiness.** Six figures about this tree lived
in two places each: `STATUS.json` pinned them and `README.md` printed them, in
a badge and in a table. The gate compared the two and failed when they
disagreed, which is a guard that reports the drift after a person has already
made it, on a class of edit where the person is not the one who knows the
answer. Worse, one of them was a fixed point: `README.md` is inside the
`documentation` group whose line count `README.md` itself prints, so writing
the count changes the count. Converging it took two passes, by hand, every
release, and the second pass existed only because the first invalidated
itself.

`tools/todo_index.py` had already answered this for the backlog table:
regenerate the block, and let the gate check the regeneration rather than the
memory of whoever last edited. This is that answer applied to the rest.

**What it computes.** File and line counts per group, and the measured figures
that come from the gate's own artefacts: the test count and coverage from
`.gate/`, the defect count from the log, the release count from the changelog.
Nothing here is a judgement; every number is a count of something on disk,
which is exactly why no person should be maintaining it.

**What it does not do, and the boundary is D-046 rather than convenience.** It
does not touch a figure that a human measured - corpus counts, host readings,
latency distributions - because those belong to whoever took them. It also
does not touch the test count or the coverage percentage, and the first
version of this file got that wrong. Those come from a *run*, not from the
tree: `.gate/tests.xml` is written by the same `make verify` that later calls
this check, so a generator reading it would report drift on every run that
changed a test, which is the manual convergence dance this file exists to
retire, reintroduced one directory over. `docs_audit` polices those pins
against `.gate` and is the right place for it.

The discriminator, stated once: can the tree recompute the number by being
read, without being executed.

    python3 tools/figures.py            # write
    python3 tools/figures.py --check    # gate mode, non-zero on drift
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS = ROOT / "STATUS.json"
README = ROOT / "README.md"

#: Top-level documents counted with `docs/` as one documentation corpus.
TOP_DOCS = ("README.md", "CHANGELOG.md", "ENGINEERING.md", "SECURITY.md",
            "TODO.md", "CONTRIBUTING.md")


def groups() -> dict[str, list[Path]]:
    """The four counted groups, resolved to files that exist right now."""
    documentation = (sorted(ROOT.glob("docs/**/*.md"))
                     + [ROOT / name for name in TOP_DOCS]
                     + [ROOT / "tests" / "harness" / "CATALOGUE.md"])
    return {
        "package": sorted(ROOT.glob("mavo/**/*.py")),
        "test": sorted(ROOT.glob("tests/**/*.py")),
        "tool": sorted(ROOT.glob("tools/**/*.py")),
        "documentation": documentation,
    }


def statistics() -> dict[str, int]:
    """File and line counts per group. Missing files are skipped, not zeroed."""
    out: dict[str, int] = {}
    for label, paths in groups().items():
        present = [p for p in paths if p.exists()]
        out[f"{label}_files"] = len(present)
        out[f"{label}_lines"] = sum(
            len(p.read_text(encoding="utf-8").splitlines()) for p in present
        )
    return out


def counted_from_documents() -> dict[str, int]:
    """Counts of entries in a document rather than of files.

    **The releases count is why this function exists.** The README's headline
    table carried `Releases | 44` while the changelog held 122 entries, wrong
    by 78 and wrong for a long time, because the figure was pinned nowhere and
    maintained by ritual: each release incremented it by one, which keeps a
    number looking tended without ever comparing it to the thing it counts.
    Three figures beside it claimed the same provenance and were right, so the
    row read as trustworthy. A count that is incremented rather than counted
    is not a measurement, and the repair is to count it here every run.

    The oldest entry uses a three-segment version, so the pattern matches on
    the heading shape rather than on the segment count.
    """
    methodology = (ROOT / "docs" / "METHODOLOGY.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    decisions = (ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    return {
        "defects_logged": len(re.findall(r"^### F\d+", methodology, re.M)),
        "releases": len(re.findall(r"^## \d[\d.]* - \d{4}-", changelog, re.M)),
        "decisions_recorded": len(re.findall(r"^## D-\d+", decisions, re.M)),
    }


def render(status: dict[str, object], text: str) -> str:
    """Rewrite every generated figure in the README from the status document."""
    stats = status["statistics"]
    measured = status["measured"]
    assert isinstance(stats, dict) and isinstance(measured, dict)
    defects = status["defects_logged"]
    tests = measured["tests_passing"]
    coverage = measured["coverage_percent"]

    releases_count = status["releases"]
    decisions_count = status["decisions_recorded"]
    swaps = (
        (r"\[!\[tests \d+\]\(https://img\.shields\.io/badge/tests-\d+-brightgreen\)\]",
         f"[![tests {tests}](https://img.shields.io/badge/tests-{tests}-brightgreen)]"),
        (r"\[!\[coverage [\d.]+%\]\(https://img\.shields\.io/badge/coverage-[\d.]+%25-brightgreen\)\]",
         f"[![coverage {coverage}%](https://img.shields.io/badge/"
         f"coverage-{coverage}%25-brightgreen)]"),
        (r"\[!\[defects logged \d+\]\(https://img\.shields\.io/badge/"
         r"defects%20logged-\d+-informational\)\]",
         f"[![defects logged {defects}](https://img.shields.io/badge/"
         f"defects%20logged-{defects}-informational)]"),
    )
    for pattern, replacement in swaps:
        text = re.sub(pattern, replacement, text, count=1)

    rows = (("Package `mavo/`", "package"), ("Tests", "test"),
            ("Tools", "tool"), ("Documentation", "documentation"))
    for label, key in rows:
        text = re.sub(
            rf"\| {re.escape(label)} \| \d+ \| [\d,]+ \|",
            f"| {label} | {stats[f'{key}_files']} | {stats[f'{key}_lines']:,} |",
            text, count=1,
        )

    prose = (
        (r"\| Tests \| \d+, of which", f"| Tests | {tests}, of which"),
        (r"\| Coverage \| [\d.]+% against", f"| Coverage | {coverage}% against"),
        (r"\| Defects logged with their class \| \d+,",
         f"| Defects logged with their class | {defects},"),
        (r"\| Releases \| \d+ in the changelog", f"| Releases | {releases_count} in the changelog"),
        (r"\| Decisions recorded with reopen conditions \| \d+,",
         f"| Decisions recorded with reopen conditions | {decisions_count},"),
    )
    for pattern, replacement in prose:
        text = re.sub(pattern, replacement, text, count=1)
    return text


def compute() -> tuple[dict[str, object], str]:
    """Run to a fixed point, which is the whole reason this is a tool.

    The documentation count includes `README.md`, and `README.md` prints the
    documentation count, so writing it can change it. Two passes reach the
    point where the counts stop moving; a third is run as the check that they
    have. The loop belongs here, once, rather than in the head of whoever is
    cutting the release.
    """
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    text = README.read_text(encoding="utf-8")
    previous: str | None = None
    for _ in range(5):
        # Updated in place: replacing the dict would reorder the file and
        # bury a real change in a diff of moved lines.
        existing = status["statistics"]
        assert isinstance(existing, dict)
        existing.update(statistics())
        status.update(counted_from_documents())
        rendered = render(status, text)
        if rendered == previous:
            break
        previous = rendered
        # The next pass counts the tree as this pass would leave it.
        README.write_text(rendered, encoding="utf-8")
        text = rendered
    else:  # pragma: no cover - five passes never oscillate in practice
        raise SystemExit("figures: the counts did not settle in five passes")
    return status, rendered


def main(argv: list[str] | None = None) -> int:
    check = "--check" in (sys.argv[1:] if argv is None else argv)
    before_status = STATUS.read_text(encoding="utf-8")
    before_readme = README.read_text(encoding="utf-8")
    status, rendered = compute()
    written = json.dumps(status, indent=2, ensure_ascii=False) + "\n"

    if check:
        # Restore whatever the fixed-point loop wrote, then report.
        README.write_text(before_readme, encoding="utf-8")
        drift = []
        if written != before_status:
            drift.append("STATUS.json")
        if rendered != before_readme:
            drift.append("README.md")
        if drift:
            print("figures: " + " and ".join(drift)
                  + " disagree with the tree; run `python3 tools/figures.py`",
                  file=sys.stderr)
            return 1
        print("figures: every derived figure agrees with the tree")
        return 0

    STATUS.write_text(written, encoding="utf-8")
    README.write_text(rendered, encoding="utf-8")
    stats = status["statistics"]
    assert isinstance(stats, dict)
    print(f"figures: written, {stats['documentation_lines']:,} documentation lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
