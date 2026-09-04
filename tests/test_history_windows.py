"""Three trailing windows from one fold, published on demand (D-048).

`trailing_counts` and `trailing_areas` were proved for one window. What this
file defends is the arrangement that puts three of them in one file: that the
week `state.json` shades by is the very tuple the history lists, that a
longer window sees what a shorter one aged out, that a window the store has
not observed in full says so, and that the third file rides the same cycle
as the other two. The fixtures are chosen so that a wrong implementation and
a right one disagree: an episode at day 20 tells 7 from 30, one at day 60
tells 30 from 90, and one open since day 100 tells a clipped span from an
unclipped one.
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.areas import AreaTable
from mavo.cli import parse_windows
from mavo.report import (
    DEFAULT_TRAILING_DAYS,
    HISTORY_WINDOWS_DAYS,
    Report,
    compose,
    publish,
    to_contract,
    to_feed,
    to_history,
    trailing_areas,
    trailing_counts,
    write_history,
)
from mavo.schema import AlertState, AreaRole, Provenance, ThreatEvent, ThreatKind

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
DAY = 24 * 60


@pytest.fixture
def table() -> AreaTable:
    return AreaTable.from_csv()


@pytest.fixture
def west(table: AreaTable) -> list:
    areas = [
        area
        for area in (table.resolve(tag) for tag in table.tags)
        if area is not None and area.is_western and area.border_lower_km is not None
    ]
    return sorted(areas, key=lambda a: (a.border_lower_km, a.border_upper_km))


def event(
    code: str,
    minutes_ago: float,
    state: AlertState = AlertState.ACTIVE,
    kind: ThreatKind = ThreatKind.DRONE,
) -> ThreatEvent:
    stamp = NOW - timedelta(minutes=minutes_ago)
    return ThreatEvent(
        area_id=code,
        state=state,
        ts_source=stamp,
        ts_ingest=stamp,
        source_id="history-windows-test",
        kind=kind,
        provenance=Provenance.REPORTED,
        role=AreaRole.SUBJECT,
    )


def episode(code: str, opened_days_ago: float, hours: float) -> list[ThreatEvent]:
    """One closed episode: active, then clear `hours` later."""
    opened = opened_days_ago * DAY
    return [
        event(code, opened),
        event(code, opened - hours * 60, AlertState.CLEAR),
    ]


@pytest.fixture
def quarter(west) -> list[ThreatEvent]:
    """Three areas, three ages. `a` had an episode 20 days ago and one 3 days
    ago; `b` one 60 days ago; `c` has been under alert since day 100 with no
    clear. Every window sees a different subset, and `c`'s span is clipped
    differently by each cutoff."""
    a, b, c = west[0], west[1], west[2]
    return (
        episode(a.code, 20, 2)
        + episode(a.code, 3, 1)
        + episode(b.code, 60, 3)
        + [event(c.code, 100 * DAY)]
    )


def by_days(report: Report) -> dict[int, object]:
    return {window.days: window for window in report.history}


def test_the_default_windows_are_seven_thirty_and_ninety(table, quarter) -> None:
    report = compose(quarter, as_of=NOW, table=table)
    assert tuple(window.days for window in report.history) == (7, 30, 90)
    assert HISTORY_WINDOWS_DAYS == (7, 30, 90)
    assert DEFAULT_TRAILING_DAYS in HISTORY_WINDOWS_DAYS


def test_a_longer_window_sees_what_a_shorter_one_aged_out(table, west, quarter) -> None:
    """The reason there are three: the episode at day 20 is in the month and
    not the week, the one at day 60 is in the quarter and not the month."""
    a, b, c = west[0], west[1], west[2]
    windows = by_days(compose(quarter, as_of=NOW, table=table))
    week = {e.code: e.episodes for e in windows[7].areas}
    month = {e.code: e.episodes for e in windows[30].areas}
    quarter_ = {e.code: e.episodes for e in windows[90].areas}
    assert week == {a.code: 1, c.code: 1}, week
    assert month == {a.code: 2, c.code: 1}, month
    assert quarter_ == {a.code: 2, b.code: 1, c.code: 1}, quarter_


def test_an_open_episode_is_clipped_to_each_window(table, west, quarter) -> None:
    """`c` has been under alert for 100 days. Its span inside each window is
    the window, no more, and it is open in all three: an unclipped span
    would report a fortnight of alert inside a week."""
    c = west[2]
    windows = by_days(compose(quarter, as_of=NOW, table=table))
    for days in (7, 30, 90):
        entry = next(e for e in windows[days].areas if e.code == c.code)
        assert entry.alert_seconds == days * 86400, (days, entry.alert_seconds)
        assert entry.open_at_as_of is True


def test_the_week_in_the_history_is_the_week_the_map_shades_by(table, quarter) -> None:
    """One fold. `recent` and `recent_areas` are the seven-day window's own
    tuples, not a recomputation that happens to agree today."""
    report = compose(quarter, as_of=NOW, table=table)
    week = by_days(report)[7]
    assert report.recent is week.oblasts
    assert report.recent_areas is week.areas
    assert report.trailing_days == week.days


def test_each_window_agrees_with_the_single_window_fold(table, quarter) -> None:
    """The history is `trailing_counts` and `trailing_areas` applied at each
    length, and nothing else. Any divergence here is a second arithmetic."""
    report = compose(quarter, as_of=NOW, table=table)
    for window in report.history:
        assert window.oblasts == trailing_counts(
            quarter, as_of=NOW, days=window.days, table=table)
        assert window.areas == trailing_areas(
            quarter, as_of=NOW, days=window.days, table=table)
        assert window.start == NOW - timedelta(days=window.days)


def test_a_window_the_log_does_not_reach_says_so(table, west) -> None:
    """The store here is three weeks old. The week and nothing else is fully
    observed; the month and the quarter carry the oldest stamp and a false
    flag, so a consumer cannot render the unobserved part as calm."""
    a = west[0]
    report = compose(episode(a.code, 21, 1), as_of=NOW, table=table)
    windows = by_days(report)
    oldest = NOW - timedelta(days=21)
    assert windows[7].log_reaches_start is True
    assert windows[30].log_reaches_start is False
    assert windows[90].log_reaches_start is False
    for window in report.history:
        assert window.oldest_observation == oldest


def test_an_event_on_the_window_boundary_counts_as_reached(table, west) -> None:
    """The log reaches a window whose start it touches. `<` here would call
    a store exactly as old as the window partial, and the flag has to be
    exact in both directions to be worth reading."""
    a = west[0]
    report = compose([event(a.code, 7 * DAY)], as_of=NOW, table=table)
    windows = by_days(report)
    assert windows[7].start == windows[7].oldest_observation
    assert windows[7].log_reaches_start is True
    assert windows[30].log_reaches_start is False


def test_an_empty_log_reaches_no_window(table) -> None:
    report = compose([], as_of=NOW, table=table)
    for window in report.history:
        assert window.oldest_observation is None
        assert window.log_reaches_start is False
        assert window.oblasts == () and window.areas == ()


def test_the_oldest_stamp_is_the_raw_one_not_the_skew_filtered_one(table, west) -> None:
    """A stamp in the future is excluded from the freshness question (F120)
    and not from this one: the oldest event decides how far back the log
    reaches, and the future is never the oldest."""
    a = west[0]
    events = [event(a.code, -600), event(a.code, 8 * DAY)]  # +10 min, 8 days ago
    report = compose(events, as_of=NOW, table=table)
    assert by_days(report)[7].oldest_observation == NOW - timedelta(days=8)


def test_history_days_must_contain_the_week(table) -> None:
    with pytest.raises(ValueError, match="must contain trailing_days"):
        compose([], as_of=NOW, table=table, history_days=(30, 90))
    with pytest.raises(ValueError, match="positive"):
        compose([], as_of=NOW, table=table, history_days=(0, 7))


def test_the_payload_carries_every_window_labelled(table, west, quarter) -> None:
    report = compose(quarter, as_of=NOW, table=table)
    payload = to_history(report)
    assert payload["v"] == to_contract(report)["v"]
    assert payload["generated_at"] == to_contract(report)["generated_at"]
    windows = payload["windows"]
    assert [w["days"] for w in windows] == [7, 30, 90]
    for block in windows:
        assert set(block) == {
            "days", "window_start", "log_oldest_at",
            "log_reaches_window_start", "oblasts", "areas",
        }
        assert block["window_start"] == (
            NOW - timedelta(days=block["days"])).isoformat(timespec="seconds")
        assert block["log_oldest_at"] == (
            NOW - timedelta(days=100)).isoformat(timespec="seconds")
    assert [w["log_reaches_window_start"] for w in windows] == [True, True, True]


def test_the_seven_day_blocks_are_byte_for_byte_the_other_files(table, quarter) -> None:
    """`recent_7d` in state.json, `recent_7d_areas` in feed.json and the
    seven-day window in history.json are one serialisation each. A consumer
    reading the week from any of the three reads the same rows."""
    report = compose(quarter, as_of=NOW, table=table)
    week = next(w for w in to_history(report)["windows"] if w["days"] == 7)
    assert week["oblasts"] == to_contract(report)["recent_7d"]
    assert week["areas"] == to_feed(report)["recent_7d_areas"]


def test_write_history_is_atomic_and_every_cycle(table, quarter) -> None:
    report = compose(quarter, as_of=NOW, table=table)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "deep" / "history.json"
        written = write_history(report, path)
        assert written == path
        assert json.loads(path.read_text(encoding="utf-8")) == to_history(report)
        leftovers = [p.name for p in path.parent.iterdir() if p.name != "history.json"]
        assert leftovers == [], leftovers


def test_publish_writes_the_third_file_beside_the_other_two(table, quarter) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        outcome = publish(
            lambda: quarter, root / "state.json", interval_s=0.0, max_cycles=2,
            table=table, sleep=lambda _s: None, now=lambda: NOW,
            feed_path=root / "feed.json", history_path=root / "history.json",
            history_days=(7, 30),
        )
        assert outcome.written == 2
        history = json.loads((root / "history.json").read_text(encoding="utf-8"))
        assert [w["days"] for w in history["windows"]] == [7, 30]
        state = json.loads((root / "state.json").read_text(encoding="utf-8"))
        assert history["generated_at"] == state["generated_at"]


def test_publish_without_a_history_path_writes_none(table, quarter) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        publish(lambda: quarter, root / "state.json", interval_s=0.0,
                max_cycles=1, table=table, sleep=lambda _s: None,
                now=lambda: NOW)
        assert sorted(p.name for p in root.iterdir()) == ["state.json"]


@pytest.mark.parametrize("spec", ["7,30,90", "90,7,30", "7", "7,14"])
def test_parse_windows_accepts_a_set_holding_the_week(spec: str) -> None:
    parsed = parse_windows(spec)
    assert parsed == tuple(sorted(int(p) for p in spec.split(",")))
    assert 7 in parsed


@pytest.mark.parametrize(("spec", "reason"), [
    ("30,90", "must include 7"),
    ("7,7,30", "listed twice"),
    ("0,7", "at least one day"),
    ("7,thirty", "not a comma-separated list"),
    ("", "not a comma-separated list"),
])
def test_parse_windows_refuses_what_would_become_a_wrong_file(spec: str, reason: str) -> None:
    with pytest.raises(ValueError, match=reason):
        parse_windows(spec)
