"""D-044. An area present in a fresh snapshot never renders as calm.

Written before the code they cover, against the shape the API and the channel
actually produced on 2026-08-30 rather than against the implementation. The two
populations measured that day appear here by name: the thirteen whose live kind
came only from a `telegram` row after their API kind was cleared by a mapping
change, and the two carrying a chronic artillery alarm under an air alert that
ended.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.report import compose, to_contract
from mavo.schema import (
    AlertState,
    AreaRole,
    Provenance,
    ThreatEvent,
    ThreatKind,
    redate_reassertions,
    state_precedence,
)
from mavo.store import EventStore
from tests.test_sprint11 import _page as channel_page

APRIL = datetime(2026, 4, 19, 20, 19, 35, tzinfo=UTC)
NOON = datetime(2026, 8, 30, 12, 0, 0, tzinfo=UTC)


def event(
    area: str,
    state: AlertState,
    kind: ThreatKind,
    ts: datetime,
    source: str = "ukrainealarm",
    ingest: datetime | None = None,
    raw: dict[str, object] | None = None,
) -> ThreatEvent:
    return ThreatEvent(
        area_id=area,
        state=state,
        ts_source=ts,
        ts_ingest=ingest if ingest is not None else ts,
        source_id=source,
        kind=kind,
        provenance=Provenance.REPORTED,
        raw_fields=raw if raw is not None else {},
        oblast="Донецька",
        role=AreaRole.SUBJECT,
    )


# --------------------------------------------------------------------------
# Part 1: the fold
# --------------------------------------------------------------------------


def test_chronic_kind_survives_a_concurrent_kind_clearing() -> None:
    """The measured case of "the 2": artillery since April, air alert ends.

    Before D-044 the CLEAR carried the newer stamp, won the area-level fold and
    erased an alarm that had been running for four months.
    """
    log = [
        event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL),
        event("UA14", AlertState.ACTIVE, ThreatKind.UNKNOWN, NOON),
        event("UA14", AlertState.CLEAR, ThreatKind.UNKNOWN, NOON + timedelta(minutes=45)),
    ]
    report = compose(log, as_of=NOON + timedelta(hours=1))
    assert [p.area_id for p in report.areas] == ["UA14"]
    picture = report.areas[0]
    assert picture.state is AlertState.ACTIVE
    # The ended kind is gone from the standings; the chronic one is not.
    assert [s.kind for s in picture.kinds] == [ThreatKind.ARTILLERY]
    assert picture.kind is ThreatKind.ARTILLERY
    assert picture.since == APRIL


def test_area_leaves_only_when_every_kind_is_clear() -> None:
    log = [
        event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL),
        event("UA14", AlertState.ACTIVE, ThreatKind.UNKNOWN, NOON),
        event("UA14", AlertState.CLEAR, ThreatKind.UNKNOWN, NOON + timedelta(minutes=45)),
        event("UA14", AlertState.CLEAR, ThreatKind.ARTILLERY, NOON + timedelta(minutes=50)),
    ]
    report = compose(log, as_of=NOON + timedelta(hours=1))
    assert report.areas == ()


def test_live_kind_from_a_second_source_holds_the_area() -> None:
    """The measured case of "the 13": the API kind cleared, a channel kind live."""
    log = [
        event("UA12", AlertState.ACTIVE, ThreatKind.MISSILE, NOON, source="telegram"),
        event("UA12", AlertState.ACTIVE, ThreatKind.UNKNOWN, NOON + timedelta(minutes=1)),
        event("UA12", AlertState.CLEAR, ThreatKind.UNKNOWN, NOON + timedelta(minutes=30)),
    ]
    report = compose(log, as_of=NOON + timedelta(hours=1))
    assert [p.area_id for p in report.areas] == ["UA12"]
    assert report.areas[0].state is AlertState.ACTIVE
    assert [s.kind for s in report.areas[0].kinds] == [ThreatKind.MISSILE]


def test_headline_is_the_loudest_live_kind_not_the_newest() -> None:
    """1a. UNKNOWN raised after ACTIVE must not become the area's word."""
    log = [
        event("UA63", AlertState.ACTIVE, ThreatKind.ARTILLERY, NOON),
        event("UA63", AlertState.UNKNOWN, ThreatKind.DRONE, NOON + timedelta(minutes=10)),
    ]
    picture = compose(log, as_of=NOON + timedelta(hours=1)).areas[0]
    assert picture.state is AlertState.ACTIVE
    assert picture.kind is ThreatKind.ARTILLERY
    assert picture.since == NOON
    # Both are published; only one is the headline.
    assert {s.kind for s in picture.kinds} == {ThreatKind.ARTILLERY, ThreatKind.DRONE}


