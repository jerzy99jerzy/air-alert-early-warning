# DECISIONS

```
Document:  docs/DECISIONS.md, version 2.6
Audience:  a contributor about to propose something that was already rejected,
           and anyone asking why an obvious approach was not taken
Companion: MECHANISMS (decisions at the level of one mechanism), FOUNDATIONS
           (the assumptions underneath), METHODOLOGY (what went wrong anyway)
Note:      every entry carries what would reopen it. A decision without a reopen
           condition is a preference wearing a decision's clothes
```


One entry per decision, including the ones that felt obvious. The last field is
the one usually omitted and the one that keeps a decision from becoming dogma.

## D-001. Codename in documentation, descriptive slug, unique namespace
Date: 2026-08-05. Status: adopted

**Decision.** The repository slug is `air-alert-early-warning`, the import
namespace is `mavo`, and the codename MAVO lives in documentation.

**Reasoning.** A slug is a search term and should be boring. An import path is a
namespace and must be unique rather than descriptive; five generic top-level
packages in an earlier repository planted five collision candidates in
`site-packages` on every install. The codename carries the thesis and belongs
where a reader is already reading prose.

**What would change this.** Publication to PyPI under a name collision, or a
decision to ship several related tools that should share a namespace prefix.

## D-002. A covariate that measures null is excluded, not merely unused
Date: 2026-08-05. Status: rejected (the covariate), adopted (the rule it set)

**Decision.** A candidate covariate that has been tested against the
attack-density series and returned a null does not enter any rule, score or
feature afterwards. The exclusion is enforced by `tests/lint_limitations.py` at
the term level, and the excluded terms are enumerated there rather than in the
documents: a guard has to name what it forbids, and that is the only place the
requirement applies.

**Reasoning.** The case that set this rule was tested on the full series, not a
subset: 738 attack nights, 87,093 munitions, September 2022 to April 2026.
Rayleigh R = 0.013, p = 0.95 on the directional test; Spearman correlation with
intensity r = +0.03, p = 0.44; mean covariate value on attack nights 49.1%
against a population mean of 50.1%. Three tests, one series, no effect at any
of them.

The general rule matters more than the instance. A variable that has been
measured to nothing is not neutral to leave lying around: it stays plausible,
it stays easy to reach for when a rule underperforms, and the next person to
reach for it will not repeat the measurement. Excluding it mechanically costs
one lint and removes a whole class of future argument.

**What would change this.** A published mechanism tied to a specific guidance or
acquisition mode, plus a pre-registered test on data not used to generate the
hypothesis. A fresh correlation found by searching the same series does not
qualify and is the exact failure being guarded against.

## D-003. Explicit rules, not a learned model
Date: 2026-08-05. Status: adopted

**Decision.** Rules are hand-written predicates with thresholds in
configuration. Runtime dependencies stay empty.

**Reasoning.** The positive class is roughly a dozen events across four years.
Any model fitted to that reproduces the overfitting that invalidated the first
analysis, and is unauditable besides. Explicit thresholds are falsifiable.

**What would change this.** A positive class in the hundreds, from a real
multi-year dataset with independent validation, and a use case where a human
cannot inspect the decision.

## D-004. Not a competitor to the state alerting system
Date: 2026-08-05. Status: adopted

**Decision.** No pursuit of mass adoption. The tool is positioned one step
earlier in the chain and says so.

**Reasoning.** The announced government application inherits a fourteen-million
user base and official authority. More importantly it is fed by the same
detection chain as the sirens, so its latency floor is the moment of detection.
This tool reads a feed from before the border, which is a different point in the
chain rather than a competing product. A state actor also cannot tolerate false
positives at that scale, which permanently leaves the early and uncertain niche
vacant for structural rather than technical reasons.

**What would change this.** The state channel publishing an ingestible upstream
feed, which would make the early tier redundant rather than complementary.

## D-005. No web UI, no mobile client
Date: 2026-08-05. Status: adopted

**Decision.** The first output channel is a Signal bot reusing existing
infrastructure. No browser interface.

**Reasoning.** A mobile client is a sprint of work that tests nothing about
whether the signal is worth delivering. Recorded because it is obvious now and
will not be in three months.

**What would change this.** A recipient group that cannot use Signal, or a
requirement to display geography that a text message cannot carry.

## D-006. Apache-2.0
Date: 2026-08-05. Status: adopted

**Decision.** Apache-2.0, matching `phantomatics`.

**Reasoning.** The portfolio currently carries three licences with no stated
reasoning, which is the first thing a partner asks about. This repository is
defensive tooling with no commercial dual-licence intent, and the patent grant is
worth more here than copyleft would be.

**What would change this.** A commercial offering built on the same tree, which
would make the `phantomatics` AGPL-plus-commercial split the better model.

