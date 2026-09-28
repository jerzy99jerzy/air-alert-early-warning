"""Two days of RCB air alerts per voivodeship: `pl_rcb_recent` (D-062).

What painted is decided by the composer: `timeline.rcb_layer` walks the window
and `poland.warnings_verdict` answers at every instant. So the first property
here is agreement: what this key calls painted at a moment is what
`warnings_blocks` paints at that moment, asked directly. The second is the
reason each painting stopped and the all-clears RCB announced, which are read
off the recorded lists version by version, and those are held against a week
the production store recorded (`tests/fixtures/store_week_2026-09-26.sqlite3.xz`),
because the ways RCB ends an alert were found there and not imagined here.

Every stamp asserted against the recording was read off the rows first: the
list reads in `feed_snapshots.observed_at` where a communique entered or left
the `ogolne` list, and the communique's own `valid_from`, `valid_to` and
`updated_at`, which RCB edits in place (23362967's `valid_to` went from 23:59
to 02:00; 23361098's `updated_at` moved to 06:59:33 when it became an
all-clear). What the recording cannot show is served into a real store from
recorded rows, some with one field changed, in orders RCB never used, and
each test says which.
"""

from __future__ import annotations

import hashlib
import json
import lzma
import random
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from mavo import poland, rcb_recent
from mavo.cli import main
from mavo.poland import Block
from mavo.report import compose, to_contract
from mavo.sources import rso
from mavo.store import EventStore
from mavo.timeline import TICK, RcbLayer
from tests.test_timeline import RECORDED_RSO, communique_store, serve
from tests.test_timeline_recorded_week import DIGEST, FIXTURE

#: The recording ends here, and its RCB record starts at 2026-09-19 18:38:28.
END = datetime(2026, 9, 26, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def week(tmp_path_factory: pytest.TempPathFactory) -> EventStore:
    raw = lzma.decompress(FIXTURE.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == DIGEST, "the recording was edited"
    path = tmp_path_factory.mktemp("week") / "events"
    path.write_bytes(raw)
    return EventStore(path)


def value(store: EventStore, end: datetime, hours: int = rcb_recent.RECENT_HOURS
          ) -> dict[str, Any]:
    block = rcb_recent.measure(store, end, hours=hours)
    assert block.published and isinstance(block.value, dict)
    # What the contract writer will do with it, so nothing here passes on a
    # shape `json` would refuse.
    back = json.loads(json.dumps(block.value, ensure_ascii=False, allow_nan=False))
    assert isinstance(back, dict)
    return back


def alerts(summary: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["slug"], alert["id"]): alert
            for row in summary["voivodeships"] for alert in row["alerts"]}


def clears(summary: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["slug"], clear["id"]): clear
            for row in summary["voivodeships"] for clear in row["all_clears"]}


def painted_by_the_composer(store: EventStore, moment: datetime) -> set[tuple[str, str]]:
    warnings, _cleared = poland.warnings_blocks(store, moment)
    assert warnings.published and warnings.value is not None
    return {(row["slug"], item["id"])
            for row in warnings.value for item in row["communiques"]}


def second(stamp: str | None) -> str | None:
    """A stamp to the second, in UTC, as the assertions below were read off the rows."""
    return None if stamp is None else stamp[:19]


def ends(summary: dict[str, Any]) -> dict[tuple[str, str], tuple[str, str | None, str,
                                                                     str | None]]:
    return {key: (alert["ended"]["reason"], second(alert["ended"]["at"]),
                  alert["ended"]["clock"], alert["ended"]["by"])
            for key, alert in alerts(summary).items() if alert["ended"] is not None}


def recorded_row(store: EventStore, source_id: str, version: int = 0) -> rso.Communique:
    """One version of a communique of the recorded week, as the reader parsed it."""
    with closing(sqlite3.connect(store.path)) as conn:
        provinces, fields = conn.execute(
            "SELECT provinces, fields FROM communiques WHERE source_id = ? "
            "ORDER BY ts_ingest LIMIT 1 OFFSET ?", (source_id, version)).fetchone()
    return rso.Communique(
        id=source_id,
        provinces=tuple(rso.Province(slug=p[0], name=p[1], city=p[2])
                        for p in json.loads(provinces)),
        fields=json.loads(fields))


def changed(item: rso.Communique, provinces: tuple[rso.Province, ...] | None = None,
            **fields: str | None) -> rso.Communique:
    """The same communique with one thing changed, for a case no recording holds."""
    return rso.Communique(id=item.id,
                          provinces=provinces if provinces is not None else item.provinces,
                          fields={**item.fields, **fields})


def run(store: EventStore, t0: datetime, lists: list[list[rso.Communique] | None],
        step: timedelta = timedelta(minutes=15)) -> None:
    for index, served in enumerate(lists):
        serve(store, t0 + step * index, served)


def _recorded() -> tuple[list[rso.Communique], list[rso.Communique]]:
    recorded = list(rso.parse_page(RECORDED_RSO.read_bytes()).communiques)
    alone = [item for item in recorded
             if "odwołan" not in (item.fields.get("title") or "").lower()]
    return recorded, alone


# ---- the recorded week


