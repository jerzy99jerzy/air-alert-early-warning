#!/usr/bin/env python3
"""Executable claims: every limitation in the README is checked against the tree.

A sentence drifts silently; a check drifts loudly. Each bullet under
"What this will not tell you" that carries a ``(lint: NAME)`` marker must have a
registered check here, and that check must pass.
"""

from __future__ import annotations

import re
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "mavo"

LUNAR_TERMS = ("lunar", "moon", "illuminat", "ksiezyc", "waxing", "waning")
NETWORK_MODULES = ("requests", "httpx", "urllib.request", "http.client", "aiohttp", "socket")


def _package_sources() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def _source_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in _package_sources())


def check_no_probability_claim() -> str | None:
    """No module may expose a probability-of-impact API."""
    offenders = [
        path.name
        for path in _package_sources()
        if re.search(r"def\s+\w*(probability|likelihood|chance_of)\w*\s*\(", path.read_text())
    ]
    return f"probability-style API found in {offenders}" if offenders else None


def check_no_lunar_variable() -> str | None:
    """The excluded variable must stay excluded, including in comments."""
    offenders: list[str] = []
    for path in _package_sources():
        lowered = path.read_text(encoding="utf-8").lower()
        offenders += [f"{path.name}:{term}" for term in LUNAR_TERMS if term in lowered]
    return f"lunar terms present in package source: {offenders}" if offenders else None


def check_unknown_not_clear() -> str | None:
    """UNKNOWN must not resolve to CLEAR, and must not be tested by negation."""
    sys.path.insert(0, str(ROOT))
    from mavo.schema import AlertState, is_actionable, is_clear

    if is_clear(AlertState.UNKNOWN) or is_actionable(AlertState.UNKNOWN):
        return "AlertState.UNKNOWN is treated as a safe or actionable state"
    return None


def check_no_ml_dependency() -> str | None:
    """Runtime dependencies stay empty; a model cannot sneak in as a library."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)
    declared = config["project"].get("dependencies", [])
    return f"runtime dependencies declared: {declared}" if declared else None


def check_network_reach_is_one_file() -> str | None:
    """Only ``mavo/transport.py`` may import a network client.

    Tightened in 0.3.0.0 from "no network at all", which stopped being true when
    the Telegram adapter landed. The check was rewritten rather than dropped: a
    claim that becomes false is replaced by the claim that is now true and still
    mechanically checkable.
    """
    offenders: list[str] = []
    for path in _package_sources():
        if path.name == "transport.py":
            continue
        text = path.read_text(encoding="utf-8")
        offenders += [f"{path.name}:{module}" for module in NETWORK_MODULES
                      if f"import {module}" in text]
    return f"network client imported outside transport.py: {offenders}" if offenders else None


CHECKS: dict[str, Callable[[], str | None]] = {
    "no_probability_claim": check_no_probability_claim,
    "no_lunar_variable": check_no_lunar_variable,
    "unknown_not_clear": check_unknown_not_clear,
    "no_ml_dependency": check_no_ml_dependency,
    "network_reach_is_one_file": check_network_reach_is_one_file,
}


def declared_markers() -> list[str]:
    """Markers actually present in the README."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    return re.findall(r"\(lint:\s*([a-z0-9_]+)\)", readme)


def main() -> int:
    """Run every declared check. Returns a process exit code."""
    markers = declared_markers()
    failures: list[str] = []

    if not markers:
        failures.append("README declares no lint markers; the limitations section is unchecked")

    for marker in markers:
        check = CHECKS.get(marker)
        if check is None:
            failures.append(f"README declares (lint: {marker}) with no registered check")
            continue
        problem = check()
        if problem:
            failures.append(f"{marker}: {problem}")

    for name in CHECKS:
        if name not in markers:
            failures.append(f"check '{name}' is registered but no README bullet claims it")

    for failure in failures:
        print(f"lint-limitations: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"lint-limitations: {len(markers)} claims verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
