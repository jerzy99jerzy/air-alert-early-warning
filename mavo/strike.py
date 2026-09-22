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
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from mavo.poland import UNPUBLISHED, Block
from mavo.sources import kpszsu
from mavo.store import EventStore

FEED = kpszsu.FEED


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
    """Their headline figure: the total, or their two figures added together.

    Deliberately not `kpszsu.downed_total`, whose third branch adds up the
    items when every one of them carries a count. That branch is right for the
    reader, which checks a reading against itself; it is wrong here, because on
    a flagged night the items are our reading and the headline is theirs, and
    the contract publishes theirs.
    """
    head = tally["headline"]
    if head["total"] is not None:
        return int(head["total"])
    if head["missiles"] is not None and head["drones"] is not None:
        return int(head["missiles"]) + int(head["drones"])
    return None


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
