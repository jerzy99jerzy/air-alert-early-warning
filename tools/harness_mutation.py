#!/usr/bin/env python3
"""Mutation-verify the attack harness.

F14, open since 0.3.0.0 and slipped twice. Every harness attack has passed on
every run since it was written, which is exactly what a harness that asserts
nothing would also do. A green harness is evidence only if a broken control
turns it red, and that had never been observed.

Each mutation below disables one control by a textual substitution in a scratch
copy of the tree, then runs the attack that guards it. The attack must fail. If
it passes, the mutation was survivable and the attack does not measure what the
catalogue says it measures.

Not every attack has a mutation. Where a control cannot be disabled by a single
substitution, the attack is listed as unverified rather than given a mutation
that flatters it, and the count is printed. Unknown is not the safe state here
either.

Not part of `make verify`: it copies the tree and runs pytest once per mutation,
which is seconds rather than milliseconds. Run it with `make harness-mutation`
when a control changes, and at every release.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Mutation:
    """One disabled control and the attack that must notice."""

    attack: str
    row: str
    path: str
    old: str
    new: str
    disables: str


MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        attack="test_a15_a_night_read_as_empty_is_not_a_total_of_zero",
        row="MT17",
        path="mavo/sources/kpszsu.py",
        old="    if not tally.launched or any(item.count is None for item in tally.launched):",
        new="    if any(item.count is None for item in tally.launched):",
        disables="decision 9's non-empty condition on a launched total",
    ),
    Mutation(
        attack="test_a1_broad_simultaneous_activation_raises_nothing",
        row="MT1",
        path="mavo/rules.py",
        old="POISON_AREA_THRESHOLD = 8",
        new="POISON_AREA_THRESHOLD = 10_000",
        disables="poison suppression",
    ),
    Mutation(
        attack="test_a2_a_silent_feed_is_not_an_all_clear",
        row="MT2",
        path="mavo/schema.py",
        old="    return state is AlertState.CLEAR",
        new="    return state is not AlertState.ACTIVE",
        disables="unknown is not the safe state",
    ),
    Mutation(
        attack="test_a3_one_fabricated_alert_cannot_raise_an_alarm",
        row="MT3",
        path="mavo/rules.py",
        old=(
            "    missile_at = r3_border_missile(night)\n"
            "    escalation_at = r2_westward_escalation(night)\n"
            "    if missile_at is None or escalation_at is None:\n"
            "        return None\n"
            "    return max(missile_at, escalation_at)"
        ),
        new="    return r1_border_active(night)",
        disables="the conjunction requirement for an alarm",
    ),
    Mutation(
        attack="test_a4_perfect_recall_does_not_buy_past_the_lift_floor",
        row="MT4",
        path="mavo/baserate.py",
        old="    elif bound < MIN_LIFT_LOWER_BOUND:",
        new="    elif bound < 0.0:",
        disables="the lift floor that separates a detector from a calendar",
    ),
    Mutation(
        attack="test_a6_a_partial_policy_cannot_read_as_complete",
        row="MT6",
        path="mavo/evaluate.py",
        old="        return any(count > 0 for _, count in self.unserved)",
        new="        return False",
        disables="coverage-gap reporting",
    ),
    Mutation(
        attack="test_a8_replaying_a_feed_does_not_grow_the_log",
        row="MT8",
        path="mavo/schema.py",
        # Re-targeted at 0.48.0.0: D-045 put `kind` into the payload and the
        # previous mutation text went stale, which this harness reported rather
        # than passed - the exact behaviour it exists for. The attack it guards
        # is unchanged: fold ingest time into identity and a re-poll of one
        # transition becomes a new row every time.
        old='''                self.role.value,
                self.kind.value,
            ]''',
        new='''                self.role.value,
                self.kind.value,
                self.ts_ingest.isoformat(),
            ]''',
        disables="idempotence by content hash",
    ),
    Mutation(
        attack="test_a9_hostile_bodies_to_the_live_adapter_do_not_raise",
        row="MT7",
        path="mavo/sources/telegram.py",
        old="    except (ValueError, TypeError):\n        return None",
        new="    except (ValueError, TypeError):\n        raise",
        disables="the never-raise contract on hostile content",
    ),
    Mutation(
        attack="test_a10_an_unreachable_source_is_not_a_quiet_one",
        row="MT11",
        path="mavo/sources/telegram.py",
        old="        body = self.transport.fetch(self.url)",
        new=(
            "        try:\n"
            "            body = self.transport.fetch(self.url)\n"
            "        except SourceUnavailable:\n"
            '            body = ""'
        ),
        disables="an outage refusing rather than reporting silence",
    ),
    Mutation(
        attack="test_a14_a_still_dangerous_area_is_not_silently_dropped",
        row="MT16",
        path="mavo/sources/telegram.py",
        old="    for ref in still_running:",
        new="    for ref in ():",
        disables="recording the areas an all-clear says are still under alert",
    ),
    Mutation(
        attack="test_a13_an_unknown_tag_is_not_replaced_by_a_prose_guess",
        row="MT14",
        path="mavo/sources/telegram.py",
        old="    elif unknown:",
        new="    elif False:",
        disables="the refusal to guess an area the channel named and the map cannot read",
    ),
    Mutation(
        attack="test_a12_the_footer_time_cannot_shift_onto_a_neighbour",
        row="MT13",
        path="mavo/sources/telegram.py",
        old="            time_match = _TIME.search(block)",
        new="            time_match = _TIME.search(body)",
        disables="block-scoped timestamp pairing",
    ),
    Mutation(
        attack="test_a11_a_skipped_window_cannot_pass_as_a_quiet_channel",
        row="MT12",
        path="mavo/sources/telegram.py",
        old="        skipped: int | None = None\n        if self._last_id is not None:",
        new="        skipped: int | None = 0\n        if self._last_id is not None:",
        disables="an unmeasurable window gap reported as unknown",
    ),
)

# A7 has no mutation. It asserts that the fixture source does not raise on any
# scenario, and the fixture generates rather than parses, so there is no control
# to disable: any mutation that makes it raise is an injected fault rather than a
# removed protection. Stated rather than counted as covered.
UNVERIFIED: tuple[tuple[str, str], ...] = (
    (
        "test_a7_hostile_payloads_do_not_become_an_outage",
        "the fixture source generates rather than parses, so no control guards it",
    ),
)


def _run_attack(tree: Path, attack: str) -> bool:
    """Run one harness attack in ``tree``. True when it passes."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/harness/test_attacks.py", "-k", attack, "-q"],
        cwd=tree,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def labels_disagree(root: Path = ROOT) -> list[str]:
    """Every mutation's row exists in the threat table and heads its attack.

    F186. The register, the catalogue and attack A14 called the all-clear
    control MT15 for eight months while the threat table's MT15 was the
    directory lock. The numbering check counted the table and nothing read a
    label against it. This reads both halves: the row must be a row of
    `docs/THREAT-MODEL.md`, and the attack's docstring must open with it, so a
    label cannot drift away from the threat it names without failing here. It
    cannot judge whether the row's prose describes the attack, and says so in
    F186's reopen condition.
    """
    threats = (root / "docs" / "THREAT-MODEL.md").read_text(encoding="utf-8")
    attacks = (root / "tests" / "harness" / "test_attacks.py").read_text(encoding="utf-8")
    problems: list[str] = []
    for mutation in MUTATIONS:
        if f"| {mutation.row} |" not in threats:
            problems.append(f"{mutation.attack}: {mutation.row} is not a row of THREAT-MODEL.md")
        head = rf'def {mutation.attack}\([^)]*\) -> None:\n    """{mutation.row}\. '
        if re.search(head, attacks) is None:
            problems.append(f"{mutation.attack}: its docstring does not open with {mutation.row}")
    return problems


