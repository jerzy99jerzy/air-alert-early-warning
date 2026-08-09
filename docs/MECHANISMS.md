# MECHANISMS

Every mechanism in MAVO: what it is, where it lives, the alternative that was
rejected, the failure it prevents, and the test that keeps it honest.

```
Document:  docs/MECHANISMS.md, version 2.0
Audience:  a contributor about to change how something works, and anyone asking
           "why is it done this way rather than the obvious way"
Companion: ARCHITECTURE (what talks to what), DATA-FLOW (what happens to a
           message), FOUNDATIONS (what any of it rests on), DECISIONS (what was
           rejected at project level)
Note:      every constant quoted here was read out of the code. Where a
           mechanism has never been exercised on real data, the section says so
           rather than describing it as though it had
```

## Contents

1. [The base rate is the whole difficulty](#1-the-base-rate-is-the-whole-difficulty)
2. [Lift, and why the gate never reaches it](#2-lift-and-why-the-gate-never-reaches-it)
3. [Fisher's exact test, one-sided](#3-fishers-exact-test-one-sided)
4. [The Wilson interval](#4-the-wilson-interval)
5. [The three gate conditions](#5-the-three-gate-conditions)
6. [Two timing regimes](#6-two-timing-regimes)
7. [The lift floor, and the budget it replaced](#7-the-lift-floor-and-the-budget-it-replaced)
8. [Demand allocation, which refuses rather than trims](#8-demand-allocation-which-refuses-rather-than-trims)
9. [Coverage gaps](#9-coverage-gaps)
10. [Poison suppression](#10-poison-suppression)
11. [Rules return a moment, not a boolean](#11-rules-return-a-moment-not-a-boolean)
12. [The conjunction, and why each conjunct is there](#12-the-conjunction-and-why-each-conjunct-is-there)
13. [Idempotence by content hash](#13-idempotence-by-content-hash)
14. [Transitions rather than snapshots](#14-transitions-rather-than-snapshots)
15. [Two timestamps on every event](#15-two-timestamps-on-every-event)
16. [Four alert states](#16-four-alert-states)
17. [The window gap, and why unknown is not zero](#17-the-window-gap-and-why-unknown-is-not-zero)
18. [Backwards paging and the id-range filename](#18-backwards-paging-and-the-id-range-filename)
19. [The advisory directory lock](#19-the-advisory-directory-lock)
20. [Six named stop conditions](#20-six-named-stop-conditions)
21. [The refusal taxonomy, and the absence of warnings](#21-the-refusal-taxonomy-and-the-absence-of-warnings)
22. [The one network seam](#22-the-one-network-seam)
23. [Executable claims](#23-executable-claims)
24. [Mutation-verified attacks](#24-mutation-verified-attacks)
25. [Provenance labels as a data type](#25-provenance-labels-as-a-data-type)

---

## 1. The base rate is the whole difficulty

**Where:** `mavo/baserate.py`, and everything downstream of it.

Every violation of Polish airspace in the observed period coincided with a night
of massed strikes on western Ukraine, which reads as recall 1.0. Those campaigns
cover roughly 57% of days, so a rule that fires on them has specificity near 0.43
and tells a reader almost nothing a calendar would not.

This is not a statistical nicety bolted on afterwards. It is why `baserate.py`
sits at the top level of the package rather than in a `stats/` subdirectory: a
contributor reading a directory listing should see immediately that the null
model is the product, and that the rules exist to be measured against it rather
than to be shipped. `tests/lint_domain.py` fails if it moves.

**What it prevents:** the whole project reducing to a well-engineered pipeline
that reproduces a calendar and calls it a warning system.

---

## 2. Lift, and why the gate never reaches it

**Where:** `RuleAssessment.lift` in `mavo/baserate.py`.

Lift is precision divided by the unconditional rate. A lift near 1.0 means the
rule added nothing over knowing the base rate. It is the single number that makes
the problem in section 1 visible without reading two others.

**It is computed and reported, and the gate never consults it.** The gate rejects
on alarm rate first, because a rule can be genuinely informative, with a lift of
1.8, and still be unusable at six alarms a week. Informativeness and usability are
different properties, and the gate is about the second.

**Rejected alternative:** gating on lift. It would let a rule buy its way past
the gate by being interesting, which is exactly the trade the lift floor
exists to refuse.

---

## 3. Fisher's exact test, one-sided

**Where:** `mavo/baserate.py`, implemented with `math.comb`.

**Rejected alternative: chi-square.** The positive class is roughly a dozen
events across four years, and the chi-square approximation is unreliable at those
counts. The exact test is a few lines of standard library.

**Rejected alternative: SciPy.** Adding a dependency for one statistic would
weaken a tool whose product is a measurement, because a measurement with an
unaudited dependency tree is weaker than one without. This is the whole of the
zero-runtime-dependency rule in one example.

**Why one-sided:** the question is whether the rule fires on event nights more
often than chance, not whether it differs from chance in either direction. A
two-sided test would also reward a rule that fires *less* often on event nights,
which is not a warning system but an anti-warning system.

**Constant:** `MAX_P_VALUE = 0.05`, published in the README gate table.

---

## 4. The Wilson interval

**Where:** `mavo/baserate.py`.

**Rejected alternative:** the normal approximation. At `a = 2, n = 40` the normal
interval runs below zero, which is not a probability and reads as false
precision.

Wilson stays inside the unit interval and is honest about asymmetry, which
matters most exactly where the data is thinnest, which is exactly where this
project operates. The interval is reported alongside every precision figure,
because a precision of 0.31 from 29 observations and a precision of 0.31 from
2900 are different claims and must not print the same way.

---

## 5. The three gate conditions

**Where:** `gate()` in `mavo/baserate.py`.

| Condition | Constant | Floor | Character |
| --- | --- | --- | --- |
| Recall | `MIN_RECALL` | 0.90 | A warning system that misses the event has no purpose |
| Lift, lower bound | `MIN_LIFT_LOWER_BOUND` | 1.50 | A control, not a metric. See section 7 |
| Association | `MAX_P_VALUE` | 0.05 | Distinguishes the rule from the calendar |

**Any failure is decisive.** There is no weighted score, no composite index, and
no configuration file that could turn one into a soft constraint. A composite
score lets a rule trade recall for association and arrive at a number that hides
which of them it failed.

**Every reason is recorded, including passing ones.** `GateVerdict.reasons`
carries a line per condition whether it passed or failed, because a verdict
listing only failures cannot be distinguished from a verdict that forgot to
check. This property is also what made F38 findable: an attack asserting on the
substring "alarm rate" matched the passing reason as well as the failing one.

`tools/manual_audit.py` fails the gate if a threshold quoted in the manual is not
the one the code enforces, so these three numbers cannot drift between the
documentation and the tree.

---

## 6. Two timing regimes

**Where:** `Regime` in `mavo/policy.py`.

A missile crossing from an alert in Lviv oblast is roughly six minutes at 700
km/h over 70 km. A drone crossing from Volyn is roughly thirty-three minutes at
180 km/h over 100 km. **Both figures are arithmetic on stated assumptions and are
labelled as inference wherever they appear, not as measurements.**

Regimes are defined by transit time rather than by munition taxonomy, because
what matters is how many minutes a warning buys, and that differs by roughly a
factor of five between the two.

**The consequence is structural, not cosmetic.** Sprint 2 measured a global
recall of 0.47 and recorded it as a mediocre rule. Sprint 3 probed what the
average hid: 7 of 7 on missile nights, 0 of 8 on drone nights. The rule was not
mediocre. It was perfect at one job and blind to another, and a single global
threshold cannot express that. Averaging across two populations produced one
number that described neither.

---

## 7. The lift floor, and the budget it replaced

**Where:** `lift_lower_bound` and `gate` in `mavo/baserate.py`.

**The load-bearing sentence: a rule must beat the calendar with confidence, not
merely fire rarely.** Through 0.7.x this slot held a ceiling of two alarms per
week, on the reasoning that a noisier channel trains its recipient to ignore it
and that an adversary can induce that at no cost. The reasoning is still
readable in D-007 and D-008; what it lacked was a measurement, and D-014 removed
it on those grounds.

What the ceiling was accidentally enforcing is that the firing must carry
information. Removing it exposes the gap immediately: a rule firing on every
campaign night has perfect recall and a p-value of 1e-03, and would pass. The
floor on the lower bound of lift closes that gap by stating the requirement
directly, and states it pessimistically because a positive class of twelve moves
a point estimate by a factor on one night.

**Rejected alternative: a floor on point lift.** Simpler, and wrong in the
direction that matters. A rule whose point lift is 2.0 with a lower bound of 0.9
has not been shown to beat the calendar at all, and at this sample size that
combination is ordinary rather than exotic.

**Rejected alternative: keeping the rate ceiling alongside the lift floor.**
Defensible, and it would have kept a control this project values. It was
rejected because the number remained unmeasured, and a hard constraint resting
on an unmeasured number is the pattern the whole repository exists to refuse.
The cost is written into D-014 rather than argued away here.

**Guarded by:** harness A4 (MT4), mutation-verified. Weakening the floor turns
A4 red.

## 8. Demand allocation, which refuses rather than trims

**Where:** `plan_policy` in `mavo/evaluate.py`, `mavo policy --allocation demand`.

Equal split gave each regime half the attention budget regardless of how often it fired. Recorded as history: the budget it divided was removed at 0.8.0.0 (D-014).
Demand allocation measures what each regime actually needs, adds 25% headroom,
and then either fits inside the total or **refuses**.

**Rejected alternative: trimming the shares to fit.** Trimming produces a policy
that runs, prints good numbers, and silently drops the alarms that did not fit
into the trimmed share. The refusal is the finding: measured demand exceeds the
recipient's attention, and the answer is to demote a regime deliberately rather
than let arithmetic demote it invisibly.

Exit code 1 from `mavo policy --allocation demand` is therefore the designed
answer, not a fault, and the manual says so in the troubleshooting table.

---

## 9. Coverage gaps

**Where:** `PolicyRun.unserved` and `has_coverage_gap` in `mavo/evaluate.py`.

A policy serving only the missile regime has recall 1.00 on the scope it serves
and leaves eight drone crossings unwarned. Those crossings are counted by kind,
exposed as a property, and printed as `COVERAGE GAP` in the summary.

**Rejected alternative:** removing unserved kinds from the denominator. That
produces a recall of 1.00 for a policy with a hole in it, printed identically to
a recall of 1.00 for a policy without one. Two different products, one number.

This is F8, and it is the clearest instance in the repository of the general
rule: **a system may have a gap, and may not have a gap it does not name.**

**Guarded by:** harness A6, mutation-verified.

---

## 10. Poison suppression

**Where:** `is_poisoned` in `mavo/rules.py`. Constants
`POISON_AREA_THRESHOLD = 8`, `POISON_WINDOW = 120 seconds`.

A source reporting eight or more distinct areas activating inside 120 seconds is
not describing weather. Every rule calls this first and returns `None` if it
trips.

**Rejected alternative:** a scoring penalty making a poisoned night less likely
to fire. A penalty is a soft control, and the attack it defends against is free:
an adversary who can induce alarms exhausts attention at no cost and disables the
system for as long as the flood lasts. A free attack gets a hard
control.

**Where the numbers come from:** they are thresholds chosen to be obviously
implausible rather than tuned. Eight simultaneous oblast activations inside two
minutes is not a pattern any real event produces. **They have never been
calibrated against real data**, and that is stated here rather than implied by
their precision.

**Guarded by:** harness A1, mutation-verified. Raising the threshold to 10,000
turns A1 red.

---

## 11. Rules return a moment, not a boolean

**Where:** the `Rule` type in `mavo/rules.py`,
`Callable[[Night], datetime | None]`.

A rule returns the moment it would have fired, or `None`. **Returning the
timestamp rather than a boolean is what makes lead time measurable.** A rule that
answers "yes" tells you nothing about whether the warning would have arrived in
time to matter, and in the missile regime the entire budget is about six minutes,
so a rule that fires correctly three minutes late has produced nothing.

This choice is why the evaluation layer can compute lead-time distributions
without any rule knowing that lead time exists.

---

## 12. The conjunction, and why each conjunct is there

**Where:** `conjunction` and `drone_conjunction` in `mavo/rules.py`.

| Rule | Fires when | Alone, it fails because |
| --- | --- | --- |
| `r1_border_active` | Any border oblast reports active | It fires on the majority of nights |
| `r2_westward_escalation` | Three or more areas activate within 90 minutes, trending west | It fires on campaigns that stop at the border |
| `r3_border_missile` | A border oblast is active and classified missile | It cannot distinguish a routine alert from an inbound raid |
| `r4_border_drone` | A border oblast is active and classified drone | Same, for the regime where classification is least reliable |
| `conjunction` | R3 **and** R2 | The only shape permitted to raise an alarm |
| `drone_conjunction` | R4 **and** R2 | Exists to be measured, not because it is expected to work |

**Each conjunct closes a specific failure of the others**, and that is the test
for adding a fourth: name the failure of the existing three that it closes. A
conjunct that merely improves a number is a threshold in disguise.

`drone_conjunction` is honest about its own prospects in its docstring. Nothing
in oblast-level alert state distinguishes a drone night that ends in a crossing
from one that does not, which is why the drone regime is demoted to observation
(D-009) and why the ADS-B channel became a prerequisite rather than an
enrichment.

**Constants:** `ESCALATION_MIN_AREAS = 3`, `ESCALATION_WINDOW = 90 minutes`.
Both uncalibrated against real data.

**The westward test is ordinal, not geometric.** `EAST_TO_WEST` is a ranked list
of areas, and R2 fires when the last activation ranks west of the first inside
the window. It is not a bearing and does not become one until a gazetteer exists
(T15).

**Guarded by:** harness A3, mutation-verified. Replacing the conjunction with R1
turns A3 red.

---

## 13. Idempotence by content hash

**Where:** `ThreatEvent.content_hash` in `mavo/schema.py`, `EventStore.append`
in `mavo/store.py`.

The hash covers area, state, source timestamp and source identity, and
**deliberately excludes ingest time**. Since 0.6.0.0 the timestamp is spelled
in UTC before hashing, so one instant reported under two offsets is one
transition (F52) - and the hash also excludes `kind` and the raw text, which is
a decision with its own entry: a reclassification of a transition is a better
reading, not a new event, and a corrected parser rebuilds a store from the raw
corpus rather than appending over an old one (D-013).

A feed polled every thirty seconds repeats an unchanged transition constantly.
Without this exclusion the log grows without bound, replay stops reconstructing
the past, and every backtest built on the log becomes quietly wrong while
continuing to produce plausible numbers.

**This is also the defence against MT8**, an adversary replaying one transition
with a fresh ingest time to inflate the log.

**Guarded by:** harness A8, mutation-verified. Adding `ts_ingest` to the hash
payload turns A8 red.

---

## 14. Transitions rather than snapshots

**Where:** `mavo/store.py`.

The store never holds "the current state of Ukraine". It holds the moments at
which something changed, and any past moment is reconstructed by replaying
transitions up to it.

**Two consequences that justify the cost:**

The backtest and a future live correlator run the same code path, so a rule
cannot behave differently in test than in production. A snapshot store would need
a separate historical reconstruction path, and two paths meant to agree are two
paths that will eventually disagree silently.

A schema change is a replay rather than a migration. There is no mutable
current-state table to ALTER, which matters for a project that has changed its
state model once already (F26) and will change its area model next (F24).

---

## 15. Two timestamps on every event

**Where:** `ThreatEvent.ts_source` and `ts_ingest` in `mavo/schema.py`.

`ts_source` is when the source says it happened. `ts_ingest` is when we learned
it. Both are always present.

**The difference is feed latency, and feed latency consumes the warning budget
directly.** In the missile regime the whole budget is about six minutes, so a
feed publishing three minutes late halves the product. A system storing one
timestamp could not tell a slow feed from a slow adversary, and could not report
that its own product had shrunk.

**Not yet measured on real data.** The first live latency measurement is owned by
sprint 6 and has not been taken.

---

## 16. Four alert states

**Where:** `AlertState` in `mavo/schema.py`, `classify_state` in
`mavo/sources/telegram.py`.

| State | Set when | Never |
| --- | --- | --- |
| `ACTIVE` | An alert-start marker matched | |
| `CLEAR` | An all-clear marker matched and no continuation marker did | |
| `PARTIAL_CLEAR` | Both an all-clear and a continuation marker matched | resolves to CLEAR, is actionable |
| `UNKNOWN` | The source has told us nothing about this area | resolves to CLEAR, is actionable |

**`is_clear` is affirmative, never a negation.** Written as a function rather
than `state != ACTIVE` at every call site, because the negation is the defect: it
silently folds every non-active state into safety.

**Why PARTIAL_CLEAR is not folded into UNKNOWN.** UNKNOWN means the source told
us nothing. PARTIAL_CLEAR means it told us two things that do not agree. A
contradiction is evidence about the source and silence is not, and evidence
discarded is evidence that cannot later be counted. The real message that forced
this announced an all-clear for a raion and said in the same message that the
alert continued there (F26).

**The partial check runs first and is decisive.** A message carrying both markers
is a contradiction, and the weaker reading has to win: a state meaning "we were
told the alert continues" must never be reachable from the branch meaning
"clear".

**The lint enumerates the enum rather than naming states**, so a fifth member is
covered on the day it lands. Naming states in the check is the version of this
that rots.

**Guarded by:** harness A2, mutation-verified, plus `test_sprint5.py`.

---

## 17. The window gap, and why unknown is not zero

**Where:** `TelegramChannelSource._window` in `mavo/sources/telegram.py`.

The channel page serves exactly twenty posts, measured. At rest a thirty-second
poll sees every one; during a mass alert the channel can emit more than twenty
between two polls, and the extras are simply gone. Nothing downstream would
notice, because a message never fetched and a message never sent produce
identical silence.

Post ids make the difference observable. Consecutive polls compare the lowest id
of this page against the highest id of the last.

| Case | `skipped` | Why |
| --- | --- | --- |
| Previous poll exists, ids present | a count | Measured |
| First poll of this source | `None` | No baseline exists. Zero would be a claim |
| No ids on the page | `None` | The observable is gone |

**The load-bearing half is the third row.** Losing the ability to measure must not
look like measuring calm. Printing zero there would make an unmonitored window
indistinguishable from a monitored quiet one, which is UNKNOWN resolving to CLEAR
one layer out from the state model.

**Two regexes, deliberately independent.** The message regex and the post-id
regex run over the same body without sharing a match. A page restructuring that
breaks one does not silently take the other with it, so "we cannot read the
messages" and "we cannot see the window" stay distinguishable.

**Guarded by:** harness A11, mutation-verified. Defaulting `skipped` to 0 turns
A11 red.

**Current limitation:** no command is resident, so `mavo collect` has no previous
poll and prints `skipped=unknown` every time. The count becomes a measurement
under `mavo watch`, which does not exist.

---

## 18. Backwards paging and the id-range filename

**Where:** `mavo/backfill.py`.

The web preview accepts a `before` cursor and pages backwards through history,
twenty posts at a time. This was believed impossible for two sprints on the
strength of a probe that could not fail (F44).

**Snapshots are named by id range, not by fetch time:**
`page-000260841-000260860.html`. The same page fetched twice is one file, which
is the idempotence principle of section 13 applied to a different medium. Naming
by clock time would turn idempotence into duplication and make a resumed run
indistinguishable from a duplicated one.

**Contiguity is computed from filenames**, so a hole is visible without opening
anything. Holes are printed with range and size and carry exit code 5, because a
census with holes it cannot see is a sample that believes otherwise.

**It parses nothing beyond post ids.** The corpus exists because the pattern
table is wrong; a corpus filtered through that table would be evidence about the
table rather than about the channel.

**Measured on 2026-08-09:** page size exactly 20, newest id 321519, backwards
paging confirmed with a cursor inside the live id range. 0.2 s between requests
was clean over a burst of twenty, and the default stays at 1.0 s because a burst
of twenty does not license a claim about a run of 2800.

---

## 19. The advisory directory lock

**Where:** `DirectoryLock` in `mavo/backfill.py`, exit code 6.

A lock file carrying the holder's pid. Advisory rather than enforced: it guards
against the operator starting a second run, which is what happened (F47), and not
against an adversary.

**Two runs against one directory do not corrupt the corpus**, because snapshot
names derive from id ranges and the second writer produces identical bytes. What
they do is double the request rate against a service whose tolerance is measured
only over a burst of twenty.

**A stale lock from a killed process is taken over, not refused.** A control
requiring a manual cleanup step nobody remembers at 02:00 is a control that gets
deleted by reflex, and a deleted control protects nothing.

---

## 20. Six named stop conditions

**Where:** `BackfillReport.stopped_because` in `mavo/backfill.py`.

Page count exhausted; `--stop-at-id` reached; a page carried no posts; a page
failed to move backwards; the source became unreachable; **the operator
interrupted it**.

The sixth was added in 0.5.3.0 after `KeyboardInterrupt` travelled through the
loop and a run that had retrieved 1150 pages reported a stack trace instead of
saying so (F46). The general lesson is in the defect log: every one of the
original five is a condition the *channel* produces, and the operator was not
modelled as a source of endings at all.

**A page that fails to move backwards is a refusal rather than a retry.** The
alternative is a loop that fetches the same page until the page count runs out
and then reports a page count that is true and a coverage that is not.

---

## 21. The refusal taxonomy, and the absence of warnings

**Where:** `mavo/errors.py`.

Every failure is a refusal with a type. **There is no warning type in this
codebase**, and that is a design decision rather than an omission: a warning is a
failure the caller is permitted to ignore, and every ignorable failure in this
domain is a silent one.

The taxonomy separates two things a caller must never confuse.
`SourceUnavailable` means the source could not be reached, and it is raised only
for reachability; content failures never produce it. A caller catching it knows it
has an outage, not an empty sky (MT11).

**Exit codes carry the distinction to a shell**, because a cron wrapper cannot
catch a Python exception:

| Code | Meaning |
| --- | --- |
| 0 | Ran, and the result is what it says |
| 1 | A designed refusal, such as an unreachable source or a naive timestamp |
| 3 | The source was unreachable |
| 4 | A snapshot could not be written |
| 5 | The corpus on disk has holes |
| 6 | Another run holds the output directory |

**Guarded by:** harness A10, mutation-verified. Catching `SourceUnavailable` and
returning an empty body turns A10 red.

---

## 22. The one network seam

**Where:** `mavo/transport.py`, the only module in the package that imports a
network client.

**Three properties bought by one constraint.** A reader can answer "what can this
thing talk to" by reading one file. Every adapter is testable without a network,
by injection. And the claim is registered in `tests/lint_limitations.py` as
`network_reach_is_one_file`, so the gate fails if a second module imports a
client.

**The transport refuses in exactly one way.** Every library-specific exception
becomes `SourceUnavailable`, so no caller needs to know which HTTP library is
underneath. A transport leaking `urllib.error.URLError` forces the coupling this
protocol exists to prevent.

**Bounds:** `DEFAULT_TIMEOUT_S = 10.0`, `MAX_BYTES = 4_000_000`. Decoding is
UTF-8 with `errors="replace"`, because a parser that raises on a malformed byte
turns hostile content into an outage (MT7).

**The User-Agent derives from `__version__`** rather than being typed, after
shipping a hardcoded `mavo/0.3.0.0` at 0.3.1.0 (F36).

**Stated limit:** that a live service returns what the tests assume is **not**
tested here. The tests exercise adapters against an injected transport, and the
limit of that is written into the module docstring rather than left implied.

---

## 23. Executable claims

**Where:** `tests/lint_limitations.py`, five claims, run by `make verify`.

Every bullet in the README's "What this will not tell you" section is registered
as a check. A claim the repository makes about itself either has a check in the
same commit or does not go in.

| Claim | Checks |
| --- | --- |
| `no_probability_claim` | No probability of impact is computed anywhere |
| `no_excluded_covariate` | A covariate excluded by measured null (D-002) appears in no package source |
| `unknown_not_clear` | No state other than CLEAR reads as clear, enumerated over `AlertState` |
| `no_ml_dependency` | No machine-learning dependency is declared |
| `network_reach_is_one_file` | Exactly one module imports a network client |

**This is the founding defect of the portfolio, in one mechanism.** ANANKE's
README described a protection the tree did not implement, and it survived because
prose is not executable.

**The honest measure of how far this reaches:** four of this repository's own
defects (F32, F33, F42, F43) are the same class, found in documents the lint does
not cover. It covers registered claims and nothing else. `tools/docs_audit.py`
extends the idea to cross-document references by resolving every cited test name,
which caught a citation that had been wrong for three releases.

---

## 24. Mutation-verified attacks

**Where:** `tools/harness_mutation.py`, in `make verify`.

One scripted attack per threat-model row. **A green attack is not evidence that a
control holds**, because an attack that asserts nothing is also green. So each
control is disabled by a textual substitution in a scratch copy of the tree, and
the attack guarding it must go red.

**The first run killed 7 of 10.** The three survivors were defects in the
attacks: one whose assertion was satisfied by the failure it was meant to detect
(F38), one that never reached the code it tested because its fixtures used the
wrong quote character (F39), and one written the same afternoon that tested the
governing decision on the one path returning before it (F40).

**One attack of eleven carries no mutation and is printed as unverified on every
run.** A7 exercises the fixture source, which generates rather than parses, so any
mutation making it raise is an injected fault rather than a removed control.
Stating that is cheaper than a mutation that flatters the count.

**A stale mutation is reported, not skipped.** If the text a mutation substitutes
no longer exists, the attack is unverified until the mutation is rewritten, and
the tool says so rather than passing quietly.

**Cost:** roughly 7 seconds of the gate's 11. It is in `verify` rather than
beside it, because a check outside the gate is a check that does not run, and
this one had already been deferred twice.

---

## 25. Provenance labels as a data type

**Where:** `Provenance` in `mavo/schema.py`, and the label convention throughout
the documentation.

Four labels: measured, reported, inference, speculation. The distinction carrying
the most weight in this domain is the first two. **Nothing in this system observes
airspace.** Every alert state is a claim by a source, and the code labels it
`reported` at ingestion rather than at display, because a pipeline that loses the
label in the middle produces a display that cannot recover it.

**The label is on the event, not on the report.** A report can be regenerated; an
event that arrived unlabelled cannot be relabelled honestly afterwards.

The same convention governs prose. Every load-bearing claim in this repository's
documents carries one of the four, and the defect log contains an entry (F49) for
a number stated in conversation without one.
