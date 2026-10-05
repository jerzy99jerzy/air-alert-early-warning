"""The declared level reaches the contract and the week (D-063).

The rule lives in `mavo.levels`: an ACTIVE kind wears the newest declaration
on its key that the source stamped by the moment and whose newest listing is
no older than the read in effect, the newest asked among the reads whose page
was in hand by then. Each test below pairs the rule with the nearest wrong
rule it must be told apart from, because a fixture the wrong rule also passes
tests nothing (METHODOLOGY's "fixtures written against the implementation"):

- a key-only join, which paints a new alarm with its predecessor's colour;
- the newest declaration since the alarm began, which keeps the level of an
  alert that ended beside a running one on the same key, and which a bound
  drawn at a re-assertion row (D-044) cuts off for the rest of the alarm;
- the headline kind's level, which names an area by stamp and not by level;
- the nearest known colour, which hides a word the source has just started
  using.

The scenarios a review of 0.60.0.0 reproduced on rows the production store
holds are written here as the rows the product writes: a re-asserted alarm
carries `reported_at` and `superseded_clear`, and an alarm that follows
another between two polls writes no row at all.
"""

from __future__ import annotations

import json
import random
import sqlite3
from collections.abc import Callable
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from mavo import cli, timeline
from mavo.areas import AreaTable
from mavo.levels import (
    EMPTY,
    KNOWN_WORDS,
    LEVEL_FEED,
    UNRECOGNISED_RANK,
    Horizon,
    LevelIndex,
    Listed,
    StoreLevels,
    index_at,
    live_index,
    read_horizon,
    window_index,
    word_rank,
)
from mavo.report import compose, publish, to_contract
from mavo.schema import (
    AlertState,
    AreaRole,
    LevelEvent,
    Provenance,
    ThreatEvent,
    ThreatKind,
)
from mavo.store import EventStore, migration_lines
from mavo.timeline import TICK

TABLE = AreaTable.from_csv()
AREA = "UA68060000000040570"
OTHER = "UA56080000000096146"
T0 = datetime(2026, 9, 20, 10, 0, tzinfo=UTC)
URL = "https://api.ukrainealarm.com/api/v3/alerts"


def minutes(count: float) -> timedelta:
    return timedelta(minutes=count)


def alert(state: AlertState, at: datetime, *, area: str = AREA,
          kind: ThreatKind = ThreatKind.UNKNOWN, source: str = "ukrainealarm",
          raw: dict[str, str] | None = None) -> ThreatEvent:
    return ThreatEvent(
        area_id=area, state=state, ts_source=at, ts_ingest=at, source_id=source,
        kind=kind, provenance=Provenance.REPORTED, raw_fields=raw or {}, oblast="",
        role=AreaRole.SUBJECT,
    )


def listed(word: str, at: datetime, last: datetime, *, area: str = AREA,
           kind: ThreatKind = ThreatKind.UNKNOWN) -> Listed:
    return Listed(area_id=area, kind=kind, word=word, level_at=at, last_read=last)


def reads(first: datetime, last: datetime, every: float = 2) -> list[datetime]:
    """A read every `every` minutes from `first` to `last`, both included."""
    out, moment = [], first
    while moment <= last:
        out.append(moment)
        moment += minutes(every)
    return out


def index(items: list[Listed], read_times: list[datetime],
          since: datetime | None = None, elapsed: float = 0.0) -> LevelIndex:
    """Reads that had their page in hand `elapsed` seconds after asking."""
    first = since if since is not None else min(read_times)
    return LevelIndex.build(items, [(moment, elapsed) for moment in read_times],
                            first_listing=first,
                            recorded_since=first + timedelta(seconds=elapsed))


def picture_at(events: list[ThreatEvent], levels: LevelIndex | None,
               moment: datetime) -> dict[str, Any]:
    report = compose([e for e in events if e.ts_source <= moment], as_of=moment,
                     table=TABLE, history_days=(7,), levels=levels)
    listed_areas: list[dict[str, Any]] = json.loads(json.dumps(to_contract(report)["areas"]))
    return {item["area_id"]: item for item in listed_areas}


def word_at(events: list[ThreatEvent], levels: LevelIndex, moment: datetime,
            area: str = AREA) -> str | None:
    item = picture_at(events, levels, moment).get(area)
    if item is None or item["level"] is None:
        return None
    return str(item["level"]["word"])


# ---- the rule


def test_a_level_stands_while_the_newest_read_lists_it() -> None:
    """Red declared at 10:01 and listed by every read to 10:30. The read at
    10:32 does not list it: from that read on the alarm wears none. A
    key-only join keeps the Red for as long as the alarm runs."""
    events = [alert(AlertState.ACTIVE, T0)]
    levels = index([listed("Red", T0 + minutes(1), T0 + minutes(30))],
                   reads(T0, T0 + minutes(60)))
    assert word_at(events, levels, T0 + minutes(1)) == "Red"
    assert word_at(events, levels, T0 + minutes(31)) == "Red"
    assert word_at(events, levels, T0 + minutes(32) - TICK) == "Red"
    assert word_at(events, levels, T0 + minutes(32)) is None
    assert word_at(events, levels, T0 + minutes(1) - TICK) is None


def test_a_new_alarm_does_not_inherit_its_predecessors_colour() -> None:
    """With an all-clear between the two alarms, and without one: an alarm
    that ends and another that begins between two polls writes no row at all
    (the key never left the list), so the second is drawn from the first
    alarm's row. Either way the Red stops at the first read that did not list
    it."""
    red = [listed("Red", T0 + minutes(20), T0 + minutes(58))]
    times = reads(T0, T0 + minutes(120))
    with_clear = [alert(AlertState.ACTIVE, T0), alert(AlertState.CLEAR, T0 + minutes(60)),
                  alert(AlertState.ACTIVE, T0 + minutes(90))]
    assert word_at(with_clear, index(red, times), T0 + minutes(95)) is None
    no_row = [alert(AlertState.ACTIVE, T0)]
    assert word_at(no_row, index(red, times), T0 + minutes(59)) == "Red"
    assert word_at(no_row, index(red, times), T0 + minutes(60)) is None
    assert word_at(no_row, index(red, times), T0 + minutes(95)) is None


