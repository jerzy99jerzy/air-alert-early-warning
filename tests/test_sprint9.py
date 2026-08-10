"""Sprint 9, T16: the means of attack is its own stream, joined by area and time.

F25 recorded the shape in sprint 4 and the code kept `kind` as an attribute of
an alert for five sprints. Measured on the twenty real messages held as
fixtures: 15 carry an alert state, 4 carry a kind marker, **none carry both**.
So every live alert had `kind = UNKNOWN`, every regime rule tested for MISSILE
or DRONE, and the regime split that this project's central finding rests on
could not fire outside the fixture generator. The same class as F65, one field
over, and it is the reason these tests assert on a live-shaped path rather than
on a constructed event.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.areas import AreaTable
from mavo.kinds import DEFAULT_KIND_TTL, KindIndex, apply_kinds
from mavo.schema import AlertState, KindEvent, KindState, ThreatEvent, ThreatKind
from mavo.sources.telegram import TelegramChannelSource, classify_kind_message
from mavo.store import EventStore
from mavo.transport import StubTransport

TXT = '<div class="tgme_widget_message_text js-message_text">'
T0 = datetime(2026, 9, 1, 20, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def areas() -> AreaTable:
    return AreaTable.from_csv()


def _page(post_id: int, when: datetime, text: str) -> str:
    return (
        f'<div class="tgme_widget_message" data-post="air_alert_ua/{post_id}">'
        f"{TXT}{text}</div>"
        f'<a class="tgme_widget_message_date">'
        f'<time datetime="{when.isoformat()}"></time></a></div>'
    )


def _kind(kind: ThreatKind, state: KindState, when: datetime, oblast: str = "lviv") -> KindEvent:
    return KindEvent(
        area_id="UA46060000000042587",
        kind=kind,
        state=state,
        ts_source=when,
        ts_ingest=when,
        source_id="telegram",
        oblast=oblast,
    )


def test_t16_a_declaration_is_its_own_event_not_an_alert(areas: AreaTable) -> None:
    """The whole defect in one assertion: two messages, two streams."""
    body = _page(1, T0, "Загроза застосування ударних БпЛА #Львівський_район") + _page(
        2, T0 + timedelta(hours=1), "🔴 Повітряна тривога #Львівський_район"
    )
    source = TelegramChannelSource(StubTransport(body), areas=areas)
    alerts = source.poll()

    assert len(alerts) == 1, "the declaration became an alert"
    assert len(source.kind_events) == 1, "the declaration reached no stream at all"
    assert source.kind_events[0].kind is ThreatKind.DRONE
    assert source.kind_events[0].state is KindState.DECLARED
    # And it is no longer counted as a parse failure, which is what it was.
    assert source.report.unparsed_count == 0


def test_t16_the_join_gives_a_live_alert_its_regime(areas: AreaTable) -> None:
    """Before this, every live alert was UNKNOWN and no regime rule could fire."""
    body = _page(1, T0, "Загроза застосування ударних БпЛА #Львівський_район") + _page(
        2, T0 + timedelta(hours=1), "🔴 Повітряна тривога #Львівський_район"
    )
    source = TelegramChannelSource(StubTransport(body), areas=areas)
    alerts = source.poll()
    assert alerts[0].kind is ThreatKind.UNKNOWN, "the alert message names no means"

    joined, report = apply_kinds(alerts, KindIndex(source.kind_events))
    assert joined[0].kind is ThreatKind.DRONE
    assert report.joined == 1 and report.carried == 0
    assert report.coverage == 1.0 and report.join_coverage == 1.0


def test_t16_a_lift_ends_the_declaration() -> None:
    """"Відбій загрози" is not "Відбій тривоги" and closes a different thing."""
    index = KindIndex(
        [
            _kind(ThreatKind.DRONE, KindState.DECLARED, T0),
            _kind(ThreatKind.DRONE, KindState.LIFTED, T0 + timedelta(hours=2)),
        ]
    )
    assert index.active("lviv", T0 + timedelta(hours=1)) == {ThreatKind.DRONE}
    assert index.active("lviv", T0 + timedelta(hours=3)) == frozenset()


def test_t16_a_declaration_without_a_lift_expires() -> None:
    """The TTL, and why it exists.

    A declaration whose lift never arrives would otherwise stay attached to the
    oblast forever: confidently wrong at unbounded distance from the evidence,
    which is worse than unknown. The six-hour default is an assumption carrying
    a label, not a measurement, and `tools/kind_coverage.py` is what replaces it.
    """
    index = KindIndex([_kind(ThreatKind.DRONE, KindState.DECLARED, T0)])
    assert index.active("lviv", T0 + DEFAULT_KIND_TTL - timedelta(minutes=1))
    assert index.active("lviv", T0 + DEFAULT_KIND_TTL) == frozenset()


def test_t16_two_kinds_at_once_resolve_to_unknown_not_to_a_pick() -> None:
    """A mixed strike is ambiguous, and ambiguity is unknown.

    Choosing the first, the newest, or the more dangerous would each be a
    fabrication with a rationale attached.
    """
    index = KindIndex(
        [
            _kind(ThreatKind.DRONE, KindState.DECLARED, T0),
            _kind(ThreatKind.MISSILE, KindState.DECLARED, T0 + timedelta(minutes=5)),
        ]
    )
    alert = ThreatEvent(
        area_id="UA46060000000042587",
        state=AlertState.ACTIVE,
        ts_source=T0 + timedelta(minutes=30),
        ts_ingest=T0 + timedelta(minutes=30),
        source_id="telegram",
        oblast="lviv",
    )
    joined, report = apply_kinds([alert], index)
    assert joined[0].kind is ThreatKind.UNKNOWN
    assert report.ambiguous == 1
    assert report.resolved == 0 and report.joined == 0


def test_t16_a_message_that_states_its_own_kind_is_not_overwritten() -> None:
    """A message beats an inference from a neighbouring message."""
    index = KindIndex([_kind(ThreatKind.DRONE, KindState.DECLARED, T0)])
    alert = ThreatEvent(
        area_id="UA46060000000042587",
        state=AlertState.ACTIVE,
        ts_source=T0 + timedelta(minutes=30),
        ts_ingest=T0 + timedelta(minutes=30),
        source_id="telegram",
        kind=ThreatKind.MISSILE,
        oblast="lviv",
    )
    joined, report = apply_kinds([alert], index)
    assert joined[0].kind is ThreatKind.MISSILE
    # And the join takes no credit for it: the counter split that keeps
    # `coverage` from flattering the join with regimes it never touched.
    assert report.carried == 1 and report.joined == 0
    assert report.coverage == 1.0 and report.join_coverage == 0.0


def test_t16_a_declaration_elsewhere_does_not_reach_this_oblast() -> None:
    """The join is by oblast. A declaration over Kharkiv says nothing about Lviv."""
    index = KindIndex([_kind(ThreatKind.DRONE, KindState.DECLARED, T0, oblast="kharkiv")])
    assert index.active("lviv", T0 + timedelta(minutes=10)) == frozenset()


def test_t16_an_alert_message_is_never_read_as_a_declaration(areas: AreaTable) -> None:
    """One text, one reader. A message carrying an alert state is an alert."""
    assert classify_kind_message("🔴 Повітряна тривога #Львівський_район", areas) == ()


def test_t16_a_declaration_naming_no_means_is_not_resolved_to_one(areas: AreaTable) -> None:
    """Refuses rather than guesses, like every other unresolved thing here."""
    assert classify_kind_message("Загроза застосування невідомого #Львівський_район", areas) == ()


def test_t16_the_stream_survives_a_write_and_a_replay(tmp_path: Path) -> None:
    """Its own table, idempotent by content hash, or the index cannot be rebuilt."""
    store = EventStore(tmp_path / "kinds.sqlite")
    event = _kind(ThreatKind.GLIDE_BOMB, KindState.DECLARED, T0)
    assert store.append_kinds([event]) == 1
    assert store.append_kinds([event]) == 0, "a re-read appended the declaration twice"
    (restored,) = list(store.replay_kinds())
    assert restored.kind is ThreatKind.GLIDE_BOMB
    assert restored.state is KindState.DECLARED
    assert restored.oblast == "lviv"


def test_t16_a_late_lift_is_honoured_over_the_assumption() -> None:
    """The source outranks the TTL, which exists only for a missing lift.

    A declaration lifted nine hours later ran for nine hours: the channel said
    so. Capping that at the six-hour assumption would let a number written in
    this repository overrule a statement made by the source, which is the
    inversion this project exists to avoid.
    """
    index = KindIndex(
        [
            _kind(ThreatKind.DRONE, KindState.DECLARED, T0),
            _kind(ThreatKind.DRONE, KindState.LIFTED, T0 + timedelta(hours=9)),
        ]
    )
    assert index.active("lviv", T0 + timedelta(hours=8)) == {ThreatKind.DRONE}
    assert index.active("lviv", T0 + timedelta(hours=10)) == frozenset()