## D-007. Alarm rate is a hard control, not a quality metric
Status: **superseded by D-014 (0.8.0.0).** Left in place with its reasoning intact: a decision log that deletes a superseded entry loses the ability to show what was believed and why.

Date: 2026-08-05. Status: adopted

**Decision.** A rule exceeding two alarms per week fails the gate outright,
regardless of precision, recall or lift.

**Reasoning.** Above that rate the audience learns to ignore the channel, which
destroys the product's only function. It is also an attack: an adversary who can
induce sub-threshold conditions can exhaust attention for free.

**What would change this.** Measured recipient behaviour showing tolerance for a
higher rate, which is an empirical question and not a preference.

## D-008. One shared alarm budget, allocated by measured demand
Status: **superseded by D-014 (0.8.0.0).** Left in place, same reason.

Date: 2026-08-06. Status: adopted

**Decision.** The two alarms per week limit is a property of the recipient. Rules
divide one total rather than each holding their own, allocation follows measured
firing rate with headroom, and an allocator that cannot fit the demand raises
instead of trimming.

**Reasoning.** Two rules each cleared at the full budget produce twice the budget,
which is the number that destroys the channel. Trimming a share silently to make
the sum fit yields a policy that passes its own gate and overruns the person it
is meant to serve, which is worse than a policy that refuses to exist.

**What would change this.** Measured recipient behaviour showing a different
tolerance, or a delivery channel where alarm cost is not attention (a dashboard
rather than a push).

## D-009. Drone regime demoted to the observation tier
Date: 2026-08-06. Status: adopted, provisional

**Decision.** Only the missile regime may raise a critical alarm. The drone
regime runs silent, and the coverage gap is declared in the output rather than
hidden by scoping the denominator.

**Reasoning.** The two-regime policy recovers full recall but leaves 2% of the
attention budget spare, which is not a margin. The drone rule buys its recall by
firing often, because nothing in oblast-level alert state separates a drone night
that ends in a crossing from one that does not.

**What would change this.** A second signal type that discriminates within drone
nights. ADS-B activity over eastern Poland is the leading candidate, which is why
that work is now a prerequisite rather than an enrichment. Real data showing the
discriminator exists in the alert stream after all would also reopen it.

## D-010. Both Ukrainian feeds are one dependency, accepted with open eyes
Date: 2026-08-08. Status: adopted

**Decision.** alerts.in.ua, api.ukrainealarm.com and the public Telegram channel
are treated as a single correlated dependency, not as independent sources.
Two-source agreement between them is never counted as confirmation (MT9). Access
to both APIs is revocable without cause or notice, and the ukrainealarm offer
contract changes unilaterally by being reposted (MT10, T12); the dependency is
accepted on those terms because no alternative feed of Ukrainian alert state
exists at this latency.

**Reasoning.** All three surfaces draw on the same upstream alerting chain, so a
wrong or silent upstream is wrong or silent everywhere at once. Multiple sources
protect against transport failure only. Pretending otherwise would let a
correlated failure masquerade as consensus, which is the exact class of
flattering default this repository is built against. The revocability is a legal
fact of the accepted contract, reviewed in full before acceptance, not a risk
discovered later.

**Which surface is upstream of which is not established.** The working model,
that the channel feeds the APIs, is an inference from public statements, not a
measurement. The correlation conclusion holds under any internal topology; the
relative latency of channel versus APIs does not, and is measured in sprint 6
rather than assumed.

**What would change this.** Either service moving to its own independent
acquisition; the ADS-B channel landing as a genuinely independent observation
(T14); or a Polish source with a stated availability commitment (T8a), any of
which would demote this from an accepted single point of failure to one input
among several.

## D-011. The classifier redesign waits for the corpus, not for the schedule
Date: 2026-08-09. Status: adopted

**Decision.** Sprint 5 was scheduled as the pattern-table redesign and did not
run it. The redesign waits until at least a week of real channel content exists
(T19). Sprint 5 instead built the parts of the source layer that determine
whether that content, once collected, can be trusted: the fourth state and
window-gap detection.

**Reasoning.** The table can only be rewritten against observed content, and the
only content in hand is twenty messages from twenty minutes of one evening,
covering four eastern oblasts and no western one. Fitting to it would reproduce
F23 at a smaller scale, which F28 already refused once. Meanwhile the corpus has
a property the code does not: it can only be collected forward in time, because
the page is a twenty-message window. *(Recorded as reasoned, and later found
false: the preview pages backwards, F44. The decision's conclusion - wait for a
corpus rather than fit to a sample - survived its wrong premise; the schedule
built on the premise did not, and 0.5.0.0 reordered it. Left in place because a
decision log that edits its own reasoning after the fact is a changelog of
opinions.)* A week spent redesigning against a sample
is a week the corpus is not being collected, and an undetected skip during a
mass alert would put holes in it that nothing downstream could see.

