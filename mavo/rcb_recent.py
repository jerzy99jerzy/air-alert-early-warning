"""The last forty-eight hours of RCB air alerts, voivodeship by voivodeship (D-062).

**The question, and why the live keys do not answer it.** On 2026-09-28 the
operator asked for the areas page to say in which voivodeships RCB raised an
air alert in the last forty-eight hours. `pl_warnings` holds what paints now
and `pl_all_clear` what was cleared and is still listed, so an alert that
ended in the morning is in neither by the evening. The seven-day slider has
it, for a reader who scrubs to the right quarter-hour. `pl_rcb_recent` is the
answer as one key of `state.json`, composed on every cycle.

**What painted is the composer's; the rest is read off the lists.** The
stretches an alert painted come from `timeline.rcb_layer`, which asks
`poland.warnings_verdict` at every instant the verdict can change, so a
voivodeship this key calls painted at a moment is the one the map painted
then, and the one the slider repaints there, by construction and by a test
that asks the live composer at the same moments. Why a painting stopped, and
which all-clears RCB announced, are read off the lists the store recorded,
version by version, with the composer's own readings of a row (`classify`,
`_issued_at`, `expiry_instant`). The verdict alone would not do: it drops an
expired communique, so an alert rewritten into an all-clear that had expired
by the next read, or one whose `valid_to` RCB moved into the past, would read
as withdrawn.

**Why a painting stopped: five words, each with the clock of its `at`.** The
week recorded from the production store
(`tests/fixtures/store_week_2026-09-26.sqlite3.xz`) ends its eight alerts in
four of these ways, and D-055's pairing, which needs an alert and its
all-clear in one list, ends none of them `[measured]`:

- `all_clear`, RCB's clock: an all-clear naming the voivodeship, issued after
  the alert, is in the list at the read where the alert stops painting. D-055
  pairing the two is this case, and so is RCB swapping one for the other in a
  single edit of the list, which is how 23362253 ended 23361410 on
  2026-09-24. `at` is RCB's stamp for that all-clear, the `announced` its own
  line carries, and `by` its id. Its `valid_from` would not do: an all-clear
  that was itself an alert rewritten keeps the moment that alert was raised.
  Where the stamp does not read, the read stands in and `clock` says so.
- `rewritten`, RCB's clock where its stamp reads: the communique itself is
  listed as an all-clear. Three of the week's alerts ended so. The rewrite
  keeps `valid_from` and moves `updated_at`, so `at` is the `updated_at` of
  that version, 3.7 to 9.5 minutes before the read that saw it `[measured,
  the three]`; where it does not read, the read stands in and `clock` says so.
- `expired`, RCB's clock: the `valid_to` of the version in the list passed.
  RCB moves it: 23362967 went from 23:59 to 02:00 while it stood.
- `withdrawn`, the read's clock: off the list, or no longer naming the
  voivodeship or the air, with no all-clear and no `valid_to` passed. The
  week's one case was first read gone 4.5 minutes before its `valid_to`,
  which may be the feed's own early expiry rather than an act of RCB.
- `unread`, the read's clock: the communique block stopped being usable, past
  the hour-old ceiling or on a list naming a row nobody wrote, so how the
  alert ended is not known. `at` is the last read before that, the last one
  that saw the alert.

**Which all-clears are events of the window.** Every version classified as an
all-clear in a list the window holds, per voivodeship it names, when RCB
announced it inside the window: `announced` is RCB's `updated_at` of the
first version that is an all-clear, which for a rewrite is the rewrite and not
the alert's `valid_from`. Where that stamp does not read, the first read that
listed it stands in, so one already listed when the window opened is not an
event of it.

**`unread`, and what an empty one licenses.** The stretches in which the list
was not read, from the last read before them to the next, where the two are
further apart than the RSO pipe's own outage threshold (two cadences, the
rule `liveness` applies); the stretches in which the verdict could not use a
read; and, when the record starts inside the window, the stretch before it.
Empty, and every alert or all-clear that stayed listed for longer than that
threshold was seen. An alert raised and taken off the list between two reads
never is, so what a page may say from an empty `unread` is what the reads
found, not what RCB did. The communique's text stays out: the live block
carries it for what is standing, and two days of bodies on every push buy a
paragraph nobody asked the list to hold.
"""

from __future__ import annotations

import bisect
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from mavo import poland
from mavo.errors import SourceUnavailable
from mavo.liveness import PRODUCTION_FEEDS
from mavo.poland import Block
from mavo.sources import rso
from mavo.store import EventStore
from mavo.timeline import RcbLayer, lists_over, rcb_layer, reads_over

#: The window, in hours: the operator's figure of 2026-09-28.
RECENT_HOURS = 48

