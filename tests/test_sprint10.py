"""S8 regressions: the report, and the honesty rules it must not lose.

`docs/MVP.md` numbers this sprint S8; the regression files are numbered by
shipped sprint, which is why this is sprint 10 on disk. The mapping is stated
here rather than left to be worked out from two sequences that diverged at
0.9.0.0.

Every test below is an invariant the product would be worthless without.

**Which of them are mutation-verified, stated precisely rather than
generously.** The tests whose docstring names a mutation were run against a
scratch copy carrying exactly that mutation and observed red. The rest are
ordinary regressions and are not claimed to be more. The blanket sentence that
stood here until 0.19.2.0 said every test had been verified that way, which was
written before any verification had happened and never corrected as tests were
added; it was false for more than half of them (F77).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mavo.areas import AreaTable
from mavo.report import (
    DEFAULT_VALID_FOR_S,
    FeedState,
    Report,
    compose,
    render_text,
    to_contract,
    write_contract,
)
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind

NOW = datetime(2026, 8, 10, 23, 41, tzinfo=UTC)
SAMBIR = "UA46080000000017237"   # Sambirskyi raion, touches the border
LVIV_RAION = "UA46060000000042587"  # Lvivskyi raion, same oblast as SAMBIR (F91)
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
    assert payload["v"] == 2
    assert payload["generated_at"] == NOW.isoformat(timespec="seconds")
    assert payload["valid_for_s"] == DEFAULT_VALID_FOR_S
    assert payload["state"] == "ok"
    assert payload["source_last_message_at"] is not None
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
    assert payload["v"] == 2
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


def test_the_oblast_field_is_a_slug_a_consumer_can_join_on() -> None:
    """F74: the map drew nothing while the distance list drew everything.

    The site indexes its geometry by ASCII slug. The contract published the
    register's Cyrillic display name in the same field, so every area landed
    in the consumer's "unplaceable" bucket: measured at four of four against
    `mavo-site` 1.2.0.0. Both readers are served now, and the join field is
    the machine one.

    Mutation: publish `picture.oblast` in the `oblast` key again.
    """
    payload = to_contract(
        compose([_event(SAMBIR, AlertState.ACTIVE, 1)], as_of=NOW, table=_table())
    )
    area = payload["areas"][0]
    assert area["oblast"] == "lviv", "the join field must be the ASCII slug"
    assert area["oblast_name"] == "Львівська", "the display name must survive too"
    assert area["oblast"].isascii(), "a consumer joins on this; it cannot be Cyrillic"


def test_an_unresolvable_oblast_publishes_an_empty_slug_not_a_guess() -> None:
    """Empty is the unknown state, and a consumer must be able to see it."""
    payload = to_contract(
        compose(
            [_event("UA00000000000000000", AlertState.ACTIVE, 1)],
            as_of=NOW,
            table=_table(),
        )
    )
    area = payload["areas"][0]
    assert area["oblast"] == ""
    assert area["oblast_name"] == "unknown"


def test_a_blind_report_publishes_a_null_source_time_rather_than_now() -> None:
    """`generated_at` says when we composed; this says when the source spoke."""
    payload = to_contract(compose([], as_of=NOW, table=_table()))
    assert payload["source_last_message_at"] is None


def test_one_episode_across_every_raion_of_an_oblast_counts_once() -> None:
    """F76: the counter measured administrative subdivision, not activity.

    A western episode lights every raion at once; 22 of the 81 in the design
    window touched all 36 western raions simultaneously. Counting transitions
    made one alert over Lviv count as seven, and an oblast with more raions
    render systematically darker. The earlier regression used a single raion,
    so the mutation had nothing to bite - the same test-data failure as the
    distance sort.

    Mutation: increment per transition into ACTIVE rather than per episode.
    """
    from mavo.report import trailing_counts

    table = _table()
    lviv = [
        table.resolve(tag).code  # type: ignore[union-attr]
        for tag in table.tags
        if table.resolve(tag) is not None
        and table.resolve(tag).oblast == "Львівська"  # type: ignore[union-attr]
    ]
    assert len(lviv) > 1, "the fixture needs an oblast with several raions"
    events = [_event(code, AlertState.ACTIVE, 120) for code in lviv]
    counts = trailing_counts(events, as_of=NOW, table=table)
    assert [(c.slug, c.alerts_count) for c in counts] == [("lviv", 1)]


def test_a_second_episode_after_a_full_all_clear_counts_again() -> None:
    """An episode closes when the last active raion is cleared, and only then."""
    from mavo.report import trailing_counts

    table = _table()
    lviv = [
        table.resolve(tag).code  # type: ignore[union-attr]
        for tag in table.tags
        if table.resolve(tag) is not None
        and table.resolve(tag).oblast == "Львівська"  # type: ignore[union-attr]
    ]
    events = (
        [_event(code, AlertState.ACTIVE, 120) for code in lviv]
        + [_event(code, AlertState.CLEAR, 100) for code in lviv]
        + [_event(lviv[0], AlertState.ACTIVE, 60)]
    )
    counts = trailing_counts(events, as_of=NOW, table=table)
    assert counts[0].alerts_count == 2
    assert counts[0].last_alert_ended_at == NOW - timedelta(minutes=100)


def test_a_partial_all_clear_does_not_close_an_episode() -> None:
    """One raion cleared while others are still under alert is not an ending.

    Mutation: close the episode on the first CLEAR. The count would then rise
    with the number of raions again, by a different route.
    """
    from mavo.report import trailing_counts

    table = _table()
    lviv = [
        table.resolve(tag).code  # type: ignore[union-attr]
        for tag in table.tags
        if table.resolve(tag) is not None
        and table.resolve(tag).oblast == "Львівська"  # type: ignore[union-attr]
    ]
    events = [_event(code, AlertState.ACTIVE, 120) for code in lviv]
    events += [_event(code, AlertState.CLEAR, 100) for code in lviv[:-1]]
    counts = trailing_counts(events, as_of=NOW, table=table)
    assert counts[0].alerts_count == 1
    assert counts[0].last_alert_ended_at is None, (
        "an episode still running has not ended"
    )


def test_unknown_does_not_close_an_episode() -> None:
    """Silence is not an all-clear, inside a counter as everywhere else.

    Mutation: treat UNKNOWN like CLEAR. A feed outage would then close every
    episode and the next message would open a new one, inflating the count
    exactly when the feed is least reliable.
    """
    from mavo.report import trailing_counts

    events = [
        _event(SAMBIR, AlertState.ACTIVE, 300),
        _event(SAMBIR, AlertState.UNKNOWN, 200),
        _event(SAMBIR, AlertState.ACTIVE, 100),
    ]
    counts = trailing_counts(events, as_of=NOW, table=_table())
    assert counts[0].alerts_count == 1
    assert counts[0].last_alert_ended_at is None


def test_an_unresolvable_area_is_not_folded_into_another_oblast() -> None:
    """A count that is quietly wrong is worse than one that is visibly absent."""
    from mavo.report import trailing_counts

    counts = trailing_counts(
        [_event("UA00000000000000000", AlertState.ACTIVE, 60)],
        as_of=NOW,
        table=_table(),
    )
    assert counts == ()


def test_an_oblast_with_no_all_clear_reports_null_rather_than_a_time() -> None:
    """Mutation: fall back to the last event's time. That reads as "ended"."""
    from mavo.report import trailing_counts

    counts = trailing_counts(
        [_event(SAMBIR, AlertState.ACTIVE, 60)], as_of=NOW, table=_table()
    )
    assert counts[0].last_alert_ended_at is None


