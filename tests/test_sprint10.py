"""S8 regressions: the report, and the honesty rules it must not lose.

`docs/MVP.md` numbers this sprint S8; the regression files are numbered by
shipped sprint, which is why this is sprint 10 on disk. The mapping is stated
here rather than left to be worked out from two sequences that diverged at
0.9.0.0.

Every test below is an invariant the product would be worthless without. Each
was verified red on a scratch copy carrying the mutation named in its
docstring.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mavo.areas import AreaTable
from mavo.report import (
    DEFAULT_VALID_FOR_S,
    FeedState,
    compose,
    render_text,
    to_contract,
    write_contract,
)
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind

NOW = datetime(2026, 8, 10, 23, 41, tzinfo=UTC)
SAMBIR = "UA46080000000017237"   # Sambirskyi raion, touches the border
YAVORIV = "UA46140000000036328"  # Yavorivskyi raion
KHARKIV = "UA63120270000028556"  # front-line, 850+ km away
# The pair that separates the two sortings: Sarnenskyi's nearest edge is closer
# (162.2 against 162.9) while its centre is further (206.7 against 202.9). Any
# ordering that reads the centre puts them the wrong way round, and the wrong
# way round is the direction that hides the nearer area.
SARNY = "UA56080000000096146"
CHORTKIV = "UA61060000000068766"


def _event(
    area_id: str,
    state: AlertState,
    minutes_ago: int,
    kind: ThreatKind = ThreatKind.UNKNOWN,
) -> ThreatEvent:
    ts = NOW - timedelta(minutes=minutes_ago)
    return ThreatEvent(
        area_id=area_id,
        state=state,
        ts_source=ts,
        ts_ingest=ts,
        source_id="test",
        kind=kind,
        provenance=Provenance.REPORTED,
    )


def _table() -> AreaTable:
    return AreaTable.from_csv()


def test_an_empty_store_reports_blind_and_not_calm() -> None:
    """The founding invariant, at the last layer before a reader.

    Mutation: return FeedState.OK when there is no observation. A report that
    renders an empty active list without saying it is blind has told a person
    the sky is clear on the strength of a dead pipeline.
    """
    report = compose([], as_of=NOW, table=_table())
    assert report.feed_state is FeedState.BLIND
    assert report.staleness_s is None, "no observation must be unknown, never 0"
    rendered = render_text(report)
    assert "BLIND" in rendered
    assert "not an all-clear" in rendered


def test_a_stale_observation_is_degraded_rather_than_current() -> None:
    """Mutation: compare against >= instead of >, or drop the comparison."""
    fresh = compose([_event(SAMBIR, AlertState.ACTIVE, 1)], as_of=NOW, table=_table())
    assert fresh.feed_state is FeedState.OK
    stale = compose(
        [_event(SAMBIR, AlertState.ACTIVE, 60)], as_of=NOW, table=_table()
    )
    assert stale.staleness_s == 3600
    assert stale.feed_state is FeedState.DEGRADED
    assert "DEGRADED" in render_text(stale)


def test_an_all_clear_removes_an_area_and_an_unknown_does_not() -> None:
    """The asymmetry is the contract, and it is not symmetrical by accident.

    Mutation: drop UNKNOWN alongside CLEAR in the fold. Both are "not active",
    and treating them alike loses the difference between a source that said
    the alert ended and a source that said nothing.
    """
    events = [
        _event(SAMBIR, AlertState.ACTIVE, 30),
        _event(SAMBIR, AlertState.CLEAR, 5),
        _event(YAVORIV, AlertState.ACTIVE, 30),
        _event(YAVORIV, AlertState.UNKNOWN, 5),
    ]
    report = compose(events, as_of=NOW, table=_table())
    listed = {p.area_id for p in report.areas}
    assert SAMBIR not in listed, "an affirmative all-clear must leave the list"
    assert YAVORIV in listed, "an unknown must stay on the list and say so"
    assert report.unknown_areas[0].state is AlertState.UNKNOWN


def test_the_latest_observation_wins_per_area() -> None:
    """Mutation: keep the first event per area instead of the last."""
    events = [
        _event(SAMBIR, AlertState.CLEAR, 30),
        _event(SAMBIR, AlertState.ACTIVE, 2),
    ]
    report = compose(events, as_of=NOW, table=_table())
    assert [p.state for p in report.areas] == [AlertState.ACTIVE]


def test_western_areas_sort_by_the_lower_bound_and_unknown_sorts_last() -> None:
    """Nearest-first, and an unknown distance must not read as nearest.

    Mutation: sort by `border_centre_km`, or let None sort first. The areas a
    centre sort is most wrong about are the ones that touch the border, which
    are the ones this project exists to watch.
    """
    events = [
        _event(YAVORIV, AlertState.ACTIVE, 1),
        _event(SAMBIR, AlertState.ACTIVE, 1),
        _event("UA00000000000000000", AlertState.ACTIVE, 1),  # not in the map
    ]
    report = compose(events, as_of=NOW, table=_table())
    order = [p.area_id for p in report.western_active]
    assert order[0] == SAMBIR, "the area touching the border must come first"
    assert "UA00000000000000000" not in order, "an unmapped area is not western"
    assert "UA00000000000000000" in report.unresolved_areas, (
        "an unmapped area must be reported, not dropped"
    )


def test_the_sort_reads_the_nearest_edge_and_not_the_centre() -> None:
    """The two orderings disagree, and only one of them is about the border.

    Sarnenskyi's nearest edge is 162.2 km out and its centre 206.7; Chortkivskyi
    is 162.9 and 202.9. A centre sort therefore puts Chortkivskyi first and
    hides the area that is actually closer. Mutation: sort by
    `border_centre_km`. The first version of this test used a pair the two
    sortings agreed on, so the mutation passed it - which is why the pair here
    was picked by searching the table for an inversion rather than by intuition.
    """
    events = [
        _event(CHORTKIV, AlertState.ACTIVE, 1),
        _event(SARNY, AlertState.ACTIVE, 1),
    ]
    report = compose(events, as_of=NOW, table=_table())
    assert [p.area_id for p in report.western_active] == [SARNY, CHORTKIV]


def test_a_blind_report_is_still_written_to_disk(tmp_path: Path) -> None:
    """The heartbeat has to survive the case that makes it matter.

    Mutation: return early from `write_contract` when there are no areas. A
    consumer polling a file that stopped being written cannot tell a dead
    producer from a quiet night, and the quiet night is the reading it will
    take. The earlier version of this test checked the payload rather than the
    file, so the mutation passed it.
    """
    target = tmp_path / "state.json"
    write_contract(compose([], as_of=NOW, table=_table()), target)
    assert target.exists(), "a blind report must still produce a file"
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["state"] == "blind"
    assert payload["observation_age_s"] is None


def test_a_front_line_area_is_not_counted_as_western() -> None:
    """The 96.5% is noise for a Polish reader and must not be in the western list."""
    report = compose([_event(KHARKIV, AlertState.ACTIVE, 1)], as_of=NOW, table=_table())
    assert report.western_active == ()
    assert len(report.active) == 1
    assert "active elsewhere: 1" in render_text(report)


def test_an_unmapped_area_prints_unknown_rather_than_a_blank() -> None:
    """Mutation: fall back to "" for oblast or 0 for distance."""
    report = compose(
        [_event("UA00000000000000000", AlertState.ACTIVE, 1)], as_of=NOW, table=_table()
    )
    picture = report.areas[0]
    assert picture.oblast == "unknown"
    assert picture.border_interval == "unknown"


def test_zero_western_alerts_is_printed_as_a_report_not_an_all_clear() -> None:
    """A quiet picture from a live feed still is not a promise of safety."""
    rendered = render_text(
        compose([_event(KHARKIV, AlertState.ACTIVE, 1)], as_of=NOW, table=_table())
    )
    assert "active in the west: 0 reported" in rendered
    assert "Absence of a report is not an all-clear." in rendered


def test_the_report_states_what_it_does_not_do() -> None:
    """The non-claim travels with the output, not only with the README."""
    assert "does not predict a crossing" in render_text(
        compose([], as_of=NOW, table=_table())
    )


def test_the_contract_carries_its_schema_version_and_heartbeat() -> None:
    """FEED-SPEC properties four and five, applied to this project's own feed."""
    payload = to_contract(
        compose([_event(SAMBIR, AlertState.ACTIVE, 1, ThreatKind.MISSILE)],
                as_of=NOW, table=_table())
    )
    assert payload["v"] == 1
    assert payload["generated_at"] == NOW.isoformat(timespec="seconds")
    assert payload["valid_for_s"] == DEFAULT_VALID_FOR_S
    assert payload["state"] == "ok"
    area = payload["areas"][0]
    assert area["katottg"] == SAMBIR
    assert area["kind"] == "missile"
    assert area["border_km_lower"] == 0.0
    assert area["alert"] == "active"


