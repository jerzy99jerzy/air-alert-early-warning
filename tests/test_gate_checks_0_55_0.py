"""F167's check, in both directions.

`docs/DEPLOYMENT.md` section 2 said *Nothing else* beside a table that did not
list the primary source. The red direction below is that defect rebuilt in a
scratch tree; the quiet one is a destination a module names in prose rather
than in a quoted address, which a check reading prose would have to guess at.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import docs_audit  # noqa: E402

TABLE = """# Deployment

## 2. Egress inventory

| Destination | Purpose | Auth | Frequency |
| --- | --- | --- | --- |
| `t.me` (channel preview) | the watchman | none | one request per cycle |

Nothing else.

## 3. Jitter is not cosmetic
"""


def _scratch(tmp_path: Path, module: str, table: str = TABLE) -> Path:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / "DEPLOYMENT.md").write_text(table, encoding="utf-8")
    (tmp_path / "mavo" / "sources").mkdir(parents=True)
    (tmp_path / "mavo" / "sources" / "feed.py").write_text(module, encoding="utf-8")
    return tmp_path


def test_the_tree_passes_today() -> None:
    assert docs_audit.check_every_source_host_is_in_the_egress_inventory() == []


def test_a_primary_source_missing_from_the_table_is_caught(tmp_path: Path) -> None:
    """F167 as it stood from 0.44.0.0 to 0.54.8.0."""
    root = _scratch(tmp_path, 'API_BASE = "https://api.ukrainealarm.com/api/v3"\n')
    problems = docs_audit.check_every_source_host_is_in_the_egress_inventory(root)
    assert len(problems) == 1
    assert "api.ukrainealarm.com" in problems[0] and "F167" in problems[0]


def test_a_host_named_only_in_prose_is_not_read_as_a_destination(tmp_path: Path) -> None:
    root = _scratch(tmp_path, '"""Mirrors what https://example.org/ documents."""\n'
                              'CHANNEL_URL = "https://t.me/s/air_alert_ua"\n')
    assert docs_audit.check_every_source_host_is_in_the_egress_inventory(root) == []


def test_a_row_below_the_section_does_not_count(tmp_path: Path) -> None:
    table = TABLE + "\n| `api.ukrainealarm.com` | a row in section 3 |\n"
    root = _scratch(tmp_path, 'API_BASE = "https://api.ukrainealarm.com/api/v3"\n', table)
    assert len(docs_audit.check_every_source_host_is_in_the_egress_inventory(root)) == 1


def test_a_tree_without_the_section_says_so(tmp_path: Path) -> None:
    root = _scratch(tmp_path, 'X = "https://t.me/s/x"\n', "# Deployment\n")
    (problem,) = docs_audit.check_every_source_host_is_in_the_egress_inventory(root)
    assert "no '## 2. Egress inventory' section" in problem
