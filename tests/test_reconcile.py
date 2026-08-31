"""`mavo reconcile`: closures the snapshot licenses, and the census it refuses.

Twelve channel-era ACTIVE rows were rendering on 2026-08-30 for areas the
API's two-minute full-state snapshots had not mentioned once since the
switchover. D-041 names the licence: fresh snapshot, area absent. These pin
the command to it: a stale snapshot examines nothing, membership protects a
live alarm from closure, the masked direction is printed and never written,
and a second apply writes nothing.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mavo.cli import main
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind
from mavo.store import EventStore

AREA_GHOST = "UA65020000000032929"   # Beryslav raion, a real ghost of 2026-08-30
AREA_LIVE = "UA14020000000013572"    # Bakhmut raion, alerting via API in the same reading


def _seed(path: Path, *, api_row_for_live: bool = True) -> EventStore:
    store = EventStore(path)
    old = datetime(2026, 8, 29, 2, 19, 49, tzinfo=UTC)
    store.append([
        ThreatEvent(AREA_GHOST, AlertState.ACTIVE, old, old, "telegram",
                    kind=ThreatKind.UNKNOWN, oblast="khersonska"),
        ThreatEvent(AREA_LIVE, AlertState.ACTIVE, old, old, "telegram",
                    kind=ThreatKind.UNKNOWN, oblast="donetska"),
    ])
    if api_row_for_live:
        newer = datetime(2026, 8, 30, 15, 30, 0, tzinfo=UTC)
        store.append([
            ThreatEvent(AREA_LIVE, AlertState.ACTIVE, newer, newer, "ukrainealarm",
                        kind=ThreatKind.UNKNOWN, oblast="donetska"),
        ])
    return store


def _snapshot(path: Path, *, age: timedelta, areas: list[str]) -> None:
    saved = datetime.now(UTC) - age
    path.write_text(json.dumps({
        "saved_at": saved.isoformat(),
        "areas": [
            {"area": area, "kind": "UNKNOWN", "began": saved.isoformat(), "oblast": ""}
            for area in areas
        ],
    }), encoding="utf-8")


def test_dry_run_closes_only_the_absent_and_writes_nothing(
    tmp_path: Path, capsys: object
) -> None:
    store_path = tmp_path / "events"
    snap = tmp_path / "snap.json"
    store = _seed(store_path)
    _snapshot(snap, age=timedelta(seconds=30), areas=[AREA_LIVE])
    code = main(["reconcile", "--store", str(store_path), "--snapshot", str(snap)])
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert code == 0
    assert "ghosts=1" in out and AREA_GHOST in out
    assert f"close {AREA_LIVE}" not in out
    assert "nothing written" in out
    assert store.count() == 3


def test_apply_writes_the_closure_and_is_idempotent(tmp_path: Path) -> None:
    store_path = tmp_path / "events"
    snap = tmp_path / "snap.json"
    store = _seed(store_path)
    _snapshot(snap, age=timedelta(seconds=30), areas=[AREA_LIVE])
    argv = ["reconcile", "--store", str(store_path), "--snapshot", str(snap), "--apply"]
    assert main(argv) == 0
    closures = [e for e in store.replay() if e.source_id == "reconcile"]
    assert [e.area_id for e in closures] == [AREA_GHOST]
    assert closures[0].state is AlertState.CLEAR
    assert closures[0].provenance is Provenance.INFERENCE
    before = store.count()
    assert main(argv) == 0
    assert store.count() == before, "a second apply must store nothing"


def test_a_stale_snapshot_examines_nothing(tmp_path: Path, capsys: object) -> None:
    store_path = tmp_path / "events"
    snap = tmp_path / "snap.json"
    store = _seed(store_path)
    _snapshot(snap, age=timedelta(seconds=3600), areas=[])
    code = main(["reconcile", "--store", str(store_path), "--snapshot", str(snap),
                 "--apply"])
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert code == 3
    assert "SNAPSHOT-STALE" in out
    assert all(e.source_id != "reconcile" for e in store.replay())


def test_a_live_row_on_a_reported_kind_is_neither_closed_nor_unmasked(
    tmp_path: Path, capsys: object
) -> None:
    """D-044 narrowed what "masked" means, and this pins the narrowing.

    Until 0.48.0.0 an area was called masked when its newest row was not an API
    ACTIVE, which counted an area held up by a live *channel* row on exactly the
    kind the snapshot reports. That is a provenance concern - the row's author
    has stopped publishing - and not a masking one: the area renders, correctly,
    as alerting. Masked now means what it says, per kind: the snapshot reports
    this key and the store's newest row for it is a clear, or there is no row.

    Neither command touches this area. Closing it is forbidden by membership,
    and unmasking it would write an INFERENCE row over a REPORTED one that
    already says the same thing.
    """
    store_path = tmp_path / "events"
    snap = tmp_path / "snap.json"
    store = _seed(store_path, api_row_for_live=False)
    _snapshot(snap, age=timedelta(seconds=30), areas=[AREA_LIVE])
    code = main(["reconcile", "--store", str(store_path), "--snapshot", str(snap),
                 "--unmask", "--apply"])
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert code == 0
    assert "masked=0" in out
    assert f"close {AREA_LIVE}" not in out
    assert f"unmask {AREA_LIVE}" not in out
    assert all(e.area_id != AREA_LIVE or e.source_id != "reconcile"
               for e in store.replay())


def test_the_masked_direction_is_named_and_never_written_without_unmask(
    tmp_path: Path, capsys: object
) -> None:
    """The census still refuses to write unless asked, and says what it found."""
    store_path = tmp_path / "events"
    snap = tmp_path / "snap.json"
    store = EventStore(store_path)
    old = datetime(2026, 8, 29, 2, 19, 49, tzinfo=UTC)
    cleared = datetime(2026, 8, 30, 16, 46, 38, tzinfo=UTC)
    store.append([
        ThreatEvent(AREA_LIVE, AlertState.ACTIVE, old, old, "ukrainealarm",
                    kind=ThreatKind.UNKNOWN, oblast="donetska"),
        ThreatEvent(AREA_LIVE, AlertState.CLEAR, cleared, cleared, "ukrainealarm",
                    kind=ThreatKind.UNKNOWN, oblast="donetska"),
    ])
    _snapshot(snap, age=timedelta(seconds=30), areas=[AREA_LIVE])
    before = store.count()
    code = main(["reconcile", "--store", str(store_path), "--snapshot", str(snap),
                 "--apply"])
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert code == 0
    assert "masked=1" in out
    assert f"MASKED {AREA_LIVE}" in out
    assert store.count() == before
