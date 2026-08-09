# MVP

```
Document:  docs/MVP.md, version 3.0
Audience:  anyone asking when this is finished, including the author on a day
           when another sprint feels justified
Companion: TODO (the backlog), DECISIONS (what was rejected), reviews/ (what
           each release actually did)
Note:      blockers are typed. Engineering blockers shrink when code is written;
           access and decision blockers do not shrink at all, and counting
           sprints toward a goal gated by one is a category error
```

## Contents

1. [What changed at 0.9.0.0, and why this document was rewritten](#1-what-changed-at-0900-and-why-this-document-was-rewritten)
2. [Audience A: the author, personal use](#2-audience-a-the-author-personal-use)
3. [Audience B: a small group who asked](#3-audience-b-a-small-group-who-asked)
4. [Audience C: public repository as a portfolio artefact](#4-audience-c-public-repository-as-a-portfolio-artefact)
5. [Audience D: a publicly available reporting instrument](#5-audience-d-a-publicly-available-reporting-instrument)
6. [What beta means](#6-what-beta-means)
7. [Five sprints to beta](#7-five-sprints-to-beta)
8. [What is deliberately not in the plan](#8-what-is-deliberately-not-in-the-plan)
9. [Where this plan will bend](#9-where-this-plan-will-bend)
10. [Amending these criteria](#10-amending-these-criteria)

---

## 1. What changed at 0.9.0.0, and why this document was rewritten

D-015 restated the product: MAVO reports a threat picture in real time and does
not predict crossings. Every criterion below was written under the previous
framing and most of them measured the wrong thing.

Three specific corrections, because "the thesis was restated" is not a licence
for silently improved criteria.

**The schedule stops being blocked by event scarcity.** Version 2.0 of this
document carried a paragraph headed "the thing that does not compress":
crossings run at two to four a year, so a four-week window contains
statistically zero of them, and recall could not be validated by autumn at any
level of effort. That was correct, and it applied to a predictor. A reporting
instrument is validated on correctness, latency and completeness, all measurable
in a week against the corpus in hand. The autumn deadline became reachable by
narrowing the claim, not by working faster.

**Area resolution moved from support to centre.** It was a gazetteer task behind
the classifier. It is now the product: a report that cannot say which rajon and
how far from the border is a relay of somebody else's feed.

**The alarm tier leaves the critical path entirely.** Not cancelled, not
scheduled. If it returns, it returns with the gate, a crossing list (T28) and a
corpus roughly fifteen times the current span (F58). None of that gates anything
below.

## 2. Audience A: the author, personal use

**Done when** the daemon has run unattended for 72 hours against the live
channel, every cycle is accounted for in the run log as events, a degradation
event or a logged defect, and the end-to-end latency from channel publication to
a rendered report is measured and recorded rather than estimated.

| Blocker | Type |
| --- | --- |
| Area resolution against real message wording | engineering (S7). The shipped table scored 0 of 20 (F23); the register replacing it is T31 |
| Distance to the border as a stored column | engineering (S8, T32) |
| `mavo watch` and the run log | engineering (S9, T23) |
| Where the daemon lives | **decision** (T25). A laptop that sleeps writes a record whose holes look like quiet nights |

## 3. Audience B: a small group who asked

**Done when** everything in A holds, plus: at least two people have been asked
and said yes (T11), the delivery path wakes a phone through Do-Not-Disturb, a
dead feed produces a blindness message within one poll interval, and the message
wording has been read by someone who did not write it, specifically for whether
it can be mistaken for a prediction.

| Blocker | Type |
| --- | --- |
| Delivery path | engineering (S10, phase M1) |
| Two people asked | **access** (T11). Nobody has been asked, and this does not shrink by writing code |
| Legal position on sending warnings to people other than the operator | **decision** (T6). Needs counsel; runs in parallel from now |

## 4. Audience C: public repository as a portfolio artefact

**Done when** everything in B holds, plus: every README limitation is registered
in the lint, the defect log has entries from real data rather than only from
fixtures, and the threat model's residual risks have been re-probed rather than
re-read.

| Blocker | Type |
| --- | --- |
| Defect log entries from real data | **met.** F23 from 20 live messages, F50 verified against the corpus, F58 from the threshold sweep |
| Threat model residuals re-probed | engineering (S11) |
| Onboarding probe from a clean clone | engineering (S11, T7) |

## 5. Audience D: a publicly available reporting instrument

The target scope. **Done when** everything in C holds, plus: the report is
correct against a hand-checked sample of real messages at a stated rate, the
measured end-to-end latency is published rather than claimed, the delivery path
has a stated availability target and a rate limit, a subscription route exists
that is not one Android app in English, and the legal position covers recipients
who are strangers.

| Blocker | Type |
| --- | --- |
| Measured correctness and latency, published | engineering (S8, S9) |
| Availability target and rate limit | engineering (S10) |
| A route that is not one app in English | engineering, **not yet scoped**. Named now so it is not discovered at the end |
| Legal position covering strangers | **decision** (T6) |
| Disengagement measured rather than assumed | engineering (T29). D-014 removed the assumed budget; shipping without an instrument repeats the assumption at scale |

## 6. What beta means

One sentence, so it cannot drift: **beta is the reporting instrument, live,
delivering to people who asked, with its correctness and latency measured and
published.**

What beta is not: no alarm class, no probability of anything, no ADS-B tier, no
app store, no claim about what will cross the border. A beta that quietly
acquires any of those has become a different product and needs a different plan.

## 7. Five sprints to beta

Five, and the number is a commitment rather than an estimate. Each sprint has an
exit criterion that can be checked by running something, and a sprint that
misses its exit criterion is reported as missed rather than absorbed into the
next one. Two-week windows, calendar dates rather than effort.

| Sprint | Window | What ships | Exit criterion, checkable |
| --- | --- | --- | --- |
| **S7** | 10 to 23 Aug | Area resolution. KATOTTH as a versioned file (T31), the parser redesign against the design window, means of attack as its own class (T16) | The measured hit rate of area resolution against a hand-labelled sample of the design window, printed as a number. Not "improved": a number, beside the 0 of 20 it replaces |
| **S8** | 24 Aug to 6 Sep | The report. Distance to the border precomputed per area (T32), report composition, a command that renders the current picture from the store | A hand-checked sample of real messages where the rendered report is correct in area, means and distance, with the error rate stated. Distances spot-checked by hand before the column is trusted anywhere |
| **S9** | 7 to 20 Sep | Real time. `mavo watch` (M0), the run log and its reader (T23, T24), interval jitter from the first commit (T27), the host decision (T25) | 72 hours unattended with every cycle accounted for, and the first end-to-end latency measurement: channel publication to rendered report, reported as a distribution rather than a best case |
| **S10** | 21 Sep to 4 Oct | Delivery. Self-hosted ntfy, the three message classes, blindness reporting, per-recipient topics (M1) | A synthetic report reaches a phone through Do-Not-Disturb within a measured time; killing the feed produces a blindness message within one interval; the delivery ledger and the phone agree over a week |
| **S11** | 5 to 18 Oct | Hardening to beta. Threat-model rows for the delivery path with tests, the clean-clone probe (T7), the identifier lint (T22), the disengagement instrument (T29) | `make verify` green from a clean clone on a machine with nothing installed, every new threat row carrying a test, and T6 recorded |

**Beta: 18 October 2026.**

**The parallel track no sprint can absorb.** T6 is a decision blocker: it needs
counsel and does not shrink by writing code. It starts now and must be recorded
before S11 closes, because Audience B is gated on it and every sprint after S9
assumes recipients exist. If it is not recorded by 5 October, beta slips to the
date it is recorded plus two weeks, and the slip is reported rather than
absorbed.

**Dependencies, stated so a slip propagates visibly.** S8 needs S7's resolution
to work at all; S9 needs S8's report to have something to render; S10 needs S9's
latency measurement to know what it is promising; S11 needs S10's delivery path
to have threats to model. Beyond the legal track there is no parallelism to
exploit, and pretending otherwise is how five sprints becomes eight.

## 8. What is deliberately not in the plan

- **The alarm tier.** Out of scope for beta by D-015. Returning it needs the
  gate, a crossing list (T28) and a far longer corpus (F58).
- **ADS-B (T14, T20).** It was a prerequisite for a drone *alarm* tier. Under a
  reporting thesis it is enrichment: valuable, not blocking, and it would cost
  most of a sprint in ingest work.
- **A second Polish feed (T8).** Unresolved access, and the report does not
  depend on it.
- **The API token (T1).** Both Ukrainian feeds share one upstream (D-010) and
  the Telegram adapter already reaches it without a token.

## 9. Where this plan will bend

The first thing cut at a deadline is measurement, because it does not show in a
demo. Here measurement is the product: an unmeasured report is somebody else's
feed with extra steps, and anyone can build that in an afternoon.

The specific risk is S7. Area resolution is the one sprint whose difficulty is
genuinely unknown, because the register's names have never been checked against
the channel's wording. If the hit rate comes back low, that is a finding, and
the correct response is to say so and re-plan rather than ship a report that is
confidently wrong about which rajon is under alert. A report that names the
wrong place is worse than no report, because it is actionable.

## 10. Amending these criteria

A criterion that moves because it turned out to be inconvenient is a scope change
and is recorded as one, in the same commit that meets it, with its reason.

*Amended 2026-08-09 (0.9.0.0).* This document was rewritten against D-015. The
previous audience criteria and the schedule to autumn are in the git history;
what replaced them, and why each replacement was necessary rather than
convenient, is section 1.
