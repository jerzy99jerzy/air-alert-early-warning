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
#
# **That rule holds for two of the four tables and destroys the other two
# (F124).** `events` and `kind_events` are derived: D-013 calls the store a
# derived artefact and the remedy - rebuild from the raw corpus - restores
# every row. `communiques` and `feed_attempts` are not derived from anything.
# A poll attempt is a record of what this program did at a moment that will
# not come again, and no corpus, endpoint or re-read reconstructs it. Refusing
# a store because a *recorded* table lacks a column names a remedy whose
# execution deletes the only copy of the evidence, which is the opposite of
# what a guard is for. The two lists below are therefore separate, and
# `_refuse_an_older_schema` treats them differently: see D-036.
DERIVED_TABLES = ("events", "kind_events")
RECORDED_TABLES = ("communiques", "feed_attempts")

EXPECTED_KIND_COLUMNS = (
    "content_hash", "area_id", "oblast", "kind", "state",
    "ts_source", "ts_ingest", "source_id", "raw_fields",
)
EXPECTED_COLUMNS = (
    "content_hash", "area_id", "state", "ts_source", "ts_ingest",
    "source_id", "kind", "provenance", "raw_fields", "oblast", "role",
)
EXPECTED_COMMUNIQUE_COLUMNS = (
    "digest", "feed", "source_id", "ts_ingest", "provinces", "fields",
)
EXPECTED_ATTEMPT_COLUMNS = (
    "started_at", "feed", "url", "outcome", "items", "unreadable", "detail",
    "elapsed_s", "first_id", "last_id",
)

#: Column definitions for the recorded tables, so a column missing from an
#: older store can be added rather than refused. Every one of them is nullable
#: and none carries a default: a row written before the column existed gets
#: NULL, which reads as "not measured" everywhere in this project and is the
#: only honest value. A migration that supplied a default would be inventing
#: the measurement the refusal was written to prevent.
RECORDED_COLUMN_TYPES: dict[str, dict[str, str]] = {
    "communiques": {},
    "feed_attempts": {
        "elapsed_s": "REAL",
        "first_id": "INTEGER",
        "last_id": "INTEGER",
    },
}

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
-- T67. The third stream, and the third table, for the reason the second one
-- exists: a Polish communique has a different issuer, a different scope and a
-- different lifetime from a Ukrainian alert, and a shared `state` column
-- between them is the modelling error F25 recorded.
--
-- `feed` names the endpoint the row was read from and is written by the
-- caller, not by the publisher. The RSO payload carries no issuer field at
-- all; this column records our reading. If the feed ever names an issuer,
-- that is a different column and it is not this one.
--
-- Every field the publisher sent is kept in `fields` as JSON, unfiltered.
-- D-034: nothing is dropped by category here. A row this project cannot
-- classify is a row it stores and cannot classify, which is a different
-- object from a row that was never published.
CREATE TABLE IF NOT EXISTS communiques (
    digest     TEXT PRIMARY KEY,
    feed       TEXT NOT NULL,
    source_id  TEXT NOT NULL,
    ts_ingest  TEXT NOT NULL,
    provinces  TEXT NOT NULL,
    fields     TEXT NOT NULL
);

