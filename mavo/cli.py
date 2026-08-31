"""Command line entry point.

Subcommands are grouped under a single ``mavo`` prefix. Every command runs
without credentials and without network access; the repository must be usable by
somebody who has neither.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from mavo import __version__
from mavo.attempts import main as attempts_main
from mavo.backfill import (
    DirectoryBusy,
    DirectoryLock,
    backfill,
    contiguity_gaps,
    lowest_on_disk,
)
from mavo.errors import SourceUnavailable
from mavo.evaluate import run_policy, run_rule
from mavo.obs import from_environment as sink_from_environment
from mavo.policy import Regime, policy_of
from mavo.report import (
    DEFAULT_VALID_FOR_S,
    FEED_WINDOW_S,
    SCHEMA_VERSION,
    FeedState,
    Report,
    compose,
    publish,
    render_text,
    write_contract,
    write_feed,
)
from mavo.rules import CANDIDATE_RULES, conjunction, drone_conjunction
from mavo.schema import (
    AlertState,
    Provenance,
    ThreatEvent,
    ThreatKind,
    is_clear,
    redate_reassertions,
)
from mavo.sources.fixture import FixtureSource, generate_history
from mavo.sources.rso import CATEGORIES as RSO_CATEGORIES
from mavo.sources.rso import FEED as RSO_FEED
from mavo.sources.rso import page_url as rso_page_url
from mavo.sources.rso import poll_once as rso_poll_once
from mavo.sources.telegram import CHANNEL_URL, poll_once
from mavo.sources.telegram import FEED as CHANNEL_FEED
from mavo.sources.ukrainealarm import API_BASE, read_key
from mavo.sources.ukrainealarm_source import (
    SNAPSHOT_MAX_AGE_S,
    UkrainealarmSource,
    _load_snapshot,
)
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

DEFAULT_POLICY = policy_of(CANDIDATE_REGIMES)


def _cmd_policy(args: argparse.Namespace) -> int:
    nights = generate_history(weeks=args.weeks, seed=args.seed)
    print(f"synthetic history: {len(nights)} nights, "
          f"{sum(1 for n in nights if n.had_crossing)} crossings")
    print("NOTE: synthetic input. This validates the split, not any hypothesis.\n")
    print(run_policy(DEFAULT_POLICY, nights).summary())
    return 0


def _cmd_backfill(args: argparse.Namespace) -> int:
    transport: Transport = StubTransport(Path(args.stub).read_text(encoding="utf-8")) \
        if args.stub else UrllibTransport()
    out = Path(args.out)
    before = args.before
    if args.resume:
        if before is not None:
            print("REFUSED: --resume and --before both given; they name different cursors")
            return 2
        before = lowest_on_disk(out)
        # Stated, not inferred. A 2900-page run that is interrupted otherwise
        # costs a full re-walk of what is already on disk, and a command whose
        # start point depends on directory contents has to say where it started.
        print(f"resuming below id {before}" if before is not None
              else "resume requested; nothing on disk yet, starting from the newest page")
    def show_progress(pages: int, lowest: int) -> None:
        # stderr, so a redirected stdout still holds only the report. A run of
        # 2800 pages takes 25 minutes and printed nothing until it finished,
        # which made working and hung indistinguishable (F48).
        if pages % 25 == 0:
            print(f"  {pages} pages, at id {lowest}", file=sys.stderr, flush=True)

    lock = DirectoryLock(out)
    try:
        lock.acquire()
    except DirectoryBusy as busy:
        print(f"REFUSED: {busy}")
        return 6
    try:
        report = backfill(
            transport,
            out,
            max_pages=args.pages,
            before=before,
            delay_s=args.delay,
            stop_at_id=args.stop_at_id,
            progress=None if args.quiet else show_progress,
        )
    finally:
        lock.release()
    print(report.summary())

    gaps = list(contiguity_gaps(Path(args.out)))
    if gaps:
        # Printed, never summed away. A corpus with holes is usable; a corpus
        # with holes it does not name is not.
        print(f"\nCONTIGUITY: {len(gaps)} gap(s) in what is on disk")
        for first, last in gaps[:20]:
            print(f"  missing {first}..{last} ({last - first + 1} posts)")
        if len(gaps) > 20:
            print(f"  ... and {len(gaps) - 20} more")
        return 5
    print("\nCONTIGUITY: no gaps in what is on disk")
    return 0


#: Feed name for the attempts table. Its own, so a store holding both pipes can
#: say which one an observation came down and `mavo attempts` can read either.
API_FEED = "ukrainealarm"
API_URL = f"{API_BASE}/alerts"

def _redate_against_stored_clears(
    store: EventStore, events: Sequence[ThreatEvent], observed_at: datetime
) -> tuple[ThreatEvent, ...]:
    """D-044 part 2, at the write boundary rather than inside the adapter.

    **Snapshot sources only, and the restriction is the whole correctness
    argument.** An assertion from a snapshot source means "this alarm is
    standing right now", so an ACTIVE arriving with a stamp older than a stored
    clear is a re-assertion of something this pipeline cleared in error, and
    dating it by the observation is the repair. An assertion from a *log*
    source means "a message existed at T", and an ACTIVE stamped before a later
    clear is then a historical claim that must lose the fold - re-dating it
    would resurrect an ended alert on every re-read of the same page, which is
    both wrong and not idempotent. The first draft of this function ran on both
    collectors and `test_sprint11` caught it: a repeated poll grew the log.

    Kept out of the adapter all the same. The store belongs to the collector,
    the `ThreatSource` protocol is `source_id` and `poll()`, and giving one
    adapter a database handle would put a store parameter on the fixture
    generator too. What travels into the adapter's module is nothing; what
    travels out is a decision made where both the store and the source model
    are already in scope.

    Only ACTIVE rows are asked about, so the query names the handful of keys a
    poll actually raised rather than the store.
    """
    keys = {
        (event.area_id, event.kind)
        for event in events
        if event.state is AlertState.ACTIVE
    }
    return redate_reassertions(
        events, store.newest_clear_by_area_kind(keys), observed_at
    )


def _cmd_collect(args: argparse.Namespace) -> int:
    """Poll the channel once, and leave a record that the poll happened.

    **The store is opened before the fetch, and the ordering is the point
    (D-036).** Until 0.41.0.0 it was opened after, so a refusal returned 3
    having written nothing: an hour the collector was blind and an hour the
    channel was quiet were the same empty set of rows, recoverable afterwards
    at no cost because the information was never written. That is the failure
    `_cmd_rso` was already written to avoid, in the command that polls the
    only source this project has.

    A store that cannot be opened is exit 7 whether or not the poll would have
    succeeded, because a poll nobody can record is not a poll this project can
    claim to have made.
    """
    transport: Transport = StubTransport(Path(args.stub).read_text(encoding="utf-8")) \
        if args.stub else UrllibTransport()
    store = None
    if args.store:
        try:
            store = EventStore(Path(args.store))
        except Exception as failure:  # noqa: BLE001
            print(f"[STORE-FAILED] {failure}")
            return 7
        for column in store.migrations_applied:
            # Once, at the moment it happens, in the journal a person greps.
            # A schema change that leaves no trace is the silent repair this
            # project refuses everywhere else (F124).
            print(f"[STORE-MIGRATED] added {column}, NULL for every earlier row")
    # F123. The baseline for `skipped`, read from the store before the fetch
    # because a `oneshot` has no previous poll of its own. None on the very
    # first poll against a fresh store, and that case stays `unknown` rather
    # than becoming zero.
    last_seen_id = store.newest_page_id(CHANNEL_FEED) if store is not None else None
    started = datetime.now(UTC)
    try:
        body = transport.fetch(CHANNEL_URL)
    except SourceUnavailable as unreachable:
        # Unreachable is not quiet. The exit code distinguishes them so a cron
        # wrapper cannot read an outage as an empty sky.
        #
        # T55. The elapsed time is measured here as well as inside the
        # transport, because a stub or a future transport that refuses without
        # timing itself would otherwise produce a line with no duration at all,
        # and a diagnostic that is present for one implementation and absent
        # for another teaches a reader to stop trusting it. The transport's own
        # figure is the more precise one and appears inside the message; this
        # one bounds the whole attempt.
        waited = (datetime.now(UTC) - started).total_seconds()
        print(f"[UNREACHABLE] {unreachable} (attempt {waited:.2f}s)")
        if store is not None:
            try:
                store.record_refusal(
                    CHANNEL_FEED, CHANNEL_URL, started, str(unreachable), waited
                )
            except Exception as failure:  # noqa: BLE001
                # Printed and not swallowed, and the exit code stays 3. Two
                # things went wrong and the caller can only be told one; the
                # more urgent is that the sky was not observed. A 7 here would
                # report a broken store to a wrapper whose next decision is
                # about the channel.
                print(f"[ATTEMPT-UNLOGGED] {failure}")
        return 3
    fetch_s = (datetime.now(UTC) - started).total_seconds()
    if args.save_raw:
        # Live snapshots complement the backfilled corpus: `mavo backfill`
        # reaches history (0.5.0.0, F44 retired the belief that the corpus
        # could only be built forward), while --save-raw captures the page as
        # it looked at poll time, which history cannot reproduce. A snapshot
        # that silently fails to land is a quiet loss of evidence, hence the
        # loud refusal and its own exit code.
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        snapshot = Path(args.save_raw) / f"channel-{stamp}.html"
        try:
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_text(body, encoding="utf-8")
        except OSError as failure:
            print(f"[SNAPSHOT-FAILED] {failure}")
            return 4
        print(f"snapshot={snapshot}")
    source, events, _ = poll_once(StubTransport(body), last_seen_id=last_seen_id)
    report = source.report
    print(f"messages={report.messages} parsed={report.parsed} "
          f"unparsed={report.unparsed_count} {report.window_line()} "
          f"latency={fetch_s:.3f}s")
    if store is not None:
        # F96. Until 0.24.0.0 this command polled the channel, printed what it
        # understood, and dropped the events. There was no path in the product
        # from the live channel into the store: `fixture` writes a synthetic
        # history, `backfill` writes raw pages, `report` reads. The gap was
        # invisible for as long as every store was filled by hand on a laptop,
        # and it surfaced within an hour of the first real deployment.
        #
        # Both streams or neither. The alert stream and the declaration stream
        # are separate events with separate lifetimes (T16), and a caller that
        # stored one and forgot the other would produce a store whose kind
        # coverage silently read zero.
        #
        # The attempt row is written in the same block and before the events,
        # so a poll that read a page and then failed to store it still leaves
        # the record that it read a page. `items` is the message count on the
        # page and `unreadable` the count the parser refused, which are the
        # two figures `record_read` already means for RSO.
        try:
            store.record_read(
                CHANNEL_FEED,
                CHANNEL_URL,
                started,
                report.messages,
                report.unparsed_count,
                fetch_s,
                report.first_id,
                report.last_id,
            )
            # Deliberately no re-dating here: this is a log source. See
            # `_redate_against_stored_clears` for why the two source models take
            # opposite answers to the same-looking question.
            appended = store.append(events)
            kinds = store.append_kinds(source.kind_events)
        except Exception as failure:  # noqa: BLE001
            # A store that cannot be written is not a quiet poll. Its own exit
            # code, for the same reason --save-raw has one: a wrapper reading
            # only stdout must not mistake a lost write for an empty sky.
            print(f"[STORE-FAILED] {failure}")
            return 7
        print(f"stored={appended} new events, {kinds} new declarations "
              f"(seen={len(events)}/{len(source.kind_events)}; the difference is "
              "idempotence, not loss)")
    if not report.gap_is_known:
        # Two ways to get here now, and they are different facts. Without a
        # store there is nowhere to have kept a baseline; with one, an unknown
        # means either the first poll this store has seen or a page carrying no
        # post ids at all, which is what a restructured or hostile page looks
        # like. The old text asserted the first cause for every case and read
        # as a permanent property of the command rather than as a state (F123).
        if store is None:
            print("NOTE: skipped is unknown, not zero. Without --store there is "
                  "no baseline to measure a skipped window against.")
        elif last_seen_id is None:
            print("NOTE: skipped is unknown, not zero. This store has no earlier "
                  "page bound to measure against; the next poll will have one.")
        else:
            print(f"NOTE: skipped is unknown, not zero. The baseline is post "
                  f"{last_seen_id} and this page carried no post ids at all, "
                  "which is what a restructured page looks like.")
    for sample in report.unparsed[:5]:
        print(f"  unparsed: {sample}")
    if report.unparsed_count:
        print("NOTE: unparsed messages are counted, never dropped. A rising count "
              "means the pattern table is drifting from the channel.")
    return 0



def _cmd_attempts(args: argparse.Namespace) -> int:
    """Delegate to the instrument. The parsing above is the one owned here.

    `mavo.attempts.main` carries its own parser so the tools/ shim and older
    command lines keep working; this wrapper rebuilds the argv it expects
    rather than reaching into its internals, so the two stay honest about
    which one owns the option surface a caller sees.
    """
    argv = ["--store", args.store, "--feed", args.feed,
            "--cadence-s", str(args.cadence_s)]
    if args.since:
        argv += ["--since", args.since]
    if args.until:
        argv += ["--until", args.until]
    return attempts_main(argv)



def _cmd_collect_api(args: argparse.Namespace) -> int:
    """Poll the API once and record both the attempt and what it observed.

    A second command rather than a flag on `collect`, and the separation is
    deliberate. `collect` is written against a page: it reads `newest_page_id`,
    carries `first_id` and `last_id`, and counts messages the parser refused.
    None of those exist for a snapshot API, and threading a second shape
    through that function would put the feed this project currently runs on at
    risk to add one it does not yet run on.

    The feed name is its own, so `mavo attempts --feed ukrainealarm` reads this
    path's cadence without mixing it into the channel's, and so a store holding
    both can say which pipe each observation came down.

    Exit codes match `collect` because a wrapper should not have to learn two
    vocabularies: 3 unreachable, 7 the store failed, 0 otherwise.
    """
    store = None
    if args.store:
        try:
            store = EventStore(Path(args.store))
        except Exception as failure:  # noqa: BLE001
            print(f"[STORE-FAILED] {failure}")
            return 7
        for column in store.migrations_applied:
            print(f"[STORE-MIGRATED] added {column}, NULL for every earlier row")
    try:
        key = read_key(path=Path(args.key_file) if args.key_file else None)
    except (SourceUnavailable, OSError) as missing:
        # A missing key is a configuration fault, not an outage, and it is not
        # written to the attempts table: nothing was attempted.
        print(f"[NO-KEY] {missing}")
        return 2
    if args.store and not args.snapshot:
        # The invocation shaped like production, missing the one flag that
        # lets production ever clear. Loud on every run, because the failure
        # it names is invisible on the map: alerts raise normally and simply
        # never end.
        print("[NO-SNAPSHOT] every run is a first poll and no alert this "
              "source raises will ever clear; a timer-driven deployment "
              "needs --snapshot")
    source = UkrainealarmSource(
        key, snapshot=Path(args.snapshot) if args.snapshot else None
    )
    started = datetime.now(UTC)
    try:
        events = source.poll()
    except SourceUnavailable as unreachable:
        waited = (datetime.now(UTC) - started).total_seconds()
        print(f"[UNREACHABLE] {unreachable} (attempt {waited:.2f}s)")
        if store is not None:
            try:
                store.record_refusal(
                    API_FEED, API_URL, started, str(unreachable), waited
                )
            except Exception as failure:  # noqa: BLE001
                print(f"[ATTEMPT-UNLOGGED] {failure}")
        return 3
    fetch_s = (datetime.now(UTC) - started).total_seconds()
    active = sum(1 for event in events if event.state is AlertState.ACTIVE)
    cleared = len(events) - active
    aged = (f"({source.snapshot_age_s:.0f}s)"
            if source.snapshot_age_s is not None else "")
    print(f"active={active} cleared={cleared} "
          f"unresolved={len(source.unresolved)} "
          f"declined={len(source.declined)} latency={fetch_s:.3f}s "
          f"snapshot={source.snapshot_state}{aged}")
    if source.snapshot_state in ("stale", "corrupt"):
        # Withheld, and said so. Silently withholding clears would put a calm
        # face on a degraded reading, which is the one rendering this project
        # exists to refuse.
        print(f"  snapshot {source.snapshot_state}: clears withheld this "
              "run; a gap in observation is not an all-clear")
    for name in source.unresolved:
        # Named, not counted only. A region the map cannot resolve is a finding
        # about the map, and a number alone cannot be acted on.
        print(f"  unresolved: {name}")
    for name in source.declined:
        # Also named, and separately (F131): the register holds this name and
        # declines it. The repair is a disambiguation or a level, not a row,
        # and folding the two populations into one word hid a live one.
        print(f"  declined by register: {name}")
    if store is not None:
        try:
            store.record_read(
                API_FEED, API_URL, started, active + cleared,
                len(source.unresolved) + len(source.declined), fetch_s,
            )
            # Before the append, and the order is the point: a row re-dated
            # after storage would already have lost to the clear it supersedes.
            redated = _redate_against_stored_clears(store, events, started)
            reasserted = sum(
                1 for event in redated if "superseded_clear" in event.raw_fields
            )
            if reasserted:
                # Loud, because a re-assertion means this pipeline cleared an
                # alarm that had not ended. The row repairs the map; the count
                # is the only place the fault itself is visible.
                print(f"  re-asserted {reasserted} alarm(s) dated by observation: "
                      "the API repeated an alert this pipeline had already cleared")
            appended = store.append(redated)
        except Exception as failure:  # noqa: BLE001
            print(f"[STORE-FAILED] {failure}")
            return 7
        print(f"stored={appended} new events (seen={len(events)}; "
              "the difference is idempotence, not loss)")
    # After the append, deliberately: a failed store keeps the old snapshot
    # standing, so the next run derives the same clears again rather than
    # losing them. The duplicate that retry can produce only nudges an
    # episode's recorded end by one cycle; a lost clear freezes it open.
    try:
        source.save_snapshot()
    except OSError as failure:
        # Loud but not fatal: the events are stored, and the degradation this
        # leaves behind - the next run withholding clears - points the safe
        # way. Invisible it must not be, because persistent write failure
        # here recreates the never-clearing map this flag exists to end.
        print(f"[SNAPSHOT-UNWRITTEN] {failure}")
    return 0


def _key_order(key: tuple[str, ThreatKind]) -> tuple[str, str]:
    """Total order over `(area_id, kind)`.

    `ThreatKind` is an Enum and Enums are unordered, so a plain tuple sort works
    until two keys share an area and then raises. Ordering on the *value* keeps
    the output stable and comparable between runs, which is what an operator
    diffing two dry-runs needs.
    """
    area_id, kind = key
    return (area_id, kind.value)


def _cmd_reconcile(args: argparse.Namespace) -> int:
    """Close channel-era episodes the API's fresh snapshot licenses closing.

    D-041's three conditions, executed: the area is in the table (candidates
    are read with their table names and anything outside would print as such);
    the API resolved and did not mention it - membership in the current
    snapshot is the test, and the snapshot must be `fresh`, because a stale or
    missing one is a gap in observation and a gap licenses nothing; and the
    parent condition is retired, its premise measured false on 2026-08-30,
    when the payload named eight Donetsk raions individually.

    **What this closes and what it only names.** Closed: rows whose newest
    event for their area is `telegram`/ACTIVE and whose area is absent from
    the fresh snapshot - an ended episode the API never saw alive and so will
    never clear (the true ghosts; twelve on 2026-08-30). Named, not touched:
    areas the snapshot holds whose newest row is *not* an API ACTIVE - the
    mirror population, a live alarm the fold may be rendering as calm, which
    is the worse direction and needs its own decision before any write.

    Dry-run is the default and prints exactly what `--apply` would write.
    Closures carry `source_id="reconcile"`, `provenance=INFERENCE`,
    `ts_source` = the snapshot's own `saved_at` (the observation that licensed
    the closure), and the ghost row's kind and oblast, so the episode ends as
    the thing it was. Idempotent by the store's content hash: a second apply
    stores nothing.
    """
    try:
        store = EventStore(Path(args.store))
    except Exception as failure:  # noqa: BLE001
        print(f"[STORE-FAILED] {failure}")
        return 7
    snapshot_path = Path(args.snapshot)
    state, age_s, previous, oblasts = _load_snapshot(
        snapshot_path, SNAPSHOT_MAX_AGE_S, datetime.now(UTC)
    )
    if state != "fresh" or previous is None:
        aged = f" ({age_s:.0f}s)" if age_s is not None else ""
        print(f"[SNAPSHOT-{state.upper()}]{aged} a gap in observation licenses "
              "no closure; nothing examined, nothing written")
        return 3
    raw = json.loads(snapshot_path.read_text(encoding="utf-8"))
    saved_at = datetime.fromisoformat(str(raw["saved_at"]))
    live_keys = set(previous)
    live_areas = {area_id for (area_id, _kind) in previous}
    newest = store.newest_by_area_kind()
    # D-044 part 3. The ghost test is per kind. A stale `telegram` ACTIVE on an
    # area the API is currently reporting under a *different* kind was outside
    # this command's reach entirely while the test asked about the area: the
    # area was present, so nothing about it was a ghost, and the stale row went
    # on holding the area's identity. Thirteen rows sat there on 2026-08-30.
    ghosts = [
        newest[key] for key in sorted(newest, key=_key_order)
        if newest[key].source_id == "telegram"
        and newest[key].state is AlertState.ACTIVE
        and key not in live_keys
    ]
    # The mirror population, per kind: a `(area, kind)` the fresh snapshot is
    # reporting right now whose newest stored row is a clear, or which has no
    # row at all. These are the alarms the map was rendering as calm.
    unmasked_keys = [
        key for key in sorted(live_keys, key=_key_order)
        if key not in newest or is_clear(newest[key].state)
    ]
    now = datetime.now(UTC)
    closures = [
        ThreatEvent(
            area_id=ghost.area_id,
            state=AlertState.CLEAR,
            ts_source=saved_at,
            ts_ingest=now,
            source_id="reconcile",
            kind=ghost.kind,
            provenance=Provenance.INFERENCE,
            raw_fields={"reason": "absent from fresh snapshot", "opened_by": ghost.source_id,
                        "opened_at": ghost.ts_source.isoformat()},
            oblast=ghost.oblast,
        )
        for ghost in ghosts
    ]
    unmasks = [
        ThreatEvent(
            area_id=area_id,
            state=AlertState.ACTIVE,
            # The observation that licenses the row, not the alarm's own start.
            # The API's `began` is kept beside it because it is true and is a
            # different claim: this row says when we saw the alarm standing.
            ts_source=saved_at,
            ts_ingest=now,
            source_id="reconcile",
            kind=kind,
            provenance=Provenance.INFERENCE,
            raw_fields={
                "reason": "present in fresh snapshot, no live row for this kind",
                "began": previous[(area_id, kind)].isoformat(),
                "superseded": (
                    newest[(area_id, kind)].ts_source.isoformat()
                    if (area_id, kind) in newest else "none"
                ),
            },
            oblast=oblasts.get((area_id, kind), ""),
        )
        for (area_id, kind) in unmasked_keys
    ]
    mode = "apply" if args.apply else "dry-run"
    print(f"reconcile {mode}: ghosts={len(closures)} masked={len(unmasks)} "
          f"snapshot_areas={len(live_areas)} snapshot_keys={len(live_keys)} "
          f"saved_at={saved_at.isoformat()}")
    for closure in closures:
        print(f"  close {closure.area_id} kind={closure.kind.value} "
              f"oblast={closure.oblast or 'unknown'} "
              f"opened_at={closure.raw_fields['opened_at']}")
    for event in unmasks:
        verb = "unmask" if args.unmask else "MASKED"
        print(f"  {verb} {event.area_id} kind={event.kind.value} "
              f"began={event.raw_fields['began']} "
              f"superseded={event.raw_fields['superseded']}")
    # The gate, and it is a gate rather than a warning. Closing a per-kind ghost
    # on an area the snapshot is reporting removes that area's last live kind
    # unless the snapshot's own kind is written in the same breath. Refusing is
    # the only safe answer: the alternative is a command that takes an area dark
    # while reporting success.
    contested = sorted({ghost.area_id for ghost in ghosts} & live_areas)
    if args.apply and contested and not args.unmask:
        print(f"[REFUSED] {len(contested)} ghost(s) sit on areas the fresh snapshot "
              "is reporting; closing them without --unmask would take a live area "
              "dark. Re-run with --unmask, or with --store only to inspect.")
        for area_id in contested:
            print(f"  contested {area_id}")
        return 4
    writes = closures + (unmasks if args.unmask else [])
    if not args.apply:
        pending = "closures and unmasks" if args.unmask else "closures"
        print(f"nothing written (pass --apply to write the {pending} above)")
        return 0
    try:
        appended = store.append(writes)
    except Exception as failure:  # noqa: BLE001
        print(f"[STORE-FAILED] {failure}")
        return 7
    print(f"stored={appended} rows (seen={len(writes)}: {len(closures)} closures, "
          f"{len(unmasks) if args.unmask else 0} unmasks; the difference "
          "is idempotence, not loss)")
    return 0

def _cmd_rso(args: argparse.Namespace) -> int:
    """Poll the Polish civil-warning feed and record what happened.

    **Every category, or the reading is partial and says nothing about it.**
    The endpoint offers a scope called `wszystkie`, and measured 2026-08-22 it
    returned 156 communiques where the five categories hold 461 between them
    with no overlap. The 305 it drops are `stany-wod`, and nothing in the
    payload or the publisher's documentation mentions the omission. A default
    that reads `wszystkie` would be a partial answer shaped exactly like a
    complete one, so this command walks the list instead.

    **The attempt is logged before the exit code is chosen**, and that ordering
    is the point. A refusal that leaves no row behind is an hour this collector
    cannot distinguish from an hour Poland was quiet, and the distinction is
    unrecoverable afterwards at any cost, because the information was never
    written (FEED-SPEC nine).

    Exit codes match `collect`: unreachable is 3 and a failed store is 7, so a
    wrapper reading only stdout cannot mistake either for an empty country.
    """
    transport: Transport = StubTransport(Path(args.stub).read_text(encoding="utf-8")) \
        if args.stub else UrllibTransport()
    store = None
    if args.store:
        try:
            store = EventStore(Path(args.store))
        except Exception as failure:  # noqa: BLE001
            print(f"[STORE-FAILED] {failure}")
            return 7

    if args.url:
        targets = [args.url]
    elif args.category:
        targets = [rso_page_url(args.category, args.page)]
    else:
        targets = [rso_page_url(name, args.page) for name in RSO_CATEGORIES]

    seen = appended = unreadable = 0
    refused = 0
    for url in targets:
        started = datetime.now(UTC)
        try:
            page, elapsed = rso_poll_once(transport, url)
        except SourceUnavailable as unreachable_now:
            if store is not None:
                store.record_refusal(RSO_FEED, url, started, str(unreachable_now))
            waited = (datetime.now(UTC) - started).total_seconds()
            print(f"[UNREACHABLE] {unreachable_now} (attempt {waited:.2f}s)")
            refused += 1
            # No break. One category refusing is not the feed refusing, and
            # abandoning the rest would turn one failure into four silences.
            continue
        if store is not None:
            store.record_read(RSO_FEED, url, started, len(page.communiques), page.unreadable)
            try:
                appended += store.append_communiques(RSO_FEED, page.communiques)
            except Exception as failure:  # noqa: BLE001
                print(f"[STORE-FAILED] {failure}")
                return 7
        seen += len(page.communiques)
        unreadable += page.unreadable
        print(f"read={len(page.communiques)} unreadable={page.unreadable} "
              f"items_on_page={page.items_on_page} items_per_page={page.items_per_page} "
              f"latency={elapsed:.3f}s {url}")

    print(f"seen={seen} unreadable={unreadable} refused={refused}/{len(targets)} "
          f"stored={appended} (seen minus stored is idempotence, not loss)")
    if unreadable:
        print("NOTE: rows without an identifier are counted, never dropped. A page that "
              "lost half its rows must not read as a short page.")
    if refused:
        # Any refusal makes the reading partial, and a partial reading that
        # exits 0 is the shape this project refuses everywhere else.
        return 3
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    """Render the current picture from a store, and optionally the contract file.

    Exit codes carry the feed state, because a wrapper that only reads stdout
    must not be able to treat blindness as a quiet sky: 0 for a fresh picture,
    5 for degraded, 6 for blind. The report itself is printed in every case -
    a blind report is an output, not an error, and suppressing it would be the
    silence this command exists to prevent.
    """
    store = EventStore(Path(args.store))
    if args.watch:
        if not args.json:
            print("--watch needs --json: the loop exists to publish the contract",
                  file=sys.stderr)
            return 2
        def announce(report: Report) -> None:
            print(f"{report.as_of.isoformat(timespec='seconds')} "
                  f"feed={report.feed_state.value} "
                  f"western_active={len(report.western_active)}", flush=True)

        # T23, F103. `publish` has accepted a `log` since the sink shipped at
        # 0.23.0.0 and no caller ever passed one, so `MAVO_LOG_FILE` was read
        # by nothing in the package while a production unit set it. The whole
        # of the repair is this argument: the loop already emits every line
        # the design calls for, to a sink that was never constructed.
        #
        # Constructed here rather than inside `publish` on purpose. A function
        # that reaches into the environment for its own instrumentation cannot
        # be tested without one, and `from_environment` returns `None` rather
        # than a no-op writer precisely so that the decision to run without a
        # log is made by a caller and is visible.
        log = sink_from_environment()
        if log is not None:
            print(f"run-log={log.path}", flush=True)
        outcome = publish(
            store.replay,
            Path(args.json),
            interval_s=args.interval,
            max_cycles=args.max_cycles,
            valid_for_s=args.valid_for,
            on_cycle=announce,
            feed_path=Path(args.feed) if args.feed else None,
            log=log,
        )
        print(outcome.line())
        # A loop that ends is not an error: it was told to stop, or the
        # operator stopped it. A write that failed is, and it is the only
        # reason that returns non-zero, because it is the only one that
        # leaves the consumer reading a file nobody is refreshing.
        return 7 if outcome.reason.startswith("write failed") else 0
    report = compose(store.replay(), valid_for_s=args.valid_for)
    print(render_text(report))
    if args.json:
        written = write_contract(report, Path(args.json))
        print(f"contract={written} v={SCHEMA_VERSION}")
    if args.feed:
        # Announced with its own line and its own count, because a feed file
        # that exists and is empty is a different state from one that was
        # never asked for, and an operator reading stdout should not have to
        # infer which happened.
        events = len(report.feed.events) if report.feed is not None else 0
        written_feed = write_feed(report, Path(args.feed))
        print(f"feed={written_feed} v={SCHEMA_VERSION} events={events} "
              f"window={FEED_WINDOW_S}s")
    return {FeedState.OK: 0, FeedState.DEGRADED: 5, FeedState.BLIND: 6}[report.feed_state]


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
        "policy", help="score the regime-split decision policy"
    )
    policy.add_argument("--weeks", type=int, default=208)
    policy.add_argument("--seed", type=int, default=1968)
    policy.set_defaults(func=_cmd_policy)

    fill = subparsers.add_parser(
        "backfill",
        help="walk channel history backwards, writing raw pages",
    )
    fill.add_argument("--out", required=True, help="directory for raw page snapshots")
    fill.add_argument("--pages", type=int, default=10, help="how many pages to fetch")
    fill.add_argument("--before", type=int, help="start below this post id (default: newest)")
    fill.add_argument("--stop-at-id", type=int, help="stop once a page reaches this id or lower")
    fill.add_argument("--delay", type=float, default=1.0,
                      help="seconds between requests; the tolerated rate is unknown")
    fill.add_argument("--quiet", action="store_true",
                      help="suppress the progress lines on stderr")
    fill.add_argument("--resume", action="store_true",
                      help="continue below the lowest id already in --out")
    fill.add_argument("--stub", help="read a saved page instead of the network")
    fill.set_defaults(func=_cmd_backfill)

    collect = subparsers.add_parser(
        "collect", help="poll the public channel once and report what was understood"
    )
    collect.add_argument("--stub", help="read a saved page instead of the network")
    collect.add_argument(
        "--store",
        help="append the parsed events and declarations to this store. Without "
             "it the poll reports and records nothing, which is what it did "
             "until 0.24.0.0 (F96)",
    )
    collect.add_argument(
        "--save-raw",
        help="write the fetched page verbatim into this directory before parsing "
             "(builds the sprint-5 corpus; the page is a ~20-message window, F27)",
    )
    collect.set_defaults(func=_cmd_collect)

    collect_api = subparsers.add_parser(
        "collect-api",
        help="poll api.ukrainealarm.com once and record the attempt",
    )
    collect_api.add_argument("--store", help="event store to append to")
    collect_api.add_argument(
        "--key-file",
        help="file holding the API key, 0600 and owned by the polling user. "
             "Omit to read MAVO_UKRAINEALARM_KEY, which is visible in "
             "/proc/<pid>/environ to anything running as the same user",
    )
    collect_api.add_argument(
        "--snapshot",
        help="file carrying the previous snapshot across runs. A oneshot "
             "deployment without it never observes an area leaving the "
             "snapshot, so no alert it raised ever clears",
    )
    collect_api.set_defaults(func=_cmd_collect_api)

    rso = subparsers.add_parser(
        "rso", help="poll the Polish civil-warning feed once and record the attempt"
    )
    rso.add_argument(
        "--category",
        choices=RSO_CATEGORIES,
        help="one published category. Omit to walk all five, which is the "
             "only way to read the whole feed: the endpoint's own "
             "`wszystkie` returns 156 of 461 communiques and says nothing "
             "about the 305 it drops (T67)",
    )
    rso.add_argument(
        "--page", type=int, default=0,
        help="page number, or 0 for the unpaged reading. Pages are 1-based "
             "and the stop condition is an empty page, never a count derived "
             "from the feed's own `totalItems`, which reports the page rather "
             "than the total",
    )
    rso.add_argument(
        "--url",
        help="read this exact address instead, bypassing category selection. "
             "For reaching one voivodeship or a page nobody has modelled yet",
    )
    rso.add_argument("--stub", help="read a saved page instead of the network")
    rso.add_argument(
        "--store",
        help="append the communiques, and log the attempt whether or not it "
             "succeeded. Without it a refusal leaves no trace and a dead "
             "collector is indistinguishable from a quiet country",
    )
    rso.set_defaults(func=_cmd_rso)

    attempts = subparsers.add_parser(
        "attempts",
        help="attempt completeness for one feed: polls made, polls refused, "
             "stretches with neither, and messages that passed unseen (T66, D-038)",
    )
    attempts.add_argument("--store", required=True, help="path to the event store")
    attempts.add_argument(
        "--feed", default="channel",
        help="feed name in feed_attempts: `channel` or `rso`",
    )
    attempts.add_argument(
        "--cadence-s", type=float, required=True,
        help="the timer interval, in seconds. Required, never inferred: this "
             "command cannot read the timer, and deriving the interval from "
             "the data would calibrate the gap detector on the gaps it is "
             "looking for",
    )
    attempts.add_argument("--since", help="ISO timestamp with an offset, inclusive")
    attempts.add_argument("--until", help="ISO timestamp with an offset, exclusive")
    attempts.set_defaults(func=_cmd_attempts)

    report_cmd = subparsers.add_parser(
        "report", help="render the current picture from a store"
    )
    report_cmd.add_argument("--store", required=True, help="path to the event store")
    report_cmd.add_argument(
        "--json", help="also write the state.json contract file to this path"
    )
    report_cmd.add_argument(
        "--feed",
        help="also write the feed.json event history to this path "
             "(24 hours, all areas, both roles; fetched on demand by a "
             "consumer rather than on every cycle)",
    )
    report_cmd.add_argument(
        "--valid-for", type=int, default=DEFAULT_VALID_FOR_S,
        help="seconds a report may be trusted after its newest observation "
             "(default %(default)s, an assumption rather than a measurement)",
    )
    report_cmd.add_argument(
        "--watch", action="store_true",
        help="publish the contract on a fixed interval until stopped (needs --json)",
    )
    report_cmd.add_argument(
        "--interval", type=float, default=30.0,
        help="seconds between cycles under --watch (default %(default)s)",
    )
    report_cmd.add_argument(
        "--max-cycles", type=int, default=None,
        help="stop after this many cycles; omit to run until interrupted",
    )
    report_cmd.set_defaults(func=_cmd_report)

    reconcile_cmd = subparsers.add_parser(
        "reconcile",
        help="close channel-era episodes a fresh API snapshot licenses closing",
    )
    reconcile_cmd.add_argument("--store", required=True, help="path to the event store")
    reconcile_cmd.add_argument(
        "--snapshot", required=True,
        help="the collector's persisted snapshot; must be fresh, a gap licenses nothing",
    )
    reconcile_cmd.add_argument(
        "--apply", action="store_true",
        help="write the rows; without it every planned row is printed and none lands",
    )
    reconcile_cmd.add_argument(
        "--dry-run", action="store_true",
        help="explicit form of the default. Accepted because docs/DEPLOYMENT.md "
             "has documented it since the D-041 switchover while the parser "
             "exited 2 on it (F134), and a runbook command that fails is worse "
             "than a flag that does nothing",
    )
    reconcile_cmd.add_argument(
        "--unmask", action="store_true",
        help="also raise an ACTIVE for every (area, kind) the fresh snapshot is "
             "reporting whose newest stored row is a clear or missing (D-044). "
             "Required alongside --apply when a ghost sits on an area the "
             "snapshot is reporting, because closing it alone would take a live "
             "area dark",
    )
    reconcile_cmd.set_defaults(func=_cmd_reconcile)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
