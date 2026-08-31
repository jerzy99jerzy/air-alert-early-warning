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

**Rewritten after F140, and the previous version is the reason.** Until then
this module compared only whole numbers of four digits or more, on the argument
that Polish writes a decimal comma and English a decimal point, so `0,04` and
`0.04` are the same figure in two unmatchable spellings, and teaching the check
two number systems was not worth a locale table nobody would maintain. That
argument was wrong twice over. It is four substitutions, written below. And the
class it gave up on - every figure under a thousand - is exactly where four
stale figures then sat for seventeen releases, in the section of the briefs
whose whole content is the claim that figures are guarded. `defects_logged` was
listed as a pin the entire time and never once compared, because a
`value < 1000` guard skipped it for every value that field will ever hold: a
check written, listed, documented and inert, which is class 2.

**What it can check and what it cannot.** It compares every figure the two
files carry, after normalising each language's own spelling of a number, and it
compares the figures that also appear in `STATUS.json` against the pin. It
cannot read prose for accuracy, and no check here should pretend to: the
defects that prompted 0.21.2.0 were a fabricated date and an overstated word
("independent"), and neither is reachable by any heuristic worth having. Those
are caught by a person re-reading, which is what `docs/reviews/` is for.

The corollary, and it is a design rule rather than a limitation: **a brief
should carry as few standing figures as it can.** A count that changes weekly
does not belong in a document nobody re-reads weekly, which is why the
open-item count was removed rather than pinned.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "docs" / "BRIEF.md"
PL = ROOT / "docs" / "BRIEF-PL.md"

#: Figures that must appear in both briefs and match the pin. Each entry is a
#: label, the path into `STATUS.json`, and how the pin is spelled in prose
#: **after normalisation**, which is why every renderer emits a decimal point.
#: A share pinned as a fraction is rendered as the percentage the briefs print;
#: the number of decimal places is part of the entry because it is part of the
#: claim, and moving one is a decision rather than a formatting choice.
PINNED: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("corpus messages", ("corpus", "messages"), "{:d}"),
    ("holdout share", ("corpus", "holdout_share"), "{:.2%}"),
    ("defects logged", ("defects_logged",), "{:d}"),
    ("decisions recorded", ("decisions_recorded",), "{:d}"),
    ("harness attacks", ("harness_attacks",), "{:d}"),
    ("tests passing", ("measured", "tests_passing"), "{:d}"),
    ("coverage percent", ("measured", "coverage_percent"), "{:.2f}"),
    ("harness mutations killed", ("measured", "harness_mutations_killed"), "{:d}"),
    ("design window nights", ("measured", "design_window_nights"), "{:d}"),
    ("design window messages", ("measured", "design_window_messages"), "{:d}"),
    ("area hashtag share", ("measured", "messages_with_area_hashtag_share"), "{:.1%}"),
    ("distinct area hashtags", ("measured", "distinct_area_hashtags_design_window"), "{:d}"),
    ("hashtags resolving", ("measured", "hashtags_resolving_to_register_code"), "{:d}"),
    ("tag/prose comparable", ("measured", "tag_prose_comparable_messages"), "{:d}"),
    ("western episodes", ("measured", "western_episodes_design_window"), "{:d}"),
    ("western wide episodes", ("measured", "western_wide_episodes_design_window"), "{:d}"),
    ("western episodes per week", ("measured", "western_episodes_per_week"), "{:.1f}"),
    ("western wide per week", ("measured", "western_wide_episodes_per_week"), "{:.1f}"),
    ("areas with border distance", ("measured", "areas_with_border_distance"), "{:d}"),
    ("border intervals at zero", ("measured", "border_intervals_reaching_zero"), "{:d}"),
    ("nearest area centre km", ("measured", "nearest_area_centre_km"), "{:.1f}"),
    ("kind coverage 1h", ("measured", "kind_coverage_1h"), "{:.1%}"),
    ("kind join coverage 1h", ("measured", "kind_join_coverage_1h"), "{:.1%}"),
    ("catalogue resources", ("measured", "open_data_catalogue_resources_searched"), "{:d}"),
    ("catalogue alerting sets",
     ("measured", "open_data_catalogue_alerting_datasets_found"), "{:d}"),
)

#: `tag_prose_agreement` is deliberately absent from the table above. The briefs
#: quote it as a bound - "agree more than 99.99% of the time" against a pin of
#: 0.99997 - so the prose figure is not the pin rendered to any number of
#: places, and a renderer that made it match would encode a rounding nobody
#: decided on. Stated here rather than left looking like an omission.

_MONTHS_PL = ("stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
              "lipca", "sierpnia", "wrzesnia", "wrze\u015bnia", "pazdziernika",
              "pa\u017adziernika", "listopada", "grudnia")
_MONTHS_EN = ("January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December")

#: Month name to number, for both spellings of the two Polish months that carry
#: diacritics. Built by name rather than by position because the Polish tuple
#: holds two entries for the same month.
_MONTH_NUMBER: dict[str, str] = {
    "stycznia": "01", "lutego": "02", "marca": "03", "kwietnia": "04",
    "maja": "05", "czerwca": "06", "lipca": "07", "sierpnia": "08",
    "wrzesnia": "09", "wrze\u015bnia": "09", "pazdziernika": "10",
    "pa\u017adziernika": "10", "listopada": "11", "grudnia": "12",
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12",
}

_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_CLOCK = re.compile(r"\b\d{1,2}:\d{2}\b")