def test_the_contract_writes_a_blind_state_rather_than_no_file() -> None:
    """A pipeline that cannot see must still publish, saying it cannot see.

    Mutation: skip the write when there is nothing to report. A consumer
    polling a file that stopped being written cannot distinguish a dead
    producer from a quiet night, which is the failure `docs/FEED-SPEC.md`
    section 4 spends a section on.
    """
    payload = to_contract(compose([], as_of=NOW, table=_table()))
    assert payload["state"] == "blind"
    assert payload["areas"] == []
    assert payload["observation_age_s"] is None, "age must be null, never 0"


def test_writing_the_contract_is_atomic_and_leaves_no_partial_file(
    tmp_path: Path,
) -> None:
    """Mutation: write in place. A consumer must never read half a file."""
    target = tmp_path / "nested" / "state.json"
    report = compose([_event(SAMBIR, AlertState.ACTIVE, 1)], as_of=NOW, table=_table())
    write_contract(report, target)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["v"] == 1
    leftovers = [p.name for p in target.parent.iterdir() if p.name != "state.json"]
    assert leftovers == [], f"temporary files survived the write: {leftovers}"


def test_rewriting_the_contract_replaces_it_without_a_gap(tmp_path: Path) -> None:
    """The heartbeat: written every cycle, changed or not."""
    target = tmp_path / "state.json"
    first = compose([_event(SAMBIR, AlertState.ACTIVE, 5)], as_of=NOW, table=_table())
    write_contract(first, target)
    later = compose(
        [_event(SAMBIR, AlertState.ACTIVE, 5)],
        as_of=NOW + timedelta(seconds=60),
        table=_table(),
    )
    write_contract(later, target)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["generated_at"] != first.as_of.isoformat(timespec="seconds")
    assert payload["state"] == "ok"


