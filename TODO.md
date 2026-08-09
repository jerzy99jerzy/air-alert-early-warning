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

## T6. Legal position on distributing warnings to people other than the operator
Status: `decision`, **due at the beginning of September**. Parallel track, and the only dated item left in the plan: it is answered by counsel or it is not, and no engineering time shortens it (`docs/MVP.md` section 7).
Does not shrink by writing code. Needs counsel, not a sprint.
**Acceptance:** a written position in `docs/DECISIONS.md` with a named basis.
*Restated 0.7.0.0.* The original title asked about a private circle, which is
the intermediate tier and not the destination. The question that actually gates
Audience D is distribution to recipients the operator does not know, and the
answer to the narrower question does not imply the broader one. Asking counsel
the smaller question would have produced a correct answer to the wrong
question, which is the more expensive kind of mistake here (F53).

## T7. Onboarding probe from a clean clone
Status: `ready`, **S11**
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
Status: `ready`, **before S10**. No longer a budget calibration (D-014); it is now the question of whether recipients exist at all, which Audience B is gated on.
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
Status: `deferred` (D-015). Was a prerequisite for a drone alarm tier. Under a reporting thesis ADS-B is enrichment: valuable, not blocking, and outside the five sprints to beta.
Promoted from enrichment to prerequisite by the sprint 3 finding. Alert state
alone cannot discriminate within drone nights, so the drone tier stays silent
until another channel exists.
**Acceptance:** ADS-B activity over eastern Poland ingested as a `ThreatSource`,
and a drone-regime rule that clears its allocated share on the adversarial
history without lowering the recall floor.

## T15. Raion and hromada gazetteer
Status: **largely met at 0.10.0.0**, by a route nobody planned. The channel tags 99.34% of messages with the area and unit type, so the gazetteer is a 127-row lookup rather than a vocabulary to search (`docs/CHANNEL.md`). What remains is correctness on the message the tag sits in, which is S7's hand-labelled sample. Original text:
Status: `ready`, **S7, core**. Promoted from support to product by D-015: a report that cannot name the rajon is a relay. Superseded in method by T31, which supplies the register this task consumes.
F24. The channel names raions and hromadas; nothing in a message identifies the
oblast. Without a mapping, the border-oblast rules that the entire thesis rests
on have no input.
**Acceptance:** every area name appearing in a week of channel content resolves
to an oblast, or is reported as unresolved. Unresolved is never silently skipped.

## T16. Means of attack as its own message class
Status: `ready`, **S7**. Under the reporting thesis this is output rather than a feature of a rule: the report says what the channel names, with the source's wording preserved.
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
Status: `done` (0.5.5.0 retrieval, recorded at 0.6.0.0)
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
Status: `ready`, self-service, **not in the beta plan** (D-015). Registration is cheap and worth doing whenever; nothing waits on it.
Recategorised from a blocked external dependency: no approval step exists, only
the registration itself. It gates T14, which gates any drone-tier alarm (D-009),
and it costs minutes.
**Acceptance:** credentials stored outside the tree and one authenticated ADS-B
read over eastern Poland recorded with its latency.


## T22. Fail the build when a document cites an identifier the package lacks
Status: `ready`, **S11**
F55: `docs/COMPUTATION.md` cited a constant that does not exist, in the document
whose subject is that figures come from measurement. The audits check cited test
names and pinned counts; nothing checks the rest of the backticked identifiers.
**Acceptance:** `tools/docs_audit.py` extracts backtick-quoted names matching an
identifier pattern from `docs/*.md` and the README, and fails on any that appear
in no package source, with an explicit allow-list for names that are deliberately
hypothetical. Verified red by citing a fabricated symbol in a scratch copy.


## T23. The observability sink and its reader
Status: `ready`, **S9**
Blocks nothing today and blocks everything at M0: shadow mode's deliverable is a
record of decisions that were never sent, so the log is the product rather than a
diagnostic. Designed in `docs/OBSERVABILITY.md` with acceptance written before
the code.
**Acceptance:** the seven criteria in that document's section 9, each as a test.
The two that are not merely plumbing: identical JSONL under `-q` and `-vv`, and
a rendering that prints `unknown` where a stage could not measure, verified by a
fixture whose parse report has no baseline.

## T24. Keep the run log out of the holdout
Status: `ready`, **S9**
The design and holdout split was frozen before any message content was read
(D-012a). A run log echoing message bodies spends that split without anyone
deciding to spend it.
**Acceptance:** a hostile fixture carrying a recognisable token in every message
body produces no occurrence of that token in the sink under default settings,
and the debug switch that lifts this writes its own line into the record.


## T25. Decide where the daemon lives
Status: `decision`, **S9**
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
Status: `ready`
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
Status: `ready`, **S9**
A fixed 60-second period is both a beacon profile to a sensor and a perfectly
regular load on an upstream with which there is no agreement. Ten to twenty
percent jitter addresses both and costs one line. It goes in first because
adding it later invalidates every interval measurement taken before it, and
those measurements are the evidence that would justify tightening the poll.
**Acceptance:** the interval is drawn per cycle, the draw is recorded in the run
log, and the recorded distribution over 72 hours matches the configured range.


## T28. The crossing event list, dated and sourced
Status: `deferred` (D-015). Was blocking while crossings were the target
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
Status: `ready`, **S11**
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
Status: `ready`, **S7**. *Renamed 0.9.2.0: the register is КАТОТТГ, KATOTTG. The
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
Status: `ready`, **S8**
D-016. Distance is the field that turns an alert into a report a person can use,
and it must be a stored column rather than a runtime call: no API key in the
warning path, no rate limit where latency is the product, and no third party
learning which rajons a Polish user asks about at three in the morning.
**Acceptance:** one scalar per area, computed offline from OpenStreetMap
geometry, with the method and the geometry version recorded. A spot check
against a handful of known distances, verified by hand, before the column is
trusted anywhere.


## T33. Alias table between the channel and the register
Status: `ready`, **S7**
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
Status: `ready`, **S7**
321 of 48,540 design-window messages carry no `#Name_unit` tag and nothing says
what they are. They may be administrative posts, or they may be exactly the
messages that matter.
**Acceptance:** a hand-read sample of them, classified, with the finding
recorded either way. If any are alerting messages, the tag parse needs a
documented fallback and the 99.34% figure needs a caveat beside it wherever it
appears.


## T35. Turn the negative result into a measurement
Status: `ready`
The design window's four western-wide alert nights show no reported Polish
airspace violation, but the source is press coverage, and a single drone downed
without debris may never reach national media. Absence of evidence, not evidence
of absence, and the log says so.
**Acceptance:** the operational command's own published posts for 2026-04-29,
2026-05-28, 2026-05-29 and 2026-06-20 read and recorded, with the finding
entered either way. A confirmed quiet night on all four is a measurement; a
missed incursion on any of them is a more interesting one.


## T36. The hand-labelled sample, retargeted
Status: `ready`, **no longer blocking S7**. The sprint closed on an exhaustive
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

**Acceptance:** at least 50 design-window messages read by hand, each with the
resolved area recorded as correct or not, and the error rate stated as a number
with its interval, its seed and its fingerprint, recorded in
`docs/METHODOLOGY.md`.
An error rate above a few percent is a finding about the channel, not about the
map, and it is recorded either way. Until this exists S7 stays open and
`STATUS.json` does not claim otherwise in prose.


## T37. The pipeline discards areas it was told about
Status: `ready`, **S8**
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