#: Why a painting stopped. A closed vocabulary, so a consumer may render each
#: word by name and refuse one it does not know.
ENDINGS: tuple[str, ...] = ("all_clear", "rewritten", "expired", "withdrawn", "unread")

#: Whose clock an end's `at` is on: a stamp RCB wrote, or a read of this pipe.
CLOCKS: tuple[str, ...] = ("rcb", "read")

#: How far apart two reads of the list may be before the stretch between them
#: is unread: the RSO pipe's own outage threshold, taken from the table the
#: live `sources` block judges the pipe by, so the two cannot drift.
SILENCE_S: float = next(spec.silence_is_an_outage_s
                        for spec in PRODUCTION_FEEDS if spec.feed == rso.FEED)

#: A communique on one voivodeship: `(slug, id)`. The pairing of D-055 is per
#: voivodeship, and so is every question this module answers.
Key = tuple[str, str]
Row = Mapping[str, Any]
Stretch = list[datetime | None]


def _iso(moment: datetime | None) -> str | None:
    """At the store's precision, like every stamp `timeline.json` carries."""
    return None if moment is None else moment.astimezone(UTC).isoformat()


def feed_instant(text: str | None) -> datetime | None:
    """One of the feed's own stamps as an instant, or None where it does not convert.

    `updated_at` arrives naive in the feed's zone, as `valid_from` does, and
    is read by `rso.to_utc` with that zone. A doubled autumn hour or a
    malformed stamp is None: an end is then put on the read's clock rather
    than on a guess.
    """
    if not text:
        return None
    try:
        return rso.to_utc(text, poland.ZONE)
    except SourceUnavailable:
        return None


@dataclass(frozen=True, slots=True)
class Record:
    """What a window is summarised from, read from the store once."""

    layer: RcbLayer
    #: The newest list at or before the window's start, then every list
    #: recorded in it, as `(observed_at, digests)`, oldest first.
    lists: tuple[tuple[datetime, tuple[str, ...]], ...]
    held: Mapping[str, Row]
    #: Every read of the list in the window, the newest before it first.
    reads: tuple[datetime, ...]

    def rows_at(self, moment: datetime) -> tuple[Row, ...] | None:
        """The rows of the list current at `moment`, or None where there is none
        or it names a row nobody wrote, which is where the verdict says `null`."""
        index = bisect.bisect_right([stamp for stamp, _ in self.lists], moment) - 1
        if index < 0:
            return None
        members = self.lists[index][1]
        if any(member not in self.held for member in members):
            return None
        return tuple(self.held[member] for member in members)


def record(store: EventStore, start: datetime, end: datetime) -> Record:
    """The layer, the lists, their rows and the reads over `[start, end]`."""
    lists = lists_over(store, rso.FEED, poland.WARNINGS_URL, start, end)
    wanted = sorted({member for _stamp, members in lists for member in members})
    return Record(
        layer=rcb_layer(store, start, end),
        lists=tuple((stamp, tuple(members)) for stamp, members in lists),
        held=store.communiques_by_digest(wanted),
        reads=tuple(reads_over(store, rso.FEED, poland.WARNINGS_URL, start, end)),
    )


Verdicts = Mapping[str, tuple[str, str] | None]


def verdicts(held: Mapping[str, Row]) -> dict[str, tuple[str, str] | None]:
    """`classify` of every row the window's lists name, once per digest.

    The composer's reading of a row, `("threat" | "all_clear", term)` or None,
    taken once: the lists repeat the same rows at every change, and the walk
    asks about them at every one.
    """
    return {digest: poland.classify(row["fields"].get("title"), poland._body(row["fields"]))
            for digest, row in held.items()}


def _kind(row: Row, known: Verdicts) -> str | None:
    """`threat`, `all_clear` or None, read as the composer reads a row."""
    verdict = known.get(str(row["digest"]))
    return None if verdict is None else verdict[0]


def _names(row: Row) -> tuple[tuple[str, str], ...]:
    return poland._names(dict(row))


def _issued(row: Row) -> datetime | None:
    return poland._issued_at(dict(row))


def _find(rows: Iterable[Row], communique: str) -> Row | None:
    return next((row for row in rows if str(row["source_id"]) == communique), None)


def _ending(reason: str, at: datetime | None, clock: str, by: str | None) -> dict[str, Any]:
    return {"reason": reason, "at": _iso(at), "clock": clock, "by": by}


