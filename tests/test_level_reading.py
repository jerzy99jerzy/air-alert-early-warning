"""The reading that opens 0.60.0.0's install, pinned (D-063, F195, F199).

`mavo level-reading` runs on the production host before anything is tagged,
from stdin under the host's own python3, and its last line is the install's
stop condition. Nothing else in the tree runs it, so these tests are the only
place a wrong count or a wrong verdict can be caught before the host prints
it. Each case is built to fail against a plausible wrong implementation: a
change counted across an all-clear, declarations ordered by arrival rather
than by the source's stamp, a threshold off by one, an age read off a key the
API has closed.
"""
from __future__ import annotations

import hashlib
import sqlite3
import subprocess
import sys
from collections.abc import Sequence
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo import cli
from mavo.level_reading import main
from mavo.store import EventStore

MODULE = Path(__file__).resolve().parents[1] / "mavo" / "level_reading.py"
T0 = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)

# (area, word, source stamp, arrival) and (area, state, source stamp, source_id)
Declaration = tuple[str, str, datetime, datetime]
Row = tuple[str, str, datetime, str]


def at(minutes: float) -> datetime:
    return T0 + timedelta(minutes=minutes)


def declared(area: str, word: str, minutes: float, arrived: float | None = None) -> Declaration:
    return (area, word, at(minutes), at(minutes if arrived is None else arrived))


def store(tmp_path: Path, declarations: Sequence[Declaration],
          rows: Sequence[Row] = ()) -> Path:
    """A store with the release's own schema, filled in the order given."""
    path = tmp_path / "events"
    EventStore(path)
    with closing(sqlite3.connect(path)) as conn:
        for n, (area, word, stamp, arrived) in enumerate(declarations):
            conn.execute(
                "INSERT INTO alert_levels (content_hash, area_id, oblast, kind, level, "
                "level_at, ts_ingest, source_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (f"d{n}", area, "o", "missile", word, stamp.isoformat(),
                 arrived.isoformat(), "ukrainealarm"))
        for n, (area, state, stamp, source) in enumerate(rows):
            conn.execute(
                "INSERT INTO events (content_hash, area_id, state, ts_source, ts_ingest, "
                "source_id, kind, provenance, raw_fields, oblast, role) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (f"e{n}", area, state, stamp.isoformat(), stamp.isoformat(), source,
                 "missile", "REPORTED", "{}", "o", "subject"))
        conn.commit()
    return path


def read(path: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, list[str]]:
    code = main([str(path)])
    captured = capsys.readouterr()
    assert not captured.err, captured.err
    return code, captured.out.splitlines()


def line(lines: list[str], prefix: str) -> str:
    found = [text for text in lines if text.startswith(prefix)]
    assert len(found) == 1, lines
    return found[0]