def test_the_contract_publishes_the_window_it_used() -> None:
    """A count without its window is a number a reader has to guess about."""
    report = compose(
        [_event(SAMBIR, AlertState.ACTIVE, 60)], as_of=NOW, table=_table()
    )
    payload = to_contract(report)
    assert payload["window_days"] == 7
    assert payload["recent_7d"] == [
        {"oblast": "lviv", "alerts_count": 1, "last_alert_ended_at": None}
    ]


def test_composing_twice_from_one_generator_does_not_empty_the_window() -> None:
    """The fold and the window both read the log; a generator serves one.

    Mutation: pass `events` straight through instead of materialising it. The
    seven-day layer would come back empty, which renders as a quiet week.
    """
    events = (e for e in [_event(SAMBIR, AlertState.ACTIVE, 60)])
    report = compose(events, as_of=NOW, table=_table())
    assert len(report.areas) == 1
    assert len(report.recent) == 1


def test_the_command_reports_the_schema_version_it_actually_wrote(
    tmp_path: Path, capsys: object
) -> None:
    """F75: the line said v=1 while the file said v=2.

    The literal was correct on the day it was typed and became a lie one
    release later, when the schema moved and the message did not. An operator
    reading the terminal would report the wrong version to a consumer
    debugging a refusal. Mutation: put the literal back.
    """
    from mavo.cli import main
    from mavo.report import SCHEMA_VERSION

    target = tmp_path / "state.json"
    main(["report", "--store", str(tmp_path / "events"), "--json", str(target)])
    printed = capsys.readouterr().out  # type: ignore[attr-defined]
    written = json.loads(target.read_text(encoding="utf-8"))["v"]
    assert written == SCHEMA_VERSION
    assert f"v={written}" in printed, "the message must name the version on disk"


