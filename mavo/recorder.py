"""Record one week of the production store as a fixture (D-058).

The timeline's agreement test runs on a week the store recorded, not on one
written for the test: fixtures chosen by the implementation are a class this
project has logged again and again (F173, F176, F185). This module is how that
week leaves the host, and it is a `mavo` subcommand because its input is the
store (D-038): `mavo record-week STORE OUT END [DAYS]`. It imports nothing
from this package, so the host's own interpreter can run the same file before
the release that carries it is installed, read-only on the store:

    sudo /usr/bin/python3 - /var/lib/mavo/events OUT.sqlite3 END [DAYS] < mavo/recorder.py

**What it copies is what the week's check reads, and nothing else.** For the
window `(END - DAYS, END]`:

- events: per `(area_id, kind)`, every row at the newest source stamp at or
  before the window's start, which holds the winner of the fold there with its
  ties; then every row stamped inside the window. Nothing older can win again,
  and nothing later is inside the file.
- lists: for the two addresses the timeline reads (`MAP_LISTS`), the newest
  list at or before the start and every list recorded inside the window; then
  the communiques, zones and outlines they name. The other RSO categories are
  read by nothing the timeline does, and their lists churn with every water
  level and road notice, so they stay behind.
- polls: per feed, the first ever (where the record starts); per address, the
  newest poll, read and refusal at or before the start; every poll inside the
  window.

The stream tables (`kind_events`, `alert_levels`, `strike_tallies`) are not
read by the timeline and are copied empty. The schema is the store's own, read
from `sqlite_master`, so the fixture opens as the store it came from.

Prints one JSON line: the window, the rows per table, the file's size.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

#: The feed whose lists name communiques, and the feed whose lists name zones.
COMMUNIQUE_FEED = "rso"
ZONE_FEED = "pansa"

#: The addresses whose lists the timeline reads: the communique scope that may
#: paint the map (`poland.WARNINGS_URL`) and the updated plan
#: (`pansa.SOURCE_URL`). Written out because this module imports nothing from
#: the package; `tests/test_timeline.py` holds them equal to the originals.
MAP_LISTS: tuple[tuple[str, str], ...] = (
    (COMMUNIQUE_FEED, "https://komunikaty.tvp.pl/komunikatyxml/wszystkie/ogolne/0?_format=xml"),
    (ZONE_FEED, "https://airspace.pansa.pl/map-configuration/uup"),
)


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat()


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})")]


def _copy(source: sqlite3.Connection, target: sqlite3.Connection, table: str,
          where: str, values: tuple[object, ...], order: str) -> int:
    names = ", ".join(_columns(source, table))
    rows = source.execute(
        f"SELECT {names} FROM {table} WHERE {where} ORDER BY {order}", values
    ).fetchall()
    marks = ", ".join("?" for _ in _columns(source, table))
    target.executemany(f"INSERT OR IGNORE INTO {table} ({names}) VALUES ({marks})", rows)
    return len(rows)


def _named(source: sqlite3.Connection, target: sqlite3.Connection, table: str,
           digests: set[str]) -> int:
    copied = 0
    ordered = sorted(digests)
    for index in range(0, len(ordered), 500):
        chunk = ordered[index:index + 500]
        marks = ", ".join("?" for _ in chunk)
        copied += _copy(source, target, table, f"digest IN ({marks})", tuple(chunk), "digest")
    return copied


def record(source_path: Path, target_path: Path, end: datetime, days: int) -> dict[str, object]:
    """Write the fixture and return what it holds."""
    if target_path.exists():
        raise FileExistsError(f"{target_path} exists; a fixture is written once")
    start = end - timedelta(days=days)
    s, e = _iso(start), _iso(end)
    source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
    target = sqlite3.connect(target_path)
    counts: dict[str, int] = {}
    try:
        for kind in ("table", "index"):
            for (sql,) in source.execute(
                "SELECT sql FROM sqlite_master WHERE type = ? AND sql IS NOT NULL "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name", (kind,)
            ):
                target.execute(str(sql))

        counts["events"] = _copy(
            source, target, "events",
            "rowid IN (SELECT e.rowid FROM events AS e JOIN ("
            " SELECT area_id, kind, MAX(ts_source) AS newest FROM events"
            " WHERE ts_source <= ? GROUP BY area_id, kind) AS m"
            " ON e.area_id = m.area_id AND e.kind = m.kind AND e.ts_source = m.newest)"
            " OR (ts_source > ? AND ts_source <= ?)",
            (s, s, e), "ts_source, area_id, content_hash",
        )

        snapshots = 0
        members: dict[str, set[str]] = {COMMUNIQUE_FEED: set(), ZONE_FEED: set()}
        for feed, url in MAP_LISTS:
            rows = source.execute(
                "SELECT rowid FROM feed_snapshots WHERE feed = ? AND url = ?"
                " AND observed_at <= ? ORDER BY observed_at DESC, rowid DESC LIMIT 1",
                (feed, url, s),
            ).fetchall()
            wanted = [row[0] for row in rows]
            wanted += [row[0] for row in source.execute(
                "SELECT rowid FROM feed_snapshots WHERE feed = ? AND url = ?"
                " AND observed_at > ? AND observed_at <= ?", (feed, url, s, e))]
            if not wanted:
                continue
            marks = ", ".join("?" for _ in wanted)
            snapshots += _copy(source, target, "feed_snapshots", f"rowid IN ({marks})",
                               tuple(wanted), "observed_at, rowid")
            for (listed,) in source.execute(
                f"SELECT members FROM feed_snapshots WHERE rowid IN ({marks})", tuple(wanted)
            ):
                members[feed].update(json.loads(listed))
        counts["feed_snapshots"] = snapshots
        counts["communiques"] = _named(source, target, "communiques", members[COMMUNIQUE_FEED])
        counts["airspace_zones"] = _named(source, target, "airspace_zones", members[ZONE_FEED])
        outlines = {str(row[0]) for row in target.execute("SELECT geometry FROM airspace_zones")}
        counts["airspace_geometries"] = _named(source, target, "airspace_geometries", outlines)

        attempts: set[int] = set()
        for (feed,) in source.execute("SELECT DISTINCT feed FROM feed_attempts").fetchall():
            first = source.execute(
                "SELECT rowid FROM feed_attempts WHERE feed = ?"
                " ORDER BY started_at ASC, rowid ASC LIMIT 1", (feed,)).fetchone()
            if first is not None:
                attempts.add(int(first[0]))
        for feed, url in source.execute(
            "SELECT DISTINCT feed, url FROM feed_attempts").fetchall():
            for outcome in (None, "read", "refused"):
                clause = "" if outcome is None else " AND outcome = ?"
                values: tuple[object, ...] = (feed, url, s) + (() if outcome is None
                                                             else (outcome,))
                row = source.execute(
                    "SELECT rowid FROM feed_attempts WHERE feed = ? AND url = ?"
                    f" AND started_at <= ?{clause}"
                    " ORDER BY started_at DESC, rowid DESC LIMIT 1", values).fetchone()
                if row is not None:
                    attempts.add(int(row[0]))
        attempts.update(int(row[0]) for row in source.execute(
            "SELECT rowid FROM feed_attempts WHERE started_at > ? AND started_at <= ?", (s, e)))
        copied = 0
        ordered = sorted(attempts)
        for index in range(0, len(ordered), 500):
            chunk = ordered[index:index + 500]
            marks = ", ".join("?" for _ in chunk)
            copied += _copy(source, target, "feed_attempts", f"rowid IN ({marks})",
                            tuple(chunk), "started_at, rowid")
        counts["feed_attempts"] = copied
        target.commit()
        target.execute("VACUUM")
    finally:
        source.close()
        target.close()
    return {"end": e, "start": s, "days": days, "rows": counts,
            "bytes": target_path.stat().st_size}


def main(argv: Sequence[str] | None = None) -> int:
    """`mavo record-week STORE OUT END [DAYS]`, or the same run from stdin."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in (3, 4):
        print("usage: mavo record-week STORE OUT END [DAYS]", file=sys.stderr)
        return 2
    try:
        end = datetime.fromisoformat(args[2])
        days = int(args[3]) if len(args) == 4 else 7
    except ValueError as failure:
        print(f"record-week: {failure}", file=sys.stderr)
        return 2
    if end.tzinfo is None or days < 1:
        print("record-week: END needs an offset and DAYS must be at least 1",
              file=sys.stderr)
        return 2
    try:
        summary = record(Path(args[0]), Path(args[1]), end.astimezone(UTC), days)
    except FileExistsError as failure:
        print(f"record-week: {failure}", file=sys.stderr)
        return 2
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
