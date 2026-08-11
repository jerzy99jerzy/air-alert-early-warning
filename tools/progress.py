#!/usr/bin/env python3
"""Read the run log. Nothing in the pipeline knows this exists.

`docs/OBSERVABILITY.md` section 6: a progress indicator wired into the run
would be a second statement about where the run is, and the first thing it
would do is disagree with the log. So the dependency runs one way only, and
`tests/lint_domain.py` fails the build if any module under `mavo/` imports
this - enforced rather than intended, in the same family as the rule that keeps
network reach in one file.

The stage vocabulary is imported from `mavo.obs`. Restating it here would be
two lists that agree until the day they do not.

**What this refuses to do.** It never renders `null` as zero. A line carrying
`"skipped": null` beside `"skipped_reason"` prints `skipped=unknown (reason)`,
because the difference between a measured zero and an unmeasurable quantity is
the difference this whole project is built on, and a reader is the last place
it can be quietly lost.

**A truncated final line is reported, not skipped.** The sink writes whole
lines or nothing (F51), so a partial line means the file was cut by something
other than the writer - a full disk, a copy taken mid-append, a killed `tee`.
Dropping it silently would turn evidence of a problem into an absence of
evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mavo.obs import SCHEMA, STAGES  # noqa: E402


@dataclass
class Recap:
    """What a run did, as read back from its own record."""

    lines: int = 0
    truncated_tail: bool = False
    unreadable: int = 0
    future_schema: int = 0
    cycles: set[str] = field(default_factory=set)
    by_stage: Counter[str] = field(default_factory=Counter)
    by_level: Counter[str] = field(default_factory=Counter)
    unknowns: Counter[str] = field(default_factory=Counter)
    rotation: str | None = None
    retain: int | None = None
    bodies_enabled: bool = False

    def render(self) -> str:
        """The recap, with every gap named rather than smoothed."""
        out = [f"progress: {self.lines} lines, {len(self.cycles)} cycles"]
        if self.rotation is not None:
            out.append(
                f"  retention: rotation={self.rotation} retain={self.retain} "
                "(older evidence is in the numbered siblings, if any)"
            )
        else:
            out.append(
                "  retention: unknown - this file carries no sink.opened line, "
                "so it is a fragment and its start is not the run's start"
            )
        stages = " ".join(
            f"{stage}={self.by_stage.get(stage, 0)}" for stage in STAGES
        )
        out.append(f"  stages: {stages}")
        if self.by_level:
            out.append(
                "  levels: "
                + " ".join(f"{name}={count}" for name, count in sorted(self.by_level.items()))
            )
        if self.unknowns:
            out.append("  unknown values, by reason:")
            out.extend(
                f"    {reason}: {count}"
                for reason, count in sorted(self.unknowns.items())
            )
        else:
            out.append("  unknown values: none recorded")
        if self.bodies_enabled:
            out.append(
                "  WARNING: this log was written with MAVO_LOG_BODIES=1 and may "
                "carry message text"
            )
        if self.unreadable:
            out.append(f"  unreadable lines: {self.unreadable}")
        if self.truncated_tail:
            out.append(
                "  GAP: the last line is truncated. The sink writes whole lines, "
                "so something outside it cut this file; the run's tail is missing "
                "rather than empty"
            )
        if self.future_schema:
            out.append(
                f"  {self.future_schema} lines carry a schema newer than v{SCHEMA}; "
                "their fields are reported as read, not reinterpreted"
            )
        return "\n".join(out)


def read(path: Path) -> Recap:
    """Fold a run log into a recap. Never raises on content."""
    recap = Recap()
    raw = path.read_bytes()
    if not raw:
        return recap
    tail_complete = raw.endswith(b"\n")
    for index, chunk in enumerate(raw.decode("utf-8", errors="replace").splitlines()):
        if not chunk.strip():
            continue
        last = index == len(raw.decode("utf-8", errors="replace").splitlines()) - 1
        try:
            record = json.loads(chunk)
        except ValueError:
            if last and not tail_complete:
                recap.truncated_tail = True
            else:
                recap.unreadable += 1
            continue
        if not isinstance(record, dict):
            recap.unreadable += 1
            continue
        recap.lines += 1
        if int(record.get("v", 0)) > SCHEMA:
            recap.future_schema += 1
        stage = str(record.get("stage", ""))
        recap.by_stage[stage] += 1
        recap.by_level[str(record.get("level", "INFO"))] += 1
        cycle = record.get("cycle")
        if isinstance(cycle, str):
            recap.cycles.add(cycle)
        if record.get("event") == "sink.opened":
            recap.rotation = record.get("rotation")
            recap.retain = record.get("retain")
        if record.get("event") == "sink.bodies_enabled":
            recap.bodies_enabled = True
        for key, value in record.items():
            if key.endswith("_reason") and record.get(key[: -len("_reason")]) is None:
                recap.unknowns[str(value)] += 1
    return recap


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="path", required=True, help="run log to read")
    args = parser.parse_args(argv)
    path = Path(args.path)
    if not path.is_file():
        print(f"progress: no run log at {path}", file=sys.stderr)
        return 2
    print(read(path).render())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
