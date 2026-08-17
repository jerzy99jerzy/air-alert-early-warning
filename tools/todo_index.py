#!/usr/bin/env python3
"""Count the backlog from the backlog, and fail when the index disagrees.

`TODO.md` grew to forty-odd entries with their state written in prose, which
means the only way to answer "how much is left" was to read all of it and
count by hand. A hand count is a number nobody can check and everybody quotes,
which is the shape of F31 and F73.

This tool reads the entries, classifies them by the `Status:` line each one
already carries, and regenerates the index block at the top of the file.
`--check` compares the block against the entries and returns non-zero on a
mismatch, so the gate catches an index that drifted rather than a reader
discovering it.

Tiers are declared per task in the status line as `[tier 1]`, `[tier 2]` or
`[tier 3]`, and an entry without one is reported rather than defaulted: a
task nobody has prioritised is a decision nobody has made, and hiding it in
tier 3 would make the omission invisible.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODO = ROOT / "TODO.md"

# T62. The identifier admits an optional letter suffix, and the widening is the
# whole point of the release that made it. Before 0.32.5.0 this pattern was
# `^## (T\d+)\.`, so `T8a` and `T8b` were not entries as far as this repository's
# tooling was concerned: the file held sixty-one headings and every number this
# tool printed described fifty-nine of them. Neither task was listed in the
# index, neither could be reported as untiered, and
# `check_identifiers_are_unique` would have passed a file holding two `## T8a.`
# entries. A check that cannot see an entry reports the file it can see, which
# is the failure mode this tool exists to remove one level up.
ENTRY = re.compile(r"^## (T\d+[a-z]?)\. (.+?)$\n(Status:.*?)(?=\n\n|\n##|\Z)", re.M | re.S)
BEGIN = "<!-- index:begin -->"
END = "<!-- index:end -->"

STATES = ("done", "moved", "ready", "decision", "blocked-external", "deferred",
          "debt")

# States that take a task out of this repository's open count. `done` is the
# work being finished; `moved` is the work belonging to another repository, and
# it is a distinct state rather than a flavour of `done` because nothing here
# can say whether it was finished. Counting a moved task as open would keep it
# in this backlog for as long as the other repository takes, which is how three
# site tasks sat in the producer's tier-2 list while nothing on the side that
# would do them was tracking them at all.
CLOSED_HERE = ("done", "moved")
SPRINTS = ("S7", "S8", "S9", "S10", "S11")

MVP = ROOT / "docs" / "MVP.md"
OPEN_SPRINT = re.compile(r"\*\*Sprint (S\d+), declared[^*]*open\.\*\*")
MVP_ROW = re.compile(r"^\| \*\*(S\d+)\*\* \| ([^|]*)\|", re.M)

# Sprints whose MVP row says closed while tasks in TODO still carry them.
# A frozen list with a written reason rather than a tolerance rule, for the
# reason the unreviewed-release set in `docs_audit.py` gives: a rule that
# tolerates a shape absorbs the next instance silently, and a named entry is a
# visible act. `check_sprint_agreement` removes an entry that stops being a
# real disagreement, so this cannot rot into a permanent exemption.
TOLERATED_OPEN_IN_A_CLOSED_SPRINT = {
    "S7": (
        "MVP.md records S7 as met on an amended criterion, and T31, T33 and "
        "T34 are work that amended criterion did not require. Whether the row "
        "is amended or the three tasks are reassigned is a decision, not a "
        "bookkeeping repair, and it is not made by this list"
    ),
}


def state_of(status: str) -> str:
    """The first state word the status line carries.

    Ordered rather than searched: `done` wins over everything, because a task
    that is finished is finished whatever else its line still says about what
    it used to block.
    """
    lowered = status.lower()
    if "done" in lowered or "largely met" in lowered:
        return "done"
    if "moved" in lowered:
        return "moved"
    for state in ("blocked-external", "deferred", "debt", "decision"):
        if state in lowered:
            return state
    return "ready" if "ready" in lowered else "unstated"


def tier_of(status: str) -> str:
    """The declared tier, or `unstated`."""
    match = re.search(r"\[tier ([123])\]", status)
    return match.group(1) if match else "unstated"


def sprint_of(status: str) -> str:
    """The sprint a task is assigned to, or `unassigned`."""
    for sprint in SPRINTS:
        if f"**{sprint}**" in status or f"`{sprint}`" in status:
            return sprint
    return "unassigned"


def entries() -> list[tuple[str, str, str, str, str]]:
    """Every task as (id, title, state, tier, sprint)."""
    text = TODO.read_text(encoding="utf-8")
    found = []
    for task_id, title, status in ENTRY.findall(text):
        found.append(
            (task_id, title.strip(), state_of(status), tier_of(status), sprint_of(status))
        )
    return found


def render_index(rows: list[tuple[str, str, str, str, str]]) -> str:
    """The block that sits at the top of the file."""
    by_state: dict[str, int] = {}
    for _id, _title, state, _tier, _sprint in rows:
        by_state[state] = by_state.get(state, 0) + 1
    total = len(rows)
    closed = sum(by_state.get(state, 0) for state in CLOSED_HERE)
    open_now = total - closed

    lines = [BEGIN, "", "### Where the backlog stands", "",
             f"**{closed} of {total} closed, {open_now} open.** Counted from the entries "
             f"below by `tools/todo_index.py`, which the gate re-runs, so this "
             f"table cannot drift from the list it summarises.", "",
             "| State | Count | What it means |", "| --- | --- | --- |"]
    meanings = {
        "done": "Finished, with the release that closed it named in the entry",
        "moved": "Owned by another repository; the entry here is a pointer, "
                 "not a copy",
        "ready": "Nothing external blocks it; it needs a session",
        "decision": "Waiting on a judgement rather than on work",
        "blocked-external": "Waiting on somebody outside this project",
        "deferred": "Deliberately parked, with the decision that parked it named",
        "debt": "Known cost carried on purpose",
        "unstated": "**No state in the entry. This is a defect in the entry.**",
    }
    for state in (*STATES, "unstated"):
        count = by_state.get(state, 0)
        if count:
            lines.append(f"| `{state}` | {count} | {meanings[state]} |")

    lines += ["", "### Priority tiers", "",
              "Tiers are a claim about *order*, not about importance, and they move "
              "as the project moves. Declared per entry so this table is generated "
              "rather than maintained.", "",
              "| Tier | Meaning |", "| --- | --- |",
              "| **1** | Blocks something already promised, or a measurement without "
              "which a shipped claim is unsupported |",
              "| **2** | Real work that nothing is waiting on today |",
              "| **3** | Worth doing, worth dropping if the project turns |", ""]
    for tier in ("1", "2", "3", "unstated"):
        chosen = [r for r in rows if r[3] == tier and r[2] not in CLOSED_HERE]
        if not chosen:
            continue
        label = f"Tier {tier}" if tier != "unstated" else "**Tier not declared**"
        lines.append(f"**{label}, {len(chosen)} open:** "
                     + ", ".join(f"[{r[0]}](#{_anchor(r[0], r[1])})" for r in chosen))
        lines.append("")

    lines += ["### By sprint", "",
              "Sprint numbering follows `docs/MVP.md`. Tasks with no sprint are "
              "either outside the beta path or not yet placed on it.", "",
              "| Sprint | Open tasks |", "| --- | --- |"]
    for sprint in (*SPRINTS, "unassigned"):
        chosen = [r for r in rows if r[4] == sprint and r[2] not in CLOSED_HERE]
        if chosen:
            listed = ", ".join(f"[{r[0]}](#{_anchor(r[0], r[1])})" for r in chosen)
            lines.append(f"| **{sprint}** | {listed} |")
    lines += ["", END]
    return "\n".join(lines)


def _anchor(task_id: str, title: str) -> str:
    """GitHub's anchor for a task heading, reimplemented as elsewhere in the gate."""
    heading = f"{task_id}. {title}"
    return re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")