def main() -> int:
    """Apply every mutation and report which attacks noticed."""
    mislabelled = labels_disagree()
    for problem in mislabelled:
        print(f"harness-mutation: {problem}", file=sys.stderr)
    if mislabelled:
        return 1
    survived: list[Mutation] = []
    killed = 0

    with tempfile.TemporaryDirectory() as workspace:
        for mutation in MUTATIONS:
            tree = Path(workspace) / mutation.attack
            shutil.copytree(
                ROOT,
                tree,
                ignore=shutil.ignore_patterns(
                    ".git", ".venv", "venv", "__pycache__", ".mypy_cache",
                    ".ruff_cache", ".pytest_cache", "*.egg-info", "data",
                ),
            )
            target = tree / mutation.path
            source = target.read_text(encoding="utf-8")
            if mutation.old not in source:
                print(
                    f"harness-mutation: {mutation.attack}: the mutated text is no longer in "
                    f"{mutation.path}. The mutation is stale, which means this attack is "
                    "unverified until it is rewritten.",
                    file=sys.stderr,
                )
                survived.append(mutation)
                continue
            target.write_text(source.replace(mutation.old, mutation.new, 1), encoding="utf-8")

            if _run_attack(tree, mutation.attack):
                survived.append(mutation)
                print(
                    f"harness-mutation: {mutation.attack} PASSED with {mutation.disables} "
                    "disabled. The attack does not measure its control.",
                    file=sys.stderr,
                )
            else:
                killed += 1
                print(f"  {mutation.row} {mutation.attack}: red with {mutation.disables} disabled")

    for attack, reason in UNVERIFIED:
        print(f"  unverified: {attack} ({reason})")

    total = len(MUTATIONS) + len(UNVERIFIED)
    print(
        f"\nharness-mutation: {killed} of {len(MUTATIONS)} mutations killed; "
        f"{len(UNVERIFIED)} of {total} attacks carry no mutation"
    )
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
