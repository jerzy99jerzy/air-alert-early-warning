"""F113: a state word inside prose is not a state.

`state_of` scanned the whole status blob, and the entry regex extends that blob
to the first blank line, so an entry's own explanation of its history was read
as its status. Four entries declaring `ready` carried the note "Moved from S8
at 0.32.9.0" and were counted `moved`, which the index renders as closed. Two
of them sat in the open sprint and one was tier 1, so the table that says of
itself that it cannot drift under-reported open work by four and lost the
sprint row's worth from the answer to "what is left".

The data below is written so that a wrong implementation and a right one give
different answers: each case pairs a declared state with prose naming a
different one, and a classifier that reads either the declaration or the prose
alone can be told apart by the pair.

Named mutation for the harness: restore `"moved" in lowered` in place of
``"`moved`" in lowered``. `test_a_provenance_note_is_not_a_state` goes red.
"""

from __future__ import annotations

import pytest

import tools.todo_index as todo_index


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        # The four this defect actually mis-stated, in the shape they carry.
        ("Status: `ready`, **S9** [tier 2]\n"
         "*Moved from S8 at 0.32.9.0, when S8 closed.*", "ready"),
        ("Status: `ready`, **S11** [tier 2]\n"
         "Moved out of the delivery sprint and back again.", "ready"),
        # The declaration still wins when it is the one saying `moved`.
        ("Status: `moved` to the consumer, 0.32.5.0 [tier 2]", "moved"),
        ("Status: `moved` to `mavo-adsb`, which holds the sampler [tier 2]\n"
         "The entry here is a pointer and the work is ready over there.",
         "moved"),
    ],
)
def test_a_provenance_note_is_not_a_state(status: str, expected: str) -> None:
    """Prose about having been moved does not move a task.

    The third and fourth cases are what stops the repair from being "never say
    moved": a classifier that simply dropped the state would pass the first two
    and fail these.
    """
    assert todo_index.state_of(status) == expected


def test_the_open_sprint_keeps_the_tasks_that_declare_it() -> None:
    """The index row and the entries beneath it answer the same question.

    This is the consequence the defect had rather than its mechanism: a task
    whose status names a sprint and declares `ready` belongs in that sprint's
    row, whatever its prose says about where it used to live.
    """
    status = ("Status: `ready`, **S9** [tier 1]\n"
              "*Moved from S8 at 0.32.9.0, when S8 closed.*")
    assert todo_index.state_of(status) == "ready"
    assert todo_index.sprint_of(status) == "S9"


def test_the_repair_did_not_reclassify_anything_else() -> None:
    """Every entry in the live file classifies as the state it declares.

    The first repair attempted for F113 read only the first physical line, and
    it also changed T40 (whose sprint token is on the second line) and T50
    (whose `done` is not on the first). This asserts the property both repairs
    were aiming at, against the file itself, so a future narrowing that breaks
    a multi-line status fails here rather than in a sprint table nobody
    re-derives.
    """
    declared_token = {
        "done": "done", "moved": "moved", "ready": "ready",
        "decision": "decision", "blocked-external": "blocked-external",
        "deferred": "deferred", "debt": "debt",
    }
    disagreements = []
    for task_id, _title, state, _tier, _sprint in todo_index.entries():
        text = todo_index.TODO.read_text(encoding="utf-8")
        marker = f"\n## {task_id}. "
        head = text[text.index(marker) + len(marker):]
        first = head.split("\n", 1)[1].split("\n", 1)[0].lower()
        for token, expected in declared_token.items():
            if f"`{token}`" in first and state != expected:
                disagreements.append(f"{task_id} declares `{token}`, counted {state}")
    assert not disagreements, "; ".join(disagreements)
