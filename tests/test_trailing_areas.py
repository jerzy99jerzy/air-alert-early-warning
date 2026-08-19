"""The trailing window at raion granularity (0.33.0.0).

`trailing_areas` restates three invariants `trailing_counts` already holds one
level up. Restated code needs restated regressions: a fold keyed on the area
does not inherit a guarantee proved about a fold keyed on the oblast, and this
project has already shipped one counter that was right for one raion and wrong
for seven (F76).

Each test below names the invariant it defends. A test whose failure message
does not say what broke is a test that has to be re-derived every time it goes
red.
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.areas import AreaTable
from mavo.report import (
    compose,
    to_contract,
    to_feed,
    trailing_areas,
    write_contract,
    write_feed,
)
from mavo.schema import AlertState, AreaRole, Provenance, ThreatEvent, ThreatKind

NOW = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)


@pytest.fixture
def table() -> AreaTable:
    return AreaTable.from_csv()


@pytest.fixture
def west(table: AreaTable) -> list:
    """Western areas with a distance, nearest first. The list this tool exists for."""
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
) -> ThreatEvent:
    stamp = NOW - timedelta(minutes=minutes_ago)
    return ThreatEvent(
        area_id=code,
        state=state,
        ts_source=stamp,
        ts_ingest=stamp,
        source_id="trailing-areas-test",
        kind=ThreatKind.DRONE,
        provenance=Provenance.REPORTED,
        role=AreaRole.SUBJECT,
    )


def test_an_episode_opened_before_the_window_is_counted_once(table, west) -> None:
    """F85, one level down. A filter on events would age out the opening."""
    subject = west[0]
    found = trailing_areas(
        [event(subject.code, 60 * 24 * 9)], as_of=NOW, table=table
    )
    assert [e.code for e in found] == [subject.code]
    assert found[0].episodes == 1, (
        "an alert running since before the window vanished from the count; the "
        "most persistently attacked area would render as the quietest"
    )
    # The opening time, not the cutoff. Reporting the cutoff would invent a
    # transition that never happened.
    assert found[0].last_active_at == NOW - timedelta(days=9)


def test_an_episode_closed_before_the_window_is_outside_it(table, west) -> None:
    subject = west[0]
    found = trailing_areas(
        [
            event(subject.code, 60 * 24 * 9),
            event(subject.code, 60 * 24 * 8, AlertState.CLEAR),
        ],
        as_of=NOW,
        table=table,
    )
    assert found == (), "an episode both opened and closed before the window counted"


def test_unknown_does_not_close_an_episode(table, west) -> None:
    """Silence is not an all-clear. The invariant the whole project rests on."""
    subject = west[0]
    found = trailing_areas(
        [
            event(subject.code, 300),
            event(subject.code, 250, AlertState.UNKNOWN),
            event(subject.code, 200),
        ],
        as_of=NOW,
        table=table,
    )
    assert found[0].episodes == 1, (
        "UNKNOWN closed an episode and the next ACTIVE opened a second one; a "
        "source that stopped talking was read as saying the alert ended"
    )
    assert found[0].last_ended_at is None


def test_partial_clear_does_not_close_an_episode(table, west) -> None:
    """The fourth state. `is_clear` is a function precisely so this cannot slip."""
    subject = west[0]
    found = trailing_areas(
        [
            event(subject.code, 300),
            event(subject.code, 250, AlertState.PARTIAL_CLEAR),
        ],
        as_of=NOW,
        table=table,
    )
    assert found[0].episodes == 1
    assert found[0].last_ended_at is None


def test_two_closed_stretches_are_two_episodes(table, west) -> None:
    subject = west[0]
    found = trailing_areas(
        [
            event(subject.code, 500),
            event(subject.code, 400, AlertState.CLEAR),
            event(subject.code, 200),
            event(subject.code, 100, AlertState.CLEAR),
        ],
        as_of=NOW,
        table=table,
    )
    assert found[0].episodes == 2
    assert found[0].last_ended_at == NOW - timedelta(minutes=100)
    assert found[0].last_active_at == NOW - timedelta(minutes=200)


def test_an_unresolvable_area_is_dropped_and_not_folded(table, west) -> None:
    """No code, no distance, no oblast. Attaching it to a neighbour is worse."""
    found = trailing_areas(
        [event("UA00000000000000000", 100), event(west[0].code, 100)],
        as_of=NOW,
        table=table,
    )
    assert [e.code for e in found] == [west[0].code]


def test_the_block_is_ordered_nearest_first(table, west) -> None:
    events = [event(area.code, 100) for area in (west[5], west[0], west[3])]
    found = trailing_areas(events, as_of=NOW, table=table)
    lower = [e.border_lower_km for e in found]
    assert lower == sorted(lower), "the block was not ordered by the lower bound"


def _partial_distance_table(tmp_path: Path, keep: list) -> AreaTable:
    """A table where **some** areas have a distance and some do not.

    A table with no distances at all cannot test an ordering: there is nothing
    for the unknown to sort against, so the assertion passes whichever way the
    comparison goes. That fixture was written first and a mutant moving unknown
    to the front of the order survived it. Logged rather than quietly fixed:
    this is the same shape as the fixtures that hid F76 and the null branch in
    `contract_check`, and the count of times it has happened is the point.
    """
    path = tmp_path / "partial_border_km.csv"
    lines = ["tag,katottg_code,centre_km,radius_km,lower_km,upper_km"]
    for area in keep:
        lines.append(
            f"{area.tag},{area.code},{area.border_centre_km},0.0,"
            f"{area.border_lower_km},{area.border_upper_km}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return AreaTable.from_csv(distance_path=path)


def test_an_area_without_a_distance_sorts_last_not_first(
    tmp_path: Path, table: AreaTable, west: list
) -> None:
    """Unknown must never read as near. The one ordering that matters here.

    The near area keeps its distance and the far one loses it, so a comparison
    that puts unknown first would also put it *before* a genuinely nearer
    place. Both orderings are observable and they disagree, which is what
    makes this a test rather than a restatement.
    """
    near, far = west[0], west[-1]
    mixed = _partial_distance_table(tmp_path, [near])
    found = trailing_areas(
        [event(near.code, 100), event(far.code, 100)], as_of=NOW, table=mixed
    )
    assert [entry.code for entry in found] == [near.code, far.code], (
        "an area with no distance sorted ahead of a measured one; unknown "
        "would have rendered as nearer than a place 0 km from the border"
    )
    assert found[0].border_lower_km is not None
    assert found[1].border_lower_km is None


def test_nearest_recent_skips_areas_with_no_distance(
    tmp_path: Path, table: AreaTable, west: list
) -> None:
    """The reduction reads past an unknown rather than reporting it as near."""
    near, far = west[0], west[-1]
    mixed = _partial_distance_table(tmp_path, [near])
    report = compose(
        [event(far.code, 100), event(near.code, 100)], as_of=NOW, table=mixed
    )
    assert report.nearest_recent is not None
    assert report.nearest_recent.code == near.code
    assert to_contract(report)["nearest_7d"]["katottg"] == near.code


def test_nearest_recent_is_none_when_nothing_has_a_distance(
    tmp_path: Path, west: list
) -> None:
    bare = _partial_distance_table(tmp_path, [])
    report = compose([event(west[0].code, 100)], as_of=NOW, table=bare)
    assert report.recent_areas != ()
    assert report.nearest_recent is None, (
        "an area with no distance was offered as the nearest; unknown would "
        "have rendered as a number in the page headline"
    )
    assert to_contract(report)["nearest_7d"] is None


def test_the_oblast_block_carries_no_distance(table, west) -> None:
    """The granularity split, asserted where it would be undone.

    An oblast interval takes its lower bound from one raion and its upper from
    another, so it describes no single place while wearing the field names of
    the per-area interval that describes exactly one.
    """
    report = compose([event(west[0].code, 100)], as_of=NOW, table=table)
    for entry in to_contract(report)["recent_7d"]:
        assert not any("border" in key for key in entry), (
            f"the oblast block grew a distance field: {sorted(entry)}"
        )


def test_summing_episodes_does_not_reproduce_the_oblast_count(table) -> None:
    """F76, stated as an assertion instead of a paragraph.

    One western episode lights every raion of an oblast at once. Summing the
    per-area counts measures how finely the oblast is subdivided, not how often
    it was attacked, and the two must not be interchangeable.
    """
    lviv = [
        area
        for area in (table.resolve(tag) for tag in table.tags)
        if area is not None and area.oblast == "Львівська"
    ]
    assert len(lviv) >= 3, "fixture needs an oblast with several raions"
    report = compose(
        [event(area.code, 100) for area in lviv], as_of=NOW, table=table
    )
    payload = to_contract(report)
    oblast = next(e for e in payload["recent_7d"] if e["oblast"] == "lviv")
    per_area = sum(
        e.episodes for e in report.recent_areas if e.oblast_slug == "lviv"
    )
    assert oblast["alerts_count"] == 1
    assert per_area == len(lviv)
    assert per_area != oblast["alerts_count"], (
        "the two counts agreed on a fixture built to separate them; the "
        "regression can no longer see F76"
    )


def test_the_two_blocks_share_no_key_space(table, west) -> None:
    report = compose([event(west[0].code, 100)], as_of=NOW, table=table)
    payload = to_contract(report)
    slugs = {entry["oblast"] for entry in payload["recent_7d"]}
    codes = {area["area_id"] for area in payload["areas"]}
    assert not (slugs & codes)


def test_the_feed_carries_the_block_and_the_state_carries_the_reduction(
    table, west
) -> None:
    report = compose([event(west[0].code, 100)], as_of=NOW, table=table)
    with tempfile.TemporaryDirectory() as directory:
        state = json.loads(
            write_contract(report, Path(directory) / "state.json").read_text(
                encoding="utf-8"
            )
        )
        feed = json.loads(
            write_feed(report, Path(directory) / "feed.json").read_text(
                encoding="utf-8"
            )
        )
    # The bulk travels in the file a reader fetches on demand, not in the one
    # polled every thirty seconds.
    assert "recent_7d_areas" not in state
    assert "recent_7d_areas" in feed
    assert state["nearest_7d"]["katottg"] == west[0].code
    assert feed["recent_7d_areas"][0]["katottg"] == west[0].code
    assert feed["window_days"] == report.trailing_days


def test_both_files_describe_one_window(table, west) -> None:
    """One composition. Two would be two weeks, and no way to tell which."""
    report = compose([event(west[0].code, 100)], as_of=NOW, table=table)
    state = to_contract(report)
    feed = to_feed(report)
    assert state["generated_at"] == feed["generated_at"]
    assert state["nearest_7d"]["katottg"] == feed["recent_7d_areas"][0]["katottg"]


def test_a_quiet_week_says_so_rather_than_going_missing(table) -> None:
    """Empty is an answer and has to look like one, in both files."""
    report = compose([], as_of=NOW, table=table)
    assert to_feed(report)["recent_7d_areas"] == []
    assert to_contract(report)["nearest_7d"] is None


def test_the_item_carries_every_field_a_consumer_reads(table, west) -> None:
    found = trailing_areas([event(west[0].code, 100)], as_of=NOW, table=table)
    item = found[0].as_item()
    assert set(item) == {
        "katottg", "area_name", "oblast", "oblast_name", "episodes",
        "last_active_at", "last_ended_at", "border_km_lower",
        "border_km_upper", "west",
    }
    assert item["episodes"] >= 1
    assert "alerts_count" not in item, (
        "the per-area count took the oblast block's field name; a consumer "
        "reaching for the familiar key would sum it into the F76 number"
    )
