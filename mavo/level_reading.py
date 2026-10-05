"""D-050's open half, read off the store: `mavo level-reading STORE` (D-063).

A `mavo` subcommand because its input is the store (D-038). It imports nothing
from this package, so the host's own interpreter runs the same file before the
release that carries it is installed, read-only on the store, as the store's
owner so nothing it opens is created under another:

    sudo -u mavo /usr/bin/python3 - /var/lib/mavo/events < mavo/level_reading.py

Opens the store with `mode=ro`, writes nothing, makes no network call. Prints
three figures and one verdict:

1. D-050's condition, measured on content: at least 50 level changes inside
   alarms the API kept open, across at least 15 distinct `(area, kind)` keys.
   A change is two consecutive declarations on one key, by the source's own
   stamp, with different words and no API all-clear between them. A key on
   which one alarm ends and the next begins between two polls leaves no
   all-clear, so a word that differs across the two counts as a change: the
   figure is an upper bound by that much.
2. The vocabulary: every word the stream holds, with its count. A word other
   than `Red` and `Yellow` is published verbatim and drawn as unrecognised.
3. The age of the newest declaration on every key whose newest API row is
   active.

The verdict line is the stop condition of the first step of 0.60.0.0's
install, and the exit status says the same: 0 met, 1 not met, 2 a usage error.
"""

from __future__ import annotations

import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime

#: The rows that speak for the API: its own, and the closures `reconcile`
#: derives from it (D-044).
API_SOURCES = ("ukrainealarm", "reconcile")
#: D-050's condition, restated 2026-09-09.
MIN_CHANGES, MIN_KEYS = 50, 15

Key = tuple[str, str]


def _stamp(text: str) -> datetime:
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def read(path: str, now: datetime) -> list[str]:
    """The reading's lines, the verdict last."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)
    try:
        declared: dict[Key, list[tuple[datetime, str]]] = defaultdict(list)
        words: Counter[str] = Counter()
        for area, kind, word, level_at in conn.execute(
                "SELECT area_id, kind, level, level_at FROM alert_levels"):
            declared[(area, kind)].append((_stamp(level_at), word))
            words[word] += 1
        # The API's own all-clears per key, by the source's clock, and the
        # state of the newest API row on every key.
        clears: dict[Key, list[datetime]] = defaultdict(list)
        newest: dict[Key, tuple[datetime, str]] = {}
        marks = ",".join("?" for _ in API_SOURCES)
        for area, kind, state, source in conn.execute(
                "SELECT area_id, kind, state, ts_source FROM events "
                f"WHERE source_id IN ({marks})", API_SOURCES):
            key, moment = (area, kind), _stamp(source)
            if state == "clear":
                clears[key].append(moment)
            if key not in newest or moment >= newest[key][0]:
                newest[key] = (moment, state)
    finally:
        conn.close()
    for rows in declared.values():
        rows.sort()

    total = sum(len(rows) for rows in declared.values())
    first = min((rows[0][0] for rows in declared.values()), default=None)
    since = f"{first:%Y-%m-%d}" if first else "never"
    lines = [f"[measured {now:%Y-%m-%d %H:%M} UTC] alert_levels rows={total} "
             f"keys={len(declared)} declared since {since}"]

    changes, keys_changed = 0, set()
    for key, rows in declared.items():
        for (before_at, before), (after_at, after) in zip(rows, rows[1:], strict=False):
            if before == after:
                continue
            if not any(before_at < c <= after_at for c in clears.get(key, ())):
                changes += 1
                keys_changed.add(key)
    met = changes >= MIN_CHANGES and len(keys_changed) >= MIN_KEYS
    lines.append(f"1. changes inside an alarm: {changes} on {len(keys_changed)} keys "
                 f"(the condition: {MIN_CHANGES} on {MIN_KEYS})")
    vocabulary = ", ".join(f"{w!r}={n}" for w, n in words.most_common()) or "none"
    outside = sorted(set(words) - {"Red", "Yellow"})
    lines.append(f"2. words: {vocabulary} | outside Red/Yellow: {outside or 'none'}")
    ages = [(now - declared[key][-1][0]).total_seconds() / 3600
            for key, (_, state) in newest.items() if state == "active" and key in declared]
    if ages:
        lines.append(
            f"3. active API keys with a declaration: {len(ages)}; age of the newest one "
            f"in hours: median {statistics.median(ages):.1f}, "
            f"p90 {_percentile(ages, .9):.1f}, max {max(ages):.1f}; "
            f"over 30 days: {sum(1 for a in ages if a > 720)}")
    else:
        lines.append("3. no active API key carries a declaration")
    lines.append(f"D-050 condition: {'MET' if met else 'NOT MET'}")
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    """`mavo level-reading STORE`, or the same run from stdin."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: mavo level-reading STORE", file=sys.stderr)
        return 2
    lines = read(args[0], datetime.now(UTC))
    print("\n".join(lines))
    return 0 if lines[-1] == "D-050 condition: MET" else 1


if __name__ == "__main__":
    sys.exit(main())
