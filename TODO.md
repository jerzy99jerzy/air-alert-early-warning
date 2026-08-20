# TODO

<!-- index:begin -->

### Where the backlog stands

**27 of 67 closed, 40 open.** Counted from the entries below by `tools/todo_index.py`, which the gate re-runs, so this table cannot drift from the list it summarises.

| State | Count | What it means |
| --- | --- | --- |
| `done` | 19 | Finished, with the release that closed it named in the entry |
| `moved` | 8 | Owned by another repository; the entry here is a pointer, not a copy |
| `ready` | 27 | Nothing external blocks it; it needs a session |
| `decision` | 7 | Waiting on a judgement rather than on work |
| `blocked-external` | 3 | Waiting on somebody outside this project |
| `deferred` | 2 | Deliberately parked, with the decision that parked it named |
| `debt` | 1 | Known cost carried on purpose |

### Priority tiers

Tiers are a claim about *order*, not about importance, and they move as the project moves. Declared per entry so this table is generated rather than maintained.

| Tier | Meaning |
| --- | --- |
| **1** | Blocks something already promised, or a measurement without which a shipped claim is unsupported |
| **2** | Real work that nothing is waiting on today |
| **3** | Worth doing, worth dropping if the project turns |

**Tier 1, 11 open:** [T6](#t6-legal-position-on-distributing-warnings-to-people-other-than-the-operator), [T39](#t39-tolerated-poll-rate-under-continuous-operation), [T40](#t40-how-late-is-the-channel-measured), [T11](#t11-ask-whether-anyone-actually-wants-this), [T34](#t34-what-is-in-the-066-of-messages-without-a-tag), [T36](#t36-the-hand-labelled-sample-retargeted), [T46](#t46-declarations-phrased-without-a-declaration-word), [T54](#t54-observe-the-staleness-machine-crossing-once-on-a-real-host), [T65](#t65-decide-what-a-successful-poll-with-no-state-change-should-render-as), [T66](#t66-attempt-completeness-as-its-own-instrument), [T68](#t68-decide-where-if-anywhere-a-polish-warning-renders)

**Tier 2, 16 open:** [T7](#t7-onboarding-probe-from-a-clean-clone), [T8a](#t8a-is-there-any-ingestible-polish-source-measured-against-feed-spec), [T8b](#t8b-does-poland-enter-the-products-scope), [T12](#t12-detect-changes-to-the-ukrainealarm-offer-contract), [T22](#t22-fail-the-build-when-a-document-cites-an-identifier-the-package-lacks), [T31](#t31-katottg-as-a-versioned-file), [T33](#t33-alias-table-between-the-channel-and-the-register), [T35](#t35-turn-the-negative-result-into-a-measurement), [T59](#t59-tags-the-channel-emits-that-the-register-map-does-not-hold), [T61](#t61-s7-against-t31-t33-and-t34-decide-then-record), [T43](#t43-raion-centroids-in-the-contract), [T48](#t48-apple-critical-alerts-entitlement), [T49](#t49-two-denominators-for-the-western-share-and-one-number-quoted-for-both), [T62](#t62-the-identifier-checks-cannot-see-a-suffixed-identifier), [T64](#t64-a-claim-about-a-systemd-unit-quotes-the-unit), [T67](#t67-the-rso-reader-and-what-it-is-a-reader-of)

**Tier 3, 13 open:** [T1](#t1-request-the-alertsinua-api-token), [T4](#t4-executable-claim-behind-the-never-raise-parser-guarantee), [T5](#t5-rolling-feed-latency-drift-detection), [T41](#t41-prototype-the-push-interface-and-compare-it-against-polling), [T9](#t9-keep-the-coverage-floor-a-ratchet), [T10](#t10-find-a-history-source-deep-enough-to-calibrate-on), [T14](#t14-second-signal-type-for-the-drone-regime), [T26](#t26-reproduce-the-pid-namespace-hole-in-directorylock-then-fix-it), [T28](#t28-the-crossing-event-list-dated-and-sourced), [T56](#t56-is-there-an-alert-feed-for-the-romanian-border-and-the-baltics), [T57](#t57-a-week-of-the-picture-statistics-a-reader-can-open), [T58](#t58-traffic-and-road-conditions-near-the-border-refused-as-posed), [T63](#t63-tags-are-annotated-and-unsigned-and-a-document-said-otherwise)

### By sprint

Sprint numbering follows `docs/MVP.md`. Tasks with no sprint are either outside the beta path or not yet placed on it.

| Sprint | Open tasks |
| --- | --- |
| **S7** | [T31](#t31-katottg-as-a-versioned-file), [T33](#t33-alias-table-between-the-channel-and-the-register), [T34](#t34-what-is-in-the-066-of-messages-without-a-tag), [T61](#t61-s7-against-t31-t33-and-t34-decide-then-record) |
| **S9** | [T39](#t39-tolerated-poll-rate-under-continuous-operation), [T40](#t40-how-late-is-the-channel-measured), [T66](#t66-attempt-completeness-as-its-own-instrument) |
| **S10** | [T11](#t11-ask-whether-anyone-actually-wants-this) |
| **S11** | [T7](#t7-onboarding-probe-from-a-clean-clone), [T22](#t22-fail-the-build-when-a-document-cites-an-identifier-the-package-lacks) |
| **S12** | [T36](#t36-the-hand-labelled-sample-retargeted) |
| **unassigned** | [T1](#t1-request-the-alertsinua-api-token), [T4](#t4-executable-claim-behind-the-never-raise-parser-guarantee), [T5](#t5-rolling-feed-latency-drift-detection), [T6](#t6-legal-position-on-distributing-warnings-to-people-other-than-the-operator), [T41](#t41-prototype-the-push-interface-and-compare-it-against-polling), [T8a](#t8a-is-there-any-ingestible-polish-source-measured-against-feed-spec), [T8b](#t8b-does-poland-enter-the-products-scope), [T9](#t9-keep-the-coverage-floor-a-ratchet), [T10](#t10-find-a-history-source-deep-enough-to-calibrate-on), [T12](#t12-detect-changes-to-the-ukrainealarm-offer-contract), [T14](#t14-second-signal-type-for-the-drone-regime), [T26](#t26-reproduce-the-pid-namespace-hole-in-directorylock-then-fix-it), [T28](#t28-the-crossing-event-list-dated-and-sourced), [T35](#t35-turn-the-negative-result-into-a-measurement), [T59](#t59-tags-the-channel-emits-that-the-register-map-does-not-hold), [T43](#t43-raion-centroids-in-the-contract), [T46](#t46-declarations-phrased-without-a-declaration-word), [T48](#t48-apple-critical-alerts-entitlement), [T49](#t49-two-denominators-for-the-western-share-and-one-number-quoted-for-both), [T54](#t54-observe-the-staleness-machine-crossing-once-on-a-real-host), [T56](#t56-is-there-an-alert-feed-for-the-romanian-border-and-the-baltics), [T57](#t57-a-week-of-the-picture-statistics-a-reader-can-open), [T58](#t58-traffic-and-road-conditions-near-the-border-refused-as-posed), [T62](#t62-the-identifier-checks-cannot-see-a-suffixed-identifier), [T63](#t63-tags-are-annotated-and-unsigned-and-a-document-said-otherwise), [T64](#t64-a-claim-about-a-systemd-unit-quotes-the-unit), [T65](#t65-decide-what-a-successful-poll-with-no-state-change-should-render-as), [T67](#t67-the-rso-reader-and-what-it-is-a-reader-of), [T68](#t68-decide-where-if-anywhere-a-polish-warning-renders) |

<!-- index:end -->

Every item carries a status, a tier, a blocker type where one exists, and an
acceptance test, so that "done" is not a matter of opinion and neither is
"next".

Status: `ready` | `blocked-external` | `decision` | `debt` | `deferred` | `done` | `moved`
Tier: `[tier 1]` | `[tier 2]` | `[tier 3]`, meaning below.

### Where the project is

*Rewritten at 0.32.5.0, and the version is in this sentence on purpose.* The
paragraph this replaces described 0.19.0.0 to 0.19.4.0 as "the last four
releases" and was still saying so at 0.32.4.0, thirteen minor versions later.
The generated block above it cannot drift, by construction. This part can, it
did, and it is the part a reader reaches first. Anyone editing here restates
the version they wrote it at, so the next drift is visible rather than
inferred.

**Sprint S9, declared partial and still open.** Its window runs to
2026-08-20 11:02:06 UTC (D-032).

**S8 closed on 2026-08-17, on an amended criterion and recorded as amended**,
the way S7 did. The report composes, the command runs, the contract ships and
the distance column is verified three ways. **The hand-checked accuracy sample
was withdrawn from it**, not met: it is drawn from western areas under alert,
that population has not appeared, and no engineering week brings it forward.
It is T36, retyped `blocked-external` and moved to **S12**, the sprint that
decides whether this project is finished rather than merely built. The full
statement of what that costs every accuracy figure here is the western
asterisk in `docs/MVP.md` section 7, and anyone quoting a number from this
repository should read it first.

**Releases since S8 have been repairs and instruments, not sprint work**, and
counting them as progress towards beta would be the mistake the paragraph above
was written to prevent. 0.19.x was an audit and its consequences; 0.2x and 0.3x
added the event stream, the threat-kind measurement, the latency instrument
(T40, built and unread), the corpus census, the privacy gate and the tooling
that keeps this file honest. Useful, and orthogonal to the sprint plan.

**The next sprint is S9, and T60 opens it rather than sitting beside it.** S9's
exit criterion is 72 unattended hours and the first end-to-end latency
distribution. `vm-mavo` runs pre-0.28.1.0 code, so F98 is not deployed and the
fetch timeout on that host is ten seconds per socket operation per resolved
address. A latency distribution measured there is a distribution of a different
instrument, which is T60's argument applied to the sprint that depends on it.

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
Status: `ready` [tier 1], **S9**. *Raised from tier 2 on 2026-08-11: the first
field measurement is not what this entry expected.*

**Measured on the cloud host, 2026-08-11, 20:18 to 22:37 UTC** [measured, one
window, n=60 polls at a ~130 s interval]:

| Quantity | Value |
| --- | --- |
| Unreachable polls | 9 of 60, 15.0% |
| Over the wider 12-hour journal | 11 of 95, 11.6% (Wilson 6.6-19.6%) |
| Longest run of consecutive failures | 2 |
| Longest gap between successful reads | 7.0 min (median 2.3 min) |
| `valid_for_s` threshold for a degraded page | 600 s |

**The failures do not trip the staleness threshold, and the margin is three
minutes rather than the eight an independence assumption would predict.**
Consecutive failures happen; they were assumed away and should not have been.

**Three explanations tested, two closed:**

- *Rate limiting by the source.* **Closed by measurement.** Ten requests in
  fifty seconds all returned 200 with a median of 0.24 s, a rate twenty-six
  times more aggressive than production. A limiter that tolerates that would
  not be tripping at 130 s.
- *The IAP tunnel.* **Closed by construction.** `mavo-collect.service` reaches
  `t.me` directly over IPv6 and knows nothing about IAP, which is the
  administrative path. The tunnel does drop, observed twice on 2026-08-11, and
  that is a separate finding about the operator's own access rather than about
  collection.
- *Packet loss on the IPv6 path.* **Open.** The mechanism fits: successful
  polls take 0.24-0.45 s against a 10 s timeout, so a failure is a stall of an
  order of magnitude, and a lost SYN retried at 1, 2, 4 and 8 seconds lands
  past the ceiling. A 60-packet ping showed 0% loss and RTT 22 ms with 0.12 ms
  deviation, **but that probe had 45% power against a 1% loss rate**, so it
  neither confirms nor refutes. 600 packets gives 99.8%.

**Retracted from the first reading of this data:** the apparent rise from 6.7%
in the first half of the window to 30.8% in the last thirty minutes. Fisher
p = 0.145 on 2/30 against 7/30. Nine failures cannot carry a trend, and the
claim was made before the arithmetic.

**What to do next, in order, and deliberately not "change the interval":**

1. **Report the elapsed time on the refusal.** `[UNREACHABLE]` says nothing
   about how long it waited, so a stall that hit the 10 s ceiling and a
   refusal that bounced in 20 ms are indistinguishable in the journal. That is
   a probe whose outcomes do not separate its hypotheses, which is F44 in the
   diagnostics rather than in the schedule. Small change, and the next night's
   journal answers the question by itself.
2. **600-packet ping, and a TCP-level equivalent**, because ICMP can be
   policed differently from TCP and a clean ping is only circumstantial.
3. **A week of the instrumentation this entry already asks for**, at the
   current interval, before any ladder step. The baseline is the thing missing.
4. **Only then** consider a single in-poll retry or a longer timeout. Both
   would mask the symptom before its cause is known, and a masked symptom in
   the component that decides whether the sky is being watched is worse than a
   visible one.

**Raised to tier 1** because this is no longer a politeness question about a
future daemon. A collector that misses roughly one poll in eight is the
instrument's own blindness, measured, in production, on the artefact that is
about to become publicly reachable.

*Original entry below.*

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
Status: `ready`, instrument at 0.30.0.0, distribution taken 2026-08-19, the row
still unwritten and waiting on T66 [tier 1], **S9**

**What is done.** `tools/latency.py` reads the store and reports the
distribution: median, p90, p99, max, the count, the window in days, negative
lags separately, and the poll interval beside them. It refuses a window shorter
than seven days without `--allow-short`, and it reports an upper bound on the
upstream rather than a channel latency, because the lag it measures contains
our own interval. Eleven regressions.

**What remains, and it is a host and a week, not an afternoon of typing.** Run
it against the live store once the collector has a week of continuous
operation, and paste the row into `docs/CHANNEL.md` section 8a with the
collection dates. The acceptance below is unchanged.

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

**Not `tools/contract_check.py`, and the collision is one word.** That tool is
in the gate and exercises the `state.json` schema this repository owns under
D-020. This task is about the ukrainealarm *offer*, a PDF on somebody else's
server. Different artefact, different upstream, different failure. Written down
because an entry that can be closed against the wrong evidence will be, once.

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


## T23. Attach the observability sink, which existed and was not connected
Status: `done` (0.32.7.0) [tier 1]

The sink and the reader shipped at 0.23.0.0; five of the seven criteria in
`docs/OBSERVABILITY.md` section 9 were met and living in `tests/test_obs.py`.
What was missing was a caller.

**Measured 2026-08-17 (F103):** `mavo.obs.from_environment` had no caller
anywhere in the package, `mavo/report.py` used `RunLog` only as the type of an
optional parameter nothing passed, and the production unit set
`MAVO_LOG_FILE=/var/lib/mavo/run.jsonl` against a file that had never existed.

**The repair was one argument**, and the belief that it needed a new unit was
itself wrong (**F104**): `mavo report --watch --json` is the loop, it runs as
`mavo-report.service`, and `publish()` had accepted a `log` for nine releases.

**What the tests found, which the wiring alone would not have.** The only
`log.line` in the loop was `publish.interval`, written before sleeping, so a
cycle that did not sleep - the last of every run, and every run ending on a
write failure - left no trace. **The record of the loop was a record of its
pauses.** A `publish.cycle` line now carries feed state, `as_of`, western
count and event count, and `skipped` is absent rather than zero because this
loop reads a store and has no window to have missed.

**Acceptance met:**
1. A live path constructs the sink, announced on stdout as `run-log=<path>` so
   a variable that did not take is visible in one line rather than three days
   later.
2. **A test that fails when nothing writes.** Its first version asserted only
   that the file was non-empty and passed against a tree with the wiring
   removed, because `RunLog.__init__` writes its own retention line: a test of
   the constructor wearing the name of a test of the loop. It asserts on
   `publish.cycle` records now, and both it and the per-cycle count are
   verified red against the unwired tree.
3. The two remaining criteria in `docs/OBSERVABILITY.md` section 9 need the
   notifier (S10) and a live view respectively, and stay named there rather
   than rounded up.
4. `MAVO_LOG_FILE` moves from `mavo-collect.service` to `mavo-report.service`
   on the host, which is a deployment step recorded in `docs/DEPLOYMENT.md`,
   not a change in this repository.

## T24. Keep the run log out of the holdout
Status: `done` (0.23.0.0, recorded 0.32.7.0) [tier 2]

The design and holdout split was frozen before any message content was read
(D-012a). A run log echoing message bodies spends that split without anyone
deciding to spend it.

**Acceptance met, and it was met four months of releases before this entry was
updated.** `tests/test_obs.py::test_the_sink_carries_no_message_text_by_default`
runs a hostile fixture whose every message body carries a recognisable token and
asserts the token appears nowhere in the sink, with `bodies_not_logged` present
so the redaction is visible rather than silent.
`test_enabling_bodies_leaves_a_mark_in_the_record_it_weakened` holds the other
half: the debug switch writes `sink.bodies_enabled` into the record it weakens,
so a later reader can tell that the file may contain holdout content. Both carry
named mutations.

**Closed on reading the suite rather than on new work**, which is the same
pattern as T27 and belongs to the same finding: the backlog understated
completion and nothing ever prompts anyone to look for good news. See the drift
section in `docs/METHODOLOGY.md`.

## T25. Decide where the daemon lives
Status: `done` (D-031, 0.32.7.0) [tier 2]

**Answered by deploying it on 2026-08-11 and recorded on 2026-08-17.** The
collector runs on `vm-mavo` in `europe-central2-a` as a `oneshot` unit under a
systemd timer, not as a daemon. `docs/MOBILE.md`'s always-on host is a Linux VM
and the supervision mechanism is systemd's.

**Acceptance met:** D-031 names the host and the mechanism and states its
reopen condition. It also records the consequence T25 could not have known:
there is no process holding state between polls, so **M0 is a new unit rather
than a flag on this one**, which changes how T23 must be read.

**Six days as a `decision` after the decision was made.** An unrecorded
decision cannot be reopened, because nobody can say what it was.

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
Status: `done` (deployed 2026-08-11, recorded 0.32.7.0) [tier 2]

`RandomizedDelaySec=5` is in `/etc/systemd/system/mavo-collect.timer.d/interval.conf`
alongside `OnUnitActiveSec=30` and `AccuracySec=1s`, and has been since the
collector was first enabled.

**Closed six days late, and the lateness is the point.** The entry read `ready`
while the thing it asks for was running in production, because the work arrived
through a deployment rather than a release and nothing here connects the two.
See **F102** and the drift section in `docs/METHODOLOGY.md`.

**Acceptance met, measured:** the interval distribution over 24 hours is
n=2619, p50 33.00 s, max 36.06 s against a theoretical ceiling of 36 s. Jitter
is present in the spread and bounded by the configuration.

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
Status: `blocked-external` (the population has not appeared), **S12** [tier 1]

*Retyped and moved at 0.32.9.0.* This was carried as an engineering blocker on
S8 and it is not one. `docs/MVP.md` types its blockers and says access and
decision blockers do not shrink when code is written; **this one shrinks for
nobody.** The sample the product needs is drawn from western areas under
alert, roughly 3.5% of what the channel carries, and it cannot be drawn from a
population that has not appeared. The instrument is built and waiting. See the
western asterisk in `docs/MVP.md` section 7.

The sprint closed on an exhaustive
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
Status: `ready`, **S9** [tier 2]
*Moved from S8 at 0.32.9.0, when S8 closed. It is a store and schema repair
rather than a report one, and holding a closed sprint open for it would have
misreported both.*
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
Status: `moved` to `mavo-adsb`, which holds the sampler, the store and the
retention. What is left here is the question, not the work [tier 2].

**Progress, 2026-08-14.** Acceptance item 1 is under way rather than done. The
sampler is deployed on `vm-mavo` as its own unit, user and store, polling once
every 60 seconds and retaining 8 days; D-028 records the cadence, the box, and
why raw state vectors are stored rather than derived landings. It is
deliberately outside this tree (`docs/DEPLOYMENT.md` section 2). Items 2, 3 and
4 are untouched and cannot start before the sampler has run its three nights,
one of them with a western-Ukraine alert.

**Not yet measured, and the arithmetic in D-028 rests on it:** whether
`x-rate-limit-remaining` is returned on this endpoint, and therefore what a
call actually costs. Until a response has been read, the credit budget is
[inference].

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


## T59. Tags the channel emits that the register map does not hold
Status: `ready`, follows T16. [tier 2]

`data/reference/tag_map.csv` holds 127 rows derived from the **design window**:
48,540 messages over 99 nights. The corpus runs 61,041 messages over 118 days.
Tags first appearing outside the window are absent from the map by
construction, and `AreaTable.resolve_all` returns them in its second element,
which its own docstring calls load-bearing because a caller ignoring it has
turned a new area into silence.

**Why this is not T34.** T34 is the 321 design-window messages carrying no tag
at all. This is messages carrying a tag the map cannot resolve. Different
population, different cause, different repair. `docs/METHODOLOGY.md` filed the
artillery near-misses under T34 for five sprints, which is why this looked
covered; the correction is in that document at 0.32.0.0.

**Why it matters beyond area coverage.** `Загроза артобстрілу` over
`Покровська територіальна громада` carries a declaration marker *and* a kind
and is lost on the tag alone. Every message of that shape is a kind
declaration the join never sees, and the join currently reaches 17% of alerts.

**Acceptance:**
1. `tools/unmapped_tags.py` run over the corpus, output recorded in
   `docs/METHODOLOGY.md` with its date and message count. Shipped at 0.32.0.0;
   the run has not been made.
2. The distinction the tool prints, read rather than totalled: a pile dominated
   by singletons is typos and one-off constructions; a pile with a heavy head
   is areas the map does not hold. These call for different repairs.
3. A decision recorded either way on whether the map extends past the design
   window. **It is not a mechanical change.** A map built from the window is an
   evidence artefact and a current map is an operational one; extending it
   means 99.34% and "127 distinct labels" stop describing the same object and
   need a caveat wherever they appear, including `docs/FEED-SPEC.md`,
   `docs/CHANNEL.md`, both briefs, `STATUS.json` and `tools/brief_check.py`.
   Versioning the map with the design-window variant frozen resolves it
   cleanly and is work, not a line.
4. If the map is extended, the measured coverage figure is re-run and the old
   one is kept beside it. A coverage number that moved because its denominator
   changed is not an improvement and must not be reported as one.

**Out of scope.** Resolving anything against KATOTTG, or estimating what
coverage would become. Both need item 1's numbers first, and item 1 may say the
work is not worth taking.

## T60. Production runs older code than `main`, and nothing here says so
Status: `done` (0.32.7.0), and **the premise was false before it was closed** [tier 1]

The entry said `vm-mavo` was last installed before 0.28.1.0 and therefore ran
pre-F98 code. Read on 2026-08-17: the host carries 0.32.2.0, installed
**2026-08-14 18:13:09 UTC**, and `connect_within` is present in the installed
`mavo/transport.py`. F98 has been deployed since three days after the entry was
written, and no document here said so. That staleness is **F102**.

**Acceptance, all three, against measurement rather than assertion:**

1. *Post-F98 code on the host, verified by a symbol rather than a version
   string.* `'connect_within' in mavo/transport.py` is `True`, read through
   `/opt/mavo/venv/bin/python`, which is the interpreter `ExecStart` names. The
   first attempt at this read used the system `python3` and returned
   `ModuleNotFoundError`, which is a correct answer to the wrong question.
2. *A line in `docs/DEPLOYMENT.md` stating what is installed, with its date,
   distinct from what this repository describes.* Written, and now carrying
   `Host state measured:` with a gate check that refuses a date more than
   fourteen days behind the release.
3. *D-027's interval distribution re-read after the change.* n=2619 over 24
   hours: min 30.06, p50 33.00, p90 35.00, p99 35.01, max 36.06, against a
   configuration ceiling of 36. D-027's one-hour figure is confirmed at
   twenty-four times the scale.

**A deploy was not needed and this is measured, not assumed.** The host is
three releases behind `main` and none of 0.32.3.1, 0.32.4.0, 0.32.5.0 or
0.32.6.0 changes an executable line.

**The reopen condition stands and is now cheap to check:** any release that is
tagged and not deployed leaves this open by definition. The repair is the dated
line, which the gate holds.

## T61. S7 against T31, T33 and T34: decide, then record
Status: `ready`, **S7**, and it is a decision rather than work. [tier 2]

`docs/MVP.md` closes S7 on an amended criterion. T31, T33 and T34 still carry
S7 and are open. `tools/todo_index.py` names this in
`TOLERATED_OPEN_IN_A_CLOSED_SPRINT` with a reason and a check that removes the
entry when the disagreement stops being real, so the state is visible and
cannot rot. What it is not is decided.

**The two answers, both defensible.** Either the S7 row in `docs/MVP.md` is
amended again to say the sprint closed without these three, which is what
happened; or the three are reassigned to a later sprint, which is what the
backlog implies. The first is honest about history and leaves three tasks
belonging to nothing. The second is tidier and rewrites what the sprint was.

**Acceptance:** whichever is chosen, a `docs/DECISIONS.md` entry with a reopen
condition, and the tolerance entry removed by the check that watches it. **A
third outcome - leaving it tolerated indefinitely - is the one this task
exists to prevent**, because a named tolerance that never resolves is an
exemption with better manners.

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
Status: `done` (0.32.5.0, against measured evidence on both sides) [tier 2]

MAVO's register carries one `kyiv`. The consumer's geometry splits `kyiv-city`
from `kyiv-oblast`, a real administrative distinction this project does not
make. Measured against `mavo-site` 1.2.0.0 on 2026-08-10: no `kyiv` in the
geometry and no mapping anywhere in the package, so the seven Kyiv-oblast
raions in `data/reference/tag_map.csv` landed in `unplaceable` and drew
nothing.

**Where the fix belonged.** The consumer, because it is the consumer's
geometry that makes the distinction. A producer that starts emitting
`kyiv-oblast` has learned its consumer's vocabulary and taken back the
decoupling D-020 bought.

**Acceptance met, both halves, and the halves were met eleven releases apart.**
`mavo-site` carries `SLUG_ALIASES = {"kyiv": "kyiv-oblast"}` in
`src/mavosite/contract.py`, resolved in `canonical_slug`, held by a test named
`test_the_kyiv_alias_is_the_only_divergence` in that repository's contract
suite [measured against 4.27.1.1 on 2026-08-17]. The slug pair is named in
`docs/WEBAPP.md` in this release.

**Why it is here at all, and why the closure is written this way.** The entry
recording F74 originally asserted that the consumer already did this, in the
present tense, without anybody having looked. This task replaced that sentence.
The replacement then went stale for eleven of the consumer's releases while
stating **It does not** in bold, which is **F81**. A task that exists because a
claim was made without measurement does not get closed by another one. The
staleness is logged as **F100**.

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
Status: `ready`, **partial at 0.27.0.0.** The second pattern is caught by a
narrower marker than the entry proposed; the first is not started, and the
prevalence of both is still unmeasured. [tier 1]

**Shipped:** `напрямок` joins `KIND_DECLARE_MARKERS`. It catches
`КАБ напрямок Краматорськ`, which the production host counted as unparsed on
every poll for a day - two messages in every twenty-message window, roughly
seven hundred times, before anybody read the journal.

**Why not the broader claim.** This entry proposes treating a munition's name
as a declaration in its own right and warns that doing so would classify
summaries and after-action reports. `напрямок` is a word about a thing in
flight now rather than a word that appears in a retrospective count, so it is
narrower and the broad version stays refused.

**The ordering was re-checked rather than assumed**, as this entry demands:
`lifting` is evaluated first and the declare test runs only under
`not lifting`, verified by reading and by a regression that puts the new
marker inside a lift.

**Still open:** `атак` for `Атака ударних БПЛА над містом`, whose inversion
risk this entry describes and which needs the lift table re-measured first.
And the measurement for what shipped: a `kind_coverage` run before and after
on the corpus, near-misses by hand, which is T45's acceptance applied to one
more marker. Until then the entry carries [assumption, unmeasured] and says
what would replace it.

*Original entry below.*

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
Status: `ready`, **S9** [tier 1]
*Moved from S8 at 0.32.9.0, when S8 closed.*

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

**Measured since, and it changes the entry from a warning to a fact.** The
consumer shipped its v3 reader at `mavo-site` 4.0.0.0 on 2026-08-12 and
refuses v2 explicitly, which was verified by running it. The deployment window
is therefore not a precaution against something that might happen; it is a
property of two programs that exist. Producer first, by minutes, and the page
is blind in between.

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
Status: `moved` to the consumer, 0.32.5.0 [tier 2]

Site work: the layers, the byte budget and the lazy loading all live in
`mavo-site`. The full entry travels to that repository's `docs/ROADMAP.md`; no
copy stays here. **A mirrored entry is F81's shape** - two descriptions of one
thing, one of them updated and the other going quiet - and the repository that
would do the work is the one that should carry the text.

What stays here is the one line this repository is answerable for: the producer
publishes no geometry and no layer, and D-016 governs any layer fetched from a
third party.

## T52. Polish, English and Ukrainian
Status: `moved` to the consumer, 0.32.5.0 [tier 2]

Site work: every string, the switch and the non-claim in the header are the
consumer's. The full entry, including the demographic argument for Ukrainian
being the largest audience this project can have, travels to `mavo-site`'s
`docs/ROADMAP.md`.

What stays here: this repository emits register names and slugs, not reader
text, and `tests/lint_domain.py` is what keeps it that way.

## T53. Full-width map, fullscreen, theme switch
Status: `moved` to the consumer, 0.32.5.0 [tier 3]

Site work, entirely: layout, the Fullscreen API and an override over
`prefers-color-scheme`. The acceptance that matters - the reduced-motion
refusal and the staleness rendering surviving all three, verified by the
browser harness rather than by looking at it - is a consumer gate clause and
cannot be checked from here. Travels to `mavo-site`'s `docs/ROADMAP.md`.

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

## T54. Observe the staleness machine crossing, once, on a real host
Status: `ready` [tier 1], **before the public link**

The page moves fresh to stale to blind on the browser's own clock, because a
server that has stopped cannot tell anyone it has stopped. **Nobody has ever
watched it happen.** The drill was started on 2026-08-11 at 18:13 and abandoned
after two minutes against a 600-second threshold; on 2026-08-12 an IAP failure
brought `observation_age_s` to 594.3 and the collector came back six seconds
short of demonstrating it by accident.

**Why this is tier 1 rather than housekeeping.** T39 measured the collector
missing roughly one poll in eight, with runs of two and a longest gap of seven
minutes. At that rate the degraded state is not hypothetical: it will be
reached, and the first person to see it should not be a stranger who was sent
the link.

**Method.** Stop three units on the producer host - `mavo-collect.timer`,
`mavo-report.service`, `mavo-push.timer` - and leave them stopped for thirty
minutes with the page open. The three matter: stopping only the collector
leaves the report loop rewriting `state.json` with a fresh `generated_at` over
an unchanging store, which is a different failure and would show the wrong
thing.

**Acceptance:** an entry in the site's `docs/DRILL-LOG.md` with the times, the
`observation_age_s` at each transition, and **what was actually seen** rather
than what was supposed to happen. Including, if it comes to that, that a
transition did not occur - which would be a defect found by the only method
that can find it.

## T55. The refusal does not say how long it waited
Status: **done at 0.26.0.0.** The refusal carries the elapsed seconds and the
exception class, measured in the transport with a monotonic clock and bounded
again in the command so a transport that does not time itself still produces a
duration. Four mutations verified red, including a constant elapsed figure,
which the data distinguishes because the regression asserts on two different
durations rather than on the presence of a number. [tier 1]

**What it unblocks, and what it does not.** T39's open hypothesis is packet
loss on the IPv6 path, whose signature is a stall of an order of magnitude
against a ten-second ceiling. One night of journal now separates that from a
fast rejection or a name-resolution failure by reading rather than by
argument. It does not answer the question by itself: the reading has to
happen, and that is a measurement on the host rather than work in this
repository.

*Original entry below.*

`[UNREACHABLE] <urlopen error timed out>` carries no elapsed time, so a stall
that hit the 10-second ceiling and a refusal that bounced in twenty
milliseconds are indistinguishable in the journal. Those are different
failures with different causes - a hung connection against a rejection or a
name-resolution error - and the journal cannot tell them apart.

**This is F44 in the diagnostics rather than in the schedule.** A probe whose
outcomes do not separate its hypotheses is not a probe, and eleven refusals
were logged before anyone noticed that the line answers no question.

**Acceptance:** the refusal line carries the elapsed seconds and the exception
class, a regression whose data distinguishes a fast failure from a slow one,
and a named mutation verified red. Then one night of journal, and T39's open
hypothesis is settled by reading rather than by argument.

**Deliberately not in scope:** a retry, a longer timeout, or a different poll
interval. Each would mask the symptom before its cause is known, and the
component in question is the one that decides whether the sky is being
watched.

## T56. Is there an alert feed for the Romanian border and the Baltics
Status: `ready` (own action, nobody's permission needed) [tier 3]

The Ukrainian channel this project reads is one country's civil defence
publishing in one place. **Whether anything comparable exists for the
Romanian border or for the Baltic states is unmeasured**, and the question is
worth an afternoon before it is worth an architecture.

**Why it is tier 3 rather than higher.** The product's thesis is distance to
the Polish border, and Romania and the Baltics are not on it. What they would
buy is a second observation of the same war from another angle, which is a
research question rather than a product one until the first is answered.

**What to look for, in the FEED-SPEC vocabulary** (section 3, the five
properties): a public endpoint, a stable schema, a stated update rate, a
version policy, and a failure that is distinguishable from silence. A
Telegram channel of a national service counts if it is public and
machine-readable in the same sense the Ukrainian one turned out to be.

**Named candidates to check rather than assume**: Romania's RO-ALERT and DSU
publications, and the Baltic states' national alerting arrangements, each of
which may be push-only to phones and therefore not readable at all. **A
negative result closes this task and is worth as much as a positive one**, in
which case it is recorded in `docs/FEED-SPEC.md` beside the Polish finding
rather than left as an open possibility somebody rediscovers.

**Acceptance:** each candidate measured against the five properties with the
date and the method, and the outcome written down either way.

## T57. A week of the picture: statistics a reader can open
Status: `ready`, needs T42 for its second half [tier 3]

A panel showing the last seven days: alerts per day, the split between west
and the rest, the distribution of threat kinds, and how much of the week the
collector was actually watching. That last number is the one nobody else
would publish and the one that makes the rest honest.

**The Jasionka half needs data this project does not yet have.** T42 is the
ADS-B measurement of the hub's operating intensity, and it follows T20's
OpenSky registration. A density chart of landings by hour, from military
transponder traffic, is a good rendering of it and D-019 already settled what
may be published: the aggregate, never the positions.

**A trap to avoid, and it is the reason this entry is not larger.** A
statistics panel is where a reporting instrument starts to look like an
analysis product. Counts of alerts are counts of *announcements*, not of
attacks, and a reader shown a bar chart will read attack intensity into it
unless every axis says otherwise. The panel is worth building only with the
collector's own uptime beside it.

**Acceptance:** counts computed from the contract rather than recomputed on
the consumer side, the collector's observed uptime for the same window shown
beside them, and each axis labelled with what it counts. The Jasionka chart
ships separately and only after T42.

## T58. Traffic and road conditions near the border: refused as posed
Status: `decision` recorded, no work planned [tier 3]

Requested 2026-08-12: road disruptions in the border area from Google Maps.
**Refused in that form**, and the reason is recorded so the request is not
rediscovered as an oversight.

The useful shape of that data is a live overlay, and a live overlay is either
the reader's browser talking to Google, which is exactly what the site's
D-S16 keeps refusing, or a server proxying a product whose terms do not allow
it to be redrawn on somebody else's map. Neither is a licensing detail that
could be worked around; both are the arrangement itself.

**What is available instead**, and it is a data question rather than a
privacy one: roads and railways drawn from vendored public-domain geometry,
which is T51 and carries a measured budget. Static roads answer "where would
somebody drive" and do not answer "is it blocked now", and the second question
is the one that was asked. So T51 is not a substitute, and this entry says so
rather than quietly delivering the cheaper thing.

**What would reopen it.** A public, non-tracking source of Polish road
incidents in the border voivodeships, which is the same shape of question as
T8a and would be measured the same way.

## T62. The identifier checks cannot see a suffixed identifier
Status: `ready`, follows D-030. [tier 2]

`ENTRY` in `tools/todo_index.py` is `^## (T\d+)\. (.+?)$`, so `T8a` and `T8b`
are not entries as far as this repository's tooling is concerned. Both are
open and both carry tier 2. The consequences are four, and none of them is
cosmetic:

1. The generated index does not list them, so the two counts at the top of
   this file describe fifty-eight of sixty headings.
2. `check_identifiers_are_unique`, added at 0.32.3.0 against exactly this
   class, would pass a file holding two `## T8a.` entries.
3. The tier check cannot report them as untiered, so the guarantee that an
   open task has been ordered does not cover them.
4. `check_sprint_agreement` does not see them either, so a suffixed task
   assigned to a closed sprint is invisible to the check written for that.

The same shape sits one document away: `docs/docs_audit.py` counts decisions
with `^## (D-\d+)` into a set, so `D-012a` collapses into `D-012` and the pin
holds over a file with one more heading than entries; and its citation
resolver is `\bD-\d{3}\b`, which cannot match a suffixed number at all, so a
dangling citation of `D-012a` would never be reported.

**Acceptance.** Both parsers admit an optional letter suffix, the index is
regenerated, and `decisions_recorded` is re-derived. Verified the way D-030's
check was: red against a planted suffixed collision before the widening,
green after. The counts this release quotes change with it, which is why the
work is separated from the release that found it rather than folded into it.

## T63. Tags are annotated and unsigned, and a document said otherwise
Status: `decision` [tier 3]

Measured 2026-08-17 across `v0.3.2.0`, `v0.20.0.0`, `v0.30.0.0`, `v0.32.0.0`
and `v0.32.4.0`: all five are annotated and carry no PGP signature. No key
exists on the operator's machine; `gpg --list-secret-keys` is empty and
`user.signingkey` is unset. The release procedure attempted `git tag -s` at
0.32.5.0 on the belief that signing was already the practice here, and failed
loudly, which is the only reason the belief was checked at all. **The belief
came from a document about this repository, not from the repository**, which
is F100's class turned inward.

**This is a decision and not work.** Signing is cheap to start and expensive
to start badly: a signed tag in the middle of an unsigned series is a question
a reader has to research rather than an assurance they can act on. The
authorship record this project already has, Software Heritage and
OpenTimestamps, is independent of it and is not weakened by tags being
unsigned.

**Acceptance:** an entry in `docs/DECISIONS.md` that either records signing as
deliberately out of scope with a reopen condition, or names the first version
from which tags are signed and states explicitly that every earlier tag is
not. Either answer closes this. What does not close it is a signed tag with no
entry.

## T64. A claim about a systemd unit quotes the unit
Status: `ready`, follows F106 [tier 2]

Three defects in one session share one mechanism: a conclusion about a file
that was not opened, drawn from a file that was (F102, F104, F106). The third
reached a tag and scheduled a deploy step that turned out to be unnecessary.

**What is checkable and what is not.** Nothing in this tree can read
`/etc/systemd/system`. What a check can do is refuse an *unsourced* claim, the
way `check_the_host_claim_is_no_older_than_the_release` refuses an undated one:
a sentence in `docs/DEPLOYMENT.md` naming a unit file, a directive or an
environment variable must sit within a block quoting `systemctl cat` or
`systemctl show` output, or it is a finding.

**Acceptance:** the check exists, is in `verify`, and is verified red against
the 0.32.7.0 text, which asserted `MAVO_LOG_FILE` was on one unit and not the
other with nothing quoted. An allow-list is permitted for prose that discusses
units in general rather than asserting their contents, and every entry on it
carries a reason.

**Why not in 0.32.8.0.** A lint written in the same hour as the defect it
targets encodes the instance rather than the class, which is F100's note. This
one has three instances to generalise from, which is an argument for writing it
soon rather than for writing it immediately.

## T65. Decide what a successful poll with no state change should render as
Status: `decision`, blocked by the S9 measurement (F107) [tier 1]

Ten minutes without a change of alert state produces `feed=degraded` while the
collector polls successfully every 33 seconds. A measured quiet is rendered as
a broken instrument. Tier 1 because it is on the page a reader is looking at.

**Input required before deciding**, and this is the blocker rather than the
work: the duty cycle of `ok` against `degraded` over the S9 window, per cycle,
with between-day variance, read from `publish.cycle` records in
`/var/lib/mavo/run.jsonl`. Eight minutes on 2026-08-17 gave 13 against 5, which
is an anecdote and is labelled as one in F107.

**The options, none obviously right and each with a cost:**

1. **A fourth feed state.** "Polled, nothing changed" as distinct from
   degraded. Honest, and it is a schema change the consumer must learn, so it
   needs a contract version and a decision on both sides of D-020.
2. **Poll outcomes in the store.** Freshness computed from observation rather
   than from events, which is what the word `newest_observation` already
   promises. Changes what the store is for and grows it by one row per poll.
3. **Leave the behaviour, change the sentence.** Cheapest, and it concedes that
   a reader is told to distrust an accurate picture roughly *n* percent of the
   time, where *n* is the number this task is waiting for.

**Acceptance:** a decision entry naming the chosen option, the measured duty
cycle it was chosen against, and a reopen condition. F107 closes with it.

## T66. Attempt completeness, as its own instrument
Status: `ready` [tier 1], **S9**

`tools/latency.py` reads the store, and the store by construction cannot tell
silence from blindness: a poll that never returned writes nothing, and a quiet
channel writes nothing, and the two are the same row count. The first framing
of this task was "add a continuity check to `latency.py`" and that framing was
wrong for exactly the reason the instrument exists.

Attempt completeness lives in journald and in `run.jsonl`, not in the store.
The distinction is `gaps` against `unobserved` in `mavo-adsb`, which measured
it first and can be read for the shape.

**Why it is tier 1.** `docs/CHANNEL.md` section 8a is empty and stays empty
until the latency tail is attributed, and the tail cannot be attributed
without knowing which minutes we were blind for. One term of a shipped
measurement rests on this.

**Acceptance:** a tool that reports, for a window, the attempts made, the
attempts that failed, and the stretches with neither, with the three counted
separately and unknown printed as unknown.


## T67. The RSO reader, and what it is a reader of
Status: `ready` [tier 2]

`mavo/sources/rso.py` parses the MSWiA feed run by TVP: pagination, the
communique fields, voivodeship scope, empty-versus-absent, and a conversion
that takes its zone from the caller and refuses an hour the zone maps twice.
It has no `poll`, no store, no timer and no caller.

**What remains, and it is not typing.** A page fetched over the wire rather
than from a fixture, a table of its own because a communique has a different
issuer, scope and lifetime from an alert and a shared `state` column is the
modelling error F25 recorded, and backfill as far as the endpoint pages.

**The number to expect before sizing this.** Pomorskie carried two messages on
2026-08-20 and Podkarpackie seventeen, dominated by storms and water levels.
The air-threat categories exist in the scheme and were not observed in the
sample. This is not a second alert stream.

**Acceptance:** communiques from the live endpoint in a table of their own,
with the timezone decision recorded, and a count of pages the endpoint offers.


## T68. Decide where, if anywhere, a Polish warning renders
Status: `decision` [tier 1]

Adding a Polish layer changes what this instrument's silence means. Today a
reader knows the map is a window onto Ukraine. Beside Polish warnings, an
absent warning reads as no warning, and this instrument is structurally later
than the statutory SMS already on that reader's phone. **A live warning layer
adds a way to be misled by absence and subtracts nothing.**

The version that adds something is the one the project lacks: a dated,
state-issued, territorially-scoped record that Poland treated a threat as
serious, sitting in the history as an outcome column rather than on the map as
an alarm. Every question about western episodes currently has no right-hand
side. 2026-08-18 supplies the first paired point.

**This is the operator's decision and nothing is built past the reader until
it is made.** T67 stops at a table; nothing renders.

**Acceptance:** a decision entry naming the surface, the words the page uses
to say this is not a warning channel, and a reopen condition.
