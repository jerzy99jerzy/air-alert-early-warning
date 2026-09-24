"""The strike tally: readings of `@kpszsu` as stored rows and as one contract key.

`mavo/sources/kpszsu.py` turns a page of the channel into figures. This module
is what the rest of the package does with them: the rows the store keeps, and
the `strike_tally` object a consumer reads. It holds no parsing rule, so a
change to the source's wording lands in one file and a change to what is
published lands in this one.

**What may be published, and the shape that enforces it** (D-056). MAVO states
the Air Force's own figures and nothing else. Two rules do most of that work
here:

- `launched_sum` is computed once, by the producer, and is None unless the
  launched list is non-empty and every item carries a count. A consumer cannot
  add up a list this module gave it and reach a total the Air Force never
  published, because on a night where that would be possible the list is not
  published either.
- a night whose own checks did not hold is published as its headline alone.
  Their total is a figure they stated; our breakdown of a night we could not
  read is not, and putting the two side by side would print our reading under
  their name.

**Impacts are stored and not published.** They are read (`влучання засобів ...
на 41 локації` is impacts with neither type nor count), and version one has no
reader-facing use for a list that renders empty beside a location count.

**No age ceiling**, following `pl_airspace`. The value carries `read_at` and
`stale_error`, so an old reading renders as old rather than disappearing. A
night stays true as history when the pipe dies; what must not happen is its
passing as the latest, and `night` beside `read_at` is what says which it is.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from mavo.poland import UNPUBLISHED, Block
from mavo.report import HISTORY_WINDOWS_DAYS
from mavo.sources import kpszsu
from mavo.store import EventStore

FEED = kpszsu.FEED

#: The windows `strike_history` carries, shortest first (D-057). Imported from
#: `report` rather than written again: two triples of windows in one package is
#: how the chart and the quarter panel come to disagree about what ninety days
#: means. The `--windows` flag moves `history.json` alone, and deliberately -
#: the sentences on the page name these three and nothing recomputes prose.
WINDOW_DAYS: tuple[int, ...] = HISTORY_WINDOWS_DAYS


def _parse_stored(stamp: str) -> datetime:
    """A stored stamp back as an aware instant, assuming UTC when it says nothing.

    The store writes UTC and refuses a naive timestamp on the way in, so the
    assumption is about rows this package wrote rather than about input.
    """
    parsed = datetime.fromisoformat(stamp)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class TallyRow:
    """One post as the store keeps it.

    `tally` is the whole reading, including the parts the contract does not
    publish, because the row is the evidence and the contract is the view.
    """

    post_id: int
    posted_at: datetime
    kind: str | None
    status: str
    night: str | None
    as_of: datetime | None
    tally: dict[str, Any] | None
    checks: tuple[str, ...]
    raw_text: str
    source_url: str
    reader: str

    def digest(self) -> str:
        """Identity: the post and the text it carried.

        The id alone would make an edited post overwrite its earlier reading,
        and the text alone would merge two posts that said the same thing on
        two days.
        """
        material = f"{self.post_id}\n{self.raw_text}"
        return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _item(item: kpszsu.Item) -> dict[str, Any]:
    """One weapon class as stored and published.

    `count` None is the count the summary did not give. It is never 0: nothing
    in this project turns an unknown into a zero, and a zero here would be the
    claim that none of that class was launched.
    """
    return {
        "class": item.cls,
        "count": item.count,
        "text": item.text,
        "approx": item.approx,
        "derived": item.derived,
    }


def tally_json(tally: kpszsu.Tally) -> dict[str, Any]:
    """The whole reading as JSON, for the row rather than for the contract."""
    head = tally.headline
    return {
        "kind": tally.kind,
        "shape": tally.shape,
        "night": tally.night.isoformat() if tally.night is not None else None,
        "as_of": tally.as_of.isoformat() if tally.as_of is not None else None,
        "headline": {
            "total": head.total,
            "missiles": head.missiles,
            "drones": head.drones,
            "unnumbered": list(head.unnumbered),
        },
        "launched_total": (
            None if tally.launched_total is None
            else {
                "assets": tally.launched_total.assets,
                "missiles": tally.launched_total.missiles,
                "drones": tally.launched_total.drones,
            }
        ),
        "launched": [_item(item) for item in tally.launched],
        "downed": [_item(item) for item in tally.downed],
        "impacts": [_item(item) for item in tally.impacts],
        "hit_locations": tally.hit_locations,
        "debris_locations": tally.debris_locations,
        "directions": tally.directions,
        "not_reached": (
            None if tally.not_reached is None
            else {"text": tally.not_reached.text, "count": tally.not_reached.count}
        ),
        "attack_continues": tally.attack_continues,
        "launched_sum": kpszsu.launched_sum(tally),
        "checks": list(tally.checks),
    }


def row_of(reading: kpszsu.Reading) -> TallyRow:
    """The store row for one reading, refused or read."""
    tally = reading.tally
    return TallyRow(
        post_id=reading.message.post_id,
        posted_at=reading.message.posted_at,
        kind=None if tally is None else tally.kind,
        status=reading.status,
        night=(
            None if tally is None or tally.night is None else tally.night.isoformat()
        ),
        as_of=None if tally is None else tally.as_of,
        tally=None if tally is None else tally_json(tally),
        checks=() if tally is None else tuple(tally.checks),
        raw_text=reading.message.text,
        source_url=reading.message.source_url,
        reader=str(kpszsu.READER_VERSION),
    )


def rows_of(page: kpszsu.Page) -> tuple[TallyRow, ...]:
    """Every reading on one page, in the order the page held them."""
    return tuple(row_of(reading) for reading in page.readings)


def headline_total(tally: dict[str, Any]) -> int | None:
    """Their headline figure: the total, their two figures added, or the one.

    Deliberately not `kpszsu.downed_total`, whose last branch adds up the
    items when every one of them carries a count. That branch is right for the
    reader, which checks a reading against itself; it is wrong here, because on
    a flagged night the items are our reading and the headline is theirs, and
    the contract publishes theirs.

    **The third branch is F187.** A drone-only night is headed ``ЗБИТО/
    ПОДАВЛЕНО 95 ВОРОЖИХ БПЛА``: one figure, in their first line, for the whole
    night. Until 0.57.0.0 this function wanted two and so returned None, and
    the page printed "no figure was given for how many were shot down" above a
    breakdown listing those same drones. Measured over the 91 nights of the
    recorded corpus: 53 carry a total, 6 carry both figures, 36 carry the drone
    figure alone, so two nights in five were published as an unknown the Air
    Force had stated. The guard is `unnumbered`: on 2026-07-01 the headline
    read 130 drones ``та ракетами`` with no count for the missiles, and there
    the single figure is not the night's total. One night in the corpus takes
    that branch and it is the one night that must not.
    """
    head = tally["headline"]
    if head["total"] is not None:
        return int(head["total"])
    if head["missiles"] is not None and head["drones"] is not None:
        return int(head["missiles"]) + int(head["drones"])
    if head["unnumbered"]:
        return None
    lone = [figure for figure in (head["missiles"], head["drones"])
            if figure is not None]
    return int(lone[0]) if len(lone) == 1 else None


def value(
    row: dict[str, Any], *, read_at: datetime, stale_error: str | None
) -> dict[str, Any]:
    """The `strike_tally` object for one night.

    On `flagged`, everything our reading produced is withheld and their
    headline stands alone, so nothing under their name is ours. That is the
    whole of the difference between the two states, and it is here rather than
    in the consumer because a rule kept in a renderer is a rule the next
    renderer does not have.
    """
    tally = row["tally"] or {}
    flagged = row["status"] != "ok"
    return {
        "night": row["night"],
        "as_of": tally.get("as_of"),
        "posted_at": _parse_stored(str(row["posted_at"])).isoformat(timespec="seconds"),
        "shape": tally.get("shape"),
        "check": "flagged" if flagged else "ok",
        "downed_total": headline_total(tally) if tally else None,
        "downed": None if flagged else list(tally.get("downed") or []),
        "launched_total": None if flagged else tally.get("launched_total"),
        "launched": None if flagged else list(tally.get("launched") or []),
        "launched_sum": None if flagged else tally.get("launched_sum"),
        "source_url": row["source_url"],
        "read_at": read_at.isoformat(timespec="seconds"),
        "stale_error": stale_error,
    }


def block(store: EventStore, as_of: datetime) -> Block:
    """`strike_tally` for one moment, or the reason it is absent or null.

    The four states of `mavo/poland.py`, minus the empty one. Absent: this
    producer has never polled the channel, so the consumer's own reading, if
    any, still stands. `null`: polled, and the store holds no readable night.
    A value: the latest night. There is no empty state, because an empty object
    would render as a night on which nothing was launched.

    `as_of` is accepted and unused, as `airspace_block` accepts it: the value
    carries the source's own hour and this producer's `read_at`, and a night is
    not stale at a moment of ours.
    """
    del as_of
    if store.newest_attempt_at(FEED) is None:
        return UNPUBLISHED
    read_at = store.newest_read_at(FEED)
    if read_at is None:
        return Block(published=True, value=None)
    row = store.newest_strike_night()
    if row is None:
        return Block(published=True, value=None)
    read_moment = _parse_stored(read_at)
    newest_attempt = store.newest_attempt_at(FEED)
    stale_error = None
    if newest_attempt is not None and _parse_stored(newest_attempt) > read_moment:
        stale_error = store.newest_refusal_detail(FEED)
    return Block(
        published=True,
        value=value(row, read_at=read_moment, stale_error=stale_error),
    )


def point(row: dict[str, Any]) -> dict[str, Any]:
    """One night as the series carries it: two figures, or the word for none.

    The same rules as `value`, one night wide. `downed` is their headline
    figure and stands on a flagged night, because the headline is theirs;
    `launched` is withheld there, because on a flagged night everything under
    the headline is our reading of a message our own checks refused.

    `launched` prefers the inventory they printed (``противник атакував 282
    засобами повітряного нападу``) over the guarded sum, and takes the sum only
    where every item they listed carried a count. Neither is ever 0: a night
    with no figure carries None, and None is drawn as a gap rather than as a
    night on which nothing flew.
    """
    tally = row["tally"] or {}
    flagged = row["status"] != "ok"
    launched: int | None = None
    if not flagged and tally:
        inventory = tally.get("launched_total")
        if isinstance(inventory, dict) and inventory.get("assets") is not None:
            launched = int(inventory["assets"])
        elif tally.get("launched_sum") is not None:
            launched = int(tally["launched_sum"])
    return {
        "night": row["night"],
        "read": True,
        "downed": headline_total(tally) if tally else None,
        "launched": launched,
        "check": "flagged" if flagged else "ok",
    }


def unread(night: date) -> dict[str, Any]:
    """A night this store holds no summary for, carried rather than skipped.

    **The series is dense or it lies about time.** A window that listed only
    the nights it had readings for would draw four columns evenly across seven
    days, and the four days the pipe was dead would not be missing from the
    picture - they would be invisible in it, which is worse, because the chart
    would look complete. Every night of the window is a column, and a night
    with nothing behind it is a column with nothing drawn in it.

    `read` is what tells the two kinds of blank apart: a night nobody read, and
    a night whose summary was read and gave no figure to publish. Both are
    blanks on the page and they are different claims about us.
    """
    return {
        "night": night.isoformat(),
        "read": False,
        "downed": None,
        "launched": None,
        "check": None,
    }


def _series_summary(
    points: Sequence[dict[str, Any]], key: str, days: int
) -> dict[str, Any]:
    """One column of one window: the sum, what went into it, and the peak.

    **`nights` is what makes the sum readable.** Adding up the nights that
    carry a figure is arithmetic on figures the Air Force published, which
    D-057 allows; presenting that sum as the total for the window would be a
    claim about the nights that carry none, which it is not. The count travels
    beside the sum so the consumer can say "at least" when the two disagree,
    and `complete` says which of the two sentences is the true one.

    A window with nothing in it has no sum at all. Zero here would say the
    Air Force reported nothing shot down over ninety days, which is a claim
    about the sky; None says we hold no figure, which is a claim about us.
    """
    figures = [(one["night"], int(one[key])) for one in points
               if one[key] is not None]
    if not figures:
        return {"sum": None, "nights": 0, "complete": False,
                "max": None, "max_night": None}
    peak = max(figures, key=lambda pair: pair[1])
    return {
        "sum": sum(figure for _, figure in figures),
        "nights": len(figures),
        "complete": len(figures) == days,
        "max": peak[1],
        "max_night": peak[0],
    }


def window(
    points: Sequence[dict[str, Any]], days: int, end: date
) -> dict[str, Any]:
    """One window over the series, with its own span and its own coverage.

    `days` is the calendar length and `nights_read` the number of those nights
    a summary was read for, so the gap between them is visible without any
    consumer having to count the series itself.
    """
    start = end - timedelta(days=days - 1)
    first, last = start.isoformat(), end.isoformat()
    inside = [one for one in points if first <= one["night"] <= last]
    return {
        "days": days,
        "start": first,
        "end": last,
        "nights_read": sum(1 for one in inside if one["read"]),
        "downed": _series_summary(inside, "downed", days),
        "launched": _series_summary(inside, "launched", days),
    }


def history(
    store: EventStore,
    as_of: datetime,
    *,
    windows: Sequence[int] = WINDOW_DAYS,
) -> Block:
    """`strike_history` for one moment: the series and its three windows.

    The same four states as `block`, and for the same reasons, so a consumer
    reads the two keys with one set of rules. Absent: never polled. `null`:
    polled, and no night is held at all. A value: the nights we read, the
    windows over them, and how much of each window they cover.

    **The anchor is the clock, not the newest row (D-057).** A window that
    ended on the last night in the store would answer a different question
    from the one a reader asks: "the last seven days" is seven days of the
    calendar, and a pipe that stopped three days ago has to show three gaps
    rather than quietly slide its window back with the data. `TrailingWindow`
    anchors the same way and publishes `log_reaches_window_start` beside it.

    **One exception, and it is data and not a threshold.** The night in
    progress has no summary until the morning, so the window ends on today's
    Kyiv date when a reading for it is already held and on yesterday's when it
    is not. A clock-hour cutoff would have been a number to defend at every
    daylight change; this asks the store what it has. When the morning summary
    never arrives, yesterday's night takes the same test the following day and
    the gap appears then, which is the honest order.
    """
    if store.newest_attempt_at(FEED) is None:
        return UNPUBLISHED
    read_at = store.newest_read_at(FEED)
    if read_at is None:
        return Block(published=True, value=None)
    spans = sorted({int(days) for days in windows})
    if not spans or spans[0] < 1:
        raise ValueError("a window is a whole number of days, at least one")
    today = as_of.astimezone(kpszsu.KYIV).date()
    # One day wider than the longest window, because the anchor can fall back
    # a day and that day's window reaches one night further into the past.
    floor = (today - timedelta(days=spans[-1])).isoformat()
    rows = store.strike_nights_since(floor)
    if not rows:
        return Block(published=True, value=None)
    read = {row["night"]: point(row) for row in rows}
    end = today if today.isoformat() in read else today - timedelta(days=1)
    start = end - timedelta(days=spans[-1] - 1)
    # Dense by construction: one entry per calendar night of the longest
    # window, read or not. See `unread` for why a series with holes in it
    # would draw a picture that looks complete.
    series = [
        read.get((start + timedelta(days=step)).isoformat())
        or unread(start + timedelta(days=step))
        for step in range((end - start).days + 1)
    ]
    return Block(published=True, value={
        "read_at": _parse_stored(read_at).isoformat(timespec="seconds"),
        "as_of_date": today.isoformat(),
        "latest_night": max(read),
        "windows": [window(series, days, end) for days in spans],
        "nights": series,
    })
