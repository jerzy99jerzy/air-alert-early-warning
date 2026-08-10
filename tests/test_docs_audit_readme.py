"""F73 regressions: the README's tables, and the sentence claiming they are checked.

The paragraph above the size table says these rows are recounted from the tree
on every run and that a stale one is a gate failure. It described
`check_statistics_match_the_tree`, which compares STATUS.json against the tree
and never reads the README. By 0.16.1.0 every row of both tables was stale,
including a test count twelve lines below an enforced badge saying otherwise.

Verified red on a scratch copy carrying the pre-repair README. Registration of
the check itself is held by `tests/test_docs_audit_versions.py`, because these
tests call the function directly and cannot see whether the gate does.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.docs_audit import check_readme_tables_match_the_pins

STATUS = json.loads(Path("STATUS.json").read_text(encoding="utf-8"))


def _status_with(**overrides: object) -> dict[str, object]:
    """A copy of the real status with the named measured value replaced."""
    status = json.loads(json.dumps(STATUS))
    for key, value in overrides.items():
        if key in status.get("measured", {}):
            status["measured"][key] = value
        elif key in status.get("statistics", {}):
            status["statistics"][key] = value
        else:
            status[key] = value
    return status


def test_the_tree_agrees_with_the_readme_today() -> None:
    """The gate check itself, so a stale row fails the suite and not only the gate."""
    assert check_readme_tables_match_the_pins(STATUS) == []


def test_a_drifted_test_count_is_reported() -> None:
    """The exact 0.16.1.0 shape: the badge says 208, the table said 206."""
    problems = check_readme_tables_match_the_pins(_status_with(tests_passing=9999))
    assert problems, "a README table two releases behind the pin passed the gate"
    assert "9999" in problems[0]


def test_a_drifted_coverage_figure_is_reported() -> None:
    """A coverage figure that flatters by a release is the class this repo attacks."""
    assert check_readme_tables_match_the_pins(_status_with(coverage_percent=11.11))


def test_a_drifted_size_row_is_reported() -> None:
    """The rows 0.6.2.0 claimed to have put behind a gate."""
    assert check_readme_tables_match_the_pins(_status_with(documentation_lines=1))


def test_a_missing_row_is_reported_rather_than_skipped() -> None:
    """A label that stops matching must fail loudly.

    Silently skipping an unmatched label would let a row leave the audit by
    being renamed, which is how a check ends up guarding an empty set.
    """
    status = json.loads(json.dumps(STATUS))
    status["statistics"].pop("tool_files")
    try:
        check_readme_tables_match_the_pins(status)
    except KeyError:
        return  # a missing pin is a hard error, not a quiet pass
    raise AssertionError("a missing statistics pin did not stop the check")