**What would change this.** Seven consecutive days of snapshots with gap
statistics, split into a design window and a holdout window. A gazetteer arriving
sooner would change what the redesign can attempt but not when it should start.

**What this costs.** The alarm tier cannot ship in September either way, because
border crossings run at two to four a year and no four-week window validates
recall. The schedule in `docs/MVP.md` is amended rather than quietly slipped.

## D-012. The corpus is split before it is read, and the rule is written down first
Date: 2026-08-09. Status: adopted

**Decision.** The design window is everything the classifier redesign may look
at. The holdout is everything it may not, until the redesign is frozen. The
boundary is a post id, chosen before any message content is read, and recorded
here: **the holdout is the newest 20% of posts by id in the corpus at the moment
the redesign begins.** Newest rather than oldest, because the redesign must be
tested against the channel as it writes today, not as it wrote in 2023.

**Reasoning.** This project already abandoned one analysis for fitting to noise.
The corpus removes the excuse that there was nothing to fit to, and replaces it
with the harder problem: with hundreds of thousands of messages it is possible to
iterate a pattern table until it scores well on everything it has seen and
nothing else. A holdout chosen after looking is not a holdout, and a holdout
chosen by a rule written after the first disappointing result is worse, because
it comes with a story.

**What this costs.** A fifth of the corpus is unavailable during the work that
needs it most, and the first honest score arrives only once. If the frozen table
scores badly on the holdout, that is the finding, and the response is a recorded
defect and a new sprint, not a second look.

**What would change this.** Nothing about convenience. A change in what the
channel emits, a restructuring that makes the newest fifth unrepresentative of
the near future, would justify moving the boundary, and would be recorded as a
scope change with its reason before the new boundary is used.

## D-012a. The boundary, computed and frozen
Date: 2026-08-09. Status: adopted, applies D-012

The corpus was retrieved on 2026-08-09: post ids 260841 to 321520, 60,680 posts
across 3,034 pages, spanning 2026-04-13 to 2026-08-09, contiguous with no
holes. The boundary below was computed from those ids **before any message
content was read**, which is the only property that makes it a holdout rather
than a test set chosen with hindsight.

| Window | Post ids | Posts | Share |
| --- | --- | --- | --- |
| Design | 260841 to 309380 | 48,540 | 80.0% |
| Holdout | 309381 to 321520 | 12,140 | 20.0% |

The boundary falls on a page edge because a page is the indivisible unit on
disk. That is why the split is 80.0% rather than exactly 80%.

**Frozen.** Moving this boundary after seeing a result is not a refinement, it
is the null result this project was built around, repeated with more data. If the
frozen table scores badly on the holdout, the response is a recorded defect and
a new sprint.


## D-013. The event store is a derived artifact, versioned by its parser

Date: 2026-08-09. Status: adopted

`content_hash` deliberately excludes `kind` and the message text: identity means
"this area entered this state at this moment according to this source". A
reclassification of the same transition - the exact thing the sprint-7 redesign
will produce for every message the 0/20 table misread - is a better *reading* of
an event, not a new event. Under `INSERT OR IGNORE` that has a sharp
consequence: appending re-parsed events to a store built by the old parser
silently keeps the old rows and drops every corrected one. The store would
preserve the defect the redesign fixes, invisibly, at the moment of fixing it.

The decision is not to widen the hash. Widening it to cover `kind` or the text
makes every parser improvement mint new identities, so a re-ingest *duplicates*
history instead of correcting it - the same defect with the opposite sign.

The decision is to name what the store is. **The raw page corpus is the
evidence; a store is a reading of it, and a reading is versioned by the parser
that produced it.** A new parser writes a new store from the raw corpus; it
never appends over an old parser's rows. This is already how the repository
works - `backfill` writes pages and nothing else precisely so parsing can happen
"later, from disk, as many times as the redesign needs" - so the decision
records the practice and closes the one path that contradicts it.

Trigger to reopen: a live, append-forever deployment where rebuilding from raw
pages stops being cheap. At that point a `parser_version` column and a stated
migration rule replace this convention, in the same release.


## D-014. The attention budget is removed; a lift floor takes its place
Date: 2026-08-09. Status: adopted, superseding D-007 and D-008

**Decision.** The two alarms per week limit is removed. It is no longer a gate
condition, no longer a constant in `mavo/baserate.py`, and no longer an
allocation refused at policy construction. The gate keeps three conditions:
recall at or above 0.90, **the lower bound of lift at or above 1.5**, and a
one-sided Fisher p at or below 0.05. The alarm rate is still computed and still
printed, labelled as measured and not gated.