def test_the_blind_cause_is_printed_even_when_a_callback_is_installed(
    tmp_path: Path, capsys: object
) -> None:
    """The production path always installs `on_cycle`, so a cause printed only
    without one is a cause no operator has ever seen (F83).

    `mavo report --watch` passes `announce` unconditionally, which made the
    `if on_cycle is None` guard select exactly the mode nobody runs. The
    operator saw `feed=blind` on every cycle and the exception that caused it
    went nowhere. Mutation: restore the guard.
    """
    from mavo.report import publish

    def broken() -> list[ThreatEvent]:
        raise OSError("store file vanished mid-read")

    publish(
        broken, tmp_path / "state.json", interval_s=0, max_cycles=1,
        table=_table(), sleep=lambda _s: None, on_cycle=lambda _r: None,
    )
    printed = capsys.readouterr().err  # type: ignore[attr-defined]
    assert "store file vanished mid-read" in printed, (
        "the cause of blindness must reach the operator on the path they run"
    )


def test_the_loop_tracks_a_changing_store_cycle_by_cycle(tmp_path: Path) -> None:
    """Every existing loop test fed a constant, so a loop that read the store
    once and replayed the first picture forever would have passed all of them.

    The store here changes between cycles - active, then cleared, then
    unreadable - and each cycle's file must reflect that cycle's store.
    Mutation: hoist `list(load())` above the loop; the second cycle then
    republishes the first picture and this fails on the cleared area.
    """
    from mavo.report import publish

    target = tmp_path / "state.json"
    logs: list[object] = [
        [_event(SAMBIR, AlertState.ACTIVE, 5)],
        [_event(SAMBIR, AlertState.ACTIVE, 5), _event(SAMBIR, AlertState.CLEAR, 2)],
        OSError("store is gone"),
    ]
    calls = {"n": 0}

    def evolving_store() -> list[ThreatEvent]:
        step = logs[calls["n"]]
        calls["n"] += 1
        if isinstance(step, OSError):
            raise step
        return step  # type: ignore[return-value]

    seen: list[tuple[str, int]] = []

    def observe(_report: Report) -> None:
        payload = json.loads(target.read_text(encoding="utf-8"))
        seen.append((payload["state"], len(payload["areas"])))

    outcome = publish(
        evolving_store, target, interval_s=0, max_cycles=3,
        table=_table(), sleep=lambda _s: None, on_cycle=observe,
        now=lambda: NOW,
    )
    assert seen == [("ok", 1), ("ok", 0), ("blind", 0)], (
        "each cycle's file must carry that cycle's store, not the first one's"
    )
    assert outcome.written == 3
    assert outcome.blind_cycles == 1


def test_a_broken_callback_does_not_stop_the_heartbeat(tmp_path: Path) -> None:
    """The observer is not the product; the file is (F84).

    `announce` prints to stdout, and a closed pipe raises BrokenPipeError
    inside `on_cycle`, which propagated out of `publish` as a stack trace with
    no PublishReport - the F46 shape, reintroduced through the observability
    hook. Killing the heartbeat because `head` closed a pipe would stop the
    one output a consumer depends on.

    The callback is disabled after its first failure and the loop keeps
    writing; the failure is counted and named. Mutation: let the exception
    propagate.
    """
    from mavo.report import publish

    target = tmp_path / "state.json"
    calls = {"n": 0}

    def fragile(_report: Report) -> None:
        calls["n"] += 1
        raise BrokenPipeError("stdout reader went away")

    outcome = publish(
        lambda: [_event(SAMBIR, AlertState.ACTIVE, 1)],
        target, interval_s=0, max_cycles=3,
        table=_table(), sleep=lambda _s: None, on_cycle=fragile,
    )
    assert outcome.written == 3, "the file must keep being written"
    assert calls["n"] == 1, "a callback that failed once is not retried forever"
    assert outcome.callback_failures == 1
    assert "callback" in outcome.line(), "the failure must be named to the operator"


def test_an_episode_open_at_the_window_edge_still_counts() -> None:
    """An alert that began before the window and never cleared is not a quiet week.

    The docstring has promised since F76 that an episode left open stays open
    and the count "does not understate". The cutoff filter broke that promise
    at the window edge: the opening event aged out, the episode had never
    closed, and the oblast under the longest-running alert rendered as the
    quietest (F85). Mutation: restore the pre-filter.
    """
    from mavo.report import trailing_counts

    events = [_event(SAMBIR, AlertState.ACTIVE, 60 * 24 * 10)]  # 10 days, never cleared
    counts = trailing_counts(events, as_of=NOW, table=_table())
    assert [(c.slug, c.alerts_count) for c in counts] == [("lviv", 1)]