def test_partial_clear_outranks_unknown_and_neither_clears_the_area() -> None:
    log = [
        event("UA63", AlertState.UNKNOWN, ThreatKind.DRONE, NOON),
        event("UA63", AlertState.PARTIAL_CLEAR, ThreatKind.MISSILE, NOON),
    ]
    picture = compose(log, as_of=NOON + timedelta(hours=1)).areas[0]
    assert picture.state is AlertState.PARTIAL_CLEAR
    assert state_precedence(AlertState.PARTIAL_CLEAR) > state_precedence(AlertState.UNKNOWN)


def test_single_kind_behaviour_is_unchanged() -> None:
    """The healthy case. Nothing about one kind per area may move."""
    log = [
        event("UA05", AlertState.ACTIVE, ThreatKind.MISSILE, NOON),
        event("UA46", AlertState.ACTIVE, ThreatKind.DRONE, NOON),
        event("UA46", AlertState.CLEAR, ThreatKind.DRONE, NOON + timedelta(minutes=20)),
    ]
    report = compose(log, as_of=NOON + timedelta(hours=1))
    assert [p.area_id for p in report.areas] == ["UA05"]
    assert report.areas[0].kind is ThreatKind.MISSILE
    assert report.areas[0].since == NOON


def test_store_and_picture_name_the_same_event(tmp_path: Path) -> None:
    """No second opinion. `newest_by_area` and `compose` must agree per area."""
    log = [
        event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL),
        event("UA14", AlertState.ACTIVE, ThreatKind.UNKNOWN, NOON),
        event("UA14", AlertState.CLEAR, ThreatKind.UNKNOWN, NOON + timedelta(minutes=45)),
        event("UA05", AlertState.ACTIVE, ThreatKind.MISSILE, NOON),
    ]
    store = EventStore(tmp_path / "events.db")
    store.append(log)
    named = {e.area_id: (e.state, e.kind, e.ts_source) for e in store.newest_by_area()}
    for picture in compose(log, as_of=NOON + timedelta(hours=1)).areas:
        assert named[picture.area_id] == (picture.state, picture.kind, picture.since)


def test_contract_publishes_every_live_kind() -> None:
    log = [
        event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL),
        event("UA14", AlertState.UNKNOWN, ThreatKind.DRONE, NOON),
        event("UA14", AlertState.CLEAR, ThreatKind.MISSILE, NOON),
    ]
    payload = to_contract(compose(log, as_of=NOON + timedelta(hours=1)))
    area = payload["areas"][0]  # type: ignore[index]
    kinds = {entry["kind"] for entry in area["kinds"]}  # type: ignore[index]
    assert kinds == {"artillery", "drone"}
    # A cleared kind leaves the block for the same reason a cleared area leaves
    # the list, and the headline is always drawn from what is published.
    assert "missile" not in kinds
    assert area["kind"] in kinds  # type: ignore[index]
    assert json.dumps(payload)  # the whole payload stays serialisable


# --------------------------------------------------------------------------
# Part 2: redating a re-assertion
# --------------------------------------------------------------------------


