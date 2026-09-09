"""The API adapter: snapshots turned into transitions without inventing clears.

The channel stopped publishing on 2026-08-29 at 04:55 UTC and this project had
no second pipe to ask. These tests hold the properties that make the
replacement safe rather than merely available: a first snapshot clears nothing,
a region leaving the snapshot clears exactly once, a failed poll clears
nothing at all, and - because production runs collectors as oneshot processes -
a persisted snapshot licenses clears across a restart only while it is young.
Stale, missing, corrupt, or stamped by a clock that ran backwards, it licenses
nothing, and says which of those it was.

Payload shape is taken from a live response measured on 2026-08-30, not from a
reading of the parser: `regionId`, `regionType`, `regionName`, `lastUpdate` and
a nested `activeAlerts` carrying its own `type` and `lastUpdate`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.areas import AreaTable
from mavo.errors import SourceUnavailable
from mavo.schema import AlertState, Provenance, ThreatKind
from mavo.sources.ukrainealarm_source import UkrainealarmSource


class SequenceTransport:
    """Returns each body in turn. `StubTransport` holds one; snapshots need a
    sequence, because the whole question is what changes between two polls."""

    def __init__(self, bodies: list[str]) -> None:
        self._bodies = list(bodies)
        self.calls = 0

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        """Return the next canned body, repeating the last one when exhausted."""
        body = self._bodies[min(self.calls, len(self._bodies) - 1)]
        self.calls += 1
        return body


LVIV = "Львівський район"
VOLODYMYR = "Володимирський район"


def _snapshot(*regions: tuple[str, str]) -> str:
    """An API body listing each `(name, type)` as one active alert."""
    return json.dumps(
        [
            {
                "regionId": str(index),
                "regionType": "District",
                "regionName": name,
                "lastUpdate": "2026-08-30T13:19:40Z",
                "activeAlerts": [
                    {
                        "regionId": str(index),
                        "regionType": "District",
                        "type": kind,
                        "lastUpdate": "2026-08-30T13:19:40Z",
                    }
                ],
            }
            for index, (name, kind) in enumerate(regions, start=1)
        ]
    )


def _source(transport: SequenceTransport) -> UkrainealarmSource:
    return UkrainealarmSource("key", areas=AreaTable.from_csv(), transport=transport)


def test_first_poll_reports_alerts_and_clears_nothing() -> None:
    """A snapshot with no predecessor cannot say what ended.

    The first poll of a process sees areas alerting and knows nothing about the
    ones that are not: their absence is unobserved, not observed-absent. Issuing
    clears here would let a restart announce all-clears for a window during
    which this process saw nothing at all.
    """
    source = _source(SequenceTransport([_snapshot((LVIV, "AIR"))]))

    events = source.poll()

    assert [event.state for event in events] == [AlertState.ACTIVE]
    assert events[0].kind is ThreatKind.UNKNOWN
    assert events[0].oblast == "Львівська"


def test_an_area_leaving_the_snapshot_clears_once() -> None:
    """The API stops listing an alert instead of announcing its end.

    The all-clear is therefore a difference between two snapshots, and it is
    dated from the observation rather than from the start the alert carried:
    the API never says when it ended, and dating the clear from the start would
    report it as having happened hours before anything saw it.
    """
    transport = SequenceTransport(
        [_snapshot((LVIV, "AIR")), _snapshot(), _snapshot()]
    )
    source = _source(transport)

    first = source.poll()
    second = source.poll()
    third = source.poll()

    assert [event.state for event in first] == [AlertState.ACTIVE]
    assert [event.state for event in second] == [AlertState.CLEAR]
    assert second[0].oblast == "Львівська"
    assert second[0].ts_source == second[0].ts_ingest
    assert third == ()


def test_a_failed_poll_clears_nothing() -> None:
    """A refusal is silence, and silence is never an all-clear.

    This is the property the whole project rests on, one layer down: an absence
    only counts as evidence when the observation succeeded. A malformed body
    must leave the previous snapshot standing rather than emptying the map.
    """
    transport = SequenceTransport([_snapshot((LVIV, "AIR")), "not json at all"])
    source = _source(transport)
    source.poll()

    with pytest.raises(SourceUnavailable):
        source.poll()

    assert source._previous is not None
    assert len(source._previous) == 1


def test_a_renamed_border_raion_resolves() -> None:
    """Volodymyr raion reaches the contract, by the name the register uses.

    The map keys this row on the channel's tag, which keeps the pre-2021 name,
    while the API publishes the current one. It is a border raion in Volyn, so
    an adapter that could not resolve it would be silent about one of the few
    areas this project exists to watch.
    """
    source = _source(SequenceTransport([_snapshot((VOLODYMYR, "AIR"))]))

    events = source.poll()

    assert [event.state for event in events] == [AlertState.ACTIVE]
    assert events[0].oblast == "Волинська"


def test_a_region_the_map_does_not_know_is_counted_not_dropped() -> None:
    """An unresolvable region is a finding about the map, not a silent loss."""
    source = _source(SequenceTransport([_snapshot(("Марсіанський район", "AIR"))]))

    events = source.poll()

    assert events == ()
    assert source.unresolved == ("Марсіанський район",)


def test_a_key_present_on_consecutive_polls_is_neither_reopened_nor_cleared() -> None:
    """The steady state, which production runs tens of thousands of times a day.

    Until 0.53.3.0 no test polled twice with the same key: the suite walked a
    key appearing and a key disappearing, never a key that simply is, and the
    two `continue` lines that make an open alert stay one open alert were
    executed by nothing (P1, the review of 2026-09-08). A defect there has the
    worst shape this project knows: an ACTIVE re-issued for an alert already
    open would announce the alarm again on the map and count one episode as
    two in the register; a CLEAR issued for a key still listed would end an
    alert that had not ended. A neighbour that comes and goes around the
    steady key is what separates the two `continue`s from their absence.
    """
    transport = SequenceTransport(
        [
            _snapshot((LVIV, "AIR")),
            _snapshot((LVIV, "AIR"), (VOLODYMYR, "AIR")),
            _snapshot((LVIV, "AIR")),
            _snapshot((LVIV, "AIR")),
        ]
    )
    source = _source(transport)

    first = source.poll()
    second = source.poll()
    third = source.poll()
    fourth = source.poll()

    assert [(e.area_id[:2], e.state) for e in first] == [("UA", AlertState.ACTIVE)]
    assert [e.state for e in second] == [AlertState.ACTIVE]
    assert second[0].area_id != first[0].area_id
    assert [e.state for e in third] == [AlertState.CLEAR]
    assert third[0].area_id == second[0].area_id
    assert fourth == ()
    assert source._previous is not None
    assert list(source._previous) == [(first[0].area_id, ThreatKind.UNKNOWN)]
    assert source._previous[(first[0].area_id, ThreatKind.UNKNOWN)] == first[0].ts_source


def test_a_key_that_leaves_and_returns_is_two_episodes() -> None:
    """A gap in the listing is an end and a new beginning, in that order.

    The steady-state test above holds a key that never leaves. This one
    holds the key that does: absent for one poll, present again on the next,
    which the API expresses by listing it, not listing it, and listing it
    again. The adapter must say CLEAR then ACTIVE - two rows, two episodes -
    and must not carry the first episode's start onto the second.
    """
    later = json.loads(_snapshot((LVIV, "AIR")))
    later[0]["lastUpdate"] = "2026-08-30T15:00:00Z"
    later[0]["activeAlerts"][0]["lastUpdate"] = "2026-08-30T15:00:00Z"
    transport = SequenceTransport(
        [_snapshot((LVIV, "AIR")), _snapshot(), json.dumps(later)]
    )
    source = _source(transport)

    first = source.poll()
    second = source.poll()
    third = source.poll()

    assert [e.state for e in first] == [AlertState.ACTIVE]
    assert [e.state for e in second] == [AlertState.CLEAR]
    assert [e.state for e in third] == [AlertState.ACTIVE]
    assert third[0].ts_source.isoformat() == "2026-08-30T15:00:00+00:00"
    assert third[0].ts_source > first[0].ts_source
    assert third[0].content_hash != first[0].content_hash


def _levelled(name: str, start: str, *levels: tuple[str, str]) -> str:
    """One alert on `name` begun at `start`, carrying the given level records."""
    return json.dumps([{
        "regionId": "1293", "regionType": "State", "regionName": name,
        "lastUpdate": start,
        "activeAlerts": [{
            "regionId": "1293", "regionType": "State", "type": "AIR",
            "lastUpdate": start,
            "activeAlertLevels": [
                {"alertLevel": level, "reason": "", "createdAt": at} for level, at in levels
            ],
        }],
    }])


def test_a_continuing_key_whose_level_changed_produces_no_episode_event() -> None:
    """An escalation is not a new alert, and the episode row is not rewritten.

    D-050: the level joins no identity, so yellow to red inside one alert
    opens no row and closes none. This is the regression control for the
    release that records level changes as their own stream: whatever that
    release adds, the episode side of `poll()` must still answer nothing
    here, and the opening row must keep the level it opened with (P2 says
    that field is the level at the start, and is read as nothing else).
    """
    yellow, red = "2026-09-08T17:22:35Z", "2026-09-08T18:01:01Z"
    transport = SequenceTransport(
        [
            _levelled(LVIV, yellow, ("Yellow", yellow)),
            _levelled(LVIV, yellow, ("Yellow", yellow), ("Red", red)),
        ]
    )
    source = _source(transport)

    first = source.poll()
    second = source.poll()

    assert [e.state for e in first] == [AlertState.ACTIVE]
    assert first[0].raw_fields["api_level"] == "Yellow"
    assert second == ()
    assert source._previous is not None
    assert len(source._previous) == 1


def test_a_declined_region_is_counted_apart_from_an_unknown_one() -> None:
    """F131 through `poll()`: a name the register holds and will not resolve.

    `resolve_prose_detail` had its own tests for the declined half; the
    adapter's branch that reads that answer and files the name under
    `declined` rather than `unresolved` had none, while production prints
    `declined=1` on every cycle. The two counters have different repairs -
    settle an ambiguity, add a row - and a name filed under the wrong one
    sends the operator to the wrong file.
    """
    source = _source(
        SequenceTransport([_snapshot(("Покровська територіальна громада", "ARTILLERY"))])
    )

    events = source.poll()

    assert events == ()
    assert source.declined == ("Покровська територіальна громада",)
    assert source.unresolved == ()


def _persisted(
    transport: SequenceTransport, path: Path, max_age_s: float = 360.0
) -> UkrainealarmSource:
    return UkrainealarmSource(
        "key",
        areas=AreaTable.from_csv(),
        transport=transport,
        snapshot=path,
        snapshot_max_age_s=max_age_s,
    )


def test_a_fresh_snapshot_lets_a_new_process_clear(tmp_path: Path) -> None:
    """The whole repair: oneshot deployments run one poll per process.

    The first process sees an alert and persists the snapshot; the second,
    minutes later by the timer, finds the area gone and must be able to say
    so. Without persistence every poll is a first poll, `cleared` is zero
    forever, and every episode the API opened stays open - the frozen-episode
    pathology manufactured locally. The clear that crosses the restart still
    carries the oblast and the start the first process observed.
    """
    path = tmp_path / "snapshot.json"
    first = _persisted(SequenceTransport([_snapshot((LVIV, "AIR"))]), path)
    assert first.snapshot_state == "missing"
    first.poll()
    first.save_snapshot()

    second = _persisted(SequenceTransport([_snapshot()]), path)
    events = second.poll()

    assert second.snapshot_state == "fresh"
    assert second.snapshot_age_s is not None and second.snapshot_age_s >= 0
    assert [event.state for event in events] == [AlertState.CLEAR]
    assert events[0].oblast == "Львівська"
    assert events[0].provenance is Provenance.INFERENCE
    assert events[0].raw_fields["began"] == "2026-08-30T13:19:40+00:00"


def test_a_stale_snapshot_licenses_nothing(tmp_path: Path) -> None:
    """A snapshot older than the ceiling means the observation had a gap.

    Clearing against it would announce all-clears for a window during which
    nothing was watching, which is the exact failure the class docstring
    names as the cost of persistence without a ceiling. The withholding is
    stated, not silent: `stale` on the state, the age on the instance.
    """
    path = tmp_path / "snapshot.json"
    first = _persisted(SequenceTransport([_snapshot((LVIV, "AIR"))]), path)
    first.poll()
    first.save_snapshot()

    second = _persisted(SequenceTransport([_snapshot()]), path, max_age_s=0.0)
    events = second.poll()

    assert second.snapshot_state == "stale"
    assert events == ()


def test_a_snapshot_from_a_backwards_clock_is_stale(tmp_path: Path) -> None:
    """A save stamped in the future is a clock not to be trusted.

    T40 measured source clocks disagreeing with ours in both directions; a
    wall clock that stepped back between two runs of the same host produces a
    negative age here, and a negative age licenses exactly what an excessive
    one does: nothing.
    """
    path = tmp_path / "snapshot.json"
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    path.write_text(
        json.dumps({"saved_at": future, "areas": []}), encoding="utf-8"
    )

    source = _persisted(SequenceTransport([_snapshot()]), path)
    source.poll()

    assert source.snapshot_state == "stale"


def test_a_missing_snapshot_is_a_cold_start(tmp_path: Path) -> None:
    """No file, no clears: the first run of a deployment has seen nothing."""
    source = _persisted(
        SequenceTransport([_snapshot((LVIV, "AIR"))]), tmp_path / "absent.json"
    )

    events = source.poll()

    assert source.snapshot_state == "missing"
    assert [event.state for event in events] == [AlertState.ACTIVE]


def test_a_corrupt_snapshot_withholds_clears_and_never_stops_collection(
    tmp_path: Path,
) -> None:
    """A broken cache is a broken cache, not an outage and not an all-clear.

    Whatever is in the file - malformed JSON here, a half-written `.partial`
    promoted by hand, a kind the schema no longer holds - the load resolves
    to `corrupt`, licenses no clears, and lets the poll proceed: alerts must
    keep raising while the cache is bad, or a disk fault would blind the one
    pipe still working.
    """
    path = tmp_path / "snapshot.json"
    path.write_text("not json at all", encoding="utf-8")

    source = _persisted(SequenceTransport([_snapshot((LVIV, "AIR"))]), path)
    events = source.poll()

    assert source.snapshot_state == "corrupt"
    assert [event.state for event in events] == [AlertState.ACTIVE]


def test_save_is_atomic_and_round_trips(tmp_path: Path) -> None:
    """The payload takes the target name only whole.

    A half-written file with the target's name is the artefact the 0.43.0.0
    deploy's failed `scp` left behind, and a loader finding one would read
    it as corrupt and withhold clears for a cycle nothing required. After a
    save there is no `.partial` beside the target, and a second process reads
    back exactly the areas the first one held.
    """
    path = tmp_path / "snapshot.json"
    first = _persisted(SequenceTransport([_snapshot((LVIV, "AIR"))]), path)
    first.poll()
    first.save_snapshot()

    assert path.exists()
    assert not path.with_name(path.name + ".partial").exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert [entry["kind"] for entry in payload["areas"]] == ["UNKNOWN"]
    assert payload["areas"][0]["oblast"] == "Львівська"


def test_an_unreadable_snapshot_is_corrupt_not_fatal(tmp_path: Path) -> None:
    """A path that exists and cannot be read as a file is a broken cache.

    A directory where the snapshot should be raises `OSError` on read, which
    is the same class a permissions fault raises; both resolve to `corrupt`,
    license nothing, and let the poll proceed, because a broken cache must
    never take down the one pipe still working.
    """
    path = tmp_path / "snapshot.json"
    path.mkdir()

    source = _persisted(SequenceTransport([_snapshot((LVIV, "AIR"))]), path)
    events = source.poll()

    assert source.snapshot_state == "corrupt"
    assert [event.state for event in events] == [AlertState.ACTIVE]


def test_a_naive_saved_at_is_corrupt(tmp_path: Path) -> None:
    """A timestamp without a timezone cannot be aged against UTC honestly.

    Guessing a zone for it would make the freshness comparison a guess too,
    and a guessed ceiling licenses clears exactly as well as no ceiling.
    """
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps({"saved_at": "2026-08-30T13:00:00", "areas": []}),
        encoding="utf-8",
    )

    source = _persisted(SequenceTransport([_snapshot()]), path)
    source.poll()

    assert source.snapshot_state == "corrupt"


def test_save_before_a_successful_poll_writes_nothing(tmp_path: Path) -> None:
    """Nothing observed, nothing persisted: an empty claim would be a claim.

    A snapshot written before the first successful poll would stamp `now`
    over a reading that never happened, and the next process would treat the
    absence of every area as fresh evidence.
    """
    path = tmp_path / "snapshot.json"
    source = _persisted(SequenceTransport([_snapshot()]), path)

    source.save_snapshot()

    assert not path.exists()


def test_an_air_alert_is_not_classified_as_a_missile() -> None:
    """The API has one type for everything that flies, and it is not a claim.

    The channel named the means of attack because it wrote it in prose:
    ballistic, drone, glide bomb. `AIR` says only that something is in the air.
    Mapping it to MISSILE would put a classification on the reader's page that
    the operator never made - a missile icon over an alert nobody called a
    missile - and would hand `r3_border_missile` a match it has no evidence
    for. Unknown is a state here, not a gap to fill with the likeliest guess
    (D-042).
    """
    source = _source(SequenceTransport([_snapshot((LVIV, "AIR"))]))

    events = source.poll()

    assert events[0].kind is ThreatKind.UNKNOWN


def test_an_artillery_alert_keeps_the_kind_the_api_states() -> None:
    """The refusal is about what the source does not say, not about all kinds.

    `ARTILLERY` is named by the API, so it survives as itself. A blanket
    UNKNOWN would discard a classification the source did make, which is the
    same defect as inventing one, pointing the other way.
    """
    source = _source(SequenceTransport([_snapshot((LVIV, "ARTILLERY"))]))

    events = source.poll()

    assert events[0].kind is ThreatKind.ARTILLERY


def test_an_informational_message_is_not_an_alert() -> None:
    """`INFO` is counted by region and never folded into UNKNOWN (T83)."""
    source = _source(SequenceTransport([_snapshot((LVIV, "INFO"), (VOLODYMYR, "AIR"))]))
    events = source.poll()
    assert [event.state for event in events] == [AlertState.ACTIVE]
    assert events[0].kind is ThreatKind.UNKNOWN
    assert source.informational == (LVIV,)
    assert source.unmapped_types == {}
    assert source.unparsed == ()


def test_an_informational_message_ending_is_not_an_all_clear() -> None:
    """What never entered the snapshot cannot clear out of it."""
    source = _source(SequenceTransport([_snapshot((LVIV, "INFO")), _snapshot()]))
    assert source.poll() == ()
    assert source.poll() == ()
    assert source.informational == ()


def test_a_novel_type_string_is_folded_to_unknown_and_named() -> None:
    """A type outside `_KIND` still raises an alert, and says which type (T83)."""
    source = _source(SequenceTransport([_snapshot((LVIV, "BALLISTIC"), (VOLODYMYR, "AIR"))]))
    events = source.poll()
    assert len(events) == 2
    assert all(event.kind is ThreatKind.UNKNOWN for event in events)
    assert source.unmapped_types == {"BALLISTIC": (LVIV,)}
    assert source.unparsed == ()
    assert source.informational == ()


def _two_alerts_one_kind(name: str, first: str, second: str, kind: str = "AIR") -> str:
    """One region carrying two active alerts of one type, begun at `first` and
    `second`, in that payload order."""
    return json.dumps(
        [
            {
                "regionId": "1284",
                "regionType": "Community",
                "regionName": name,
                "lastUpdate": second,
                "activeAlerts": [
                    {"regionId": "1284", "regionType": "Community",
                     "type": kind, "lastUpdate": first},
                    {"regionId": "1284", "regionType": "Community",
                     "type": kind, "lastUpdate": second},
                ],
            }
        ]
    )


def test_two_alerts_of_one_kind_on_one_area_fold_to_the_earliest_start() -> None:
    """The store keys an episode on `(area_id, kind)`, so two alerts of one
    type in one region are one row whatever the API sends. Until 0.53.0.0 the
    row took the start of whichever alert came later in the payload's own
    order, which the API does not promise; a captured payload on 2026-09-08
    carried one hromada with two `AIR` alerts whose level records dated March
    and that afternoon, and which start the episode wore depended on list
    position. The stamps in this test are chosen, not copied from that payload.

    The rule is the earliest start, in either order, and the fold is counted
    so it can be read off the recap rather than inferred from a date.
    """
    march, today = "2026-03-10T14:01:38Z", "2026-09-08T18:00:40Z"
    for order in ((march, today), (today, march)):
        source = _source(SequenceTransport([_two_alerts_one_kind(LVIV, *order)]))
        events = source.poll()
        assert [event.state for event in events] == [AlertState.ACTIVE]
        assert events[0].ts_source.isoformat() == "2026-03-10T14:01:38+00:00", order
        assert source.overlapping == {(events[0].area_id, "UNKNOWN"): 2}


def test_a_region_with_one_alert_per_kind_reports_no_overlap() -> None:
    """The counter is silent when nothing folds, so a non-empty value is a
    finding and not a constant."""
    source = _source(SequenceTransport([_snapshot((LVIV, "AIR"), (VOLODYMYR, "ARTILLERY"))]))
    source.poll()
    assert source.overlapping == {}


def test_the_substitution_mark_follows_the_start_that_is_kept() -> None:
    """One of two overlapping alerts carries no start and takes the read time
    (F136); the other carries a real one. Whichever order they arrive in, the
    row keeps the real start and does not say it was observed at read time,
    because that mark is what lets the latency measurement leave substituted
    rows out, and a real stamp mislabelled would be left out with them.
    """
    real = "2026-09-08T18:00:40Z"
    for first, second in ((real, None), (None, real)):
        body = json.dumps([{
            "regionId": "1284", "regionType": "Community", "regionName": LVIV,
            "lastUpdate": real,
            "activeAlerts": [
                {"regionId": "1284", "regionType": "Community", "type": "AIR",
                 **({"lastUpdate": first} if first else {})},
                {"regionId": "1284", "regionType": "Community", "type": "AIR",
                 **({"lastUpdate": second} if second else {})},
            ],
        }])
        source = _source(SequenceTransport([body]))
        events = source.poll()
        assert len(events) == 1
        assert events[0].ts_source.isoformat() == "2026-09-08T18:00:40+00:00", (first, second)
        assert "ts_source_origin" not in events[0].raw_fields, (first, second)
        assert source.overlapping == {(events[0].area_id, "UNKNOWN"): 2}


def _escalated(name: str, yellow: str, red: str, last_update: str) -> str:
    """One alert that went yellow to red, with `lastUpdate` bumped to the red
    record, the shape measured on 2026-09-08."""
    return json.dumps([{
        "regionId": "1293", "regionType": "State", "regionName": name,
        "lastUpdate": last_update,
        "activeAlerts": [{
            "regionId": "1293", "regionType": "State", "type": "AIR",
            "lastUpdate": last_update,
            "activeAlertLevels": [
                {"alertLevel": "Red", "reason": "", "createdAt": red},
                {"alertLevel": "Yellow", "reason": "", "createdAt": yellow},
            ],
        }],
    }])


def test_an_escalated_alert_begins_at_its_first_level_not_its_last_update() -> None:
    """From 2026-09-06 the API bumps `lastUpdate` when an alert changes level,
    so read as a start it dates the episode from the escalation. Measured on
    2026-09-08: Kharkiv city went yellow at 17:22:35 and red at 18:01:01, and
    `lastUpdate` sat at 18:01:00. The row must wear the first level's stamp,
    whatever order the level records arrive in.
    """
    yellow, red, bumped = "2026-09-08T17:22:35Z", "2026-09-08T18:01:01Z", "2026-09-08T18:01:00Z"
    source = _source(SequenceTransport([_escalated(LVIV, yellow, red, bumped)]))
    events = source.poll()
    assert [event.state for event in events] == [AlertState.ACTIVE]
    assert events[0].ts_source.isoformat() == "2026-09-08T17:22:35+00:00"
    assert "ts_source_origin" not in events[0].raw_fields


def test_an_alert_without_level_records_still_begins_at_last_update() -> None:
    """A payload from before the field existed, or a record whose level
    stamps cannot be read, must parse exactly as it always did."""
    source = _source(SequenceTransport([_snapshot((LVIV, "AIR"))]))
    events = source.poll()
    assert events[0].ts_source.isoformat() == "2026-08-30T13:19:40+00:00"
    body = json.dumps([{
        "regionId": "1", "regionType": "District", "regionName": LVIV,
        "lastUpdate": "2026-08-30T13:19:40Z",
        "activeAlerts": [{"regionId": "1", "regionType": "District", "type": "AIR",
                          "lastUpdate": "2026-08-30T13:19:40Z",
                          "activeAlertLevels": [
                              {"alertLevel": "Red", "createdAt": "not a stamp"}, "junk"]}],
    }])
    source = _source(SequenceTransport([body]))
    events = source.poll()
    assert events[0].ts_source.isoformat() == "2026-08-30T13:19:40+00:00"


def _two_alerts_with_levels(name: str, first: str, first_level: tuple[str, str],
                            second: str, second_level: tuple[str, str]) -> str:
    """Two `AIR` alerts on one region, each with one level record."""
    def alert(start: str, level: tuple[str, str]) -> dict[str, object]:
        return {"regionId": "1284", "regionType": "Community", "type": "AIR",
                "lastUpdate": start,
                "activeAlertLevels": [{"alertLevel": level[0], "reason": "",
                                       "createdAt": level[1]}]}
    return json.dumps([{
        "regionId": "1284", "regionType": "Community", "regionName": name,
        "lastUpdate": second,
        "activeAlerts": [alert(first, first_level), alert(second, second_level)],
    }])


def test_the_active_row_carries_the_newest_level_record_whatever_its_position() -> None:
    """D-050, the capture half. The level is the record with the newest
    `createdAt`, never the first or the last in the list: both orders were
    measured in one payload. The string is the API's own word, not mapped."""
    yellow, red, bumped = "2026-09-08T17:22:35Z", "2026-09-08T18:01:01Z", "2026-09-08T18:01:00Z"
    red_first = _source(SequenceTransport([_escalated(LVIV, yellow, red, bumped)])).poll()
    reversed_body = json.loads(_escalated(LVIV, yellow, red, bumped))
    reversed_body[0]["activeAlerts"][0]["activeAlertLevels"].reverse()
    yellow_first = _source(SequenceTransport([json.dumps(reversed_body)])).poll()
    for events in (red_first, yellow_first):
        assert [event.state for event in events] == [AlertState.ACTIVE]
        assert events[0].raw_fields["api_level"] == "Red"
        assert events[0].raw_fields["api_level_at"] == "2026-09-08T18:01:01+00:00"
        assert events[0].ts_source.isoformat() == "2026-09-08T17:22:35+00:00"


