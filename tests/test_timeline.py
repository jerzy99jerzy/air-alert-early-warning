"""The seven-day timeline (D-058): the file and the live rules must agree.

Every layer is held to one check. The file's picture of a moment, built by
choosing the intervals that hold it and deciding nothing (`picture_from_file`),
must equal what the live rules say when asked about that moment directly
(`picture_from_store`: `compose`, the two Polish composers, `measure_feed`).
The moments are drawn at random across the window and taken at every boundary
the file carries, one tick either side, because a missing change point shows
exactly there and nowhere else.

The Ukrainian logs are generated, not written: the generator knows the states,
kinds and clock quirks the store holds (ties on both stamps, rows stamped
before the window and after the file's end) and nothing about how the timeline
walks them. The Polish layers run on recordings already in the tree, the RSO
page of 2026-09-16 with its alert and all-clear and the UUP plan of 2026-09-14,
served into a real store in the order the collectors write. The recorded week
from the production store is its own test.
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from mavo import poland, timeline
from mavo.areas import AreaTable
from mavo.liveness import PRODUCTION_FEEDS, FeedSpec, PipeState, measure_feed
from mavo.report import compose
from mavo.schema import AlertState, AreaRole, Provenance, ThreatEvent, ThreatKind
from mavo.sources import pansa, rso
from mavo.store import EventStore
from mavo.timeline import TICK

FIXTURES = Path(__file__).parent / "fixtures"
RECORDED_RSO = FIXTURES / "rso_ogolne_2026-09-16.xml"
UUP = FIXTURES / "pansa_uup.json"

#: Four raions the area table resolves, two western, and one code it does not,
#: which `compose` keeps and names `unresolved`.
AREAS = (
    "UA56080000000096146",
    "UA68060000000040570",
    "UA12080050000062712",
    "UA63120270000028556",
    "UA99000000000000001",
)

TABLE = AreaTable.from_csv()


def event(area: str, state: AlertState, kind: ThreatKind, ts: datetime,
          ingest: datetime | None = None, source: str = "ukrainealarm") -> ThreatEvent:
    return ThreatEvent(
        area_id=area, state=state, ts_source=ts,
        ts_ingest=ingest if ingest is not None else ts,
        source_id=source, kind=kind, provenance=Provenance.REPORTED,
        raw_fields={}, oblast="", role=AreaRole.SUBJECT,
    )


def normalised(value: object) -> object:
    return json.loads(json.dumps(value, ensure_ascii=False))


def boundaries(payload: dict[str, Any]) -> set[datetime]:
    """Every `from` and `to` the file carries, in every layer."""
    found: set[datetime] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("from", "to") and isinstance(value, str):
                    found.add(datetime.fromisoformat(value))
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


def moments(payload: dict[str, Any], rng: random.Random, count: int = 60,
            edges: int = 120) -> list[datetime]:
    """Random instants, plus up to `edges` boundaries with a tick either side.

    Capped because the check asks the store once per instant and a day of a
    30-second pipe carries hundreds of boundaries; the sample is drawn afresh
    per seed, and every boundary kind the file has is among them.
    """
    start = datetime.fromisoformat(payload["window"]["start"])
    end = datetime.fromisoformat(payload["generated_at"])
    span = (end - start).total_seconds()
    chosen = {start, end}
    chosen.update(start + timedelta(seconds=rng.uniform(0, span)) for _ in range(count))
    found = sorted(boundaries(payload))
    for edge in rng.sample(found, min(edges, len(found))):
        chosen.update({edge - TICK, edge, edge + TICK})
    return sorted(moment for moment in chosen if start <= moment <= end)


def assert_agrees(store: EventStore, events: list[ThreatEvent], end: datetime,
                  days: int, rng: random.Random, feeds: tuple[FeedSpec, ...] = PRODUCTION_FEEDS,
                  ) -> dict[str, Any]:
    payload = normalised(timeline.build(store, events, end, table=TABLE, feeds=feeds, days=days))
    assert isinstance(payload, dict)
    for moment in moments(payload, rng):
        from_file = normalised(timeline.picture_from_file(payload, moment))
        from_store = normalised(timeline.picture_from_store(
            store, events, moment, table=TABLE, feeds=feeds))
        assert from_file == from_store, f"the file and the rules disagree at {moment.isoformat()}"
    return payload


# ---- the areas: generated logs against `compose`


def generated_log(rng: random.Random, start: datetime, count: int = 320) -> list[ThreatEvent]:
    """A log over ten days around a week, with the quirks the store holds."""
    states = [AlertState.ACTIVE] * 4 + [AlertState.CLEAR] * 4 + [
        AlertState.UNKNOWN, AlertState.PARTIAL_CLEAR]
    base = start - timedelta(days=2)
    log: list[ThreatEvent] = []
    for _ in range(count):
        # Whole minutes a third of the time, so rows share a source stamp.
        offset = rng.uniform(0, 10 * 86400)
        if rng.random() < 0.33:
            offset = float(int(offset // 60) * 60)
        ts = base + timedelta(seconds=offset)
        ingest = ts + timedelta(seconds=rng.choice((0.0, 0.0, 30.0, rng.uniform(0, 900))))
        log.append(event(rng.choice(AREAS), rng.choice(states), rng.choice(list(ThreatKind)),
                         ts, ingest))
    # Echoes: the same area, kind and source stamp read again with another state
    # and another ingest stamp, placed before or after the original, so the
    # fold's tie on the source stamp is decided by ingest and not by order.
    for original in rng.sample(log, 24):
        shift = timedelta(seconds=rng.choice((-45.0, 45.0, rng.uniform(-600, 600))))
        echo = event(original.area_id, rng.choice(states), original.kind,
                     original.ts_source, original.ts_ingest + shift)
        log.insert(log.index(original) + rng.choice((0, 1)), echo)
    # One poll reporting two threats of one area in the same second: a full tie.
    tie = base + timedelta(days=4, hours=3)
    log.append(event(AREAS[0], AlertState.ACTIVE, ThreatKind.DRONE, tie, tie))
    log.append(event(AREAS[0], AlertState.ACTIVE, ThreatKind.MISSILE, tie, tie))
    log.sort(key=lambda item: (item.ts_source, item.area_id))
    return log


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_areas_agree_with_compose_at_every_boundary(tmp_path: Path, seed: int) -> None:
    rng = random.Random(seed)
    end = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    log = generated_log(rng, end - timedelta(days=7))
    payload = assert_agrees(EventStore(tmp_path / "events"), log, end, 7, rng)
    assert payload["areas"]["intervals"], "a generated week with no interval tests nothing"


def test_an_alert_still_running_is_open_and_not_ended(tmp_path: Path) -> None:
    end = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    log = [event(AREAS[0], AlertState.ACTIVE, ThreatKind.DRONE, end - timedelta(hours=1))]
    payload = timeline.build(EventStore(tmp_path / "events"), log, end, table=TABLE,
                             feeds=(), days=7)
    [interval] = payload["areas"]["intervals"]  # type: ignore[index]
    assert interval["to"] is None
    assert interval["from"] == (end - timedelta(hours=1)).isoformat()


def test_a_standing_older_than_the_window_starts_at_the_window(tmp_path: Path) -> None:
    """The file's scope is the week; when the standing began is the item's `since`."""
    end = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    april = datetime(2026, 4, 19, 20, 19, 35, tzinfo=UTC)
    log = [event(AREAS[1], AlertState.ACTIVE, ThreatKind.ARTILLERY, april)]
    payload = timeline.build(EventStore(tmp_path / "events"), log, end, table=TABLE,
                             feeds=(), days=7)
    areas = payload["areas"]
    [interval] = areas["intervals"]  # type: ignore[index]
    assert interval["from"] == (end - timedelta(days=7)).isoformat()
    assert interval["since"] == april.isoformat(timespec="seconds")
    assert areas["log_reaches_window_start"] is True  # type: ignore[index]
    assert areas["places"][AREAS[1]]["oblast_name"] == "Хмельницька"  # type: ignore[index]


def test_a_log_that_starts_inside_the_window_says_so(tmp_path: Path) -> None:
    end = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    log = [event(AREAS[0], AlertState.CLEAR, ThreatKind.DRONE, end - timedelta(days=2))]
    payload = timeline.build(EventStore(tmp_path / "events"), log, end, table=TABLE,
                             feeds=(), days=7)
    assert payload["areas"]["log_reaches_window_start"] is False  # type: ignore[index]
    assert payload["areas"]["intervals"] == []  # type: ignore[index]


def test_a_row_stamped_after_the_file_is_not_in_it(tmp_path: Path) -> None:
    end = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    log = [event(AREAS[0], AlertState.ACTIVE, ThreatKind.DRONE, end + timedelta(seconds=30))]
    payload = timeline.build(EventStore(tmp_path / "events"), log, end, table=TABLE,
                             feeds=(), days=7)
    assert payload["areas"]["intervals"] == []  # type: ignore[index]


def test_a_full_tie_names_the_area_by_the_kind_and_not_by_the_order() -> None:
    """Two kinds, one state, one source stamp, one ingest stamp: one poll."""
    moment = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    rows = [event(AREAS[0], AlertState.ACTIVE, kind, moment, moment)
            for kind in (ThreatKind.MISSILE, ThreatKind.DRONE)]
    one = compose(rows, as_of=moment, table=TABLE).areas[0]
    other = compose(list(reversed(rows)), as_of=moment, table=TABLE).areas[0]
    assert one.kind is other.kind is ThreatKind.DRONE


# ---- the communiques: the recording of 2026-09-16 against `warnings_blocks`


def serve(store: EventStore, at: datetime, communiques: list[Any] | None) -> None:
    """One poll of the map scope as `mavo rso` writes it; None is a refusal."""
    if communiques is None:
        store.record_refusal(rso.FEED, poland.WARNINGS_URL, at, "HTTP Error 503")
        return
    store.append_communiques(rso.FEED, communiques)
    store.record_snapshot(rso.FEED, poland.WARNINGS_URL, at,
                          [item.digest() for item in communiques])
    store.record_read(rso.FEED, poland.WARNINGS_URL, at, len(communiques), 0)


def communique_store(path: Path) -> tuple[EventStore, datetime]:
    """Two days of the map scope: a list, an empty list, a refused stretch longer
    than the ceiling, the recorded page with its alert and all-clear, and the
    same page with the all-clear gone, so the alert paints until its end."""
    from tests.test_poland import PAGE

    store = EventStore(path)
    synthetic = list(rso.parse_page(PAGE).communiques)
    recorded = list(rso.parse_page(RECORDED_RSO.read_bytes()).communiques)
    without_all_clear = [item for item in recorded
                         if "odwołan" not in (item.fields.get("title") or "").lower()]
    assert len(without_all_clear) == len(recorded) - 1
    moment = datetime(2026, 9, 15, 0, 0, tzinfo=UTC)
    end = datetime(2026, 9, 17, 6, 0, tzinfo=UTC)
    while moment <= end:
        if moment < datetime(2026, 9, 15, 12, 0, tzinfo=UTC):
            served: list[Any] | None = synthetic
        elif moment < datetime(2026, 9, 15, 20, 0, tzinfo=UTC):
            served = []
        elif moment < datetime(2026, 9, 15, 22, 30, tzinfo=UTC):
            served = None
        elif moment < datetime(2026, 9, 16, 4, 0, tzinfo=UTC):
            served = []
        elif moment < datetime(2026, 9, 16, 12, 0, tzinfo=UTC):
            served = recorded
        else:
            served = without_all_clear
        serve(store, moment, served)
        moment += timedelta(minutes=15)
    return store, end


@pytest.fixture(scope="module")
def communiques(tmp_path_factory: pytest.TempPathFactory) -> tuple[EventStore, datetime]:
    """Built once: every test below reads it and none writes."""
    return communique_store(tmp_path_factory.mktemp("rso") / "events")


def test_the_communiques_agree_with_the_composer_at_every_boundary(
    communiques: tuple[EventStore, datetime],
) -> None:
    store, end = communiques
    payload = assert_agrees(store, [], end, 2, random.Random(7))
    rcb = payload["rcb"]
    assert rcb["recorded_since"] == "2026-09-15T00:00:00+00:00"
    nulls = [item for item in rcb["intervals"] if item["pl_warnings"] is None]
    assert [(item["from"], item["to"]) for item in nulls] == [
        ("2026-09-15T20:45:00.000001+00:00", "2026-09-15T22:30:00+00:00")
    ], "one refused stretch past the ceiling, and nothing else unreadable"


def test_an_alert_left_standing_ends_when_its_validity_does(
    communiques: tuple[EventStore, datetime],
) -> None:
    """With its all-clear gone from the list, the 07:05 alert paints lubelskie
    until `valid_to` 23:59 Warsaw, 21:59 UTC, and the tick after it is clear."""
    store, end = communiques
    payload = timeline.build(store, [], end, table=TABLE, feeds=(), days=2)
    painted = [
        (item["from"], item["to"]) for item in payload["rcb"]["intervals"]  # type: ignore[index]
        if any(row["slug"] == "lubelskie" for row in item["pl_warnings"] or [])
    ]
    assert painted[-1] == ("2026-09-16T12:00:00+00:00", "2026-09-16T21:59:00.000001+00:00")


def test_a_moment_before_the_first_poll_is_not_recorded(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    first = datetime(2026, 9, 19, 18, 38, tzinfo=UTC)
    serve(store, first, [])
    end = first + timedelta(days=1)
    payload = timeline.build(store, [], end, table=TABLE, feeds=PRODUCTION_FEEDS, days=7)
    before = timeline.picture_from_file(payload, first - timedelta(hours=1))
    assert before["rcb"] == timeline.ABSENT
    assert before["coverage"]["rso"] == "unrecorded"  # type: ignore[index]
    after = timeline.picture_from_file(payload, first + timedelta(minutes=1))
    assert after["rcb"] == {"pl_warnings": [], "pl_all_clear": []}


# ---- the airspace: the plan of 2026-09-14 against `airspace_block`


def plan_store(path: Path) -> tuple[EventStore, datetime]:
    """Polled and refused for a night, then the plan; one structure dropped from
    the list at 13:00 and back at 15:00, and a refused afternoon that keeps the
    last plan drawn, because the airspace has no age ceiling."""
    store = EventStore(path)
    page = pansa.parse(UUP.read_bytes())
    full = list(page.zones)
    fewer = [zone for zone in full if zone.designator != "EPTS9"]
    assert len(fewer) < len(full)
    moment = datetime(2026, 9, 13, 10, 0, tzinfo=UTC)
    end = datetime(2026, 9, 15, 3, 0, tzinfo=UTC)
    while moment <= end:
        if moment < datetime(2026, 9, 14, 4, 0, tzinfo=UTC) or (
                datetime(2026, 9, 14, 16, 30, tzinfo=UTC) <= moment
                < datetime(2026, 9, 14, 19, 0, tzinfo=UTC)):
            store.record_refusal(pansa.FEED, pansa.SOURCE_URL, moment, "HTTP Error 502")
        else:
            zones = fewer if (datetime(2026, 9, 14, 13, 0, tzinfo=UTC) <= moment
                              < datetime(2026, 9, 14, 15, 0, tzinfo=UTC)) else full
            store.append_airspace_zones(pansa.FEED, zones)
            store.record_snapshot(pansa.FEED, pansa.SOURCE_URL, moment,
                                  [zone.digest() for zone in zones])
            store.record_read(pansa.FEED, pansa.SOURCE_URL, moment, len(zones), page.unreadable)
        moment += timedelta(minutes=30)
    return store, end


@pytest.fixture(scope="module")
def plans(tmp_path_factory: pytest.TempPathFactory) -> tuple[EventStore, datetime]:
    """Built once: every test below reads it and none writes."""
    return plan_store(tmp_path_factory.mktemp("pansa") / "events")


def test_the_airspace_agrees_with_the_composer_at_every_boundary(
    plans: tuple[EventStore, datetime],
) -> None:
    store, end = plans
    payload = assert_agrees(store, [], end, 2, random.Random(11))
    air = payload["airspace"]
    assert air["unread"] == [{"from": "2026-09-13T10:00:00+00:00",
                              "to": "2026-09-14T04:00:00+00:00"}]
    assert set(air["geometries"]) == {item["geometry"] for item in air["intervals"]}


def test_a_zone_leaves_at_its_reservation_end_and_the_list_change(
    plans: tuple[EventStore, datetime],
) -> None:
    store, end = plans
    payload = timeline.build(store, [], end, table=TABLE, feeds=(), days=2)
    windows = sorted(
        (item["from"], item["to"]) for item in payload["airspace"]["intervals"]  # type: ignore[index]
        if item["designator"] == "EPTS9"
    )
    # 08:00 opens the first window, 13:00 drops the structure from the list,
    # 15:00 brings it back, and the later window closes a tick after 20:00.
    assert windows[0][0] == "2026-09-14T08:00:00+00:00"
    assert ("2026-09-14T08:00:00+00:00", "2026-09-14T13:00:00+00:00") in windows
    assert windows[-1][1] == "2026-09-14T20:00:00.000001+00:00"


# ---- coverage: generated polls against `measure_feed`


def test_coverage_agrees_with_liveness_at_every_boundary(tmp_path: Path) -> None:
    rng = random.Random(5)
    store = EventStore(tmp_path / "events")
    spec = FeedSpec(feed="channel", source_id="telegram", role="watchman", cadence_s=30.0)
    end = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
    moment = end - timedelta(days=1, hours=2)
    stop = end - timedelta(hours=14)
    while moment <= stop:
        if rng.random() < 0.85:
            store.record_read("channel", "https://t.me/s/air_alert_ua", moment, 20, 0)
        else:
            store.record_refusal("channel", "https://t.me/s/air_alert_ua", moment, "HTTP Error 502")
        # Mostly on cadence, sometimes a stall of up to five minutes.
        moment += timedelta(seconds=rng.choice((30.0, 31.5, 29.0, rng.uniform(60, 300))))
    payload = assert_agrees(store, [], end, 1, rng, feeds=(spec,))
    assert payload["coverage"]["channel"]["gaps"], "a day with no gap tests only half"


def test_a_past_moment_reads_the_pipe_as_it_stood_then(tmp_path: Path) -> None:
    """F188 in `liveness`: a read made later is not evidence about earlier."""
    store = EventStore(tmp_path / "events")
    spec = FeedSpec(feed="ukrainealarm", source_id="ukrainealarm", role="primary",
                    cadence_s=120.0)
    ten = datetime(2026, 9, 20, 10, 0, tzinfo=UTC)
    store.record_read("ukrainealarm", "u", ten, 1, 0)
    store.record_read("ukrainealarm", "u", ten + timedelta(hours=2), 1, 0)
    assert measure_feed(store, spec, as_of=ten + timedelta(hours=1)).state is PipeState.STALLED
    assert measure_feed(store, spec, as_of=ten - timedelta(seconds=1)).state is PipeState.UNKNOWN


# ---- the store at a moment


def test_the_tails_answer_for_a_moment(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    t0 = datetime(2026, 9, 20, 10, 0, tzinfo=UTC)
    store.record_read("x", "u", t0, 1, 0)
    store.record_refusal("x", "u", t0 + timedelta(minutes=5), "HTTP Error 503")
    store.record_read("x", "u", t0 + timedelta(minutes=10), 2, 0)
    at = t0 + timedelta(minutes=7)
    assert store.newest_attempt_at("x", at=at) == (t0 + timedelta(minutes=5)).isoformat()
    assert store.newest_read_at("x", at=at) == t0.isoformat()
    assert store.newest_read("x", at=at)["items"] == 1  # type: ignore[index]
    assert store.newest_refusal_detail("x", at=t0) is None
    assert store.newest_refusal_detail("x", at=at) == "HTTP Error 503"
    assert store.newest_read("x", at=t0) is not None, "the edge is inclusive"
    assert store.newest_read("x", at=t0 - TICK) is None
    assert store.oldest_attempt_at("x") == t0.isoformat()
    assert store.oldest_attempt_at("y") is None


def test_the_list_range_is_half_open(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    t0 = datetime(2026, 9, 20, 10, 0, tzinfo=UTC)
    for minutes, members in ((0, ["a"]), (5, ["b"]), (10, ["a"])):
        store.record_snapshot("x", "u", t0 + timedelta(minutes=minutes), members)
    rows = store.snapshots("x", "u", since=t0 + timedelta(minutes=5),
                           until=t0 + timedelta(minutes=10))
    assert [row["members"] for row in rows] == [["b"]]
    assert [row["members"] for row in store.snapshots("x", "u")] == [["a"], ["b"], ["a"]]


def test_a_past_moment_is_drawn_with_the_list_read_then(
    communiques: tuple[EventStore, datetime], plans: tuple[EventStore, datetime],
) -> None:
    """F188: until 0.58.0.0 both composers took a moment and read the newest
    list whatever it was, so the past was painted with the present."""
    store, _end = communiques
    morning = datetime(2026, 9, 15, 6, 0, tzinfo=UTC)
    warnings, _cleared = poland.warnings_blocks(store, morning)
    assert [row["slug"] for row in warnings.value] == ["malopolskie", "podkarpackie"]
    before = poland.warnings_blocks(store, datetime(2026, 9, 14, 23, 0, tzinfo=UTC))
    assert before == (poland.UNPUBLISHED, poland.UNPUBLISHED)

    plan, _plan_end = plans
    refused = poland.airspace_block(plan, datetime(2026, 9, 13, 12, 0, tzinfo=UTC))
    assert refused == poland.Block(published=True, value=None)
    later = poland.airspace_block(plan, datetime(2026, 9, 14, 17, 0, tzinfo=UTC)).value
    assert later["read_at"] == "2026-09-14T16:00:00+00:00"
    assert later["stale_error"] == "HTTP Error 502"
    earlier = poland.airspace_block(plan, datetime(2026, 9, 14, 16, 10, tzinfo=UTC)).value
    assert earlier["stale_error"] is None, "the refusal at 16:30 had not happened yet"


# ---- the file


def test_the_file_is_json_and_names_its_window(
    communiques: tuple[EventStore, datetime],
) -> None:
    store, end = communiques
    payload = timeline.build(store, [], end, table=TABLE, feeds=PRODUCTION_FEEDS, days=7)
    text = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    back = json.loads(text)
    assert back["v"] == timeline.TIMELINE_VERSION
    assert back["window"] == {"start": (end - timedelta(days=7)).isoformat(), "days": 7}
    assert set(back) == {"v", "generated_at", "window", "areas", "rcb", "airspace", "coverage"}
    assert set(back["coverage"]) == {spec.feed for spec in PRODUCTION_FEEDS}
    assert back["airspace"]["recorded_since"] is None, "PAŻP never polled in this store"


# ---- the commands: the check P0's acceptance runs on the host


def cli_store(path: Path) -> tuple[EventStore, datetime]:
    """A store with alerts in it as well as lists, written as the collectors do."""
    store, end = communique_store(path)
    rng = random.Random(3)
    store.append(generated_log(rng, end - timedelta(days=7), count=120))
    return store, end


def test_the_two_ways_of_printing_a_moment_print_the_same(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    from mavo.cli import main

    store_path = tmp_path / "events"
    _store, end = cli_store(store_path)
    written = tmp_path / "timeline.json"
    assert main(["timeline", "--store", str(store_path), "--out", str(written),
                 "--as-of", end.isoformat()]) == 0
    line = capsys.readouterr().out
    assert f"timeline={written} bytes=" in line and "gzip_bytes=" in line and "build_s=" in line
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["v"] == timeline.TIMELINE_VERSION
    for moment in ("2026-09-15T21:00:00+00:00", "2026-09-16T13:00:00+00:00", end.isoformat()):
        assert main(["timeline", "--store", str(store_path), "--at", moment]) == 0
        asked = capsys.readouterr().out
        assert main(["timeline", "--file", str(written), "--at", moment]) == 0
        chosen = capsys.readouterr().out
        assert asked == chosen, moment


def test_a_moment_outside_the_file_is_refused_and_not_answered_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    from mavo.cli import main

    store_path = tmp_path / "events"
    _store, end = cli_store(store_path)
    written = tmp_path / "timeline.json"
    assert main(["timeline", "--store", str(store_path), "--out", str(written),
                 "--as-of", end.isoformat(), "--days", "1"]) == 0
    capsys.readouterr()
    early = (end - timedelta(days=2)).isoformat()
    assert main(["timeline", "--file", str(written), "--at", early]) == 2
    assert "outside the file's window" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [
    ["timeline", "--at", "2026-09-16T12:00:00+00:00"],
    ["timeline", "--store", "x", "--at", "2026-09-16T12:00:00"],
    ["timeline", "--file", "x", "--out", "y"],
    ["timeline", "--store", "x", "--out", "y", "--days", "0"],
])
def test_a_command_that_cannot_name_its_moment_or_its_input_is_refused(
    argv: list[str], capsys: pytest.CaptureFixture[str],
) -> None:
    from mavo.cli import main

    assert main(argv) == 2
    assert capsys.readouterr().err


def test_the_report_loop_writes_the_timeline_beside_the_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    from mavo.cli import main

    store_path = tmp_path / "events"
    cli_store(store_path)
    state, written = tmp_path / "state.json", tmp_path / "timeline.json"
    assert main(["report", "--store", str(store_path), "--json", str(state),
                 "--timeline", str(written), "--watch", "--interval", "0",
                 "--max-cycles", "1"]) == 0
    capsys.readouterr()
    contract = json.loads(state.read_text(encoding="utf-8"))
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["v"] == timeline.TIMELINE_VERSION
    # One moment for both files: the contract prints it to the second.
    moment = datetime.fromisoformat(payload["generated_at"]).replace(microsecond=0)
    assert moment == datetime.fromisoformat(contract["generated_at"])
    assert main(["report", "--store", str(store_path), "--json", str(state),
                 "--timeline", str(written), "--timeline-every", "0"]) == 2


def test_a_cycle_that_could_not_replay_writes_no_timeline(tmp_path: Path) -> None:
    """An empty log is a week with no alerts; a file saying so is silence as calm."""
    from mavo.report import publish

    def unreadable() -> list[ThreatEvent]:
        raise OSError("disk I/O error")

    built: list[datetime] = []

    def builder(events: object, moment: datetime) -> dict[str, object]:
        built.append(moment)
        return {"v": timeline.TIMELINE_VERSION}

    written = tmp_path / "timeline.json"
    outcome = publish(unreadable, tmp_path / "state.json", interval_s=0, max_cycles=2,
                      sleep=lambda _s: None, table=TABLE, timeline_path=written,
                      timeline=builder)
    assert outcome.written == 2, "the contract is still written, blind"
    assert built == [] and not written.exists()


def test_the_timeline_is_written_on_its_own_cadence(tmp_path: Path) -> None:
    from mavo.report import publish

    built: list[datetime] = []

    def builder(events: object, moment: datetime) -> dict[str, object]:
        built.append(moment)
        return {"v": timeline.TIMELINE_VERSION}

    publish(list, tmp_path / "state.json", interval_s=0, max_cycles=5,
            sleep=lambda _s: None, table=TABLE, timeline_path=tmp_path / "t.json",
            timeline=builder, timeline_every=2)
    assert len(built) == 3, "cycles one, three and five"
    with pytest.raises(ValueError):
        publish(list, tmp_path / "state.json", interval_s=0, max_cycles=1,
                sleep=lambda _s: None, table=TABLE, timeline_path=tmp_path / "t.json",
                timeline=builder, timeline_every=0)


# ---- the recorder: the week that leaves the host answers as the store does


def test_the_recorded_week_answers_as_the_store_it_came_from(tmp_path: Path) -> None:
    """`mavo/recorder.py`, run as on the host before its release is installed
    (the module on stdin, the store read-only), keeps every row the week's
    check reads: the file built from the copy equals the file built from the
    store, the log's first stamp aside, and so does every moment asked of
    either. The subcommand is the same code, asked once more below."""
    import subprocess
    import sys

    full = tmp_path / "events"
    communique_store(full)
    plan_store(full)
    store = EventStore(full)
    rng = random.Random(9)
    end = datetime(2026, 9, 17, 6, 0, tzinfo=UTC)
    store.append(generated_log(rng, end - timedelta(days=3), count=200))
    # A category the map never reads, listed inside the window: it stays behind.
    weather = rso.page_url("meteorologiczne", 0)
    recorded = list(rso.parse_page(RECORDED_RSO.read_bytes()).communiques)
    store.append_communiques(rso.FEED, recorded)
    store.record_snapshot(rso.FEED, weather, end - timedelta(hours=5),
                          [item.digest() for item in recorded[:30]])
    store.record_read(rso.FEED, weather, end - timedelta(hours=5), 30, 0)
    copy = tmp_path / "week.sqlite3"
    script = Path(__file__).parents[1] / "mavo" / "recorder.py"
    with script.open("rb") as stdin:
        done = subprocess.run(
            [sys.executable, "-", str(full), str(copy), end.isoformat(), "3"],
            stdin=stdin, capture_output=True, check=True,
        )
    summary = json.loads(done.stdout)
    assert summary["days"] == 3 and summary["rows"]["events"] > 0
    assert full.stat().st_size > copy.stat().st_size

    week = EventStore(copy)
    events, copied = list(store.replay()), list(week.replay())
    assert len(copied) < len(events)
    assert week.newest_snapshot(rso.FEED, weather) is None
    assert week.newest_read(rso.FEED, weather) is not None, "every poll is kept for coverage"
    one = normalised(timeline.build(store, events, end, table=TABLE,
                                    feeds=PRODUCTION_FEEDS, days=3))
    other = normalised(timeline.build(week, copied, end, table=TABLE,
                                      feeds=PRODUCTION_FEEDS, days=3))
    assert isinstance(one, dict) and isinstance(other, dict)
    for payload in (one, other):
        payload["areas"].pop("oldest_observation")
    assert one == other
    for moment in moments(one, rng, count=20, edges=30):
        assert normalised(timeline.picture_from_store(
            store, events, moment, table=TABLE, feeds=PRODUCTION_FEEDS)) == normalised(
            timeline.picture_from_store(week, copied, moment, table=TABLE,
                                        feeds=PRODUCTION_FEEDS)), moment


def test_the_subcommand_records_and_refuses_what_it_cannot_do(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    from mavo.cli import main

    full = tmp_path / "events"
    communique_store(full)
    out = tmp_path / "week.sqlite3"
    end = "2026-09-17T06:00:00+00:00"
    assert main(["record-week", str(full), str(out), end, "2"]) == 0
    assert json.loads(capsys.readouterr().out)["rows"]["feed_snapshots"] > 0
    assert main(["record-week", str(full), str(out), end]) == 2, "written once"
    assert main(["record-week", str(full), str(tmp_path / "b"), "2026-09-17T06:00"]) == 2
    assert main(["record-week", str(full), str(tmp_path / "c"), end, "0"]) == 2
    assert main(["record-week", str(full), str(tmp_path / "d"), end, "seven"]) == 2
    assert "record-week" in capsys.readouterr().err


def test_the_recorder_names_the_lists_the_timeline_reads() -> None:
    """The recorder imports nothing from the package, so it writes the two
    addresses out; if either drifts, a recorded week holds the wrong lists."""
    from mavo.recorder import MAP_LISTS

    assert set(MAP_LISTS) == {(rso.FEED, poland.WARNINGS_URL),
                              (pansa.FEED, pansa.SOURCE_URL)}
