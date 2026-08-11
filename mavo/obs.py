"""The run log: one writer, one schema, and no message text.

`docs/OBSERVABILITY.md` designed this before any of it existed and wrote seven
acceptance criteria in section 9. This module implements the sink half; the
reader is `tools/progress.py` and nothing under `mavo/` may import it, which
`tests/lint_domain.py` enforces rather than merely asking for.

**Why the sink is the product rather than a diagnostic.** Shadow mode's
deliverable is a record of decisions that were never sent (T23). If the record
is wrong, there is nothing else to check it against, so the log gets the same
treatment as the report: unknowns stay unknown, a partial write is detectable,
and the thing that would weaken a guarantee leaves a mark in the record it
weakened.

Three constraints are inherited from defects already paid for.

**Appends are atomic per line (F51).** A line is written with one `os.write`
onto a descriptor opened `O_APPEND`, so a process killed mid-run leaves the
last line either whole or absent. A truncated final record is worse than a
missing one: its absence is indistinguishable from a cycle that never ran,
which is the same invisible hole the corpus census refuses.

**Rotation renames rather than truncates, and the retention is stated in the
sink's own first line.** A log that silently dropped its oldest evidence would
let a post-mortem read a partial history as a complete one, so the reader is
told the policy by the file itself rather than by documentation it may not have.

**Unknown is a value, not a zero.** `Unknown("first_poll_has_no_baseline")`
serialises as `null` beside a `*_reason`, because the whole project turns on
the difference between "measured zero" and "could not measure", and a log that
collapses them is a log that will eventually be believed.

The one thing this module deliberately does not do is decide what a cycle is.
It writes lines. A caller that has nothing true to say should say nothing.
"""

from __future__ import annotations

import json
import os
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

#: Schema version, carried on every line so a query written months later does
#: not have to guess which shape it is reading.
SCHEMA = 1

#: The stage vocabulary. The reader imports this rather than restating it: two
#: lists of stage names is one list and a bug waiting for the day they differ.
STAGES = ("fetch", "parse", "store", "report", "publish", "notify", "sink")

#: Environment switches, named here because they are part of the contract.
LOG_FILE = "MAVO_LOG_FILE"
LOG_BODIES = "MAVO_LOG_BODIES"

#: Field names that would carry message text into the record. Refused by
#: default; see `docs/OBSERVABILITY.md` section 3 and T24. Two independent
#: reasons hold, either sufficient: the design/holdout split was frozen before
#: any content was read (D-012a) and a log that echoes bodies spends it without
#: anyone deciding to, and SECURITY.md forbids raw per-subject records in
#: artifacts that get pasted into issues.
BODY_FIELDS = frozenset({"text", "body", "message", "raw", "sample", "unparsed"})

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
DEFAULT_RETAIN = 5


@dataclass(frozen=True, slots=True)
class Unknown:
    """A value that could not be measured, and why.

    Serialises to `null` plus `<field>_reason`. There is no constructor for an
    unknown without a reason on purpose: "unknown" with no explanation is the
    shape that eventually gets read as zero.
    """

    reason: str

    def __post_init__(self) -> None:
        if not self.reason:
            raise ValueError("an unknown must carry the reason it is unknown")


def _encode(fields: dict[str, Any]) -> dict[str, Any]:
    """Flatten `Unknown` values into `null` beside their reason."""
    out: dict[str, Any] = {}
    for key, value in fields.items():
        if isinstance(value, Unknown):
            out[key] = None
            out[f"{key}_reason"] = value.reason
        else:
            out[key] = value
    return out


