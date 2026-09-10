#!/usr/bin/env python3
"""Invariants specific to this repository.

These substitute for a second pair of eyes: a single maintainer cannot notice a
structural claim going stale, so the structure is asserted.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_baserate_is_top_level() -> list[str]:
    """The null model stays visible in the tree rather than folded into a helper."""
    if not (ROOT / "mavo" / "baserate.py").exists():
        return ["mavo/baserate.py is missing; the null model must be a top-level module"]
    return []


def check_single_namespace() -> list[str]:
    """Exactly one importable top-level package."""
    candidates = [
        path.name
        for path in ROOT.iterdir()
        if path.is_dir() and (path / "__init__.py").exists()
    ]
    if candidates != ["mavo"]:
        return [f"expected exactly one top-level package 'mavo', found {candidates}"]
    return []


def check_every_sprint_has_a_regression_file() -> list[str]:
    """Sprints declared shipped in STATUS.json have a regression file.

    Previously this scraped the changelog for the word "sprint", which meant a
    sentence naming future work failed the build. Shipped is a fact recorded in
    STATUS.json, not a word appearing in prose.
    """
    import json

    status = ROOT / "STATUS.json"
    if not status.exists():
        return ["STATUS.json is missing"]
    sprints = {str(number) for number in json.loads(status.read_text())["sprint_test_files"]}
    missing = [
        number
        for number in sorted(sprints)
        if not (ROOT / f"tests/test_sprint{number}.py").exists()
    ]
    return [f"sprint {number} has no tests/test_sprint{number}.py" for number in missing]


def check_docs_case_convention() -> list[str]:
    """Design documents uppercase, generated artefacts lowercase."""
    problems: list[str] = []
    for path in sorted((ROOT / "docs").glob("*.md")):
        stem = path.stem
        if stem.startswith("report"):
            continue
        if stem != stem.upper():
            problems.append(f"docs/{path.name} is a design document and must be UPPERCASE.md")
    return problems


def check_the_pipeline_does_not_import_its_reader() -> list[str]:
    """No module under `mavo/` may import `tools.progress`.

    `docs/OBSERVABILITY.md` section 6 asks for this and the last acceptance
    criterion in section 9 says it is a lint rather than an intention. The
    reason is not layering hygiene: a progress indicator wired into the run
    would be a second statement about where the run is, and the first thing it
    would do is disagree with the log. One writer, one record, one direction.
    """
    problems = []
    for module in sorted((ROOT / "mavo").rglob("*.py")):
        text = module.read_text(encoding="utf-8")
        if "tools.progress" in text or "from tools import progress" in text:
            problems.append(
                f"{module.relative_to(ROOT)} imports the run log's reader; the "
                "pipeline writes the record and never reads it back"
            )
    return problems


def _opens_the_store(source: str) -> bool:
    """True when this module reaches the event store itself.

    Read from the syntax tree rather than by substring, and the difference is
    not fastidiousness: `tools/manual_audit.py` names `EventStore` in a comment
    about which commands construct one, and a grep-shaped check would have
    called that an instrument and demanded it move. Two signals count, and both
    are acts rather than mentions: a call to ``sqlite3.connect``, and an import
    from ``mavo.store``. A forwarding shim does neither - it imports the module
    that does - which is why the two shims in `tools/` need no exemption entry,
    and an exemption list nobody has to maintain cannot rot into one.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # An unparseable module is somebody else's failure and this check has
        # nothing to say about it; `lint` fails on it one target earlier.
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # Exact, or a submodule of it. `startswith` alone would call a
            # hypothetical `mavo.storefront` a store reader, which is a small
            # thing until the day somebody adds one and cannot work out why
            # the gate is asking them to ship it as a subcommand.
            if module == "mavo.store" or module.startswith("mavo.store."):
                return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "connect"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "sqlite3"
        ):
            return True
    return False


def check_no_tool_reads_the_store(root: Path | None = None) -> list[str]:
    """D-038 against the population it governs, not against one worked example.

    The decision says an instrument whose input is the **store** ships as a
    `mavo` subcommand, and one whose input is the **tree** stays in `tools/`.
    It was adopted after `attempts.py` was found unrunnable on the host that
    holds a store, `attempts.py` was moved, and `latency.py` - same connection,
    same file, same host - was left where it was for twenty-three releases. The
    stated blocker on T40 was a discharged one the whole time; the real one was
    this, and it was invisible because a rule with one worked example looks
    satisfied. Nothing compared the decision against its population, so this
    does, and T84 is the entry that asked for it.

    What it cannot see: an instrument that reads the store through a subprocess,
    or over SSH, or by a path this function does not recognise as a connection.
    The check is narrower than the decision and saying so here is cheaper than
    a reader assuming otherwise.
    """
    tree_root = root if root is not None else ROOT
    tools = tree_root / "tools"
    if not tools.is_dir():
        return [f"{tools} is not a directory; this check reads the tools tree"]
    problems = []
    for module in sorted(tools.rglob("*.py")):
        if _opens_the_store(module.read_text(encoding="utf-8")):
            problems.append(
                f"{module.relative_to(tree_root)} opens the event store from "
                "`tools/`, which the wheel does not install, so it cannot run "
                "on the host that holds one (D-038). Ship it as a `mavo` "
                "subcommand and leave a forwarding shim"
            )
    return problems


def main() -> int:
    """Run every domain invariant. Returns a process exit code."""
    problems = (
        check_baserate_is_top_level()
        + check_single_namespace()
        + check_every_sprint_has_a_regression_file()
        + check_docs_case_convention()
        + check_the_pipeline_does_not_import_its_reader()
        + check_no_tool_reads_the_store()
    )
    for problem in problems:
        print(f"lint-domain: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("lint-domain: invariants hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
