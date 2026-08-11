"""Append-only store: idempotence, ordering and round-tripping."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from mavo.schema import ThreatEvent
from mavo.store import EventStore


def test_append_is_idempotent(store_path: Path, event: ThreatEvent) -> None:
    store = EventStore(store_path)
    assert store.append([event]) == 1
    assert store.append([event]) == 0
    assert store.count() == 1


def test_repoll_with_new_ingest_time_does_not_duplicate(
    store_path: Path, event: ThreatEvent
) -> None:
    store = EventStore(store_path)
    store.append([event])
    store.append([replace(event, ts_ingest=event.ts_ingest + timedelta(minutes=2))])
    assert store.count() == 1


def test_append_of_nothing_is_not_an_error(store_path: Path) -> None:
    assert EventStore(store_path).append([]) == 0


def test_replay_round_trips_every_field(store_path: Path, event: ThreatEvent) -> None:
    store = EventStore(store_path)
    store.append([event])
    (restored,) = list(store.replay())
    assert restored.area_id == event.area_id
    assert restored.state is event.state
    assert restored.kind is event.kind
    assert restored.provenance is event.provenance
    assert restored.ts_source == event.ts_source


def test_replay_is_ordered_by_source_time(store_path: Path, event: ThreatEvent) -> None:
    later = replace(event, area_id="volyn", ts_source=event.ts_source + timedelta(minutes=10))
    store = EventStore(store_path)
    store.append([later, event])
    assert [e.area_id for e in store.replay()] == ["lviv", "volyn"]


# --- F52, the ordering contract ----------------------------------------------

def test_f52_a_naive_timestamp_is_refused_at_the_boundary(store_path: Path) -> None:
    """The store orders by ISO text; a timestamp without an offset breaks that.

    Refused rather than repaired, because repairing means inventing an offset.
    """
    from datetime import datetime

    import pytest

    from mavo.errors import NaiveTimestamp
    from mavo.schema import AlertState

    naive = ThreatEvent(
        area_id="lviv",
        state=AlertState.ACTIVE,
        ts_source=datetime(2026, 9, 1, 21, 0, 0),
        ts_ingest=datetime(2026, 9, 1, 21, 0, 30),
        source_id="test",
    )
    with pytest.raises(NaiveTimestamp):
        EventStore(store_path).append([naive])


def test_f52_mixed_offsets_replay_in_true_chronology(store_path: Path) -> None:
    """21:00+02:00 is 19:00 UTC and must replay before 20:00+00:00.

    Lexicographic order over the raw strings puts them the other way around;
    normalizing to UTC at append is what makes the text order the time order.
    """
    from datetime import UTC, datetime, timedelta, timezone

    from mavo.schema import AlertState

    plus_two = timezone(timedelta(hours=2))
    earlier_wall_clock_later_instant = ThreatEvent(
        area_id="volyn",
        state=AlertState.ACTIVE,
        ts_source=datetime(2026, 9, 1, 20, 0, 0, tzinfo=UTC),
        ts_ingest=datetime(2026, 9, 1, 20, 0, 30, tzinfo=UTC),
        source_id="test",
    )
    later_wall_clock_earlier_instant = ThreatEvent(
        area_id="lviv",
        state=AlertState.ACTIVE,
        ts_source=datetime(2026, 9, 1, 21, 0, 0, tzinfo=plus_two),  # 19:00 UTC
        ts_ingest=datetime(2026, 9, 1, 21, 0, 30, tzinfo=plus_two),
        source_id="test",
    )
    store = EventStore(store_path)
    store.append([earlier_wall_clock_later_instant, later_wall_clock_earlier_instant])
    replayed = [event.area_id for event in store.replay()]
    assert replayed == ["lviv", "volyn"]


def test_f52_two_spellings_of_one_instant_are_one_transition(store_path: Path) -> None:
    # The same moment reported as +02:00 by one poll and +00:00 by another must
    # hash identically, or idempotence silently depends on the reporter's clock
    # presentation rather than on the transition.
    from datetime import UTC, datetime, timedelta, timezone

    from mavo.schema import AlertState

    plus_two = timezone(timedelta(hours=2))

    def at(tz: object) -> ThreatEvent:
        return ThreatEvent(
            area_id="lviv",
            state=AlertState.ACTIVE,
            ts_source=datetime(2026, 9, 1, 21, 0, 0, tzinfo=tz),  # type: ignore[arg-type]
            ts_ingest=datetime(2026, 9, 1, 21, 5, 0, tzinfo=UTC),
            source_id="test",
        )

    local = at(plus_two)
    utc = at(timezone(timedelta(hours=0)))
    assert local.ts_source == utc.ts_source - timedelta(hours=2)  # distinct instants: differ
    same_instant_local = ThreatEvent(
        area_id="lviv",
        state=AlertState.ACTIVE,
        ts_source=datetime(2026, 9, 1, 23, 0, 0, tzinfo=plus_two),  # == 21:00 UTC
        ts_ingest=datetime(2026, 9, 1, 21, 5, 0, tzinfo=UTC),
        source_id="test",
    )
    assert same_instant_local.content_hash() == utc.content_hash()
    store = EventStore(store_path)
    assert store.append([utc, same_instant_local]) == 1


def _many(event: ThreatEvent, count: int) -> list[ThreatEvent]:
    """`count` distinct events, ordered and unique on `(ts_source, area_id)`."""
    return [
        replace(
            event,
            area_id=f"UA{index:017d}",
            ts_source=event.ts_source + timedelta(minutes=index),
        )
        for index in range(count)
    ]


def test_an_abandoned_replay_does_not_hold_a_connection(
    store_path: Path, event: ThreatEvent
) -> None:
    """F94. The reader used to keep a connection open across every yield.

    A caller that started a replay and kept the iterator without finishing it
    held the connection for as long as it held the generator, and garbage
    collection did not reliably take it back. Measured on the pre-repair store,
    2026-08-11: 100 started-and-retained iterators held 201 descriptors, and
    102 were still held after `del` and an explicit `gc.collect()`.

    The assertion is on descriptors rather than on structure, because the
    structure is not the promise - the promise is that abandoning a replay
    costs nothing that has to be reclaimed. Mutation: restore the single
    `with closing(self._connect())` around the yield loop.
    """
    import os

    if not Path("/proc/self/fd").is_dir():  # pragma: no cover - platform guard
        pytest.skip("descriptor count needs /proc; the store itself is portable")

    store = EventStore(store_path)
    store.append(_many(event, 40))
    baseline = len(os.listdir("/proc/self/fd"))
    started = []
    for _ in range(50):
        iterator = store.replay()
        next(iterator)  # start it, then never finish it
        started.append(iterator)
    assert len(os.listdir("/proc/self/fd")) == baseline, (
        "an abandoned replay is holding an open connection"
    )


def test_replay_crosses_chunk_boundaries_without_losing_or_repeating_a_row(
    store_path: Path, event: ThreatEvent
) -> None:
    """The keyset paging must be exact, not approximately exact.

    Chunking is the F94 repair, and it introduces the one failure the single
    connection could not have: a boundary that skips a row or serves it twice.
    The store holds more than two chunks, and the replay must be the whole log,
    in order, once each. Mutation: page with LIMIT/OFFSET, or compare with `>=`.
    """
    store = EventStore(store_path)
    total = EventStore.CHUNK * 2 + 7
    store.append(_many(event, total))
    replayed = [item.area_id for item in store.replay()]
    assert len(replayed) == total
    assert len(set(replayed)) == total, "a row was served twice across a boundary"
    assert replayed == sorted(replayed), "chunking lost the source-time order"


def test_a_sort_key_tie_on_a_chunk_boundary_loses_no_row(
    store_path: Path, event: ThreatEvent
) -> None:
    """Two rows may legitimately share `(ts_source, area_id)`, and paging must survive it.

    The schema is unique on `content_hash`, not on the sort key: T37's own
    example is one message that clears an area and lists the same area as still
    under alert, two rows with one timestamp. Strict keyset comparison on the
    tied pair drops whichever row the boundary cuts off, and the row it drops
    can be the one saying the area is still dangerous. The exactness test above
    could not see this because `_many` builds keys that never tie - the data
    was chosen by the implementation. Mutation: page on `(ts_source, area_id)`
    without the hash tiebreak.
    """
    from mavo.schema import AlertState, AreaRole

    store = EventStore(store_path)
    filler = _many(event, EventStore.CHUNK - 1)
    tied_ts = event.ts_source + timedelta(days=365)
    cleared = replace(event, area_id="UAZZZ", ts_source=tied_ts,
                      state=AlertState.CLEAR, role=AreaRole.SUBJECT)
    still_active = replace(event, area_id="UAZZZ", ts_source=tied_ts,
                           state=AlertState.ACTIVE, role=AreaRole.CONTINUATION)
    appended = store.append([*filler, cleared, still_active])
    assert appended == EventStore.CHUNK + 1, "the tied pair must be two rows"
    replayed = list(store.replay())
    assert len(replayed) == EventStore.CHUNK + 1, (
        "a chunk boundary inside a sort-key tie dropped a row"
    )
    states = {(item.area_id, item.state, item.role) for item in replayed}
    assert (cleared.area_id, AlertState.ACTIVE, AreaRole.CONTINUATION) in states, (
        "the row silently lost was the one saying the area is still under alert"
    )


def test_a_store_of_exactly_one_chunk_terminates(
    store_path: Path, event: ThreatEvent
) -> None:
    """The off-by-one that would loop forever, or query forever.

    A full final chunk cannot be distinguished from a chunk with more behind it
    without asking again, and asking again must terminate on the empty answer.
    Mutation: drop the `if not rows: return` guard.
    """
    store = EventStore(store_path)
    store.append(_many(event, EventStore.CHUNK))
    assert len(list(store.replay())) == EventStore.CHUNK
