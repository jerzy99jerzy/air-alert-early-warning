"""Append-only event store.

Transitions are stored, never snapshots: any past moment must be reconstructible
from the log, because the backtest and the live correlator run the same code
over the same rows.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mavo.errors import NaiveTimestamp, SchemaMismatch
from mavo.schema import (
    AlertState,
    AreaRole,
    KindEvent,
    KindState,
    Provenance,
    ThreatEvent,
    ThreatKind,
)

# Bumped whenever a column is added. A store written by an older version is
# refused rather than migrated: D-013 already says a re-reading is done by
# rebuilding from the raw corpus, so an in-place migration would invent values
# for columns the old rows never carried and the invented value would be
# indistinguishable from a measured one.
EXPECTED_KIND_COLUMNS = (
    "content_hash", "area_id", "oblast", "kind", "state",
    "ts_source", "ts_ingest", "source_id", "raw_fields",
)
EXPECTED_COLUMNS = (
    "content_hash", "area_id", "state", "ts_source", "ts_ingest",
    "source_id", "kind", "provenance", "raw_fields", "oblast", "role",
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    content_hash TEXT PRIMARY KEY,
    area_id      TEXT NOT NULL,
    state        TEXT NOT NULL,
    ts_source    TEXT NOT NULL,
    ts_ingest    TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    kind         TEXT NOT NULL,
    provenance   TEXT NOT NULL,
    raw_fields   TEXT NOT NULL,
    oblast       TEXT NOT NULL,
    role         TEXT NOT NULL
);

-- T16. The second stream, in its own table rather than a discriminator column
-- on the first. An alert and a declaration of a means of attack have different
-- lifetimes and different states; sharing a `state` column between them would
-- be the modelling error F25 recorded, expressed in SQL.
CREATE TABLE IF NOT EXISTS kind_events (
    content_hash TEXT PRIMARY KEY,
    area_id      TEXT NOT NULL,
    oblast       TEXT NOT NULL,
    kind         TEXT NOT NULL,
    state        TEXT NOT NULL,
    ts_source    TEXT NOT NULL,
    ts_ingest    TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    raw_fields   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_ts_source ON events (ts_source);
CREATE INDEX IF NOT EXISTS idx_events_area ON events (area_id, ts_source);
"""


def _stored_form(ts: datetime, label: str) -> str:
    """ISO text in UTC, refusing a timestamp that has no offset to normalize.

    ``replay`` orders by this text. Lexicographic order over ISO strings is
    chronological only when every string shares one offset, so every timestamp
    is normalized to UTC here, at the single point of entry, rather than trusted
    to arrive uniform. A naive datetime cannot be normalized without inventing
    an offset for it, which is why it is a refusal and not a repair (F52).
    """
    if ts.tzinfo is None:
        raise NaiveTimestamp(
            f"{label} has no UTC offset; the store orders lexicographically by ISO "
            "text, which is chronological only in one uniform offset"
        )
    return ts.astimezone(UTC).isoformat()


