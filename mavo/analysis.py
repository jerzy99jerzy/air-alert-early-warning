"""Weeks set against weeks: what `analysis.json` carries (D-064).

**The question.** On 2026-10-18 the operator asked for a page that sets the
last weeks of the Ukrainian alarm record beside the weeks before them, with the
reader choosing how many of each as far back as ninety days, and that shows
what happened in Ukraine whenever RCB raised an air alert in Poland. The live
files cannot answer it: `state.json` is a moment, `timeline.json` is a week,
and a week has nothing to be compared with.

**Every figure the page prints is computed here.** The site selects a block of
this file, formats it and maps it to pixels; it adds, divides and ranks nothing
(D-S97 there). So every choice the page offers, each pair of "the last n
weeks" and "the m weeks before them", arrives as its own comparison, and a
choice the file does not carry is a choice the page cannot make. The cost is a
file of a few hundred kilobytes written once an hour, which is cheaper than a
second implementation of a median in another repository.

**What is compared, and why only that.**

* **The band.** The 26 raions of the area table whose nearer edge lies within
  150 km of the Polish border, five of them touching it. A rate summed over
  raions would measure how finely an oblast is subdivided (F76), so the band is
  counted as a whole: an *episode* starts when the band goes from no alarm in
  any raion to an alarm in one.
* **Per observed minute.** A minute this record did not see counts in neither
  numerator nor denominator, so a week with an outage is not a quiet week.
  Unseen is the union of four things: before the first change the window
  holds; a pipe's coverage gap by the live rule (`timeline.feed_coverage`); a
  stretch of `SILENCE_MIN` or more with no change anywhere in Ukraine, which is
  a source that said nothing rather than a quiet country; and a minute in which
  a raion of the band stood in a state that is not a reading.
* **One instrument at a time.** The channel until D-040's switch, the API after
  it. An onset never straddles the switch, and every week says which
  instrument measured it, so a background that reaches into August says so
  instead of pooling the two silently (F155).
* **Calendar weeks**, Monday to Sunday in Warsaw time, the current one cut at
  the file's own moment. A week with less than half of itself observed is not
  usable and is never compared.

**RCB, from the register's own walk.** An alert is an alert of `pl_rcb_recent`
(D-062), read over the whole window: what painted is the composer's, and the
stretches in which the list was not read are its `unread`, which here is a hole
in the denominator rather than a week without alerts. How often the list was
read is measured from the reads themselves and never assumed. A comparison of
weekly RCB counts that mixes a coarse cadence with a fine one is not assessed,
because a short alert can slip between two reads fifteen minutes apart and not
between two reads a minute apart.

**What the file refuses to say.** No probability, no projection, no fitted
model of the war. A comparison is a verdict against the range of the chosen
background weeks, in five words. The speed under `rings` is the apparent speed
at which areas *declared* alarms, never the speed of anything flying.
"""

from __future__ import annotations

import bisect
import math
import random
import statistics
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from mavo import rcb_recent
from mavo.areas import AreaTable, oblast_slug
from mavo.liveness import FeedSpec
from mavo.schema import ThreatEvent
from mavo.store import EventStore
from mavo.timeline import area_layer, feed_coverage

#: The file's own version, apart from `state.json`'s and `timeline.json`'s:
#: the three are read by different code and change for different reasons.
ANALYSIS_VERSION = 1

#: Weeks, days and hours are Warsaw's. The page is read in Poland, and a week
#: that started on a Kyiv Monday would split a Polish Sunday night in two.
ZONE = ZoneInfo("Europe/Warsaw")

#: The current week and the twelve before it: at most 91 days, the operator's
#: ninety days rounded out to whole weeks.
WEEKS = 13

#: The band, by the nearer edge of each raion's distance interval.
BAND_KM = 150.0

#: A stretch with no change anywhere in Ukraine at least this long, outside a
#: read gap, is a source saying nothing. The longest quiet stretch outside gaps
#: and silences in the record of 2026-08-11 to 2026-10-18 is 135 minutes
#: [measured on the production export of 2026-10-18], so the threshold sits
#: above anything the record has produced while it was speaking.
SILENCE_MIN = 180

#: Half a week observed, or the week is not compared.
USABLE_SEEN_MIN = 7 * 1440 // 2

#: An hour of a day enters the hour-of-day profile with this much of it seen.
HOUR_SEEN_MIN = 30

#: The rings east of the band: the latest onset in each 75 km ring at most this
#: many minutes before the band's own onset, with the record unbroken between.
RING_EDGES_KM: tuple[int, ...] = (150, 225, 300, 375, 450, 525, 600)
LEAD_WINDOW_MIN = 360

#: The straight line is fitted through the rings up to here; further east the
#: alarm has usually been running for hours and the leads stop ordering.
FIT_UPTO_KM = 450

#: Resampling of a group's episodes for the spread of the fitted speed, seeded
#: per group, so the same choice of weeks always prints the same interval.
RESAMPLES = 300
SEED = 20261018

#: Around every RCB alert: minutes before and after it, and the step.
EVENT_FROM_MIN, EVENT_TO_MIN, EVENT_STEP_MIN = -180, 120, 5

#: Breaks shorter than these do not separate two episodes, for the check that
#: the verdict on episodes does not hang on how an episode is cut.
MERGES_MIN: tuple[int, ...] = (10, 30, 60)

#: A day with at least this much alarm in the band is a long day, and a day
#: counts as wholly observed with this share of it seen.
LONG_DAY_MIN = 8 * 60
FULL_DAY_SHARE = 0.95

#: A run of long days closing the recent weeks is worth a sentence from this
#: many days; shorter, the page says nothing about it.
STREAK_MIN_DAYS = 3

#: Reads of the RSO list at most this far apart are a fine cadence; further
#: apart, up to the pipe's own outage threshold, a coarse one; past it, a hole.
#: A week with more than `COARSE_WEEK_MIN` minutes under coarse reads was read
#: at the coarse cadence. A cadence run shorter than `CADENCE_RUN_MIN_H` hours
#: is a hiccup inside another cadence and is not reported as a cadence.
RSO_FINE_READ_S = 120
COARSE_WEEK_MIN = 60
CADENCE_RUN_MIN_H = 6

#: The reader's choice: one to four recent weeks, at least two background
#: weeks, and the page opens on two against five where the record allows it.
CURRENT_MAX = 4
BASELINE_MIN = 2
DEFAULT_CHOICE = (2, 5)

#: The rules set against the RCB record: at least k raions of the band under
#: alarm at once, and an alarm in a raion touching the border.
RULE_KS: tuple[int, ...] = tuple(range(1, 11))

#: A rule near the ideal corner: preceding three alerts in four, at most one
#: idle waking every two days. Only says whether the page may write that none
#: of the simple rules is; it scores nothing.
RULE_NEAR_RECALL = 0.75
RULE_NEAR_IDLE_PER_DAY = 0.5

#: The waiting-time curve, printed at this many log-spaced points from one
#: minute to `WAIT_GRID_TOP_MIN`.
WAIT_GRID_POINTS = 81
WAIT_GRID_TOP_MIN = 3000

#: The breaks counted into these lengths, in minutes, for the page's bars: the
#: edges a reader reads without a scale (ten minutes, half an hour, an hour,
#: two, six, twelve, a day), and two and twelve hours among them because the
#: sentence about bursts is told at those two lengths. The last has no end.
WAIT_BUCKETS_MIN: tuple[int, ...] = (0, 10, 30, 60, 120, 360, 720, 1440)

#: A stretch of the record shorter than this is not listed among the gaps.
GAP_LISTED_MIN = 5

#: Word choices the page makes from figures, decided here so the page decides
#: none: a raion whose daily hours grew by this much has more alarm (and by
#: the second figure, much more); the page names the oblasts of the first
#: `RAION_LEAD` raions; two medians of the lead before an RCB alert this close
#: are the same lead; and an hour of day this close to the background's share
#: is about the same hour.
RAION_RISING_H = 0.05
RAION_STRONG_H = 0.5
RAION_LEAD = 6
SINCE_CLOSE_MIN = 5.0
HOURS_CLOSE = 0.10

#: The page may say "about k times as often as usual" of the oblasts most often
#: under alarm at a voivodeship's alerts only when every one of them is at
#: least this many times its ordinary share: below it the rounded figure would
#: read "1 time as often", and the page prints the two shares instead.
OBLAST_RATIO_MIN = 1.5

