"""Sprint 8 regressions: every named area reaches the store, in one vocabulary.

Two findings, both of which produced code that was correct in isolation and
wrong in composition.

**T37.** A message can name several areas and the pipeline kept the first.
Worse, an all-clear can carry a list of areas where the alert is *still
running*, written in prose rather than as tags, and nothing recorded any of it:
5.2% of comparable design-window messages, 4,064 area mentions. A report whose
stated product is completeness was dropping the half of the message that says
*still dangerous there*.

**T38.** The rules tested `event.area_id` against `BORDER_OBLASTS`. On the live
path `area_id` is a KATOTTG register code and `BORDER_OBLASTS` holds coarse
slugs, so the comparison could only ever be false: every border predicate was
unsatisfiable outside the fixture, silently, and the fixture is the one input
where it happened to work. Found by an external review, not by a test.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.areas import AreaTable, oblast_slug
from mavo.errors import SchemaMismatch
from mavo.rules import r1_border_active
from mavo.schema import BORDER_OBLASTS, AlertState, AreaRole, ThreatEvent, ThreatKind
from mavo.sources.fixture import Night
from mavo.sources.telegram import TelegramChannelSource, classify_message
from mavo.store import EventStore
from mavo.transport import StubTransport

TXT = '<div class="tgme_widget_message_text js-message_text">'

# The message that produced F26, verbatim from the channel: an all-clear whose
# own continuation list names the same raion as still under alert.
SAME_AREA_CONTRADICTION = (
    "🟡 15:53 Відбій тривоги в Куп’янський район.\n"
    "Зверніть увагу, тривога ще триває у:\n- Куп’янський район\n#Купянський_район"
)

# The shape that costs the most: the all-clear is real for the tagged area and
# the list names a different area where the alert continues.
OTHER_AREA_CONTINUATION = (
    "🟢 15:53 Відбій тривоги в Куп’янський район.\n"
    "Зверніть увагу, тривога ще триває у:\n- Пологівський район\n#Купянський_район"
)


@pytest.fixture
def areas() -> AreaTable:
    return AreaTable.from_csv()


def _page(post_id: int, when: str, text: str) -> str:
    """One message in the live page shape: text first, time in the footer."""
    return (
        f'<div class="tgme_widget_message" data-post="air_alert_ua/{post_id}">'
        f"{TXT}{text}</div>"
        f'<a class="tgme_widget_message_date"><time datetime="{when}"></time></a></div>'
    )


def test_t37_a_continuation_list_produces_more_than_one_event(areas: AreaTable) -> None:
    """The acceptance criterion, asserted end to end through `poll`."""
    body = _page(4001, "2026-09-01T21:00:00+00:00", OTHER_AREA_CONTINUATION)
    events = TelegramChannelSource(StubTransport(body), areas=areas).poll()

    assert len(events) > 1, "the continuation list was discarded; that is the T37 loss"
    by_role = {event.role: event for event in events}
    assert by_role[AreaRole.SUBJECT].state is AlertState.CLEAR
    still_running = by_role[AreaRole.CONTINUATION]
    assert still_running.state is AlertState.ACTIVE
    assert still_running.area_id != by_role[AreaRole.SUBJECT].area_id


def test_t37_the_two_roles_are_distinguishable_not_merged(areas: AreaTable) -> None:
    """An area cleared and an area still running must not read alike.

    The acceptance says continuation areas are *distinguishable* from the
    subject of the all-clear. A consumer matches on the field; a note buried in
    `raw_fields` would not be matchable and would decay into prose.
    """
    mentions = classify_message(OTHER_AREA_CONTINUATION, areas)
    roles = {mention.role for mention in mentions}
    assert roles == {AreaRole.SUBJECT, AreaRole.CONTINUATION}


def test_t37_one_area_told_two_things_stays_a_contradiction(areas: AreaTable) -> None:
    """F26 survives T37: the same area cleared and continuing is PARTIAL_CLEAR.

    Splitting this into a CLEAR row and an ACTIVE row would replace a stated
    contradiction with two confident claims, one of them wrong. The weaker
    reading wins, exactly as it did before the areas could be attributed.
    """
    mentions = classify_message(SAME_AREA_CONTRADICTION, areas)
    assert len(mentions) == 1
    assert mentions[0].state is AlertState.PARTIAL_CLEAR
    assert mentions[0].role is AreaRole.SUBJECT


def test_t37_a_message_naming_several_areas_yields_one_event_each(areas: AreaTable) -> None:
    """13.3% of comparable messages name two to eight areas. All of them count."""
    text = "🔴 Повітряна тривога\n#Львівський_район #Стрийський_район #Самбірський_район"
    mentions = classify_message(text, areas)
    assert len({mention.area_id for mention in mentions}) == 3
    assert all(mention.state is AlertState.ACTIVE for mention in mentions)


def test_t38_a_real_classified_event_can_satisfy_the_border_predicate(
    areas: AreaTable,
) -> None:
    """The defect in one line: this assertion was unsatisfiable before 0.12.0.0.

    A live-shaped event carries a raion register code in `area_id`. While the
    rules compared that code against a set of oblast slugs, no real event could
    ever be a border event, and no test noticed because every test built its
    events from the fixture, where the two vocabularies happen to coincide.
    """
    lviv_tag = next(
        tag for tag in areas.tags if (ref := areas.resolve(tag)) and ref.oblast == "Львівська"
    )
    body = _page(4002, "2026-09-01T21:00:00+00:00", f"🔴 Повітряна тривога\n#{lviv_tag}")
    events = TelegramChannelSource(StubTransport(body), areas=areas).poll()

    assert len(events) == 1
    event = events[0]
    assert event.area_id.startswith("UA"), "area_id is a register code, not a slug"
    assert event.area_id not in BORDER_OBLASTS, "the two vocabularies are still distinct"
    assert event.oblast in BORDER_OBLASTS, "and the coarse one is what the rules read"

    night = Night(
        start=event.ts_source, scenario="live-shaped", events=(event,), crossing_at=None
    )
    assert r1_border_active(night) == event.ts_source


def test_t38_an_unknown_oblast_is_empty_and_matches_nothing() -> None:
    """Unknown is "" and never a member of any oblast set."""
    assert oblast_slug("Нововигадана") == ""
    assert "" not in BORDER_OBLASTS


def test_t38_the_store_round_trips_the_oblast_and_the_role(tmp_path: Path) -> None:
    """Both new fields survive a write and a replay, or they are decoration."""
    event = ThreatEvent(
        area_id="UA46060000000042587",
        state=AlertState.ACTIVE,
        ts_source=datetime(2026, 9, 1, 21, 0, tzinfo=UTC),
        ts_ingest=datetime(2026, 9, 1, 21, 0, 30, tzinfo=UTC),
        source_id="telegram",
        kind=ThreatKind.DRONE,
        oblast="lviv",
        role=AreaRole.CONTINUATION,
    )
    store = EventStore(tmp_path / "s8.sqlite")
    store.append([event])
    (restored,) = list(store.replay())
    assert restored.oblast == "lviv"
    assert restored.role is AreaRole.CONTINUATION


def test_t37_one_message_naming_one_area_twice_is_two_rows(tmp_path: Path) -> None:
    """Role is part of the identity, so the two readings do not collide.

    Cleared here and still running there is one message and two transitions. If
    `content_hash` ignored the role, the second would be dropped as a duplicate
    of the first whenever the states happened to agree.
    """
    ts = datetime(2026, 9, 1, 21, 0, tzinfo=UTC)
    common = {
        "area_id": "UA46060000000042587",
        "state": AlertState.ACTIVE,
        "ts_source": ts,
        "ts_ingest": ts + timedelta(seconds=30),
        "source_id": "telegram",
    }
    store = EventStore(tmp_path / "roles.sqlite")
    added = store.append(
        [
            ThreatEvent(**common, role=AreaRole.SUBJECT),
            ThreatEvent(**common, role=AreaRole.CONTINUATION),
        ]
    )
    assert added == 2


def test_t38_a_store_from_an_older_version_is_refused(tmp_path: Path) -> None:
    """A missing column is a refusal, not a migration (D-013).

    `CREATE TABLE IF NOT EXISTS` says nothing about a table that already exists
    with fewer columns, so without the check an older store opens cleanly and
    then lies one row at a time.
    """
    import sqlite3

    path = tmp_path / "old.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE events (content_hash TEXT PRIMARY KEY, area_id TEXT NOT NULL, "
            "state TEXT NOT NULL, ts_source TEXT NOT NULL, ts_ingest TEXT NOT NULL, "
            "source_id TEXT NOT NULL, kind TEXT NOT NULL, provenance TEXT NOT NULL, "
            "raw_fields TEXT NOT NULL)"
        )
    with pytest.raises(SchemaMismatch):
        EventStore(path)


def test_t37_the_unknown_tag_refusal_survives_the_multi_area_rewrite(
    areas: AreaTable,
) -> None:
    """F60 must not be reintroduced by the path that now reads prose.

    `classify_message` resolves prose for the continuation list, which is a
    second prose reader in the same function that refuses prose guesses for the
    subject. A message tagging an area the map does not know still resolves to
    nothing at all, rather than to whatever its prose mentions.
    """
    text = "🔴 Повітряна тривога в Львівській області\n#Вигаданський_район"
    assert classify_message(text, areas) == ()