-- FEED-SPEC property nine, owed by this project to itself. RSO publishes no
-- heartbeat, so an hour with no communiques and an hour in which this
-- collector was dead are the same empty set in `communiques` and no care at
-- rendering time recovers the difference.
--
-- `items` is NULL for a refusal and 0 for a page that was read and held
-- nothing. Those are two different facts and the schema has to make them
-- representable differently or the distinction collapses at the first
-- timeout. The two writers below exist so that the wrong combination cannot
-- be expressed by a caller.
--
-- `elapsed_s` is how long the attempt took, added at 0.41.0.0 under D-036.
-- T55 put the same figure in the refusal line for the reason it is here: a
-- stall that hit the ten-second ceiling and a rejection that bounced in
-- twenty milliseconds are different failures, and a table of attempts that
-- cannot tell them apart answers no question the journal could not already
-- answer worse. NULL where the caller did not time itself, never 0.0: a
-- fetch that took no time is not a fetch nobody timed.
--
-- `first_id` and `last_id` are the post-id bounds of the page that was read,
-- added at 0.42.0.0 to close F123. They are the cursor two invocations can
-- both reach: `mavo collect` is a `oneshot`, so the in-process `_last_id` on
-- the source object was never carried from one poll to the next on the host
-- and `skipped` read `unknown` on every poll the machine has ever made. The
-- bounds live here rather than in a cursor file because a cursor records only
-- where we are and this records where we have been, which is the difference
-- between resuming and auditing.
--
-- NULL on a refusal and on a page carrying no ids, which is what a hostile or
-- restructured page looks like. A zero would claim the channel is at post 0.
CREATE TABLE IF NOT EXISTS feed_attempts (
    started_at TEXT NOT NULL,
    feed       TEXT NOT NULL,
    url        TEXT NOT NULL,
    outcome    TEXT NOT NULL,
    items      INTEGER,
    unreadable INTEGER,
    detail     TEXT,
    elapsed_s  REAL,
    first_id   INTEGER,
    last_id    INTEGER
);
"""

# **Separate from `_SCHEMA`, and the separation is load-bearing.** An index
# names columns, so `CREATE INDEX` against a table written by an older version
# raises `OperationalError: no such column` from inside `executescript`, before
# the refusal below can run. The caller then gets a message naming a column and
# nothing about which version wrote the store or what to do next. Tables first,
# columns checked, indexes last.
_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_events_ts_source ON events (ts_source);
CREATE INDEX IF NOT EXISTS idx_events_area ON events (area_id, ts_source);
CREATE INDEX IF NOT EXISTS idx_communiques_feed ON communiques (feed, ts_ingest);
CREATE INDEX IF NOT EXISTS idx_attempts_feed ON feed_attempts (feed, started_at);
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

    #: Columns added to a recorded table when this store was opened, newest
    #: caller last. Empty on every ordinary open. It is an attribute rather
    #: than a log line because this module prints nothing, and a migration
    #: that leaves no trace is the silent repair this project refuses: the
    #: commands that open a store read this and say so on stdout, once, at the
    #: moment it happens.
    migrations_applied: tuple[str, ...]

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrations_applied = ()
        with closing(self._connect()) as conn:
            conn.executescript(_SCHEMA)
            conn.commit()
            self._refuse_an_older_schema(conn)
            self.migrations_applied = self._extend_the_recorded_tables(conn)
            conn.executescript(_INDEXES)
            conn.commit()

    @staticmethod
    def _refuse_an_older_schema(conn: sqlite3.Connection) -> None:
        """Refuse a store whose *derived* tables predate this version.

        ``CREATE TABLE IF NOT EXISTS`` is silent about a table that already
        exists with fewer columns, so without this check an older store would
        open cleanly and then fail one row at a time, or worse, read back events
        with fields that were never written. The refusal names the missing
        columns and the remedy, which is a rebuild rather than a migration.

        **Narrowed to the derived tables at 0.41.0.0 (F124).** Until then this
        method refused on all four, and the remedy it named - rebuild from the
        raw corpus - restores `events` and `kind_events` and deletes
        `communiques` and `feed_attempts`, which no corpus can reconstruct. A
        guard whose prescribed repair destroys the evidence it was protecting
        is not a guard, and it would have fired on this very release: adding
        one column to the attempts table would have made the production store
        unopenable and the documented fix would have thrown away every poll
        record on the host. D-036 records the split; recorded tables are
        extended below instead.
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
                "it, so no row carries a value that was never observed (D-013). This "
                f"applies to the derived tables {', '.join(DERIVED_TABLES)} only"
            )

    @staticmethod
    def _extend_the_recorded_tables(conn: sqlite3.Connection) -> tuple[str, ...]:
        """Add a missing column to a recorded table, and say which.

        A recorded table holds what this program did, not what it derived, so
        the D-013 remedy does not apply to it (F124). The migration is
        additive and nothing else: a column named in ``RECORDED_COLUMN_TYPES``
        and absent from the table is appended, nullable, with no default, so
        every row written before this release reads NULL rather than a value
        nobody observed.

        **A column this version does not know how to add is still a refusal.**
        Silently accepting a recorded table that lacks a column would put the
        store back in the state the refusal exists to prevent, one table over.
        """
        added: list[str] = []
        for table, expected in (
            ("communiques", EXPECTED_COMMUNIQUE_COLUMNS),
            ("feed_attempts", EXPECTED_ATTEMPT_COLUMNS),
        ):
            present = tuple(row[1] for row in conn.execute(f"PRAGMA table_info({table})"))
            for column in expected:
                if column in present:
                    continue
                declared = RECORDED_COLUMN_TYPES[table].get(column)
                if declared is None:
                    raise SchemaMismatch(
                        f"store is missing {table}.{column} and this version has no "
                        f"column type for it, so it cannot be added without inventing "
                        f"one; {table} holds records that cannot be rebuilt, so copy "
                        "the file aside before doing anything else (D-036)"
                    )
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declared}")
                added.append(f"{table}.{column}")
        if added:
            conn.commit()
        return tuple(added)

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

    def append_communiques(self, feed: str, communiques: Iterable[Any]) -> int:
        """Insert communiques, ignoring ones already present. Returns rows added.

        Idempotence is by the communique's own content digest and not by its
        identifier, because the feed edits in place: `updated_at` moves and the
        identifier does not, so a store keyed on the identifier could not tell
        a re-publication from a rewrite. Keying on content means an edit lands
        as a second row and both readings survive, which is what a record is
        for.

        `feed` is stated by the caller. Nothing here infers it, because the
        payload does not carry it.
        """
        now = _stored_form(datetime.now(UTC), "ts_ingest")
        rows = [
            (
                item.digest(),
                feed,
                item.id,
                now,
                json.dumps(
                    [[p.slug, p.name, p.city] for p in item.provinces],
                    sort_keys=True,
                    ensure_ascii=False,
                ),
                json.dumps(item.fields, sort_keys=True, ensure_ascii=False),
            )
            for item in communiques
        ]
        if not rows:
            return 0
        with closing(self._connect()) as conn:
            before = conn.total_changes
            conn.executemany(
                "INSERT OR IGNORE INTO communiques (digest, feed, source_id, ts_ingest, "
                "provinces, fields) VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            return conn.total_changes - before

    def count_communiques(self, feed: str | None = None) -> int:
        """Rows held, for the whole table or one feed."""
        with closing(self._connect()) as conn:
            if feed is None:
                return int(conn.execute("SELECT COUNT(*) FROM communiques").fetchone()[0])
            return int(
                conn.execute(
                    "SELECT COUNT(*) FROM communiques WHERE feed = ?", (feed,)
                ).fetchone()[0]
            )

    def replay_communiques(self, feed: str) -> Iterator[dict[str, Any]]:
        """Every communique held for one feed, oldest reading first.

        Ordered by ingest time and then by digest, because ingest time ties
        whenever one poll stored several rows and a tie broken by nothing is a
        different order on every read.
        """
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT source_id, ts_ingest, provinces, fields FROM communiques "
                "WHERE feed = ? ORDER BY ts_ingest, digest",
                (feed,),
            ).fetchall()
        for row in rows:
            yield {
                "source_id": row[0],
                "ts_ingest": row[1],
                "provinces": json.loads(row[2]),
                "fields": json.loads(row[3]),
            }

    def record_read(
        self,
        feed: str,
        url: str,
        started_at: datetime,
        items: int,
        unreadable: int,
        elapsed_s: float | None = None,
        first_id: int | None = None,
        last_id: int | None = None,
    ) -> None:
        """Log a poll that returned a page. `items` may legitimately be zero.

        Separate from ``record_refusal`` so that a caller cannot write a
        refusal carrying `items=0`. That single confusion is the one this
        table exists to prevent, and a shared writer with optional arguments
        would leave it one keyword away.

        ``elapsed_s`` defaults to None rather than to 0.0 because a caller
        that does not time itself has not measured a duration of zero.
        """
        self._record(feed, url, started_at, "read", items, unreadable, None,
                     elapsed_s, first_id, last_id)

    def record_refusal(
        self,
        feed: str,
        url: str,
        started_at: datetime,
        detail: str,
        elapsed_s: float | None = None,
    ) -> None:
        """Log a poll that returned nothing readable. `items` stays NULL.

        NULL is not zero here and the distinction is the property: zero means
        the publisher said there is nothing, NULL means we did not find out.
        """
        # No id bounds on a refusal: there was no page to bound. They stay NULL
        # rather than repeating the previous poll's, which would make a run of
        # refusals look like a run of identical pages.
        self._record(feed, url, started_at, "refused", None, None, detail,
                     elapsed_s, None, None)

    def _record(
        self,
        feed: str,
        url: str,
        started_at: datetime,
        outcome: str,
        items: int | None,
        unreadable: int | None,
        detail: str | None,
        elapsed_s: float | None,
        first_id: int | None,
        last_id: int | None,
    ) -> None:
        row = (
            _stored_form(started_at, "started_at"),
            feed,
            url,
            outcome,
            items,
            unreadable,
            detail,
            elapsed_s,
            first_id,
            last_id,
        )
        with closing(self._connect()) as conn:
            conn.execute(
                "INSERT INTO feed_attempts (started_at, feed, url, outcome, items, "
                "unreadable, detail, elapsed_s, first_id, last_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )
            conn.commit()

    def attempts(
        self,
        feed: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Every poll logged for one feed, oldest first.

        Returned whole rather than streamed: this table holds one row per poll
        and is read by a person asking what the collector was doing, not by
        the report path.

        ``since`` is inclusive and ``until`` exclusive, so two adjacent
        windows partition the rows between them instead of both claiming the
        row on the boundary. Both are compared in stored form - ISO text
        normalised to UTC - because that is what the column holds and what
        `ORDER BY` on it means.
        """
        clauses = ["feed = ?"]
        values: list[Any] = [feed]
        if since is not None:
            clauses.append("started_at >= ?")
            values.append(_stored_form(since, "since"))
        if until is not None:
            clauses.append("started_at < ?")
            values.append(_stored_form(until, "until"))
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT started_at, url, outcome, items, unreadable, detail, elapsed_s, "
                "first_id, last_id "
                f"FROM feed_attempts WHERE {' AND '.join(clauses)} "
                "ORDER BY started_at, rowid",
                tuple(values),
            ).fetchall()
        return tuple(
            {
                "started_at": row[0],
                "url": row[1],
                "outcome": row[2],
                "items": row[3],
                "unreadable": row[4],
                "detail": row[5],
                "elapsed_s": row[6],
                "first_id": row[7],
                "last_id": row[8],
            }
            for row in rows
        )

    def newest_page_id(self, feed: str) -> int | None:
        """The highest post id this feed has ever been observed to serve.

        The cursor `mavo collect` seeds itself from, and the reason F123 could
        not be fixed inside the source object: a `oneshot` process has no
        previous poll, so the baseline has to survive the process that measured
        it.

        **Highest, not most recent.** A page that came back short or out of
        order must not move the cursor backwards, because a cursor that
        retreats reports the messages between as newly skipped and counts the
        same window twice. `MAX` over the column is one expression and cannot
        drift from that sentence.

        None when no attempt for this feed has ever carried ids, which is the
        first poll and is genuinely unknown rather than zero.
        """
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT MAX(last_id) FROM feed_attempts WHERE feed = ?", (feed,)
            ).fetchone()
        return int(row[0]) if row and row[0] is not None else None