def test_an_alarm_re_asserted_after_a_spurious_clear_keeps_its_level() -> None:
    """D-044: one poll missed the key, a clear was written, the next poll saw
    the alarm again and the row is dated by that observation. The Yellow the
    source stamped at the alarm's start is still listed, so it stands. A bound
    drawn at the re-assertion row (or at the clear) drops it for the rest of
    the alarm; measured on two of four re-assertions of the recorded week."""
    events = [
        alert(AlertState.ACTIVE, T0),
        alert(AlertState.CLEAR, T0 + minutes(20)),
        alert(AlertState.ACTIVE, T0 + minutes(22),
              raw={"reported_at": T0.isoformat(),
                   "superseded_clear": (T0 + minutes(20)).isoformat()}),
    ]
    levels = index([listed("Yellow", T0, T0 + minutes(80))], reads(T0, T0 + minutes(80)))
    assert word_at(events, levels, T0 + minutes(10)) == "Yellow"
    assert word_at(events, levels, T0 + minutes(21)) is None   # the clear stands then
    assert word_at(events, levels, T0 + minutes(30)) == "Yellow"
    assert word_at(events, levels, T0 + minutes(79)) == "Yellow"


def test_a_level_the_source_stopped_listing_beside_a_running_alarm_goes() -> None:
    """Two alerts of one kind on one area (`AIR` and `URBAN_FIGHTS` both fold
    to UNKNOWN): the chronic one carries a Red from 2022, the air alert a
    Yellow from 10:00 that the API lists as current while it runs. When the
    air alert ends, the API's current level is the Red again. The newest
    declaration since the alarm began is the Yellow for ever after."""
    chronic = datetime(2022, 4, 1, tzinfo=UTC)
    events = [alert(AlertState.ACTIVE, chronic)]
    levels = index([listed("Red", chronic, T0 + minutes(90)),
                    listed("Yellow", T0, T0 + minutes(40))],
                   reads(T0 - minutes(30), T0 + minutes(90)))
    assert word_at(events, levels, T0 - minutes(1)) == "Red"
    assert word_at(events, levels, T0 + minutes(30)) == "Yellow"
    assert word_at(events, levels, T0 + minutes(42)) == "Red"


def test_a_declaration_counts_from_its_own_stamp_on_the_sources_clock() -> None:
    """Stamped at 10:05:30, between two reads: it stands from its stamp, the
    clock the alarm's own row is drawn on, not from the read that saw it."""
    events = [alert(AlertState.ACTIVE, T0)]
    stamp = T0 + minutes(5.5)
    levels = index([listed("Yellow", T0, T0 + minutes(4)),
                    listed("Red", stamp, T0 + minutes(60))], reads(T0, T0 + minutes(60)))
    assert word_at(events, levels, stamp - TICK) == "Yellow"
    assert word_at(events, levels, stamp) == "Red"


def test_before_the_presence_record_a_level_is_unrecorded_and_published_so() -> None:
    """The rows written before 0.60.0.0 say nothing about which read listed
    them. A moment before the first read that recorded it wears no level, and
    the contract says from when the record runs, so a consumer draws that
    moment as unrecorded rather than as an alarm the source left unlevelled."""
    events = [alert(AlertState.ACTIVE, T0)]
    since = T0 + minutes(30)
    levels = index([listed("Red", T0, T0 + minutes(60))], reads(T0, T0 + minutes(60)),
                   since=since)
    assert word_at(events, levels, since - TICK) is None
    assert word_at(events, levels, since) == "Red"
    report = compose(events, as_of=since, table=TABLE, history_days=(7,), levels=levels)
    assert to_contract(report)["alert_levels"] == {
        "source": "api.ukrainealarm.com",
        "recorded_since": since.isoformat(timespec="seconds")}


@pytest.mark.parametrize("state", [AlertState.UNKNOWN, AlertState.PARTIAL_CLEAR])
def test_only_an_active_kind_wears_a_level(state: AlertState) -> None:
    events = [alert(AlertState.ACTIVE, T0), alert(state, T0 + minutes(30))]
    levels = index([listed("Red", T0, T0 + minutes(60))], reads(T0, T0 + minutes(60)))
    item = picture_at(events, levels, T0 + minutes(31))[AREA]
    assert item["alert"] == state.value
    assert item["level"] is None and item["kinds"][0]["level"] is None


def test_a_level_on_the_channels_rows_comes_from_the_apis_listing_alone() -> None:
    """The channel names the same area and kind as the API (`AIR` is
    UNKNOWN): a channel row stamped after the API's start is the area's newest
    row. The level is the API's listing, whatever row heads the area."""
    events = [alert(AlertState.ACTIVE, T0),
              alert(AlertState.ACTIVE, T0 + minutes(3), source="telegram")]
    levels = index([listed("Red", T0, T0 + minutes(60))], reads(T0, T0 + minutes(60)))
    assert word_at(events, levels, T0 + minutes(5)) == "Red"


# ---- the area's level


def test_the_area_level_is_the_loudest_kind_and_not_the_headline() -> None:
    """Artillery raised after a red air alert names the area (newer stamp)
    and carries no level; the area is still red, from the air alert."""
    events = [alert(AlertState.ACTIVE, T0),
              alert(AlertState.ACTIVE, T0 + minutes(20), kind=ThreatKind.ARTILLERY)]
    levels = index([listed("Red", T0 + minutes(1), T0 + minutes(60))],
                   reads(T0, T0 + minutes(60)))
    item = picture_at(events, levels, T0 + minutes(21))[AREA]
    assert item["kind"] == "artillery"
    assert item["level"] == {"word": "Red", "declared_at": (T0 + minutes(1)).isoformat(),
                             "kind": "unknown"}