def test_the_last_two_days_of_the_recording_read_as_the_rows_say(week: EventStore) -> None:
    """The window 2026-09-24 00:00 to 2026-09-26 00:00 UTC. Six alerts on two
    voivodeships, and none of them ended by D-055's pairing inside one list:
    rewritten in place, replaced at one read, run out, withdrawn."""
    summary = value(week, END)
    assert summary["hours"] == 48
    assert (summary["start"], summary["end"]) == (
        "2026-09-24T00:00:00+00:00", "2026-09-26T00:00:00+00:00")
    assert summary["recorded_since"] == "2026-09-19T18:38:28.168793+00:00"
    assert summary["unread"] == [], "no two reads of the list further apart than 30 min"
    assert [row["slug"] for row in summary["voivodeships"]] == ["lubelskie", "podkarpackie"]
    assert {key: (second(alert["painted"][0]["from"]), second(alert["painted"][-1]["to"]))
            for key, alert in alerts(summary).items()} == {
        ("lubelskie", "23361098"): ("2026-09-24T03:51:16", "2026-09-24T05:09:01"),
        ("lubelskie", "23361410"): ("2026-09-24T06:12:06", "2026-09-24T13:11:16"),
        ("lubelskie", "23362967"): ("2026-09-24T19:51:34", "2026-09-25T00:00:00"),
        ("podkarpackie", "23361411"): ("2026-09-24T06:43:06", "2026-09-24T12:55:31"),
        ("podkarpackie", "23363073"): ("2026-09-24T20:06:44", "2026-09-24T21:59:00"),
        ("podkarpackie", "23363287"): ("2026-09-24T22:41:40", "2026-09-25T00:59:00"),
    }
    assert ends(summary) == {
        # Listed as "zakończył się atak" at the 05:09:01 read with `valid_from`
        # unchanged and `updated_at` 06:59:33 Warsaw: RCB's own time for the edit.
        ("lubelskie", "23361098"): ("rewritten", "2026-09-24T04:59:33", "rcb", "23361098"),
        # Left the list at 13:11:16 as 23362253 entered it: dated by RCB's
        # stamp for that all-clear, `updated_at` 15:01:55 Warsaw, the same
        # moment its own line carries as `announced`.
        ("lubelskie", "23361410"): ("all_clear", "2026-09-24T13:01:55", "rcb", "23362253"),
        # `valid_to` moved from 23:59 to 02:00 Warsaw; it ran out at 00:00 UTC,
        # fourteen minutes before the list dropped it.
        ("lubelskie", "23362967"): ("expired", "2026-09-25T00:00:00", "rcb", None),
        # First read gone at 12:55:31, 4.5 minutes before `valid_to` 15:00 Warsaw, and no
        # all-clear for podkarpackie that day.
        ("podkarpackie", "23361411"): ("withdrawn", "2026-09-24T12:55:31", "read", None),
        ("podkarpackie", "23363073"): ("expired", "2026-09-24T21:59:00", "rcb", None),
        ("podkarpackie", "23363287"): ("expired", "2026-09-25T00:59:00", "rcb", None),
    }
    assert {key: (second(clear["announced"]), second(clear["appeared"]), clear["valid_from"],
                  clear["ended"])
            for key, clear in clears(summary).items()} == {
        # Announced at the rewrite, not at the alert's 05:44 it still carries.
        ("lubelskie", "23361098"): ("2026-09-24T04:59:33", "2026-09-24T05:09:01",
                                    "2026-09-24T05:44:00+02:00", []),
        ("lubelskie", "23362253"): ("2026-09-24T13:01:55", "2026-09-24T13:11:16",
                                    "2026-09-24T15:01:00+02:00", []),
        # Dated 05:22 Warsaw, three hours after the alert it follows ran out.
        ("lubelskie", "23364006"): ("2026-09-25T03:24:57", "2026-09-25T03:38:54",
                                    "2026-09-25T05:22:00+02:00", []),
    }


def test_the_week_ends_its_eight_alerts_four_ways_and_pairs_none(week: EventStore) -> None:
    """The whole record, 2026-09-19 18:38 to the end. D-055 pairs an alert
    with an all-clear only inside one list, and RCB never listed the two
    together: this is the finding the reasons exist to carry."""
    summary = value(week, END, hours=7 * 24)
    reasons = Counter(reason for reason, _at, _clock, _by in ends(summary).values())
    assert reasons == {"rewritten": 3, "expired": 3, "all_clear": 1, "withdrawn": 1}
    assert all(clear["ended"] == [] for clear in clears(summary).values())
    assert summary["unread"] == [{"from": "2026-09-19T00:00:00+00:00",
                                  "to": "2026-09-19T18:38:28.168793+00:00"}], (
        "the window starts before the record, and says where the record starts")
    assert set(rcb_recent.ENDINGS) >= set(reasons)
    rewrites = [at for reason, at, clock, _by in ends(summary).values() if reason == "rewritten"]
    assert sorted(rewrites) == ["2026-09-21T21:19:26", "2026-09-23T05:51:03",
                                "2026-09-24T04:59:33"], "each rewrite on RCB's own `updated_at`"


def test_what_the_key_calls_painted_is_what_the_composer_painted(week: EventStore) -> None:
    """One rule. Every stretch the week's summary calls painted is painted by
    `warnings_blocks` at its first instant and its last tick and not at its end;
    and at every sampled end the alerts still open are the list painted then."""
    summary = value(week, END, hours=7 * 24)
    for (slug, communique), alert in alerts(summary).items():
        for stretch in alert["painted"]:
            start = datetime.fromisoformat(stretch["from"])
            assert (slug, communique) in painted_by_the_composer(week, start)
            assert stretch["to"] is not None
            stop = datetime.fromisoformat(stretch["to"])
            assert (slug, communique) in painted_by_the_composer(week, stop - TICK)
            assert (slug, communique) not in painted_by_the_composer(week, stop)
    rng = random.Random(59)
    record = datetime(2026, 9, 19, 18, 38, 28, 168793, tzinfo=UTC)
    moments = {record + (END - record) * rng.random() for _ in range(25)}
    for alert in alerts(summary).values():
        for stretch in alert["painted"]:
            for edge in (stretch["from"], stretch["to"]):
                moment = datetime.fromisoformat(edge)
                moments.update({moment - TICK, moment, moment + TICK})
    for end in sorted(moments):
        recent = value(week, end)
        still = {key for key, alert in alerts(recent).items() if alert["ended"] is None}
        assert still == painted_by_the_composer(week, end), end.isoformat()
        assert all(alert["painted"][-1]["to"] is None
                   for alert in alerts(recent).values() if alert["ended"] is None)


