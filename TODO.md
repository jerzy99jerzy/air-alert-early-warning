# TODO

<!-- index:begin -->

### Where the backlog stands

**12 of 50 closed, 38 open.** Counted from the entries below by `tools/todo_index.py`, which the gate re-runs, so this table cannot drift from the list it summarises.

| State | Count | What it means |
| --- | --- | --- |
| `done` | 12 | Finished, with the release that closed it named in the entry |
| `ready` | 30 | Nothing external blocks it; it needs a session |
| `decision` | 3 | Waiting on a judgement rather than on work |
| `blocked-external` | 2 | Waiting on somebody outside this project |
| `deferred` | 2 | Deliberately parked, with the decision that parked it named |
| `debt` | 1 | Known cost carried on purpose |

### Priority tiers

Tiers are a claim about *order*, not about importance, and they move as the project moves. Declared per entry so this table is generated rather than maintained.

| Tier | Meaning |
| --- | --- |
| **1** | Blocks something already promised, or a measurement without which a shipped claim is unsupported |
| **2** | Real work that nothing is waiting on today |
| **3** | Worth doing, worth dropping if the project turns |

**Tier 1, 7 open:** [T6](#t6-legal-position-on-distributing-warnings-to-people-other-than-the-operator), [T40](#t40-how-late-is-the-channel-measured), [T11](#t11-ask-whether-anyone-actually-wants-this), [T34](#t34-what-is-in-the-066-of-messages-without-a-tag), [T36](#t36-the-hand-labelled-sample-retargeted), [T46](#t46-declarations-phrased-without-a-declaration-word), [T47](#t47-two-threat-kinds-the-consumer-cannot-name)

**Tier 2, 20 open:** [T7](#t7-onboarding-probe-from-a-clean-clone), [T39](#t39-tolerated-poll-rate-under-continuous-operation), [T12](#t12-detect-changes-to-the-ukrainealarm-offer-contract), [T22](#t22-fail-the-build-when-a-document-cites-an-identifier-the-package-lacks), [T23](#t23-the-observability-sink-and-its-reader), [T24](#t24-keep-the-run-log-out-of-the-holdout), [T25](#t25-decide-where-the-daemon-lives), [T27](#t27-jitter-the-poll-interval-from-the-first-commit-of-m0), [T29](#t29-measure-disengagement-instead-of-assuming-it), [T31](#t31-katottg-as-a-versioned-file), [T33](#t33-alias-table-between-the-channel-and-the-register), [T35](#t35-turn-the-negative-result-into-a-measurement), [T37](#t37-the-pipeline-discards-areas-it-was-told-about), [T42](#t42-operating-intensity-of-the-jasionka-hub-measured-from-ads-b), [T43](#t43-raion-centroids-in-the-contract), [T44](#t44-the-consumer-has-no-kyiv-and-seven-raions-draw-no-marker), [T48](#t48-apple-critical-alerts-entitlement), [T51](#t51-geographic-layers-fetched-only-when-asked-for), [T52](#t52-polish-english-and-ukrainian), [T49](#t49-two-denominators-for-the-western-share-and-one-number-quoted-for-both)

**Tier 3, 11 open:** [T1](#t1-request-the-alertsinua-api-token), [T3](#t3-resolve-r2-which-currently-adds-nothing), [T4](#t4-executable-claim-behind-the-never-raise-parser-guarantee), [T5](#t5-rolling-feed-latency-drift-detection), [T41](#t41-prototype-the-push-interface-and-compare-it-against-polling), [T9](#t9-keep-the-coverage-floor-a-ratchet), [T10](#t10-find-a-history-source-deep-enough-to-calibrate-on), [T14](#t14-second-signal-type-for-the-drone-regime), [T26](#t26-reproduce-the-pid-namespace-hole-in-directorylock-then-fix-it), [T28](#t28-the-crossing-event-list-dated-and-sourced), [T53](#t53-full-width-map-fullscreen-theme-switch)

### By sprint

Sprint numbering follows `docs/MVP.md`. Tasks with no sprint are either outside the beta path or not yet placed on it.

| Sprint | Open tasks |
| --- | --- |
| **S7** | [T31](#t31-katottg-as-a-versioned-file), [T33](#t33-alias-table-between-the-channel-and-the-register), [T34](#t34-what-is-in-the-066-of-messages-without-a-tag) |
| **S8** | [T36](#t36-the-hand-labelled-sample-retargeted), [T37](#t37-the-pipeline-discards-areas-it-was-told-about), [T47](#t47-two-threat-kinds-the-consumer-cannot-name) |
| **S9** | [T39](#t39-tolerated-poll-rate-under-continuous-operation), [T40](#t40-how-late-is-the-channel-measured), [T23](#t23-the-observability-sink-and-its-reader), [T24](#t24-keep-the-run-log-out-of-the-holdout), [T25](#t25-decide-where-the-daemon-lives), [T27](#t27-jitter-the-poll-interval-from-the-first-commit-of-m0) |
| **S10** | [T11](#t11-ask-whether-anyone-actually-wants-this) |
| **S11** | [T7](#t7-onboarding-probe-from-a-clean-clone), [T22](#t22-fail-the-build-when-a-document-cites-an-identifier-the-package-lacks), [T29](#t29-measure-disengagement-instead-of-assuming-it) |
| **unassigned** | [T1](#t1-request-the-alertsinua-api-token), [T3](#t3-resolve-r2-which-currently-adds-nothing), [T4](#t4-executable-claim-behind-the-never-raise-parser-guarantee), [T5](#t5-rolling-feed-latency-drift-detection), [T6](#t6-legal-position-on-distributing-warnings-to-people-other-than-the-operator), [T41](#t41-prototype-the-push-interface-and-compare-it-against-polling), [T9](#t9-keep-the-coverage-floor-a-ratchet), [T10](#t10-find-a-history-source-deep-enough-to-calibrate-on), [T12](#t12-detect-changes-to-the-ukrainealarm-offer-contract), [T14](#t14-second-signal-type-for-the-drone-regime), [T26](#t26-reproduce-the-pid-namespace-hole-in-directorylock-then-fix-it), [T28](#t28-the-crossing-event-list-dated-and-sourced), [T35](#t35-turn-the-negative-result-into-a-measurement), [T42](#t42-operating-intensity-of-the-jasionka-hub-measured-from-ads-b), [T43](#t43-raion-centroids-in-the-contract), [T44](#t44-the-consumer-has-no-kyiv-and-seven-raions-draw-no-marker), [T46](#t46-declarations-phrased-without-a-declaration-word), [T48](#t48-apple-critical-alerts-entitlement), [T51](#t51-geographic-layers-fetched-only-when-asked-for), [T52](#t52-polish-english-and-ukrainian), [T53](#t53-full-width-map-fullscreen-theme-switch), [T49](#t49-two-denominators-for-the-western-share-and-one-number-quoted-for-both) |

<!-- index:end -->

Every item carries a status, a tier, a blocker type where one exists, and an
acceptance test, so that "done" is not a matter of opinion and neither is
"next".

Status: `ready` | `blocked-external` | `decision` | `debt` | `deferred` | `done`
Tier: `[tier 1]` | `[tier 2]` | `[tier 3]`, meaning below.

### Where the project is

**Sprint S8, declared partial and still open.** `docs/MVP.md` records it that
way: the report composes, the command runs and the contract ships, and the
exit criterion, a hand-checked sample of real messages with a stated error
rate (T36), is not met. Nothing is closed by having been worked on.

The last four releases were **not** sprint work and should not be counted as
progress towards beta. 0.19.0.0 to 0.19.4.0 were an audit and its
consequences: a contract joined on the wrong field, a counter measuring the
wrong unit, a test file claiming a verification it had not had, and the
threat-kind repair with its measurement. Useful, and orthogonal to S8.

**What closes S8:** T36 plus the by-hand distance spot check. Both need the
corpus, so both happen on the operator's machine.

## T1. Request the alerts.in.ua API token
Status: `blocked-external` (access) [tier 3]
**This is the only item that does not shrink by writing code.** It gates the real
backtest, which gates every audience in `docs/MVP.md`. It should have been the
first action of sprint 0 and precedes any further editor work.
**Acceptance:** a token in the local keychain and one successful authenticated
call recorded with its latency.

## T2. Split the decision into missile and drone regimes
Status: `done` (sprint 3, 0.2.0) [tier 3]
Sprint 2 finding: no single rule holds both the alarm rate and drone-night
recall.
**Acceptance met:** `mavo policy` reports both regimes; the missile regime passes
all three conditions against its allocated share. The drone regime does not, and
is demoted under D-009 rather than accommodated.

## T3. Resolve R2, which currently adds nothing
Status: `ready` (still open after sprint 3) [tier 3]
The conjunction's numbers are identical to R3, so the third conjunct is inert.
**Acceptance:** either R2 is redefined and the conjunction's contingency table
differs from R3's, or R2 is removed and the README stops describing it.

## T4. Executable claim behind the never-raise parser guarantee
Status: `ready` (narrowed after sprint 4) [tier 3]
Sprint 4 delivered the suite for the Telegram adapter (F17, harness A9); the
fixture source generates rather than parses, so hostile input does not apply to
it. What remains is the rule for adapters that do not exist yet.
**Acceptance:** every future `ThreatSource` that parses external input lands with
its hostile suite in the same release, and a lint or convention makes an adapter
without one visible. Malformed, truncated, oversized and hostile payloads; no
exception escapes; unparseable records counted rather than dropped.

## T5. Rolling feed-latency drift detection
Status: `ready` [tier 3]
Residual risk in the threat model: a subtly late source degrades lead time
without tripping anything.
**Acceptance:** a test where a source's latency doubles mid-history and the run
reports degradation.

## T6. Legal position on distributing warnings to people other than the operator
Status: `decision`, **due at the beginning of September**. Parallel track, and the only dated item left in the plan: it is answered by counsel or it is not, and no engineering time shortens it (`docs/MVP.md` section 7). [tier 1]
Does not shrink by writing code. Needs counsel, not a sprint.
**Acceptance:** a written position in `docs/DECISIONS.md` with a named basis.
*Restated 0.7.0.0.* The original title asked about a private circle, which is
the intermediate tier and not the destination. The question that actually gates
Audience D is distribution to recipients the operator does not know, and the
answer to the narrower question does not imply the broader one. Asking counsel
the smaller question would have produced a correct answer to the wrong
question, which is the more expensive kind of mistake here (F53).

## T7. Onboarding probe from a clean clone
Status: `ready`, **S11**. The visibility question that had been travelling with [tier 2]
this task is resolved separately in `docs/MVP.md` section 4 on 0.16.1.0:
repository visibility is not an Audience C criterion. What remains here is the
probe itself, which was always an engineering task.
**Acceptance:** a fresh clone into an empty directory, README followed from zero,
with the point of failure recorded. Not "it looks correct".


## T39. Tolerated poll rate under continuous operation
Status: `ready`, blocks M0 [tier 2], **S9**

**Where this came from.** Re-collecting the corpus after F68 meant 3,000 requests
in one burst, which raised the question of what rate the source tolerates. It
went through at 1.0 s once and 1.5 s once [measured, n=2], and neither
observation says anything about the daemon's profile: a few hundred requests a
day, indefinitely, from one address. Carrying a burst result over to continuous
operation would be an inference with no measurement under it.

**The goal is not to find the limit.** It is to check that the requirement sits
below it. The requirement is two minutes, from the window arithmetic: 20 messages
a page, and at an assumed 120 messages/hour under a massed strike the page is a
10-minute window, so two minutes keeps a factor of five. There is no reason to
probe faster than the requirement; probing for a ceiling is looking for a block.

**Instrumentation before escalation.** Every request logs status, response size,
message count, id bounds and response time. A week of that is the baseline
without which degradation cannot be recognised.

**Ladder:** 5 minutes for 72 hours, then 2 minutes for 72 hours. No lower.

**Stop conditions, any of which ends the escalation and returns to 5 minutes for
a week:** a 429, 403 or 503; a page with fewer than 20 messages not explained by
genuine channel silence; a step change in response time; any gap in id
contiguity. The last one matters most, because the dangerous failure has no
error code: a block is visible, a truncated 200 looks like an ordinary page.

**Worth checking first, because it may remove the problem instead of measuring
it:** whether the preview serves `ETag` or `Last-Modified`. A conditional
request ending in 304 costs a fraction of a full response, which is the only
lever that improves freshness and politeness at once.

**The measurement is tied to the address it was taken from (D-018).** Both
successful backfill runs went out over a residential connection, and data-centre
ranges are treated differently by most anti-bot layers. Moving the collector to a
cloud host invalidates them: the ladder restarts from five minutes on the new
address rather than continuing.

**Acceptance:** a daily request budget recorded in `docs/MANUAL.md`, a request
counter in the run log, and the ladder's outcome recorded as a measurement with
its date **and the address class it was taken from** - including if the outcome
is "two minutes caused degradation", in which case the requirement and the
window arithmetic come back to the table rather than the interval quietly
moving.


## T40. How late is the channel, measured
Status: `ready`, blocks T41 and any latency claim [tier 1], **S9**

**Where this came from.** The observation that during a strike the unit that
matters is seconds, not minutes. That is correct, and it reframes the polling
question rather than answering it: poll-interval latency is only worth arguing
about relative to the latency already spent upstream, which nobody has measured.
`docs/METHODOLOGY.md` lists the channel's latency relative to the APIs as
unknown, and the 30 July episode ran **six minutes** from detection at 03:40 to
loss of radar contact at 03:46 `[reported]` without anyone knowing where in
those six minutes the channel speaks. The figure was thirteen in this entry
until 2026-08-10 and was unsourced; six is less room, which makes the
measurement more worth doing rather than less.

**What to measure.** For every message: the post's own timestamp against the
moment it was received. A week gives a distribution rather than an anecdote.
This is cheap, needs no new interface, and can run beside the existing reader.

**Why it gates the rest.** If the upstream costs two minutes, then fighting for
our sixty seconds is optimising a small term beside a large one, and the
honest report says so. If the upstream is seconds, the transport choice in T41
becomes the dominant term and is worth a sprint.

**Acceptance:** median, p90 and max of post-timestamp to receipt, over at least
a week, recorded in `docs/CHANNEL.md` with the collection dates and the
interval used.


## T41. Prototype the push interface, and compare it against polling
Status: `ready`, after T40 [tier 3]

**Where this came from.** Same place as T40. Polling is the wrong instrument for
seconds however fast it runs: at a two-minute interval the mechanism itself adds
60 s on average and 120 s at worst, and the only way to shrink that is more
requests at a surface that was never meant for them.

**What changes with MTProto.** A listening client should receive a post within
seconds of publication over one long-lived connection [inference from the
protocol's design, unmeasured on this channel - measuring it is this task's
acceptance, not its premise]: no interval, no request budget, no question about
tolerated rate. T39 stops being a measurement and becomes moot. Whether a
listener is *the earliest* publicly reachable point depends on the channel
actually being the upstream of both APIs, which D-010 deliberately does not
claim - it records the three surfaces as correlated and labels the upstream
topology an inference (METHODOLOGY, provenance table). What holds either way:
no publicly reachable point is known to be earlier, and this prototype cannot
settle that ranking, only its own receipt times.

**What it costs, stated up front.** MTProto needs an account and an `api_id`, so
an identity linked to the operator enters the threat model and a secret enters
`docs/DEPLOYMENT.md`, where there is none today. The failure mode changes shape
too: a dropped connection is not an absence of events but blindness, and it must
render as UNKNOWN behind a local timeout rather than as quiet.

**Acceptance:** a listener running beside the existing reader over the same
window, with both streams stored; a comparison of receipt times per post id; and
a decision recorded either way about whether polling stays as the fallback path.
The comparison is the deliverable, not the listener.


## T8a. Is there any ingestible Polish source, measured against FEED-SPEC
Status: `ready` (own action, no permission needed) [tier 2]

**This replaces T8, and why it was replaced is F95.** The old entry justified
itself with "sprint 6 assumes a Polish feed exists to switch to". Sprint 6
closed long ago; `shipped_sprints` reaches 9. The task outlived its reason and
kept the reason, and its acceptance clause still asked "what that does to
sprint 6", which is a question with no addressee. It also carried
`blocked-external (access)`, which was wrong: nothing here needs anyone's
permission, and labelling an unstarted measurement as externally blocked is how
it stayed unstarted for six sprints.

**What is actually being asked.** Not "does a Polish channel exist" - RCB
messages and sirens exist and reach millions. The question is whether any
Polish source can be *consumed*, and `docs/FEED-SPEC.md` section 3 already
defines what that means. The old acceptance said "one working read", which does
not say a read of what, with what geography, at what latency. That looseness is
why a positive result would have been unfalsifiable.

**Measured against the five properties, one row each, verdict per source.**
The candidates, with what the project currently believes and its provenance:

| Source | Believed | Provenance |
| --- | --- | --- |
| RCB alert (SMS) | free text to a phone, no stream | `[reported]`, FEED-SPEC section 2 |
| RCB's public web and social postings | unexamined | **nothing** - this is the gap |
| RSO application | partially machine readable, not an open stream | `[assumption, unmeasured]` |
| NOTAM | machine readable | `[assumption, unmeasured]` - the old T8 asserted this flatly and nothing measured it |
| MSWiA application | not released | `[reported]` |

**The two rows with no provenance at all are the work.** RSO and NOTAM were
asserted machine-readable in a one-line task nobody revisited; RCB's public
postings were never looked at, which is the odd part, because scraping a
public web preview is exactly the technique that produced this project's entire
Ukrainian corpus.

**Acceptance, and it closes in either direction.** For each candidate, a row in
a written finding stating its verdict on each of FEED-SPEC's five properties -
public and unauthenticated, areas by register code, transitions in both
directions with timestamps, versioned schema, heartbeat - with the evidence
that produced the verdict. Plus, for any source that scores at all:

- **one real read**, committed as a fixture, with the raw response kept
- **an area resolved to a TERYT code**, or an explicit statement that only
  prose is available and what a name matcher would cost, which is F23's
  failure mode arriving on the Polish side
- **latency against something independent**, using T40's method: the source's
  own timestamp against the moment of receipt, over a week, reported as a
  distribution rather than a best case. A single sample is an anecdote
- **the absence of a heartbeat stated explicitly** where there is none, because
  a source that goes quiet indistinguishably from a quiet sky is the failure
  this project refuses everywhere

**A negative result closes this task and is worth as much as a positive one.**
"No Polish source satisfies more than one of the five, and here is the evidence
per source" is a publishable finding, it is the empirical backing FEED-SPEC
currently argues without, and it is the strongest possible answer to anyone
who says the specification is asking for something already available.

**What this task must not do.** It must not decide whether Poland enters the
product. That is T8b, it depends on T6, and mixing the two is what let the
original entry sit in tier 3 looking like a research errand.

## T8b. Does Poland enter the product's scope
Status: `decision`, blocked by T8a and T6 [tier 2]

Separated from T8a on 2026-08-11 because one entry was carrying a measurement
and a product decision, and the measurement was hostage to the decision nobody
was making.

**The decision.** Whether MAVO reports the Polish side as well as the Ukrainian
one. Today it does not: D-015 fixes the thesis on reporting the picture across
the border, `docs/MVP.md` places no Polish areas in any sprint, and the site's
geometry asset carries 25 Ukrainian oblasts and no Polish voivodeship.

**What makes this a decision rather than a backlog item.**

- **It changes what the product is to a reader.** A page showing western
  Ukrainian oblasts and a distance to the border is a situational instrument
  for someone in Poland. A page showing Polish alerts is a warning service for
  the country the reader is standing in, and the bar it will be held to is not
  the same bar.
- **T6 stops being a formality.** Republishing state-issued Polish alerts under
  a private brand is the exact case where "this is not a state service" has to
  be more than a line in a header. Nothing here should ship before T6 has an
  answer, and T6 has no date.
- **It doubles the source surface** for a project whose single greatest stated
  weakness is depending on one source.

**Acceptance:** an entry in `docs/DECISIONS.md` stating whether Poland is in
scope, with the reopen condition, and - if yes - the corresponding sprint
entries in `docs/MVP.md` and a geometry decision for the site. If no, the same
entry records why, so the question stops being reopened by enthusiasm.

**Not blocked on anything external.** Both blockers are the project's own.

## T9. Keep the coverage floor a ratchet
Status: `debt` [tier 3]
The floor is set at 95, three points below the 98.3 measured in sprint 2. It
rises when a sprint genuinely raises coverage and never as a target, because a
target invites tests written for the number.
**Acceptance:** any commit that raises measured coverage by more than five points
raises the floor in the same commit.

## T10. Find a history source deep enough to calibrate on
Status: `blocked-external` (access) [tier 3]
Neither Ukrainian API carries multi-year history: alerts.in.ua exposes
`month_ago`, ukrainealarm returns the last 25 alerts per region. The real-data
backtest assumed several years and roughly a dozen positive events.
**Acceptance:** either a source covering the full period, or a written decision
in `docs/DECISIONS.md` accepting calibration on one month with the resulting
confidence intervals stated.

## T11. Ask whether anyone actually wants this
Status: `ready`, **before S10**. No longer a budget calibration (D-014); it is now the question of whether recipients exist at all, which Audience B is gated on. [tier 1], **S10**
No recipient has been identified. `docs/MVP.md` names a small trusted group and
nobody in it has been asked. Until then the alarm threshold is calibrated against
a hypothetical tolerance.
**Acceptance:** two conversations, recorded: would they want this, and at what
firing rate would they stop reading it. The second answer replaces the assumed
two per week.

## T12. Detect changes to the ukrainealarm offer contract
Status: `ready` [tier 2]
The contract changes unilaterally by being reposted, with no notification
obligation. The only defence is our own check.
**Acceptance:** the collector hashes `contract.pdf` on each run and logs a change.

## T13. Record the revocability of both Ukrainian feeds
Status: `done` (0.3.2.0) [tier 3]
**Acceptance met:** MT9 and MT10 in `docs/THREAT-MODEL.md`, D-010 in
`docs/DECISIONS.md` with the conditions that would reopen the dependency
question. Found open during the 0.3.2.0 audit because MT9 cited D-010 before it
existed (F33).

## T14. Second signal type for the drone regime
Status: `deferred` (D-015). Was a prerequisite for a drone alarm tier. Under a reporting thesis ADS-B is enrichment: valuable, not blocking, and outside the five sprints to beta. [tier 3]
Promoted from enrichment to prerequisite by the sprint 3 finding. Alert state
alone cannot discriminate within drone nights, so the drone tier stays silent
until another channel exists.
**Acceptance:** ADS-B activity over eastern Poland ingested as a `ThreatSource`,
and a drone-regime rule that clears its allocated share on the adversarial
history without lowering the recall floor.

## T15. Raion and hromada gazetteer
Status: **largely met at 0.10.0.0**, by a route nobody planned. The channel tags 99.34% of messages with the area and unit type, so the gazetteer is a 127-row lookup rather than a vocabulary to search (`docs/CHANNEL.md`). What remains is correctness on the message the tag sits in, which is S7's hand-labelled sample. Original text: [tier 3]
Status: `ready`, **S7, core**. Promoted from support to product by D-015: a report that cannot name the rajon is a relay. Superseded in method by T31, which supplies the register this task consumes.
F24. The channel names raions and hromadas; nothing in a message identifies the
oblast. Without a mapping, the border-oblast rules that the entire thesis rests
on have no input.
**Acceptance:** every area name appearing in a week of channel content resolves
to an oblast, or is reported as unresolved. Unresolved is never silently skipped.

## T16. Means of attack as its own message class
Status: `done` (sprint 9, 0.14.0.0) [tier 3]
F25. `kind` is modelled as an attribute of an alert; the channel emits it as a
separate message tied to a hromada, with its own lifetime.
**Acceptance met:** a threat-type message produces its own `KindEvent`, stored in
its own table, and `mavo/kinds.py` joins it to alerts by oblast and time window.
The regime rules are unchanged: the join happens before them, so they still read
`event.kind` and know nothing about how it got there.

*Why this was the blocker and not a tidy-up.* Measured on the twenty real
messages held as fixtures: 15 carry an alert state, 4 carry a kind marker, and
**none carry both**. Every live alert therefore had `kind = UNKNOWN`, every
regime rule tests for MISSILE or DRONE, and the regime split this project's
central finding rests on could not fire outside the fixture generator. The same
class as F65, one field over. Logged as F67.

*Open behind it, and it is a measurement rather than code:* the join is only
worth its complexity if enough alerts receive a regime. `tools/kind_coverage.py`
answers that from the corpus, which is not in the tree. Until it is run, the
six-hour `DEFAULT_KIND_TTL` is an assumption carrying a label, and whether the
regime split describes the world or only the generator is still the open
question `docs/METHODOLOGY.md` marks as speculation.


## T17. The fourth state: a partial all-clear
Status: `done` (sprint 5, 0.4.0.0) [tier 3]
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
Status: `done` (sprint 5, 0.4.0.0) [tier 3]
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
Status: `done` (0.5.5.0 retrieval, recorded at 0.6.0.0) [tier 3]
**Acceptance met:** post ids 260841 to 321520, 60,680 posts over 3,034 pages
spanning 118 days, contiguous with no gaps, exit code 0; id range, span and the
design/holdout boundary (D-012a) recorded in `STATUS.json`, boundary computed
before any message content was read. This entry was still `ready` while
`STATUS.json` already carried the corpus block - the file that holds rules
lagged the file that holds facts by one release, which is the drift class
docs-audit exists for, in the one file it does not read.
Original text:
Status: `ready`, **no longer time-boxed**
`mavo backfill` reaches history rather than waiting for it (0.5.0.0). The window
constraint that shaped D-011 and the sprint 5 scope decision did not exist (F44).
**Acceptance:** a contiguous corpus covering at least the last 90 days, exit code
0 from `mavo backfill`, its id range and time span recorded in `STATUS.json`, and
the design/holdout boundary computed and written down per D-012 before any
message content is read.

## T21. Measure the tolerated request rate
Status: `done` (0.5.1.0), with a named limit [tier 3]
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
Status: **done, 0.16.1.0.** Account created 2026-08-10, API client activated, [tier 3]
credentials stored outside the tree.

**Acceptance met [measured, 2026-08-10]:** OAuth2 client-credentials token in
276 ms, one authenticated `/states/all` read over the western box (latitude 48
to 52, longitude 22 to 27) in 275 ms, returning 10 state vectors.
`X-Rate-Limit-Remaining` moved from 4000 to 3999, so the box costs **one credit
per call** on the Standard allowance: a ceiling of one call every 21.6 s, and a
30 to 45 s poll with margin for retries. That figure is now a measurement
rather than a reading of the published credit tiers.

**The assumption this task carried was false, and the correction matters more
than the task.** T20 was recorded as gating T14 and therefore any drone-tier
alarm (D-009). ADS-B cannot see the drone tier. Shahed-type munitions and
missiles carry no transponder; ADS-B shows only what chooses to be seen, and
Ukrainian civil airspace is closed. The claim "OpenSky is a prerequisite for
the drone tier" was `[assumption, unmeasured]` from the day it was written and
is **false**. The drone tier has no source in this feed and never had one.
Recorded here rather than quietly rewritten, because a backlog that edits its
own false premises out of existence stops being evidence about how the work is
done.

**What the feed can carry instead**, in descending order of how well it is
supported: an aggregate count of transmitting military aircraft (D-019,
reported and never scored); a correlation between ISR or tanker presence over
south-eastern Poland and alert nights on the Ukrainian side [hypothesis,
unmeasured, no lift computed]; and the absence of civilian traffic as a lagging
confirmation. None of the three is a drone-tier signal.

**Follow-on, open:** sampler run over at least three nights, one with a
western-Ukraine alert, per D-019's preconditions. The 10 August snapshot showed
all 10 vectors west of longitude 23.5, that is on the Polish side, with nothing
over the Ukrainian half of the box - one snapshot, and therefore an observation
rather than a base rate.


## T22. Fail the build when a document cites an identifier the package lacks
Status: `ready`, **S11** [tier 2]
F55: `docs/COMPUTATION.md` cited a constant that does not exist, in the document
whose subject is that figures come from measurement. The audits check cited test
names and pinned counts; nothing checks the rest of the backticked identifiers.
**Acceptance:** `tools/docs_audit.py` extracts backtick-quoted names matching an
identifier pattern from `docs/*.md` and the README, and fails on any that appear
in no package source, with an explicit allow-list for names that are deliberately
hypothetical. Verified red by citing a fabricated symbol in a scratch copy.


## T23. The observability sink and its reader
Status: `ready`, **S9** [tier 2]
Blocks nothing today and blocks everything at M0: shadow mode's deliverable is a
record of decisions that were never sent, so the log is the product rather than a
diagnostic. Designed in `docs/OBSERVABILITY.md` with acceptance written before
the code.
**Acceptance:** the seven criteria in that document's section 9, each as a test.
The two that are not merely plumbing: identical JSONL under `-q` and `-vv`, and
a rendering that prints `unknown` where a stage could not measure, verified by a
fixture whose parse report has no baseline.

## T24. Keep the run log out of the holdout
Status: `ready`, **S9** [tier 2]
The design and holdout split was frozen before any message content was read
(D-012a). A run log echoing message bodies spends that split without anyone
deciding to spend it.
**Acceptance:** a hostile fixture carrying a recognisable token in every message
body produces no occurrence of that token in the sink under default settings,
and the debug switch that lifts this writes its own line into the record.


## T25. Decide where the daemon lives
Status: `decision`, **S9** [tier 2]
`docs/MOBILE.md` assumes an operator-controlled always-on host and does not say
which. A laptop that sleeps is not one: shadow mode on a sleeping machine writes
a record whose holes look like quiet nights, which is the defect this project
exists to refuse, arriving through the scheduler. The answer changes what M0
costs by more than any other open item: a Mac needs a signed wrapper, a
`KeepAlive` plist and a TCC-safe data directory, while a Linux host gets the
same attribution from a named systemd unit for free.
**Acceptance:** a decision entry in `docs/DECISIONS.md` naming the host and the
supervision mechanism, with the reopen condition stated.

## T26. Reproduce the pid-namespace hole in DirectoryLock, then fix it
Status: `ready` [tier 3]
`DirectoryLock._alive` calls `os.kill(pid, 0)`. Pids are per namespace, so two
containers on one data volume can both hold the lock while each believes it owns
it, disabling the control that keeps the request rate against the upstream from
doubling. Reasoned from the code, not observed (`docs/DEPLOYMENT.md` section 9).
**Acceptance:** two containers on one mounted volume, both attempting the lock,
with the outcome recorded either way. If it reproduces: a host identifier beside
the pid or `flock` on a descriptor, a regression verified red against the
current implementation, and a threat-model row. If it does not reproduce, the
negative result is recorded in `docs/METHODOLOGY.md` and this entry closes.

## T27. Jitter the poll interval from the first commit of M0
Status: `ready`, **S9** [tier 2]
A fixed 60-second period is both a beacon profile to a sensor and a perfectly
regular load on an upstream with which there is no agreement. Ten to twenty
percent jitter addresses both and costs one line. It goes in first because
adding it later invalidates every interval measurement taken before it, and
those measurements are the evidence that would justify tightening the poll.
**Acceptance:** the interval is drawn per cycle, the draw is recorded in the run
log, and the recorded distribution over 72 hours matches the configured range.


## T28. The crossing event list, dated and sourced
Status: `deferred` (D-015). Was blocking while crossings were the target [tier 3]
variable; the tool reports rather than predicts, so a scored recall against a
crossing list is no longer on the critical path. The list stays worth building
for retrospective validation of any future alarm class, and it stops holding
anything up.
`tools/threshold_sweep.py` measures what a threshold costs in alarms per week
and is silent on what it catches, because nothing in this repository knows which
nights carried a border crossing. The event list has lived in prose ("roughly a
dozen over four years") since the beginning, which is enough to reason about
sample size and not enough to score a rule.
**Acceptance:** a committed file, one row per crossing, each with a date, a
regime, and a named public source, plus an explicit statement of the coverage it
claims and the period it covers. Rows whose regime is uncertain are marked
uncertain rather than assigned, because a positive class of twelve cannot absorb
a guess. Until this exists, no threshold sweep can produce a recall and no gate
verdict on real data is possible.


## T29. Measure disengagement instead of assuming it
Status: `ready`, **S11** [tier 2]
D-014 removed the alarm budget because the number behind it was assumed. The
honest replacement is not a better guess but a measurement: mute rate,
unsubscribe rate, and time to first mute, recorded as first-class metrics beside
recall and lead time from the first week the channel exists.
**Acceptance:** the run log carries per-recipient delivery and disengagement
events, and a report states the rate at which recipients stop listening against
the frequency at which they were notified. If the rate turns out to be sharply
frequency-dependent, a rate condition returns to the gate with a measured
number attached, and D-014 is reopened on its own stated terms.


## T31. KATOTTG as a versioned file
Status: `ready`, **S7**. *Renamed 0.9.2.0: the register is КАТОТТГ, KATOTTG. The [tier 2]
earlier spelling KATOTTH followed one English transliteration and did not match
what any source publishes.*

**Candidate located and measured** [measured, 2026-08-09, by retrieving it]:
`kaminarifox/katottg-json` carries the codifier as JSON, `orderDate` 2024-01-19,
31,751 items, with categories O oblast, P raion, H hromada, M city, C village
and others. Restricted to the eight western oblasts it yields 36 raions and 484
hromadas. Names are the bare adjectival forms the channel would inflect:
`Володимирський`, `Ковельський`, `Затурцівська`.

**Blocking issue, and it is not technical: the repository declares no licence.**
No licence means all rights reserved, so it cannot be vendored into an
Apache-2.0 tree, whatever its contents. The underlying codifier is a Ukrainian
government publication and open, so the fix is to take it from the official
publication and use this repository only to cross-check the parse.
**Acceptance:** the register in the tree with its official source URL, version
and retrieval date recorded, a licence statement that survives reading, a loader
with no runtime dependency, and the hit rate from `tools/register_probe.py`
recorded as a number.
D-016. The Ukrainian state administrative register, successor to KOATUU, gives
hromada, rajon and oblast with stable codes, which is the mapping F23 showed to
be missing: the shipped table keyed on oblasts while the channel emits the
smaller units.
**Acceptance:** the register in the repository as data with its source, version
and retrieval date recorded, a loader with no runtime dependency, and a measured
hit rate of the register's names against the design window, reported as a number
rather than an impression. A hit rate below what the channel actually emits is a
finding about the register and is recorded as one.

## T32. Distance from each area to the Polish border, precomputed
Status: `done with a stated deviation` (0.13.0.0) [tier 3]
D-016. Distance is the field that turns an alert into a report a person can use,
and it must be a stored column rather than a runtime call: no API key in the
warning path, no rate limit where latency is the product, and no third party
learning which rajons a Polish user asks about at three in the morning.

*Delivered 0.13.0.0.* `data/reference/border_km.csv`, 127 of 127 areas, generated
by `tools/border_distance.py` from the KATOTTG-to-OSM register join published by
`ua-geo` and a vendored extract of the Polish outline. Method, both source
checksums and the geometry version are in the file header. Four hand-verified
spot checks run in the generator and again in the suite.

**The deviation:** the criterion asked for one scalar and this is an interval.
The scalar is unavailable and would be wrong where it matters most: a centre
point puts Самбірський район 14.2 km from a border it actually touches. The
interval bounds the true nearest-edge distance using a disc of equal area, and
`AreaRef.border_interval` renders `0-46 km`. Permitted under the rule that a
criterion may move only when the replacement is harder than the original.

**What would close it properly:** polygons keyed by KATOTTG. Neither
geoBoundaries (git-lfs, objects served off-domain) nor Overpass is reachable
from the environment this was built in. With polygons, the same tool computes a
true minimum by swapping the point for a vertex list, and the interval collapses
to the scalar the criterion asked for.


## T33. Alias table between the channel and the register
Status: `ready`, **S7** [tier 2]
The channel tags `#ВолодимирВолинський_район`; the register lists
`Володимирський` after a renaming. Found by accident while joining, which means
nothing has systematically compared the two vocabularies and there may be more.
The general shape of the problem: the register and the channel evolve
independently, and either can change a name first (`docs/CHANNEL.md`).
*Update 0.11.0.0:* the one ambiguous tag is resolved. `Покровська_територіальна_громада`
matched four hromadas by name; in the corpus it appears beside
`Нікопольський район` and `Дніпропетровська область`, which identifies the
Pokrovska hromada of Dnipropetrovsk oblast. Context settles what a name cannot,
and the map can go to 127 of 127 once the row is written with that reason.

**Acceptance:** every one of the 127 tags either resolves directly or carries an
alias with the reason recorded, plus a check that fails when a tag appears in the
corpus that the map does not know. A new tag is a finding, not a fallback.

## T34. What is in the 0.66% of messages without a tag
Status: `ready`, **S7** [tier 1]
321 of 48,540 design-window messages carry no `#Name_unit` tag and nothing says
what they are. They may be administrative posts, or they may be exactly the
messages that matter.
**Acceptance:** a hand-read sample of them, classified, with the finding
recorded either way. If any are alerting messages, the tag parse needs a
documented fallback and the 99.34% figure needs a caveat beside it wherever it
appears.


## T35. Turn the negative result into a measurement
Status: `ready` [tier 2]
The design window's four western-wide alert nights show no reported Polish
airspace violation, but the source is press coverage, and a single drone downed
without debris may never reach national media. Absence of evidence, not evidence
of absence, and the log says so.
**Acceptance:** the operational command's own published posts for 2026-04-29,
2026-05-28, 2026-05-29 and 2026-06-20 read and recorded, with the finding
entered either way. A confirmed quiet night on all four is a measurement; a
missed incursion on any of them is a more interesting one.


## T36. The hand-labelled sample, retargeted
Status: `ready`, **no longer blocking S7**. The sprint closed on an exhaustive [tier 1], **S8**
consistency check instead (`docs/METHODOLOGY.md`, sprint 7 closed): 38,520 of
38,521 comparable messages agree between tag and prose, 99.997%. What that check
cannot see is the 9,701 messages carrying a tag and no prose area, 20% of the
corpus, and the hand sample is now the only instrument for those.
**Acceptance:** at least 50 messages drawn from the tags-without-prose
population alone, read by hand, with the error rate and its interval recorded.
Sampling from the population where an exhaustive check already exists would
measure the same thing twice and worse.
Original text:
Sprint 7 measured that the channel tags 99.34% of messages and that 126 of 127
tags resolve to a register code. Neither says the tag on a message describes the
area that message is about. No automated probe can assert that, which is why the
criterion was written as a hand-labelled sample before the sprint began.
**The instrument exists** (`tools/label_sample.py`, 0.10.3.0): `draw` writes a
seeded, fingerprinted sample in two strata, `score` reads it back and reports the
error rate with a Wilson interval and refuses a partially filled file. What
remains is the reading, which is a person and cannot be delegated to a probe.

**Sharpened again at 0.21.3.0, and the instrument would not have met the
acceptance before this.** `draw` sampled proportionally from everything that
resolved. The west is 3.5% of tag occurrences, so a fifty-row draw contained
**one or two western messages** on average, and the acceptance asks for a
figure about the areas near the border. A sample can be the right size, drawn
with a recorded seed and a fingerprint, and still answer a question nobody
asked.

`draw` now uses three strata: `western`, `front_line`, `unknown_tag`. Half of
the resolved rows are western by construction, and when the corpus holds fewer
western messages than asked for, it says so rather than quietly returning a
short stratum.

**The consequence is stated in both directions, because oversampling buys one
thing and costs another.** The resulting rate is about the areas this product
reports on, which is what S8 asks. It is **not** an error rate for the
channel's traffic, and `score` prints no combined figure: pooling an
oversampled stratum with a proportional one produces an average over weights
the sampler chose, which is neither number.

A file drawn before this change is refused by `score` rather than read, because
its `resolved` stratum is a mixture nobody chose.

**Verified end to end on a synthetic corpus** (draw, fill, score) before being
handed over, so the first real run is a measurement rather than a debugging
session.

**Sharpened at 0.20.0.0, after the instrument grew and a first sample was
taken.** `tools/label_sample.py` now draws three verdict columns, `area_ok`,
`kind_ok` and `distance_ok`, because S8 asks whether the report is right in
area, means and distance, and `score` reports a **whole-row** rate beside the
three: a reader sees one line, so a row is wrong if any of the three is.

A first sample exists and does not count: the twenty real messages in the tree,
0 errors on all three dimensions, Wilson [0%, 16.1%]. All twenty are eastern,
from twenty-six minutes of one afternoon. The intervals it judged are 700 to
1,000 km wide, where an error of tens of kilometres is invisible; the intervals
that matter reach zero at the border and none was tested.

**Acceptance, restated so it cannot be met by accident:** fifty rows from the
design window with western areas represented, all three columns filled one row
at a time, scored with the whole-row rate and its Wilson interval, and the
figure written into `docs/METHODOLOGY.md` beside the sample's fingerprint. A
redraw is allowed and visible; a redraw until the number improves is not a
measurement.

**Acceptance:** at least 50 design-window messages read by hand, each with the
resolved area recorded as correct or not, and the error rate stated as a number
with its interval, its seed and its fingerprint, recorded in
`docs/METHODOLOGY.md`.
An error rate above a few percent is a finding about the channel, not about the
map, and it is recorded either way. Until this exists S7 stays open and
`STATUS.json` does not claim otherwise in prose.


## T37. The pipeline discards areas it was told about
Status: `ready`, **S8** [tier 2]
Two losses, both currently invisible, found by the sprint 7 consistency check.
A message naming several areas yields one event, because `ThreatEvent` carries
one area: 13.3% of comparable messages name two to eight. And an all-clear can
carry a continuation list, areas where the alert is *still running*: 5.2% of
comparable messages, 4,064 area mentions in the design window, none of them
recorded anywhere.
The second is the worse one. A report whose stated product is completeness is
dropping the half of the message that says *still dangerous there*.
**Acceptance:** every area named by a message reaches the store with its own
state, continuation areas included and distinguishable from the subject of the
all-clear; the two rows in `docs/DATA-FLOW.md` move from invisible to visible;
and a regression asserts that a message with a continuation list produces more
than one event.


## T42. Operating intensity of the Jasionka hub, measured from ADS-B
Status: `ready`, follows T20. Not on the beta critical path, and not in any [tier 2]
score.

**What this is.** Rzeszow-Jasionka is the logistics hub through which support
for Ukraine moves. During a war, how hard that hub is working is part of the
situational picture a reader near the border is entitled to see, and it is
observable from public ADS-B: aircraft that broadcast their own position are
counted, and nothing else is. Reported alongside the alert picture, never
weighed into any assessment (D-019).

**Why it is worth measuring rather than assuming.** Nobody involved has a base
rate for it. How many military aircraft transmit over that box on an ordinary
night, how the count varies by hour, and whether it moves at all against alert
nights on the Ukrainian side are four separate unknowns, and the field cannot
be published before the first two are answered. The 10 August snapshot returned
ten vectors, all of them west of longitude 23.5 and two of them military on the
ground at Jasionka [measured, n=1], which is an observation and not a base rate.

**Semantics, load-bearing and not negotiable.** The count is a lower bound on
*transmitting* aircraft. A high number means something. A low number means
nothing: transponder silence plausibly correlates with exactly the situations a
reader would most want to know about [inference from operational practice,
unmeasured]. Any rendering that lets zero read as calm rebuilds this project's
founding defect in a new place, so the framing travels in the field itself.

**Acceptance:**
1. Sampler run over at least three nights, one of them with a western-Ukraine
   alert, raw snapshots retained outside the tree.
2. Base rate and hourly variance of the transmitting-military count, stated
   with n and the window, plus the frequency of a null response from the API.
3. A decision recorded either way on whether the count is published: it ships
   with its lower-bound framing, or it is dropped for carrying no signal.
   D-019 already names the threshold under which dropping is the answer.
4. If it ships, a `state.json` schema version bump, because adding a field
   silently is what `docs/FEED-SPEC.md` section 3 tells other people not to do.

**Out of scope, stated so it does not creep in.** No aircraft identities, no
positions, no callsigns on any public surface. No tracking of individual
airframes over time. No inference about what any specific flight is carrying.
The published artefact is one integer and its framing.

**The secondary hypothesis, kept separate.** Whether ISR or tanker presence
over south-eastern Poland correlates with alert nights on the Ukrainian side is
a different question with a different acceptance, and it has no lift computed
[hypothesis, unmeasured]. Recorded here so it is not quietly folded into the
count above, which would be one measurement carrying two claims.


## T43. Raion centroids in the contract
Status: `ready`, follows F74. Small, and it changes what the map can say. [tier 2]

Every marker on the consumer's map is currently anchored to a whole oblast,
with an uncertainty ellipse the size of that oblast's bounding box, because
the contract carries no coordinates. Two raions under alert in one oblast
render as one marker. That is honest, and it throws away resolution this
project already has: areas resolve to KATOTTG codes, and `border_km.csv` was
computed from registered centre points, so the coordinates exist upstream of
a column that does not carry them.

**Acceptance:** a `lat`/`lon` pair per area in `data/reference/`, provenance
recorded with the source and its licence the way `border_km.csv` records the
register pin; both published in the contract when known and **absent rather
than approximated** when not; a schema bump; and a check that every published
coordinate falls inside the area it claims, verified the way the consumer
verifies its own anchors by point-in-polygon.

**What this does not license.** A finer marker is not a finer claim. The feed
still reports administrative states, not objects, and a raion-anchored marker
is "somewhere in this raion", which is why the uncertainty field must shrink
with the anchor rather than disappear.


## T44. The consumer has no `kyiv`, and seven raions draw no marker
Status: `ready`, small, and it belongs to the site rather than here. [tier 2]

MAVO's register carries one `kyiv`. The consumer's geometry splits `kyiv-city`
from `kyiv-oblast`, a real administrative distinction this project does not
make. Measured against `mavo-site` 1.2.0.0: no `kyiv` in the geometry and no
mapping anywhere in the package, so the seven Kyiv-oblast raions in
`data/reference/tag_map.csv` land in `unplaceable` and draw nothing.

**Where the fix belongs.** The consumer, because it is the consumer's
geometry that makes the distinction. A producer that starts emitting
`kyiv-oblast` has learned its consumer's vocabulary and taken back the
decoupling D-020 bought.

**Acceptance:** one line in the consumer mapping `kyiv` onto `kyiv-oblast`,
with a test, and a note in this repository's contract documentation naming the
slug pair. Until then, the gap is real and is stated in `docs/WEBAPP.md`
rather than left for a reader to discover from an empty patch of map.

**Why it is here at all.** Because the entry recording F74 originally asserted
that the consumer already did this, in the present tense, without anybody
having looked. That sentence is corrected in the log; this task is what
replaces it.


## T45. Measure the kind tables again, against the same corpus
Status: **done, 2026-08-10.** Result recorded in `docs/METHODOLOGY.md` under [tier 3]
"Threat-kind coverage after the F71 repair". Coverage 0.128 to 0.196,
`join_coverage` 0.104 to 0.170, MISSILE 25 to 242, unparsed down 56%. The
near-miss review produced three findings and one avoided inversion, all in
that section. The acceptance below stands as the record of what was asked.

The repair in 0.19.3.0 is derived from four message forms quoted in F71 plus
one found while testing it. That is evidence the parser now accepts forms it
demonstrably refused, and evidence for nothing else. **How much of the corpus
it recovers is unmeasured**, and the entries carry `[assumption, unmeasured]`
until this runs.

**Acceptance:** `tools/kind_coverage.py --raw data/raw --sample 30` on the same
corpus that produced the baseline, reported beside these figures:

| Quantity | Baseline, 2026-08-10 |
| --- | --- |
| Declarations | 2,392 |
| Lifts | 993 |
| Still unparsed | 4,447 |
| MISSILE / DRONE / GLIDE_BOMB | 25 / 1,492 / 1,868 |
| Coverage at 1 h TTL | 0.128 |
| `join_coverage` at 1 h TTL | 0.104 |
| UNKNOWN after the join | 36,697 of 42,910 |

Plus two things the numbers alone will not say:

1. **The near-miss pile, reviewed by hand.** A coverage figure that rises
   because a marker became over-broad looks identical to one that rises
   because a marker became correct. `небезпека` measured zero hits and is a
   candidate for removal; `загроза` is short and its false-hit rate is the
   thing this review exists to find.
2. **Whether artillery is now a large share of declarations.** If it is, the
   reporting tier gains a category the alarm rules deliberately never see, and
   `docs/WEBAPP.md` needs a legend entry rather than a silent fifth glyph.

**What would count as failure.** Coverage rising while the hand-reviewed
sample shows the new hits are wrong. In that case the entries are reverted
rather than tuned, because a table tuned against a number it also produces is
the fitting-to-noise failure this project was founded on refusing.


## T46. Declarations phrased without a declaration word
Status: `ready`, and **blocked on nothing except its own measurement**. Do not [tier 1]
start it without reading the inversion note first.

Two patterns remain in the near-miss pile after 0.19.4.0, both measured:

1. `Атака ударних БПЛА над містом` - a declaration whose verb is `атака` in a
   form the table does not carry. Catching it means adding `атак` to
   `KIND_DECLARE_MARKERS`.
2. `КАБи 9677 на КРАМАТОРСЬК`, `каб напрямок Краматорськ` - the
   Donetsk-facing traffic announces a means with **no declaration word at
   all**. Catching it means treating the name of a munition as a declaration
   in its own right, which is a different kind of claim: it would classify any
   message mentioning a munition, including summaries and after-action
   reports.

**Read this before touching the declare table.** Adding `атак` was measured
against the corpus as an inversion risk: `Відбій атаки дронів-камікадзе`
carries `атак`, and under the pre-0.19.4.0 lift table carried no lift phrase,
so every lift of that shape would have been read as a fresh declaration. That
is why the lift table was widened first. **The lift table is widened before
the declare table, never after**, and any future extension of the declare side
re-checks that ordering rather than assuming it holds.

**Acceptance:** a third `kind_coverage` run with the 0.19.4.0 table as
baseline, the near-miss pile read by hand again, and specifically: the count
of messages classified as DECLARED whose text also contains `відбій`, which
must be zero. Item 2 is a separate decision and should not be folded into the
same run: two changes, one measurement, no attribution.


## T47. Two threat kinds the consumer cannot name
Status: `ready`, **S8** [tier 1]

MAVO classifies four kinds. The consumer knows three strings and maps
everything else onto one label:

| Kind | Declarations, 2026-08-10 | What the page shows |
| --- | --- | --- |
| `drone` | 2,756 | alarm dronowy, with a glyph |
| `glide_bomb` | 2,104 | **typ nieznany**, no glyph |
| `missile` | 242 | alarm rakietowy, with a glyph |
| `artillery` | 934 | **typ nieznany**, no glyph |

So three thousand declarations, more than the missile and drone counts
together, arrive named and render as unnamed. That is not a lie, and it is the
same collapse this project refuses everywhere else: "the source said nothing"
and "the source said something this reader has no word for" are different
facts, and one label for both loses the difference. It is `AlertState.UNKNOWN`
against `PARTIAL_CLEAR`, one layer out.

**Glide bombs specifically are worth a category even though they do not reach
Poland.** They are the largest single class in the corpus, they mark which
oblast is being worked over right now, and a reader watching the western belt
learns something real from seeing that Zaporizhzhia is under KAB rather than
under drones. The alarm tier never sees them (D-015, and the regimes name
missile and drone explicitly); the reporting tier should.

**Acceptance:**
1. `docs/WEBAPP.md` carries the full list of `kind` values as part of the
   contract, and `tools/contract_check.py` fails when a member of
   `ThreatKind` is missing from it. That check is in this repository because
   the producer is where the enum lives.
2. The consumer gains a label and a glyph for each, or states in its legend
   that it renders them as unknown deliberately. Either is honest; silence is
   not.
3. No new regime. A glide-bomb or artillery declaration must remain unable to
   reach an alarm rule, and a test asserts it.

**What would reopen the third point.** Evidence that a glide bomb has ever
crossed or landed near the Polish border, which would make it a warning
question rather than a reporting one. Nothing in the corpus suggests it.


## T48. Apple critical-alerts entitlement
Status: `ready` (own action), **not started** [tier 2]

On iOS, a notification that bypasses Do Not Disturb and the ringer switch needs
the critical-alerts entitlement. Apple grants it per application, on
application. A civil-safety warning app is squarely the category the
entitlement exists for, but the decision and its timing belong to Apple
`[reported; the process is Apple-documented, the approval odds are not]`.

**Why this is tier 2 and self-service rather than blocked, corrected on
2026-08-10.** The first version of this entry called it `blocked-external` and
tier 3, on the reasoning that there is nothing to apply with because no app
exists. That reasoning was wrong.

What Apple's request requires, stated as the requirement rather than as a
status: a developer account with a Team ID, a registered bundle identifier, and
a written description of the use case. **The application does not require a
published app, or a written one.** Everything on that list is obtainable
without waiting on anybody, which is what makes this self-service rather than
externally blocked.

**And the use-case description is the part this project is unusually well
placed for.** The entitlement is granted on the strength of what the app is
for. A public repository with a test suite, a defect log, a written statement
of what the tool refuses to claim, and a working report is a stronger case
than an unbuilt idea, which is what most applications are. The material that
would go in the description already exists in `docs/BRIEF.md`.

**Why it is not tier 1.** Applying costs an afternoon and answers a question
whose answer changes the architecture, so waiting has a cost. But two things
are still true and both belong in the application: nobody receives anything
yet, and T6 has produced no written legal position. Describing a service with
no recipients is not dishonest, and it is a weaker application than the same
one made after T11.

**The reason to do it early anyway.** The lead time is entirely outside this
project's control and the answer changes the design rather than the schedule.
A refusal makes the voice-call bridge the iOS alarm path outright. Finding
that out after building around the entitlement is the expensive order.

### Progress, to be filled in as it moves

| Stage | State | Date | Note |
| --- | --- | --- | --- |
| Constraint documented | **done** | 2026-08-10 | `docs/MOBILE.md`, "The iOS constraint, named" |
| Use-case description drafted | not started | | Source material is `docs/BRIEF.md` |
| Application submitted | not started | | |
| Apple response | | | **A pending application is not progress. This row is the only one that closes the question** |

**On the "call bridge", and this needs correcting rather than planning.**
`docs/MOBILE.md` contains one clause, in parentheses, saying that until the
entitlement exists an iOS recipient's alarm path is a voice call. An earlier
version of this entry gave that clause a row in the table above and a
recommendation to exercise it early. **That was an overreach**: a passing
remark in one document was promoted to a component with a plan, which is the
drift this repository is supposed to catch.

Examined properly, the idea conflicts with three things written elsewhere:

- **Phone numbers are personal data.** This project refused Google map tiles so
  a reader's viewport never reaches a third party (D-016) and keeps client
  addresses out of the access log. Storing recipients' numbers and handing them
  to a carrier on every alarm is a different category from anything it has
  declined so far.
- **A telephony provider is an external dependency with a contract and a bill**,
  in a project whose hard rule is stdlib-only with no runtime dependencies. A
  push server can be self-hosted; a carrier cannot.
- **Automatically telephoning people at night is a larger change of class than
  a push notification**, in a system that has just decided (D-015 revision 1)
  that moving from reporting to warning needs T6 and T11 answered first.

**Nothing about the bridge is decided, and this entry does not decide it.** If
the entitlement is refused, the options are: no alarm class on iOS at all, a
non-guaranteed push that says plainly that it may be silenced, or a voice path
with the privacy and dependency costs above accepted in writing. That is a
decision for `DECISIONS.md`, taken when there is a reason to take it, not a
row in a progress table.

**Acceptance for this task, narrowed accordingly:** the entitlement granted and
one alarm delivered through Do Not Disturb on a real handset, or the refusal
recorded here with its date. **What happens after a refusal is out of scope
until it happens.**

**What would remove this task entirely.** A decision that iOS is out of scope
(`docs/MOBILE.md` already keeps it off the M1 and M2 critical path), or
recipients who all use Android, which is knowable only after T11.

## T50. An event stream in the contract, schema v3
Status: **partial at 0.25.0.0, and the remaining half is named rather than
rounded off.** Shipped and held by regressions: schema v3, the twenty-minute
window inside `state.json`, `feed.json` over twenty-four hours, both roles, all
of Ukraine, the cap and its flag, `window_start`, `counts_24h`, and
`tools/contract_check.py` reading all of it. **Not done:** the deprecation
policy for v2, and the size measurement under a mass alert rather than under a
quiet night. Both are below. [tier 1]

**The consequence of the half that is missing, and it is operational.** The v3
payload is a strict superset of v2 - every field a v2 consumer requires is
still there - but `mavo-site` 3.0.0.0 refuses any version it does not know, by
design, because a page rendering an unfamiliar payload with familiar
assumptions is worse than one that says it cannot read the file. So **0.25.0.0
must not reach production before the site release that reads v3**. Deploying
it alone turns the public page blind, correctly and unhelpfully. The two
releases go out in one window, producer first by minutes rather than by days.

**What a deprecation policy would have to say**, when it is written: how long
the producer keeps writing a v2-shaped file beside the v3 one, and what ends
that period. This project has one consumer and controls it, which is why the
absence is survivable today and why it stops being survivable the moment
anyone else reads the contract - FEED-SPEC section 3 property four is exactly
this obligation, written for somebody else's feed.

*Original entry below.*

`state.json` v2 carries the **current picture** - `areas` - and **seven-day
counts** - `recent_7d`. It carries no history. A live feed of transitions is
history, so the consumer cannot build one from what the producer publishes,
and no amount of work on the site changes that: the contract is owned by the
producer (D-020).

**What has to be decided rather than implemented, and it is the whole task.**
How long a window the contract carries. The file is fetched every two minutes
by every reader, so every event in it is paid for on every poll by everyone.
An hour of transitions is a panel that is usually empty; a week is a file that
grows without bound during a mass alert, which is exactly when the reader is on
one bar of signal. **Neither end of that trade is obviously right and the entry
must not pretend otherwise.**

**A second thing the volume makes real.** MAVO sees on the order of a dozen
transitions a day across 23 oblasts. A feed panel modelled on a dashboard that
shows hundreds of rows a month will look broken most of the night. That is
information rather than a fault - the sky is usually quiet - but a panel that
reads as "nothing is working" when it means "nothing is happening" repeats this
project's oldest failure in a new place, and the design has to refuse it
explicitly.

**Acceptance:** schema v3 carrying transitions with a timestamp, an area, a
kind and a state change; a stated window with the reasoning for its length; a
deprecation policy for v2 with a period, not an intention; `tools/contract_check.py`
extended to both versions; and a measurement of the file size under a mass
alert rather than under a quiet night, because the quiet night is not the case
that breaks it.

## T51. Geographic layers, fetched only when asked for
Status: `ready`, needs T50 for nothing [tier 2]

Voivodeship borders, Polish and Ukrainian border-region cities, and possibly
major routes. The value is a reader orienting the alert against a place they
know rather than against an outline.

**The budget is measured and is the constraint.** First visit is 117.4 KiB
gzipped, repeat visit 13.7 KiB, of which geometry is 106 KiB and is cached
after the first load. `deploy/nginx.conf` records what that costs on a slow
link: the geometry asset is the difference between eight seconds and
twenty-two at 120 kbit/s, and the audience is a phone at night, sometimes on
one bar.

**The resolution is lazy loading, not a smaller map.** Detail ships as separate
assets fetched on zoom or on an explicit toggle. A reader who never asks pays
nothing; a reader who wants to see where this is relative to Zamość pays
deliberately.

**Acceptance:** the first visit without layers **does not grow**, each layer
measured separately in KiB gzipped and recorded, source and licence named per
layer, and the geometry verification extended to whatever new coordinates
arrive. Routes are the heaviest and go last, or not at all if the measurement
says they do not fit.

**What this does not do, and it is a decision.** It does not introduce map
tiles. Tiles from a third party would send every reader's viewport, address and
timing to that party, which is precisely what D-016 refused for Google's tiles.
Self-hosted vector tiles are a real alternative and carry their own cost - a
WebGL renderer is roughly 200 KiB of JavaScript and would end the site's
zero-dependency, hashed-CSP posture. That trade belongs in a decision entry
before any of it is written, not in a commit.

## T52. Polish, English and Ukrainian
Status: `ready` [tier 2]

**Ukrainian is not symmetry with anybody, and the reason is measured by
demography rather than by product taste.** Roughly two million Ukrainians live
in Poland `[reported]`, which makes them the largest single audience this
project can have. For that reader MAVO is not a situational instrument about a
neighbour; it is a view of the country their family is in, read from Poland.
That changes what the page is for, and the entry records it so a later reader
does not mistake the third language for decoration.

Polish is the stated audience. English is the portfolio surface and the
language `docs/FEED-SPEC.md` argues in.

**Acceptance:** three complete sets, no string left in Polish under another
language, the switch working without JavaScript for the basic path, and the
non-claim in the header - that this is not a state service - translated with
the same care as everything else, because it is the sentence the legal position
rests on.

## T53. Full-width map, fullscreen, theme switch
Status: `ready` [tier 3]

Cheap, no conflicts with anything recorded. The page already honours
`prefers-color-scheme`; the switch is an override plus a remembered choice.
Fullscreen is the Fullscreen API. Full width is layout.

**Acceptance:** the reduced-motion refusal and the staleness rendering survive
all three, verified by the browser harness rather than by looking at it.

## T49. Two denominators for the western share, and one number quoted for both
Status: `ready` (own action), **not started** [tier 2]

The T36 draw on 2026-08-11 measured the design-window population directly:
**1,006 western messages against 41,848 front-line, so 2.35% of resolved
messages** `[measured]`. The figure this repository quotes elsewhere is 3.5%,
which comes from `docs/CHANNEL.md` and is a share of **tag occurrences**, not
of messages `[measured, different denominator]`.

Both are correct about what they count. They are not interchangeable, and the
direction of the gap is explained rather than mysterious: a western alert
routinely names several raions in one message - the draw contains one naming
seven - so the same event contributes one message and seven tag occurrences,
which lifts the occurrence share above the message share.

**Why this is a task rather than a correction.** Each sentence quoting 3.5% has
to be read to see which quantity it meant. `mavo/areas.py` says "96.5% of tag
occurrences", which is exact. Other places say "3.5% western" with no
denominator at all, and those are the ones at risk: a reader takes the nearest
available meaning, and for a sentence about traffic that is messages.
Rewriting them to 2.35% without reading them would replace one unlabelled
number with another.

**Acceptance.** Every occurrence of 3.5% or 96.5% either names its denominator
in the sentence or is replaced by the message-share figure with its own. A
`lint_domain` rule refusing a bare "3.5%" near the word "western" is the
mechanism that would keep it, and whether that rule is worth its false
positives is part of the task rather than assumed.

**Not urgent, and the reason is worth stating.** No measurement divides by
either figure; both appear in prose describing the shape of the traffic. The
cost is a reader's misunderstanding, not a wrong result. That is exactly the
class F80 came from, which is why it is logged rather than left in a session.
