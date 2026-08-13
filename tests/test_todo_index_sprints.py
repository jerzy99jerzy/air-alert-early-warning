"""Review R-4 of 0.23.1.0: three artefacts disagreeing about which sprint is open.

`STATUS.json` counted nine sprints shipped, `TODO.md` said S8 was partial and
still open, and `docs/MANUAL.md` referred to sprint 6 in the future tense. The
field was renamed to `sprint_test_files`, which is what it measures. The rest
of the repair is this check, and a check with no test that fails when it is
removed is the preference R-4 was about.

These call the function directly against written inputs, so the registration of
the check in the gate is held separately, by the tool's own `--check` path.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tools.todo_index as todo_index

_TODO = """# TODO

**Sprint {declared}, declared partial and still open.** Prose the check reads.

## T31. A task in a closed sprint
Status: `ready`, **S7** [tier 2]
**Acceptance:** stated elsewhere.

## T33. Another task in the same closed sprint
Status: `ready`, **S7** [tier 2]
**Acceptance:** stated elsewhere.

## T36. A task in the open sprint
Status: `ready`, **S8** [tier 1]
**Acceptance:** stated elsewhere.
"""

_MVP = """# MVP

| Sprint | Window | What ships | Exit criterion, checkable |
| --- | --- | --- | --- |
| **S7** | {s7} | Area resolution | Met on an amended criterion |
| **S8** | {s8} | The report | Still partial |
"""


def _tree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    declared: str = "S8",
    s7: str = "closed 9 Aug",
    s8: str = "**N/A**",
) -> list[tuple[str, str, str, str, str]]:
    todo = tmp_path / "TODO.md"
    mvp = tmp_path / "MVP.md"
    todo.write_text(_TODO.format(declared=declared), encoding="utf-8")
    mvp.write_text(_MVP.format(s7=s7, s8=s8), encoding="utf-8")
    monkeypatch.setattr(todo_index, "TODO", todo)
    monkeypatch.setattr(todo_index, "MVP", mvp)
    return todo_index.entries()


def test_the_arrangement_this_repository_is_actually_in_passes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # S7 closed with open tasks under it is the live disagreement, named in the
    # tolerated list with a reason. The check must accept exactly that and
    # nothing wider.
    rows = _tree(monkeypatch, tmp_path)
    assert todo_index.check_sprint_agreement(rows) == []


def test_a_sprint_declared_open_in_prose_cannot_be_closed_in_the_plan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    rows = _tree(monkeypatch, tmp_path, declared="S7")
    problems = todo_index.check_sprint_agreement(rows)
    assert any("declares S7 open" in problem for problem in problems)


def test_a_closed_sprint_that_still_carries_open_tasks_is_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The tolerated list holds S7 only. A second sprint acquiring the same
    # shape has to be a visible act, which is the point of a frozen list over
    # a rule that tolerates the shape wherever it appears.
    rows = _tree(monkeypatch, tmp_path, s8="closed 12 Aug")
    problems = todo_index.check_sprint_agreement(rows)
    assert any("closes S8" in problem and "T36" in problem for problem in problems)


def test_a_tolerated_entry_that_is_no_longer_a_disagreement_is_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Otherwise the list outlives what put it there, which is how the first
    # nineteen unreviewed releases accumulated.
    rows = _tree(monkeypatch, tmp_path, s7="**N/A**", s8="closed 12 Aug")
    problems = todo_index.check_sprint_agreement(rows)
    assert any("remove it from" in problem for problem in problems)


def test_the_sentence_the_check_reads_cannot_be_rephrased_away(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    rows = _tree(monkeypatch, tmp_path)
    todo = tmp_path / "TODO.md"
    todo.write_text(
        todo.read_text(encoding="utf-8").replace(
            "**Sprint S8, declared partial and still open.**", "S8 is roughly where we are."
        ),
        encoding="utf-8",
    )
    problems = todo_index.check_sprint_agreement(rows)
    assert any("no longer declares which sprint is open" in problem for problem in problems)
