"""Scripted attacks, one per threat-model row. Catalogue in CATALOGUE.md.

These are not unit tests of the modules they touch. Each one plays an adversary
and asserts the product's observable response, so that a refactor which keeps
the unit tests green but loses a control still fails here.
"""

from __future__ import annotations

import random
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from mavo.baserate import Contingency, assess_rule, gate
from mavo.errors import BudgetOverAllocated
from mavo.evaluate import run_policy
from mavo.policy import DecisionPolicy, Regime, RegimeRule, equal_split
from mavo.rules import CANDIDATE_RULES, conjunction, drone_conjunction
from mavo.schema import AlertState, ThreatEvent, ThreatKind, is_clear
from mavo.sources.fixture import FixtureSource, build_night, generate_history
from mavo.store import EventStore

T0 = datetime(2026, 9, 1, 21, 0, 0)
MISSILE = (Regime.MISSILE, "CONJ-missile", conjunction)
DRONE = (Regime.DRONE, "CONJ-drone", drone_conjunction)


def test_a1_broad_simultaneous_activation_raises_nothing() -> None:
    """MT1. A source claiming the whole country is alight must produce no alarm."""
    night = build_night(T0, "poisoned-feed", random.Random(1))
    fired = {name: rule(night) for name, rule in CANDIDATE_RULES.items()}
    assert set(fired.values()) == {None}, f"suppression walked through: {fired}"


def test_a2_a_silent_feed_is_not_an_all_clear() -> None:
    """MT2. Degradation must not read as safety, in either direction."""
    night = build_night(T0, "degraded-feed", random.Random(1))
    assert conjunction(night) is None
    assert is_clear(AlertState.UNKNOWN) is False


def test_a3_one_fabricated_alert_cannot_raise_an_alarm() -> None:
    """MT3. A single area with no vector behind it is not an inbound raid."""
    assert conjunction(build_night(T0, "border-only", random.Random(1))) is None


def test_a4_perfect_recall_does_not_buy_past_the_alarm_budget() -> None:
    """MT4. Attention exhaustion is refused even by a rule that never misses."""
    assessment = assess_rule(
        "exhauster", Contingency(a=8, b=600, c=0, d=100), observation_weeks=100
    )
    verdict = gate(assessment)
    assert assessment.recall == 1.0
    assert verdict.passes is False
    assert any("alarm rate" in reason for reason in verdict.reasons)


def test_a5_budget_cannot_be_spent_twice() -> None:
    """MT5. Two regimes cannot each hold the whole of a shared budget."""
    with pytest.raises(BudgetOverAllocated):
        DecisionPolicy(
            rules=(
                RegimeRule(Regime.MISSILE, "a", conjunction, 2.0),
                RegimeRule(Regime.DRONE, "b", drone_conjunction, 2.0),
            ),
            total_budget_per_week=2.0,
        )


def test_a6_a_partial_policy_cannot_read_as_complete() -> None:
    """MT6. An unserved crossing kind is counted and printed, never absorbed."""
    run = run_policy(equal_split([MISSILE]), generate_history(weeks=208))
    assert run.combined.assessment.recall == 1.0
    assert run.has_coverage_gap is True
    assert "COVERAGE GAP" in run.summary()


def test_a7_hostile_payloads_do_not_become_an_outage() -> None:
    """MT7. A parser that raises turns a hostile string into an outage.

    Fixture path only. No live adapter exists, and the catalogue says so rather
    than implying coverage this does not have.
    """
    source = FixtureSource([])
    assert list(source.poll()) == []

    for scenario in ("quiet", "poisoned-feed", "degraded-feed"):
        night = build_night(T0, scenario, random.Random(3))
        assert FixtureSource([night]).poll() is not None


def test_a8_replaying_a_feed_does_not_grow_the_log(tmp_path: Path) -> None:
    """MT8. Re-polling an unchanged transition must cost nothing."""
    store = EventStore(tmp_path / "attack.sqlite")
    event = ThreatEvent(
        area_id="lviv",
        state=AlertState.ACTIVE,
        ts_source=T0,
        ts_ingest=T0 + timedelta(seconds=30),
        source_id="attacker",
        kind=ThreatKind.MISSILE,
    )
    # An attacker replaying the same transition with a fresh ingest time every
    # 30 seconds for an hour must not be able to grow the log.
    for minute in range(120):
        store.append([replace(event, ts_ingest=T0 + timedelta(minutes=minute))])
    assert store.count() == 1


def test_a9_hostile_bodies_to_the_live_adapter_do_not_raise() -> None:
    """MT7. The Telegram adapter absorbs content failures and reports them."""
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import StubTransport

    txt = "<div class='tgme_widget_message_text'>"
    hostile = [
        "",
        "not html",
        f"<time datetime='nonsense'></time>{txt}Львів тривога</div>",
        f"{txt}{'А' * 80_000}</div>",
        f"{txt}\x00\x01\x02</div>",
        f"<time datetime='2026-09-01T21:00:00+00:00'></time>{txt}wording nobody anticipated</div>",
    ]
    for body in hostile:
        source = TelegramChannelSource(StubTransport(body))
        assert source.poll() is not None
        assert source.report.parsed <= source.report.messages


def test_a10_an_unreachable_source_is_not_a_quiet_one() -> None:
    """MT11. An outage must not be indistinguishable from an empty sky."""
    from mavo.errors import SourceUnavailable
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import FailingTransport

    with pytest.raises(SourceUnavailable):
        TelegramChannelSource(FailingTransport()).poll()
