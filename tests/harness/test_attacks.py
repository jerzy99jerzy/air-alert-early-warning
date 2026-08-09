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
from mavo.evaluate import run_policy
from mavo.policy import Regime, policy_of
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


def test_a4_perfect_recall_does_not_buy_past_the_lift_floor() -> None:
    """MT4. A rule that fires on nearly everything cannot pass by never missing.

    F38, in its original form: the earlier table failed on association as well
    as on the gated condition, and the assertion looked for a substring the
    *passing* reason also contained, so both halves were satisfiable with the
    control disabled. The table below clears recall and association, leaving the
    lift floor as the only condition able to fail, and the assertion names it.

    Rewritten at 0.8.0.0 (D-014). The gated condition used to be the alarm rate;
    it is now the lower bound on lift. The attack is the same attack, because
    what it always tested was whether a rule can buy an alarm by firing broadly
    enough to be right eventually.
    """
    # A calendar: 12 events over 1460 windows, firing on 57% of them and
    # catching all of them. Recall is perfect, the association is significant,
    # and the firing still tells the recipient nothing they did not have from
    # the date. The old table used here fired often *and* carried information,
    # so under the lift floor it passes, correctly: firing often is no longer
    # the offence. Firing uninformatively is.
    assessment = assess_rule(
        "calendar", Contingency(a=12, b=820, c=0, d=628), observation_weeks=208
    )
    verdict = gate(assessment)
    assert assessment.recall == 1.0
    assert assessment.p_value < 0.05, "the table must clear association, or this proves nothing"
    assert verdict.passes is False
    assert any("lift lower bound" in reason and "below floor" in reason
               for reason in verdict.reasons)


def test_a6_a_partial_policy_cannot_read_as_complete() -> None:
    """MT6. An unserved crossing kind is counted and printed, never absorbed."""
    run = run_policy(policy_of([MISSILE]), generate_history(weeks=208))
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


def test_a13_an_unknown_tag_is_not_replaced_by_a_prose_guess() -> None:
    """MT14. The area the channel named, but the map cannot read, stays unread.

    F60. The sprint 7 fallback fired whenever the tag path produced nothing,
    which is wider than its justification. A message tagging an area the map
    does not know, and mentioning an oblast in prose, resolved to that oblast
    from the table that scores 0 of 20 on real content. The unknown tag was
    still reported, so the failure looked like an accounting quirk rather than
    what it was: an event carrying a guess about where the danger is.

    The adversarial reading is the one that makes it an attack rather than a
    bug. The channel's vocabulary drifts on its own schedule, and an attacker
    who can get one unrecognised tag into a message with an oblast name in it
    obtains a warning that names the wrong place. A report naming the wrong
    place is worse than no report, because it is actionable.
    """
    from mavo.areas import AreaTable
    from mavo.sources.telegram import classify

    table = AreaTable.from_csv()
    misleading = "Львівська область #Вигаданський_район Повітряна тривога"
    assert classify(misleading, table) is None, "a prose guess replaced an unknown tag"
    assert classify(misleading) is not None, "the untagged fallback must still work"


def test_a14_a_still_dangerous_area_is_not_silently_dropped() -> None:
    """MT15. An all-clear must not speak for the areas it says are still alight.

    The channel writes the cleared area as a tag and the areas where the alert
    continues as prose after a marker. Reading only the tags produced an
    all-clear and nothing else, which is the system going quiet about a place
    its own source had just called dangerous. The attack is the message itself,
    verbatim in shape from the corpus.
    """
    from mavo.areas import AreaTable
    from mavo.schema import AlertState, AreaRole
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import StubTransport

    text = (
        "🟢 15:53 Відбій тривоги в Куп’янський район.\n"
        "Зверніть увагу, тривога ще триває у:\n- Пологівський район\n#Купянський_район"
    )
    body = (
        '<div class="tgme_widget_message" data-post="air_alert_ua/7001">'
        f'<div class="tgme_widget_message_text js-message_text">{text}</div>'
        '<a class="tgme_widget_message_date">'
        '<time datetime="2026-09-01T21:00:00+00:00"></time></a></div>'
    )
    events = TelegramChannelSource(StubTransport(body), areas=AreaTable.from_csv()).poll()

    continuing = [event for event in events if event.role is AreaRole.CONTINUATION]
    assert continuing, "the still-running area left no trace; the all-clear spoke alone"
    assert all(event.state is AlertState.ACTIVE for event in continuing)
    cleared = [event for event in events if event.role is AreaRole.SUBJECT]
    assert [event.state for event in cleared] == [AlertState.CLEAR]
    assert continuing[0].area_id != cleared[0].area_id
