"""An inventory of the corpus, so that "is this the same corpus" has an answer.

Writes `data/aggregates/corpus_manifest.csv`, a tier-2 artifact: one row per page
snapshot with its id range, byte size, message count and SHA-256, plus a header
carrying the aggregate digest, the id range, the contiguity verdict and the date
the inventory was taken.

## Why this exists

On 2026-08-09 the corpus was lost. Sixty thousand posts, four months, the
evidence base under every measurement this project publishes, gone from a
laptop with no second copy. The tree carried a `MANIFEST.sha256` over 101 source
files and nothing at all over the data those files were written to analyse.

The loss is recoverable, because Telegram addresses posts by id and a page
re-fetched is a page unchanged, so the same id range yields the same corpus.
That is the good news and it is also the trap: **without an inventory there is
no way to demonstrate that the second copy is the first one.** The measurements
would be re-derived from something that merely resembled the original, and the
resemblance would be an assumption in the one place this project refuses them.

Class: a critical artifact with no inventory (F68). The same shape as F64, a pin
that nothing compared against the tree, one layer further out: a claim about
something the gate could not see.

## What the digest is, and what it is not

The aggregate digest is the SHA-256 of the sorted per-page digests. It changes
when any page changes, when a page is added, and when a page is removed. It says
nothing about whether the corpus is *complete* — that is what the contiguity
column is for — and nothing about whether it is *the right window*, which is
what the id range is for. Three separate questions, three separate columns, on
purpose.

## Usage

    python3 tools/corpus_inventory.py --raw data/raw

The corpus itself stays out of the tree (tier 1, `data/raw` is gitignored). The
inventory goes in, because it is counts and hashes over filenames: no message
content, nothing per-subject, and it is exactly what a reader needs to check
that a published measurement was taken over the data it claims.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from mavo.backfill import SNAPSHOT_NAME, contiguity_gaps

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "aggregates" / "corpus_manifest.csv"
POST = re.compile(r'data-post="[^/]+/(\d+)"')

FIELDS = ("page", "id_lo", "id_hi", "messages", "bytes", "sha256")

# Keys the inventory schema supersedes, written by hand before this tool
# existed. Removed on write, each removal printed: leaving them would keep two
# contradictory descriptions of the corpus in one block ("posts: 60680" beside
# "messages: 61240"), and the stale one would be the one somebody quotes.
# `span_days` cannot be derived from the inventory and is removed rather than
# preserved stale; the removal is printed, so it is a recorded loss, not a
# silent one.
SUPERSEDED = (
    "posts", "post_id_low", "post_id_high", "retrieved", "contiguous", "span_days",
)


def patch_corpus_block(
    status: dict[str, object], fields: dict[str, object]
) -> tuple[dict[str, object], list[str]]:
    """Merge ``fields`` into ``status["corpus"]`` without erasing foreign keys.

    The first version of this tool did ``status["corpus"] = {...}`` and erased
    the D-012a holdout boundary (``design_window_high_id``, ``holdout_low_id``,
    ``holdout_share``, ``content_read_before_freeze``) — fields this tool does
    not own and cannot recompute. The gate passed, because nothing read them:
    the same class as F64, committed inside the tool built to close that class.
    The contract now: this function owns exactly ``fields`` plus the
    ``SUPERSEDED`` legacy names it retires; every other key survives the write.
    """
    existing = status.get("corpus")
    block: dict[str, object] = dict(existing) if isinstance(existing, dict) else {}
    notes: list[str] = []
    for key in SUPERSEDED:
        if key in block:
            notes.append(f"corpus.{key} removed: superseded by the inventory schema")
            del block[key]
    preserved = sorted(key for key in block if key not in fields)
    block.update(fields)
    status["corpus"] = block
    if preserved:
        notes.append(
            "corpus fields preserved, not owned by the inventory: " + ", ".join(preserved)
        )
    return status, notes


def inventory(directory: Path) -> tuple[list[dict[str, str]], list[str]]:
    """One row per snapshot, plus whatever is wrong with the set of them."""
    rows: list[dict[str, str]] = []
    problems: list[str] = []

    for snapshot in sorted(directory.glob("page-*.html")):
        match = SNAPSHOT_NAME.search(snapshot.name)
        if match is None:
            problems.append(f"{snapshot.name}: not a snapshot name; ignored by every reader")
            continue
        payload = snapshot.read_bytes()
        text = payload.decode("utf-8", errors="replace")
        ids = [int(found) for found in POST.findall(text)]
        low, high = int(match.group(1)), int(match.group(2))
        if ids and (min(ids) != low or max(ids) != high):
            # The filename is what every tool reads; if it disagrees with the
            # page it names, the file is unusable and saying so is the point of
            # an inventory.
            problems.append(
                f"{snapshot.name}: filename says {low}..{high}, content holds "
                f"{min(ids)}..{max(ids)}"
            )
        rows.append(
            {
                "page": snapshot.name,
                "id_lo": str(low),
                "id_hi": str(high),
                "messages": str(len(ids)),
                "bytes": str(len(payload)),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return rows, problems


def aggregate_digest(rows: list[dict[str, str]]) -> str:
    """One digest over the whole set, order-independent by construction."""
    joined = "\n".join(sorted(row["sha256"] for row in rows))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--out", type=Path, default=OUTPUT)
    parser.add_argument(
        "--write-status",
        action="store_true",
        help="patch STATUS.json's corpus block from the inventory just written",
    )
    arguments = parser.parse_args()

    if not arguments.raw.exists():
        print(f"corpus-inventory: {arguments.raw} does not exist")
        return 1

    rows, problems = inventory(arguments.raw)
    for problem in problems:
        print(f"corpus-inventory: {problem}")
    if not rows:
        print(f"corpus-inventory: no snapshots in {arguments.raw}")
        return 1

    gaps = list(contiguity_gaps(arguments.raw))
    low = min(int(row["id_lo"]) for row in rows)
    high = max(int(row["id_hi"]) for row in rows)
    messages = sum(int(row["messages"]) for row in rows)
    digest = aggregate_digest(rows)

    arguments.out.parent.mkdir(parents=True, exist_ok=True)
    with arguments.out.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# Inventory of the page snapshots the published measurements were taken over.\n"
            f"# taken_at      {datetime.now(UTC).date().isoformat()}\n"
            f"# pages         {len(rows)}\n"
            f"# messages      {messages}\n"
            f"# id_range      {low}..{high}\n"
            f"# contiguity    {'no gaps' if not gaps else f'{len(gaps)} gap(s): {gaps[:5]}'}\n"
            f"# digest        sha256:{digest}\n"
            "# The digest is over the sorted per-page digests. It answers 'is this the same\n"
            "# corpus'. Completeness is the contiguity line; the right window is id_range.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"corpus-inventory: {len(rows)} pages, {messages} messages, ids {low}..{high}, "
        f"{'no gaps' if not gaps else str(len(gaps)) + ' gaps'}"
    )
    print(f"corpus-inventory: digest sha256:{digest}")
    print(f"corpus-inventory: written to {arguments.out}")
    if arguments.write_status:
        # Written by the tool rather than typed by a person, on purpose. Every
        # figure in STATUS.json is supposed to come from a measurement, and a
        # number retyped by hand from a measurement is a number from memory with
        # extra steps.
        status_path = ROOT / "STATUS.json"
        status = json.loads(status_path.read_text(encoding="utf-8"))
        status, notes = patch_corpus_block(
            status,
            {
                "manifest": "data/aggregates/corpus_manifest.csv",
                "pages": len(rows),
                "messages": messages,
                "id_range": f"{low}..{high}",
                "digest": f"sha256:{digest}",
                "contiguity": "no gaps" if not gaps else f"{len(gaps)} gap(s)",
                "size_mb": round(sum(int(row["bytes"]) for row in rows) / 1_000_000),
                "taken_at": datetime.now(UTC).date().isoformat(),
            },
        )
        for note in notes:
            print(f"corpus-inventory: {note}")
        status_path.write_text(
            json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print("corpus-inventory: STATUS.json corpus block updated from the inventory")

    if gaps:
        print("corpus-inventory: gaps are a finding, not a warning. Record or close them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