**Reasoning, in the operator's words and not softened.** The budget encoded an
assumption about how a recipient behaves at a given notification frequency, and
nobody had measured it. Users who care will leave the tool on and moderate the
push settings themselves; users who do not will mute it and open it when they
are worried. Modelling that behaviour from an armchair and then hard-coding the
model as a refusal is the same error this project refuses everywhere else: a
plausible mechanism, encoded before measurement.

**What the budget was accidentally doing, and what replaces it.** With the
alarm-rate condition removed, a rule firing on every campaign night has perfect
recall and a p-value of 1e-03, so it passes on the two remaining conditions
while telling the recipient nothing they did not have from the calendar. The
budget had been serving as an accidental proxy for "the firing must carry
information". The lift floor states that directly, and states it at the *lower*
bound of the precision interval rather than the point estimate, because with a
dozen positive events a point lift moves by a factor on one night either way.
On the measured scenarios: a rule firing on 57% of nights reaches a lower bound
of 1.01 and fails; on 30% it reaches 1.92 and passes; on 14% it reaches 3.70.

**What was lost, stated plainly rather than argued away.** Alarm fatigue as an
attack surface is no longer refused by construction. An adversary able to
induce firings can no longer be stopped by a rate condition; what remains is the
poison check, the lift floor, and the recipient's own notification controls. The
author considers this an acceptable trade because the removed control rested on
an unmeasured number. This paragraph exists so that a future reader can weigh
that trade rather than discover it.

**Measured consequence, recorded rather than tuned.** On the adversarial
synthetic history, `R1-border-active` now passes the gate at 2.52 alarms per
week with a lift lower bound of 1.69. Through 0.7.x nothing passed. The margin
over the floor is thin, and the history is synthetic, so this is a statement
about the machinery and not about the world.

**What would change this.** A measurement. If mute and unsubscribe rates are
recorded once the channel exists and show that recipients disengage above some
frequency, that frequency returns as a condition with a number behind it. The
successor to T11 is that measurement rather than two conversations.


## D-015. The tool reports a picture; it does not predict a crossing
Date: 2026-08-09. Status: adopted

**Decision.** The product is a real-time situational report about the threat
picture on the Ukrainian side, with area resolution and distance to the Polish
border. Predicting a crossing is out of scope, permanently, and no output may be
phrased so that a reader can mistake one for the other.

**Reasoning.** A crossing is the outcome of processes none of the available
feeds observe: interception, where debris of an intercepted munition falls,
navigation failure, and an adversary's choices minutes earlier. A predictor
trained or tuned against roughly a dozen positive events would be fitting to
noise generated by mechanisms it cannot see, which is the failure this project
was founded on refusing. Reporting what is happening now, faster and more
completely than anything else available to a private person, is both achievable
and useful, and it is what the observation of 30 July showed to be missing.

**The figure this decision originally cited was wrong, corrected 2026-08-10.**
It said the episode lasted thirteen minutes. Checked against reporting: the
object was detected in Polish airspace at 03:40 and disappeared from radar at
03:46, six minutes later, near Tarnawa-Kolonia in Lubelskie `[reported;
Dowodztwo Operacyjne RSZ via Polish press]`. No source found supports thirteen.
The number had been carried in this repository unsourced since the decision was
written.

**The correction strengthens the decision rather than weakening it.** Six
minutes is less room, not more, and the same reporting supplies something the
decision only asserted: Ukrainian fighters were pursuing the missiles up to the
Polish border and their radar signature was hard to separate from the missiles
themselves, which delayed identification. That is the mechanism D-015 names as
unobservable, described from the other side by the people who were watching it
happen.

**What this changes, and it is more than wording.** The dozen crossings stop
being the target variable, so T28 stops blocking and the corpus no longer needs
to be long enough to contain them. The 57% base rate stops being the number to
beat. The gate, with recall, lift and Fisher, applies to an alarm class alone,
if one is ever built; the reporting tier is judged on correctness, latency and
completeness, all measurable on the corpus in hand. Area resolution stops being
a supporting gazetteer and becomes the core of the product (D-016).

**What would change this.** Evidence that a specific, mechanically explicable
precursor is observable in the feeds and precedes crossings, pre-registered and
tested on data it did not generate. Not a correlation found by searching the
same series.

### D-015, revision 1. From reporting instrument to warning infrastructure
Date: 2026-08-10. Status: adopted. The text above stands as the record of the
earlier position; this revision supersedes its framing and not its boundary.

**Decision.** MAVO is designed as an element of warning infrastructure rather
than solely as a situational reporting instrument. The design target is to be
the best available warning channel on the interval *before* a potential
crossing, judged on its own merits rather than against what the sirens, the RCB
text alerts or the RSO application do. Good situational awareness is the
product; latency is a property of it, not an enrichment of it.