def ending(key: Key, painted: Row, moment: datetime, rows: Sequence[Row] | None,
           reads: Sequence[datetime], known: Verdicts,
           announced: Mapping[Key, datetime | None]) -> dict[str, Any]:
    """Why an alert stopped painting its voivodeship at `moment`, as `ended` says it.

    `painted` is the version that painted last; `rows` the list current at
    `moment`, or None where the verdict could not use it; `announced` RCB's
    stamp for each all-clear of the window, as its own line carries it. The
    order of the tests is the order of preference: the publisher's own words,
    then a field running out, then an absence. The alert's issue time is its
    version in the list where it still is, as D-055 compares them, so an
    alert whose `valid_from` RCB moved back to before a standing all-clear
    ends at that all-clear, as the composer's `ended` says. An end by an
    all-clear is dated by that all-clear's `announced` and never by its
    `valid_from`, which for an alert rewritten into an all-clear is the moment
    it was raised.
    """
    slug, communique = key
    if rows is None:
        # The last read before the block stopped being usable, and not a read
        # at `moment` itself: a list naming a row nobody wrote is recorded by
        # a read, and that read did not see the alert.
        index = bisect.bisect_left(list(reads), moment) - 1
        return _ending("unread", reads[index] if index >= 0 else None, "read", None)
    current = _find(rows, communique)
    if current is not None and _kind(current, known) == "all_clear":
        stamp = feed_instant(current["fields"].get("updated_at"))
        return _ending("rewritten", stamp or moment, "rcb" if stamp else "read", communique)
    version = current if current is not None else painted
    issued = _issued(version)
    candidates: list[tuple[datetime, str]] = []
    for row in rows:
        at = _issued(row)
        if (issued is not None and at is not None and at > issued
                and _kind(row, known) == "all_clear"
                and slug in (named for named, _name in _names(row))):
            candidates.append((at, str(row["source_id"])))
    if candidates:
        _issued_first, by = min(candidates)
        stamp = announced.get((slug, by))
        return _ending("all_clear", stamp or moment, "rcb" if stamp else "read", by)
    expiry = poland.expiry_instant(version["fields"].get("valid_to"))
    if expiry is not None and expiry < moment:
        return _ending("expired", expiry, "rcb", None)
    return _ending("withdrawn", moment, "read", None)


def holes(reads: Sequence[datetime], start: datetime, end: datetime,
          silence_s: float = SILENCE_S) -> list[Stretch]:
    """Stretches of `[start, end]` between two reads further apart than `silence_s`.

    From the last read before the stretch to the next, clipped to the window;
    the tail is open when the newest read is older than the threshold at `end`.
    """
    limit = timedelta(seconds=silence_s)
    found: list[Stretch] = []
    for before, after in zip(reads, reads[1:], strict=False):
        if after - before > limit and after > start:
            found.append([max(before, start), after])
    if reads and end - reads[-1] > limit:
        found.append([max(reads[-1], start), None])
    return found


def merged(stretches: Iterable[Stretch]) -> list[Stretch]:
    """Stretches joined where they touch or overlap; `None` as an end is open."""
    starts: list[tuple[datetime, datetime | None]] = []
    for begin, finish in stretches:
        if begin is not None:
            starts.append((begin, finish))
    out: list[Stretch] = []
    for begin, finish in sorted(starts, key=lambda pair: pair[0]):
        last = out[-1] if out else None
        if last is None or (last[1] is not None and begin > last[1]):
            out.append([begin, finish])
        elif last[1] is not None and (finish is None or finish > last[1]):
            last[1] = finish
    return out


@dataclass(slots=True)
class _Alert:
    #: The newest version seen painting, as the verdict published it.
    item: Mapping[str, Any]
    painted: list[Stretch]
    ended: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class _Clear:
    row: Row
    term: str
    #: The read that first listed the version that is an all-clear.
    appeared: datetime
    #: RCB's `updated_at` of that version, or None where it does not read.
    announced: datetime | None


def _extend(stretches: list[Stretch], start: datetime, end: datetime | None) -> None:
    """Add `[start, end)`, joined to the last stretch when the two touch."""
    if stretches and stretches[-1][1] == start:
        stretches[-1][1] = end
    else:
        stretches.append([start, end])


def _clears(rec: Record, names: dict[str, str], known: Verdicts) -> dict[Key, _Clear]:
    """Every all-clear the window's lists hold, per voivodeship, at its first sighting."""
    found: dict[Key, _Clear] = {}
    for stamp, members in rec.lists:
        for member in members:
            row = rec.held.get(member)
            verdict = known.get(member)
            if row is None or verdict is None or verdict[0] != "all_clear":
                continue
            fields = row["fields"]
            for slug, name in _names(row):
                names.setdefault(slug, name)
                key = (slug, str(row["source_id"]))
                if key not in found:
                    found[key] = _Clear(row=row, term=verdict[1], appeared=stamp,
                                        announced=feed_instant(fields.get("updated_at")))
    return found