def test_a_clearance_announced_before_the_window_is_not_one_of_its_events(
    week: EventStore,
) -> None:
    """Window 2026-09-23 08:00 to 2026-09-25 08:00 UTC. 23358462's all-clear,
    announced by its `updated_at` 07:51:03 Warsaw on 2026-09-23 and still listed
    when the window opens - the list dropped it at 10:18:39 - belongs to the
    morning before the window. Its alert stopped painting before it too."""
    summary = value(week, datetime(2026, 9, 25, 8, 0, tzinfo=UTC))
    assert sorted(clears(summary)) == [("lubelskie", "23361098"), ("lubelskie", "23362253"),
                                       ("lubelskie", "23364006")]
    assert ("lubelskie", "23358462") not in alerts(summary)
    whole = value(week, END, hours=7 * 24)
    assert ("lubelskie", "23358462") in clears(whole), (
        "the same all-clear is an event of a window that holds its announcement")


def test_a_rewrite_inside_the_window_counts_though_its_valid_from_is_older(
    week: EventStore,
) -> None:
    """Twelve hours from 04:30 UTC on 2026-09-24. 23361098 was issued at 03:44
    UTC, before the window, and rewritten at 04:59:33, inside it: the alert is
    painted from the window's start, and the all-clear it became is an event of
    the window whatever its `valid_from` says."""
    start = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
    summary = value(week, start + timedelta(hours=12), hours=12)
    alert = alerts(summary)[("lubelskie", "23361098")]
    assert alert["painted"][0]["from"] == "2026-09-24T04:30:00+00:00"
    assert alert["ended"]["reason"] == "rewritten"
    clear = clears(summary)[("lubelskie", "23361098")]
    assert (clear["valid_from"], second(clear["announced"])) == (
        "2026-09-24T05:44:00+02:00", "2026-09-24T04:59:33")


def test_the_most_recent_voivodeship_comes_first(week: EventStore) -> None:
    """Ordered by the last moment of anything on each voivodeship, the
    window's end for what is still painted, and by slug on a tie. At 00:30 UTC
    on 2026-09-25 lubelskie's alert ran out half an hour earlier and
    podkarpackie's 23363287 is painted until 00:59, so podkarpackie leads; at
    21:00 UTC the day before both are painted and the slug decides."""
    after_midnight = value(week, datetime(2026, 9, 25, 0, 30, tzinfo=UTC))
    assert [row["slug"] for row in after_midnight["voivodeships"]] == [
        "podkarpackie", "lubelskie"]
    assert sorted(key for key, alert in alerts(after_midnight).items()
                  if alert["ended"] is None) == [("podkarpackie", "23363287")]
    evening = value(week, datetime(2026, 9, 24, 21, 0, tzinfo=UTC))
    assert [row["slug"] for row in evening["voivodeships"]] == ["lubelskie", "podkarpackie"]
    assert sorted(key for key, alert in alerts(evening).items() if alert["ended"] is None) == [
        ("lubelskie", "23362967"), ("podkarpackie", "23363073")]
    afternoon = value(week, datetime(2026, 9, 24, 13, 0, tzinfo=UTC))
    assert [row["slug"] for row in afternoon["voivodeships"]] == [
        "lubelskie", "podkarpackie"]
    assert alerts(afternoon)[("podkarpackie", "23361411")]["ended"]["reason"] == "withdrawn"
    assert alerts(afternoon)[("lubelskie", "23361410")]["ended"] is None


# ---- what the recording cannot show


def test_a_stretch_nobody_read_is_listed_from_the_last_read_to_the_next(
    tmp_path: Path,
) -> None:
    """The timeline's own store: the synthetic page to 12:00, empty lists, polls
    refused from 20:00 to 22:15, the recorded page with its alert and all-clear
    from 04:00, and the alert alone from 12:00 on 2026-09-16. The last read
    before the refusals is 19:45 and the next 22:30, further apart than the
    pipe's thirty minutes, so that stretch is unread, the verdict's own `null`
    from 20:45 inside it."""
    store, end = communique_store(tmp_path / "events")
    summary = value(store, end)
    assert summary["unread"] == [{"from": "2026-09-15T19:45:00+00:00",
                                  "to": "2026-09-15T22:30:00+00:00"}]
    assert [row["slug"] for row in summary["voivodeships"]] == [
        "lubelskie", "malopolskie", "podkarpackie"]
    found = {key: (alert["painted"], alert["ended"]) for key, alert in alerts(summary).items()}
    left = [{"from": "2026-09-15T06:00:00+00:00", "to": "2026-09-15T12:00:00+00:00"}]
    gone = {"reason": "withdrawn", "at": "2026-09-15T12:00:00+00:00", "clock": "read",
            "by": None}
    assert found == {
        ("malopolskie", "1"): (left, gone),
        ("malopolskie", "3"): (left, gone),
        ("podkarpackie", "3"): (left, gone),
        # Paired with its all-clear and unpainted from 04:00; painted when the
        # all-clear left, until `valid_to` 23:59 Warsaw.
        ("lubelskie", "23337896"): (
            [{"from": "2026-09-16T12:00:00+00:00", "to": "2026-09-16T21:59:00.000001+00:00"}],
            {"reason": "expired", "at": "2026-09-16T21:59:00+00:00", "clock": "rcb",
             "by": None}),
    }
    assert alerts(summary)[("malopolskie", "1")]["valid_from"] is None, (
        "a communique with no issue stamp is listed with none, not with a guess")
    assert clears(summary) == {("lubelskie", "23337898"): {
        "id": "23337898", "title": "ALERT RCB- ODWOŁANIE ZAGROŻENIA",
        "valid_from": "2026-09-16T07:36:00+02:00", "air_term": "odwołan",
        "announced": "2026-09-16T05:37:29+00:00", "appeared": "2026-09-16T04:00:00+00:00",
        "ended": ["23337896"]}}