def test_a_change_counts_inside_an_alarm_and_not_across_the_apis_all_clear(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = store(tmp_path, [
        declared("open", "Yellow", 0), declared("open", "Red", 10),
        declared("cleared", "Yellow", 0), declared("cleared", "Red", 10),
        declared("reconciled", "Yellow", 0), declared("reconciled", "Red", 10),
        declared("channel", "Yellow", 0), declared("channel", "Red", 10),
        declared("same", "Red", 0), declared("same", "Red", 10),
        declared("ends-at-next", "Yellow", 0), declared("ends-at-next", "Red", 10),
        declared("ends-at-first", "Yellow", 0), declared("ends-at-first", "Red", 10),
    ], [
        ("cleared", "clear", at(5), "ukrainealarm"),
        ("reconciled", "clear", at(5), "reconcile"),
        # Only the API's own all-clears end an alarm the API kept open.
        ("channel", "clear", at(5), "telegram"),
        # An all-clear stamped at the next declaration's own moment ends the
        # alarm before it; one stamped at the first declaration's moment ends
        # an alarm before both.
        ("ends-at-next", "clear", at(10), "ukrainealarm"),
        ("ends-at-first", "clear", at(0), "ukrainealarm"),
    ])
    _, lines = read(path, capsys)
    assert line(lines, "1. ") == (
        "1. changes inside an alarm: 3 on 3 keys (the condition: 50 on 15)")


def test_declarations_are_ordered_by_the_sources_stamp_not_by_arrival(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # By stamp: Yellow, Red, Yellow, two changes. Inserted, or sorted by
    # arrival, the same three rows read Red, Yellow, Yellow: one.
    path = store(tmp_path, [
        declared("k", "Red", 10, arrived=11),
        declared("k", "Yellow", 20, arrived=21),
        declared("k", "Yellow", 0, arrived=25),
    ])
    _, lines = read(path, capsys)
    assert line(lines, "1. ").startswith("1. changes inside an alarm: 2 on 1 keys")


def _changes(changes: int, keys: int) -> list[Declaration]:
    out: list[Declaration] = []
    for key in range(keys):
        mine = changes // keys + (1 if key < changes % keys else 0)
        out += [declared(f"k{key}", ("Yellow", "Red")[step % 2], step)
                for step in range(mine + 1)]
    return out


@pytest.mark.parametrize(("changes", "keys", "verdict", "code"), [
    (50, 15, "MET", 0),
    (49, 15, "NOT MET", 1),
    (50, 14, "NOT MET", 1),
])
def test_the_verdict_is_met_at_fifty_changes_on_fifteen_keys_and_not_one_short(
        tmp_path: Path, capsys: pytest.CaptureFixture[str], changes: int, keys: int,
        verdict: str, code: int) -> None:
    returncode, lines = read(store(tmp_path, _changes(changes, keys)), capsys)
    assert line(lines, "1. ").startswith(
        f"1. changes inside an alarm: {changes} on {keys} keys")
    assert lines[-1] == f"D-050 condition: {verdict}"
    assert returncode == code


def test_an_empty_stream_is_not_met_and_says_it_was_never_declared(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    returncode, lines = read(store(tmp_path, []), capsys)
    assert lines[0].endswith("alert_levels rows=0 keys=0 declared since never")
    assert line(lines, "2. ") == "2. words: none | outside Red/Yellow: none"
    assert line(lines, "3. ") == "3. no active API key carries a declaration"
    assert lines[-1] == "D-050 condition: NOT MET"
    assert returncode == 1


def test_a_word_outside_red_and_yellow_is_named(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = store(tmp_path, [
        declared("a", "Red", 0), declared("b", "Red", 0),
        declared("c", "Yellow", 0), declared("d", "Orange", 0),
    ])
    _, lines = read(path, capsys)
    words = line(lines, "2. ")
    assert words.startswith("2. words: 'Red'=2, ")
    assert words.endswith("| outside Red/Yellow: ['Orange']")


def test_ages_are_read_only_off_keys_whose_newest_api_row_is_active(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    now = datetime.now(UTC)
    recent, old = now - timedelta(hours=1), now - timedelta(days=40)
    path = store(tmp_path, [
        ("recent", "Red", recent, recent),
        ("old", "Yellow", old, old),
        ("closed", "Red", recent, recent),
        ("unknown", "Red", recent, recent),
        ("channel", "Red", recent, recent),
    ], [
        ("recent", "active", recent, "ukrainealarm"),
        ("old", "active", old, "ukrainealarm"),
        ("closed", "active", old, "ukrainealarm"),
        ("closed", "clear", recent, "reconcile"),
        ("unknown", "unknown", recent, "ukrainealarm"),
        ("channel", "active", recent, "telegram"),
        ("undeclared", "active", recent, "ukrainealarm"),
    ])
    _, lines = read(path, capsys)
    ages = line(lines, "3. ")
    assert ages.startswith("3. active API keys with a declaration: 2;")
    assert ages.endswith("over 30 days: 1")


def test_the_host_runs_the_same_file_from_stdin_and_the_store_is_left_as_it_was(
        tmp_path: Path) -> None:
    """As the install's first step runs it: the module piped to an interpreter
    without site-packages, where `mavo` cannot be imported, as on a host that
    does not have the release yet; its last line the stop condition."""
    path = store(tmp_path, _changes(50, 15), [("k0", "active", at(1), "ukrainealarm")])
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with MODULE.open("rb") as stdin:
        done = subprocess.run([sys.executable, "-I", "-S", "-", str(path)], stdin=stdin,
                              capture_output=True, text=True, check=False, timeout=60)
    assert (done.returncode, done.stderr) == (0, "")
    assert done.stdout.splitlines()[-1] == "D-050 condition: MET"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_the_subcommand_reads_the_same_and_names_its_one_argument(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = store(tmp_path, _changes(3, 2))
    assert cli.main(["level-reading", str(path)]) == 1
    assert capsys.readouterr().out.splitlines()[-1] == "D-050 condition: NOT MET"
    assert main([]) == 2
    assert capsys.readouterr().err.strip() == "usage: mavo level-reading STORE"
