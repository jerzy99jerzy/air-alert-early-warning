#!/usr/bin/env python3
"""False precision, counted per document and ratcheted downward.

**The rule.** A figure is printed to the precision that changes a reader's
decision and no further. `7.84 days` is eight days; the hundredth of a day is
fourteen minutes of a week-long window and it changes nothing anybody does. A
digit that cannot change a decision is not rigour, it is rigour's costume, and
in a repository whose whole argument is that unmeasured things must not look
measured, that costume is worse here than it would be elsewhere.

**What the rule does not touch, and this is most of what is left.** Three
classes of figure keep every digit they have:

* **Counts.** 61,041 messages, 446 tests, 5,120 observations. A count is not a
  measurement and has no resolution to exceed.
* **Ratios where the digits are the claim.** 99.997% is "one message in
  38,521" and 0.076% is "fourteen polls in eighteen thousand". Rounding those
  deletes the finding rather than the noise.
* **Statistical output where the reader is doing the arithmetic.** Precision,
  recall, lift and p-values at three decimals inside `docs/METHODOLOGY.md` and
  `docs/MANUAL.md`, which are read by somebody checking the sums.

Machine-generated pins are also outside it. `coverage_percent` is produced by
`pytest-cov`, pinned in `STATUS.json`, compared against `.gate/coverage.json`
and against a badge; rounding it in prose would create a fourth number rather
than remove a third.

**Why this counts instead of judging.** Which class a figure belongs to is not
decidable from the text: `0.076` and `7.84` are the same shape and only one is
noise. A checker that guessed would be wrong in both directions and would then
have to be argued with. So it counts, per file, against a ceiling that may
fall and may not rise. **The ceiling is exact in both directions**: a file
above it has gained a figure nobody classified, and a file below it has been
cleaned without the debt being written down, and a debt that quietly shrinks
is a debt nobody can report on.

**The limitation, stated rather than discovered.** A count cannot tell one
figure from another, so swapping a rounded figure for a fresh unrounded one
passes. This measures direction, which is what a ratchet is for, and it is the
same trade `fail_under` makes on coverage.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Dated records. `CHANGELOG.md` and the reviews say what was true at a
#: release, and a figure inside them is evidence of what was claimed then.
#: Rounding those would edit the record to make the present look tidier, which
#: is the one edit this repository never makes.
EXCLUDED = ("CHANGELOG.md", "docs/reviews/")

#: Two or more decimals, excluding version strings (`0.33.0.2`), addresses
#: (`34.116.232.215`) and anything glued to a word.
FIGURE = re.compile(r"(?<![\w.])\d+\.\d{2,}(?!\.\d)(?!\w)")

#: The same figure written the Polish way. Applied **only** to `*-PL.md`,
#: because a comma means one thing in `96,61` and another in `38,521`, and
#: which one it means is a property of the document's language rather than of
#: the string. Exactly two fractional digits, so a thousands group of three
#: cannot be read as a decimal; a Polish figure with three decimals is missed
#: and that is a stated hole rather than a discovered one.
FIGURE_PL = re.compile(r"(?<![\d,.])\d+,\d{2}(?!\d)")

#: Per-file ceilings, measured at 0.35.0.0. **These may only fall.** The
#: documentation sprint lowers them; nothing else may raise one.
CEILINGS: dict[str, int] = {
    "ENGINEERING.md": 3,
    "README.md": 23,
    "TODO.md": 27,
    "docs/BRIEF-PL.md": 6,
    "docs/BRIEF.md": 6,
    "docs/CHANNEL.md": 19,
    "docs/COMPUTATION.md": 20,
    "docs/DATA-FLOW.md": 6,
    "docs/DECISIONS.md": 32,
    "docs/DEPLOYMENT.md": 14,
    "docs/FEED-SPEC.md": 6,
    "docs/FOUNDATIONS.md": 7,
    "docs/MANUAL.md": 19,
    "docs/MECHANISMS.md": 16,
    "docs/METHODOLOGY.md": 81,
    "docs/MVP.md": 2,
    "docs/OBSERVABILITY.md": 1,
}


def documents() -> list[Path]:
    """Every tracked Markdown file that is not a dated record."""
    listed = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [
        ROOT / name
        for name in listed
        if not any(name.startswith(prefix) for prefix in EXCLUDED)
    ]


def count(path: Path) -> int:
    """Figures with two or more decimals in one document, in either notation."""
    text = path.read_text(encoding="utf-8")
    found = len(FIGURE.findall(text))
    if path.name.endswith("-PL.md"):
        found += len(FIGURE_PL.findall(text))
    return found


def main() -> int:
    """Compare every document against its ceiling. Returns a process exit code."""
    problems: list[str] = []
    total = 0
    for path in sorted(documents()):
        name = path.relative_to(ROOT).as_posix()
        found = count(path)
        total += found
        ceiling = CEILINGS.get(name, 0)
        if found > ceiling:
            problems.append(
                f"{name} carries {found} figures with two or more decimals and "
                f"its ceiling is {ceiling}; round the new one, or raise the "
                f"ceiling in tools/precision_lint.py with the reason"
            )
        elif found < ceiling:
            problems.append(
                f"{name} carries {found} and its ceiling is still {ceiling}; "
                f"lower the ceiling, so the debt this file used to hold is "
                f"recorded as paid rather than forgotten"
            )
    for stale in sorted(set(CEILINGS) - {p.relative_to(ROOT).as_posix() for p in documents()}):
        problems.append(f"{stale} has a ceiling and is not a tracked document")
    for problem in problems:
        print(f"lint-precision: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"lint-precision: {total} figures held at their ceilings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