**What does not change, and it is the part that matters.** The epistemic
boundary above holds in full. MAVO does not predict crossings; the 0 of 22
result stands, and no output may be phrased so that a reader can mistake a
report for a prediction. Being a warning channel means delivering the Ukrainian
picture faster and more legibly than the alternatives, not claiming to know
what crosses. `docs/FEED-SPEC.md` section 6 says sirens remain the fastest
channel to a sleeping person; that describes a different interval, after a
crossing and inside Poland, and is not in tension with this revision.

**What changes.**

1. **Silence becomes a liability rather than a gap.** A reporting instrument
   that goes quiet has missing data. Warning infrastructure that goes quiet is
   telling its reader the sky is calm. Heartbeat, staleness on the face of the
   output, and an explicit blind state move from backlog to core requirement.
   `docs/FEED-SPEC.md` section 4 was written about the Polish feed that does
   not exist; it now applies to this project's own output.
2. **Latency becomes a measured property end to end**, from channel post to
   state to rendered page. T39, T40, T41 and D-018 move from a backlog thread
   into the core. The MTProto latency claim in T41 stays
   `[inference, unmeasured]` until it is measured: infrastructure does not get
   to assume its own speed.
3. **T11 is a blocker rather than a formality.** Two conversations with
   recipients is the floor before shadow mode, not a box to tick.
4. **T6 escalates from a September date.** The distance between what the tool
   claims and what a reader does with it at half past three is a design
   surface, not a legal afterthought.
5. **Public framing follows.** Once this ships, no description of the project
   as pure reporting is accurate. The notifications sentence removed from the
   LinkedIn draft is a temporary hedge to revisit rather than a settled
   position.

**Reasoning.** Stated by the operator on 2026-08-10: sirens fail by reach and
audibility; machine data fails differently, by a silence that looks like calm.
That asymmetry is the one this repository documents about itself (F69, and
FEED-SPEC section 4), so accepting it as a design constraint is consistent
rather than novel. Designing to be best-possible on the pre-crossing interval
is the honest version of what the project was already doing, and the
reporting-instrument framing was in part a hedge against a responsibility now
explicitly accepted.

**What would change this.** T11 surfacing recipients who treat the output as a
take-cover signal despite the framing, which would reopen whether this posture
is tenable without institutional backing. A regulatory development making an
unofficial warning channel untenable for a private operator in Poland. Or
shadow-mode measurement showing end-to-end latency cannot in fact beat the
channels this means to precede, in which case the claim is withdrawn from the
framing rather than softened in it.

## D-016. Geocoding is a versioned file, not a service call
Date: 2026-08-09. Status: adopted

**Decision.** Area resolution uses the Ukrainian state administrative register
(KATOTTG, КАТОТТГ, successor to KOATUU) as a file in the repository, joined to centroids
and boundaries from OpenStreetMap. Distance from each area to the Polish border
is computed once, offline, and stored as a column. No geocoding API is called at
runtime, by this or any other provider.

**Reasoning.** A commercial geocoding API would produce the same numbers and
would add three things this project refuses: a runtime dependency and an API key
in the warning path, a rate limit on the one path where latency is the product,
and a third party who learns which rajons a Polish user is asking about at three
in the morning. A file has none of those, is auditable, is diffable, and works
with the network down, which is the state the tool most needs to survive.

**Practical shape.** The register gives the hierarchy hromada, raion, oblast
with stable codes, which is exactly the mapping the channel's wording needs
(F23: the shipped table keyed on oblasts while the channel emits the smaller
units). Distance to the border is a precomputed scalar per area, so a message
becomes "Yavorivskyi rajon, Lviv oblast, 34 km" without a single network call.

**What would change this.** Nothing about convenience. Only a demonstration
that the register is unusable for the wording the channel actually emits, which
is an empirical question the design window can answer.

## D-017. The channel is consumed at its own pace, under one identity

Date: 2026-08-09. Status: adopted

**Decision.** MAVO consumes the Telegram channel from one address, under one
identity, at a rate it can state publicly. Rotating IP addresses, distributing
requests across proxies, or otherwise obscuring the consumer from the source in
order to raise throughput is refused. Rejected while re-collecting the corpus
after losing it (F68), when the question "could we stress-test the limit
anonymously" was the obvious next thought.

**Reasoning.** Three, in ascending order of weight.

It would measure the wrong thing. The question worth answering is not where the
limit is but whether the requirement sits below it, and the requirement is one
poll every two minutes (T39). Probing for a ceiling we do not intend to
approach is looking for a block.

It would make availability depend on concealment. A warning system whose feed
survives only while its consumer is unrecognisable to its source has a
dependency it cannot supervise, cannot document, and cannot hand to anyone else
to operate.

It would cost the argument. `docs/FEED-SPEC.md` asks Polish institutions for a
feed that is public, unauthenticated and honestly consumable, and it rests on
the observation that the Ukrainian channel could be verified rather than taken
on trust. A project that simultaneously rotated addresses to extract more from
someone else's preview page forfeits the standing to ask.

