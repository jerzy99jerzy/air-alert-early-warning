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

**Two questions, two commands, and the split is the repair for F101.** Both
lived in one check inside `verify` at 0.32.5.0, and the hash half made the gate
unrunnable after any edit to any tracked file: hashes are a property of a
*commit*, and a working tree under edit is supposed to differ from one. The
only way past a red gate was to regenerate, which is the act this tool's own
error message forbids. A control that produces the behaviour it prohibits is
worse than no control, because it teaches the operator to reach for the
override.

- **Completeness** is a property of the tree at any moment: every tracked file
  is listed, and nothing listed has stopped being tracked. Edit-insensitive, so
  it belongs in `verify` and runs on every gate.
- **Digests** answer whether the manifest describes *this commit*. Run by
  `make manifest` before a release and by the gate on the detached worktree,
  where the tree is clean by construction, and by CI after the push, which is
  where a release shipped without a regenerated manifest becomes visible to
  somebody other than the person who forgot.

`--write` regenerates. It is the only way the file should ever change, and it
is a release step rather than a way of making anything green.
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


def completeness() -> int:
    """Every tracked file is listed and nothing listed has stopped being tracked.

    The half that survives an edit, and therefore the half that belongs in the
    gate. It is also the half `shasum -c` never had: that command cannot report
    a line the manifest does not contain, and thirteen tracked files were in
    exactly that state at 0.32.4.0 with nothing saying so.
    """
    paths = tracked_files()
    entries = listed()
    problems = [f"tracked and absent from the manifest: {path}"
                for path in paths if path not in entries]
    problems += [f"listed and no longer tracked: {path}"
                 for path in sorted(set(entries) - set(paths))]
    for problem in problems:
        print(f"manifest-completeness: {problem}", file=sys.stderr)
    if problems:
        print(
            f"manifest-completeness: {len(problems)} problem(s); a file entered "
            "or left the repository without the manifest following it",
            file=sys.stderr,
        )
        return 1
    print(f"manifest-completeness: OK, {len(paths)} tracked file(s), all listed")
    return 0


def digests() -> int:
    """Every listed digest matches, which is a question about a commit.

    Not in `verify`, and F101 is why. Run this on a clean tree: before a tag,
    on the detached worktree, or in CI after the push. A mismatch here on a
    tree under edit means the tree is under edit; a mismatch on a clean one
    means the release chain skipped `make manifest-write`.
    """
    paths = tracked_files()
    entries = listed()
    problems = [f"content differs from its entry: {path}"
                for path in paths
                if entries.get(path) is not None and digest(path) != entries[path]]
    for problem in problems:
        print(f"manifest: {problem}", file=sys.stderr)
    if problems:
        print(
            f"manifest: {len(problems)} digest(s) disagree. On a clean tree "
            "this means the release chain did not run `make manifest-write`. "
            "On a tree under edit it means the tree is under edit, which is "
            "why this check is not in `verify`",
            file=sys.stderr,
        )
        return 1
    print(f"manifest: OK, {len(paths)} tracked file(s), every digest holds")
    return 0


def check() -> int:
    """Both questions, for the release chain and for CI."""
    return completeness() or digests()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true",
                        help="regenerate the manifest from the tracked files")
    parser.add_argument("--completeness", action="store_true",
                        help="only the edit-insensitive half, the one in `verify`")
    args = parser.parse_args()
    if args.write:
        return write()
    return completeness() if args.completeness else check()


if __name__ == "__main__":
    sys.exit(main())
