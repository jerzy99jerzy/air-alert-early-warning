"""Scripted attacks, one per threat-model row. Catalogue in CATALOGUE.md.

These are not unit tests of the modules they touch. Each one plays an adversary
and asserts the product's observable response, so that a refactor which keeps
the unit tests green but loses a control still fails here.
"""

from __future__ import annotations

import random
from dataclasses import replace
from datetime import UTC, datetime, timedelta
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

T0 = datetime(2026, 9, 1, 21, 0, 0, tzinfo=UTC)
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
    """MT4. Attention exhaustion is refused even by a rule that never misses.

    F38. The earlier table failed the gate on association as well as on alarm
    rate, and the assertion looked for the substring "alarm rate", which the
    *passing* reason also contains. Both halves were satisfiable with the alarm
    budget disabled. The table now clears recall and association, so alarm rate
    is the only condition left to fail, and the assertion names the failure.
    """
    assessment = assess_rule(
        "exhauster", Contingency(a=20, b=200, c=0, d=800), observation_weeks=100
    )
    verdict = gate(assessment)
    assert assessment.recall == 1.0
    assert assessment.p_value < 0.05, "the table must clear association, or this proves nothing"
    assert verdict.passes is False
    assert any("exceeds" in reason for reason in verdict.reasons)


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

    # F39. These were single-quoted, and the page serves double quotes, so the
    # message regex matched nothing and every hostile body was absorbed without
    # the parser ever seeing it. The attack passed by not arriving. The same
    # rule holds under the block parser (F50): a message must carry the
    # data-post anchor the live page always carries, or it never becomes a
    # message at all — so every hostile body below except the first two is
    # anchored, and the reached-counter still guards against a silent miss.
    txt = '<div class="tgme_widget_message_text js-message_text">'

    def anchored(inner: str, post: int) -> str:
        return f'<div class="tgme_widget_message" data-post="air_alert_ua/{post}">{inner}</div>'

    hostile = [
        "",
        "not html",
        anchored(f'<time datetime="nonsense"></time>{txt}Львів тривога</div>', 901),
        anchored(f"{txt}{'А' * 80_000}</div>", 902),
        anchored(f"{txt}\x00\x01\x02</div>", 903),
        anchored(
            f'{txt}wording nobody anticipated</div>'
            f'<time datetime="2026-09-01T21:00:00+00:00"></time>',
            904,
        ),
    ]
    reached = 0
    for body in hostile:
        source = TelegramChannelSource(StubTransport(body))
        assert source.poll() is not None
        assert source.report.parsed <= source.report.messages
        reached += source.report.messages
    assert reached > 0, "no hostile body reached the parser; this attack proves nothing"


def test_a10_an_unreachable_source_is_not_a_quiet_one() -> None:
    """MT11. An outage must not be indistinguishable from an empty sky."""
    from mavo.errors import SourceUnavailable
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import FailingTransport

    with pytest.raises(SourceUnavailable):
        TelegramChannelSource(FailingTransport()).poll()


def test_a11_a_skipped_window_cannot_pass_as_a_quiet_channel() -> None:
    """MT12. A mass alert overflows the page; the skip must be observable.

    Two failure shapes in one attack. Messages that pass between polls are
    counted, and a page that carries no post ids reports unknown rather than
    zero, because losing the observable must not look like observing calm.
    """
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import StubTransport

    def page(ids: list[int]) -> str:
        txt = '<div class="tgme_widget_message_text js-message_text">'
        return "".join(
            f'<div class="tgme_widget_message" data-post="air_alert_ua/{post}">'
            f'<time datetime="2026-09-01T21:00:00+00:00"></time>'
            f"{txt}Львівська область<br/>Повітряна тривога</div></div>"
            for post in ids
        )

    source = TelegramChannelSource(StubTransport(page([500, 501])))
    source.poll()
    source.transport = StubTransport(page([560, 561]))
    source.poll()
    assert source.report.skipped == 58, "a skipped window passed as continuity"
    assert source.report.gap_is_known is True

    # F40. The first version of this attack asserted unknown only for a page
    # with no ids, which `_window` answers before reaching the code that decides
    # unknown-versus-zero. The first-poll case is the one that governs it.
    fresh = TelegramChannelSource(StubTransport(page([700, 701])))
    fresh.poll()
    assert fresh.report.skipped is None, "a first poll invented a baseline it does not have"

    blind = TelegramChannelSource(StubTransport("<html>no post ids</html>"))
    blind.poll()
    assert blind.report.skipped is None, "an unmeasurable gap reported as zero"


def test_a12_the_footer_time_cannot_shift_onto_a_neighbour() -> None:
    """MT13. Timestamps must pair within a message block, never across one.

    The live page carries each message's time in its footer, after the text. A
    page-wide scan that requires time-then-text pairs message N's time with
    message N+1's text: every event one message late, the first text dropped,
    the last time orphaned (F50). In the missile regime the whole warning
    budget is about six minutes, so a one-message shift in ``ts_source`` is not
    cosmetic; it is the lead-time measurement quietly poisoned. The assertion
    is exact equality on both pairs, so a shift in either direction goes red.
    """
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import StubTransport

    txt = '<div class="tgme_widget_message_text js-message_text">'
    page = (
        '<div class="tgme_widget_message" data-post="air_alert_ua/601">'
        f"{txt}🔴 Львівська область Повітряна тривога</div>"
        '<time datetime="2026-09-01T21:04:00+00:00"></time></div>'
        '<div class="tgme_widget_message" data-post="air_alert_ua/602">'
        f"{txt}🔴 Волинська область Повітряна тривога</div>"
        '<time datetime="2026-09-01T21:11:00+00:00"></time></div>'
    )
    source = TelegramChannelSource(StubTransport(page))
    stamped = {event.area_id: event.ts_source.isoformat() for event in source.poll()}
    assert stamped == {
        "lviv": "2026-09-01T21:04:00+00:00",
        "volyn": "2026-09-01T21:11:00+00:00",
    }, "a footer timestamp crossed a message boundary"
