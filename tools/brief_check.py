#!/usr/bin/env python3
"""The two briefs must agree with each other, and their figures with the pins.

`docs/BRIEF.md` and `docs/BRIEF-PL.md` are the same document in two languages.
Nothing in the gate read either of them until 0.21.2.0, and within an hour of
the Polish one being written the two had already drifted: both said "34 open
items" while the backlog held 35, because a task had been added in between and
neither sentence knew.

That drift was predicted in `docs/reviews/0.21.0.0.md`, in the paragraph
recording that nothing checks whether the two still say the same thing. A risk
written down and left unguarded is the shape this repository logs about itself
(F72), so this is the guard.

**What it can check and what it cannot.** It compares the numbers that appear
in both files, and the ones that also appear in `STATUS.json`. It cannot read
prose for accuracy, and no check here should pretend to: the defects that
prompted this release were a fabricated date and an overstated word
("independent"), and neither is reachable by any heuristic worth having. Those
are caught by a person re-reading, which is what `docs/reviews/` is for.

The corollary, and it is a design rule rather than a limitation: **a brief
should carry as few standing figures as it can.** A count that changes weekly
does not belong in a document nobody re-reads weekly, which is why the open-item
count was removed rather than pinned.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "docs" / "BRIEF.md"
PL = ROOT / "docs" / "BRIEF-PL.md"

# Figures that must appear in both briefs and match the pin. Each entry is the
# label, the pin path in STATUS.json, and how the number is written in prose.
PINNED = (
    ("corpus messages", ("corpus", "messages"), "{:,}"),
    ("defects logged", ("defects_logged",), "{:d}"),
)


def pin(status: dict[str, object], path: tuple[str, ...]) -> int:
    """Follow a dotted path into the status document."""
    node: object = status
    for key in path:
        assert isinstance(node, dict)
        node = node[key]
    assert isinstance(node, int)
    return node


def figures(text: str) -> set[str]:
    """Whole numbers of four digits or more, with thousands separators removed.

    Deliberately narrow, and the narrowness was forced by the first run. Polish
    writes a decimal comma and English a decimal point, so `0,04` and `0.04`
    are the same figure in two unmatchable spellings, and comparing them
    produced three false positives immediately. Rather than teach the check
    two number systems, it looks only at figures where the two languages agree
    on the shape: whole numbers large enough that a thousands separator is the
    only punctuation they carry.

    What this gives up: every small number and every decimal, which is most of
    them. What it keeps is the class that actually drifted, corpus and traffic
    counts, and it keeps them without a locale table nobody would maintain.
    """
    found = set()
    for raw in re.findall(r"\d{1,3}(?:[ ,\u00a0]\d{3})+|\d{4,}", text):
        cleaned = re.sub(r"[ ,\u00a0]", "", raw)
        if cleaned.isdigit():
            found.add(cleaned)
    return found


def check() -> list[str]:
    """Compare the briefs against each other and against the pins."""
    if not EN.exists() or not PL.exists():
        return ["one of the two briefs is missing; they are a pair by design"]
    english = EN.read_text(encoding="utf-8")
    polish = PL.read_text(encoding="utf-8")
    status = json.loads((ROOT / "STATUS.json").read_text(encoding="utf-8"))
    problems: list[str] = []

    for label, path, _form in PINNED:
        value = pin(status, path)
        rendered = {str(value)}
        if value < 1000:
            continue  # below the width this check can compare across languages
        for name, text in (("BRIEF.md", english), ("BRIEF-PL.md", polish)):
            if not rendered & figures(text):
                problems.append(
                    f"{name} does not carry the pinned {label} ({value}); "
                    f"either the figure drifted or it was removed without saying so"
                )

    # Numbers present in one brief and absent from the other. Years are
    # excluded: they are structure rather than claims.
    structural = {"2026", "2025", "2024", "2023", "2022"}
    only_en = figures(english) - figures(polish) - structural
    only_pl = figures(polish) - figures(english) - structural
    for side, missing in (("BRIEF.md", only_en), ("BRIEF-PL.md", only_pl)):
        other = "BRIEF-PL.md" if side == "BRIEF.md" else "BRIEF.md"
        for number in sorted(missing):
            problems.append(
                f"{side} carries the figure {number} and {other} does not; "
                f"the two are the same document and drifted apart"
            )
    return problems


def main() -> int:
    """Run the check. Returns a process exit code."""
    problems = check()
    for problem in problems:
        print(f"brief-check: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("brief-check: the two briefs agree, and their pinned figures hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