def test_an_alert_without_a_readable_level_puts_no_level_on_the_row() -> None:
    """No key rather than an empty one: a consumer must be able to tell a
    payload from before the field existed from a payload that says nothing."""
    events = _source(SequenceTransport([_snapshot((LVIV, "AIR"))])).poll()
    assert "api_level" not in events[0].raw_fields
    assert "api_level_at" not in events[0].raw_fields
    body = json.loads(_escalated(LVIV, "2026-09-08T17:22:35Z", "2026-09-08T18:01:01Z",
                                 "2026-09-08T18:01:00Z"))
    records = body[0]["activeAlerts"][0]["activeAlertLevels"]
    records[0]["createdAt"] = "not a stamp"
    records[1]["alertLevel"] = ""
    events = _source(SequenceTransport([json.dumps(body)])).poll()
    assert "api_level" not in events[0].raw_fields


def test_two_alerts_on_one_key_take_the_newest_level_across_both() -> None:
    """The fold (F147) keeps the earliest start; the level is the newest
    record across both alerts, so the row can begin at the first alert and
    wear the level of the second."""
    body = _two_alerts_with_levels(
        LVIV, "2026-09-08T17:00:00Z", ("Yellow", "2026-09-08T17:00:00Z"),
        "2026-09-08T18:00:00Z", ("Red", "2026-09-08T18:00:00Z"))
    source = _source(SequenceTransport([body]))
    events = source.poll()
    assert len(events) == 1
    assert events[0].ts_source.isoformat() == "2026-09-08T17:00:00+00:00"
    assert events[0].raw_fields["api_level"] == "Red"
    assert list(source.overlapping.values()) == [2]


def test_an_unknown_key_on_an_alert_or_a_level_record_is_counted_and_named() -> None:
    """The canary. `activeAlertLevels` arrived without announcement and
    changed a field's meaning (F148); the next key to arrive is printed on
    the day it lands, and a payload with only known keys counts nothing."""
    source = _source(SequenceTransport([_snapshot((LVIV, "AIR"))]))
    source.poll()
    assert source.unknown_keys == {}
    body = json.loads(_escalated(LVIV, "2026-09-08T17:22:35Z", "2026-09-08T18:01:01Z",
                                 "2026-09-08T18:01:00Z"))
    body[0]["activeAlerts"][0]["severity"] = 3
    body[0]["activeAlerts"][0]["activeAlertLevels"][0]["colour"] = "#f00"
    source = _source(SequenceTransport([json.dumps(body)]))
    source.poll()
    assert source.unknown_keys == {"activeAlertLevels.colour": 1, "severity": 1}
