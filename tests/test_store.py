"""Append-only store: idempotence, ordering and round-tripping."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

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