**What would change this.** Not throughput. Only a demonstration that ordinary,
identified consumption at the required rate is refused *and* that no faster
interface exists - and the second half is already false, because MTProto is a
push interface and is the answer to the latency question anyway (T41).

## D-018. Collection does not scale; delivery does

Date: 2026-08-09. Status: adopted

**Decision.** The collector runs as exactly one process on one always-on host
that the operator controls (T25). Moving it to cloud infrastructure is a
decision about *availability*, not about throughput, and it is taken on those
grounds or not at all. The scalability question belongs to the delivery side and
arrives with M2, when the number of recipients stops being one.

**Reasoning.** One channel, one stream. A second collector instance adds no
throughput: it doubles the request rate against a source this project is
deliberately careful with, and it produces two copies of the truth about one
window that then have to be reconciled. Under the push interface (T41) it is
starker still, since that is a single long-lived connection under a single
identity and replicating it is meaningless.

What genuinely fails today is uptime, and it failed visibly during the corpus
re-collection: a laptop taken out of a clamshell stand is an outage, and in a
log an unplanned one is indistinguishable from a gap in the channel. That is
the argument for a host, and it is sufficient on its own.

The side that does scale is delivery. `docs/MOBILE.md` already records that an
ntfy instance serving one operator is a container while the same instance
serving an open subscriber list is a service with an availability target, which
would be the first component here to have one.

**Consequence for T39, and it is not optional.** The two successful backfill
runs went out over a residential connection. Data-centre address ranges are
treated differently by most anti-bot layers, so moving the collector to cloud
infrastructure changes the consumer's profile and **invalidates both
observations**. The tolerated-rate ladder restarts from five minutes on the new
address; it does not continue. Recorded here because the alternative is somebody
migrating the host and assuming the measurement travelled with it.

**What comes with the host, into `docs/DEPLOYMENT.md` before the move rather
than after.** An MTProto secret on someone else's machine, tier-1 corpus data on
someone else's disk, and a Telegram identity linked to the operator administered
remotely. None is a blocker; all three are things to write down first.

**What this does not license.** Being in a cloud is not an argument for moving
the alarm path onto managed push. The constraint in `docs/MOBILE.md` is
infrastructure the operator controls, which a VPS satisfies as well as a box
under a desk; FCM and APNs are a third party on the path that wakes a person,
and that is a separate decision with separate reasoning.

**What would change this.** A measurement showing that one collector cannot keep
up with the channel, which the window arithmetic currently says is not close, or
a second independent signal (ADS-B, T20) whose collection genuinely parallelises
because it is a different source rather than a second reader of the same one.

## D-019. ADS-B visibility of military aircraft: measured, aggregated, published
Date: 2026-08-10. Status: adopted

**Decision.** MAVO consumes OpenSky Network state vectors for the western box
(latitude 48 to 52, longitude 22 to 27) and may publish an aggregate count of
transmitting military aircraft in the report and on the site. Raw vectors -
positions, callsigns, ICAO24 addresses - stay in the offline measurement layer
and are not published.

**Reasoning.** ADS-B is voluntary emission. An aircraft broadcasting on 1090 MHz
has chosen to be visible, and an operator that wants silence switches the
transponder off, which is routine practice. Aggregating public emissions is
standard and openly practised OSINT; this project adds no collection capability
and no datum unavailable to anyone with a receiver. During a war, logistics
activity at a hub is part of the situational picture a reader near the border
is entitled to see.

**The counterargument, recorded and rejected.** Raised in review on 2026-08-10:
a Polish-language threat-awareness site aggregating "ISR active over
Podkarpacie now" lowers the access threshold to information about defensive
assets, which inverts the argument this project makes in `docs/FEED-SPEC.md`
section 5, where the information defended was already broadcast by siren.
Rejected on the grounds above. The aggregate-only publication form is kept as a
hedge rather than as an admission that the objection holds.

**Semantics of the published figure, which is the load-bearing part.** The
count is a lower bound on *transmitting* aircraft and not a measurement of
activity. A high number means something; a low number means nothing, and
transponder silence plausibly correlates with exactly the situations a reader
would most want to know about [inference from operational practice,
unmeasured]. The field carries that framing in itself rather than in a
footnote. A zero rendering as calm would be this repository's founding failure
wearing a new coat.

**Preconditions before the field ships.** Sampler measurement across at least
three nights, one of them with a western-Ukraine alert, establishing the base
rate, its variance by hour, and the frequency of a null response. A schema
version bump on `state.json`, because FEED-SPEC section 3 property four is a
requirement this project wrote for others and therefore owes its own consumers.
And no participation in any score: the figure is reported, never weighed, the
same separation applied to the 96.5% of front-line traffic.

