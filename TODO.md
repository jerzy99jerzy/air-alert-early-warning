# TODO

Every item carries a status, a blocker type where one exists, and an acceptance
test, so that "done" is not a matter of opinion.

Status: `ready` | `blocked-external` | `decision` | `debt`

## T1. Request the alerts.in.ua API token
Status: `blocked-external` (access)
**This is the only item that does not shrink by writing code.** It gates the real
backtest, which gates every audience in `docs/MVP.md`. It should have been the
first action of sprint 0 and precedes any further editor work.
**Acceptance:** a token in the local keychain and one successful authenticated
call recorded with its latency.

## T2. Split the decision into missile and drone regimes
Status: `done` (sprint 3, 0.2.0)
Sprint 2 finding: no single rule holds both the alarm rate and drone-night
recall.
**Acceptance met:** `mavo policy` reports both regimes; the missile regime passes
all three conditions against its allocated share. The drone regime does not, and
is demoted under D-009 rather than accommodated.

## T3. Resolve R2, which currently adds nothing
Status: `ready` (still open after sprint 3)
The conjunction's numbers are identical to R3, so the third conjunct is inert.
**Acceptance:** either R2 is redefined and the conjunction's contingency table
differs from R3's, or R2 is removed and the README stops describing it.

## T4. Executable claim behind the never-raise parser guarantee
Status: `ready` (narrowed after sprint 4)
Sprint 4 delivered the suite for the Telegram adapter (F17, harness A9); the
fixture source generates rather than parses, so hostile input does not apply to
it. What remains is the rule for adapters that do not exist yet.
**Acceptance:** every future `ThreatSource` that parses external input lands with
its hostile suite in the same release, and a lint or convention makes an adapter
without one visible. Malformed, truncated, oversized and hostile payloads; no
exception escapes; unparseable records counted rather than dropped.

## T5. Rolling feed-latency drift detection
Status: `ready`
Residual risk in the threat model: a subtly late source degrades lead time
without tripping anything.
**Acceptance:** a test where a source's latency doubles mid-history and the run
reports degradation.

## T6. Legal position on distributing warnings beyond a private circle
Status: `decision`
Does not shrink by writing code. Needs counsel, not a sprint.
**Acceptance:** a written position in `docs/DECISIONS.md` with a named basis.

## T7. Onboarding probe from a clean clone
Status: `ready`
**Acceptance:** a fresh clone into an empty directory, README followed from zero,
with the point of failure recorded. Not "it looks correct".

## T8. Is there any ingestible Polish channel at all
Status: `blocked-external` (access)
Sprint 6 assumes a Polish feed exists to switch to. RSO and NOTAM are machine
readable; RCB and the announced government application probably are not.
**Acceptance:** one working read from at least one Polish source, or a written
finding that none exists and what that does to sprint 6.

## T9. Keep the coverage floor a ratchet
Status: `debt`
The floor is set at 95, three points below the 98.3 measured in sprint 2. It
rises when a sprint genuinely raises coverage and never as a target, because a
target invites tests written for the number.
**Acceptance:** any commit that raises measured coverage by more than five points
raises the floor in the same commit.

## T10. Find a history source deep enough to calibrate on
Status: `blocked-external` (access)
Neither Ukrainian API carries multi-year history: alerts.in.ua exposes
`month_ago`, ukrainealarm returns the last 25 alerts per region. The real-data
backtest assumed several years and roughly a dozen positive events.
**Acceptance:** either a source covering the full period, or a written decision
in `docs/DECISIONS.md` accepting calibration on one month with the resulting
confidence intervals stated.

## T11. Ask whether anyone actually wants this
Status: `ready`
No recipient has been identified. `docs/MVP.md` names a small trusted group and
nobody in it has been asked. Until then the alarm threshold is calibrated against
a hypothetical tolerance.
**Acceptance:** two conversations, recorded: would they want this, and at what
firing rate would they stop reading it. The second answer replaces the assumed
two per week.

## T12. Detect changes to the ukrainealarm offer contract
Status: `ready`
The contract changes unilaterally by being reposted, with no notification
obligation. The only defence is our own check.
**Acceptance:** the collector hashes `contract.pdf` on each run and logs a change.

