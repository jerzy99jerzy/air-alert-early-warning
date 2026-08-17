#!/usr/bin/env python3
"""What the channel says about the means of attack that this parser cannot see.

`KIND_MARKERS` holds eight stems over four kinds. They were written before
the corpus existed, so the coverage they achieve measures the parser as much
as it measures the channel. The open question is not "should the table be
longer" -- it is **which additions would recover how many alerts, and at what
false-positive cost**, and that question has an answer in the corpus rather
than in anyone's intuition.

This tool answers it in four parts:

1. **The gap, sized.** How many messages carry a declaration or lift marker
   and still resolve to no kind, and what share of the corpus that is. If the
   number is small, everything below is a curiosity.

2. **The vocabulary, ranked.** The most frequent word stems appearing in
   those messages and absent from the current table. This is the candidate
   list, generated from the corpus rather than proposed from memory.

3. **Each candidate, costed.** For a hand-supplied list of proposed stems:
   how many currently-unresolved messages each would resolve, how many it
   would collide with (messages that already resolve, where the stem would
   introduce a second kind and turn a resolution into an ambiguity), and how
   many messages it would touch that carry no declaration marker at all.

4. **A sample to read.** Coverage figures quoted without reading messages are
   the failure mode `kind_coverage.py` names in its own docstring, and it
   applies here identically. The tool prints examples and expects them to be
   read before any number leaves this terminal.

WHAT IT DOES NOT DO

It proposes no additions and edits no table. A stem that recovers many
messages may still be wrong -- `каб` is three characters and was kept short
deliberately, with the false-hit rate called a question for the corpus rather
than a guess to encode. This measures; deciding stays with a person, and the
decision belongs in `DECISIONS.md` with these numbers attached.

It also cannot see what the channel does not write. A means of attack the
channel never names is not a vocabulary gap, and no amount of stem-mining
will produce it.

Usage:
    python3 tools/vocab_gaps.py --raw data/raw
    python3 tools/vocab_gaps.py --raw data/raw --top 60 --sample 15
    python3 tools/vocab_gaps.py --raw data/raw --candidates candidates.txt

The corpus is tier 1 and not in the tree, so this cannot run in CI. Its
output is a measurement to be recorded in `docs/METHODOLOGY.md` by hand, with
its date and the message count it read.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mavo.backfill import read_snapshot_messages  # noqa: E402
from mavo.sources.telegram import (  # noqa: E402
    KIND_DECLARE_MARKERS,
    KIND_LIFT_MARKERS,
    KIND_MARKERS,
    classify_state,
)

#: Cyrillic word-ish runs. Latin and digits are kept out of the ranking on
#: purpose: `х-101` and `ту-95` are real vocabulary, but they are rare enough
#: that frequency ranking buries them, and they are better tested as named
#: candidates than discovered by mining.
WORD = re.compile(r"[\u0400-\u04FF]{4,}")

#: Words too common to be evidence of anything. Kept deliberately short: a
#: long stop list is a way of deciding the answer before measuring it.
STOP = {
    "загроза", "тривога", "область", "області", "громада", "громади",
    "район", "району", "відбій", "увага", "перебування", "укритті",
    "укриття", "небезпека", "небезпеки", "оголошено", "повітряна",
    "повітряної", "тривоги", "місто", "міста", "напрямку", "через",
    # Not a marker, but the phrasing every declaration shares: it appears in
    # essentially the whole gap and ranking it first would put the question's
    # own grammar at the top of its answer. Measured, not assumed: it came
    # first at 100% of the gap on the first run against a test corpus.
    "застосування", "застосуванню",
}


#: The words the markers themselves are made of. They appear in every
#: message in the gap by construction, so ranking them as candidates would
#: put the question's own phrasing at the top of its answer.
MARKER_WORDS = {
    w for marker in tuple(KIND_DECLARE_MARKERS) + tuple(KIND_LIFT_MARKERS)
    for w in WORD.findall(marker.lower())
}


def stems_of(text: str) -> set[str]:
    """Distinct long-ish Cyrillic words, lowered, minus the stop list."""
    return {w for w in WORD.findall(text.lower())
            if w not in STOP and w not in MARKER_WORDS}


def kinds_in(text: str) -> set[str]:
    """The kinds the current table finds, isolated from every other layer.

    Deliberately not `classify_kind_message`: that also resolves an area, so
    a message naming a perfectly clear means over an unmapped tag comes back
    empty and would be counted here as a vocabulary gap. It is an area gap,
    a different population with a different repair, and conflating the two is
    how `tools/unmapped_tags.py` records that METHODOLOGY.md already
    misattributed one set of near-misses to the wrong cause.

    This mirrors the kind step of `classify_kind_message` exactly: the set of
    stems present, where exactly one means a resolution and two mean the
    parser refuses rather than guesses.
    """
    lowered = text.lower()
    return {value.name for pattern, value in KIND_MARKERS.items()
            if pattern in lowered}


def resolves(text: str) -> bool:
    """Would the kind layer alone get a single kind out of this message?"""
    return len(kinds_in(text)) == 1


def has_marker(text: str) -> bool:
    lowered = text.lower()
    return any(m in lowered for m in KIND_DECLARE_MARKERS) or any(
        m in lowered for m in KIND_LIFT_MARKERS)


def known_stem(text: str) -> bool:
    lowered = text.lower()
    return any(stem in lowered for stem in KIND_MARKERS)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--sample", type=int, default=10)
    ap.add_argument("--candidates", type=Path, default=None,
                    help="file of proposed stems, one per line, # for comments")
    args = ap.parse_args()

    if not args.raw.exists():
        print(f"vocab-gaps: {args.raw} does not exist. The corpus is tier 1 "
              "and not in the tree.")
        return 2

    messages = read_snapshot_messages(args.raw)
    if not messages:
        print(f"vocab-gaps: no messages under {args.raw}")
        return 1

    texts = [text for _when, text in messages]
    total = len(texts)

    alerts = [t for t in texts if classify_state(t) is not None]
    marked = [t for t in texts if classify_state(t) is None and has_marker(t)]
    resolved = [t for t in marked if resolves(t)]
    unresolved = [t for t in marked if not resolves(t)]

    print("corpus [measured]")
    print("-" * 60)
    print(f"  snapshots read from   {args.raw}")
    print(f"  messages              {total}")
    print(f"  alert-state messages  {len(alerts)} "
          f"({100.0 * len(alerts) / total:.1f}%)")
    print(f"  kind-marker messages  {len(marked)} "
          f"({100.0 * len(marked) / total:.1f}%)")
    print(f"    of which resolve    {len(resolved)} "
          f"({100.0 * len(resolved) / max(len(marked), 1):.1f}% of marked)")
    print(f"    of which do not     {len(unresolved)} "
          f"({100.0 * len(unresolved) / max(len(marked), 1):.1f}% of marked)")

    # Why each unresolved message failed. The two causes need different
    # repairs and lumping them together is how "extend the table" becomes the
    # answer to a question it does not address.
    no_stem = [t for t in unresolved if not kinds_in(t)]
    many = [t for t in unresolved if len(kinds_in(t)) > 1]
    print(f"\n  unresolved because no known stem appears: {len(no_stem)}")
    print("    -> a vocabulary gap, which is what this tool measures")
    print(f"  unresolved because two kinds are named at once:  {len(many)}")
    print("    -> two kinds named at once, or a stem inside a word the table "
          "did not\n       intend. Extending the table cannot fix these and "
          "may worsen them.")

    print(f"\ncandidate stems, top {args.top} [measured]")
    print("-" * 60)
    print("  Frequency among messages that carry a declaration or lift marker "
          "and\n  resolve to nothing. A stem high in this list is common in "
          "the gap; that is\n  not the same as being a means of attack, and "
          "the sample below is how you\n  tell the difference.")
    counts: Counter[str] = Counter()
    for text in no_stem:
        counts.update(stems_of(text))
    width = max((len(w) for w, _n in counts.most_common(args.top)), default=10)
    for word, n in counts.most_common(args.top):
        share = 100.0 * n / max(len(no_stem), 1)
        print(f"  {word:{width}s}  {n:6d}  {share:5.1f}% of the gap")

    if args.candidates:
        proposed = [line.strip().lower()
                    for line in args.candidates.read_text(
                        encoding="utf-8").splitlines()
                    if line.strip() and not line.startswith("#")]
        print(f"\nproposed stems, costed [measured] -- {len(proposed)}")
        print("-" * 60)
        print(f"  {'stem':16s} {'recovers':>9s} {'collides':>9s} "
              f"{'unmarked':>9s}")
        print("  " + "-" * 56)
        for stem in proposed:
            # recovers: unresolved-for-lack-of-stem messages this would catch
            recovers = sum(1 for t in no_stem if stem in t.lower())
            # collides: messages that resolve today and would gain a second
            # kind, which `classify_kind_message` turns into no kind at all.
            # A stem that recovers 40 and collides with 60 is a net loss and
            # the table would look better while performing worse.
            collides = sum(1 for t in resolved if stem in t.lower())
            # unmarked: messages carrying the stem but no declaration marker.
            # Not a loss, but a size for how much of the channel the stem
            # touches outside the population it was proposed for.
            unmarked = sum(1 for t in texts
                           if stem in t.lower() and not has_marker(t)
                           and classify_state(t) is None)
            print(f"  {stem:16s} {recovers:9d} {collides:9d} {unmarked:9d}")
        print("\n  recovers: unresolved messages this stem would give a kind")
        print("  collides: messages that resolve today and would become "
              "ambiguous,\n            because two kinds in one message "
              "resolve to none")
        print("  unmarked: messages carrying the stem with no declaration "
              "marker at all")

    if args.sample:
        print(f"\nsample of the gap [measured] -- {args.sample} messages")
        print("-" * 60)
        print("  Read these before quoting any number above. The tables were "
              "written\n  before the corpus existed, so an unread coverage "
              "figure describes the\n  parser and not the channel.")
        step = max(1, len(no_stem) // args.sample)
        for text in no_stem[::step][: args.sample]:
            flat = " ".join(text.split())
            print(f"\n  | {flat[:300]}")

    print("\nNothing above proposes a change. A stem that recovers many "
          "messages may\nstill be wrong, and the decision belongs in "
          "DECISIONS.md with these numbers\nattached to it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