def test_an_all_clear_that_joins_its_alert_ends_it_at_rcbs_own_stamp(tmp_path: Path) -> None:
    """D-055 inside one list, after the alert has painted: the alert alone
    from 05:06, then the page with both from 05:51. The end is 07:37:29
    Warsaw, RCB's `updated_at` for the all-clear and the `announced` its own
    line carries, and not the read that saw it."""
    store = EventStore(tmp_path / "events")
    recorded, alone = _recorded()
    t0 = datetime(2026, 9, 16, 5, 6, tzinfo=UTC)
    run(store, t0, [alone] * 3 + [recorded] * 9)
    summary = value(store, t0 + timedelta(hours=3))
    alert = alerts(summary)[("lubelskie", "23337896")]
    assert alert["painted"] == [{"from": "2026-09-16T05:06:00+00:00",
                                 "to": "2026-09-16T05:51:00+00:00"}]
    assert alert["ended"] == {"reason": "all_clear", "at": "2026-09-16T05:37:29+00:00",
                              "clock": "rcb", "by": "23337898"}
    clear = clears(summary)[("lubelskie", "23337898")]
    assert (clear["ended"], clear["announced"]) == (["23337896"], alert["ended"]["at"])


def test_an_alert_whose_valid_from_moves_back_ends_at_the_all_clear_d055_names(
    tmp_path: Path,
) -> None:
    """The recorded pair with the alert first dated 07:40 Warsaw, after the
    all-clear's 07:36, so both are listed and the alert paints; then dated
    07:05 as recorded, and D-055 pairs them. The end is the all-clear the
    composer names, not a withdrawal."""
    store = EventStore(tmp_path / "events")
    recorded, _alone = _recorded()
    clear = next(item for item in recorded if item.id == "23337898")
    alert = next(item for item in recorded if item.id == "23337896")
    late = changed(alert, valid_from="2026-09-16 07:40:00")
    t0 = datetime(2026, 9, 16, 5, 45, tzinfo=UTC)
    run(store, t0, [[late, clear]] * 3 + [[alert, clear]] * 3)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("lubelskie", "23337896")]["ended"] == {
        "reason": "all_clear", "at": "2026-09-16T05:37:29+00:00", "clock": "rcb",
        "by": "23337898"}
    assert clears(summary)[("lubelskie", "23337898")]["ended"] == ["23337896"]


def test_a_rewrite_already_expired_at_the_next_read_is_still_a_rewrite(
    tmp_path: Path, week: EventStore,
) -> None:
    """23361098's two recorded versions, the all-clear first read at 06:15 UTC,
    after the 08:00 Warsaw `valid_to` RCB gave it: the verdict drops it as
    expired, and the summary still reads the rewrite on RCB's `updated_at` and
    lists the all-clear. A late read, not an order RCB never used."""
    store = EventStore(tmp_path / "events")
    alert, rewrite = recorded_row(week, "23361098", 0), recorded_row(week, "23361098", 1)
    t0 = datetime(2026, 9, 24, 3, 45, tzinfo=UTC)
    run(store, t0, [[alert]] * 10 + [[rewrite]] * 2)
    summary = value(store, t0 + timedelta(hours=3))
    assert alerts(summary)[("lubelskie", "23361098")]["ended"] == {
        "reason": "rewritten", "at": "2026-09-24T04:59:33+00:00", "clock": "rcb",
        "by": "23361098"}
    clear = clears(summary)[("lubelskie", "23361098")]
    assert (clear["announced"], clear["appeared"]) == (
        "2026-09-24T04:59:33+00:00", "2026-09-24T06:15:00+00:00")


def test_a_valid_to_moved_into_the_past_ends_it_as_expired(
    tmp_path: Path, week: EventStore,
) -> None:
    """23362967's versions in the reverse of RCB's order: until 02:00 Warsaw
    first, then until 23:59 the day before, read at 23:00 UTC when that had
    passed. The verdict drops the second version as expired; the end is its
    `valid_to`, not a withdrawal."""
    store = EventStore(tmp_path / "events")
    first, second_version = recorded_row(week, "23362967", 0), recorded_row(week, "23362967", 1)
    t0 = datetime(2026, 9, 24, 22, 0, tzinfo=UTC)
    run(store, t0, [[second_version]] * 4 + [[first]] * 2)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("lubelskie", "23362967")]["ended"] == {
        "reason": "expired", "at": "2026-09-24T21:59:00+00:00", "clock": "rcb", "by": None}


def test_an_all_clear_outranks_a_valid_to_that_passed_at_the_same_read(
    tmp_path: Path, week: EventStore,
) -> None:
    """The case above with 23364006, a later lubelskie all-clear, listed at the
    read where the alert's `valid_to` is found passed: the publisher's words
    come before a field running out."""
    store = EventStore(tmp_path / "events")
    first, second_version = recorded_row(week, "23362967", 0), recorded_row(week, "23362967", 1)
    later = recorded_row(week, "23364006")
    t0 = datetime(2026, 9, 24, 22, 0, tzinfo=UTC)
    run(store, t0, [[second_version]] * 4 + [[first, later]] * 2)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("lubelskie", "23362967")]["ended"] == {
        "reason": "all_clear", "at": "2026-09-25T03:24:57+00:00", "clock": "rcb",
        "by": "23364006"}


def test_the_earliest_of_two_all_clears_is_the_end(tmp_path: Path, week: EventStore) -> None:
    """23361410 leaves the list at the read that first lists two lubelskie
    all-clears dated after it, 15:01 and, a day early, 05:22: the end is the
    first of them."""
    store = EventStore(tmp_path / "events")
    alert = recorded_row(week, "23361410")
    first_clear, second_clear = recorded_row(week, "23362253"), recorded_row(week, "23364006")
    t0 = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    run(store, t0, [[alert]] * 5 + [[second_clear, first_clear]] * 3)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("lubelskie", "23361410")]["ended"] == {
        "reason": "all_clear", "at": "2026-09-24T13:01:55+00:00", "clock": "rcb",
        "by": "23362253"}