class RunLog:
    """The only writer of the sink.

    One module owns the vocabulary, the line schema and the file handle, which
    is what makes `SCHEMA` a single point of change rather than a convention
    that holds until someone is in a hurry.
    """

    def __init__(
        self,
        path: Path,
        *,
        max_bytes: int = DEFAULT_MAX_BYTES,
        retain: int = DEFAULT_RETAIN,
        allow_bodies: bool | None = None,
        now: Any = None,
    ) -> None:
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.retain = retain
        self._now = now if now is not None else (lambda: datetime.now(UTC))
        self.allow_bodies = (
            allow_bodies
            if allow_bodies is not None
            else os.environ.get(LOG_BODIES) == "1"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fresh = not self.path.exists() or self.path.stat().st_size == 0
        if fresh:
            self._append(
                self._compose(
                    "sink",
                    "sink.opened",
                    level="INFO",
                    provenance="measured",
                    rotation="rename",
                    max_bytes=max_bytes,
                    retain=retain,
                )
            )
        if self.allow_bodies:
            # A switch that disables an evidential guarantee leaves a mark in
            # the record it weakened. Written every time the sink is opened
            # with it, not once per process: a reader holding one rotated file
            # must be able to see it from that file alone.
            self._append(
                self._compose(
                    "sink",
                    "sink.bodies_enabled",
                    level="WARNING",
                    provenance="measured",
                    note=f"{LOG_BODIES}=1; this file may contain message text",
                )
            )

    def cycle_id(self) -> str:
        """A short, unguessable id grouping one cycle's lines."""
        return secrets.token_hex(3)

    def line(
        self,
        stage: str,
        event: str,
        *,
        cycle: str | None = None,
        level: str = "INFO",
        provenance: str = "measured",
        **fields: Any,
    ) -> dict[str, Any]:
        """Write one line. Returns what was written, for the caller's tests."""
        if stage not in STAGES:
            raise ValueError(f"unknown stage {stage!r}; STAGES is the vocabulary")
        record = self._compose(
            stage, event, cycle=cycle, level=level, provenance=provenance, **fields
        )
        self._rotate_if_needed()
        self._append(record)
        return record

    @contextmanager
    def timed(self, stage: str, event: str, **fields: Any) -> Iterator[dict[str, Any]]:
        """Time a stage and write its line on the way out, success or not.

        The line is written in a `finally`, because a stage that raised is
        exactly the stage whose duration a post-mortem wants, and a record that
        exists only for the happy path is a record of the happy path.
        """
        extra: dict[str, Any] = {}
        started = self._now()
        failure: BaseException | None = None
        try:
            yield extra
        except BaseException as raised:  # noqa: BLE001 - re-raised below
            failure = raised
            raise
        finally:
            elapsed_ms = int((self._now() - started).total_seconds() * 1000)
            merged = {**fields, **extra, "ms": elapsed_ms}
            if failure is not None:
                merged["level"] = "ERROR"
                merged["error"] = type(failure).__name__
            self.line(stage, event, **merged)

    def _compose(
        self, stage: str, event: str, **fields: Any
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "v": SCHEMA,
            "ts": self._now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "stage": stage,
            "event": event,
        }
        record.update(_encode(fields))
        if not self.allow_bodies:
            refused = sorted(BODY_FIELDS & set(record))
            for key in refused:
                record[key] = None
                record[f"{key}_reason"] = "bodies_not_logged"
            if refused:
                record["redacted"] = refused
        return {key: value for key, value in record.items() if value is not None
                or key in _NULLABLE(record)}

    def _append(self, record: dict[str, Any]) -> None:
        payload = (json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n").encode(
            "utf-8"
        )
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            # One write on an O_APPEND descriptor. Not `print` and not a
            # buffered handle: a buffer flushed by the interpreter on the way
            # out is exactly what produces a half-line when it does not get to
            # exit (F51).
            os.write(fd, payload)
        finally:
            os.close(fd)

    def _rotate_if_needed(self) -> None:
        if not self.path.exists() or self.path.stat().st_size < self.max_bytes:
            return
        oldest = self.path.with_suffix(self.path.suffix + f".{self.retain}")
        if oldest.exists():
            oldest.unlink()
        for index in range(self.retain - 1, 0, -1):
            source = self.path.with_suffix(self.path.suffix + f".{index}")
            if source.exists():
                source.rename(self.path.with_suffix(self.path.suffix + f".{index + 1}"))
        # Rename, never truncate: a reader mid-file keeps reading a whole file.
        self.path.rename(self.path.with_suffix(self.path.suffix + ".1"))
        self._append(
            self._compose(
                "sink",
                "sink.opened",
                level="INFO",
                provenance="measured",
                rotation="rename",
                max_bytes=self.max_bytes,
                retain=self.retain,
                note="rotated; older evidence is in the numbered siblings",
            )
        )


def _NULLABLE(record: dict[str, Any]) -> frozenset[str]:  # noqa: N802
    """Keys allowed to hold `null`: those with a stated reason beside them.

    This is the mechanism behind "unknown is a value". A `None` with no
    `<key>_reason` is dropped from the line rather than written, so a consumer
    can never meet a bare null and guess what it meant.
    """
    return frozenset(
        key for key in record if f"{key}_reason" in record
    )


def from_environment(**kwargs: Any) -> RunLog | None:
    """A sink if `MAVO_LOG_FILE` names one, otherwise nothing.

    Returning `None` rather than a no-op writer is deliberate: a caller has to
    decide what it does without a log, and a silent null object lets a run
    believe it is recording when it is not.
    """
    target = os.environ.get(LOG_FILE)
    return RunLog(Path(target), **kwargs) if target else None