def test_reassertion_after_a_spurious_clear_is_dated_by_observation() -> None:
    reasserted = event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL)
    cleared_at = NOON
    observed = NOON + timedelta(minutes=2)
    (row,) = redate_reassertions(
        [reasserted], {("UA14", ThreatKind.ARTILLERY): cleared_at}, observed
    )
    assert row.ts_source == observed
    assert row.raw_fields["reported_at"] == APRIL.isoformat()
    assert row.raw_fields["superseded_clear"] == cleared_at.isoformat()
    # And the whole point: it can now land at all.
    original = event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL)
    assert row.content_hash() != original.content_hash()


def test_a_healthy_activation_is_left_alone() -> None:
    fresh = event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, NOON)
    (row,) = redate_reassertions(
        [fresh],
        {("UA14", ThreatKind.ARTILLERY): NOON - timedelta(hours=3)},
        NOON + timedelta(minutes=1),
    )
    assert row is fresh


def test_no_stored_clear_leaves_the_stamp_alone() -> None:
    fresh = event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL)
    (row,) = redate_reassertions([fresh], {}, NOON)
    assert row is fresh


def test_clears_are_never_redated() -> None:
    closing = event("UA14", AlertState.CLEAR, ThreatKind.ARTILLERY, APRIL)
    (row,) = redate_reassertions(
        [closing], {("UA14", ThreatKind.ARTILLERY): NOON}, NOON + timedelta(minutes=1)
    )
    assert row is closing


def test_redating_is_per_kind_not_per_area() -> None:
    """A clear on one kind must not re-date an activation on another."""
    other = event("UA14", AlertState.ACTIVE, ThreatKind.DRONE, APRIL)
    (row,) = redate_reassertions(
        [other], {("UA14", ThreatKind.ARTILLERY): NOON}, NOON + timedelta(minutes=1)
    )
    assert row is other


