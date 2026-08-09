# MVP

```
Document:  docs/MVP.md, version 2.0
Audience:  anyone asking when this is finished, including the author on a day
           when another sprint feels justified
Companion: TODO (the backlog), DECISIONS (what was rejected), reviews/ (what
           each release actually did)
Note:      blockers are typed. Engineering blockers shrink when code is written;
           access and decision blockers do not shrink at all, and counting
           sprints toward a goal gated by one is a category error
```

## Contents

1. [Audience A: the author, personal use](#audience-a-the-author-personal-use)
2. [Audience B: a small trusted group](#audience-b-a-small-trusted-group)
3. [Audience C: public repository as a portfolio artefact](#audience-c-public-repository-as-a-portfolio-artefact)
4. [Audience D: a publicly available warning system](#audience-d-a-publicly-available-warning-system)
4. [Amending these criteria](#amending-these-criteria)
5. [Schedule to autumn](#schedule-to-autumn)


What finished means, per audience. A codebase always yields another defect, so
without exit criteria every sprint can be justified as the next one indefinitely.

Blockers are typed. **Engineering** blockers shrink when code is written.
**Access** blockers do not shrink at all, no matter how many sprints pass, and
counting sprints toward a goal gated by one is a category error.

## Audience A: the author, personal use

**Done when** the collector has run continuously for four weeks against live
feeds in shadow mode, the measured alarm rate for the chosen rule sits inside
budget, and the median lead time on any true positive in that window is recorded.

| Blocker | Type |
| --- | --- |
| alerts.in.ua API token | **access**, application submitted, one follow-up ~20 Aug. No longer on the critical path: gates cross-source comparison and API history (T10), not ingestion |
| Live feed latency measurement | engineering. Unblocked by sprint 4: the Telegram adapter reaches the shared upstream without a token. First measurement owned by sprint 6 |
| Regime split, missile and drone paths | engineering, **done** (sprint 3, D-009: missile alarms, drone demoted) |
| Working classifier against real channel content | engineering. The shipped table scored 0 of 20 (F23); redesign is sprint 7 - sprint 6 shipped the corpus acquisition it waits on (T19, done) - and remains the critical path |
| Signal output channel | engineering (sprint 7) |

*Amended 2026-08-08 (0.3.2.0).* The original table gated latency measurement on
the token, which sprint 4 made false and this document did not follow. Recorded
as a scope change rather than silently edited: the amendment tracks a shipped
capability, not an inconvenient criterion.

## Audience B: a small trusted group

**Done when** everything in A holds, plus: the guard test on message content
passes, `Responsible use` is written, the onboarding probe has been run from a
clean clone by following the README from zero, and a documented rule has cleared
the gate on real data rather than synthetic.

| Blocker | Type |
| --- | --- |
| Real-data backtest clearing the gate | engineering. **No longer blocked on the token**: sprint 6 retrieved 60,680 real messages without one (T19, F44). Blocked on the sprint 7 classifier, which is engineering and shrinks by writing code |
| Onboarding probe from a clean clone | engineering |
| Legal position on distributing warnings to people other than the operator | **decision**, needs counsel, does not shrink by writing code (T6) |

## Audience C: public repository as a portfolio artefact

**Done when** everything in B holds, plus: every README limitation is registered
in the lint, the defect log has entries from real data rather than only from
fixtures, and the threat model's residual risks have been re-probed rather than
re-read.

| Blocker | Type |
| --- | --- |
| Defect log entries from real data | **met.** F23 was measured against 20 live messages and F50 verified against the corpus, neither needing a token. The row survived as blocked for three releases after it stopped being true |
| Threat model residuals re-probed | engineering |

## Audience D: a publicly available warning system

The target scope, and the rung this ladder was missing until 0.7.0.0. Audience
C makes the *code* public; it says nothing about the *system* being available to
someone who is not the author, which is what this project is for. A ladder whose
top rung is a portfolio artefact quietly redefines the goal as the thing that is
easiest to reach, and two documents had already started planning against that
smaller goal (F53).

**Done when** everything in C holds, plus: a rule has cleared the gate on the
holdout rather than the design window, the alarm path has run in shadow mode
long enough to state a measured alarm rate on real data, the legal position
covers recipients who are strangers rather than a named circle, the delivery
path has a stated availability target and a rate limit, and there is a
subscription route that does not require an Android phone and English.

| Blocker | Type |
| --- | --- |
| A rule clearing the gate on the holdout | engineering, blocked on sprint 7 |
| Measured alarm rate from shadow mode on real data | engineering, blocked on the daemon (`mavo watch`, phase M0) |
| Legal position covering distribution to strangers | **decision** (T6, restated). Does not shrink by writing code, and is broader than the private-circle question originally asked |
| Disengagement measured rather than assumed | engineering (T29). D-014 removed the assumed budget; the replacement is an instrument, and a public tier shipped without one repeats the assumption at scale |
| Delivery capacity: availability target and rate limit | engineering, and the first component here that would carry an availability target at all |
| A subscription route that is not one Android app in English | engineering, **not yet scoped**. Named now so it is not discovered at the end |

The gap between C and D is the honest measure of how far this project is from
its purpose, and it is deliberately larger than the gap between A and C.

*Amended 2026-08-09 (0.7.0.0).* Audience D is new, and two Audience B and C
rows that read `blocked on the token` were corrected: the corpus was retrieved
without a token in sprint 6, which made both false at that moment and neither
followed. Recorded as a scope change under the rule below, with its reason: the
criteria were not moved because they were inconvenient, they were moved because
they were wrong.

## Amending these criteria

A criterion that moves because it turned out to be inconvenient is a scope change
and is recorded as one, in the same commit that meets it, with its reason.


---

## Schedule to autumn

Written because the project is time-sensitive: further attacks are expected this
autumn and the tool should be useful before then. Dates are calendar, not effort.

**The thing that does not compress.** Border crossings run at roughly two to four
per year. A four-week shadow-mode window contains, statistically, zero positive
events. It measures the false-alarm side and nothing else. Recall and lead time
cannot be validated by autumn at any level of effort, because the constraint is
event scarcity, not engineering time.

**Consequence, and it is not negotiable.** The observation tier can ship in
September. The alarm tier cannot. Shipping an alarm tier to people who will rely
on it, without the measurement that justifies its threshold, is precisely the
failure mode this project exists to prevent.

| Window | Sprint | Capability or defect class | Blocker |
| --- | --- | --- | --- |
| 6 to 12 Aug | S4 | Live ingestion without waiting on anyone: `TelegramChannelSource` against the public Ajax channel, which is the shared upstream of both APIs. **Shipped 0.3.0.0.** OpenSky account still outstanding | none |
| 6 to 9 Aug | S5 | **Shipped 0.4.0.0.** Not the scheduled classifier redesign. The evidence container instead: fourth state (F26), window-gap detection (F27), harness mutation-verified (F14, after two slips). Scope change recorded as D-011 | none |
| 10 to 19 Aug | S6 | Corpus collection running (T19) and the classifier redesign against it, not against a sample. First live latency measurement | corpus needs seven days of wall clock |
| 20 to 23 Aug | S7 | Output channel as an attack surface: Signal delivery, guard test on message content, sender-side rate limit. Follow-ups sent if still silent | none |
| 24 Aug to 21 Sep | S8 | Shadow mode, four weeks, nothing sent. Measures alarm rate on real data | calendar only |
| 22 to 30 Sep | S9 | Threshold correction, observation tier to a small group, manual completed for every shipped command | T11 |

**T11 is promoted to a blocker.** The alarm threshold is calibrated against a
recipient's tolerance and no recipient has been asked. Those two conversations
must happen before shadow mode starts on 24 August, not after, or four weeks of
measurement will be scored against a number taken from the air.

**Where this plan will bend under time pressure.** The first thing cut at a
deadline is calibration, because it does not show in a demo. Here calibration is
the product. Without it what remains is a Telegram relay that anyone can build in
an afternoon and that needs neither this repository nor its author.
