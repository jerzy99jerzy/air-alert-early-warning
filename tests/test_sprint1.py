"""Sprint 1 regressions: the adapter boundary and the store.

Defect class: a state that means "we do not know" being folded into a state that
means "nothing is happening", and a re-poll of an unchanged feed multiplying rows
until the replay no longer reconstructs the past.

Verified red against a scratch copy where `is_clear` was written as
`state != AlertState.ACTIVE` and the store used a plain INSERT.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from mavo.schema import AlertState, ThreatEvent, is_clear
from mavo.store import EventStore


def test_negation_of_active_is_not_the_definition_of_clear() -> None:
    naive = [state for state in AlertState if state is not AlertState.ACTIVE]
    correct = [state for state in AlertState if is_clear(state)]
    assert naive != correct
    assert AlertState.UNKNOWN in naive
    assert AlertState.UNKNOWN not in correct


def test_repeated_polling_does_not_grow_the_log(store_path: Path, event: ThreatEvent) -> None:
    store = EventStore(store_path)
    for minute in range(5):
        store.append([replace(event, ts_ingest=event.ts_ingest + timedelta(minutes=minute))])
    assert store.count() == 1
    assert len(list(store.replay())) == 1