class EventStore:
    """SQLite-backed append-only log with idempotent writes."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn:
            conn.executescript(_SCHEMA)
            conn.commit()
            self._refuse_an_older_schema(conn)

    @staticmethod
    def _refuse_an_older_schema(conn: sqlite3.Connection) -> None:
        """Refuse a store whose columns predate this version.

        ``CREATE TABLE IF NOT EXISTS`` is silent about a table that already
        exists with fewer columns, so without this check an older store would
        open cleanly and then fail one row at a time, or worse, read back events
        with fields that were never written. The refusal names the missing
        columns and the remedy, which is a rebuild rather than a migration.
        """
        found = tuple(row[1] for row in conn.execute("PRAGMA table_info(events)"))
        missing = [column for column in EXPECTED_COLUMNS if column not in found]
        kind_found = tuple(row[1] for row in conn.execute("PRAGMA table_info(kind_events)"))
        missing += [
            f"kind_events.{column}"
            for column in EXPECTED_KIND_COLUMNS
            if column not in kind_found
        ]
        if missing:
            raise SchemaMismatch(
                f"store is missing column(s) {', '.join(missing)}; it was written by an "
                "older version. Rebuild it from the raw corpus rather than migrating "
                "it, so no row carries a value that was never observed (D-013)"
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def append(self, events: Iterable[ThreatEvent]) -> int:
        """Insert events, ignoring ones already present. Returns rows added.

        Idempotence is by content hash, so re-polling a feed that repeats an
        unchanged transition costs nothing and corrupts nothing.
        """
        rows = [
            (
                event.content_hash(),
                event.area_id,
                event.state.value,
                _stored_form(event.ts_source, "ts_source"),
                _stored_form(event.ts_ingest, "ts_ingest"),
                event.source_id,
                event.kind.value,
                event.provenance.name,
                json.dumps(event.raw_fields, sort_keys=True),
                event.oblast,
                event.role.value,
            )
            for event in events
        ]
        if not rows:
            return 0
        with closing(self._connect()) as conn:
            before = conn.total_changes
            conn.executemany(
                "INSERT OR IGNORE INTO events (content_hash, area_id, state, ts_source, "
                "ts_ingest, source_id, kind, provenance, raw_fields, oblast, role) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            return conn.total_changes - before

    #: Rows read per connection by the streaming readers. Large enough that a
    #: replay of any store this project has produced is one or two round trips,
    #: small enough that a chunk is never a materialisation of the whole log.
    CHUNK = 500

    def _chunks(
        self, columns: str, table: str
    ) -> Iterator[tuple[tuple[Any, ...], ...]]:
        """Rows in ``(ts_source, area_id)`` order, a connection per chunk.

        **F94.** The readers below used to hold one connection open across
        every ``yield``. A caller that started the iterator and did not finish
        it - ``next()`` once, an early ``break``, storing it for later - left
        the connection open for as long as it held the generator, and garbage
        collection did not reliably take it back: measured 2026-08-11, 201
        descriptors for 100 started-and-retained iterators, of which 102 were
        still held after ``del`` and an explicit ``gc.collect()``.

        Keyset pagination rather than ``LIMIT``/``OFFSET``: resuming from the
        last key read cannot skip or repeat a row the way an offset can when a
        write lands between chunks. What it can do is include a row appended
        mid-replay, which the single-connection version could do as well -
        neither took a transaction - so this is not a change in that guarantee,
        only a change in how long a file handle lives.

        The key is ``(ts_source, area_id, content_hash)``, and the third
        column is load-bearing. The schema is unique on ``content_hash``
        alone; ``(ts_source, area_id)`` legitimately ties, because one message
        can clear an area and list the same area as still under alert (T37) -
        two rows, one timestamp. A strict comparison on the tied pair drops
        whichever row the chunk boundary cuts off, and the dropped row can be
        the one saying the area is still dangerous. The hash also makes the
        order within a tie a property of the content rather than of insertion,
        so two stores rebuilt from the same corpus replay identically.
        """
        last: tuple[Any, Any, Any] | None = None
        while True:
            with closing(self._connect()) as conn:
                if last is None:
                    cursor = conn.execute(
                        f"SELECT {columns}, content_hash FROM {table} "  # noqa: S608
                        "ORDER BY ts_source, area_id, content_hash LIMIT ?",
                        (self.CHUNK,),
                    )
                else:
                    cursor = conn.execute(
                        f"SELECT {columns}, content_hash FROM {table} "  # noqa: S608
                        "WHERE (ts_source, area_id, content_hash) > (?, ?, ?) "
                        "ORDER BY ts_source, area_id, content_hash LIMIT ?",
                        (last[0], last[1], last[2], self.CHUNK),
                    )
                rows = tuple(cursor.fetchall())
            if not rows:
                return
            yield rows
            if len(rows) < self.CHUNK:
                return
            tail = rows[-1]
            ts_at, area_at = (
                (self._KIND_TS_SOURCE, self._KIND_AREA_ID)
                if table == "kind_events"
                else (self._TS_SOURCE, self._AREA_ID)
            )
            # content_hash is appended by `_chunks` itself as the final SELECT
            # column, so its position is `-1` for either table and the reader's
            # own column indices are untouched.
            last = (tail[ts_at], tail[area_at], tail[-1])

    # Column positions of the sort key inside the SELECT lists below. Named
    # rather than written as literals at the point of use, because a reordered
    # SELECT would otherwise page from the wrong column and lose rows silently.
    _AREA_ID = 0
    _TS_SOURCE = 2
    _KIND_AREA_ID = 0
    _KIND_TS_SOURCE = 4

    def replay(self) -> Iterator[ThreatEvent]:
        """Yield every stored event in source-time order.

        Still an iterator, and still not a materialisation of the whole log:
        rows are read a chunk at a time (see ``_chunks``), so an abandoned
        replay costs one chunk of tuples and no open connection.
        """
        for rows in self._chunks(
            "area_id, state, ts_source, ts_ingest, source_id, kind, "
            "provenance, raw_fields, oblast, role",
            "events",
        ):
            for row in rows:
                yield ThreatEvent(
                    area_id=row[0],
                    state=AlertState(row[1]),
                    ts_source=datetime.fromisoformat(row[2]),
                    ts_ingest=datetime.fromisoformat(row[3]),
                    source_id=row[4],
                    kind=ThreatKind(row[5]),
                    provenance=Provenance[row[6]],
                    raw_fields=json.loads(row[7]),
                    oblast=row[8],
                    role=AreaRole(row[9]),
                )

    def count(self) -> int:
        """Number of stored events."""
        with closing(self._connect()) as conn:
            result: int = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            return result

    def append_kinds(self, events: Iterable[KindEvent]) -> int:
        """Persist declarations and liftings. Idempotent by content hash, as alerts are."""
        rows = [
            (
                event.content_hash,
                event.area_id,
                event.oblast,
                event.kind.value,
                event.state.value,
                _stored_form(event.ts_source, "ts_source"),
                _stored_form(event.ts_ingest, "ts_ingest"),
                event.source_id,
                json.dumps(event.raw_fields, sort_keys=True),
            )
            for event in events
        ]
        if not rows:
            return 0
        with closing(self._connect()) as conn:
            before = conn.execute("SELECT COUNT(*) FROM kind_events").fetchone()[0]
            conn.executemany(
                "INSERT OR IGNORE INTO kind_events (content_hash, area_id, oblast, kind, "
                "state, ts_source, ts_ingest, source_id, raw_fields) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            after = conn.execute("SELECT COUNT(*) FROM kind_events").fetchone()[0]
        return int(after - before)

    def replay_kinds(self) -> Iterator[KindEvent]:
        """Every declaration in source order, for building a `KindIndex`.

        Chunked for the same reason as ``replay`` (F94); the sort key sits at a
        different column here, which is why the positions are named constants.
        """
        for rows in self._chunks(
            "area_id, oblast, kind, state, ts_source, ts_ingest, "
            "source_id, raw_fields",
            "kind_events",
        ):
            for row in rows:
                yield KindEvent(
                    area_id=row[0],
                    oblast=row[1],
                    kind=ThreatKind(row[2]),
                    state=KindState(row[3]),
                    ts_source=datetime.fromisoformat(row[4]),
                    ts_ingest=datetime.fromisoformat(row[5]),
                    source_id=row[6],
                    raw_fields=json.loads(row[7]),
                )