def test_the_area_table_resolves_a_register_code(tmp_path: Path) -> None:
    """The lookup direction a stored event needs, added for this sprint."""
    table = _table()
    area = table.by_code(SAMBIR)
    assert area is not None
    assert area.is_western
    assert table.by_code("nonsense") is None


def test_the_nearest_distance_is_a_lower_bound_or_unknown() -> None:
    """A headline number that must not exist when it cannot be computed."""
    empty = compose([], as_of=NOW, table=_table())
    assert empty.nearest_km is None, "no active area means unknown, not zero"
    report = compose(
        [_event(SARNY, AlertState.ACTIVE, 1), _event(CHORTKIV, AlertState.ACTIVE, 1)],
        as_of=NOW,
        table=_table(),
    )
    assert report.nearest_km == 162.2


def test_an_unresolved_area_is_named_in_the_rendered_report() -> None:
    """Counted and printed. The alternative is a silently shorter list."""
    rendered = render_text(
        compose(
            [_event("UA00000000000000000", AlertState.ACTIVE, 1)],
            as_of=NOW,
            table=_table(),
        )
    )
    assert "unresolved by the map: 1" in rendered


def test_a_failed_write_leaves_no_temporary_file_behind(tmp_path: Path) -> None:
    """Mutation: drop the cleanup in the except branch.

    A crash mid-write must not leave a `.state-*.tmp` beside the real file:
    the next reader of that directory would find two files where the contract
    says one, and the stale one has no timestamp saying it is stale.
    """
    import mavo.report as report_module

    target = tmp_path / "state.json"
    report = compose([_event(SAMBIR, AlertState.ACTIVE, 1)], as_of=NOW, table=_table())
    original = report_module.os.replace

    def explode(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    report_module.os.replace = explode  # type: ignore[assignment]
    try:
        raised = False
        try:
            write_contract(report, target)
        except OSError:
            raised = True
        assert raised, "a failed write must not be swallowed"
    finally:
        report_module.os.replace = original  # type: ignore[assignment]
    assert list(tmp_path.iterdir()) == [], "a temporary file survived a failed write"


def test_the_command_exits_with_the_feed_state(tmp_path: Path) -> None:
    """The exit code is the part a cron wrapper reads, so it carries blindness.

    Mutation: return 0 regardless of feed state. A wrapper that only checks the
    status would then treat a dead pipeline as a healthy quiet one, which is
    the failure this whole module is arranged against.
    """
    from mavo.cli import main
    from mavo.store import EventStore

    store_path = tmp_path / "events"
    assert main(["report", "--store", str(store_path)]) == 6, "empty store is blind"

    store = EventStore(store_path)
    store.append([_event(SAMBIR, AlertState.ACTIVE, 10_000)])
    assert main(["report", "--store", str(store_path)]) == 5, "old observation is degraded"

    fresh = tmp_path / "fresh"
    EventStore(fresh).append(
        [
            ThreatEvent(
                area_id=SAMBIR,
                state=AlertState.ACTIVE,
                ts_source=datetime.now(UTC),
                ts_ingest=datetime.now(UTC),
                source_id="test",
                kind=ThreatKind.MISSILE,
                provenance=Provenance.REPORTED,
            )
        ]
    )
    out = tmp_path / "state.json"
    assert main(["report", "--store", str(fresh), "--json", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["state"] == "ok"


def test_the_loop_publishes_blindness_rather_than_skipping_a_cycle(
    tmp_path: Path,
) -> None:
    """The heartbeat's whole point, at the layer where it is easiest to lose.

    Mutation: `continue` instead of composing a blind report when the store
    cannot be read. A consumer polling a file that stopped being refreshed
    reads the last good picture and its own clock, and on a short outage that
    looks exactly like a quiet night.
    """
    from mavo.report import publish

    target = tmp_path / "state.json"
    calls = {"n": 0}

    def broken_store() -> list[ThreatEvent]:
        calls["n"] += 1
        raise OSError("store is gone")

    outcome = publish(
        broken_store, target, interval_s=0, max_cycles=3, table=_table(),
        sleep=lambda _s: None, on_cycle=lambda _r: None,
    )
    assert calls["n"] == 3
    assert outcome.cycles == 3
    assert outcome.written == 3, "a blind cycle must still write"
    assert outcome.blind_cycles == 3
    assert json.loads(target.read_text(encoding="utf-8"))["state"] == "blind"


def test_the_loop_names_why_it_stopped(tmp_path: Path) -> None:
    """A loop that ends without a reason has told its operator nothing (F46)."""
    from mavo.report import publish

    outcome = publish(
        lambda: [_event(SAMBIR, AlertState.ACTIVE, 1)],
        tmp_path / "state.json",
        interval_s=0,
        max_cycles=2,
        table=_table(),
        sleep=lambda _s: None,
    )
    assert outcome.reason == "reached max_cycles=2"
    assert "cycles=2" in outcome.line()
    assert "blind=0" in outcome.line()


def test_a_failed_write_stops_the_loop_and_says_so(tmp_path: Path) -> None:
    """Mutation: swallow the OSError and keep looping.

    A loop that cannot write is not publishing, and continuing quietly would
    make the process look healthy while the file ages.
    """
    import mavo.report as report_module
    from mavo.report import publish

    original = report_module.os.replace

    def explode(*args: object, **kwargs: object) -> None:
        raise OSError("read-only filesystem")

    report_module.os.replace = explode  # type: ignore[assignment]
    try:
        outcome = publish(
            lambda: [_event(SAMBIR, AlertState.ACTIVE, 1)],
            tmp_path / "state.json",
            interval_s=0,
            max_cycles=5,
            table=_table(),
            sleep=lambda _s: None,
        )
    finally:
        report_module.os.replace = original  # type: ignore[assignment]
    assert outcome.written == 0
    assert outcome.reason.startswith("write failed")
    assert outcome.cycles == 1, "the loop must stop on the first failed write"


def test_an_interrupt_is_a_named_stop_condition(tmp_path: Path) -> None:
    """F46 again, in a new loop. An interrupt is the common case, not an error."""
    from mavo.report import publish

    def interrupt(_seconds: float) -> None:
        raise KeyboardInterrupt

    outcome = publish(
        lambda: [_event(SAMBIR, AlertState.ACTIVE, 1)],
        tmp_path / "state.json",
        interval_s=0,
        max_cycles=None,
        table=_table(),
        sleep=interrupt,
    )
    assert outcome.reason == "interrupted by operator"
    assert outcome.written == 1, "the cycle that completed still published"


def test_watch_without_a_target_refuses_rather_than_running(tmp_path: Path) -> None:
    """--watch with nowhere to write is a loop that does nothing, loudly."""
    from mavo.cli import main

    assert main(["report", "--store", str(tmp_path / "events"), "--watch"]) == 2


def test_the_loop_publishes_a_blind_file_when_the_store_cannot_be_read(
    tmp_path: Path,
) -> None:
    """The heartbeat's whole reason, at the one place it is easiest to lose.

    Mutation: `continue` instead of publishing when `load()` raises. A consumer
    polling a file that stopped being written cannot tell a dead producer from
    a quiet night, and the quiet night is the reading it will take.
    """
    from mavo.report import publish

    target = tmp_path / "state.json"

    def broken() -> list[ThreatEvent]:
        raise RuntimeError("store is gone")

    outcome = publish(
        broken, target, interval_s=0, max_cycles=2, table=_table(), sleep=lambda _: None
    )
    assert outcome.cycles == 2
    assert outcome.written == 2, "a failed read must still produce a file"
    assert outcome.blind_cycles == 2
    assert json.loads(target.read_text(encoding="utf-8"))["state"] == "blind"


def test_the_loop_counts_what_it_did_and_names_why_it_stopped(tmp_path: Path) -> None:
    """A loop that ends without saying why has told its operator all is well."""
    from mavo.report import publish

    target = tmp_path / "state.json"
    outcome = publish(
        lambda: [_event(SAMBIR, AlertState.ACTIVE, 1)],
        target,
        interval_s=0,
        max_cycles=3,
        table=_table(),
        sleep=lambda _: None,
    )
    assert outcome.cycles == 3
    assert outcome.written == 3
    assert outcome.blind_cycles == 0
    assert "max_cycles=3" in outcome.reason
    assert "stopped:" in outcome.line()


def test_an_interrupt_is_a_stop_condition_and_not_a_stack_trace(
    tmp_path: Path,
) -> None:
    """F46's lesson, carried into the second loop this repository has.

    A run interrupted by an operator reports what it did. The alternative was
    measured once already: a backfill that had retrieved 1150 pages printed a
    traceback instead of a count.
    """
    from mavo.report import publish

    calls = {"n": 0}

    def load() -> list[ThreatEvent]:
        calls["n"] += 1
        if calls["n"] > 2:
            raise KeyboardInterrupt
        return [_event(SAMBIR, AlertState.ACTIVE, 1)]

    outcome = publish(
        load,
        tmp_path / "state.json",
        interval_s=0,
        max_cycles=10,
        table=_table(),
        sleep=lambda _: None,
    )
    assert outcome.reason == "interrupted by operator"
    assert outcome.written == 2


def test_a_write_failure_stops_the_loop_and_is_named(tmp_path: Path) -> None:
    """Mutation: swallow the OSError and keep cycling.

    A loop that cannot write is not publishing, and continuing quietly would
    leave a consumer reading a file nobody is refreshing while the process
    that should be refreshing it reports success.
    """
    import mavo.report as report_module
    from mavo.report import publish

    # Permissions are not the lever here: the suite runs as root in CI and in
    # the container, where a read-only directory is not read-only. Failing the
    # rename directly tests the branch rather than the environment.
    original = report_module.os.replace

    def explode(*args: object, **kwargs: object) -> None:
        raise OSError("read-only file system")

    report_module.os.replace = explode  # type: ignore[assignment]
    try:
        outcome = publish(
            lambda: [_event(SAMBIR, AlertState.ACTIVE, 1)],
            tmp_path / "state.json",
            interval_s=0,
            max_cycles=3,
            table=_table(),
            sleep=lambda _: None,
        )
    finally:
        report_module.os.replace = original  # type: ignore[assignment]
    assert outcome.written == 0
    assert outcome.cycles == 1, "the loop must stop rather than spin on a dead write"
    assert outcome.reason.startswith("write failed")


def test_watch_without_an_output_path_refuses(tmp_path: Path) -> None:
    """The loop exists to publish. Without a target it would be a busy no-op."""
    from mavo.cli import main

    assert main(["report", "--store", str(tmp_path / "events"), "--watch"]) == 2