## T13. Record the revocability of both Ukrainian feeds
Status: `done` (0.3.2.0)
**Acceptance met:** MT9 and MT10 in `docs/THREAT-MODEL.md`, D-010 in
`docs/DECISIONS.md` with the conditions that would reopen the dependency
question. Found open during the 0.3.2.0 audit because MT9 cited D-010 before it
existed (F33).

## T14. Second signal type for the drone regime
Status: `ready`
Promoted from enrichment to prerequisite by the sprint 3 finding. Alert state
alone cannot discriminate within drone nights, so the drone tier stays silent
until another channel exists.
**Acceptance:** ADS-B activity over eastern Poland ingested as a `ThreatSource`,
and a drone-regime rule that clears its allocated share on the adversarial
history without lowering the recall floor.

## T15. Raion and hromada gazetteer
Status: `ready`
F24. The channel names raions and hromadas; nothing in a message identifies the
oblast. Without a mapping, the border-oblast rules that the entire thesis rests
on have no input.
**Acceptance:** every area name appearing in a week of channel content resolves
to an oblast, or is reported as unresolved. Unresolved is never silently skipped.

## T16. Means of attack as its own message class
Status: `ready`
F25. `kind` is modelled as an attribute of an alert; the channel emits it as a
separate message tied to a hromada, with its own lifetime.
**Acceptance:** a threat-type message produces its own event, and the decision
layer joins it to alerts by area and time window rather than reading it off the
alert.

## T17. The fourth state: a partial all-clear
Status: `done` (sprint 5, 0.4.0.0)
**Acceptance met:** `AlertState.PARTIAL_CLEAR` exists, `classify_state` returns
it for a message carrying both an all-clear and a continuation marker, and
`test_sprint5.py` asserts it never resolves to CLEAR or to actionable. The lint
behind the README claim enumerates the enum, so a fifth state is covered on the
day it is added.
Original text:
F26. "Відбій тривоги... тривога ще триває у:" is an all-clear that says the alert
continues. `AlertState` has no member for it.
**Acceptance:** a partial all-clear is a distinct state, and a test asserts it
never resolves to CLEAR.

## T18. Detect a skipped message window
Status: `done` (sprint 5, 0.4.0.0)
**Acceptance met:** consecutive polls compare post ids and report the skipped
count; where it cannot be measured, on a first poll or a page without ids, it is
reported as unknown rather than zero. MT12 and harness A11.
Original text:
F27. The page serves roughly the last twenty messages. During a mass alert the
channel emits more than that in a short period, and a skipped message leaves no
trace.
**Acceptance:** consecutive polls compare message ids; a gap is reported rather
than inferred from silence.

## T19. Build the real-message corpus
Status: `ready`, **no longer time-boxed**
`mavo backfill` reaches history rather than waiting for it (0.5.0.0). The window
constraint that shaped D-011 and the sprint 5 scope decision did not exist (F44).
**Acceptance:** a contiguous corpus covering at least the last 90 days, exit code
0 from `mavo backfill`, its id range and time span recorded in `STATUS.json`, and
the design/holdout boundary computed and written down per D-012 before any
message content is read.

## T21. Measure the tolerated request rate
Status: `done` (0.5.1.0), with a named limit
**Acceptance met:** measured at 0.5 s and 0.2 s over 20 requests each, both clean
with no silent page truncation, recorded in `docs/METHODOLOGY.md` with
provenance. The default was **not** changed: a burst of 20 does not license a
claim about a run of 2900. What remains unmeasured is stated in the same table
rather than left as an implication.
Original text:
`--delay 1.0` is a guess made deliberately conservative because the cost of being
wrong is losing access to the only corpus this project has. A guess is not a
measurement and is labelled as neither in the code.
**Acceptance:** a short run at increasing rates with the response status
recorded, the tolerated rate written into `docs/METHODOLOGY.md` with its
provenance, and the default changed only if the measurement supports it.

## T20. OpenSky Network registration
Status: `ready`, self-service
Recategorised from a blocked external dependency: no approval step exists, only
the registration itself. It gates T14, which gates any drone-tier alarm (D-009),
and it costs minutes.
**Acceptance:** credentials stored outside the tree and one authenticated ADS-B
read over eastern Poland recorded with its latency.