def test_the_log_source_is_not_redated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Re-dating is for snapshot sources only, and this pins the boundary.

    A page carrying an activation and a later all-clear for one area must store
    the same two rows however many times it is read. The first draft of D-044
    ran the re-dating on this collector too, and the alert rose again on every
    re-poll: the log grew, and an ended alarm came back. `redate_reassertions`
    is a correct answer to a question a log source is not asking.
    """
    from mavo.cli import main

    page = tmp_path / "page.html"
    page.write_text(channel_page(), encoding="utf-8")
    db = tmp_path / "events.db"
    assert main(["collect", "--stub", str(page), "--store", str(db)]) == 0
    first = EventStore(db).count()
    assert first > 0
    assert main(["collect", "--stub", str(page), "--store", str(db)]) == 0
    assert EventStore(db).count() == first
    capsys.readouterr()


def test_redating_is_pure() -> None:
    """Same arguments, same answer, no clock and no store."""
    batch = [event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL)]
    clears = {("UA14", ThreatKind.ARTILLERY): NOON}
    first = redate_reassertions(batch, clears, NOON + timedelta(minutes=1))
    second = redate_reassertions(batch, clears, NOON + timedelta(minutes=1))
    assert first == second
    assert batch[0].ts_source == APRIL  # the input is untouched


def test_redated_row_wins_the_fold_against_the_clear_it_supersedes() -> None:
    """The end-to-end property parts 1 and 2 exist for."""
    stored_clear = event("UA14", AlertState.CLEAR, ThreatKind.ARTILLERY, NOON)
    reasserted = redate_reassertions(
        [event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL)],
        {("UA14", ThreatKind.ARTILLERY): NOON},
        NOON + timedelta(minutes=2),
    )
    report = compose([stored_clear, *reasserted], as_of=NOON + timedelta(hours=1))
    assert [p.area_id for p in report.areas] == ["UA14"]
    assert report.areas[0].state is AlertState.ACTIVE


# --------------------------------------------------------------------------
# Part 2, storage
# --------------------------------------------------------------------------


def test_newest_clear_query_answers_per_kind(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events.db")
    store.append([
        event("UA14", AlertState.CLEAR, ThreatKind.ARTILLERY, NOON),
        event("UA14", AlertState.CLEAR, ThreatKind.ARTILLERY, NOON - timedelta(hours=2)),
        event("UA14", AlertState.ACTIVE, ThreatKind.DRONE, NOON),
        event("UA05", AlertState.CLEAR, ThreatKind.MISSILE, APRIL),
    ])
    answer = store.newest_clear_by_area_kind([
        ("UA14", ThreatKind.ARTILLERY),
        ("UA14", ThreatKind.DRONE),
        ("UA05", ThreatKind.MISSILE),
        ("UA99", ThreatKind.MISSILE),
    ])
    assert answer == {
        ("UA14", ThreatKind.ARTILLERY): NOON,
        ("UA05", ThreatKind.MISSILE): APRIL,
    }


def test_newest_clear_query_asks_nothing_for_an_empty_batch(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events.db")
    assert store.newest_clear_by_area_kind([]) == {}


# --------------------------------------------------------------------------
# Part 3: reconcile
# --------------------------------------------------------------------------


def write_snapshot(path: Path, saved_at: datetime, entries: list[tuple[str, str]]) -> None:
    path.write_text(
        json.dumps({
            "saved_at": saved_at.isoformat(),
            "areas": [
                {"area": area, "kind": kind, "began": APRIL.isoformat(),
                 "oblast": "Донецька"}
                for area, kind in entries
            ],
        }),
        encoding="utf-8",
    )


@pytest.fixture()
def masked_world(tmp_path: Path) -> tuple[Path, Path]:
    """The 2026-08-30 shape: one area masked, one true ghost."""
    store = EventStore(tmp_path / "events.db")
    store.append([
        # Masked: the snapshot reports UA14/ARTILLERY, the store's newest row
        # for that key is a clear.
        event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, APRIL),
        event("UA14", AlertState.CLEAR, ThreatKind.ARTILLERY, NOON),
        # A true ghost: a channel ACTIVE on an area the snapshot does not hold.
        event("UA99", AlertState.ACTIVE, ThreatKind.MISSILE, APRIL, source="telegram"),
    ])
    snapshot = tmp_path / "snapshot.json"
    write_snapshot(snapshot, datetime.now(UTC), [("UA14", "ARTILLERY")])
    return tmp_path / "events.db", snapshot


def run(argv: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    from mavo.cli import main

    code = main(argv)
    return code, capsys.readouterr().out


def test_unmask_raises_the_masked_area(
    masked_world: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    db, snapshot = masked_world
    code, out = run(
        ["reconcile", "--store", str(db), "--snapshot", str(snapshot),
         "--unmask", "--apply"],
        capsys,
    )
    assert code == 0
    assert "masked=1" in out
    store = EventStore(db)
    picture = compose(store.replay(), as_of=datetime.now(UTC))
    assert "UA14" in {p.area_id for p in picture.areas}


def test_unmask_is_idempotent(
    masked_world: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    db, snapshot = masked_world
    argv = ["reconcile", "--store", str(db), "--snapshot", str(snapshot),
            "--unmask", "--apply"]
    run(argv, capsys)
    before = EventStore(db).count()
    code, out = run(argv, capsys)
    assert code == 0
    assert EventStore(db).count() == before
    assert "masked=0" in out


def test_dry_run_writes_nothing(
    masked_world: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    db, snapshot = masked_world
    before = EventStore(db).count()
    code, out = run(
        ["reconcile", "--store", str(db), "--snapshot", str(snapshot),
         "--unmask", "--dry-run"],
        capsys,
    )
    assert code == 0
    assert EventStore(db).count() == before
    assert "nothing written" in out


def test_ghost_test_is_per_kind(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A stale channel kind on an area the API reports under another kind."""
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.append([
        event("UA12", AlertState.ACTIVE, ThreatKind.MISSILE, APRIL, source="telegram"),
    ])
    snapshot = tmp_path / "snapshot.json"
    write_snapshot(snapshot, datetime.now(UTC), [("UA12", "UNKNOWN")])
    code, out = run(
        ["reconcile", "--store", str(db), "--snapshot", str(snapshot),
         "--unmask", "--apply"],
        capsys,
    )
    assert code == 0
    assert "ghosts=1" in out and "masked=1" in out
    # Closed per kind, and the area did not go dark: the snapshot's own kind
    # was written in the same breath.
    areas = compose(EventStore(db).replay(), as_of=datetime.now(UTC)).areas
    picture = next(p for p in areas if p.area_id == "UA12")
    assert [s.kind for s in picture.kinds] == [ThreatKind.UNKNOWN]


