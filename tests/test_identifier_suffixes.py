"""T62: the identifier checks could not see a suffixed identifier.

Measured on 0.32.4.0 before the widening: `TODO.md` held sixty-one `## T`
headings and `tools/todo_index.py` reported fifty-nine, because `T8a` and `T8b`
did not match `^## (T\\d+)\\.`. `docs/DECISIONS.md` held twenty-nine `## D-`
headings and `STATUS.json` pinned twenty-eight, because `D-012a` collapsed into
`D-012` in a set. Both numbers were counted by hand, which is the state a
generated index exists to remove.

Each test here is red against the narrow pattern and green against the wide
one. The registration of these checks in the gate is held elsewhere, by the
tools' own entry points, the same split `test_todo_index_sprints.py` makes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.docs_audit as docs_audit
import tools.todo_index as todo_index

_TODO_WITH_A_SUFFIX = """# TODO

**Sprint S8, declared partial and still open.** Prose the check reads.

## T8a. A task carrying a letter suffix
Status: `ready` [tier 2]
**Acceptance:** stated elsewhere.

## T8b. Another one, and a different state
Status: `decision`, blocked by T8a [tier 2]
**Acceptance:** stated elsewhere.

## T9. A task with no suffix at all
Status: `ready` [tier 3]
**Acceptance:** stated elsewhere.
"""

_TODO_WITH_A_SUFFIXED_COLLISION = """# TODO

## T8a. One entry
Status: `ready` [tier 2]

## T8a. A second entry under the same identifier
Status: `ready` [tier 3]
"""

_TODO_WITH_A_MOVED_TASK = """# TODO

## T51. Work that belongs to another repository
Status: `moved` to the consumer, 0.32.5.0 [tier 2]

## T60. Work that belongs here
Status: `ready` [tier 1]
"""


def _todo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, text: str) -> list[
    tuple[str, str, str, str, str]
]:
    path = tmp_path / "TODO.md"
    path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(todo_index, "TODO", path)
    return todo_index.entries()


def test_a_suffixed_task_is_an_entry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Red against `^## (T\\d+)\\.`, which returns one row instead of three."""
    rows = _todo(monkeypatch, tmp_path, _TODO_WITH_A_SUFFIX)
    assert [row[0] for row in rows] == ["T8a", "T8b", "T9"]


def test_a_suffixed_task_carries_its_state_and_tier(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An entry the parser cannot see cannot be reported as untiered either.

    This is consequence three in T62: the guarantee that every open task has
    been ordered did not cover the two tasks the parser skipped.
    """
    rows = _todo(monkeypatch, tmp_path, _TODO_WITH_A_SUFFIX)
    by_id = {row[0]: row for row in rows}
    assert by_id["T8a"][2] == "ready"
    assert by_id["T8b"][2] == "decision"
    assert by_id["T8a"][3] == "2"


def test_two_entries_under_one_suffixed_identifier_are_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Consequence two in T62, and the reason the widening came first.

    `check_identifiers_are_unique` was added at 0.32.3.0 against exactly this
    class and would have passed a file holding two `## T8a.` entries, because
    neither was an entry.
    """
    rows = _todo(monkeypatch, tmp_path, _TODO_WITH_A_SUFFIXED_COLLISION)
    problems = todo_index.check_identifiers_are_unique(rows)
    assert any("T8a is used by 2 entries" in problem for problem in problems)


def test_a_moved_task_leaves_this_repositorys_open_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`moved` is closed here and is not `done`.

    Three site tasks sat in the producer's tier-2 list while nothing on the
    side that would do them was tracking them. Counting them as open kept them
    in this backlog for as long as the other repository took, and counting them
    as done would claim a completion this repository cannot observe.
    """
    rows = _todo(monkeypatch, tmp_path, _TODO_WITH_A_MOVED_TASK)
    index = todo_index.render_index(rows)
    assert "**1 of 2 closed, 1 open.**" in index
    assert "T51" not in index
    assert "T60" in index


def test_a_suffixed_decision_is_counted_as_its_own_entry(tmp_path: Path) -> None:
    """`D-012a` collapsed into `D-012`, so the pin held over an extra heading.

    Red against `^## (D-\\d+)`: the set holds one element and the count agrees
    with a pin of one over a log carrying two entries.
    """
    log = tmp_path / "DECISIONS.md"
    log.write_text(
        "## D-012. The boundary\n\nBody.\n\n"
        "## D-012a. The boundary, computed and frozen\n\nBody.\n",
        encoding="utf-8",
    )
    entries = docs_audit.decision_entries(log.read_text(encoding="utf-8"))
    assert entries == ["D-012", "D-012a"]


def test_a_dangling_suffixed_citation_is_reachable_by_the_resolver() -> None:
    """The citation pattern was `\\bD-\\d{3}\\b` and could not match at all.

    A document citing `D-012a` where no such entry exists would never have been
    reported, which is the half of T62 that is silent rather than wrong.
    """
    assert docs_audit.cited_decisions("see D-012a and D-016") == {
        "D-012a", "D-016",
    }
