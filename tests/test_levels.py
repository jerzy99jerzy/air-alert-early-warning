"""The fourth stream: an alert's level as its own row (D-050, the second half).

The level changes inside an alert without an end event and without a new key,
so it can be neither part of the alert row's identity (a ghost per
escalation) nor a column read off the opening row (frozen at the start, P2).
These tests hold the properties that make a separate stream safe: the
identity is the word and the moment it was declared, so a declaration that
stands is one row however many polls see it and a change is a second row;
the newest declaration is chosen by the source's stamp and not by the order
anything arrived in; an older store gains the table and says so; and the
adapter hands over every open alert's current declaration, not only the new
ones, because that is what turns idempotence into a change log.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.schema import AlertState, LevelEvent, ThreatKind
from mavo.sources.ukrainealarm_source import UkrainealarmSource
from mavo.store import EventStore

T0 = datetime(2026, 9, 8, 17, 22, 35, tzinfo=UTC)
T1 = datetime(2026, 9, 8, 18, 1, 1, tzinfo=UTC)


def _level(level: str = "Yellow", at: datetime = T0, seen: datetime = T0,
           area: str = "UA46060000000000000") -> LevelEvent:
    return LevelEvent(area_id=area, kind=ThreatKind.UNKNOWN, level=level, level_at=at,
                      ts_ingest=seen, source_id="ukrainealarm", oblast="Львівська")


def test_the_identity_is_the_word_and_its_moment_and_not_the_observation() -> None:
    """`ts_ingest` is outside the hash by design: the same declaration seen
    on the next poll must hash to the row the store already holds."""
    seen_again = _level(seen=T0 + timedelta(minutes=2))
    assert _level().content_hash == seen_again.content_hash
    assert _level().content_hash != _level(level="Red").content_hash
    assert _level().content_hash != _level(at=T1).content_hash
    assert _level().content_hash != _level(area="UA05000000000000000").content_hash


def test_a_standing_declaration_is_one_row_and_a_change_is_a_second(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    assert store.append_levels([_level()]) == 1
    assert store.append_levels([_level(seen=T0 + timedelta(minutes=2))]) == 0
    assert store.append_levels([_level(seen=T0 + timedelta(minutes=4))]) == 0
    assert store.append_levels([_level("Red", at=T1, seen=T1)]) == 1
    assert store.count_levels() == 2
    assert [e.level for e in store.replay_levels()] == ["Yellow", "Red"]


def test_the_newest_declaration_is_chosen_by_its_stamp_not_by_arrival(tmp_path: Path) -> None:
    """The red record can be observed before the yellow one - both can sit in
    one payload, in either order - and the current level is still the one
    declared later."""
    store = EventStore(tmp_path / "events")
    store.append_levels([_level("Red", at=T1, seen=T0)])
    store.append_levels([_level("Yellow", at=T0, seen=T1)])
    newest = store.newest_level_by_area_kind()
    assert list(newest) == [("UA46060000000000000", ThreatKind.UNKNOWN)]
    current = newest[("UA46060000000000000", ThreatKind.UNKNOWN)]
    assert current.level == "Red"
    assert current.level_at == T1


def test_an_empty_append_writes_nothing_and_a_fresh_store_has_no_levels(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    assert store.append_levels([]) == 0
    assert store.count_levels() == 0
    assert store.newest_level_by_area_kind() == {}


def test_a_store_written_before_the_stream_gains_the_table_and_says_so(tmp_path: Path) -> None:
    """The schema move on the production host, rehearsed. A store with the
    four tables of 0.53.3.0 opens under this version, the table appears, and
    `migrations_applied` names it so the collector prints it once. A fresh
    store and a store already opened by this version report nothing: a
    table that was never absent is not a migration."""
    path = tmp_path / "events"
    fresh = EventStore(path)
    assert fresh.migrations_applied == ()
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TABLE alert_levels")
        conn.commit()
    conn.close()
    reopened = EventStore(path)
    assert reopened.migrations_applied == ("alert_levels (table)",)
    assert reopened.count_levels() == 0
    assert EventStore(path).migrations_applied == ()


LVIV = "Львівський район"


def _payload(*levels: tuple[str, str], start: str = "2026-09-08T17:22:35Z") -> str:
    return json.dumps([{
        "regionId": "1293", "regionType": "State", "regionName": LVIV,
        "lastUpdate": start,
        "activeAlerts": [{
            "regionId": "1293", "regionType": "State", "type": "AIR",
            "lastUpdate": start,
            "activeAlertLevels": [
                {"alertLevel": level, "reason": "", "createdAt": at} for level, at in levels
            ],
        }],
    }])


class _Bodies:
    def __init__(self, bodies: list[str]) -> None:
        self._bodies = bodies
        self.calls = 0

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        body = self._bodies[min(self.calls, len(self._bodies) - 1)]
        self.calls += 1
        return body


def test_the_adapter_hands_over_the_standing_declaration_on_every_poll() -> None:
    """Every open key, not only the new ones. The episode side of `poll()`
    stays silent on the second poll (the steady state) while the level side
    repeats the standing declaration; the store's hash is what keeps that
    from becoming a second row."""
    yellow = "2026-09-08T17:22:35Z"
    source = UkrainealarmSource("k", transport=_Bodies([_payload(("Yellow", yellow))]))
    first = source.poll()
    assert [e.state for e in first] == [AlertState.ACTIVE]
    assert [(e.level, e.level_at.isoformat()) for e in source.levels] == [
        ("Yellow", "2026-09-08T17:22:35+00:00")]
    assert source.levels[0].area_id == first[0].area_id
    assert source.levels[0].oblast == first[0].oblast
    second = source.poll()
    assert second == ()
    assert [e.level for e in source.levels] == ["Yellow"]
    assert source.levels[0].content_hash == source.levels[0].content_hash


def test_an_escalation_inside_an_open_alert_is_a_new_declaration_and_no_event() -> None:
    """The regression control from 0.53.3.0, completed: the episode side is
    still silent and the level side now carries the change."""
    yellow, red = "2026-09-08T17:22:35Z", "2026-09-08T18:01:01Z"
    source = UkrainealarmSource("k", transport=_Bodies([
        _payload(("Yellow", yellow)),
        _payload(("Yellow", yellow), ("Red", red)),
    ]))
    first = source.poll()
    first_hash = source.levels[0].content_hash
    second = source.poll()
    assert [e.state for e in first] == [AlertState.ACTIVE]
    assert second == ()
    assert [(e.level, e.level_at.isoformat()) for e in source.levels] == [
        ("Red", "2026-09-08T18:01:01+00:00")]
    assert source.levels[0].content_hash != first_hash


def test_an_alert_without_a_readable_level_hands_over_no_declaration() -> None:
    source = UkrainealarmSource("k", transport=_Bodies([_payload()]))
    events = source.poll()
    assert [e.state for e in events] == [AlertState.ACTIVE]
    assert source.levels == ()


def test_the_adapter_and_the_store_together_make_one_row_per_change(tmp_path: Path) -> None:
    yellow, red = "2026-09-08T17:22:35Z", "2026-09-08T18:01:01Z"
    source = UkrainealarmSource("k", transport=_Bodies([
        _payload(("Yellow", yellow)),
        _payload(("Yellow", yellow)),
        _payload(("Yellow", yellow), ("Red", red)),
        _payload(("Yellow", yellow), ("Red", red)),
    ]))
    store = EventStore(tmp_path / "events")
    counts = []
    for _ in range(4):
        source.poll()
        counts.append(store.append_levels(source.levels))
    assert counts == [1, 0, 1, 0]
    assert [e.level for e in store.replay_levels()] == ["Yellow", "Red"]


def test_the_collector_announces_the_new_table_once_and_as_a_table(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The line the operator greps for on the first cycle after the 0.53.4.0
    install, and its wording: a table is created empty, it does not read
    NULL for earlier rows, because it has none."""
    from mavo import cli

    class _Fake:
        migrations_applied = ("alert_levels (table)", "feed_attempts.last_id")

    cli._announce_migrations(_Fake())  # type: ignore[arg-type]
    out = capsys.readouterr().out
    assert "[STORE-MIGRATED] created alert_levels, empty until the first cycle writes it" in out
    assert "[STORE-MIGRATED] added feed_attempts.last_id, NULL for every earlier row" in out
    path = tmp_path / "events"
    EventStore(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TABLE alert_levels")
        conn.commit()
    conn.close()
    cli._announce_migrations(EventStore(path))
    assert "created alert_levels" in capsys.readouterr().out