#: The six measures, in the order the page prints them.
METRICS: tuple[str, ...] = ("episodes", "band_h", "duration", "breadth", "border_h", "rcb")

#: Five verdicts, and the three words for a comparison that is not made.
VERDICTS: tuple[str, ...] = ("all_above", "some_above", "in_range", "some_below",
                             "all_below", "thin", "not_computable", "not_assessed")

#: Every mask below is a Python integer whose bit i is the i-th minute of the
#: window. Counting a stretch is a shift and a `bit_count`.
Mask = int


def _bits(spans: Iterable[tuple[int, int]]) -> Mask:
    mask = 0
    for a, b in spans:
        if b > a:
            mask |= ((1 << (b - a)) - 1) << a
    return mask


def _count(mask: Mask, a: int, b: int) -> int:
    if b <= a:
        return 0
    return ((mask >> a) & ((1 << (b - a)) - 1)).bit_count()


def _merge(spans: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    """Half-open minute spans joined where they touch or overlap."""
    out: list[tuple[int, int]] = []
    for a, b in sorted(spans):
        if b <= a:
            continue
        if out and a <= out[-1][1]:
            if b > out[-1][1]:
                out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def _runs(flags: bytearray) -> list[tuple[int, int]]:
    """The runs of non-zero bytes, as half-open spans."""
    out: list[tuple[int, int]] = []
    start: int | None = None
    for i, flag in enumerate(flags):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(flags)))
    return out


