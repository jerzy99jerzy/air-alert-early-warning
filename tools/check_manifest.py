#!/usr/bin/env python3
"""`MANIFEST.sha256` covers every tracked file and every hash still holds.

**Why this is not `shasum -c MANIFEST.sha256`.** That command answers one of the
two questions. It reports a listed file whose content changed and a listed file
that vanished, and it is silent about a file the manifest never listed at all,
because a manifest cannot check a line it does not have. Measured on
0.32.4.0 before this tool existed: 23 of 137 listed hashes disagreed with the
tree **and 13 tracked files were absent from the manifest entirely**, among
them `tools/check_no_private_artifacts.py` and `tools/vocab_gaps.py`. The
second figure had never been counted, and it is the weaker failure precisely
because nothing reported it.

**What this detects, stated so nobody reads it as more.** Accident, not an
adversary. The manifest lives in the same repository as the files it lists, so
anyone who can edit a file can edit its line; this is not a tamper-evidence
control and `docs/ARCHITECTURE.md` no longer suggests it is. What it catches is
an incomplete transfer, a zip that disagrees with the tree it claims to be, a
file added to the repository without an entry, and an edit that reached the
tree without reaching the release chain. Those have all happened here.

Truth comes from `git ls-files` rather than a directory walk, so an ignored
build artefact is out of scope by construction rather than by an exclusion list
that has to be maintained. No repository means the question cannot be answered,
which is exit code 2 and not a pass, the same convention
`tools/check_no_private_artifacts.py` uses for the same reason.

`--write` regenerates. It is the only way the file should ever change.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "MANIFEST.sha256"

# The manifest cannot carry its own digest: writing the line changes the file
# the line describes. Excluded by name rather than by a rule about self
# reference, so a reader can see the one gap without deriving it.
EXCLUDED = {"MANIFEST.sha256"}


def tracked_files() -> list[str]:
    """Every path `git` tracks, sorted, excluding the manifest itself."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        print(f"manifest: CANNOT CHECK: git ls-files: {result.stderr.strip()}",
              file=sys.stderr)
        raise SystemExit(2)
    return sorted(
        path for path in result.stdout.splitlines()
        if path and path not in EXCLUDED
    )


def digest(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def listed() -> dict[str, str]:
    """The manifest as a mapping, or an empty one when it does not exist."""
    if not MANIFEST.exists():
        return {}
    entries: dict[str, str] = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            continue
        entries[parts[1].lstrip("*")] = parts[0]
    return entries


def write() -> int:
    paths = tracked_files()
    MANIFEST.write_text(
        "".join(f"{digest(path)}  {path}\n" for path in paths),
        encoding="utf-8",
    )
    print(f"manifest: written, {len(paths)} file(s)")
    return 0


def check() -> int:
    paths = tracked_files()
    entries = listed()
    problems: list[str] = []

    unlisted = [path for path in paths if path not in entries]
    for path in unlisted:
        problems.append(f"tracked and absent from the manifest: {path}")

    untracked = sorted(set(entries) - set(paths))
    for path in untracked:
        problems.append(f"listed and no longer tracked: {path}")

    for path in paths:
        expected = entries.get(path)
        if expected is None:
            continue
        if digest(path) != expected:
            problems.append(f"content differs from its entry: {path}")

    for problem in problems:
        print(f"manifest: {problem}", file=sys.stderr)
    if problems:
        print(
            f"manifest: {len(problems)} problem(s); run "
            "`python3 tools/check_manifest.py --write` as part of the release "
            "chain, never as a way of making this check green",
            file=sys.stderr,
        )
        return 1
    print(f"manifest: OK, {len(paths)} tracked file(s), every hash holds")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true",
                        help="regenerate the manifest from the tracked files")
    args = parser.parse_args()
    return write() if args.write else check()


if __name__ == "__main__":
    sys.exit(main())