def test_an_alert_with_no_issue_stamp_is_never_ended_by_an_all_clear(tmp_path: Path) -> None:
    """D-055's safe side: the synthetic page's malopolskie alert carries no
    `valid_from`, and the recorded all-clear moved onto malopolskie is listed
    as it leaves. With no stamp to order them by, the all-clear ends nothing."""
    from tests.test_poland import PAGE

    store = EventStore(tmp_path / "events")
    undated = next(item for item in rso.parse_page(PAGE).communiques if item.id == "1")
    recorded, _alone = _recorded()
    clear = next(item for item in recorded if item.id == "23337898")
    moved = changed(clear, provinces=(rso.Province(slug="malopolskie", name="Małopolskie"),))
    t0 = datetime(2026, 9, 16, 5, 45, tzinfo=UTC)
    run(store, t0, [[undated]] * 3 + [[moved]] * 3)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("malopolskie", "1")]["ended"]["reason"] == "withdrawn"
    assert ("malopolskie", "23337898") in clears(summary)


def test_the_name_shown_is_the_feeds_and_the_slug_is_the_key(tmp_path: Path) -> None:
    """In the page recorded 2026-09-16 name and slug differ for four of eleven
    voivodeships (D-055). The recorded alert moved onto `slaskie`, named
    Śląskie by the feed: the row is keyed on the slug and shows the name."""
    store = EventStore(tmp_path / "events")
    _recorded_page, alone = _recorded()
    alert = next(item for item in alone if item.id == "23337896")
    moved = changed(alert, provinces=(rso.Province(slug="slaskie", name="Śląskie"),))
    t0 = datetime(2026, 9, 16, 5, 10, tzinfo=UTC)
    run(store, t0, [[moved]] * 4)
    [row] = value(store, t0 + timedelta(hours=1))["voivodeships"]
    assert (row["slug"], row["voivodeship"]) == ("slaskie", "śląskie")


def test_an_all_clear_issued_before_the_alert_never_ends_it(
    tmp_path: Path, week: EventStore,
) -> None:
    """D-055's order of stamps: 23362967, issued 21:42 Warsaw on 2026-09-24,
    leaves the list at the read that first lists 23362253, the all-clear dated
    15:01 the same day and valid until 23:59. Both name lubelskie, and the
    earlier one is not this alert's end, so the alert was withdrawn. Real rows,
    in an order RCB never used."""
    store = EventStore(tmp_path / "events")
    alert = recorded_row(week, "23362967")
    earlier = recorded_row(week, "23362253")
    t0 = datetime(2026, 9, 24, 19, 55, tzinfo=UTC)
    run(store, t0, [[alert]] * 4 + [[earlier]] * 4)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("lubelskie", "23362967")]["ended"] == {
        "reason": "withdrawn", "at": "2026-09-24T20:55:00+00:00", "clock": "read", "by": None}
    assert clears(summary)[("lubelskie", "23362253")]["ended"] == []


def test_an_all_clear_for_another_voivodeship_is_not_this_ones_end(
    tmp_path: Path, week: EventStore,
) -> None:
    """The pairing is per voivodeship. podkarpackie's 23363073, issued 22:01
    Warsaw on 2026-09-24, leaves the list at the read that first lists
    lubelskie's 23364006, dated after it. Real rows, in an order RCB never
    used: the all-clear is listed hours before its own stamp, which this rule
    does not read, and the alert leaves an hour before its `valid_to`."""
    store = EventStore(tmp_path / "events")
    alert = recorded_row(week, "23363073")
    elsewhere = recorded_row(week, "23364006")
    t0 = datetime(2026, 9, 24, 20, 5, tzinfo=UTC)
    run(store, t0, [[alert]] * 4 + [[elsewhere]] * 4)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("podkarpackie", "23363073")]["ended"] == {
        "reason": "withdrawn", "at": "2026-09-24T21:05:00+00:00", "clock": "read", "by": None}
    assert ("lubelskie", "23364006") in clears(summary)


def test_an_all_clear_that_was_an_alert_dates_the_end_by_its_rewrite(
    tmp_path: Path, week: EventStore,
) -> None:
    """23361410 stands; another lubelskie communique joins it already rewritten
    into an all-clear, raised at 08:10 Warsaw and rewritten at 09:10. D-055
    pairs them, and the end is the rewrite, the all-clear's `announced`, not
    the 08:10 its `valid_from` kept. 23358462's rewrite with its three stamps
    moved onto that day, an order RCB never used."""
    store = EventStore(tmp_path / "events")
    alert = recorded_row(week, "23361410")
    other = changed(recorded_row(week, "23358462", 1), valid_from="2026-09-24 08:10:00",
                    valid_to="2026-09-24 23:59:00", updated_at="2026-09-24 09:10:00")
    t0 = datetime(2026, 9, 24, 6, 15, tzinfo=UTC)
    run(store, t0, [[alert]] * 4 + [[alert, other]] * 2)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("lubelskie", "23361410")]["ended"] == {
        "reason": "all_clear", "at": "2026-09-24T07:10:00+00:00", "clock": "rcb",
        "by": "23358462"}
    clear = clears(summary)[("lubelskie", "23358462")]
    assert (clear["valid_from"], clear["announced"]) == (
        "2026-09-24T08:10:00+02:00", "2026-09-24T07:10:00+00:00")


def test_an_all_clear_whose_stamp_does_not_read_falls_back_on_the_read(
    tmp_path: Path, week: EventStore,
) -> None:
    """23362253 with its `updated_at` in the hour the autumn clock change
    doubles: the end it gives 23361410 is on the read's clock, and the
    all-clear is still an event of the window, placed by the read that first
    listed it. Real rows, one stamp changed."""
    store = EventStore(tmp_path / "events")
    alert = recorded_row(week, "23361410")
    clear = changed(recorded_row(week, "23362253"), updated_at="2026-10-25 02:30:00")
    t0 = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
    run(store, t0, [[alert]] * 5 + [[clear]] * 3)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("lubelskie", "23361410")]["ended"] == {
        "reason": "all_clear", "at": "2026-09-24T13:15:00+00:00", "clock": "read",
        "by": "23362253"}
    listed = clears(summary)[("lubelskie", "23362253")]
    assert (listed["announced"], listed["appeared"]) == (None, "2026-09-24T13:15:00+00:00")


