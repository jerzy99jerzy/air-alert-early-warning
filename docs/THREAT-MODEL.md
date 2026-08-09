# THREAT-MODEL

```
Document:  docs/THREAT-MODEL.md, version 2.0
Audience:  a contributor adding a control, and anyone trying to break this
Companion: MECHANISMS (how each control works), tests/harness/CATALOGUE.md (the
           scripted attack per row), METHODOLOGY (what was found by trying)
Note:      every row carries a control or a **named acceptance**, and every
           acceptance carries the trigger that would reopen it. An accepted risk
           with no trigger is an unaddressed one with better manners
```

## Contents

1. [Who benefits from the output being wrong](#who-benefits-from-the-output-being-wrong)
2. [Rows](#rows)
3. [Residual, stated rather than hidden](#residual-stated-rather-than-hidden)
4. [What the maintainer can do](#what-the-maintainer-can-do)


Adversaries against this tool, not against the world. Rows are numbered MT1
upward with no gaps, each carrying either a control or a named acceptance, and
the test that measures it. `tools/docs_audit.py` fails on a gap or a count that
disagrees with `STATUS.json`.

An accepted risk is not an unaddressed one. It has a trigger that would reopen
it, and where possible a harness attack that asserts the acceptance, so that
forgetting it costs a deliberate test change.

## Who benefits from the output being wrong

An actor conducting incursions benefits in both directions. A false negative
removes warning. A sustained false-positive rate removes attention, which is
cheaper to induce and lasts longer.

## Rows

| Row | Threat | Control or acceptance | Measured by |
| --- | --- | --- | --- |
| MT1 | A source reports implausibly broad simultaneous activation, manufacturing an alarm | Poison suppression: eight or more distinct areas inside 120 seconds suppresses every rule | `test_rules.py::test_poisoned_feed_is_suppressed_entirely`, harness A1 |
| MT2 | A source goes silent during a real event and silence reads as safety, or speaks ambiguously and the ambiguity reads as safety | `AlertState.UNKNOWN` and `AlertState.PARTIAL_CLEAR` are distinct states; `is_clear` is affirmative, never the negation of ACTIVE, and the lint enumerates the enum rather than naming states | `test_schema.py::test_unknown_is_not_the_safe_state`, `test_sprint5.py::test_f26_a_partial_all_clear_never_resolves_to_clear`, harness A2 |
| MT3 | A single fabricated alert in one border oblast raises an alarm | Alarm tier requires the conjunction; one area cannot raise one | `test_rules.py::test_border_only_does_not_fire_the_conjunction`, harness A3 |
| MT4 | A rule that fires broadly enough to be right eventually buys an alarm by never missing: perfect recall, significant association, and no information in the firing | The gate's lift floor. A rule must beat the base rate at the *lower* bound of its precision interval, so a calendar fails on the one statement it cannot make. Replaced the alarm-rate condition at 0.8.0.0 (D-014) | harness A4, `test_attacks.py::test_a4_perfect_recall_does_not_buy_past_the_lift_floor` |
| MT5 | Budget laundering: several rules each cleared at the full budget produce a multiple of it | **Row retired at 0.8.0.0 (D-014).** The control was a construction-time refusal in `DecisionPolicy` and it was removed with the budget. Recorded rather than deleted: the attack was real while the budget existed, and a threat model that quietly loses rows cannot be diffed against its own history |
| MT6 | A partial policy reads as complete because unserved crossings left the denominator | Coverage gaps are counted by kind, exposed as `has_coverage_gap`, and printed | `test_sprint3.py::test_f8_partial_policy_reports_its_gap`, harness A6 |
| MT7 | Hostile input converts into an outage: a malformed payload crashes the collector during the window that matters | Contract: `ThreatSource.poll` absorbs every content failure and reports it. Measured on the fixture and Telegram adapters; the API adapters do not exist yet | harness A7 and A9, `test_telegram.py::test_hostile_bodies_do_not_raise` |
| MT8 | Re-polling an unchanged feed multiplies rows until replay stops reconstructing the past | Idempotence by content hash, which excludes `ts_ingest` | `test_store.py::test_repoll_with_new_ingest_time_does_not_duplicate`, harness A8 |
| MT9 | Correlated upstream failure. alerts.in.ua and api.ukrainealarm.com both draw on the same Ajax Telegram channel, so two-source agreement is not independent confirmation | **Accepted, named.** Two sources protect against transport failure only. Trigger to reopen: either service moving to its own acquisition, or the ADS-B channel landing as a genuinely independent observation | not testable in-tree; recorded in `docs/DECISIONS.md` D-010 |
| MT10 | Access revoked without cause. Both Ukrainian feeds grant access revocable at any time with no notice, and the ukrainealarm contract changes unilaterally by being reposted | **Accepted, named.** Mitigated by more than one source and by hashing the contract on each run (T12). Trigger to reopen: a Polish channel with a stated availability commitment | T12 acceptance test, not yet implemented |
| MT11 | An unreachable source is read as a quiet one, so an outage looks like an empty sky | `SourceUnavailable` is raised only for reachability; content failures never produce it. The two paths cannot be confused by a caller | harness A10, `test_telegram.py::test_an_unreachable_source_refuses_rather_than_returning_nothing` |
| MT12 | The page is a window of roughly twenty messages. During a mass alert the channel emits more than that between two polls, and the skipped messages leave no trace, so an overflow reads as a quiet channel | Post ids are compared across polls and the skipped count is reported. Where it cannot be measured, on a first poll or a page without ids, it is reported as unknown rather than zero | harness A11, `test_sprint5.py::test_f27_a_skipped_window_is_counted` |
| MT13 | The live page carries each message's timestamp in its footer, after the text. A page-wide scan that assumes the opposite order pairs message N's time with message N+1's text: every `ts_source` one message late, silently, during exactly the mass alerts that matter (F50). Not an attacker's move but the same damage as one: a systematic falsification of the input the lead-time claim rests on | Messages are isolated by their `data-post` anchor and the timestamp is searched within the block only, so the pairing cannot cross a message boundary by construction. The page fixture is a captured live order, not a synthetic one written to the parser's assumption | harness A12, `test_telegram.py::test_f50_footer_time_pairs_with_its_own_message` |
| MT14 | The channel's vocabulary drifts on its own schedule. A tag the area map has never seen, in a message that also names an oblast in prose, produced a warning naming the wrong place: a guess from the table that scores 0 of 20, attached to an event, while the unknown tag was reported separately as though nothing had been decided (F60). A report naming the wrong place is worse than no report, because it is actionable | A message whose tags resolve to nothing returns no classification at all, so the unknown tag is the only outcome. The prose fallback is reachable only from messages carrying no tags | harness A13, `test_areas.py::test_f60_an_unknown_tag_does_not_fall_back_to_the_oblast_table` |
| MT15 | An all-clear carries a list of areas where the alert is *still running*, written in prose rather than as tags. The tag path cannot see that list, so a message saying "cleared here, still dangerous there" reached the store as an all-clear and nothing else: 5.2% of comparable design-window messages, 4,064 area mentions, none recorded (T37). Not an attacker's move, and the same damage as one — the system is silent about a place its own source called dangerous | Every area a message names becomes its own event, and the continuation list is read from the prose after the marker and carries `AreaRole.CONTINUATION`. Where one area is both cleared and listed as continuing, the contradiction is kept as `PARTIAL_CLEAR` rather than resolved into two confident rows | harness A14, `test_sprint8.py::test_t37_a_continuation_list_produces_more_than_one_event` |

## Residual, stated rather than hidden

A source that is subtly late rather than silent degrades lead time without
tripping anything. Not currently detected. T5 plans a rolling latency
distribution with an alert on drift.

The output channel does not exist yet, so its threats (a compromised publishing
path sending arbitrary warnings to a trusting audience) are not modelled here.
They land with the channel, in the same version, or the channel does not land.
`docs/MOBILE.md` drafts the rows they will become.

*Amended 0.7.0.0.* That deferral was written while the plan misstated the
project as private-circle only (F53). At the project's actual scope, a public
warning system, the same compromise is a mass-notification event whose harm is
not proportional to recipient count: a false airspace alarm arriving at once
across a region is an incident in its own right. The deferral stands, because
modelling a channel that does not exist produces rows nothing can test, but the
priority does not: these rows are a precondition of the public tier rather than
a follow-up to it, and `docs/MVP.md` Audience D states them as blockers.

## What the maintainer can do

A single maintainer cannot notice a structural claim going stale, which is why
`tests/lint_*.py` and `tools/*_audit.py` assert structure rather than trusting
review. The specific failure being guarded against is documentation describing a
protection the tree no longer implements.