def test_red_outranks_a_newer_yellow_on_another_kind() -> None:
    events = [alert(AlertState.ACTIVE, T0), alert(AlertState.ACTIVE, T0,
                                                  kind=ThreatKind.ARTILLERY)]
    levels = index([listed("Red", T0 + minutes(1), T0 + minutes(60)),
                    listed("Yellow", T0 + minutes(9), T0 + minutes(60),
                           kind=ThreatKind.ARTILLERY)], reads(T0, T0 + minutes(60)))
    assert word_at(events, levels, T0 + minutes(10)) == "Red"


def test_a_word_no_release_knows_is_published_verbatim_and_outranks_red() -> None:
    events = [alert(AlertState.ACTIVE, T0), alert(AlertState.ACTIVE, T0,
                                                  kind=ThreatKind.ARTILLERY)]
    levels = index([listed("Red", T0 + minutes(9), T0 + minutes(60)),
                    listed("Orange", T0 + minutes(1), T0 + minutes(60),
                           kind=ThreatKind.ARTILLERY)], reads(T0, T0 + minutes(60)))
    item = picture_at(events, levels, T0 + minutes(10))[AREA]
    assert item["level"]["word"] == "Orange"
    assert {k["kind"]: k["level"]["word"] for k in item["kinds"]} == {
        "unknown": "Red", "artillery": "Orange"}


def test_the_rank_is_the_sources_order_and_open() -> None:
    assert KNOWN_WORDS == ("Yellow", "Red")
    assert word_rank("Yellow") < word_rank("Red") < word_rank("red") == UNRECOGNISED_RANK


# ---- the contract


def test_a_picture_that_did_not_read_the_stream_publishes_no_key() -> None:
    payload = to_contract(compose([alert(AlertState.ACTIVE, T0)], as_of=T0, table=TABLE,
                                  history_days=(7,)))
    assert "alert_levels" not in payload
    assert payload["areas"][0]["level"] is None  # type: ignore[index]


def test_a_stream_with_no_presence_recorded_yet_says_so_with_a_null() -> None:
    payload = to_contract(compose([alert(AlertState.ACTIVE, T0)], as_of=T0, table=TABLE,
                                  history_days=(7,), levels=EMPTY))
    assert payload["alert_levels"] == {"source": "api.ukrainealarm.com",
                                       "recorded_since": None}
    assert payload["areas"][0]["level"] is None  # type: ignore[index]


class _Reader:
    """A level reader whose two steps can each fail, and which records its calls."""

    def __init__(self, levels: LevelIndex, fail: str = "") -> None:
        self.levels, self.fail, self.calls = levels, fail, list[str]()

    def horizon(self) -> Horizon:
        self.calls.append("horizon")
        if self.fail == "horizon":
            raise OSError("feed_attempts: disk I/O error")
        return Horizon(T0 + minutes(1))

    def live(self, horizon: Horizon) -> LevelIndex:
        self.calls.append("live")
        if self.fail == "live":
            raise OSError("alert_levels: disk I/O error")
        return self.levels


@pytest.mark.parametrize("step", ["horizon", "live"])
def test_a_cycle_that_cannot_read_the_stream_publishes_the_alerts_without_the_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], step: str,
) -> None:
    """And its week is written without the levels too, whichever step failed:
    the two files of one cycle agree on whether the stream was read."""
    target = tmp_path / "state.json"
    reader = _Reader(EMPTY, fail=step)
    given: list[Horizon | None] = []

    def week(events: object, moment: datetime, horizon: Horizon | None) -> dict[str, object]:
        given.append(horizon)
        return {"v": timeline.TIMELINE_VERSION}

    publish(lambda: [alert(AlertState.ACTIVE, T0)], target, interval_s=0, max_cycles=1,
            table=TABLE, sleep=lambda _s: None, now=lambda: T0 + minutes(1),
            levels=reader, history_days=(7, 30, 90),
            timeline_path=tmp_path / "timeline.json", timeline=week)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert "alert_levels" not in payload
    assert [item["area_id"] for item in payload["areas"]] == [AREA]
    assert "[LEVELS-FAILED]" in capsys.readouterr().err
    assert reader.calls == (["horizon"] if step == "horizon" else ["horizon", "live"])
    assert given == [None]


