"""Command line entry point.

Subcommands are grouped under a single ``mavo`` prefix. Every command runs
without credentials and without network access; the repository must be usable by
somebody who has neither.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from mavo import __version__
from mavo.errors import BudgetOverrun, SourceUnavailable
from mavo.evaluate import plan_policy, run_policy, run_rule
from mavo.policy import Regime, equal_split
from mavo.rules import CANDIDATE_RULES, conjunction, drone_conjunction
from mavo.sources.fixture import FixtureSource, generate_history
from mavo.sources.telegram import CHANNEL_URL, probe
from mavo.store import EventStore
from mavo.transport import StubTransport, Transport, UrllibTransport


def _cmd_fixture(args: argparse.Namespace) -> int:
    nights = generate_history(weeks=args.weeks, seed=args.seed)
    store = EventStore(Path(args.out))
    added = store.append(FixtureSource(nights).poll())
    crossings = sum(1 for night in nights if night.had_crossing)
    print(f"nights={len(nights)} events_added={added} crossings={crossings}")
    print(f"store={args.out} total_events={store.count()}")
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    nights = generate_history(weeks=args.weeks, seed=args.seed)
    print(f"synthetic history: {len(nights)} nights, "
          f"{sum(1 for n in nights if n.had_crossing)} crossings")
    print("NOTE: synthetic input. This validates the gate, not any hypothesis.\n")
    failures = 0
    for rule_id, rule in CANDIDATE_RULES.items():
        run = run_rule(rule_id, rule, nights)
        print(run.summary())
        if not run.verdict.passes:
            failures += 1
    print(f"\n{failures}/{len(CANDIDATE_RULES)} candidate rules fail the gate")
    return 0


CANDIDATE_REGIMES = [
    (Regime.MISSILE, "CONJ-missile", conjunction),
    (Regime.DRONE, "CONJ-drone", drone_conjunction),
]

DEFAULT_POLICY = equal_split(CANDIDATE_REGIMES, total=2.0)


def _cmd_policy(args: argparse.Namespace) -> int:
    nights = generate_history(weeks=args.weeks, seed=args.seed)
    print(f"synthetic history: {len(nights)} nights, "
          f"{sum(1 for n in nights if n.had_crossing)} crossings")
    print("NOTE: synthetic input. This validates the split, not any hypothesis.\n")
    if args.allocation == "demand":
        try:
            policy = plan_policy(CANDIDATE_REGIMES, nights, total_budget=2.0)
        except BudgetOverrun as overrun:
            # Not a crash. The allocator refusing is the answer: measured demand
            # does not fit the recipient's attention, and the correct response is
            # to demote a regime, not to raise the total.
            print(f"[FAIL] allocation: {overrun}")
            return 1
    else:
        policy = DEFAULT_POLICY
    print(f"allocation: {args.allocation}")
    print(run_policy(policy, nights).summary())
    return 0


def _cmd_collect(args: argparse.Namespace) -> int:
    transport: Transport = StubTransport(Path(args.stub).read_text(encoding="utf-8")) \
        if args.stub else UrllibTransport()
    started = datetime.now(UTC)
    try:
        body = transport.fetch(CHANNEL_URL)
    except SourceUnavailable as unreachable:
        # Unreachable is not quiet. The exit code distinguishes them so a cron
        # wrapper cannot read an outage as an empty sky.
        print(f"[UNREACHABLE] {unreachable}")
        return 3
    fetch_s = (datetime.now(UTC) - started).total_seconds()
    if args.save_raw:
        # The classifier redesign (sprint 5) needs days of real content, and the
        # page is a ~20-message window (F27), so the corpus can only be built
        # forward in time. A snapshot that silently fails to land is a quiet
        # loss of exactly that evidence, hence the loud refusal and its own
        # exit code.
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        snapshot = Path(args.save_raw) / f"channel-{stamp}.html"
        try:
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_text(body, encoding="utf-8")
        except OSError as failure:
            print(f"[SNAPSHOT-FAILED] {failure}")
            return 4
        print(f"snapshot={snapshot}")
    report, _ = probe(StubTransport(body))
    print(f"messages={report.messages} parsed={report.parsed} "
          f"unparsed={report.unparsed_count} latency={fetch_s:.3f}s")
    for sample in report.unparsed[:5]:
        print(f"  unparsed: {sample}")
    if report.unparsed_count:
        print("NOTE: unparsed messages are counted, never dropped. A rising count "
              "means the pattern table is drifting from the channel.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(prog="mavo", description=__doc__)
    parser.add_argument("--version", action="version", version=f"mavo {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fixture = subparsers.add_parser("fixture", help="generate a synthetic history into a store")
    fixture.add_argument("--out", default="data/raw/fixture.sqlite")
    fixture.add_argument("--weeks", type=int, default=52)
    fixture.add_argument("--seed", type=int, default=1968)
    fixture.set_defaults(func=_cmd_fixture)

    gate_cmd = subparsers.add_parser("gate", help="score candidate rules against the base rate")
    gate_cmd.add_argument("--weeks", type=int, default=208)
    gate_cmd.add_argument("--seed", type=int, default=1968)
    gate_cmd.set_defaults(func=_cmd_gate)

    policy = subparsers.add_parser(
        "policy", help="score the regime-split decision policy and its total budget"
    )
    policy.add_argument("--weeks", type=int, default=208)
    policy.add_argument("--seed", type=int, default=1968)
    policy.add_argument("--allocation", choices=["equal", "demand"], default="equal")
    policy.set_defaults(func=_cmd_policy)

    collect = subparsers.add_parser(
        "collect", help="poll the public channel once and report what was understood"
    )
    collect.add_argument("--stub", help="read a saved page instead of the network")
    collect.add_argument(
        "--save-raw",
        help="write the fetched page verbatim into this directory before parsing "
             "(builds the sprint-5 corpus; the page is a ~20-message window, F27)",
    )
    collect.set_defaults(func=_cmd_collect)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