def closed_in_the_plan() -> set[str]:
    """Sprints whose ``docs/MVP.md`` row declares a closing date."""
    return {
        sprint
        for sprint, window in MVP_ROW.findall(MVP.read_text(encoding="utf-8"))
        if window.strip().lower().startswith("closed")
    }


def check_identifiers_are_unique(
    rows: list[tuple[str, str, str, str, str]],
) -> list[str]:
    """Two entries may not carry the same `T<n>`.

    The index above counts entries, and a count is blind to identity: three
    identifiers were issued twice while every number in the table stayed
    correct, because fifty-eight entries with fifty-five distinct names still
    total fifty-eight. Completeness and uniqueness are different questions and
    only the first had a check, which is D-S34's shape in the consumer and
    F31's in this repository.

    What a collision costs is not tidiness. `docs/DEPLOYMENT.md` says "tracked
    as T57" and the CHANGELOG closes a different T57 four hundred lines apart;
    a sentence naming a task no longer names one task. The number is issued
    from memory rather than derived from the file, which is the same mechanism
    as a version typed at tag time.
    """
    seen: dict[str, list[str]] = {}
    for task_id, title, _state, _tier, _sprint in rows:
        seen.setdefault(task_id, []).append(title)
    return [
        f"{task_id} is used by {len(titles)} entries: "
        + "; ".join(f"\u201c{t}\u201d" for t in titles)
        for task_id, titles in sorted(seen.items())
        if len(titles) > 1
    ]


