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

#: Per-file ceilings, measured at 0.35.0.0. **A ceiling falls freely and rises
#: only with a reason written beside it**, which is what the error message has
#: always said and what the first version of this comment overstated as "may
#: only fall". A rule stated two ways in one module is a rule nobody can apply,
#: and this one was contradicting itself within a release of being written.
#:
#: Raised at 0.36.0.0:
#: * ``docs/METHODOLOGY.md`` 81 to 82. The entry for F109 quotes ``0.076``,
#:   the withdrawn pin, rather than describing it: a figure that was wrong by
#:   two orders of magnitude is evidence, and rounding it would soften the
#:   record of the error.
#:
#: Lowered at 0.36.0.0:
#: * ``docs/DEPLOYMENT.md`` 14 to 12. The F98 table's own figures were rounded
#:   while the section around them was rewritten.
#:
#: Raised at 0.37.0.0:
#: * ``TODO.md`` 27 to 28. "Where the project is" quotes ``0.076``, the
#:   withdrawn pin, beside the measured rate - the third site of the same
#:   exception, and the same reason each time: the contrast is the record.
#: * ``docs/DEPLOYMENT.md`` 13 to 14 at 0.40.0.0. The new figure is the
#:   document's own version marker, ``1.10``, and the error message's first
#:   option does not exist for it: an identifier cannot be rounded. The
#:   pattern cannot tell a measurement from a version, and this is the
#:   first marker in the tree to reach two digits after the dot. The
#:   durable repair is to skip the marker line rather than to buy a slot,
#:   which lowers counts across many documents and therefore owes a pass
#:   tightening every ceiling to its new count - not a release-night edit.
#: * ``docs/DEPLOYMENT.md`` 12 to 13. The S9 outcome paragraph quotes
#:   ``0.076``, the withdrawn pin, beside the measured 9.9% - the contrast is
#:   the finding and rounding the quote would soften the record, same
#:   exception as the F109 entry itself.
CEILINGS: dict[str, int] = {
    "ENGINEERING.md": 3,
    # 23 -> 22 at 0.42.0.0, and the first attempt at this line said 20 for a
    # reason that turned out to be wrong. `coverage_percent` is 96.6, one
    # decimal, so the *table row* dropped a figure - but the badge is written
    # by `check_badges_match_the_pins` as `:.2f` and its alt text has to match
    # the badge, so `96.60` still appears twice. Measured after the README was
    # in its final shape rather than predicted from the pin: 22.
    #
    # Lowered rather than left, which is what makes this a ratchet. T77 is the
    # same observation from the other direction: a ceiling that only ever rises
    # stops measuring the thing it was built for.
    # 22 -> 23 at 0.43.0.0, and this ceiling has now moved 23 -> 22 -> 23 in
    # three releases without a single new claim of false precision: it tracks
    # how many decimals the *coverage pin itself* happens to carry (96.48 ->
    # 96.6 -> 96.11), and the badge, its alt text and the table row all quote
    # the pin. A ceiling that follows a checked figure's formatting is
    # measuring noise; noted in the 0.43.0.0 review as a candidate for
    # excluding pin-quoted figures from this count rather than chasing them.
    "README.md": 23,
    # Raised at 0.39.1.0, 28 to 35, and the shape of the raise is the argument
    # for T77. **One of the seven is a measurement:** T9's closure quotes ``96.43``,
    # which is
    # `coverage_percent`: produced by pytest-cov, pinned in ``STATUS.json``,
    # compared against ``.gate/coverage.json`` and against a badge. Rounding it
    # here would create a fourth number rather than remove a third, which is the
    # exemption this module's own docstring states for machine-generated pins.
    # The two daily shares in the same entry were rounded to one decimal
    # instead: a tenth of a point on a day's duty cycle changes nothing anybody
    # does, which is the rule rather than the exemption.
    #
    # The other six are not measurements at all. **T77's own entry names the
    # tokens it exists to be about** - two truncated release numbers, two
    # interpreter versions quoted twice between the entry and its acceptance,
    # and ``7.84``, this module's own docstring example of the thing it does
    # want to catch - and an entry about tokens that cannot name them is not an
    # entry. So this counter's ceiling rose by four
    # to hold a task written because the counter counts the wrong things, which
    # is the clearest statement of the problem available and is left standing
    # here rather than tidied away.
    "TODO.md": 35,
    "docs/BRIEF-PL.md": 6,
    "docs/BRIEF.md": 6,
    "docs/CHANNEL.md": 19,
    "docs/COMPUTATION.md": 20,
    "docs/DATA-FLOW.md": 6,
    # 32 -> 33 at 0.43.0.0: D-039 quotes the measured poll latency, 0.26 s,
    # because the no-lock arithmetic rests on it and rounding a load-bearing
    # figure to "fast" is how arithmetic becomes hope.
    "docs/DECISIONS.md": 33,
    "docs/DEPLOYMENT.md": 14,
    "docs/FEED-SPEC.md": 6,
    "docs/FOUNDATIONS.md": 7,
    # 19 -> 20 at 0.43.0.0: the rewritten 4.5 (F127) quotes the channel's
    # hashtag coverage, 99.34%, the figure the sprint-7 redesign stands on.
    # 20 -> 21 at 0.47.0.0: section ordinal 4.10 reads to this lint as a
    # two-decimal figure; a heading number is not a precision claim.
    "docs/MANUAL.md": 21,
    "docs/MECHANISMS.md": 16,
    # Raised at 0.39.1.0, 82 to 87. F119's entry names the two interpreter
    # versions the defect appeared and disappeared on, ``3.14`` and ``3.12``,
    # five times between them, because the entry grew two paragraphs about
    # which interpreter saw what and neither can be written without naming
    # both.
    # and the whole finding is that one of them saw it and the other did not.
    # `FIGURE` excludes version strings only in the four-segment form this
    # repository uses for itself, so a two-segment interpreter version reads as
    # a figure with two decimals. **This is the second ceiling this release
    # raised for a reason unrelated to precision** and the class is logged as
    # T77 rather than absorbed here.
    "docs/METHODOLOGY.md": 87,
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