def test_closing_a_contested_ghost_without_unmask_is_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The gate. Closing alone would take a live area dark."""
    db = tmp_path / "events.db"
    EventStore(db).append([
        event("UA12", AlertState.ACTIVE, ThreatKind.MISSILE, APRIL, source="telegram"),
    ])
    snapshot = tmp_path / "snapshot.json"
    write_snapshot(snapshot, datetime.now(UTC), [("UA12", "UNKNOWN")])
    before = EventStore(db).count()
    code, out = run(
        ["reconcile", "--store", str(db), "--snapshot", str(snapshot), "--apply"],
        capsys,
    )
    assert code == 4
    assert "[REFUSED]" in out
    assert EventStore(db).count() == before


def test_a_stale_snapshot_licenses_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "events.db"
    EventStore(db).append([event("UA14", AlertState.CLEAR, ThreatKind.ARTILLERY, NOON)])
    snapshot = tmp_path / "snapshot.json"
    write_snapshot(
        snapshot, datetime.now(UTC) - timedelta(hours=2), [("UA14", "ARTILLERY")]
    )
    before = EventStore(db).count()
    code, out = run(
        ["reconcile", "--store", str(db), "--snapshot", str(snapshot),
         "--unmask", "--apply"],
        capsys,
    )
    assert code == 3
    assert "SNAPSHOT-STALE" in out
    assert EventStore(db).count() == before


def test_reconcile_orders_two_kinds_on_one_area(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A total order over `(area, kind)`.

    `ThreatKind` is an Enum and Enums are unordered, so a tuple sort raises the
    moment two keys share an area. Every unit test above had one kind per area
    or areas that differed by the string part, so the tie never reached the
    enum; an end-to-end run on the 2026-08-30 shape did, with a TypeError.
    """
    db = tmp_path / "events.db"
    EventStore(db).append([
        event("UA14", AlertState.CLEAR, ThreatKind.ARTILLERY, NOON),
        event("UA14", AlertState.CLEAR, ThreatKind.DRONE, NOON),
    ])
    snapshot = tmp_path / "snapshot.json"
    write_snapshot(
        snapshot, datetime.now(UTC), [("UA14", "ARTILLERY"), ("UA14", "DRONE")]
    )
    code, out = run(
        ["reconcile", "--store", str(db), "--snapshot", str(snapshot),
         "--unmask", "--apply"],
        capsys,
    )
    assert code == 0
    assert "masked=2" in out
    picture = compose(EventStore(db).replay(), as_of=datetime.now(UTC)).areas[0]
    assert {s.kind for s in picture.kinds} == {ThreatKind.ARTILLERY, ThreatKind.DRONE}


def test_row_identity_carries_kind() -> None:
    """D-045. Two kinds asserted for one area at one instant are two rows.

    Under the D-013 identity they were one: the hash excluded `kind`, so the
    second row was silently discarded at the write boundary. That discard is
    the measured cause of the thirteen - the D-042 re-key emitted activations
    under the new kind that hashed identically to the pre-D-042 rows already
    stored - and it is what `--unmask` would trip over by construction, since
    every row it writes carries one `saved_at`.
    """
    artillery = event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, NOON)
    drone = event("UA14", AlertState.ACTIVE, ThreatKind.DRONE, NOON)
    assert artillery.content_hash() != drone.content_hash()
    # And a re-read of the same transition is still one row, which is the
    # property the identity exists for.
    again = event("UA14", AlertState.ACTIVE, ThreatKind.ARTILLERY, NOON,
                  ingest=NOON + timedelta(seconds=30))
    assert artillery.content_hash() == again.content_hash()