def _r(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(float(value), digits)


def _median(values: Sequence[float]) -> float | None:
    return float(statistics.median(values)) if values else None


def _quantile(values: Sequence[float], q: float) -> float | None:
    """Linear between the two nearest order statistics."""
    if not values:
        return None
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def _fit(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float] | None:
    """Least-squares slope and intercept, or None where the line is undefined."""
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / sxx
    return slope, my - slope * mx


def _instant(text: object) -> datetime | None:
    """An ISO stamp with an offset as an instant; anything else is None."""
    if not isinstance(text, str):
        return None
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    return moment.astimezone(UTC) if moment.tzinfo is not None else None


def _local_midnight(day: date) -> datetime:
    """Midnight in Warsaw, which no change of clocks ever touches."""
    return datetime(day.year, day.month, day.day, tzinfo=ZONE).astimezone(UTC)


def _day_of(stamp: str) -> date:
    return datetime.fromisoformat(stamp).astimezone(ZONE).date()


@dataclass(frozen=True, slots=True)
class BandRaion:
    """One raion of the band, from the area table."""

    code: str
    name: str
    oblast: str
    oblast_name: str
    km_lower: float
    km_upper: float

    @property
    def border(self) -> bool:
        return self.km_lower == 0

    def as_item(self) -> dict[str, object]:
        return {"code": self.code, "name": self.name, "oblast": self.oblast,
                "oblast_name": self.oblast_name, "km_lower": self.km_lower,
                "km_upper": self.km_upper, "border": self.border}


def band_raions(table: AreaTable, km: float = BAND_KM) -> tuple[BandRaion, ...]:
    """The band, nearest the border first: every raion whose nearer edge is within `km`.

    Read from the table rather than from what the window happened to hold, so a
    raion that stayed quiet is in the band as a raion without an alarm instead
    of missing from it.
    """
    found: dict[str, BandRaion] = {}
    for tag in table.tags:
        area = table.resolve(tag)
        if (area is None or area.unit != "P" or area.border_lower_km is None
                or area.border_upper_km is None or area.border_lower_km >= km):
            continue
        found[area.code] = BandRaion(area.code, area.name, oblast_slug(area.oblast), area.oblast,
                                     area.border_lower_km, area.border_upper_km)
    return tuple(sorted(found.values(), key=lambda r: (r.km_lower, r.km_upper, r.name)))


@dataclass(frozen=True, slots=True)
class Inputs:
    """What one analysis is computed from, read from the store once.

    Kept apart from the store so that the arithmetic below can be held to a
    window written by hand, and so that `read_inputs` is the only part of this
    module that opens anything.
    """

    start: datetime
    end: datetime
    #: `timeline.area_layer`'s places, and its spans as `(area_id, alert, from, to)`.
    places: Mapping[str, Mapping[str, Any]]
    spans: Sequence[tuple[str, str, datetime, datetime | None]]
    band: Sequence[BandRaion]
    #: When each Ukrainian pipe's attempts begin, and its gaps by the live rule.
    api_since: datetime | None
    channel_since: datetime | None
    api_gaps: Sequence[tuple[datetime, datetime | None]]
    channel_gaps: Sequence[tuple[datetime, datetime | None]]
    #: `rcb_recent.summarise` over the window, or None before any RSO poll.
    rcb: Mapping[str, Any] | None
    #: Every read of the RSO list in the window, the newest before it first.
    rso_reads: Sequence[datetime]
    #: The RSO pipe's outage threshold, past which two reads are a hole.
    rso_silence_s: float


def window_start(end: datetime) -> datetime:
    """Monday 00:00 in Warsaw, `WEEKS - 1` weeks before the week of the window's last minute.

    The last minute and not `end` itself: a file written in the first minute of
    a Monday would otherwise open a week no minute long, which `_weeks` drops,
    and carry twelve weeks under a window that says thirteen.
    """
    local = (end - timedelta(minutes=1)).astimezone(ZONE)
    monday = local.date() - timedelta(days=local.weekday(), weeks=WEEKS - 1)
    return _local_midnight(monday)


def read_inputs(store: EventStore, events: Iterable[ThreatEvent], end: datetime, *,
                table: AreaTable, feeds: Sequence[FeedSpec]) -> Inputs:
    """The window ending at `end`, read from the store and the replayed log."""
    start = window_start(end)
    layer = area_layer(events, start, end, table)
    spec = {entry.feed: entry for entry in feeds}
    api = feed_coverage(store, spec["ukrainealarm"], start, end)
    channel = feed_coverage(store, spec["channel"], start, end)
    silence_s = spec["rso"].silence_is_an_outage_s
    rec = rcb_recent.record(store, start, end)
    summary = rcb_recent.summarise(rec, start, end,
                                   hours=int((end - start).total_seconds() // 3600),
                                   silence_s=silence_s)
    return Inputs(
        start=start, end=end, places=layer.places,
        spans=[(span.area_id, str(span.standing.get("alert")), span.span.start, span.span.end)
               for span in layer.spans],
        band=band_raions(table),
        api_since=api.recorded_since, channel_since=channel.recorded_since,
        api_gaps=[(gap.start, gap.end) for gap in api.gaps],
        channel_gaps=[(gap.start, gap.end) for gap in channel.gaps],
        rcb=summary, rso_reads=tuple(rec.reads), rso_silence_s=silence_s,
    )


def build(store: EventStore, events: Iterable[ThreatEvent], end: datetime, *,
          table: AreaTable, feeds: Sequence[FeedSpec]) -> dict[str, object]:
    """The whole file for the window ending at `end`."""
    return analyse(read_inputs(store, events, end, table=table, feeds=feeds))


# ---- the minute record


class _Record:
    """The window as minutes: who was under alarm, what was seen, by which pipe."""

    def __init__(self, src: Inputs) -> None:
        self.src = src
        self.start = src.start
        n = self.total = self.minute(src.end)
        self.full: Mask = (1 << n) - 1
        self._areas(src)
        self._coverage(src)
        self._counts()
        self._rcb(src)

    def minute(self, moment: datetime) -> int:
        return (moment - self.start) // timedelta(minutes=1)

    def iso(self, minute: int) -> str:
        """A minute of the window on the Warsaw clock, to the minute."""
        moment = self.start + timedelta(minutes=minute)
        return moment.astimezone(ZONE).isoformat(timespec="minutes")

    def seen_through(self, a: int, b: int) -> bool:
        """Every minute of `[a, b)` observed."""
        a, b = max(0, a), min(self.total, b)
        return b <= a or self.seen_at.count(0, a, b) == 0

    def _areas(self, src: Inputs) -> None:
        n = self.total
        active: dict[str, list[tuple[int, int]]] = {}
        unclear: dict[str, list[tuple[int, int]]] = {}
        boundaries: set[int] = set()
        for area_id, alert, begin, finish in src.spans:
            a = self.minute(begin)
            b = n if finish is None else self.minute(finish)
            boundaries.add(a)
            if finish is not None:
                boundaries.add(b)
            a, b = max(0, a), min(n, b)
            if b > a:
                (active if alert == "active" else unclear).setdefault(area_id, []).append((a, b))
        #: Every moment at which some area of Ukraine changed, inside the window.
        self.boundaries = sorted(x for x in boundaries if 0 < x < n)

        def code_of(area_id: str) -> str:
            return str((src.places.get(area_id) or {}).get("katottg") or area_id)

        index = {raion.code: k for k, raion in enumerate(src.band)}
        band: list[list[tuple[int, int]]] = [[] for _ in src.band]
        unclear_band: list[tuple[int, int]] = []
        for area_id, spans in active.items():
            k = index.get(code_of(area_id))
            if k is not None:
                band[k].extend(spans)
        for area_id, spans in unclear.items():
            if code_of(area_id) in index:
                unclear_band.extend(spans)
        self.band_spans = [_merge(spans) for spans in band]
        self.band_bits = [_bits(spans) for spans in self.band_spans]
        self.band_runs = _merge(span for spans in self.band_spans for span in spans)
        self.band_any: Mask = _bits(self.band_runs)
        border = [k for k, raion in enumerate(src.band) if raion.border]
        self.border_runs = _merge(span for k in border for span in self.band_spans[k])
        self.border_any: Mask = _bits(self.border_runs)
        self.unclear_spans = _merge(unclear_band)

        rings: list[list[tuple[int, int]]] = [[] for _ in RING_EDGES_KM[1:]]
        edges = list(zip(RING_EDGES_KM, RING_EDGES_KM[1:], strict=False))
        for area_id, spans in active.items():
            km = (src.places.get(area_id) or {}).get("border_km_lower")
            if isinstance(km, bool) or not isinstance(km, (int, float)):
                continue
            for r, (lo, hi) in enumerate(edges):
                if lo <= km < hi:
                    rings[r].extend(spans)
        #: Per ring, the minutes at which its alarm began after a minute without one.
        self.ring_onsets = [[a for a, _b in _merge(spans)] for spans in rings]

    def _coverage(self, src: Inputs) -> None:
        n = self.total
        self.switch = n if src.api_since is None else min(n, max(0, self.minute(src.api_since)))
        self.api: Mask = self.full & ~((1 << self.switch) - 1)
        self.gap_spans = _merge(self._clip(src.channel_gaps, 0, self.switch)
                                + self._clip(src.api_gaps, self.switch, n))
        gap_bits = _bits(self.gap_spans)
        self.record_from = self.boundaries[0] if self.boundaries else n
        marks = self.boundaries + [n]
        self.silence_spans = [
            (x, y) for x, y in zip(marks, marks[1:], strict=False)
            if y - x >= SILENCE_MIN and (y - x) - _count(gap_bits, x, y) >= SILENCE_MIN
        ]
        blind = _merge(self.gap_spans + [(0, self.record_from)] + self.silence_spans
                       + self.unclear_spans)
        self.seen: Mask = self.full & ~_bits(blind)
        self.seen_at = bytearray(b"\x01") * n
        for a, b in blind:
            self.seen_at[a:b] = bytes(b - a)

    def _clip(self, spans: Sequence[tuple[datetime, datetime | None]], lo: int, hi: int
              ) -> list[tuple[int, int]]:
        out = []
        for begin, finish in spans:
            a = max(lo, self.minute(begin))
            b = min(hi, self.total if finish is None else self.minute(finish))
            if b > a:
                out.append((a, b))
        return out

    def _counts(self) -> None:
        n = self.total
        diff = [0] * (n + 1)
        for spans in self.band_spans:
            for a, b in spans:
                diff[a] += 1
                diff[b] -= 1
        count = [0] * n
        running = 0
        for i in range(n):
            running += diff[i]
            count[i] = running
        #: How many raions of the band were under alarm, minute by minute.
        self.band_n = count
        self.band_at = bytearray(1 if c else 0 for c in count)
        self.border_at = bytearray(n)
        for a, b in self.border_runs:
            self.border_at[a:b] = b"\x01" * (b - a)
        #: The minutes at which the band's alarm began after a minute without
        #: one, both minutes observed and measured by one instrument: the start
        #: of a run of the band's alarm, since the runs are merged.
        self.onsets = [a for a, _b in self.band_runs
                       if a > 0 and a != self.switch and self.seen_at[a] and self.seen_at[a - 1]]
        self.onset_set = frozenset(self.onsets)
        self.seen_api = self.seen & self.api
        self.band_seen = self.band_any & self.seen
        self.border_seen = self.border_any & self.seen
        self.raion_seen = [bits & self.seen for bits in self.band_bits]

    def _rcb(self, src: Inputs) -> None:
        n = self.total
        self.alerts: list[dict[str, Any]] = []
        self.rcb_first: int | None = None
        self.rcb_seen: Mask = 0
        self.rcb_unread: list[tuple[int, int]] = []
        self.coarse: Mask = 0
        self.cadence: list[dict[str, Any]] = []
        reads = list(src.rso_reads)
        summary = src.rcb
        if summary is None:
            return
        first = _instant(summary["recorded_since"])
        if first is None:
            return
        self.rcb_first = min(n, max(0, self.minute(first)))
        unread = []
        for stretch in summary["unread"]:
            begin = _instant(stretch["from"])
            finish = _instant(stretch["to"])
            if begin is None:
                continue
            unread.append((max(0, self.minute(begin)),
                           n if finish is None else min(n, self.minute(finish))))
        self.rcb_unread = _merge(unread)
        self.rcb_seen = self.full & ~((1 << self.rcb_first) - 1) & ~_bits(self.rcb_unread)
        self._cadence(reads, src.rso_silence_s)
        for row in summary["voivodeships"]:
            for alert in row["alerts"]:
                painted = [moment for moment in (_instant(p["from"]) for p in alert["painted"])
                           if moment is not None]
                if not painted:
                    continue
                listed = min(painted)
                declared = _instant(alert.get("valid_from"))
                anchor = declared if declared is not None else listed
                # Cut where every other count is cut, at the window's last
                # whole minute: an alert of the minute still running would be
                # listed here and counted in no week and no day.
                if not 0 <= self.minute(anchor) < n:
                    continue
                self.alerts.append({
                    "slug": str(row["slug"]), "voivodeship": str(row["voivodeship"]),
                    "id": str(alert["id"]), "valid_from": alert.get("valid_from"),
                    "anchor": anchor, "minute": self.minute(anchor),
                    "declared": declared is not None, "listed": listed,
                    "read_every_s": _spacing(reads, anchor),
                })
        self.alerts.sort(key=lambda a: (a["anchor"], a["slug"], a["id"]))

    def _cadence(self, reads: Sequence[datetime], silence_s: float) -> None:
        """How often the RSO list was read, as runs of one cadence."""
        runs: list[list[Any]] = []
        coarse: list[tuple[int, int]] = []
        for before, after in zip(reads, reads[1:], strict=False):
            spacing = (after - before).total_seconds()
            if spacing > silence_s:
                continue
            kind = "fine" if spacing <= RSO_FINE_READ_S else "coarse"
            if kind == "coarse":
                coarse.append((max(0, self.minute(before)), min(self.total, self.minute(after))))
            if runs and runs[-1][0] == kind and runs[-1][2] == before:
                runs[-1][2] = after
                runs[-1][3].append(spacing)
            else:
                runs.append([kind, before, after, [spacing]])
        self.coarse = _bits(_merge(coarse))
        kept: list[list[Any]] = []
        for run in runs:
            if run[2] - run[1] < timedelta(hours=CADENCE_RUN_MIN_H):
                continue
            if kept and kept[-1][0] == run[0]:
                kept[-1][2] = run[2]
                kept[-1][3].extend(run[3])
            else:
                kept.append(run)
        self.cadence = [
            {"cadence": kind, "from": begin.astimezone(ZONE).isoformat(timespec="minutes"),
             "to": finish.astimezone(ZONE).isoformat(timespec="minutes"),
             "every_s": round(statistics.median(spacings))}
            for kind, begin, finish, spacings in kept
        ]


def _spacing(reads: Sequence[datetime], moment: datetime) -> int | None:
    """Seconds between the read at or before `moment` and the read after it."""
    index = bisect.bisect_right(reads, moment) - 1
    if index < 0 or index + 1 >= len(reads):
        return None
    return round((reads[index + 1] - reads[index]).total_seconds())


def _cadence_of(spacing: int | None, silence_s: float) -> str | None:
    if spacing is None:
        return None
    if spacing <= RSO_FINE_READ_S:
        return "fine"
    return "coarse" if spacing <= silence_s else "unread"


# ---- stretches: weeks and days


@dataclass(slots=True)
class _Stretch:
    """A stretch of the window and the sums every measure is made of."""

    a: int
    b: int
    first_day: date
    last_day: date
    minutes: int = 0
    seen: int = 0
    api: int = 0
    band: int = 0
    border: int = 0
    raion: int = 0
    episodes: int = 0
    rcb_seen: int = 0
    rcb: int = 0
    coarse: int = 0
    #: The stretch's own length on the calendar, which the window may cut.
    length: int = 0
    raions: list[int] = field(default_factory=list)
    rcb_by: dict[str, int] = field(default_factory=dict)

    @property
    def channel(self) -> int:
        return self.seen - self.api


_SUMMED = ("minutes", "seen", "api", "band", "border", "raion", "episodes", "rcb_seen", "rcb",
           "coarse")


def _measure(rec: _Record, a: int, b: int, first_day: date, last_day: date,
             length: int) -> _Stretch:
    s = _Stretch(a, b, first_day, last_day, minutes=b - a, length=length)
    s.seen = _count(rec.seen, a, b)
    s.api = _count(rec.seen_api, a, b)
    s.band = _count(rec.band_seen, a, b)
    s.border = _count(rec.border_seen, a, b)
    s.raions = [_count(bits, a, b) for bits in rec.raion_seen]
    s.raion = sum(s.raions)
    s.episodes = bisect.bisect_left(rec.onsets, b) - bisect.bisect_left(rec.onsets, a)
    s.rcb_seen = _count(rec.rcb_seen, a, b)
    for alert in rec.alerts:
        if a <= alert["minute"] < b:
            s.rcb += 1
            s.rcb_by[alert["slug"]] = s.rcb_by.get(alert["slug"], 0) + 1
    s.coarse = _count(rec.coarse & rec.rcb_seen, a, b)
    return s


def _pool(stretches: Sequence[_Stretch]) -> _Stretch:
    out = _Stretch(stretches[0].a, stretches[-1].b, stretches[0].first_day,
                   stretches[-1].last_day)
    out.raions = [0] * len(stretches[0].raions)
    for s in stretches:
        for name in _SUMMED:
            setattr(out, name, getattr(out, name) + getattr(s, name))
        out.raions = [x + y for x, y in zip(out.raions, s.raions, strict=True)]
    return out


def _value(key: str, s: _Stretch, *, pooled: bool = False) -> float | None:
    """One measure of a stretch, or None where the stretch cannot carry it.

    A week carries a measure with half of itself observed, and RCB's with half
    of itself read; a pooled stretch of several weeks is held to a day of RSO
    reads, since each week in it was already held to its own floor.
    """
    if key == "rcb":
        floor = 1440 if pooled else USABLE_SEEN_MIN
        return s.rcb / s.rcb_seen * 7 * 1440 if s.rcb_seen >= floor else None
    if not pooled and s.seen < USABLE_SEEN_MIN:
        return None
    if key == "episodes":
        return s.episodes / s.seen * 1440 if s.seen else None
    if key == "band_h":
        return s.band / s.seen * 24 if s.seen else None
    if key == "duration":
        return s.band / s.episodes if s.episodes else None
    if key == "breadth":
        return s.raion / s.band if s.band else None
    if key == "border_h":
        return s.border / s.seen * 24 if s.seen else None
    raise KeyError(key)


def _cadence_class(s: _Stretch) -> str | None:
    if s.rcb_seen == 0:
        return None
    return "coarse" if s.coarse > COARSE_WEEK_MIN else "fine"


def _weeks(rec: _Record) -> list[_Stretch]:
    first = rec.start.astimezone(ZONE).date()
    out = []
    for w in range(WEEKS):
        monday = first + timedelta(weeks=w)
        a = rec.minute(_local_midnight(monday))
        if a >= rec.total:
            break
        whole = rec.minute(_local_midnight(monday + timedelta(weeks=1)))
        out.append(_measure(rec, a, min(rec.total, whole), monday,
                            monday + timedelta(days=6), whole - a))
    return out


def _days(rec: _Record) -> list[_Stretch]:
    first = rec.start.astimezone(ZONE).date()
    out = []
    day = first
    while True:
        a = rec.minute(_local_midnight(day))
        if a >= rec.total:
            break
        whole = rec.minute(_local_midnight(day + timedelta(days=1)))
        out.append(_measure(rec, a, min(rec.total, whole), day, day, whole - a))
        day += timedelta(days=1)
    return out


def _hour_cells(rec: _Record) -> dict[tuple[date, int], list[int]]:
    """Per Warsaw day and hour: minutes seen, and minutes seen with a band alarm.

    Walked in UTC hours. Warsaw's offset is a whole number of hours, so every UTC
    hour is one Warsaw hour, and the doubled hour of an October night adds into
    one cell.
    """
    cells: dict[tuple[date, int], list[int]] = {}
    moment = rec.start
    while moment < rec.src.end:
        a = rec.minute(moment)
        b = min(rec.total, rec.minute(moment + timedelta(hours=1)))
        local = moment.astimezone(ZONE)
        cell = cells.setdefault((local.date(), local.hour), [0, 0])
        cell[0] += _count(rec.seen, a, b)
        cell[1] += _count(rec.band_seen, a, b)
        moment += timedelta(hours=1)
    return cells


# ---- episodes, the waits between them, and what came before them


def _episodes(rec: _Record) -> list[dict[str, Any]]:
    anchors = [alert["minute"] for alert in rec.alerts]
    n = rec.total
    out = []
    for a, b in rec.band_runs:
        if a not in rec.onset_set:
            continue
        censored = (not rec.seen_through(a, b) or b >= n or not rec.seen_at[b]
                    or a < rec.switch <= b)
        peak = max((rec.band_n[i] for i in range(a, b) if rec.seen_at[i]), default=None)
        leads: list[int | None] = []
        for onsets in rec.ring_onsets:
            k = bisect.bisect_right(onsets, a) - 1
            ok = k >= 0 and a - onsets[k] <= LEAD_WINDOW_MIN and rec.seen_through(onsets[k], a + 1)
            leads.append(a - onsets[k] if ok else None)
        rcb = any(a <= t < b for t in anchors)
        out.append({
            "start": rec.iso(a), "end": rec.iso(b), "minute": a, "end_minute": b,
            "minutes": b - a, "censored": censored,
            "source": "api" if a >= rec.switch else "channel",
            "peak_raions": peak, "border": bool(_count(rec.border_any, a, b)),
            "rcb": rcb,
            # "Without an RCB alert" is a reading only if the list was read for
            # every minute of the episode; an alert that was seen is one
            # whatever the reads around it.
            "rcb_recorded": rcb or _count(rec.rcb_seen, a, b) == b - a,
            "leads": leads,
        })
    return out


def _waits(rec: _Record, episodes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Every break between two episodes that the record saw from end to end."""
    out = []
    for one, two in zip(episodes, episodes[1:], strict=False):
        if one["censored"] or one["source"] != two["source"]:
            continue
        a, b = one["end_minute"], two["minute"]
        if b <= a or not rec.seen_through(a, b):
            continue
        out.append({"before": two["start"], "minutes": b - a, "source": two["source"]})
    return out


def _merged_onsets(rec: _Record, merge: int) -> list[int]:
    """The onsets no band alarm preceded within `merge` minutes."""
    out = []
    for k, (a, _b) in enumerate(rec.band_runs):
        if a not in rec.onset_set:
            continue
        if k and rec.band_runs[k - 1][1] > a - merge:
            continue
        out.append(a)
    return out


# ---- RCB alerts against the Ukrainian picture


def _alert_rows(rec: _Record) -> list[dict[str, Any]]:
    band = rec.src.band
    out = []
    for alert in rec.alerts:
        t = alert["minute"]
        seen = 0 <= t < rec.total and bool(rec.seen_at[t])
        series = [rec.band_n[t + d] if 0 <= t + d < rec.total and rec.seen_at[t + d] else None
                  for d in range(EVENT_FROM_MIN, EVENT_TO_MIN + 1, EVENT_STEP_MIN)]
        on = [k for k, bits in enumerate(rec.band_bits) if seen and (bits >> t) & 1]
        nearest = min(on, key=lambda k: (band[k].km_lower, band[k].km_upper)) if on else None
        since = None
        if seen and rec.band_at[t]:
            m = t
            while m > 0 and rec.band_at[m - 1] and rec.seen_at[m - 1]:
                m -= 1
            since = {"at": rec.iso(m), "minutes_before": t - m,
                     "cut_by_gap": bool(m > 0 and not rec.seen_at[m - 1])}
        # Measured from the time the communique gives. Without one the anchor
        # is the listing itself, and "seen 0 minutes after" would be a zero
        # printed for an unknown.
        seen_after = ((alert["listed"] - alert["anchor"]).total_seconds() / 60
                      if alert["declared"] else None)
        out.append({
            "at": rec.iso(t), "valid_from": alert["valid_from"], "declared": alert["declared"],
            "voivodeship": alert["voivodeship"], "slug": alert["slug"], "id": alert["id"],
            "seen_after_min": _r(seen_after, 1), "read_every_s": alert["read_every_s"],
            "read_cadence": _cadence_of(alert["read_every_s"], rec.src.rso_silence_s),
            "band_raions_at_alert": rec.band_n[t] if seen else None,
            "border_at_alert": bool(rec.border_at[t]) if seen else None,
            "nearest": nearest,
            "oblasts_at_alert": sorted({band[k].oblast for k in on}),
            "band_alarm_since": since,
            "band_raions_series": series,
        })
    return out


def _rules(rec: _Record) -> dict[str, Any] | None:
    """Simple rules held to the RCB record: how often they fire, and for what."""
    if rec.rcb_first is None:
        return None
    lo, n = rec.rcb_first, rec.total
    days = _count(rec.seen_api & rec.rcb_seen, lo, n) / 1440
    #: Every alert of the window, and those the band was observed at. Recall is
    #: asked of the second; whether a firing was idle, of the first, since an
    #: alert the band was not observed at is still an alert.
    moments = [a["minute"] for a in rec.alerts]
    anchors = [t for t in moments if rec.seen_at[t]]
    rules: list[dict[str, Any]] = []

    def judge(key: str, k: int | None, runs: Sequence[tuple[int, int]], on: bytearray) -> None:
        # A firing counts where the days are counted: begun at an observed
        # minute of the API's era after the RCB record began, with the list
        # read for every minute of it. One the list was not read through could
        # not have been seen to be idle, and counted as idle it would be
        # silence counted as an all-clear.
        firings = [(a, b) for a, b in runs
                   if a >= max(lo, rec.switch) and a > 0 and rec.seen_at[a] and rec.seen_at[a - 1]
                   and _count(rec.rcb_seen, a, b) == b - a]
        idle = sum(1 for a, b in firings if not any(a <= t < b for t in moments))
        covered = sum(1 for t in anchors if t > 0 and on[t] and on[t - 1])
        rules.append({
            "key": key, "k": k, "firings": len(firings), "idle": idle,
            "covered": covered, "alerts": len(anchors),
            "firings_per_day": _r(len(firings) / days, 3) if days else None,
            "idle_per_day": _r(idle / days, 3) if days else None,
            "recall": _r(covered / len(anchors), 4) if anchors else None,
        })

    for k in RULE_KS:
        on = bytearray(1 if c >= k else 0 for c in rec.band_n)
        judge(f"k{k}", k, _runs(on), on)
    judge("border", None, rec.border_runs, rec.border_at)
    border = rules[-1]
    match = next((r for r in rules[:-1] if r["covered"] == border["covered"]), None)
    return {
        "since": rec.iso(lo), "observed_days": _r(days, 2), "alerts": len(anchors),
        "alerts_without_reading": len(rec.alerts) - len(anchors), "rules": rules,
        # The count rule that precedes as many alerts as the border rule, and
        # how many times as many idle wakings it costs.
        "border_match": None if match is None else {
            "key": match["key"],
            "idle_ratio": (_r(match["idle"] / border["idle"], 2) if border["idle"] else None),
        },
        # Whether any rule sits near the corner an ideal rule would occupy.
        "any_near_ideal": any(
            r["recall"] is not None and r["idle_per_day"] is not None
            and r["recall"] >= RULE_NEAR_RECALL and r["idle_per_day"] <= RULE_NEAR_IDLE_PER_DAY
            for r in rules),
    }


def _oblasts(rec: _Record, alerts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Per oblast of the band: at how many alerts it was under alarm, and how often usually."""
    if rec.rcb_first is None:
        return []
    lo, n = rec.rcb_first, rec.total
    base = rec.seen_api & rec.rcb_seen
    whole = _count(base, lo, n)
    out = []
    for slug in dict.fromkeys(raion.oblast for raion in rec.src.band):
        bits = 0
        for k, raion in enumerate(rec.src.band):
            if raion.oblast == slug:
                bits |= rec.band_bits[k]
        share = _count(bits & base, lo, n) / whole if whole else None
        by: dict[str, dict[str, Any]] = {}
        for alert in alerts:
            if alert["band_raions_at_alert"] is None:
                continue
            row = by.setdefault(alert["slug"], {"alerts": 0, "with_alarm": 0})
            row["alerts"] += 1
            row["with_alarm"] += int(slug in alert["oblasts_at_alert"])
        for row in by.values():
            row["share"] = _r(row["with_alarm"] / row["alerts"], 4)
            row["to_minute_share"] = (_r(row["with_alarm"] / row["alerts"] / share, 2)
                                      if share else None)
        out.append({
            "oblast": slug,
            "oblast_name": next(r.oblast_name for r in rec.src.band if r.oblast == slug),
            "minute_share": _r(share, 4),
            "by_voivodeship": by,
        })
    return out


def _oblast_top(oblasts: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per voivodeship, the oblasts most often under alarm at its alerts.

    Every oblast that shares the highest count is named, in band order: a tie
    broken by the order of a list would print one oblast where the record holds
    two. No oblast is named when none was under alarm at any of the alerts.
    """
    top: dict[str, dict[str, Any]] = {}
    for row in oblasts:
        for slug, counts in row["by_voivodeship"].items():
            held = top.setdefault(slug, {"oblasts": [], "with_alarm": 0,
                                         "alerts": counts["alerts"], "ratios": []})
            k = counts["with_alarm"]
            if k <= 0 or k < held["with_alarm"]:
                continue
            if k > held["with_alarm"]:
                held["oblasts"], held["ratios"], held["with_alarm"] = [], [], k
            held["oblasts"].append(row["oblast"])
            held["ratios"].append(counts["to_minute_share"])
    for held in top.values():
        ratios = held.pop("ratios")
        held["well_above_usual"] = bool(ratios) and all(
            r is not None and r >= OBLAST_RATIO_MIN for r in ratios)
    return top


# ---- groups: a set of weeks and what the page describes about it


def _wait_grid() -> list[float]:
    top = math.log(WAIT_GRID_TOP_MIN)
    return [math.exp(top * i / (WAIT_GRID_POINTS - 1)) for i in range(WAIT_GRID_POINTS)]


def _waits_block(waits: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    xs = [float(w["minutes"]) for w in waits]
    if not xs:
        return None
    mean = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / len(xs))

    def longer(t: float) -> float:
        return sum(1 for x in xs if x > t) / len(xs)

    def at(t: float) -> dict[str, float | None]:
        return {"share": _r(longer(t), 4), "random": _r(math.exp(-t / mean), 4)}

    grid = _wait_grid()
    uppers: list[int | None] = [*WAIT_BUCKETS_MIN[1:], None]
    buckets = []
    for a, b in zip(WAIT_BUCKETS_MIN, uppers, strict=True):
        n = sum(1 for x in xs if x >= a and (b is None or x < b))
        chance = math.exp(-a / mean) - (0.0 if b is None else math.exp(-b / mean))
        buckets.append({"from_min": a, "to_min": b, "n": n, "share": _r(n / len(xs), 4),
                        "random": _r(chance, 4)})
    return {
        "n": len(xs), "mean": _r(mean, 1), "median": _r(_median(xs), 1),
        # Every break in one of the lengths, and the share a random arrival
        # of alerts with the same mean break would put there (exponential).
        "buckets": buckets,
        "cv": _r(sd / mean, 3), "max": int(max(xs)),
        "under_30_share": _r(sum(1 for x in xs if x < 30) / len(xs), 3),
        "longer": [_r(longer(t), 4) for t in grid],
        "random": [_r(math.exp(-t / mean), 4) for t in grid],
        "at_2h": at(120), "at_12h": at(720),
        # The shape the page names when both hold in both groups: fewer long
        # breaks than chance at two hours, more than chance at twelve.
        "fewer_over_2h": longer(120) < math.exp(-120 / mean),
        "more_over_12h": longer(720) > math.exp(-720 / mean),
    }


def _speed(episodes: Sequence[Mapping[str, Any]], rings: Sequence[Mapping[str, Any]]
           ) -> dict[str, Any] | None:
    """The straight line through the rings' medians, and its spread over resamples."""
    near = [r for r, ring in enumerate(rings) if ring["to_km"] <= FIT_UPTO_KM]
    mids = [(rings[r]["from_km"] + rings[r]["to_km"]) / 2 for r in near]
    xs = [mids[i] for i, r in enumerate(near) if rings[r]["median"] is not None]
    ys = [float(rings[r]["median"]) for r in near if rings[r]["median"] is not None]
    fitted = _fit(xs, ys) if len(xs) >= 3 else None
    if fitted is None:
        return None
    slope, intercept = fitted
    rng = random.Random(SEED)
    speeds = []
    for _ in range(RESAMPLES):
        pick = [episodes[int(rng.random() * len(episodes))] for _ in episodes]
        bx, by = [], []
        for i, r in enumerate(near):
            v = [float(e["leads"][r]) for e in pick if e["leads"][r] is not None]
            if v:
                bx.append(mids[i])
                by.append(float(statistics.median(v)))
        line = _fit(bx, by) if len(bx) >= 3 else None
        if line is not None and line[0] > 0:
            speeds.append(60 / line[0])
    return {
        "minutes_per_km": _r(slope, 5), "intercept_min": _r(intercept, 2),
        "km_per_h": _r(60 / slope, 1) if slope > 0 else None,
        "rings_used": len(xs), "upto_km": FIT_UPTO_KM,
        "km_per_h_p05": _r(_quantile(speeds, 0.05), 1),
        "km_per_h_p95": _r(_quantile(speeds, 0.95), 1),
        "resamples": len(speeds),
    }


def _rings_block(episodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rings = []
    for r, (lo, hi) in enumerate(zip(RING_EDGES_KM, RING_EDGES_KM[1:], strict=False)):
        v = [float(e["leads"][r]) for e in episodes if e["leads"][r] is not None]
        rings.append({"from_km": lo, "to_km": hi, "n": len(v), "of": len(episodes),
                      "median": _r(_median(v), 1), "p25": _r(_quantile(v, 0.25), 1),
                      "p75": _r(_quantile(v, 0.75), 1)})
    return {"rings": rings, "speed": _speed(episodes, rings)}


def _rcb_block(alerts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    points = len(range(EVENT_FROM_MIN, EVENT_TO_MIN + 1, EVENT_STEP_MIN))
    median, q1, q3, share, count = [], [], [], [], []
    for i in range(points):
        v = [float(a["band_raions_series"][i]) for a in alerts
             if a["band_raions_series"][i] is not None]
        count.append(len(v))
        median.append(_r(_median(v), 2))
        q1.append(_r(_quantile(v, 0.25), 2))
        q3.append(_r(_quantile(v, 0.75), 2))
        share.append(_r(sum(1 for x in v if x > 0) / len(v), 4) if v else None)
    read = [a for a in alerts if a["band_raions_at_alert"] is not None]
    since = [float(a["band_alarm_since"]["minutes_before"]) for a in read
             if a["band_alarm_since"] is not None]
    return {
        "alerts": len(alerts), "read": len(read),
        "with_band": sum(1 for a in read if a["band_raions_at_alert"]),
        "border": sum(1 for a in read if a["border_at_alert"]),
        "median_raions_at_alert": _r(_median([float(a["band_raions_at_alert"]) for a in read]), 1),
        "median_since_min": _r(_median(since), 1),
        "median": median, "q1": q1, "q3": q3, "share_any": share, "n": count,
    }


def _group(rec: _Record, weeks: Sequence[_Stretch], chosen: Sequence[int],
           episodes: Sequence[Mapping[str, Any]], waits: Sequence[Mapping[str, Any]],
           alerts: Sequence[Mapping[str, Any]],
           cells: Mapping[tuple[date, int], list[int]]) -> dict[str, Any]:
    picked = [weeks[w] for w in chosen]
    pooled = _pool(picked)
    days = {s.first_day + timedelta(days=d) for s in picked for d in range(7)}
    eps = [e for e in episodes if _day_of(e["start"]) in days]
    recorded = [e for e in eps if e["rcb_recorded"]]
    hours = [{"days": 0, "with_alarm": 0} for _ in range(24)]
    for (day, hour), (seen, alarm) in cells.items():
        if day in days and seen >= HOUR_SEEN_MIN:
            hours[hour]["days"] += 1
            hours[hour]["with_alarm"] += int(alarm > 0)
    seen_days = pooled.seen / 1440
    return {
        "weeks": list(chosen),
        "first_day": picked[0].first_day.isoformat(), "last_day": picked[-1].last_day.isoformat(),
        "seen_min": pooled.seen, "seen_days": _r(seen_days, 2),
        "episodes": {
            "count": len(eps),
            "per_day": _r(len(eps) / seen_days, 3) if seen_days else None,
            "median_minutes": _r(_median([float(e["minutes"]) for e in eps]), 1),
            "median_peak": _r(_median([float(e["peak_raions"]) for e in eps
                                       if e["peak_raions"] is not None]), 1),
            "rcb_recorded": len(recorded),
            "with_rcb": sum(1 for e in recorded if e["rcb"]),
        },
        "waits": _waits_block([w for w in waits if _day_of(w["before"]) in days]),
        "rings": _rings_block(eps),
        "rcb": _rcb_block([a for a in alerts if _day_of(a["at"]) in days]),
        "hours": hours,
        "raions_h": [_r(x / pooled.seen * 24, 3) if pooled.seen else None
                     for x in pooled.raions],
    }


# ---- comparisons


def _verdict(cur: Sequence[float | None], base: Sequence[float]) -> dict[str, Any]:
    """Where each recent week stands against the range of the background weeks."""
    out: dict[str, Any] = {"median": _r(_median(base)), "min": _r(min(base)) if base else None,
                           "max": _r(max(base)) if base else None, "weeks": len(base),
                           "above": None, "below": None, "last_above": None, "last_below": None}
    if len(base) < BASELINE_MIN:
        out["verdict"] = "thin"
        return out
    if any(v is None for v in cur):
        # A recent week the measure cannot be computed for (no episode to
        # average, no reads of the list) is not a week inside the range: the
        # comparison is not made rather than made on the weeks that remain,
        # whose verdict would be read as the verdict on all of them.
        out["verdict"] = "not_computable"
        return out
    above = [v is not None and v > max(base) for v in cur]
    below = [v is not None and v < min(base) for v in cur]
    out.update(above=sum(above), below=sum(below), last_above=above[-1], last_below=below[-1])
    if all(above):
        out["verdict"] = "all_above"
    elif all(below):
        out["verdict"] = "all_below"
    elif any(above):
        out["verdict"] = "some_above"
    elif any(below):
        out["verdict"] = "some_below"
    else:
        out["verdict"] = "in_range"
    return out


def _metric(key: str, weeks: Sequence[_Stretch], cur: Sequence[int], base: Sequence[int]
            ) -> dict[str, Any]:
    cv = [_value(key, weeks[w]) for w in cur]
    bv = [v for v in (_value(key, weeks[w]) for w in base) if v is not None]
    out = _verdict(cv, bv)
    if key == "rcb" and out["verdict"] not in ("thin", "not_computable"):
        classes = {_cadence_class(weeks[w]) for w in (*cur, *base)
                   if _value(key, weeks[w]) is not None}
        if len(classes) > 1:
            out["verdict"] = "not_assessed"
    pooled = _value(key, _pool([weeks[w] for w in cur]), pooled=True)
    last = cv[-1]
    out.update(current=_r(pooled), weeks_values=[_r(v) for v in cv],
               last_to_max=_r(last / out["max"], 3) if last is not None and out["max"] else None)
    return out


def _robust(weeks: Sequence[_Stretch], merged: Mapping[int, Sequence[int]],
            cur: Sequence[int], base: Sequence[int]) -> list[dict[str, Any]]:
    out = []
    for merge in MERGES_MIN:
        onsets = merged[merge]

        def rate(w: int, onsets: Sequence[int] = onsets) -> float | None:
            s = weeks[w]
            if s.seen < USABLE_SEEN_MIN:
                return None
            inside = bisect.bisect_left(onsets, s.b) - bisect.bisect_left(onsets, s.a)
            return inside / s.seen * 1440

        bv = [v for v in (rate(w) for w in base) if v is not None]
        out.append({"merge_min": merge, "verdict": _verdict([rate(w) for w in cur], bv)["verdict"]})
    return out


def _streak(days: Sequence[_Stretch], cur_days: set[date], base_days: set[date]
            ) -> dict[str, Any]:
    """The run of long days that closes the recent weeks, and how many the background had.

    The day still running is passed over, and any other day breaks the run
    unless it was whole, seen to `FULL_DAY_SHARE` and long: a day the record
    did not hold is not a long day, and stepping over it would print a run of
    long days with an unknown one inside it.
    """
    run: list[_Stretch] = []
    # Walked back from the last day of the recent weeks, not of the window: on
    # a Monday the week still running is not usable yet, and its first day
    # would end every run before it began.
    for d in reversed([d for d in days if d.first_day in cur_days]):
        if not run and d.minutes < d.length:
            continue
        if (d.minutes < d.length or d.seen < FULL_DAY_SHARE * d.minutes
                or d.band < LONG_DAY_MIN):
            break
        run.insert(0, d)
    return {
        "days": len(run),
        "notable": len(run) >= STREAK_MIN_DAYS,
        "from": run[0].first_day.isoformat() if run else None,
        "to": run[-1].first_day.isoformat() if run else None,
        "baseline_long_days": sum(1 for d in days
                                  if d.first_day in base_days and d.band >= LONG_DAY_MIN),
    }


def _coverage(rec: _Record, days: Sequence[_Stretch], chosen: set[date]) -> dict[str, Any]:
    """How much of the chosen weeks was seen, and their weakest day after the record began.

    The chosen weeks' own days only: a week left out as unusable between two
    chosen ones is in neither group, and its day without a record would name
    the weakest day of weeks that do not hold it. The day the record began and
    the days before it are left out of the weakest: a day nobody could have
    recorded says when the record starts, which the page says in its own
    words, and not how well it was kept.
    """
    inside = [d for d in days if d.first_day in chosen and d.minutes]
    seen = sum(d.seen for d in inside)
    whole = sum(d.minutes for d in inside)
    kept = [d for d in inside if d.a > rec.record_from]
    weakest = min(kept, key=lambda d: d.seen / d.minutes) if kept else None
    return {
        "seen_share": _r(seen / whole, 4) if whole else None,
        "weakest_day": weakest.first_day.isoformat() if weakest else None,
        "weakest_share": _r(weakest.seen / weakest.minutes, 4) if weakest else None,
    }


def _week_days(weeks: Sequence[_Stretch], chosen: Sequence[int]) -> set[date]:
    return {weeks[w].first_day + timedelta(days=d) for w in chosen for d in range(7)}


def _episodes_rcb(episodes: Sequence[Mapping[str, Any]], days: set[date]) -> dict[str, Any]:
    """Episodes of the RSO record inside the chosen weeks, with an RCB alert and without."""
    chosen = [e for e in episodes if e["rcb_recorded"] and _day_of(e["start"]) in days]

    def side(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        return {"n": len(rows),
                "median_minutes": _r(_median([float(e["minutes"]) for e in rows]), 1),
                "median_peak": _r(_median([float(e["peak_raions"]) for e in rows
                                           if e["peak_raions"] is not None]), 1)}

    with_rcb = side([e for e in chosen if e["rcb"]])
    without = side([e for e in chosen if not e["rcb"]])
    longer = (with_rcb["n"] and without["n"]
              and with_rcb["median_minutes"] > without["median_minutes"]
              and with_rcb["median_peak"] > without["median_peak"])
    return {"with_rcb": with_rcb, "without_rcb": without, "longer_and_wider": bool(longer)}


def _hours_summary(current: Mapping[str, Any], baseline: Mapping[str, Any]
                   ) -> dict[str, Any] | None:
    """The hour-of-day profile in the words the page uses: its range and its extremes."""
    def shares(group: Mapping[str, Any]) -> list[float | None]:
        return [h["with_alarm"] / h["days"] if h["days"] else None for h in group["hours"]]

    cur, base = shares(current), shares(baseline)
    known_cur = [(v, h) for h, v in enumerate(cur) if v is not None]
    known_base = [v for v in base if v is not None]
    if not known_cur or not known_base:
        return None
    peak = max(known_cur, key=lambda p: (p[0], -p[1]))
    low = min(known_cur, key=lambda p: (p[0], p[1]))
    low_base = base[low[1]]
    return {
        "current": [_r(v, 4) for v in cur], "baseline": [_r(v, 4) for v in base],
        "baseline_min": _r(min(known_base), 4), "baseline_max": _r(max(known_base), 4),
        "peak_hour": peak[1], "peak_share": _r(peak[0], 4),
        "low_hour": low[1], "low_share": _r(low[0], 4),
        "low_close_to_baseline": low_base is not None and abs(low[0] - low_base) <= HOURS_CLOSE,
    }


def _compare(rec: _Record, weeks: Sequence[_Stretch], days: Sequence[_Stretch],
             merged: Mapping[int, Sequence[int]], cur: Sequence[int], base: Sequence[int],
             groups: Mapping[str, Mapping[str, Any]], keys: tuple[str, str],
             episodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    cur_days, base_days = _week_days(weeks, cur), _week_days(weeks, base)
    current, baseline = groups[keys[0]], groups[keys[1]]
    band = rec.src.band
    raions = []
    for k, (c, b) in enumerate(zip(current["raions_h"], baseline["raions_h"], strict=True)):
        if c is not None and b is not None:
            change = c - b
            raions.append({"raion": k, "baseline_h": b, "current_h": c,
                           "change_h": _r(change, 3), "rising": change >= RAION_RISING_H,
                           "strong": change >= RAION_STRONG_H})
    raions.sort(key=lambda row: (-row["change_h"], row["raion"]))
    top = [row for row in raions[:RAION_LEAD] if row["rising"]]
    rising = None
    if top:
        rising = {
            "oblasts": list(dict.fromkeys(band[row["raion"]].oblast for row in top)),
            "km_lower_min": min(band[row["raion"]].km_lower for row in top),
            "km_lower_max": max(band[row["raion"]].km_lower for row in top),
        }
    since = (current["rcb"]["median_since_min"], baseline["rcb"]["median_since_min"])
    since_unchanged = (None if None in since
                       else abs(float(since[0]) - float(since[1])) <= SINCE_CLOSE_MIN)
    speeds = (current["rings"]["speed"], baseline["rings"]["speed"])
    overlap = None
    if all(s is not None and s["km_per_h_p05"] is not None and s["km_per_h"] is not None
           for s in speeds):
        c, b = speeds
        overlap = bool(c["km_per_h_p95"] >= b["km_per_h_p05"]
                       and b["km_per_h_p95"] >= c["km_per_h_p05"])
    return {
        "n": len(cur), "m": len(base), "current": keys[0], "baseline": keys[1],
        "channel_weeks": sum(1 for w in base if weeks[w].channel > 0),
        "metrics": {key: _metric(key, weeks, cur, base) for key in METRICS},
        "robust": _robust(weeks, merged, cur, base),
        "streak": _streak(days, cur_days, base_days),
        "coverage": _coverage(rec, days, cur_days | base_days),
        "raions": raions,
        "raions_rising": rising,
        "speeds_overlap": overlap,
        "episodes_rcb": _episodes_rcb(episodes, cur_days | base_days),
        "rcb_since_unchanged": since_unchanged,
        "hours": _hours_summary(current, baseline),
    }


# ---- the file


def _week_item(rec: _Record, s: _Stretch, usable: bool) -> dict[str, Any]:
    return {
        "first_day": s.first_day.isoformat(), "last_day": s.last_day.isoformat(),
        "from": rec.iso(s.a), "to": rec.iso(s.b), "minutes": s.minutes,
        "partial": s.minutes < s.length,
        "seen_min": s.seen, "seen_days": _r(s.seen / 1440, 2),
        "unseen_h": round((s.minutes - s.seen) / 60),
        "short_record": s.seen < FULL_DAY_SHARE * s.minutes,
        "api_min": s.api, "channel_min": s.channel,
        "source": None if not s.seen else ("channel" if s.channel > s.api else "api"),
        "usable": usable,
        "band_min": s.band, "border_min": s.border, "raion_min": s.raion, "episodes": s.episodes,
        "rcb_seen_min": s.rcb_seen, "rcb_alerts": s.rcb, "rcb_by_voivodeship": s.rcb_by,
        "rso_cadence": _cadence_class(s),
        "values": {key: _r(_value(key, s)) for key in METRICS},
    }


def _day_item(rec: _Record, d: _Stretch, cells: Mapping[tuple[date, int], list[int]]
              ) -> dict[str, Any]:
    day = d.first_day
    before = max(0, min(d.b, rec.record_from) - d.a)
    return {
        "date": day.isoformat(), "minutes": d.minutes, "complete": d.minutes == d.length,
        "seen_min": d.seen, "api_min": d.api, "channel_min": d.channel,
        "before_record_min": before,
        "seen_share": _r(d.seen / d.minutes, 4) if d.minutes else None,
        "api_share": _r(d.api / d.minutes, 4) if d.minutes else None,
        "channel_share": _r(d.channel / d.minutes, 4) if d.minutes else None,
        "band_min": d.band, "border_min": d.border, "episodes": d.episodes,
        "rcb_alerts": d.rcb,
        "raion_min": d.raions,
        "hours_seen_min": [cells.get((day, h), [0, 0])[0] for h in range(24)],
        "hours_alarm_min": [cells.get((day, h), [0, 0])[1] for h in range(24)],
    }


def _blind(rec: _Record) -> list[dict[str, Any]]:
    out = []
    kinds = (("gap", rec.gap_spans), ("silence", rec.silence_spans),
             ("unclear", rec.unclear_spans))
    for kind, spans in kinds:
        for a, b in spans:
            a = max(a, rec.record_from)
            if b - a < GAP_LISTED_MIN:
                continue
            out.append({"from": rec.iso(a), "to": rec.iso(b), "minutes": b - a, "kind": kind,
                        "source": "api" if a >= rec.switch else "channel"})
    return sorted(out, key=lambda item: (item["from"], item["kind"]))


def _seen_after(alerts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for cadence in ("coarse", "fine"):
        v = [float(a["seen_after_min"]) for a in alerts
             if a["read_cadence"] == cadence and a["seen_after_min"] is not None]
        out[cadence] = ({"n": len(v), "median": _r(_median(v), 1), "max": _r(max(v), 1)}
                        if v else None)
    return out


def _iso_utc(moment: datetime | None) -> str | None:
    return None if moment is None else moment.astimezone(UTC).isoformat()


def analyse(src: Inputs) -> dict[str, object]:
    """The `analysis.json` payload, version `ANALYSIS_VERSION`, from one window."""
    rec = _Record(src)
    weeks = _weeks(rec)
    days = _days(rec)
    cells = _hour_cells(rec)
    episodes = _episodes(rec)
    waits = _waits(rec, episodes)
    alerts = _alert_rows(rec)
    usable = [w for w, s in enumerate(weeks) if s.seen >= USABLE_SEEN_MIN]
    merged = {merge: _merged_onsets(rec, merge) for merge in MERGES_MIN}
    oblasts = _oblasts(rec, alerts)

    groups: dict[str, dict[str, Any]] = {}
    comparisons = []
    for n in range(1, CURRENT_MAX + 1):
        if len(usable) - n < BASELINE_MIN:
            break
        cur = usable[-n:]
        ckey = f"c{n}"
        groups[ckey] = _group(rec, weeks, cur, episodes, waits, alerts, cells)
        for m in range(BASELINE_MIN, len(usable) - n + 1):
            base = usable[-n - m:-n]
            bkey = f"b{n}-{m}"
            groups[bkey] = _group(rec, weeks, base, episodes, waits, alerts, cells)
            comparisons.append(_compare(rec, weeks, days, merged, cur, base, groups,
                                        (ckey, bkey), episodes))
    n_default = min(DEFAULT_CHOICE[0], max(0, len(usable) - BASELINE_MIN))
    default = None
    if n_default:
        default = {"n": n_default,
                   "m": min(DEFAULT_CHOICE[1], len(usable) - n_default)}

    def strip(e: Mapping[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in e.items() if k not in ("minute", "end_minute")}

    return {
        "v": ANALYSIS_VERSION,
        "generated_at": _iso_utc(src.end),
        "zone": "Europe/Warsaw",
        "window": {"start": _iso_utc(src.start), "end": _iso_utc(src.end), "weeks": WEEKS,
                   "minutes": rec.total},
        "record": {
            "from": rec.iso(rec.record_from) if rec.record_from < rec.total else None,
            "channel_since": _iso_utc(src.channel_since),
            "api_since": _iso_utc(src.api_since),
            "switch": rec.iso(rec.switch) if rec.switch < rec.total else None,
        },
        "definitions": {
            "band_km": BAND_KM, "silence_min": SILENCE_MIN, "usable_seen_min": USABLE_SEEN_MIN,
            "hour_seen_min": HOUR_SEEN_MIN, "rings_km": list(RING_EDGES_KM),
            "lead_window_min": LEAD_WINDOW_MIN, "fit_upto_km": FIT_UPTO_KM,
            "resamples": RESAMPLES, "seed": SEED,
            "event_minutes": [EVENT_FROM_MIN, EVENT_TO_MIN, EVENT_STEP_MIN],
            "merges_min": list(MERGES_MIN), "long_day_min": LONG_DAY_MIN,
            "full_day_share": FULL_DAY_SHARE, "rso_fine_read_s": RSO_FINE_READ_S,
            "coarse_week_min": COARSE_WEEK_MIN, "wait_grid_min": [_r(t, 3) for t in _wait_grid()],
            "wait_buckets_min": list(WAIT_BUCKETS_MIN),
            "gap_listed_min": GAP_LISTED_MIN, "streak_min_days": STREAK_MIN_DAYS,
        },
        "band": [raion.as_item() for raion in src.band],
        "weeks": [_week_item(rec, s, w in usable) for w, s in enumerate(weeks)],
        "days": [_day_item(rec, d, cells) for d in days],
        "blind": _blind(rec),
        "episodes": [strip(e) for e in episodes],
        "waits": waits,
        "rcb": {
            "recorded_since": None if rec.rcb_first is None else rec.iso(rec.rcb_first),
            # The stretch before the first poll is not a hole in the record but
            # its start, which `recorded_since` already says.
            "unread": [{"from": rec.iso(a), "to": rec.iso(b), "minutes": b - a}
                       for a, b in rec.rcb_unread
                       if b - a >= GAP_LISTED_MIN and rec.rcb_first is not None
                       and a >= rec.rcb_first],
            "cadence": rec.cadence,
            "alerts": alerts,
            "seen_after": _seen_after(alerts),
            "oblasts": oblasts,
            "oblast_top": _oblast_top(oblasts),
            "hours": [sum(1 for a in alerts if int(a["at"][11:13]) == hour) for hour in range(24)],
            "rules": _rules(rec),
        },
        "choices": {"usable_weeks": usable, "current_max": CURRENT_MAX,
                    "baseline_min": BASELINE_MIN, "default": default},
        "groups": groups,
        "comparisons": comparisons,
    }