def test_a_rewrite_whose_stamp_does_not_read_is_dated_by_the_read_that_saw_it(
    tmp_path: Path, week: EventStore,
) -> None:
    """23361098's rewrite with its `updated_at` in the doubled autumn hour:
    `rewritten` stays, on the read's clock. Real rows, one stamp changed."""
    store = EventStore(tmp_path / "events")
    alert = recorded_row(week, "23361098", 0)
    rewrite = changed(recorded_row(week, "23361098", 1), updated_at="2026-10-25 02:30:00")
    t0 = datetime(2026, 9, 24, 3, 45, tzinfo=UTC)
    run(store, t0, [[alert]] * 5 + [[rewrite]] * 2)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("lubelskie", "23361098")]["ended"] == {
        "reason": "rewritten", "at": "2026-09-24T05:00:00+00:00", "clock": "read",
        "by": "23361098"}


def test_a_later_threat_in_its_place_does_not_end_it_as_an_all_clear(
    tmp_path: Path, week: EventStore,
) -> None:
    """podkarpackie's 23363073 leaves the list at the read that first lists
    23363287, the next podkarpackie alert, issued after it. A threat ends
    nothing under D-055, so the first was withdrawn. Real rows, swapped at one
    read, which RCB never did."""
    store = EventStore(tmp_path / "events")
    first, second_alert = recorded_row(week, "23363073"), recorded_row(week, "23363287")
    t0 = datetime(2026, 9, 24, 20, 5, tzinfo=UTC)
    run(store, t0, [[first]] * 4 + [[second_alert]] * 4)
    summary = value(store, t0 + timedelta(hours=2))
    assert alerts(summary)[("podkarpackie", "23363073")]["ended"] == {
        "reason": "withdrawn", "at": "2026-09-24T21:05:00+00:00", "clock": "read", "by": None}


def test_a_voivodeship_with_an_all_clear_alone_shows_the_feeds_name(tmp_path: Path) -> None:
    """The recorded all-clear moved onto `slaskie`, named Śląskie by the feed,
    with no alert beside it: the row is still keyed on the slug and shows the
    name, which here only the all-clear can supply."""
    store = EventStore(tmp_path / "events")
    recorded, _alone = _recorded()
    clear = next(item for item in recorded if item.id == "23337898")
    moved = changed(clear, provinces=(rso.Province(slug="slaskie", name="Śląskie"),))
    t0 = datetime(2026, 9, 16, 5, 30, tzinfo=UTC)
    run(store, t0, [[moved]] * 4)
    [row] = value(store, t0 + timedelta(hours=1))["voivodeships"]
    assert (row["slug"], row["voivodeship"], row["alerts"]) == ("slaskie", "śląskie", [])


def test_the_newest_version_that_painted_is_the_one_shown(tmp_path: Path) -> None:
    """The recorded alert first dated 07:10 Warsaw, then 07:05 as recorded, and
    painting throughout: the line carries the `valid_from` it last painted
    with."""
    store = EventStore(tmp_path / "events")
    _recorded_page, alone = _recorded()
    alert = next(item for item in alone if item.id == "23337896")
    first = changed(alert, valid_from="2026-09-16 07:10:00")
    t0 = datetime(2026, 9, 16, 5, 15, tzinfo=UTC)
    run(store, t0, [[first]] * 3 + [[alert]] * 3)
    painted = alerts(value(store, t0 + timedelta(hours=1)))[("lubelskie", "23337896")]
    assert (painted["valid_from"], painted["ended"]) == ("2026-09-16T07:05:00+02:00", None)


def test_a_gap_that_opened_before_the_window_is_counted_from_its_start(
    tmp_path: Path,
) -> None:
    """Reads at 06:00 and 06:15, then 07:30: the window opening at 06:45 holds
    the gap from its own first instant, not from a read it does not contain.
    And a window that opens after the newest read is unread from its start."""
    store = EventStore(tmp_path / "events")
    t0 = datetime(2026, 9, 20, 6, 0, tzinfo=UTC)
    for moment in (t0, t0 + timedelta(minutes=15), t0 + timedelta(minutes=90)):
        serve(store, moment, [])
    summary = value(store, t0 + timedelta(hours=1, minutes=45), hours=1)
    assert summary["unread"] == [{"from": "2026-09-20T06:45:00+00:00",
                                  "to": "2026-09-20T07:30:00+00:00"}]
    later = value(store, t0 + timedelta(hours=4), hours=2)
    assert later["unread"] == [{"from": "2026-09-20T08:00:00+00:00", "to": None}]


def test_a_gap_that_closes_as_the_window_opens_is_not_in_it(tmp_path: Path) -> None:
    """Reads at 06:00, then from 06:45, the window's first instant, every 15
    minutes: the 45 minutes between the first two lie before the window, and
    the window holds no stretch of them, not even an empty one."""
    store = EventStore(tmp_path / "events")
    t0 = datetime(2026, 9, 20, 6, 0, tzinfo=UTC)
    for moment in [t0] + [t0 + timedelta(minutes=45 + 15 * step) for step in range(5)]:
        serve(store, moment, [])
    assert value(store, t0 + timedelta(hours=1, minutes=45), hours=1)["unread"] == []


def test_a_hole_wholly_before_the_window_is_not_one_of_its_stretches() -> None:
    """`holes` on its own, with reads the store would never hand it: the walk
    passes one read at or before the window's start and then only reads inside
    it, so a hole lying wholly before the window reaches this function only
    from another caller, and must not come back as a stretch of the window."""
    t = [datetime(2026, 9, 20, 5, 0, tzinfo=UTC) + timedelta(minutes=m) for m in (0, 60, 75, 90)]
    assert rcb_recent.holes(t, datetime(2026, 9, 20, 6, 10, tzinfo=UTC), t[-1]) == []


