"""Rule behaviour, including the adversarial cases the clean ones miss."""

from __future__ import annotations

import random
from datetime import datetime

import pytest

from mavo.errors import UnknownScenario
from mavo.rules import (
    conjunction,
    is_poisoned,
    r1_border_active,
    r2_westward_escalation,
    r3_border_missile,
)
from mavo.sources.fixture import build_night

T0 = datetime(2026, 3, 1, 21, 0, 0)


def _night(scenario: str, seed: int = 7):
    return build_night(T0, scenario, random.Random(seed))


def test_quiet_night_fires_nothing() -> None:
    night = _night("quiet")
    assert r1_border_active(night) is None
    assert conjunction(night) is None


def test_missile_night_fires_the_conjunction() -> None:
    assert conjunction(_night("clean-missile")) is not None


def test_border_only_does_not_fire_the_conjunction() -> None:
    # Wrong vector: the far south-west alone is not an inbound raid.
    night = _night("border-only")
    assert r1_border_active(night) is not None
    assert r2_westward_escalation(night) is None
    assert conjunction(night) is None


def test_poisoned_feed_is_suppressed_entirely() -> None:
    night = _night("poisoned-feed")
    assert is_poisoned(night) is True
    assert r1_border_active(night) is None
    assert r3_border_missile(night) is None
    assert conjunction(night) is None


def test_degraded_feed_unknown_states_do_not_raise_an_alarm() -> None:
    # UNKNOWN must contribute nothing to a warning decision, in either direction.
    night = _night("degraded-feed")
    assert r3_border_missile(night) is None
    assert conjunction(night) is None


def test_conjunction_fires_no_earlier_than_its_weakest_conjunct() -> None:
    night = _night("clean-missile")
    fired = conjunction(night)
    missile = r3_border_missile(night)
    escalation = r2_westward_escalation(night)
    assert fired is not None and missile is not None and escalation is not None
    assert fired >= missile and fired >= escalation


def test_unknown_scenario_is_rejected_rather_than_silently_empty() -> None:
    with pytest.raises(UnknownScenario, match="unknown scenario"):
        build_night(T0, "not-a-scenario", random.Random(1))