def test_the_loop_publishes_the_level_it_read(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    reader = _Reader(index([listed("Red", T0, T0 + minutes(1))], [T0, T0 + minutes(1)]))
    publish(lambda: [alert(AlertState.ACTIVE, T0)], target, interval_s=0, max_cycles=1,
            table=TABLE, sleep=lambda _s: None, now=lambda: T0 + minutes(1),
            levels=reader, history_days=(7, 30, 90))
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["areas"][0]["level"]["word"] == "Red"
    assert payload["alert_levels"]["recorded_since"] == T0.isoformat(timespec="seconds")


# ---- the store: presence recorded by the read that listed it


def _declared(word: str, at: datetime, *, area: str = AREA,
              kind: ThreatKind = ThreatKind.UNKNOWN) -> LevelEvent:
    return LevelEvent(area_id=area, kind=kind, level=word, level_at=at, ts_ingest=at,
                      source_id="ukrainealarm", oblast="")


def _presence(store: EventStore) -> list[tuple[str, str | None, str | None]]:
    with closing(sqlite3.connect(store.path)) as conn:
        return [(str(r[0]), r[1], r[2]) for r in conn.execute(
            "SELECT level, first_read, last_read FROM alert_levels ORDER BY level_at")]


def test_a_read_records_its_listing_and_last_read_only_moves_forward(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    yellow = _declared("Yellow", T0)
    first, second = T0 + minutes(1), T0 + minutes(3)
    assert store.append_levels([yellow], read_at=first) == 1
    assert store.append_levels([yellow], read_at=second) == 0
    assert _presence(store) == [("Yellow", first.isoformat(), second.isoformat())]
    store.append_levels([yellow], read_at=first)  # a read replayed late
    assert _presence(store) == [("Yellow", first.isoformat(), second.isoformat())]
    assert store.levels_listed_since() == first
    assert [row[2] for row in store.listed_levels(second)] == ["Yellow"]
    assert store.listed_levels(second + TICK) == []


def test_an_older_store_gains_the_columns_says_so_and_records_from_its_next_read(
    tmp_path: Path,
) -> None:
    """The table as 0.53.4.0 created it, with a row in it: opened here, it gains
    two nullable columns and the opening says so; the row reads NULL until a
    read lists it, and the presence record starts at that read."""
    path = tmp_path / "events"
    EventStore(path)
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("DROP INDEX idx_levels_last_read")
        conn.execute("DROP INDEX idx_levels_first_read")
        conn.execute("ALTER TABLE alert_levels DROP COLUMN last_read")
        conn.execute("ALTER TABLE alert_levels DROP COLUMN first_read")
        conn.execute(
            "INSERT INTO alert_levels (content_hash, area_id, oblast, kind, level, "
            "level_at, ts_ingest, source_id) VALUES (?, ?, '', 'unknown', 'Red', ?, ?, "
            "'ukrainealarm')",
            (_declared("Red", T0).content_hash, AREA, T0.isoformat(), T0.isoformat()))
        conn.commit()
    reopened = EventStore(path)
    assert reopened.migrations_applied == ("alert_levels.first_read",
                                           "alert_levels.last_read")
    assert migration_lines(reopened) == [
        "[STORE-MIGRATED] added alert_levels.first_read, NULL for every earlier row",
        "[STORE-MIGRATED] added alert_levels.last_read, NULL for every earlier row"]
    assert _presence(reopened) == [("Red", None, None)]
    assert reopened.levels_listed_since() is None
    read = T0 + minutes(5)
    reopened.append_levels([_declared("Red", T0)], read_at=read)
    assert _presence(reopened) == [("Red", read.isoformat(), read.isoformat())]
    assert EventStore(path).migrations_applied == ()
    with closing(sqlite3.connect(path)) as conn:
        indexes = {str(row[0]) for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'alert_levels'")}
        plan = " ".join(str(row[-1]) for row in conn.execute(
            "EXPLAIN QUERY PLAN SELECT MIN(first_read) FROM alert_levels "
            "WHERE first_read IS NOT NULL"))
    assert {"idx_levels_last_read", "idx_levels_first_read"} <= indexes
    assert "idx_levels_first_read" in plan, plan


def test_the_feed_presence_is_read_from_is_the_one_collect_api_records() -> None:
    assert cli.API_FEED == LEVEL_FEED


def _record_reads(store: EventStore, times: list[datetime],
                  elapsed: Callable[[], float] = lambda: 0.0) -> None:
    for moment in times:
        store.record_read(LEVEL_FEED, URL, moment, 1, 0, elapsed())


def test_the_three_indexes_answer_alike(tmp_path: Path) -> None:
    """The live index, the index at one moment and the week's index name one
    declaration for the moment each is asked about."""
    store = EventStore(tmp_path / "events")
    times = reads(T0, T0 + minutes(20))
    yellow, red = _declared("Yellow", T0), _declared("Red", T0 + minutes(9))
    for moment in times:
        store.append_levels([red if moment >= T0 + minutes(10) else yellow], read_at=moment)
    _record_reads(store, times)
    key = (AREA, ThreatKind.UNKNOWN)
    horizon = read_horizon(store)
    week = window_index(store, T0 - minutes(30), T0 + minutes(20), horizon)
    for moment in (T0 + minutes(5), T0 + minutes(9), T0 + minutes(10), T0 + minutes(20)):
        one = index_at(store, moment, horizon).standing(key, moment)
        assert one == week.standing(key, moment), moment
    live = live_index(store, horizon)
    assert live.standing(key, T0 + minutes(20)) == week.standing(key, T0 + minutes(20))
    assert [item.word for item in live.listed[key]] == ["Red"]


def test_collect_api_stamps_the_listing_with_its_read_and_records_the_read_last(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The level stream is written before the read, so no report cycle can
    find a recorded read whose listing is not yet in the table; and a failed
    append leaves the read unrecorded, so the previous read and its listing
    stand rather than a read that listed nothing."""
    from mavo.cli import main

    class _Stub:
        source_id = "ukrainealarm"
        unresolved: tuple[str, ...] = ()
        declined: tuple[str, ...] = ()
        unparsed: tuple[str, ...] = ()
        informational: tuple[str, ...] = ()
        unmapped_types: dict[str, tuple[str, ...]] = {}
        overlapping: dict[tuple[str, str], int] = {}
        unknown_keys: dict[str, int] = {}
        snapshot_state = "disabled"
        snapshot_age_s: float | None = None

        def __init__(self, key: str, snapshot: Path | None = None) -> None:
            self.levels: tuple[LevelEvent, ...] = ()

        def save_snapshot(self) -> None:
            return None

        def poll(self) -> tuple[ThreatEvent, ...]:
            self.levels = (_declared("Yellow", T0),)
            return (alert(AlertState.ACTIVE, T0),)

    monkeypatch.setenv("MAVO_UKRAINEALARM_KEY", "k")
    monkeypatch.setattr(cli, "UkrainealarmSource", _Stub)
    # The order itself, asserted where it happens: when the rows are appended
    # and when the read is recorded, the read's listing is already stored.
    # A collector that recorded the read, or appended the rows, first would
    # pass every check of what the store holds afterwards (the release's
    # third review, with a mutant that moved the listing last).
    seen: list[str] = []
    real_append, real_record = cli.EventStore.append, cli.EventStore.record_read

    def listed_by(store: EventStore, started: datetime) -> list[str]:
        return [row[2] for row in store.listed_levels(started)]

    def append(self: EventStore, events: Any) -> int:
        seen.append("rows")
        assert listed_by(self, datetime.now(UTC) - minutes(1)) == ["Yellow"], \
            "the rows were appended before the read's listing was stored"
        return real_append(self, events)

    def record_read(self: EventStore, feed: str, url: str, started_at: datetime,
                    *args: Any, **kwargs: Any) -> None:
        seen.append("read")
        assert listed_by(self, started_at) == ["Yellow"], \
            "the read was recorded before its listing was stored"
        real_record(self, feed, url, started_at, *args, **kwargs)

    monkeypatch.setattr(cli.EventStore, "append", append)
    monkeypatch.setattr(cli.EventStore, "record_read", record_read)
    path = tmp_path / "events"
    assert main(["collect-api", "--store", str(path)]) == 0
    assert seen == ["rows", "read"]
    store = EventStore(path)
    newest = store.newest_read_at(LEVEL_FEED)
    assert newest is not None
    assert _presence(store) == [("Yellow", newest, newest)]

    def failing(self: EventStore, events: object) -> int:
        raise sqlite3.OperationalError("database is locked")

    # The class `mavo.cli` holds, which is not always the one imported here:
    # a test elsewhere in the suite re-imports the package's modules.
    monkeypatch.setattr(cli.EventStore, "append", failing)
    assert main(["collect-api", "--store", str(path)]) == 7
    assert cli.EventStore(path).newest_read_at(LEVEL_FEED) == newest
    # The read ran on the wall clock, so the moment asked about is now.
    reopened = cli.EventStore(path)
    assert live_index(reopened, read_horizon(reopened)).standing(
        (AREA, ThreatKind.UNKNOWN), datetime.now(UTC)) is not None


# ---- the week


def test_a_change_inside_one_alarm_and_the_end_of_a_listing_are_intervals(
    tmp_path: Path,
) -> None:
    store = EventStore(tmp_path / "events")
    times = reads(T0, T0 + minutes(60))
    yellow, red = _declared("Yellow", T0 + minutes(5)), _declared("Red", T0 + minutes(40))
    for moment in times:
        listed_now = ([yellow] if T0 + minutes(5) <= moment < T0 + minutes(40)
                      else [red] if T0 + minutes(40) <= moment <= T0 + minutes(50) else [])
        store.append_levels(listed_now, read_at=moment)
    _record_reads(store, times)
    end = T0 + minutes(60)
    payload = json.loads(json.dumps(timeline.build(
        store, [alert(AlertState.ACTIVE, T0)], end, table=TABLE, feeds=(), days=1,
        horizon=read_horizon(store))))
    spans = [((item["level"] or {}).get("word"), item["from"])
             for item in payload["areas"]["intervals"]]
    assert spans == [(None, T0.isoformat()),
                     ("Yellow", (T0 + minutes(6)).isoformat()),
                     ("Red", (T0 + minutes(40)).isoformat()),
                     (None, (T0 + minutes(52)).isoformat())]
    assert payload["areas"]["levels"] == {"recorded_since": (T0 + minutes(6)).isoformat()}


def test_a_week_built_from_a_store_with_no_presence_reads_recorded_since_null(
    tmp_path: Path,
) -> None:
    store = EventStore(tmp_path / "events")
    _record_reads(store, [T0])
    payload = timeline.build(store, [alert(AlertState.ACTIVE, T0)], T0 + minutes(5),
                             table=TABLE, feeds=(), days=1, horizon=read_horizon(store))
    assert payload["areas"]["levels"] == {"recorded_since": None}  # type: ignore[index]
    unread = timeline.build(store, [alert(AlertState.ACTIVE, T0)], T0 + minutes(5),
                            table=TABLE, feeds=(), days=1)
    assert "levels" not in unread["areas"]  # type: ignore[operator]


@pytest.mark.parametrize("seed", [11, 12, 13, 14])
def test_the_week_and_compose_agree_on_the_level_at_every_boundary(
    tmp_path: Path, seed: int,
) -> None:
    """Generated alarms on two areas and three kinds from two sources, and a
    generated level stream recorded the way `collect-api` records it: reads
    at a jittered cadence with gaps, each listing for every key the newest
    declaration of those it carries. Declarations come and go, older ones come
    back (a chronic alert's record after an air alert ends), words include one
    no release knows, and stamps tie with alert rows and with reads. The file
    must answer each moment as `compose` does, at every boundary and a tick
    either side."""
    rng = random.Random(seed)
    end = T0 + timedelta(days=2)
    start = end - timedelta(days=1)
    kinds = (ThreatKind.UNKNOWN, ThreatKind.ARTILLERY, ThreatKind.DRONE)
    states = [AlertState.ACTIVE] * 3 + [AlertState.CLEAR] * 2 + [AlertState.UNKNOWN]
    origin = start - timedelta(hours=6)
    events: list[ThreatEvent] = []
    for _ in range(140):
        at = origin + timedelta(seconds=rng.uniform(0, 30 * 3600))
        if rng.random() < 0.5:
            at = at.replace(second=0, microsecond=0)
        events.append(alert(rng.choice(states), at, area=rng.choice((AREA, OTHER)),
                            kind=rng.choice(kinds),
                            source=rng.choice(("ukrainealarm", "ukrainealarm", "telegram"))))
    store = EventStore(tmp_path / "events")
    moment, times = origin, []
    while moment <= end:
        if rng.random() > 0.05:  # a refused poll records no read
            times.append(moment)
        moment += timedelta(seconds=rng.choice((60, 60, 61, 120, 900)))
    keys = [(area, kind) for area in (AREA, OTHER) for kind in kinds]
    pool: dict[tuple[str, ThreatKind], list[LevelEvent]] = {key: [] for key in keys}
    for key in keys:
        for _ in range(rng.randint(2, 6)):
            stamp = origin + timedelta(seconds=rng.uniform(-3600, 30 * 3600))
            if rng.random() < 0.3:
                stamp = rng.choice(times)  # ties with a read
            pool[key].append(_declared(rng.choice(("Yellow", "Red", "Red", "Orange")),
                                       stamp, area=key[0], kind=key[1]))
    install = times[len(times) // 5]
    for read in times:
        handed = []
        for key in keys:
            present = [d for d in pool[key] if d.level_at <= read and rng.random() < 0.7]
            if present:
                handed.append(max(present, key=lambda d: d.level_at))
        if read >= install:
            store.append_levels(handed, read_at=read)
        else:
            store.append_levels(handed)  # before the columns: no presence
    _record_reads(store, times, elapsed=lambda: rng.choice((0.0, 0.4, 1.7, 61.0)))
    horizon = read_horizon(store)
    payload = json.loads(json.dumps(timeline.build(store, events, end, table=TABLE,
                                                   feeds=(), days=1, horizon=horizon)))
    edges = sorted({datetime.fromisoformat(item[side])
                    for item in payload["areas"]["intervals"]
                    for side in ("from", "to") if item[side] is not None})
    probes = {start, end} | {start + (end - start) * rng.random() for _ in range(40)}
    for edge in edges:
        probes |= {edge - TICK, edge, edge + TICK}
    levelled = 0
    for probe in sorted(p for p in probes if start <= p <= end):
        from_file = json.loads(json.dumps(timeline.picture_from_file(payload, probe)))
        from_store = json.loads(json.dumps(timeline.picture_from_store(
            store, events, probe, table=TABLE, feeds=(), horizon=horizon)))
        assert from_file["areas"] == from_store["areas"], probe.isoformat()
        levelled += sum(1 for item in from_file["areas"] if item["level"] is not None)
    assert levelled, "a generated week where no moment wears a level tests nothing"


def test_the_instants_are_a_stamp_a_first_read_after_a_listing_and_the_record_start() -> None:
    times = reads(T0, T0 + minutes(20))
    levels = index([listed("Red", T0 + minutes(3), T0 + minutes(10)),
                    listed("Yellow", T0 - minutes(30), T0 + minutes(20), area=OTHER)],
                   times, since=T0 + minutes(2), elapsed=0.5)
    half = timedelta(seconds=0.5)
    assert levels.instants(T0, T0 + minutes(20)) == {
        T0 + minutes(2) + half: {OTHER},   # older than the record: starts with it
        T0 + minutes(3): {AREA},           # its own stamp
        T0 + minutes(12) + half: {AREA},   # the first read after its last listing, in hand
    }


# ---- the read's own clock, and one horizon per replay (F198)


def test_a_level_stands_until_the_alarm_its_read_ended_ends() -> None:
    """The read that stops listing a Red because its alarm ended asks at
    10:32:00 and has the page at 10:32:01.5; the all-clear it derives is
    stamped when the page arrived, 10:32:00.8. Dated by its start the read
    would take the Red away 0.8 s before the alarm ends, and a reader shown
    that moment is told the source lists no level for a red alarm."""
    asked = T0 + minutes(32)
    ended = asked + timedelta(seconds=0.8)
    events = [alert(AlertState.ACTIVE, T0), alert(AlertState.CLEAR, ended)]
    levels = index([listed("Red", T0, T0 + minutes(30))], reads(T0, T0 + minutes(60)),
                   elapsed=1.5)
    assert word_at(events, levels, asked + timedelta(seconds=0.5)) == "Red"
    assert word_at(events, levels, ended - TICK) == "Red"
    assert AREA not in picture_at(events, levels, ended) or (
        picture_at(events, levels, ended)[AREA]["alert"] != "active")


def test_the_week_carries_no_unlevelled_sliver_at_the_end_of_a_levelled_alarm(
    tmp_path: Path,
) -> None:
    """The same alarm through the store and the file: one Red interval and
    the all-clear, nothing between them."""
    store = EventStore(tmp_path / "events")
    times = reads(T0, T0 + minutes(40))
    red = _declared("Red", T0)
    for moment in times:
        store.append_levels([red] if moment <= T0 + minutes(30) else [], read_at=moment)
    _record_reads(store, times, elapsed=lambda: 1.5)
    ended = T0 + minutes(32) + timedelta(seconds=0.8)
    events = [alert(AlertState.ACTIVE, T0), alert(AlertState.CLEAR, ended)]
    payload = json.loads(json.dumps(timeline.build(
        store, events, T0 + minutes(40), table=TABLE, feeds=(), days=1,
        horizon=read_horizon(store))))
    spans = [(item["alert"], (item["level"] or {}).get("word"), item["from"], item["to"])
             for item in payload["areas"]["intervals"]]
    opened = T0 + timedelta(seconds=1.5)  # the first read's page in hand
    assert spans == [("active", None, T0.isoformat(), opened.isoformat()),
                     ("active", "Red", opened.isoformat(), ended.isoformat())]


def test_the_record_opens_when_its_first_read_took_effect(tmp_path: Path) -> None:
    """The first read that records presence asks at 10:30 and has the page
    at 10:30:02. An alarm it ended (its all-clear at 10:30:01) was listed
    only by reads that recorded nothing; before the page arrived the moment
    is unrecorded, never an alarm the source left unlevelled."""
    store = EventStore(tmp_path / "events")
    first = T0 + minutes(30)
    store.append_levels([_declared("Yellow", T0 + minutes(1), area=OTHER)], read_at=first)
    _record_reads(store, [T0, first, first + minutes(2)], elapsed=lambda: 2.0)
    horizon = read_horizon(store)
    live = live_index(store, horizon)
    assert live.first_listing == first
    assert live.recorded_since == first + timedelta(seconds=2)
    events = [alert(AlertState.ACTIVE, T0), alert(AlertState.CLEAR, first + timedelta(seconds=1)),
              alert(AlertState.ACTIVE, T0, area=OTHER)]
    at = index_at(store, first + timedelta(seconds=0.5), horizon)
    assert at.standing((OTHER, ThreatKind.UNKNOWN), first + timedelta(seconds=0.5)) is None
    later = first + timedelta(seconds=2)
    assert index_at(store, later, horizon).standing(
        (OTHER, ThreatKind.UNKNOWN), later) is not None
    payload = timeline.build(store, events, first + minutes(5), table=TABLE, feeds=(),
                             days=1, horizon=horizon)
    assert payload["areas"]["levels"] == {  # type: ignore[index]
        "recorded_since": (first + timedelta(seconds=2)).isoformat()}


def test_a_first_read_never_logged_opens_the_record_at_the_next_logged_one(
    tmp_path: Path,
) -> None:
    """Its listing was stored and its `record_read` failed: the stamp in
    `first_read` names no logged read, and the record opens with the first
    logged read after it, never before."""
    store = EventStore(tmp_path / "events")
    unlogged, logged = T0 + minutes(10), T0 + minutes(12)
    store.append_levels([_declared("Red", T0)], read_at=unlogged)
    store.append_levels([_declared("Red", T0)], read_at=logged)
    _record_reads(store, [T0, logged], elapsed=lambda: 1.0)
    live = live_index(store, read_horizon(store))
    assert live.recorded_since == logged + timedelta(seconds=1)
    assert next(store.iter_reads_from(LEVEL_FEED, unlogged)) == (logged, 1.0)
    assert list(store.iter_reads_back(LEVEL_FEED, logged)) == [(logged, 1.0), (T0, 1.0)]


def test_a_read_asked_later_speaks_once_its_page_is_in_hand() -> None:
    """Asked at 10:00 and in hand at 10:00:05; a second read asked at 10:00:01
    is in hand at 10:00:02. From 10:00:02 the second is in effect, and the
    first's page arriving later does not take its place: what the source said
    at 10:00 is older than what it said at 10:00:01."""
    second = T0 + timedelta(seconds=1)
    levels = LevelIndex.build((), [(T0, 5.0), (second, 1.0)], first_listing=T0,
                              recorded_since=T0 + timedelta(seconds=2))
    assert levels.read_at(T0 + timedelta(seconds=1.9)) is None
    assert levels.read_at(T0 + timedelta(seconds=2)) == second
    assert levels.read_at(T0 + timedelta(seconds=6)) == second
    assert levels.overtaken(T0 - TICK) == T0 + timedelta(seconds=2)
    assert levels.opening() == T0 + timedelta(seconds=2)


def _poll_ending(store: EventStore, ended: datetime, area: str = AREA) -> None:
    """What `collect-api` writes for a read that ended the alarm: its (empty)
    listing, the all-clear, then the read itself."""
    store.append_levels([], read_at=ended)
    store.append([alert(AlertState.CLEAR, ended + timedelta(seconds=0.5), area=area)])
    store.record_read(LEVEL_FEED, URL, ended, 0, 0, 1.0)


def _levelled_store(path: Path, base: datetime) -> EventStore:
    store = EventStore(path)
    times = reads(base, base + minutes(20))
    for moment in times:
        store.append_levels([_declared("Red", base)], read_at=moment)
    store.append([alert(AlertState.ACTIVE, base)])
    _record_reads(store, times, elapsed=lambda: 1.0)
    return store


def test_a_read_recorded_while_the_replay_ran_is_not_used(tmp_path: Path) -> None:
    """A collector run lands between the replay and the level query: the
    replay still holds the alarm open, the newest read no longer lists its
    Red. Asked about the newest read, the cycle publishes a red alarm with no
    level; asked about the read on record before the replay, it does not."""
    store = _levelled_store(tmp_path / "events", T0)
    ended = T0 + minutes(22)

    def load() -> list[ThreatEvent]:
        events = list(store.replay())
        _poll_ending(store, ended)
        return events

    target, written = tmp_path / "state.json", tmp_path / "timeline.json"

    def week(events: object, moment: datetime, horizon: Horizon | None) -> dict[str, object]:
        return timeline.build(store, list(events), moment,  # type: ignore[call-overload]
                              table=TABLE, feeds=(), days=1, horizon=horizon)

    publish(load, target, interval_s=0, max_cycles=1, table=TABLE, sleep=lambda _s: None,
            now=lambda: ended + minutes(1), levels=StoreLevels(store),
            history_days=(7, 30, 90), timeline_path=written, timeline=week)
    item = json.loads(target.read_text(encoding="utf-8"))["areas"][0]
    assert item["alert"] == "active" and item["level"]["word"] == "Red"
    [last] = [span for span in json.loads(written.read_text(encoding="utf-8"))
              ["areas"]["intervals"] if span["to"] is None]
    assert last["alert"] == "active" and last["level"]["word"] == "Red"


@pytest.mark.parametrize("command", ["report", "watch", "timeline", "at"])
def test_every_command_that_replays_takes_its_horizon_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    command: str,
) -> None:
    """The four ways a command replays the store and reads the level stream,
    with a collector run landing inside the replay."""
    from mavo.cli import main

    base = datetime.now(UTC).replace(microsecond=0) - minutes(30)
    path = tmp_path / "events"
    _levelled_store(path, base)
    ended = base + minutes(22)
    original = cli.EventStore.replay

    def replay(self: EventStore) -> Any:
        events = list(original(self))
        if not getattr(replay, "done", False):
            replay.done = True  # type: ignore[attr-defined]
            _poll_ending(self, ended)
        return iter(events)

    monkeypatch.setattr(cli.EventStore, "replay", replay)
    state, written = tmp_path / "state.json", tmp_path / "timeline.json"
    if command == "at":
        capsys.readouterr()
        moment = (ended + minutes(1)).isoformat()
        assert main(["timeline", "--store", str(path), "--at", moment]) == 0
        [item] = json.loads(capsys.readouterr().out)["areas"]
        assert item["alert"] == "active" and item["level"]["word"] == "Red"
        return
    if command == "timeline":
        args = ["timeline", "--store", str(path), "--out", str(written), "--days", "1"]
    else:
        args = ["report", "--store", str(path), "--json", str(state),
                "--timeline", str(written)]
        if command == "watch":
            args += ["--watch", "--interval", "0", "--max-cycles", "1"]
    main(args)
    if command != "timeline":
        item = json.loads(state.read_text(encoding="utf-8"))["areas"][0]
        assert item["alert"] == "active" and item["level"]["word"] == "Red", command
    [last] = [span for span in json.loads(written.read_text(encoding="utf-8"))
              ["areas"]["intervals"] if span["to"] is None]
    assert last["alert"] == "active" and last["level"]["word"] == "Red", command


@pytest.mark.parametrize("command", ["report", "watch"])
def test_a_command_whose_declarations_cannot_be_read_writes_its_week_without_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    command: str,
) -> None:
    """The horizon was read and the declarations were not: the contract goes
    out without `alert_levels` and the week of the same run without
    `areas.levels`, so the two files agree that the stream was not read. The
    week, handed the horizon, would read the stream on its own (the release's
    fourth review)."""
    from mavo.cli import main

    base = datetime.now(UTC).replace(microsecond=0) - minutes(30)
    path = tmp_path / "events"
    _levelled_store(path, base)

    def fail(*_args: object, **_kwargs: object) -> LevelIndex:
        raise OSError("database is locked")

    monkeypatch.setattr(cli, "live_index", fail)
    monkeypatch.setattr("mavo.levels.live_index", fail)
    state, written = tmp_path / "state.json", tmp_path / "timeline.json"
    args = ["report", "--store", str(path), "--json", str(state),
            "--timeline", str(written)]
    if command == "watch":
        args += ["--watch", "--interval", "0", "--max-cycles", "1"]
    main(args)
    assert "alert_levels" not in json.loads(state.read_text(encoding="utf-8"))
    week = json.loads(written.read_text(encoding="utf-8"))["areas"]
    assert "levels" not in week
    assert all(span["level"] is None for span in week["intervals"])
    assert "[LEVELS-FAILED] database is locked" in capsys.readouterr().err


def test_the_live_index_holds_a_declaration_stamped_while_its_read_was_in_flight(
    tmp_path: Path,
) -> None:
    """The horizon is the newest read's `started_at`; a declaration the source
    stamped after that read asked and before its page arrived is still that
    read's listing. Bounded by the horizon's stamp, the live picture lost it
    until the next read."""
    store = EventStore(tmp_path / "events")
    asked = T0 + minutes(10)
    stamp = asked + timedelta(seconds=0.4)
    store.append_levels([_declared("Red", stamp)], read_at=asked)
    store.record_read(LEVEL_FEED, URL, asked, 1, 0, 1.0)
    live = live_index(store, read_horizon(store))
    found = live.standing((AREA, ThreatKind.UNKNOWN), asked + minutes(1))
    assert found is not None and found.word == "Red"


def test_a_read_that_took_negative_time_speaks_no_earlier_than_it_asked() -> None:
    """A wall clock stepped back during a fetch measures a negative duration;
    the page is not in hand before the read asked for it."""
    levels = LevelIndex.build((), [(T0, -3.0)], first_listing=T0, recorded_since=T0)
    assert levels.read_at(T0 - timedelta(seconds=1)) is None
    assert levels.read_at(T0) == T0


def test_an_areas_level_on_a_tie_of_words_is_the_later_declaration() -> None:
    """Two kinds of one area both listed `Red`: the area names the later
    declaration, the one whose stamp a reader is shown as when it was set."""
    events = [alert(AlertState.ACTIVE, T0), alert(AlertState.ACTIVE, T0,
                                                  kind=ThreatKind.ARTILLERY)]
    levels = index([listed("Red", T0 + minutes(9), T0 + minutes(60)),
                    listed("Red", T0 + minutes(1), T0 + minutes(60),
                           kind=ThreatKind.ARTILLERY)], reads(T0, T0 + minutes(60)))
    item = picture_at(events, levels, T0 + minutes(10))[AREA]
    assert item["level"] == {"word": "Red", "declared_at": (T0 + minutes(9)).isoformat(),
                             "kind": "unknown"}
    swapped = index([listed("Red", T0 + minutes(1), T0 + minutes(60)),
                     listed("Red", T0 + minutes(9), T0 + minutes(60),
                            kind=ThreatKind.ARTILLERY)], reads(T0, T0 + minutes(60)))
    assert picture_at(events, swapped, T0 + minutes(10))[AREA]["level"]["kind"] == "artillery"


def test_a_failed_level_read_costs_a_picture_at_a_moment_its_levels_and_nothing_else(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """`timeline --at` prints the picture without levels and says why, as the
    week does; until the third review it raised."""
    store = _levelled_store(tmp_path / "events", T0)

    def broken(*_args: object) -> LevelIndex:
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(timeline, "index_at", broken)
    picture = timeline.picture_from_store(store, list(store.replay()), T0 + minutes(5),
                                          table=TABLE, feeds=(), horizon=read_horizon(store))
    [item] = json.loads(json.dumps(picture["areas"]))
    assert item["alert"] == "active" and item["level"] is None
    assert "[LEVELS-FAILED] timeline --at: database is locked" in capsys.readouterr().err