def test_an_alert_gone_at_the_instant_of_its_valid_to_was_withdrawn(
    tmp_path: Path, week: EventStore,
) -> None:
    """The composer calls a communique over only after its `valid_to`
    (`poland.is_expired`), so one missing from a read taken at that very
    instant left while it still stood. 23363073, valid until 23:59 Warsaw,
    absent from a read at 21:59:00 UTC exactly."""
    store = EventStore(tmp_path / "events")
    alert = recorded_row(week, "23363073")
    t0 = datetime(2026, 9, 24, 21, 14, tzinfo=UTC)
    run(store, t0, [[alert]] * 3 + [[]] * 2)
    summary = value(store, t0 + timedelta(hours=1))
    assert alerts(summary)[("podkarpackie", "23363073")]["ended"] == {
        "reason": "withdrawn", "at": "2026-09-24T21:59:00+00:00", "clock": "read", "by": None}


def test_an_alert_the_block_lost_sight_of_ends_unread_and_resumes(tmp_path: Path) -> None:
    """The alert alone, read for an hour; two hours refused, so past the
    ceiling the block says nothing; read again. Two painted stretches, the end
    of the first dated by the last read, and the stretch between the reads is
    the window's `unread`, not a quiet voivodeship."""
    store = EventStore(tmp_path / "events")
    _recorded_page, alone = _recorded()
    t0 = datetime(2026, 9, 16, 5, 6, tzinfo=UTC)
    run(store, t0, [None if 5 <= step < 13 else alone for step in range(20)])
    lost = "2026-09-16T07:06:00.000001+00:00"
    last_read = "2026-09-16T06:06:00+00:00"
    record = "2026-09-16T05:06:00+00:00"
    during = value(store, t0 + timedelta(hours=2, minutes=30))
    alert = alerts(during)[("lubelskie", "23337896")]
    assert alert["ended"] == {"reason": "unread", "at": last_read, "clock": "read", "by": None}
    assert during["unread"] == [{"from": "2026-09-14T07:36:00+00:00", "to": record},
                                {"from": last_read, "to": None}]
    after = value(store, t0 + timedelta(hours=4, minutes=45))
    alert = alerts(after)[("lubelskie", "23337896")]
    assert [(stretch["from"], stretch["to"]) for stretch in alert["painted"]] == [
        (record, lost), ("2026-09-16T08:21:00+00:00", None)]
    assert alert["ended"] is None
    assert after["unread"] == [{"from": "2026-09-14T09:51:00+00:00", "to": record},
                               {"from": last_read, "to": "2026-09-16T08:21:00+00:00"}]


def test_reads_further_apart_than_the_pipes_threshold_leave_a_stretch_unread(
    tmp_path: Path,
) -> None:
    """Reads every 15 minutes, then one 29 minutes after the last and one 31
    after that: only the second pair is further apart than the thirty minutes
    the pipe calls an outage, and the verdict, which keeps a list for an hour,
    never went `null` across either."""
    store = EventStore(tmp_path / "events")
    t0 = datetime(2026, 9, 20, 6, 0, tzinfo=UTC)
    times = [t0 + timedelta(minutes=15 * step) for step in range(4)]
    times += [times[-1] + timedelta(minutes=29)]
    times += [times[-1] + timedelta(minutes=31)]
    times += [times[-1] + timedelta(minutes=15 * step) for step in range(1, 4)]
    for moment in times:
        serve(store, moment, [])
    summary = value(store, times[-1], hours=3)
    assert summary["unread"] == [
        {"from": "2026-09-20T05:30:00+00:00", "to": "2026-09-20T06:00:00+00:00"},
        {"from": "2026-09-20T07:14:00+00:00", "to": "2026-09-20T07:45:00+00:00"}]
    assert rcb_recent.SILENCE_S == 1800.0


def test_a_list_naming_a_row_nobody_wrote_is_unread_though_the_reads_went_on(
    tmp_path: Path,
) -> None:
    """Reads every 15 minutes throughout, and for half an hour the list they
    recorded names a digest the store never held: the verdict says `null`
    there rather than a partial list, and so does the window."""
    store = EventStore(tmp_path / "events")
    _recorded_page, alone = _recorded()
    t0 = datetime(2026, 9, 16, 5, 6, tzinfo=UTC)
    for step in range(9):
        at = t0 + timedelta(minutes=15 * step)
        if step in (3, 4):
            store.record_snapshot(rso.FEED, poland.WARNINGS_URL, at, ["0" * 64])
            store.record_read(rso.FEED, poland.WARNINGS_URL, at, 1, 0)
        else:
            serve(store, at, alone)
    summary = value(store, t0 + timedelta(hours=2), hours=2)
    assert summary["unread"] == [{"from": "2026-09-16T05:51:00+00:00",
                                  "to": "2026-09-16T06:21:00+00:00"}]
    # Ended where the torn list arrived, and dated by the read before it: the
    # read at 05:51 recorded the torn list and did not see the alert.
    alert = alerts(summary)[("lubelskie", "23337896")]
    assert alert["ended"] is None
    assert [(one["from"], one["to"]) for one in alert["painted"]] == [
        ("2026-09-16T05:06:00+00:00", "2026-09-16T05:51:00+00:00"),
        ("2026-09-16T06:21:00+00:00", None)]
    during = value(store, t0 + timedelta(minutes=50), hours=2)
    assert alerts(during)[("lubelskie", "23337896")]["ended"] == {
        "reason": "unread", "at": "2026-09-16T05:36:00+00:00", "clock": "read", "by": None}


