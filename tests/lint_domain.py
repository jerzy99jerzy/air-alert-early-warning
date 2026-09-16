#!/usr/bin/env python3
"""Invariants specific to this repository.

These substitute for a second pair of eyes: a single maintainer cannot notice a
structural claim going stale, so the structure is asserted.
"""

from __future__ import annotations

import argparse
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


def _delegating_subcommands(root: Path) -> dict[str, Path]:
    """Subcommands whose work is a module's own `main`, found from the imports.

    `mavo/cli.py` writes `from mavo.latency import main as latency_main`, so
    the pairing is in the syntax tree and needs no hand-maintained list - a
    list here would be the thing that rots while the check reports green.
    """
    source = (root / "mavo" / "cli.py").read_text(encoding="utf-8")
    found: dict[str, Path] = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ImportFrom):
            continue
        module_name = node.module or ""
        if not module_name.startswith("mavo."):
            continue
        stem = module_name.split(".")[-1]
        for alias in node.names:
            if alias.name == "main" and alias.asname == f"{stem}_main":
                module = root / "mavo" / f"{stem}.py"
                if module.exists():
                    found[stem] = module
    return found


def _options_declared_in(module: Path) -> set[str]:
    """Every `--flag` the module's own parser accepts, read from the source."""
    flags: set[str] = set()
    for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                        and arg.value.startswith("--"):
                    flags.add(arg.value)
    return flags


def check_a_delegating_subcommand_mirrors_its_module(root: Path | None = None) -> list[str]:
    """F157. Two parsers describe one command and must accept the same flags.

    `mavo latency` rebuilds an argv and hands it to `mavo/latency.py`. The
    module grew `--source` at 0.54.0.0 and the subcommand did not, so the
    command two documents printed for the one outstanding measurement of a
    just-closed sprint exited 2 with `unrecognized arguments`.

    Nothing caught it, and the reason is directional rather than absent.
    `manual_audit.check_every_option_documented` walks the *CLI parser* and
    requires each flag to appear in the manual; a flag that never reaches the
    CLI parser is outside its walk, and the manual agreed with the parser
    because both were missing the same one. Twenty-four regressions covered
    the module and every one called `main` directly. The seam between the two
    parsers had no reader; this is it.

    Only one direction is enforced, deliberately: every flag the module
    accepts must be reachable through the subcommand. The reverse would forbid
    a subcommand adding an option of its own, and `attempts` may yet want one.
    """
    tree_root = root if root is not None else ROOT
    sys.path.insert(0, str(tree_root))
    from mavo.cli import build_parser

    subparsers: dict[str, argparse.ArgumentParser] = {}
    for action in build_parser()._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            subparsers.update(choices)

    problems: list[str] = []
    for name, module in sorted(_delegating_subcommands(tree_root).items()):
        sub = subparsers.get(name)
        if sub is None:
            problems.append(
                f"mavo/cli.py imports {module.name}'s main as {name}_main and "
                f"registers no `{name}` subcommand"
            )
            continue
        exposed = {flag for option in sub._actions for flag in option.option_strings}
        for flag in sorted(_options_declared_in(module) - exposed):
            problems.append(
                f"`mavo {name}` does not accept {flag}, which mavo/{module.name} "
                "accepts. A caller reading the module's usage gets "
                "`unrecognized arguments` (F157)"
            )
    return problems


#: The modules whose functions open a store on an operator's or a unit's
#: behalf. `mavo/store.py` is not here: it is the thing being opened.
_STORE_OPENERS = ("mavo/cli.py", "mavo/attempts.py")


def _calls(node: ast.AST) -> set[str]:
    """Every name called anywhere inside `node`, plain or as an attribute."""
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        target = child.func
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, ast.Attribute):
            names.add(target.attr)
    return names


def check_every_store_opener_announces_migrations(root: Path | None = None) -> list[str]:
    """F168. A function that constructs an `EventStore` also prints what the open moved.

    `EventStore.__init__` creates a missing recorded table and adds a missing
    recorded column on every open, and records the fact in
    `migrations_applied` for the caller to print - "once, at the moment it
    happens, in the journal a person greps" (0.53.4.0). The printing was
    beside the two collectors and nowhere else, so `mavo report`, which runs
    on the host as a long-lived unit, created three tables without a line
    when it opened the store first after an install. A migration announced
    only by whichever command opens the store first is announced by chance.

    Read from the syntax tree, per function: a function whose body calls
    `EventStore` must also call `_announce_migrations` or `migration_lines`.
    The two openers outside `cli.py` are `attempts.py`, which is listed, and
    `latency.py`, which reads the file through `sqlite3` directly and creates
    nothing, so it is not an opener in this sense.
    """
    tree_root = root if root is not None else ROOT
    problems: list[str] = []
    for relative in _STORE_OPENERS:
        module = tree_root / relative
        if not module.exists():
            problems.append(f"{relative} is missing; this check reads it")
            continue
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            called = _calls(node)
            if "EventStore" not in called:
                continue
            if called & {"_announce_migrations", "migration_lines"}:
                continue
            problems.append(
                f"{relative}::{node.name} constructs an EventStore and prints nothing "
                "about what the open migrated; a table created in silence is the "
                "repair the store refuses (F168)"
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
        + check_a_delegating_subcommand_mirrors_its_module()
        + check_every_store_opener_announces_migrations()
    )
    for problem in problems:
        print(f"lint-domain: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("lint-domain: invariants hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
