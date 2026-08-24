#!/usr/bin/env python3
"""An adapter that parses somebody else's bytes ships with its hostile suite.

T4, and the rule is older than the check. Sprint 4 delivered the hostile suite
for the Telegram adapter after F17 found that a malformed message took the
collector down; harness attack A9 pins it. What was never written down in a
form a build could read is the rule for the *next* adapter, and this repository
has added two since: `ukrainealarm` and `rso`.

**The rule.** A module under `mavo/sources/` that turns external bytes into
this package's types is an adapter. Every adapter has a test module naming it,
and that module exercises hostile input: malformed, truncated, oversized, or
structurally wrong. An adapter without one is reported here rather than
discovered by the thing it failed to survive.

**What decides that a module is an adapter, and why it is not `ThreatSource`.**
`rso.py` implements no `ThreatSource` - it is a reader for a Polish feed that
has no alert semantics yet - and it parses a third party's JSON, which is the
property that matters. Keying on the protocol would have exempted the newest
parser in the tree. Keying on *parsing external bytes* is the honest rule, and
`fixture.py` is exempt by the same rule rather than by a name: it generates
rather than parses, which is also why harness A7 stands unverified.

**What this cannot do.** It reads for the presence of hostile cases, not for
their quality. A test named for hostile input that asserts nothing would pass
here and fail a reader, and no counter can tell those apart. This measures that
the work was attempted, which is the same trade the mutation register makes at
one level down.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "mavo" / "sources"
TESTS = ROOT / "tests"

#: Modules under `mavo/sources/` that are not adapters, each with the reason.
#: A name added here without one is the exemption this check exists to refuse.
NOT_AN_ADAPTER = {
    "__init__.py": "the protocol and its exports; parses nothing",
    "fixture.py": "generates synthetic nights rather than parsing bytes, which "
                  "is why harness A7 carries no mutation either",
}

#: Evidence that a test module exercises hostile input. Names rather than
#: assertions, for the reason the docstring states.
HOSTILE = re.compile(
    r"hostile|malformed|truncated|oversized|garbage|not_json|invalid_json|"
    r"does_not_raise|never_raises|unparseable|corrupt",
    re.I,
)

#: Calls that mean a module reads a third party's bytes.
PARSES = ("loads", "load", "fromisoformat", "parse", "findall", "search", "match")


def _parses_external_bytes(path: Path) -> bool:
    """True when the module decodes or scans input it did not produce."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in PARSES:
            return True
        if isinstance(node, ast.Name) and node.id in {"json", "html"}:
            return True
    return False


def main() -> int:
    """Report every adapter with no hostile suite. Returns an exit code."""
    problems: list[str] = []
    checked = 0
    for path in sorted(SOURCES.glob("*.py")):
        if path.name in NOT_AN_ADAPTER:
            continue
        if not _parses_external_bytes(path):
            problems.append(
                f"mavo/sources/{path.name} parses nothing this check can see; "
                f"either it is not an adapter and belongs in NOT_AN_ADAPTER "
                f"with a reason, or the rule needs widening"
            )
            continue
        checked += 1
        stem = path.stem
        covering = [
            test for test in sorted(TESTS.glob("test_*.py"))
            if stem in test.read_text(encoding="utf-8")
        ]
        if not covering:
            problems.append(f"mavo/sources/{path.name} is named by no test module (T4)")
            continue
        hostile = [t for t in covering if HOSTILE.search(t.read_text(encoding="utf-8"))]
        if not hostile:
            problems.append(
                f"mavo/sources/{path.name} has tests but none of them "
                f"({', '.join(t.name for t in covering)}) exercises hostile "
                f"input; an adapter parsing somebody else's bytes ships with "
                f"one (T4)"
            )
    for problem in problems:
        print(f"lint-adapters: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"lint-adapters: {checked} adapter(s), each with a hostile suite; "
          f"{len(NOT_AN_ADAPTER)} exempt with reasons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