#: `\s+` rather than a literal space, and a trailing year the pattern consumes
#: rather than leaves behind. Both were found by running this module against the
#: files rather than by reasoning about them: a date wrapped across a line break
#: reads as no date at all, and a year left standing after the day and month are
#: removed reads as a quantity appearing four times on one side and once on the
#: other. Same class as the defect this module was rewritten for.
_DATE_PL = re.compile(r"\b(\d{1,2})\s+(" + "|".join(_MONTHS_PL) + r")(?:\s+(\d{4}))?")
_DATE_EN = re.compile(r"\b(\d{1,2})\s+(" + "|".join(_MONTHS_EN) + r")(?:\s+(\d{4}))?")

#: Polish inflects: the header writes `version 2.5` and the prose writes
#: `w wersji 2.4`. A pattern matching only the nominative missed every mention
#: in the body of the Polish file.
_VERSION = re.compile(r"(?:version|revision|wersj\w*)\s+v?\d+(?:\.\d+)+",
                      re.IGNORECASE)


def dates(text: str, polish: bool) -> set[str]:
    """Every date in the file as `MM-DD`, whatever the calendar convention.

    English writes `2026-08-12` where Polish writes `12 sierpnia 2026`. Both
    are the same day and neither is a claim about a quantity, so they are
    compared here as dates and removed before the figures are compared. Without
    this the parity check fires on `08` five times against two, which is a
    difference in convention and nothing else.
    """
    found = {f"{m.group(1)}-{m.group(2)}"
             for m in re.finditer(r"\b\d{4}-(\d{2})-(\d{2})\b", text)}
    pattern = _DATE_PL if polish else _DATE_EN
    for match in pattern.finditer(text):
        found.add(f"{_MONTH_NUMBER[match.group(2)]}-{int(match.group(1)):02d}")
    return found


def figures(text: str, polish: bool) -> Counter[str]:
    """Every numeric token, normalised out of its language's spelling.

    Polish separates thousands with a space and marks decimals with a comma;
    English does the reverse. Dates, clock times and version strings are removed
    first, because none of them is a quantity and all three differ by convention
    between the two files.
    """
    stripped = _ISO_DATE.sub(" ", text)
    stripped = (_DATE_PL if polish else _DATE_EN).sub(" ", stripped)
    stripped = _CLOCK.sub(" ", stripped)
    stripped = _VERSION.sub(" ", stripped)
    stripped = re.sub(r"\b\d+\.\d+\.\d+\.\d+\b", " ", stripped)
    if polish:
        stripped = re.sub(r"(?<=\d)[\u0020\u00a0\u2009](?=\d{3}\b)", "", stripped)
        stripped = re.sub(r"(?<=\d),(?=\d)", ".", stripped)
    else:
        stripped = re.sub(r"(?<=\d),(?=\d{3}\b)", "", stripped)
    return Counter(re.findall(r"\d+(?:\.\d+)?", stripped))


def pin(status: dict[str, object], path: tuple[str, ...]) -> float:
    """Follow a path into the status document."""
    node: object = status
    for key in path:
        assert isinstance(node, dict)
        node = node[key]
    assert isinstance(node, (int, float))
    return float(node)


def render(value: float, form: str) -> str:
    """Spell a pin the way the briefs spell it, normalised to a decimal point."""
    if form.endswith("%}"):
        return form.format(value).rstrip("%")
    if form.endswith("d}"):
        return form.format(int(value))
    return form.format(value)


def check() -> list[str]:
    """Compare the briefs against each other and against the pins."""
    if not EN.exists() or not PL.exists():
        return ["one of the two briefs is missing; they are a pair by design"]
    english = EN.read_text(encoding="utf-8")
    polish = PL.read_text(encoding="utf-8")
    status = json.loads((ROOT / "STATUS.json").read_text(encoding="utf-8"))
    problems: list[str] = []

    en_figures = figures(english, polish=False)
    pl_figures = figures(polish, polish=True)

    for label, path, form in PINNED:
        wanted = render(pin(status, path), form)
        for name, found in (("BRIEF.md", en_figures), ("BRIEF-PL.md", pl_figures)):
            if wanted not in found:
                problems.append(
                    f"{name} does not carry the pinned {label} ({wanted}); "
                    f"either the figure drifted or it was removed without saying so"
                )

    only_en_dates = dates(english, polish=False) - dates(polish, polish=True)
    only_pl_dates = dates(polish, polish=True) - dates(english, polish=False)
    for side, missing_dates in (("BRIEF.md", only_en_dates),
                                ("BRIEF-PL.md", only_pl_dates)):
        other = "BRIEF-PL.md" if side == "BRIEF.md" else "BRIEF.md"
        for day in sorted(missing_dates):
            problems.append(
                f"{side} carries the date {day} and {other} does not; "
                f"the two are the same document and drifted apart"
            )

    # Every remaining figure, by value and by how many times it is used. A
    # figure quoted twice on one side and once on the other is a drift too:
    # that is how a corrected number ends up standing beside its old value.
    for value in sorted(set(en_figures) | set(pl_figures), key=float):
        in_en, in_pl = en_figures[value], pl_figures[value]
        if in_en != in_pl:
            problems.append(
                f"the figure {value} appears {in_en} time(s) in BRIEF.md and "
                f"{in_pl} time(s) in BRIEF-PL.md; the two are the same document"
            )
    return problems


def main() -> int:
    """Run the check. Returns a process exit code."""
    problems = check()
    for problem in problems:
        print(f"brief-check: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("brief-check: the two briefs agree figure for figure, "
          "and every pinned figure holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
