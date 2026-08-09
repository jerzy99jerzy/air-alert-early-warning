"""Behaviour of the event schema and its four alert states."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from mavo.schema import (
    AlertState,
    Provenance,
    ThreatEvent,
    ThreatSource,
    is_actionable,
    is_clear,
)


def test_weakest_label_wins() -> None:
    assert Provenance.weakest([Provenance.MEASURED, Provenance.INFERENCE]) is Provenance.INFERENCE


def test_empty_provenance_is_speculation_not_measured() -> None:
    # Absence must not resolve to the flattering label.
    assert Provenance.weakest([]) is Provenance.SPECULATION


@pytest.mark.parametrize(
    ("state", "clear", "actionable"),
    [
        (AlertState.CLEAR, True, False),
        (AlertState.ACTIVE, False, True),
        (AlertState.UNKNOWN, False, False),
    ],
)
def test_tristate_both_directions(state: AlertState, clear: bool, actionable: bool) -> None:
    assert is_clear(state) is clear
    assert is_actionable(state) is actionable


def test_unknown_is_not_the_safe_state() -> None:
    # The defect this guards: `state != ACTIVE` folds UNKNOWN into CLEAR.
    assert is_clear(AlertState.UNKNOWN) is False
    assert (AlertState.UNKNOWN != AlertState.ACTIVE) is True


def test_content_hash_ignores_ingest_time(event: ThreatEvent) -> None:
    later = replace(event, ts_ingest=event.ts_ingest + timedelta(minutes=5))
    assert later.content_hash() == event.content_hash()


def test_content_hash_separates_distinct_transitions(event: ThreatEvent) -> None:
    other = replace(event, area_id="volyn")
    assert other.content_hash() != event.content_hash()


def test_latency_is_stored_not_assumed(event: ThreatEvent) -> None:
    assert event.latency_s == 45.0


def test_fixture_source_satisfies_the_protocol() -> None:
    from mavo.sources.fixture import FixtureSource

    assert isinstance(FixtureSource([]), ThreatSource)
