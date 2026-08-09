# FOUNDATIONS

What this project rests on. Every load-bearing claim, its provenance, and what
would falsify it.

```
Document:  docs/FOUNDATIONS.md, version 1.0
Audience:  a contributor deciding whether a change is consistent with why this
           exists, and a reader deciding whether to believe any of it
Companion: METHODOLOGY (what may be claimed and the defect log), MECHANISMS
           (how each mechanism works), DECISIONS (what was rejected)
Note:      a claim without a provenance label in this document is a defect.
           "Inference" and "measured" are not decoration; they change what a
           reader is entitled to conclude
```

## Contents

1. [Provenance labels](#1-provenance-labels)
2. [What this tool is for](#2-what-this-tool-is-for)
3. [The observation the project starts from](#3-the-observation-the-project-starts-from)
4. [The problem that observation creates](#4-the-problem-that-observation-creates)
5. [Assumptions, each with its falsifier](#5-assumptions-each-with-its-falsifier)
6. [What is measured, and on what](#6-what-is-measured-and-on-what)
7. [The null result this project is built around](#7-the-null-result-this-project-is-built-around)
8. [What would make this project stop](#8-what-would-make-this-project-stop)

---

## 1. Provenance labels

Four labels, applied to every load-bearing claim in this repository. They are
not a style convention. They determine what a reader may conclude.

| Label | Means | Example |
| --- | --- | --- |
| **measured** | Produced by running something and recording the result | The channel page carries exactly 20 posts. Four runs, no exception |
| **reported** | A source said it. We have not verified it and often cannot | An oblast is under alert. This is what the feed claims, not what the sky contains |
| **inference** | Derived from measurements by an argument that is written down | ~650 posts per day, from three windows of measured volume |
| **speculation** | A hypothesis worth testing that has not been tested | Drone crossings may be undecidable from oblast-level alert state |

The distinction that matters most in this domain is **measured** against
**reported**. Nothing in this system observes airspace. Every alert state is a
claim by a source, and the code labels it as such at the point of ingestion, not
at the point of display. A pipeline that loses the label somewhere in the middle
produces a display that cannot recover it.

---

## 2. What this tool is for

**MAVO reports a threat picture in real time. It does not predict what will
cross into Poland.** Stated first because everything downstream follows from it,
and because until 0.9.0.0 this document said something else.

The distinction is not a hedge. A crossing depends on how many munitions
Ukrainian air defence brings down, on where the debris of the intercepted ones
falls, on whether a drone loses its way, and on decisions taken by an adversary
minutes earlier. None of that is observable from any feed this project can
reach, and no volume of history makes it observable. A tool that claimed to
predict crossings would be claiming access to information that does not exist
in its inputs.

What *is* observable, at the moment it happens, is the threat picture on the
Ukrainian side: which areas are under alert, how intense the activity is right
now, what means of attack the channel names, and how far the nearest alerted
area is from the Polish border. That is a fact about the present rather than a
claim about the future, and it is exactly what a person twenty kilometres from
the border cannot currently get at three in the morning.

Three properties define the product, in this order:

1. **Maximum information.** Everything the sources support, with its provenance
   attached, rather than a distilled verdict.
2. **Maximum speed.** The value of the report decays in minutes. A correct
   report that arrives after the sirens is a news item.
3. **Completeness.** Silence must never be ambiguous: an area whose state is
   unknown is reported unknown, and a dead feed is reported as blindness.

**What this costs, stated rather than discovered.** The tool cannot tell anyone
whether to take cover. It can tell them that a massed strike is under way sixty
kilometres from where they are and that the nearest alerted rajon is closer than
it was ten minutes ago. What they do with that is theirs, and the decision to
act belongs to the state alerting system that exists for it (D-004).

**Consequences of the restatement**, recorded because each one silently changed
what other work is worth doing: the roughly twelve crossings stop being the
target variable, so the corpus no longer has to be long enough to contain them;
the base rate of campaign nights stops being the number to beat, because nothing
is being predicted; and the gate with its recall, lift and Fisher conditions
applies to the alarm class alone, if an alarm class is ever built. The reporting
tier is judged on correctness, latency and completeness, which are measurable on
the corpus in hand.

## 3. The observation the project starts from

**[measured, external]** Every violation of Polish airspace in the observed
period coincided with a night of massed Russian strikes on western Ukraine.

That is the entire seed of the project. It reads like a warning signal: if the
strikes are visible in Ukrainian alert feeds, and the crossings only happen on
those nights, then the feeds carry advance notice of the crossings.

**[measured, external]** Those campaigns cover roughly 57% of days.

That is the same observation, read honestly. A rule that fires on campaign
nights has recall near 1.0 and fires on more than half of all nights. Perfect
recall and a 57% firing rate is not a detector. It is a calendar with extra
steps.

---

## 4. The problem that observation creates

The project exists to answer one question: **is there enough resolution in the
available feeds to separate the nights that matter from the nights that merely
look the same?**

Three axes of resolution are available in principle:

| Axis | From | Status |
| --- | --- | --- |
| Time | Hour rather than night | Available. Alerts carry timestamps |
| Space | Border oblast, and below it raion, rather than country | Partially available. The channel emits raion-level alerts; the model does not yet use them (F24) |
| Means | Missile against drone classification | Partially available. The channel carries means on separate messages from the alerts they qualify (F25) |

Whether those three are enough is an empirical question, and this repository is
built so that the answer **no** can be reached and recorded rather than tuned
away. The gate exists for that: a rule that cannot beat the base rate fails,
and failing is a result rather than a bug.

---

## 5. Assumptions, each with its falsifier

An assumption with no falsifier is not an assumption. It is a belief, and it
belongs in a different document.

### A1. The Ukrainian feeds are correlated, not independent

**[inference, from public statements]** alerts.in.ua, api.ukrainealarm.com and
the public Telegram channel all draw on the same upstream alerting chain.

Consequence: two-source agreement is never confirmation. Multiple sources
protect against transport failure and nothing else. This is MT9 and D-010, and
it is why ADS-B moved from optional enrichment to a prerequisite for any
drone-tier alarm.

**Falsifier:** either service moving to its own independent acquisition, which
would be visible as timing divergence during an event. **Not currently
measured.** The relative latency between channel and APIs is unknown, and the
claim that the channel is upstream of the APIs is inference, not measurement.

### A2. Alert state is reported, never observed

**[definitional]** Nothing in this system observes the sky. Every state is a
claim by a source that may be wrong, late, or absent.

Consequence: the tri-state was never sufficient. UNKNOWN exists because silence
is not safety, and PARTIAL_CLEAR exists because a source that contradicts itself
has told us something different from a source that said nothing (F26).

**Falsifier:** an independently observing input. ADS-B is the only planned one,
and it observes the aviation system's reaction rather than the threat, which is
a weaker but real signal.

### A3. Attention is a finite resource owned by the recipient

**[design decision, contested in this repository]** Two alarms per week, shared
across all regimes.

The reasoning is not politeness. An adversary who can induce sub-threshold
conditions floods the channel at no cost, and the flooding
outlasts the campaign (MT4). The alarm rate is therefore a hard gate condition
rather than a quality metric.

**This assumption has been challenged during development** on the grounds that
a recipient facing an air raid reads everything. The counter-argument, recorded
because the challenge was reasonable: the recipient is not in one extreme night,
they are in the two hundred nights that look identical before it, and the ratio
between 57% of days and two to four crossings a year is the whole problem.

**Falsifier:** a measured alarm rate during shadow mode that the recipient
reports as tolerable, or a design in which one episode yields one message rather
than messages. The second is the more likely refinement.

### A4. The positive class is too small to fit a model to

**[measured]** Roughly a dozen crossings across four years.

Consequence: rules are explicit predicates with thresholds in configuration, not
a learned model. This is registered as a README limitation and enforced by a
lint that fails if a machine-learning dependency appears.

**Falsifier:** a materially larger labelled positive class. The realistic route
is a different label, such as air-defence reaction rather than confirmed
crossing, which is more frequent and arguably closer to what a recipient cares
about. That would change what the product claims, so it is a decision to record
rather than a parameter to change.

### A5. Two timing regimes, not one

**[inference, arithmetic on stated assumptions]** A missile crossing from an
alert in Lviv oblast is roughly six minutes at 700 km/h over 70 km. A drone
crossing from Volyn is roughly thirty-three minutes at 180 km/h over 100 km.

Consequence: one threshold cannot serve both, which sprint 3 measured directly.
Global recall of 0.47 hid 7 of 7 on missile nights and 0 of 8 on drone nights.

**Falsifier:** measured lead times on real events that contradict the
arithmetic. The arithmetic is arithmetic, not a measurement, and is labelled as
such wherever it appears.

### A6. Degradation must be visible, or absence is meaningless

**[design decision]** Unknown is never printed as zero. An unreachable source
is never an empty result. A skipped message window is a count when measurable
and `unknown` when not.

Consequence: several exit codes and a state that never resolves to clear.

**Falsifier:** none. This one is not empirical; it is the property the project
is for. A version of MAVO that reads absence as safety is not a worse MAVO, it
is a different and dangerous tool.

---

## 6. What is measured, and on what

**Channel structure, measured 2026-08-09 on the design window** (48,540
messages, 2,427 pages, 607 refused above the boundary). Detail in
`docs/CHANNEL.md`.

| Claim | Provenance |
| --- | --- |
| 99.34% of messages carry a `#Name_unit` hashtag | measured |
| 127 distinct tags across 99 nights | measured |
| 126 of 127 resolve to a unique KATOTTG code | measured, by joining |
| Tag occurrences: raion 61,531, hromada 7,630, oblast 515 | measured |
| Western oblasts hold 2,456 of 69,676 tag occurrences, 3.5% | measured |
| 36 western tags, covering all 36 western raions in the register | measured |
| The west is alerted as a block rather than per raion | inference, from the uniformity of western tag counts at 56 to 58 |
| The channel and the register are independently evolving vocabularies | measured, one instance: the channel tags `ВолодимирВолинський`, the register lists `Володимирський` |


The most important sentence in this repository: **almost every number produced
so far was produced against a synthetic history.**

| Number | Source | What it is evidence about |
| --- | --- | --- |
| Every candidate rule fails the gate | `mavo gate` on the fixture generator | The generator, and the gate's arithmetic. Not the world |
| Policy at 1.96 alarms/week, reported and no longer gated (D-014) | `mavo policy` on the fixture generator | The generator |
| Recall 7 of 7 missile, 0 of 8 drone | Fixture scenarios | The generator's construction, which is why the drone finding is labelled speculation rather than measurement |
| Classifier hit rate 0 of 20 | **Real channel content**, 2026-08-08 | The channel, and the pattern table. This is the only product measurement on real data so far |
| Page size 20, backwards paging, channel volume | **Real channel**, 2026-08-09 | The channel on that day |

The fixture generator is not a simulation of Ukraine. It is a device for
exercising the decision path, and every number derived from it is a property of
the device. This is stated here, in the README, in STATUS.json and in
METHODOLOGY, because it is the claim most likely to be quietly dropped when the
numbers start looking good.

---

## 7. The null result this project is built around

Before this repository existed, a candidate covariate was proposed to explain
the timing of attacks and it looked convincing on a chart. Tested against the
full attack-density series, 738 attack nights and 87,093 munitions from
September 2022 to April 2026, it returned a null on every test applied:
Rayleigh R = 0.013 with p = 0.95, Spearman r = +0.03 with p = 0.44, and a mean
value on attack nights of 49.1% against a population mean of 50.1%. The
analysis built on it does not survive, and the variable is excluded (D-002).

This is not history. It is the reason for three structural choices:

- **No model fitted to the positive class.** A pattern that convinces the eye
  on a small sample is the normal case, not the exception, and a learned model
  on a dozen positive events would reproduce the same error with more
  machinery and less visibility.
- **The lint at term level.** `tests/lint_limitations.py` fails if an excluded
  covariate appears in package source, so re-introduction takes a deliberate
  test change rather than a plausible-sounding commit. A null result that lives
  only in prose is an opinion.
- **The design/holdout split declared before reading** (D-012). With twenty
  messages there was nothing to overfit to. With a corpus of hundreds of
  thousands, there is.

The attack-density series remains the reference dataset for how attacks
distribute in time, and the procedure remains the standard for admitting any
new covariate: a directional test on the full series, pre-registered, before
the variable is allowed near a rule.

---

## 8. What would make this project stop

Stated so that continuing is a decision rather than a default.

- **The gate is never cleared on real data.** If no rule beats the base rate
  once real backtesting is possible, the honest output is a written negative
  result and an archived repository, not a lowered threshold.
- **The feeds become unavailable.** Access to both APIs is revocable without
  cause (MT10, D-010). The public channel is the fallback and is equally
  revocable.
- **No rule beats the calendar with confidence.** Sprint 3 already
  produced a configuration that passes at a 2% margin, which is not comfortable.
  If real data makes that worse, the shippable product may be the observation
  tier only, with no alarm tier at all.
- **Someone builds it properly.** If a state or alliance system provides the
  same lead time publicly, this becomes redundant, and the correct response is to
  say so.