def test_an_episode_straddling_the_edge_records_its_close() -> None:
    """Opened before the window, cleared inside it: one episode, with its end."""
    from mavo.report import trailing_counts

    events = [
        _event(SAMBIR, AlertState.ACTIVE, 60 * 24 * 10),
        _event(SAMBIR, AlertState.CLEAR, 60 * 24 * 6),
    ]
    counts = trailing_counts(events, as_of=NOW, table=_table())
    assert counts[0].alerts_count == 1
    assert counts[0].last_alert_ended_at == NOW - timedelta(minutes=60 * 24 * 6)


def test_an_episode_closed_before_the_window_does_not_count() -> None:
    """The guard on the other side: affirmatively over before the window began.

    This replaces the old fixture for the cutoff, whose single un-cleared
    ACTIVE was exactly the open-at-the-edge case the counter was wrong about:
    test data chosen by the implementation, measuring the code against itself.
    """
    from mavo.report import trailing_counts

    events = [
        _event(SAMBIR, AlertState.ACTIVE, 60 * 24 * 10),
        _event(SAMBIR, AlertState.CLEAR, 60 * 24 * 9),
    ]
    assert trailing_counts(events, as_of=NOW, table=_table()) == ()


def test_a_carried_episode_absorbs_an_in_window_one() -> None:
    """F91. The count moves in both directions, and the F85 entry said one.

    Every F85 regression used a single area per oblast, and with one area a
    carried episode can never absorb an in-window one, so the fixtures could
    not express this at all. Two areas of one oblast: the first opens before
    the window and never clears, the second runs ACTIVE, CLEAR, ACTIVE inside
    it. The oblast never stops being under alert, so this is one episode.

    The pre-F85 fold answered 2 here, because it dropped the pre-window event
    and started a fresh episode on each in-window ACTIVE. Verified on the
    operator's machine against `d988094` in a worktree, 2 against 1.

    This test asserts the current behaviour and pins the direction question
    rather than settling it: if `alerts_count` should count in-window openings
    rather than oblast-level episodes, this is the test that has to change, and
    changing it should be a decision rather than a fix.
    """
    from mavo.report import trailing_counts

    events = [
        _event(SAMBIR, AlertState.ACTIVE, 60 * 24 * 10),
        _event(LVIV_RAION, AlertState.ACTIVE, 60 * 24 * 5),
        _event(LVIV_RAION, AlertState.CLEAR, 60 * 24 * 4),
        _event(LVIV_RAION, AlertState.ACTIVE, 60 * 24 * 3),
    ]
    counts = trailing_counts(events, as_of=NOW, table=_table())
    assert [(c.slug, c.alerts_count) for c in counts] == [("lviv", 1)], (
        "an oblast under continuous alert across the window edge is one episode"
    )


def test_the_interval_is_drawn_per_cycle_and_recorded(tmp_path: Path) -> None:
    """T27. A fixed period is a beacon profile and a regular load.

    The draw goes in now rather than after the first measurements, because
    adding it later would invalidate every interval measurement taken before
    it - and those measurements are the evidence that would justify tightening
    the poll. Each waited interval is recorded, because a distribution nobody
    kept is a distribution nobody can check against the configured range.
    Mutation: sleep `interval_s` directly.
    """
    from mavo.report import publish

    waits: list[float] = []
    draws = iter([54.0, 66.0, 60.0])
    outcome = publish(
        lambda: [_event(SAMBIR, AlertState.ACTIVE, 1)],
        tmp_path / "state.json", interval_s=60.0, max_cycles=3,
        table=_table(), sleep=waits.append, on_cycle=lambda _r: None,
        jitter=0.10, draw=lambda low, high: next(draws),
    )
    assert waits == [54.0, 66.0], "the loop must sleep what it drew"
    assert outcome.intervals == (54.0, 66.0)


def test_the_draw_stays_inside_the_configured_spread(tmp_path: Path) -> None:
    """The bounds handed to the draw are the configured range, not a guess."""
    from mavo.report import publish

    seen: list[tuple[float, float]] = []

    def record(low: float, high: float) -> float:
        seen.append((low, high))
        return low

    publish(
        lambda: [], tmp_path / "state.json", interval_s=60.0, max_cycles=2,
        table=_table(), sleep=lambda _s: None, jitter=0.15, draw=record,
    )
    assert seen == [(51.0, 69.0)]
