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
    assert events[0].kind is ThreatKind.MISSILE
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
    assert [entry["kind"] for entry in payload["areas"]] == ["MISSILE"]
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
