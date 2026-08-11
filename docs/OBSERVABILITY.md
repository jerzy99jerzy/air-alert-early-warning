# Watching a run

Version: 1.1 / 2026-08-11
Status: **partly built.** `mavo/obs.py` is the sink and `tools/progress.py` is
the reader, both shipped at 0.23.0.0 against the acceptance in section 9, five
of whose seven criteria are met. What is still a plan: `mavo watch` itself,
which waits on T25, and everything downstream of a notifier, which is S10.
Sections describing those still describe what is designed rather than what
runs, and the acceptance criteria stay as written, because criteria adjusted to
what the code turned out to do are not criteria.
Companion: `docs/MOBILE.md` (phase M0, the daemon this observes),
`docs/MECHANISMS.md` (the counters), `docs/METHODOLOGY.md` (why unknown is
never zero).

## Contents

1. [Why this exists here specifically](#1-why-this-exists-here-specifically)
2. [The durable sink](#2-the-durable-sink)
3. [What a line may and may not contain](#3-what-a-line-may-and-may-not-contain)
4. [Watching a cycle](#4-watching-a-cycle)
5. [Degradation is a rendering, not a footnote](#5-degradation-is-a-rendering-not-a-footnote)
6. [The reader is a reader](#6-the-reader-is-a-reader)
7. [Explain](#7-explain)
8. [Dry run](#8-dry-run)
9. [Acceptance](#9-acceptance)
10. [What this does not give you](#10-what-this-does-not-give-you)

## 1. Why this exists here specifically

A pipeline that runs once and prints a report can be judged by its report. A
daemon that polls every minute for weeks in shadow mode cannot, and shadow mode
is where this project spends its next stretch: the whole point of M0 is to
produce a record of decisions that were never sent, which means **the log is the
deliverable**, not a diagnostic side effect.

Two consequences that shape everything below.

The record must be complete independently of how anyone invoked the process. An
audit trail whose contents depend on which verbosity flag was passed that day is
not evidence, and this repository already refuses that pattern elsewhere: the
gate does not have a lenient mode either.

The record must distinguish three outcomes, not two. Every other tool of this
shape reports success and failure. Here a cycle can also be **unmeasurable**,
and collapsing that into either of the other two is the founding defect of the
project restated at the observability layer. A stage that could not measure
something prints `unknown`, and a stage that measured zero prints `0`, and the
renderer must make those visually distinct or it is lying quietly.

## 2. The durable sink

`MAVO_LOG_FILE` attaches a rotating JSONL sink carrying the full event stream at
DEBUG regardless of console flags. The console keeps its own level and its own
shape; the sink is always one JSON object per line.

```
MAVO_LOG_FILE=./state/run.jsonl mavo watch -q &
python -m tools.progress --follow
```

Two constraints inherited from defects this repository already paid for.

**Appends are atomic per line** and rotation renames rather than truncates
(F51). A log that can be interrupted mid-line yields a truncated final record
whose absence is indistinguishable from a cycle that never ran, which is the
same invisible hole the corpus census refuses.

**Rotation is by size with a retained count, and the retention is stated in the
sink's own first line.** A log that silently dropped its oldest evidence would
let a post-mortem read a partial history as a complete one.

## 3. What a line may and may not contain

This is where MAVO diverges from the pattern it borrows, and the divergence is
not stylistic.

**The sink carries counts, ids, timings and verdicts. It does not carry message
text.** Two independent reasons, either sufficient:

- **The holdout.** The design and holdout windows were split before any message
  content was read (D-012a). A log that echoed message bodies would put holdout
  content in front of the author's eyes during ordinary operations, and the
  split would be spent without anyone deciding to spend it. Contamination by
  convenience is still contamination.
- **The security rule.** `SECURITY.md` already forbids raw per-subject records
  in committed artifacts. A run log is exactly the artifact that gets pasted
  into an issue.

Where a body is genuinely needed to diagnose a parse failure, the line carries a
**hash and a length**, and the raw page is already on disk under `--save-raw` if
the operator asked for it. `MAVO_LOG_BODIES=1` exists for local debugging, and
its use is itself logged as a line, because a switch that disables an evidential
guarantee should leave a mark in the record it weakened.

One line, elided:

```json
{"ts":"2026-08-09T21:04:07.412Z","cycle":"7f2a1c","stage":"parse","level":"INFO",
 "event":"parse.report","messages":20,"parsed":0,"unparsed":20,"skipped":null,
 "skipped_reason":"first_poll_has_no_baseline","provenance":"measured","ms":8}
```

`skipped` is `null` with a stated reason, never `0`. Any consumer that renders
`null` as zero is broken, and the acceptance test below asserts against exactly
that.

## 4. Watching a cycle

`tools/progress.py` reports the run in the shape of a playbook run rather than a
dashboard. Append-only lines, no cursor movement, no full-screen redraw, colour
dropped when the output is not a terminal. Deliberate rather than minimal: this
runs over SSH, inside a scheduler's captured output, and piped into `less` or a
file, and a view that repaints is unreadable in all three. The captured text is
the text the operator saw.

```
CYCLE [7f2a1c] 2026-08-09T21:04:07Z ******************************************

STAGE [poll : t.me/s/air_alert_ua] *******************************************
ok: [poll] duration=412ms bytes=98214 window=321498..321517

STAGE [parse : messages to events] *******************************************
ok: [parse] duration=8ms messages=20 parsed=0 unparsed=20 skipped=unknown (first poll)

STAGE [store : append] *******************************************************
ok: [store] duration=3ms appended=0 duplicates=0

STAGE [evaluate : rules per regime] ******************************************
note: [evaluate] no_events_to_evaluate

CYCLE RECAP ******************************************************************
poll     : ok        412ms   bytes=98214 window=321498..321517
parse    : ok          8ms   messages=20 parsed=0 unparsed=20 skipped=unknown
store    : ok          3ms   appended=0 duplicates=0
evaluate : ok          2ms   rules=2 fired=0
policy   : ok          1ms   rules=2 fired=0 ledger=untouched
notify   : shadow      0ms   would_send=0
  uptime=71h12m cycles=4271 degraded=3 last_degraded=2026-08-09T04:11:52Z
  parsed_ratio=0.00 (F23 open, sprint 7)
```

The recap line every operator will actually read is `parsed=0 unparsed=20`. That
is the shipped classifier defect printing itself once a minute for weeks, which
is the correct behaviour: a known defect that stops being visible stops being
known. When sprint 7 lands, the same line is how the fix is observed rather than
asserted.

`--follow` on a live file and the same command on a finished file are one code
path, so a post-mortem and a live view cannot drift apart. There is no separate
history mode to keep in step.

## 5. Degradation is a rendering, not a footnote

The failure case has to be as legible as the success case, because it is the one
that matters at 04:00.

```
STAGE [poll : t.me/s/air_alert_ua] *******************************************
refused: [poll] refusal.source_unavailable attempt=3 last_ok=2026-08-09T04:02:10Z

CYCLE RECAP ******************************************************************
poll     : refused     -     refusal.source_unavailable streak=3
parse    : unknown     -     no body to parse
store    : ok          1ms   appended=0 duplicates=0
evaluate : unknown     -     inputs unknown, not empty
policy   : ok          1ms   rules=2 fired=0 ledger=untouched
notify   : sent        7ms   class=degradation topic=mavo-degraded ledger=n/a
  the system is blind for lviv, volyn since 04:02:10Z
```

Three things in that block are load-bearing. `parse` and `evaluate` print
`unknown`, not `ok` with zeros, because there was no input rather than no
events. `notify` fires on the **degradation** class, which is uncounted against
any rate limit the recipient has set, so blindness reports itself through a
channel the recipient can tune separately from alarms. And the recap says *blind*, in those words, because a recap that
reads as calm during an outage has reconstructed unknown-resolves-to-clear one
layer above the code that forbids it.

## 6. The reader is a reader

`tools/progress.py` imports the stage vocabulary from `mavo.obs.STAGES` and no
call site in the pipeline knows it exists. A progress indicator wired into the
run would be a second statement about where the run is, and the first thing it
would do is disagree with the log.

The dependency direction is enforced, not merely intended: a domain lint fails
the build if any module under `mavo/` imports `tools.progress`, in the same
family as the existing rule that keeps network reach in one file.

`mavo.obs` is also the only writer of the sink. One module owns the vocabulary,
the line schema and the file handle, which is what makes the schema version
below a single point of change rather than a convention.

## 7. Explain

```
mavo explain --night 2026-07-14
mavo explain --rule CONJ-missile
```

Prints the derivation rule by rule and exits without writing anything. Priority
here is decided in deterministic code with no model anywhere in the path, and a
decision that cannot show its working is, to anyone who did not write the code,
indistinguishable from an opaque one.

**Rules that did not fire are printed too**, with the conjunct that failed,
because "evaluated and did not apply" is a different claim from "never
considered", and at a base rate of 57% the second is the more likely mistake.

For a rule, explain prints its gate arithmetic in the vocabulary of
`docs/COMPUTATION.md`: the contingency table, recall, the alarm rate against the
allocated share, the Wilson interval on precision, the one-sided Fisher p, and
the verdict with the condition that decided it. A rule that fails prints which
of the three conditions failed, so "this rule is not allowed to wake anyone" has
a reason attached rather than a boolean.

Where an input is unknown, explain says unknown and stops deriving. It does not
substitute a default and continue, because a derivation completed on invented
inputs is worse than no derivation.

## 8. Dry run

`--dry-run` performs no external write. Reads still happen, so a cycle can be
inspected end to end without touching anything downstream. In this system the
external writes are three, and all three are suppressed: the notification, the
delivery ledger row, and the raw snapshot under `--save-raw`.

The event store is deliberately **not** suppressed, and this is the one place
the pattern is adapted rather than copied. The store is a local derived artifact
rebuilt from the raw corpus at will (D-013), so writing to it is not an external
effect. Suppressing it would make a dry run diverge from a real one in the state
that feeds the next cycle's comparison, and a rehearsal that changes the thing
being rehearsed is not a rehearsal.

`--dry-run` prints the same recap as a live cycle with `notify: dry-run` in
place of `sent`, so the two are comparable line by line.

## 9. Acceptance

Written before the code. Each is a test, not an impression.

**State at 0.23.0.0, when the sink and the reader shipped.** Five of the seven
are met and live in `tests/test_obs.py`. Two are not, and which two is stated
rather than the sprint being rounded up:

- *A refused poll produces a degradation notification within one cycle* needs a
  notifier, which is S10. The publishing loop's blindness accounting exists and
  is held by `tests/test_sprint10.py`; the notification does not exist.
- *`tools/progress.py` replaying a finished file produces the same recap the
  live view produced* needs a live view, and there is no channel-polling loop
  yet: `mavo watch` waits on T25, which is a decision rather than an
  implementation. The reader is tested against files, which is a weaker claim
  and is recorded as one.

- Console verbosity flags do not change the sink. Two runs over identical
  injected input, one with `-q` and one with `-vv`, produce byte-identical JSONL
  after normalising timestamps and durations.
- A stage that cannot measure emits `null` with a `*_reason`, and the renderer
  prints `unknown`. Asserted by a fixture whose parse report has no baseline: a
  rendering containing `skipped=0` fails the test.
- A refused poll produces a degradation notification within one cycle and is
  not rendered as an alarm. Asserted against an injected notifier.
- The sink contains no message text under default settings. A hostile fixture
  carrying a recognisable token in every message body must not produce that
  token anywhere in the log file.
- Killing the process mid-write leaves the last line either complete or absent,
  never truncated, and the reader reports the gap rather than skipping it.
- `tools/progress.py` replaying a finished file produces the same recap the live
  view produced for that run.
- A domain lint fails when a module under `mavo/` imports the reader.

## 10. What this does not give you

It does not make the daemon reliable. It makes the daemon's behaviour legible,
which is a different and smaller claim. A cycle that silently produced wrong
events will produce a beautiful record of doing so, and the only defence against
that is the same one as everywhere else here: the attacks in
`tests/harness/`, and the fixture that is captured rather than imagined (F50).

It does not replace the delivery ledger. The ledger is the authoritative record of
what was sent; the sink is the observation stream. A log line carries the
`ledger_id` so the two can be reconciled, and a notification on a phone with no
matching ledger row is finding-grade rather than a display bug.

It is not a metrics endpoint. Aggregation over the JSONL is a query someone
writes when there is a question, not a dashboard maintained in advance. The
schema carries `"v": 1` so that query does not have to guess.