def check_sprint_agreement(rows: list[tuple[str, str, str, str, str]]) -> list[str]:
    """TODO's prose, the entries beneath it, and the plan must say one thing.

    Review R-4 of 0.23.1.0 found three artefacts disagreeing about which sprint
    was open: ``STATUS.json`` counted nine sprints shipped, ``TODO.md`` said S8
    was partial and open, and ``docs/MANUAL.md`` referred to sprint 6 in the
    future tense. The first was repaired by renaming the field to what it
    measures. This is the other half, and it is the half that matters: a wrong
    status is worse than a wrong priority, because status ends arguments.

    Two things are checked, and neither is a matter of judgement. The sprint
    TODO declares open cannot be one the plan calls closed. And a sprint the
    plan calls closed cannot still carry open tasks, unless it is named in
    ``TOLERATED_OPEN_IN_A_CLOSED_SPRINT`` with a reason, in which case it must
    still be a real disagreement - an entry that has been resolved is reported
    so the list shrinks by the gate rather than by memory.
    """
    text = TODO.read_text(encoding="utf-8")
    closed = closed_in_the_plan()
    problems: list[str] = []
    if not closed:
        problems.append(
            "no sprint row in docs/MVP.md declares a closing window; this check "
            "reads that column and cannot verify a rephrasing"
        )
    declared = OPEN_SPRINT.search(text)
    if declared is None:
        problems.append(
            "TODO.md no longer declares which sprint is open in the sentence "
            "this check reads; a plan whose current sprint is implicit is the "
            "state R-4 found"
        )
    elif declared.group(1) in closed:
        problems.append(
            f"TODO.md declares {declared.group(1)} open and docs/MVP.md gives it "
            "a closing window"
        )
    still_open: dict[str, list[str]] = {}
    for task_id, _title, state, _tier, sprint in rows:
        if sprint in closed and state not in CLOSED_HERE:
            still_open.setdefault(sprint, []).append(task_id)
    for sprint, tasks in sorted(still_open.items()):
        if sprint not in TOLERATED_OPEN_IN_A_CLOSED_SPRINT:
            problems.append(
                f"docs/MVP.md closes {sprint} and {', '.join(tasks)} are still "
                f"open under it; amend the row, move the tasks, or name {sprint} "
                "in TOLERATED_OPEN_IN_A_CLOSED_SPRINT with a reason"
            )
    for sprint in sorted(TOLERATED_OPEN_IN_A_CLOSED_SPRINT):
        if sprint not in still_open:
            problems.append(
                f"{sprint} is named as tolerating open tasks in a closed sprint "
                "and no longer has any; remove it from "
                "TOLERATED_OPEN_IN_A_CLOSED_SPRINT"
            )
    return problems


def main() -> int:
    """Regenerate or check the index. Returns a process exit code."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="compare without writing; non-zero when they disagree")
    args = parser.parse_args()

    rows = entries()
    if not rows:
        print("todo-index: no task entries found in TODO.md", file=sys.stderr)
        return 1
    fresh = render_index(rows)
    text = TODO.read_text(encoding="utf-8")

    if BEGIN not in text or END not in text:
        if args.check:
            print("todo-index: TODO.md carries no index block", file=sys.stderr)
            return 1
        text = text.replace("# TODO\n", "# TODO\n\n" + fresh + "\n", 1)
        TODO.write_text(text, encoding="utf-8")
        print(f"todo-index: index written, {len(rows)} tasks")
        return 0

    current = text[text.index(BEGIN):text.index(END) + len(END)]
    if args.check:
        # First, because a colliding identifier makes every later message
        # ambiguous: "T57 is open under S9" names two tasks, not one.
        collisions = check_identifiers_are_unique(rows)
        if collisions:
            for problem in collisions:
                print(f"todo-index: {problem}", file=sys.stderr)
            return 1
        if current.strip() != fresh.strip():
            print("todo-index: the index disagrees with the entries below it; "
                  "run `python3 tools/todo_index.py`", file=sys.stderr)
            return 1
        unstated = [r[0] for r in rows if r[3] == "unstated"
                    and r[2] not in CLOSED_HERE]
        if unstated:
            print(f"todo-index: open tasks with no tier: {', '.join(unstated)}",
                  file=sys.stderr)
            return 1
        disagreements = check_sprint_agreement(rows)
        if disagreements:
            for problem in disagreements:
                print(f"todo-index: {problem}", file=sys.stderr)
            return 1
        print(f"todo-index: {len(rows)} tasks, index holds, sprint status agrees")
        return 0

    TODO.write_text(text.replace(current, fresh), encoding="utf-8")
    print(f"todo-index: index regenerated, {len(rows)} tasks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