**What would change this.** A request from a Polish or allied institution to
withhold the field. Evidence that the aggregate is being cited as
targeting-relevant in a way raw trackers are not. A change in OpenSky's terms
restricting redistribution of derived aggregates. Or a measured base rate so
low that the field carries no signal, in which case it is dropped for being
uninformative rather than for being dangerous.

## D-020. The contract file is written by the producer, not inferred by the consumer
Date: 2026-08-10. Status: adopted

**Decision.** MAVO writes `state.json` itself, through `mavo report --json`.
The schema lives in `mavo/report.py` and is exercised by this repository's own
gate. The companion site reads that file and nothing else: no import of
`mavo`, no traversal of the event store, no knowledge of the domain types.

**Reasoning.** The site was built with an adapter that imported MAVO, walked
its store and read attributes off its domain objects, and the binding was
honestly labelled `[inference]` because it had never run against the package.
Its own pre-flight tool exists to discover which attribute names are wrong.
That arrangement puts the contract in the hands of the party that cannot check
it: a rename in `AreaRef` passes MAVO's gate, ships, and breaks the site
silently, at a moment nobody is watching a web page for regressions. Ownership
belongs where the checking is. The producer publishes a file with a schema
version in it; the consumer validates that version and refuses what it does
not understand.

**This is also what `docs/FEED-SPEC.md` asks of everyone else.** The
specification demands a public feed with codes rather than prose, both
transitions, a versioned schema and a heartbeat. Consuming our own output
through an inferred adapter, while asking a ministry for a versioned schema,
would be arguing a case this project does not follow. The `state.json` in
section 5 of `SITE-ARCHITECTURE.md` and the payload in `mavo/report.py` are
now the same artifact, written once.

**What this costs.** The site's adapter and its MAVO-introspection checks
become dead code and should be deleted rather than left as a second path. Two
readers of one contract is how the schema drifts.

**What would change this.** A consumer needing a projection MAVO has no reason
to compute, which would be an argument for a second exporter rather than for
an adapter reaching into the store. Or a measurement showing the file write is
a bottleneck under load, which the window arithmetic says is not close.

## D-021. One review per major release, and the ones that never got one are named
Date: 2026-08-10. Status: adopted

**Decision.** A review is written for every **major** release, meaning a change
to the second version component: 0.19.x to 0.20.0.0 needs one, 0.20.0.0 to
0.20.1.0 does not. `tools/docs_audit.py` fails the gate on a major release with
no file in `docs/reviews/`, and the releases that shipped without one are a
frozen list in that check rather than a date cutoff.

**Reasoning.** Four documents said this repository files one review per
release. It had filed nine for fifty. The rule was not being broken by
carelessness: reviews kept being written, and kept landing in session artifacts
outside the tree, so the practice continued while the record of it stopped
(F79). At five releases in an afternoon, one per release is a rule nobody can
follow, and a rule nobody can follow is not a stricter version of this one, it
is an absent one wearing a stricter one's language.

**Why a frozen list rather than a cutoff date.** A cutoff would silently absorb
the next release that skips a review, which is exactly how the first nineteen
accumulated. Adding a version to `UNREVIEWED` is an edit somebody makes on
purpose, in a file the gate reads, with a sentence in `docs/reviews/README.md`
saying why.

**What a review is, and what forbids writing them backwards.** A reading of a
tree by somebody who does not yet know what they will find. Three were filed
late at 0.20.1.0, unedited, each carrying a note saying when it was written;
that is legitimate because the reading happened. Producing a file now for
0.12.0.0 from the changelog would assert that something was examined when it
was not, which is the fabrication the rest of this apparatus exists against.

**What would change this.** A run of majors where the review finds nothing
three times running, which would suggest the trigger is wrong rather than the
practice. Or a move to release trains, where the unit worth reviewing stops
being the version number.


## D-022. A default argument may not select a superseded implementation

Sprint 7 replaced the oblast-stem area table with the register map and left the
old one behind `areas=None`. `probe()` - the whole live path - passed nothing,
so the product ran the superseded implementation for two sprints while the
repair sat one argument away (F90).

**The decision.** When an implementation is replaced, the old one is deleted in
the same release. A caller that has not been updated fails loudly or does the
new thing; it never silently gets the old behaviour. A `None` default that
means "use the version we stopped believing in" is the worst available option,
because it is invisible at every call site and reads as a convenience.

**Why not a deprecation warning instead.** A warning printed by a library into
a process nobody is watching is the same class of mechanism as the assertion
that failed here: it addresses a reader who is not there. Deleting the code
makes the compiler and the test suite the readers, and both are present.

**What this cost, stated so the cost is not forgotten.** Deleting `AREAS`
turned seven tests red, and repairing them meant rewriting three fixtures. That
work was not incidental to the deletion; it *was* the deletion doing its job,
surfacing the tests that had been written against the old implementation and
had been quietly passing ever since.