def summarise(rec: Record, start: datetime, end: datetime, *, hours: int,
              silence_s: float = SILENCE_S) -> dict[str, Any] | None:
    """The `pl_rcb_recent` value for `[start, end]`, or None before the first poll.

    `rec.layer` holds at least one interval whenever the feed was polled by
    `end`, which is `timeline.rcb_layer`'s own guarantee.
    """
    first = rec.layer.recorded_since
    if first is None or first > end:
        return None
    unread: list[Stretch] = holes(rec.reads, start, end, silence_s)
    if first > start:
        unread.append([start, first])
    known = verdicts(rec.held)
    names: dict[str, str] = {}
    clears = _clears(rec, names, known)
    announced = {key: clear.announced for key, clear in clears.items()}
    alerts: dict[Key, _Alert] = {}
    paired: dict[Key, list[str]] = {}
    painted_before: dict[Key, Row] = {}
    for span in rec.layer.spans:
        stretch = span.span
        rows = span.warnings.value if span.warnings.published else None
        listed = rec.rows_at(stretch.start) if rows is not None else None
        painted: dict[Key, Row] = {}
        if rows is None or listed is None:
            unread.append([stretch.start, stretch.end])
        else:
            # The verdict read this very list, so every id it painted is in it;
            # a miss is a store changing under the walk and raises, which the
            # report loop's guard turns into `null` for this key alone.
            by_id = {str(row["source_id"]): row for row in listed}
            for row in rows:
                slug = str(row["slug"])
                names.setdefault(slug, str(row["voivodeship"]))
                for item in row["communiques"]:
                    key = (slug, str(item["id"]))
                    painted[key] = by_id[key[1]]
                    alert = alerts.setdefault(key, _Alert(item=item, painted=[]))
                    alert.item = item
                    alert.ended = None
                    _extend(alert.painted, stretch.start, stretch.end)
            for row in span.all_clear.value or []:
                for item in row["communiques"]:
                    ids = paired.setdefault((str(row["slug"]), str(item["id"])), [])
                    ids.extend(str(one) for one in item.get("ended") or () if str(one) not in ids)
        for key, version in painted_before.items():
            if key not in painted:
                alerts[key].ended = ending(key, version, stretch.start, listed, rec.reads,
                                           known, announced)
        painted_before = painted

    rows_out: dict[str, dict[str, Any]] = {}
    latest: dict[str, datetime] = {}

    def row_of(slug: str, moment: datetime) -> dict[str, Any]:
        latest[slug] = max(latest.get(slug, moment), moment)
        return rows_out.setdefault(slug, {
            "slug": slug, "voivodeship": names.get(slug, slug),
            "alerts": [], "all_clears": [],
        })

    for (slug, communique), alert in sorted(
            alerts.items(), key=lambda pair: (pair[1].painted[0][0] or start, pair[0])):
        last = alert.painted[-1][1]
        row_of(slug, last if last is not None else end)["alerts"].append({
            "id": communique,
            "title": alert.item.get("title"),
            "valid_from": alert.item.get("valid_from"),
            "air_term": alert.item.get("air_term"),
            "painted": [{"from": _iso(a), "to": _iso(b)} for a, b in alert.painted],
            "ended": alert.ended,
        })
    for (slug, communique), clear in sorted(
            clears.items(), key=lambda pair: (pair[1].announced or pair[1].appeared, pair[0])):
        if (clear.announced or clear.appeared) < start:
            continue
        fields = clear.row["fields"]
        row_of(slug, clear.announced or clear.appeared)["all_clears"].append({
            "id": communique,
            "title": fields.get("title"),
            "valid_from": poland.feed_stamp_as_iso(fields.get("valid_from")),
            "air_term": clear.term,
            "announced": _iso(clear.announced),
            "appeared": _iso(clear.appeared),
            "ended": paired.get((slug, communique), []),
        })
    order = sorted(rows_out, key=lambda slug: (-latest[slug].timestamp(), slug))
    return {
        "hours": hours,
        "start": _iso(start),
        "end": _iso(end),
        "recorded_since": _iso(first),
        "unread": [{"from": _iso(a), "to": _iso(b)} for a, b in merged(unread)],
        "voivodeships": [rows_out[slug] for slug in order],
    }


def measure(store: EventStore, as_of: datetime, hours: int = RECENT_HOURS) -> Block:
    """`pl_rcb_recent` for the window ending at `as_of`, or absent before any poll.

    Absent on the terms of `pl_warnings`: this producer never polled RSO, so
    there is no record to summarise. There is no empty state apart from a
    window with nothing in it, which lists no voivodeship and says in
    `unread` whether it could see.
    """
    start = as_of - timedelta(hours=hours)
    value = summarise(record(store, start, as_of), start, as_of, hours=hours)
    if value is None:
        return poland.UNPUBLISHED
    return Block(published=True, value=value)
