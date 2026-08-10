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

ENTRY = re.compile(r"^## (T\d+)\. (.+?)$\n(Status:.*?)(?=\n\n|\n##|\Z)", re.M | re.S)
BEGIN = "<!-- index:begin -->"
END = "<!-- index:end -->"

STATES = ("done", "ready", "decision", "blocked-external", "deferred", "debt")
SPRINTS = ("S7", "S8", "S9", "S10", "S11")


def state_of(status: str) -> str:
    """The first state word the status line carries.

    Ordered rather than searched: `done` wins over everything, because a task
    that is finished is finished whatever else its line still says about what
    it used to block.
    """
    lowered = status.lower()
    if "done" in lowered or "largely met" in lowered:
        return "done"
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
    done = by_state.get("done", 0)
    open_now = total - done

    lines = [BEGIN, "", "### Where the backlog stands", "",
             f"**{done} of {total} closed, {open_now} open.** Counted from the entries "
             f"below by `tools/todo_index.py`, which the gate re-runs, so this "
             f"table cannot drift from the list it summarises.", "",
             "| State | Count | What it means |", "| --- | --- | --- |"]
    meanings = {
        "done": "Finished, with the release that closed it named in the entry",
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
        chosen = [r for r in rows if r[3] == tier and r[2] != "done"]
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
        chosen = [r for r in rows if r[4] == sprint and r[2] != "done"]
        if chosen:
            listed = ", ".join(f"[{r[0]}](#{_anchor(r[0], r[1])})" for r in chosen)
            lines.append(f"| **{sprint}** | {listed} |")
    lines += ["", END]
    return "\n".join(lines)


def _anchor(task_id: str, title: str) -> str:
    """GitHub's anchor for a task heading, reimplemented as elsewhere in the gate."""
    heading = f"{task_id}. {title}"
    return re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")


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
        if current.strip() != fresh.strip():
            print("todo-index: the index disagrees with the entries below it; "
                  "run `python3 tools/todo_index.py`", file=sys.stderr)
            return 1
        unstated = [r[0] for r in rows if r[3] == "unstated" and r[2] != "done"]
        if unstated:
            print(f"todo-index: open tasks with no tier: {', '.join(unstated)}",
                  file=sys.stderr)
            return 1
        print(f"todo-index: {len(rows)} tasks, index holds")
        return 0

    TODO.write_text(text.replace(current, fresh), encoding="utf-8")
    print(f"todo-index: index regenerated, {len(rows)} tasks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
