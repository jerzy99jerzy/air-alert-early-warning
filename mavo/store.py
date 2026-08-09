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

from mavo.errors import NaiveTimestamp
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind

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
            )
            for event in events
        ]
        if not rows:
            return 0
        with closing(self._connect()) as conn:
            before = conn.total_changes
            conn.executemany(
                "INSERT OR IGNORE INTO events (content_hash, area_id, state, ts_source, "
                "ts_ingest, source_id, kind, provenance, raw_fields) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            return conn.total_changes - before

    def replay(self) -> Iterator[ThreatEvent]:
        """Yield every stored event in source-time order."""
        with closing(self._connect()) as conn:
            cursor = conn.execute(
                "SELECT area_id, state, ts_source, ts_ingest, source_id, kind, "
                "provenance, raw_fields FROM events ORDER BY ts_source, area_id"
            )
            # Iterated, not fetchall(): the docstring promises an iterator
            # and materializing the whole log first would quietly break that
            # promise on the first store big enough for it to matter.
            for row in cursor:
                yield ThreatEvent(
                    area_id=row[0],
                    state=AlertState(row[1]),
                    ts_source=datetime.fromisoformat(row[2]),
                    ts_ingest=datetime.fromisoformat(row[3]),
                    source_id=row[4],
                    kind=ThreatKind(row[5]),
                    provenance=Provenance[row[6]],
                    raw_fields=json.loads(row[7]),
                )

    def count(self) -> int:
        """Number of stored events."""
        with closing(self._connect()) as conn:
            result: int = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            return result
