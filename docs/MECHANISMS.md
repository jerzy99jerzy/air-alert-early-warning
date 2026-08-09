# MECHANISMS

## The base rate is the whole difficulty

Every violation of Polish airspace in the observed period coincided with a night
of massed strikes on western Ukraine, which reads as recall 1.0. Those campaigns
cover roughly 57% of days, so a rule that fires on them has specificity near 0.43
and tells a reader almost nothing they could not get from a calendar.

`lift` makes this visible in one number: precision divided by the unconditional
rate. A lift near 1.0 means the rule added nothing. The gate rejects on alarm
rate before lift is ever consulted, because a rule can be genuinely informative
and still unusable.

## Why Fisher rather than a chi-square

The positive class is roughly a dozen events across four years. A chi-square
approximation is unreliable at those counts, and the exact test is a few lines of
`math.comb`. Adding SciPy for one statistic would weaken a tool whose product is
a measurement with a dependency tree nobody audits.

The test is one-sided: the question is whether the rule fires on event nights
more often than chance, not whether it differs in either direction.

## Why Wilson rather than the normal approximation

At `a = 2, n = 40` the normal interval runs below zero. Wilson stays inside the
unit interval and is honest about the asymmetry, which matters when the whole
point is to avoid overstating a rule.

## Two timing regimes

A missile crossing from an alert in Lviv oblast is roughly six minutes at 700
km/h over 70 km. A drone crossing from Volyn is roughly thirty-three minutes at
180 km/h over 100 km. Both are arithmetic on stated assumptions, not measurements.

The consequence is structural rather than cosmetic: a single threshold cannot
serve both, and the sprint 2 finding is exactly this. The missile filter that
holds the alarm rate inside budget discards every drone night, taking recall to
0.47.

## Poison suppression

A source reporting eight or more distinct areas activating inside 120 seconds is
not describing weather. Suppression is a hard control rather than a scoring
penalty because the attack is free: an adversary who can induce alarms exhausts
the audience's attention and disables the system at no cost to themselves.

## Idempotence by content hash

The hash covers area, state, source timestamp and source identity, and
deliberately excludes ingest time. A feed polled every thirty seconds repeats an
unchanged transition constantly; without this the log grows without bound and the
replay stops reconstructing the past, which would silently break every backtest
built on it.

## Four states, because three could not hold a contradiction

A three-state model has ACTIVE, CLEAR and UNKNOWN, and UNKNOWN carries the whole
weight of "we do not know". Real channel content produced a case it cannot hold:
a message announcing an all-clear for an area and saying in the same message that
the alert continues there.

Folding that into CLEAR is wrong in the dangerous direction. Folding it into
UNKNOWN is wrong in a subtler one: UNKNOWN means the source told us nothing, and
this source told us two things that disagree. A contradiction is evidence about
the source, and evidence discarded is evidence that cannot later be counted.
`PARTIAL_CLEAR` keeps the two distinguishable. Neither resolves to CLEAR and
neither is actionable for an alarm.

## The window gap, and why unknown is not zero

The channel page serves roughly the last twenty messages. At rest a thirty-second
poll sees every one; during a mass alert the channel can emit more than twenty
between two polls, and the extras are simply gone. Nothing downstream would
notice, because a message that was never fetched and a message that was never
sent produce identical silence.

Post ids make the difference observable. Consecutive polls compare the lowest id
of this page against the highest id of the last, and the difference is the number
that passed unseen.

The load-bearing part is what happens when that cannot be computed. On a first
poll there is no previous highest id, and on a page carrying no ids there is
nothing to compare. Both report `unknown`, never `0`. Zero is a measurement
meaning "nothing was missed"; printing it when nothing was measured would make an
unmonitored window indistinguishable from a monitored quiet one, which is the
same defect as UNKNOWN resolving to CLEAR, one layer out.