**What would reopen it.** A replacement that genuinely needs a migration window
- an external consumer on the old behaviour, which this project does not yet
have. In that case the old implementation stays reachable under a name that
says what it is (`classify_with_the_pre_sprint7_table`), never under a default,
and the name carries the release in which it goes.

## D-024. The event stream: two files, a twenty-minute window and a day

**Decision.** The contract gains an event stream at schema v3, published in two
places from one composition. `state.json` carries `events`, a twenty-minute
window of every transition, with `window_start` beside it. `feed.json` carries
the same shape over twenty-four hours. Both carry **all of Ukraine** and
**both roles**, `subject` and `continuation`. A cap of 5,000 events applies to
either window, with `truncated` in the payload when it binds.

**Why a stream at all.** `state.json` v2 carried the current picture and
seven-day counts and no history. A consumer cannot build a panel of what
happened tonight from a picture of now, however the page is written, and the
contract belongs to the producer (D-020), so the absence was ours to fix
rather than the site's to work around.

**Why two files rather than one longer window.** They have different costs.
`state.json` is re-read on every cycle and every open tab pays for it; a day of
history there is a recurring charge on a phone that may be on one bar during
exactly the night it matters. `feed.json` is fetched when a reader opens the
history and then obeys ordinary HTTP caching. Measured against the same budget
as the geometry: roughly 800 events a day is about 18 KiB gzipped, 1.2 seconds
on 120 kbit/s once, against 0.3 KiB per cycle for the short window.

**Why twenty minutes and not sixty.** Operator's decision, 2026-08-12. A dead
collector empties the panel three times faster, and the panel emptying is a
signal the page exists to deliver. The cost is that a device asleep for longer
than the window cannot distinguish a gap from a quiet stretch, which is why
`window_start` is published rather than left to be derived: the consumer
compares it against its own last successful read and refuses to render
continuity across a hole.

**Why all of Ukraine, and not the west.** The first draft filtered to the eight
western oblasts on a bandwidth argument. Measured, that argument was weak:
1.2 seconds once on the worst line this project designs for. The stronger
reason against filtering is that a quiet twenty minutes in the west during a
night when the east is burning is a different fact from a quiet night, and a
reader near the border is entitled to both. `counts_24h` splits west from rest
so the page can say which it is.

**Why both roles.** One message can clear an area and list five others as still
under alert: one `subject`, five `continuation`. A stream carrying only
subjects would drop the five areas that are still dangerous. This repository
has already made that loss once, in the 4,064 continuation areas discarded
before T37, and F82 is the same family.

**Why the cap is 5,000 rather than 200.** The first proposal said 200, on a
figure of "a dozen transitions a day". That figure described **western** areas
while the stream carries **all** of Ukraine: two denominators for one number,
the shape of T49. Measured: production ingested 27 events in 97 minutes on
2026-08-11, which is about 400 a day, and the per-message estimate over the
corpus gives about 800. A 200-event cap would have bound every single day,
which makes it a window with a misleading name and makes `truncated`
permanently true and therefore useless. At 5,000 the cap binds only above six
times anything measured, so `truncated` firing is itself a measurement.

**What would reopen it.** `truncated` going true, which turns the cap from a
safety net into a design parameter and means the window needs re-thinking
rather than raising. Or a measurement showing consumers fetch `feed.json` far
more often than the design assumes, which would collapse the cost argument for
the split.

## D-026. Beta stops depending on anyone asking for it

**Decision.** The beta definition in `docs/MVP.md` loses its middle clause.
Beta is the reporting instrument, live, with its correctness and latency
measured and published. Whether anyone has asked for it no longer bears on the
version number, and the blocker row for it is gone from the readiness table.

**Reasoning.** The clause was written when the only imagined delivery was a
push to two named phones, and in that world it was the same thing as consent.
It is not the same thing now. The site has been publicly reachable since
2026-08-12; who visits it is not a property of the instrument, is not
controlled by this repository, and does not shrink by writing code. Asking
permission to exist and being correct are different questions, and only the
second is what a version number should turn on.

**What did not change, and this is the part worth reading twice.** T11 still
gates **push delivery**. Waking somebody's phone at three in the morning
requires that they asked; a page they chose to open does not. The two were one
clause because the project once had one delivery path, and separating them is
the whole content of this decision. `docs/MVP.md` section 3 keeps the
requirement where it belongs, and the README keeps saying that recipients are
gated by T6 and T11.

**What stays in the way of beta.** Correctness measured on western areas
(T36), and end-to-end latency as a distribution rather than as fetch time per
poll (T40). Both are properties of the thing rather than of its audience, and
neither is close.

**What would reopen it.** A delivery path that pushes rather than waits,
at which point the consent question returns to the definition, because it is
then a property of what the instrument does rather than of who happens to read
it.