def test_the_list_at_a_moment_is_none_before_the_first_and_where_a_row_is_missing() -> None:
    """`Record.rows_at` on its own. The walk only asks it where the verdict
    published rows, so while the two read one store its `None` is never met
    there; it is held here so that a store changing under the walk reads as
    unread and not as an empty list."""
    t0 = datetime(2026, 9, 20, 6, 0, tzinfo=UTC)
    row = {"digest": "a" * 64, "source_id": "1", "fields": {}, "provinces": []}
    record = rcb_recent.Record(
        layer=RcbLayer(recorded_since=t0, spans=()),
        lists=((t0, ("a" * 64,)), (t0 + timedelta(minutes=15), ("a" * 64, "b" * 64))),
        held={"a" * 64: row},
        reads=(t0, t0 + timedelta(minutes=15)),
    )
    assert record.rows_at(t0 - timedelta(microseconds=1)) is None
    assert record.rows_at(t0) == (row,)
    assert record.rows_at(t0 + timedelta(minutes=14)) == (row,)
    assert record.rows_at(t0 + timedelta(minutes=15)) is None


def test_a_quiet_window_lists_no_voivodeship_and_says_where_its_record_starts(
    tmp_path: Path,
) -> None:
    store = EventStore(tmp_path / "events")
    first = datetime(2026, 9, 20, 6, 0, tzinfo=UTC)
    run(store, first, [[]] * (4 * 48 + 1))
    end = first + timedelta(hours=24)
    summary = value(store, end)
    assert summary["voivodeships"] == []
    assert summary["unread"] == [{"from": "2026-09-19T06:00:00+00:00",
                                  "to": "2026-09-20T06:00:00+00:00"}]
    assert value(store, first + timedelta(hours=48))["unread"] == [], (
        "a window the record covers from its first instant has nothing unread")


def test_before_the_first_poll_the_key_is_absent(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    assert rcb_recent.measure(store, END) == poland.UNPUBLISHED
    serve(store, END, [])
    assert rcb_recent.measure(store, END - timedelta(minutes=1)) == poland.UNPUBLISHED
    assert rcb_recent.measure(store, END).published


@pytest.mark.parametrize(("text", "instant"), [
    ("2026-09-24 06:59:33", "2026-09-24T04:59:33+00:00"),
    # The doubled autumn hour, as the feed writes it: no instant rather than a
    # guess, so an end falls back to the read that saw it.
    ("2026-10-25 02:30:00", None),
    ("not a stamp", None),
    (None, None),
    ("", None),
])
def test_a_feed_stamp_reads_as_the_reader_reads_it(text: str | None,
                                                    instant: str | None) -> None:
    found = rcb_recent.feed_instant(text)
    assert (None if found is None else found.isoformat()) == instant
    if text:
        try:
            reference: datetime | None = rso.to_utc(text, poland.ZONE)
        except rso.SourceUnavailable:
            reference = None
        assert found == reference


def test_stretches_join_where_they_touch_and_an_open_one_takes_the_rest() -> None:
    t = [datetime(2026, 9, 20, hour, tzinfo=UTC) for hour in range(8)]
    assert rcb_recent.merged([[t[3], t[4]], [t[0], t[1]], [t[1], t[2]]]) == [
        [t[0], t[2]], [t[3], t[4]]]
    assert rcb_recent.merged([[t[0], None], [t[2], t[3]]]) == [[t[0], None]]
    assert rcb_recent.merged([[t[0], t[5]], [t[1], t[2]]]) == [[t[0], t[5]]]
    assert rcb_recent.merged([[t[0], t[2]], [t[1], None]]) == [[t[0], None]]


# ---- the contract and the loop


def test_the_contract_carries_the_key_only_when_published() -> None:
    report = compose([], as_of=END)
    assert "pl_rcb_recent" not in to_contract(report)
    assert to_contract(replace(report, rcb_recent=Block(published=True, value=None)))[
        "pl_rcb_recent"] is None
    assert "pl_rcb_recent" not in to_contract(replace(report, rcb_recent=Block(published=False)))
    held = {"hours": 48, "voivodeships": []}
    assert to_contract(replace(report, rcb_recent=Block(published=True, value=held)))[
        "pl_rcb_recent"] == held


def _polled(tmp_path: Path) -> Path:
    """An hour of reads ending now, of the synthetic page `tests/test_poland.py`
    reviews: the loop runs on the wall clock, and every recorded alert is past
    its `valid_to` by now, while the page's two live threats never end."""
    from tests.test_poland import PAGE

    path = tmp_path / "events"
    store = EventStore(path)
    page = list(rso.parse_page(PAGE).communiques)
    now = datetime.now(UTC)
    for step in range(4):
        serve(store, now - timedelta(minutes=45 - 15 * step), page)
    return path


def test_the_report_loop_publishes_the_window_beside_the_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    path = _polled(tmp_path)
    state = tmp_path / "state.json"
    assert main(["report", "--store", str(path), "--json", str(state), "--watch",
                 "--interval", "0", "--max-cycles", "1"]) == 0
    payload = json.loads(state.read_text(encoding="utf-8"))
    recent = payload["pl_rcb_recent"]
    assert recent["hours"] == 48
    assert recent["end"][:19] == payload["generated_at"][:19]
    painted = {(row["slug"], item["id"])
               for row in payload["pl_warnings"] for item in row["communiques"]}
    still = {(row["slug"], alert["id"]) for row in recent["voivodeships"]
             for alert in row["alerts"] if alert["ended"] is None}
    assert still == painted == {("malopolskie", "1"), ("malopolskie", "3"),
                                ("podkarpackie", "3")}


def test_a_failure_to_summarise_nulls_the_key_and_nothing_else(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    path = _polled(tmp_path)

    def broken(_store: EventStore, _moment: datetime) -> Block:
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr("mavo.cli.measure_rcb_recent", broken)
    state = tmp_path / "state.json"
    assert main(["report", "--store", str(path), "--json", str(state), "--watch",
                 "--interval", "0", "--max-cycles", "1"]) == 0
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["pl_rcb_recent"] is None
    assert payload["pl_warnings"], "the live list must survive the two days"
    assert "[RCB-RECENT-FAILED] disk I/O error" in capsys.readouterr().err
