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


def test_the_masked_direction_is_named_and_never_written(
    tmp_path: Path, capsys: object
) -> None:
    """An area the snapshot holds whose newest row is not an API ACTIVE."""
    store_path = tmp_path / "events"
    snap = tmp_path / "snap.json"
    store = _seed(store_path, api_row_for_live=False)
    _snapshot(snap, age=timedelta(seconds=30), areas=[AREA_LIVE])
    code = main(["reconcile", "--store", str(store_path), "--snapshot", str(snap),
                 "--apply"])
    out = capsys.readouterr().out  # type: ignore[attr-defined]
    assert code == 0
    assert f"MASKED {AREA_LIVE}" in out
    assert f"close {AREA_LIVE}" not in out
    assert all(e.area_id != AREA_LIVE or e.source_id != "reconcile"
               for e in store.replay())
