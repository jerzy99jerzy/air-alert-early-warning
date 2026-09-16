"""F168. A store opened first by `mavo report` created tables in silence.

Reproduced in the 0.55.0.0 session before the repair `[measured]`: a store
missing the three recorded tables of that release, opened by
`mavo report --watch`, gained all three and printed no `[STORE-MIGRATED]` line
on either stream; `mavo rso` opened it next and printed nothing either, because
by then there was nothing left to migrate. The install plan's discriminator
rested on that line, and whether it appeared depended on which unit restarted
first.
"""

from __future__ import annotations

import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import pytest

from mavo.cli import main
from mavo.store import EventStore, migration_lines

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lint_domain  # noqa: E402

TABLES = ("feed_snapshots", "airspace_zones", "airspace_geometries")
FIXTURE = Path(__file__).parent / "fixtures" / "rso_page.xml"


def _older_store(path: Path) -> None:
    """A store as 0.54.8.0 left it: every table but the three of 0.55.0.0."""
    EventStore(path)
    with closing(sqlite3.connect(path)) as conn:
        for table in TABLES:
            conn.execute(f"DROP TABLE {table}")
        conn.commit()


def test_the_publishing_loop_announces_the_tables_it_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The red direction of F168, as it stood at 0.54.8.0."""
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    store = tmp_path / "events"
    _older_store(store)
    assert main(["report", "--store", str(store), "--json", str(tmp_path / "s.json"),
                 "--watch", "--interval", "0", "--max-cycles", "1"]) == 0
    out = capsys.readouterr().out
    for table in TABLES:
        assert f"[STORE-MIGRATED] created {table}, empty until the first cycle writes it" in out
    assert out.count("[STORE-MIGRATED]") == 3


def test_the_one_shot_report_and_attempts_announce_too(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store = tmp_path / "events"
    _older_store(store)
    main(["report", "--store", str(store)])
    assert capsys.readouterr().out.count("[STORE-MIGRATED] created") == 3
    _older_store(store)
    assert main(["attempts", "--store", str(store), "--feed", "channel",
                 "--cadence-s", "30"]) == 0
    assert capsys.readouterr().out.count("[STORE-MIGRATED] created") == 3


def test_a_second_open_has_nothing_to_announce(tmp_path: Path) -> None:
    store = tmp_path / "events"
    _older_store(store)
    assert len(migration_lines(EventStore(store))) == 3
    assert migration_lines(EventStore(store)) == []


def test_the_sentences_are_the_ones_the_collectors_always_printed() -> None:
    class _Fake:
        migrations_applied = ("alert_levels (table)", "feed_attempts.last_id")

    assert migration_lines(_Fake()) == [  # type: ignore[arg-type]
        "[STORE-MIGRATED] created alert_levels, empty until the first cycle writes it",
        "[STORE-MIGRATED] added feed_attempts.last_id, NULL for every earlier row",
    ]


def test_the_tree_passes_the_opener_lint_today() -> None:
    assert lint_domain.check_every_store_opener_announces_migrations() == []


def test_an_opener_that_prints_nothing_is_named(tmp_path: Path) -> None:
    """F168's own shape in a scratch tree: `report` opens, and says nothing."""
    (tmp_path / "mavo").mkdir()
    (tmp_path / "mavo" / "cli.py").write_text(
        "def _cmd_report(args):\n"
        "    store = EventStore(args.store)\n"
        "    return 0\n"
        "def _cmd_collect(args):\n"
        "    store = EventStore(args.store)\n"
        "    _announce_migrations(store)\n"
        "    return 0\n",
        encoding="utf-8",
    )
    (tmp_path / "mavo" / "attempts.py").write_text(
        "def main(argv):\n    for line in migration_lines(EventStore(argv[0])):\n"
        "        print(line)\n",
        encoding="utf-8",
    )
    problems = lint_domain.check_every_store_opener_announces_migrations(tmp_path)
    assert len(problems) == 1
    assert "cli.py::_cmd_report" in problems[0] and "F168" in problems[0]
