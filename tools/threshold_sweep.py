#!/usr/bin/env python3
"""What does an intensification threshold cost in alarms per week?

The question this answers is the one the scenario tables could not: a rule that
fires on nights of intensified activity is only worth building if the fraction
of nights it fires on is small enough to fit a recipient's attention. That
fraction is a property of the corpus, not of an argument, and until it is
measured every statement about feasibility is a scenario.

**What this tool measures.** For each candidate threshold it reports how many
nights carry at least that many alert messages, what fraction of all nights
that is, and what firing rate per week that implies. Four axes are swept
independently: message volume per night and its busiest hour, each with and
without a term filter.

**The hourly axis exists because the nightly one measured flat.** On the first
real run every night in the design window carried more than 120 messages, so a
per-night volume threshold cannot separate anything: the channel is loud
continuously, at roughly 490 messages a night. Intensification, if it is
visible at all, is an hourly phenomenon that a nightly count averages away. The
hourly axis takes each night's busiest clock hour and sweeps thresholds on
that.

**What it does not measure, and this is the load-bearing caveat.** It cannot
tell you the recall of any threshold, because it does not know which nights
carried a border crossing. Recall comes from the event list, which lives
outside this corpus. A threshold that fires on 8% of nights is affordable; it
is worthless if it sleeps through the crossings, and this tool is silent on
that half of the gate by construction.

**The area filter will look broken, and it is not this tool that is broken.**
The shipped pattern table keys on oblast names while the channel emits raions
and hromadas (F23), so a western-oblast term list matches close to nothing.
That is why coverage is printed on every run: a filtered sweep whose coverage
is near zero is reporting the classifier defect, not a property of the nights.
Until the sprint 7 redesign lands, the volume sweep is the usable half.

**Holdout.** The tool refuses to read any page above the boundary frozen in
`STATUS.json` (D-012a). The boundary was computed before any message content
was read, and a sweep that quietly crossed it would spend the split without a
decision to spend it. It writes nothing, anywhere.

Usage:

    python3 tools/threshold_sweep.py --corpus data/raw/corpus
    python3 tools/threshold_sweep.py --corpus data/raw/corpus --terms west.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mavo.backfill import SNAPSHOT_NAME as PAGE_RANGE  # noqa: E402
from mavo.sources.telegram import _BLOCK, _TEXT, _TIME, _parse_timestamp, _strip  # noqa: E402

# Oblast-level terms, kept explicit and known incomplete. This is not a
# gazetteer; T15 owns that. Anything matched here is matched because the
# channel happened to name an oblast, which F23 measured at near zero.
DEFAULT_WEST_TERMS: tuple[str, ...] = (
    "львів", "волин", "рівнен", "тернопіл", "івано-франків",
    "закарпат", "хмельниц", "чернівец",
)


def _boundary() -> int:
    """The frozen design/holdout post id, read rather than remembered."""
    status = json.loads((ROOT / "STATUS.json").read_text(encoding="utf-8"))
    corpus = status.get("corpus", {})
    if "design_window_high_id" in corpus:
        return int(corpus["design_window_high_id"])
    raise SystemExit(
        "STATUS.json carries no holdout boundary. Refusing to sweep: a sweep that "
        "cannot prove it stayed inside the design window is not evidence (D-012a)"
    )


def _design_pages(directory: Path, boundary: int) -> tuple[list[Path], int]:
    """Pages wholly below the boundary, and the count refused for being above."""
    kept: list[Path] = []
    refused = 0
    for path in sorted(directory.glob("page-*.html")):
        match = PAGE_RANGE.search(path.name)
        if match is None:
            continue
        if int(match.group(2)) <= boundary:
            kept.append(path)
        else:
            refused += 1
    return kept, refused


def _night_of(when: datetime, cutover_hour: int) -> str:
    """Label the night a timestamp belongs to.

    A night that runs past midnight is one night, not two. The cutover is a
    parameter and printed on every run, because the choice moves every number
    below and a threshold quoted without it is not reproducible.
    """
    shifted = when.astimezone(UTC) - timedelta(hours=cutover_hour)
    return shifted.date().isoformat()


def _read(paths: list[Path], cutover_hour: int, terms: tuple[str, ...]) -> tuple[
    Counter[str], Counter[str], Counter[tuple[str, int]], Counter[tuple[str, int]], int, int
]:
    """Nightly and hourly counters, filtered and not, plus messages and undated."""
    per_night: Counter[str] = Counter()
    per_night_matched: Counter[str] = Counter()
    per_hour: Counter[tuple[str, int]] = Counter()
    per_hour_matched: Counter[tuple[str, int]] = Counter()
    messages = 0
    undated = 0
    for path in paths:
        body = path.read_text(encoding="utf-8", errors="replace")
        for block in _BLOCK.findall(body):
            time_match = _TIME.search(block)
            text_match = _TEXT.search(block)
            messages += 1
            stamp = _parse_timestamp(time_match.group(1)) if time_match else None
            if stamp is None:
                undated += 1
                continue
            night = _night_of(stamp, cutover_hour)
            hour = stamp.astimezone(UTC).hour
            per_night[night] += 1
            per_hour[(night, hour)] += 1
            if text_match is not None:
                lowered = _strip(text_match.group(1)).lower()
                if any(term in lowered for term in terms):
                    per_night_matched[night] += 1
                    per_hour_matched[(night, hour)] += 1
    return per_night, per_night_matched, per_hour, per_hour_matched, messages, undated


def _busiest_hour(per_hour: Counter[tuple[str, int]]) -> Counter[str]:
    """Each night's busiest clock hour, as a count.

    The maximum rather than the mean: a night with one violent hour and eleven
    quiet ones is the shape being looked for, and a mean would erase exactly
    that night.
    """
    peaks: Counter[str] = Counter()
    for (night, _hour), count in per_hour.items():
        if count > peaks[night]:
            peaks[night] = count
    return peaks


def _sweep(per_night: Counter[str], nights: int, label: str,
           thresholds: tuple[int, ...] = (1, 5, 10, 20, 30, 40, 60, 80, 120, 160, 200)) -> None:
    if nights == 0:
        print(f"  {label}: no nights, nothing to sweep")
        return
    print("  threshold  nights  share   firings/week")
    for threshold in thresholds:
        above = sum(1 for count in per_night.values() if count >= threshold)
        share = above / nights
        print(f"  >= {threshold:<7} {above:<7} {share:6.1%}  {share * 7:.2f}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", required=True, help="directory of raw page snapshots")
    parser.add_argument("--cutover-hour", type=int, default=15,
                        help="UTC hour at which a new night begins (default 15)")
    parser.add_argument("--terms", help="file of area terms, one per line, UTF-8")
    args = parser.parse_args(argv)

    directory = Path(args.corpus)
    if not directory.is_dir():
        print(f"threshold-sweep: {directory} is not a directory", file=sys.stderr)
        return 2

    boundary = _boundary()
    pages, refused = _design_pages(directory, boundary)
    if not pages:
        print("threshold-sweep: no pages below the boundary. Nothing measured, and "
              "that is a finding rather than a zero", file=sys.stderr)
        return 1

    terms: tuple[str, ...] = DEFAULT_WEST_TERMS
    if args.terms:
        loaded = [
            line.strip().lower()
            for line in Path(args.terms).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        terms = tuple(loaded)

    per_night, matched, per_hour, hour_matched, messages, undated = _read(
        pages, args.cutover_hour, terms
    )
    peaks = _busiest_hour(per_hour)
    peaks_matched = _busiest_hour(hour_matched)
    nights = len(per_night)
    matched_total = sum(matched.values())

    print("threshold-sweep [measured, over the design window only]")
    print(f"  pages read           {len(pages)}")
    print(f"  pages refused        {refused} (above the frozen boundary {boundary}, D-012a)")
    print(f"  messages read        {messages}")
    print(f"  messages undated     {undated}" if undated else "  messages undated     0")
    print(f"  nights covered       {nights}")
    print(f"  night cutover hour   {args.cutover_hour}:00 UTC")
    print(f"  area terms           {len(terms)}")
    print(f"  term coverage        {matched_total}/{messages} messages "
          f"({matched_total / messages:.2%})" if messages else "  term coverage unknown")
    print()

    print("A. messages per night, no classifier needed [measured]")
    _sweep(per_night, nights, "volume")
    print()

    print("B. busiest hour of the night, no classifier needed [measured]")
    print("   The nightly axis measured flat on real data, so this is the one that")
    print("   can still separate: a night with one violent hour is the shape.")
    _sweep(peaks, nights, "hourly peak")
    print()

    if matched_total == 0:
        print("C. area-filtered: no message matched any term.")
        print("   This is F23 reporting itself, not a property of the nights: the")
        print("   channel names raions and hromadas, the terms name oblasts. The")
        print("   filtered sweep is unavailable until the sprint 7 redesign, and")
        print("   printing zeros here would be a measurement of nothing.")
    else:
        print("C. area-filtered, per night [measured, coverage above]")
        _sweep(matched, nights, "filtered")
        print()
        print("D. area-filtered, busiest hour [measured, coverage above]")
        print("   Read C and D against the coverage figure. A filter matching one")
        print("   message in a hundred measures the nights on which the channel")
        print("   happened to name an oblast, which is not the same population as")
        print("   the nights of western activity.")
        _sweep(peaks_matched, nights, "filtered peak", thresholds=(1, 2, 3, 5, 8, 10, 15, 20, 30))
    print()
    print("Recall is not measured here and no threshold below is affordable until")
    print("it is: this tool knows nothing about which nights carried a crossing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
