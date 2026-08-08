# MVP

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
| Live feed latency measurement | engineering. Unblocked by sprint 4: the Telegram adapter reaches the shared upstream without a token. First measurement owned by sprint 5 |
| Regime split, missile and drone paths | engineering, **done** (sprint 3, D-009: missile alarms, drone demoted) |
| Working classifier against real channel content | engineering. The shipped table scored 0 of 20 (F23); redesign is sprint 5 and needs the corpus (T19) |
| Signal output channel | engineering (sprint 6) |

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
| Real-data backtest clearing the gate | engineering, blocked on the token |
| Onboarding probe from a clean clone | engineering |
| Legal position on distributing warnings beyond a private circle | **decision**, needs counsel, does not shrink by writing code |

## Audience C: public repository as a portfolio artefact

**Done when** everything in B holds, plus: every README limitation is registered
in the lint, the defect log has entries from real data rather than only from
fixtures, and the threat model's residual risks have been re-probed rather than
re-read.

| Blocker | Type |
| --- | --- |
| Defect log entries from real data | engineering, blocked on the token |
| Threat model residuals re-probed | engineering |

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
| 13 to 19 Aug | S5 | Hostile input as an outage vector: never-raise contract made executable across every adapter. First live latency measurement | none |
| 20 to 23 Aug | S6 | Output channel as an attack surface: Signal delivery, guard test on message content, sender-side rate limit. Follow-ups sent if still silent | none |
| 24 Aug to 21 Sep | S7 | Shadow mode, four weeks, nothing sent. Measures alarm rate on real data | calendar only |
| 22 to 30 Sep | S8 | Threshold correction, observation tier to a small group, manual completed for every shipped command | T11 |

**T11 is promoted to a blocker.** The alarm threshold is calibrated against a
recipient's tolerance and no recipient has been asked. Those two conversations
must happen before shadow mode starts on 24 August, not after, or four weeks of
measurement will be scored against a number taken from the air.

**Where this plan will bend under time pressure.** The first thing cut at a
deadline is calibration, because it does not show in a demo. Here calibration is
the product. Without it what remains is a Telegram relay that anyone can build in
an afternoon and that needs neither this repository nor its author.
