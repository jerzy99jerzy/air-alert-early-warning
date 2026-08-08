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
