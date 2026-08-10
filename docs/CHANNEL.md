# The channel, as it actually is

Version: 1.2 / 2026-08-09
What the source emits, measured on 48,540 real messages, and what that changes.
Companion: `docs/DATA-FLOW.md` (how a message becomes an event),
`docs/METHODOLOGY.md` (F23 and F59), `docs/DECISIONS.md` (D-016, geocoding).

```
Note: every figure in this document was produced by running something against
      the design window of the corpus. Nothing here is an estimate, and the two
      inferences are labelled as inferences where they appear.
```

## Contents

1. [Why this document exists](#1-why-this-document-exists)
2. [The measurement](#2-the-measurement)
3. [The hashtag is the structure](#3-the-hashtag-is-the-structure)
4. [The tag vocabulary is small and closed](#4-the-tag-vocabulary-is-small-and-closed)
5. [Joining the tags to the state register](#5-joining-the-tags-to-the-state-register)
6. [The east-west split is the product](#6-the-east-west-split-is-the-product)
7. [What this corrects](#7-what-this-corrects)
8. [What follows for the parser](#8-what-follows-for-the-parser)
9. [What is still unknown](#9-what-is-still-unknown)

---

## 1. Why this document exists

The shipped classifier scored **0 of 20** against real channel content (F23) and
that number was never explained, only recorded. Two sprints of work were planned
around the assumption that the fix was a bigger vocabulary: the table keyed on
oblast names, the channel emits smaller units, so the answer looked like a
gazetteer of raions and hromadas.

That assumption was wrong in a way that mattered. The channel does not name
areas in prose at all, or rather it does so incidentally. It labels almost every
message with a **hashtag** carrying the area and its unit type explicitly. The
parse problem was never vocabulary. It was that nobody had read the structure.

This document records the measurement that established that, because it is the
single most consequential finding in the project so far and it changes the shape
of three sprints.

## 2. The measurement

Design window only, 2,427 pages, 607 pages above the frozen holdout boundary
refused and counted (D-012a). All figures **measured**, 2026-08-09.

| Quantity | Value |
| --- | --- |
| Messages read | 48,540 |
| Messages carrying a hashtag of the form `#Name_unit` | **48,222 (99.34%)** |
| Messages carrying a bulleted `• Name unit` list item | 5,112 (10.53%) |
| Distinct hashtags in 99 nights | **127** |
| Tag occurrences, all units | 69,676 |
| Tag occurrences by unit | raion 61,531, hromada 7,630, oblast 515 |
| Tags mapping unambiguously to a register code | **126 of 127** |
| Tag occurrences in western oblasts, unambiguous | 2,456 (**3.5%**) |
| Distinct western tags | 36 |

For contrast, the same corpus searched the way the previous approach would have
searched it, by matching truncated register names against message text: **16.56%
of messages as an upper bound and 6.06% as a lower bound**, the gap being stems
that collide across oblasts. Structure beats the heuristic by roughly a factor
of six on the lower bound and needs no stemming, no truncation parameter and no
disambiguation.

## 3. The hashtag is the structure

Every alerting message carries one or more tags of the form:

```
#Харківський_район
#Сумський_район
#м_Харків_та_Харківська_територіальна_громада
#Донецька_область
```

Three properties make this the right parse target and each one removes a class
of guesswork:

**The unit type is explicit.** `_район`, `_громада`, `_область`. Nothing has to
be inferred from the shape of a name, and the same base name at two levels stays
distinguishable.

**The name is in the nominative.** No inflection to strip, which is what forced
stem truncation in the first attempt and what made stems collide across oblasts.

**Spaces are underscores.** Multi-word names survive as single tokens, so a
regex boundary is unambiguous where free text is not.

A second structure exists and is weaker: bulleted lists, `• Вознесенський
район`, in 10.53% of messages. Those carry the unit word too but sit inside
prose, and they appear to accompany the tags rather than replace them. They are
a cross-check, not a parse target.

## 4. The tag vocabulary is small and closed

**127 distinct tags across 99 nights.** That number is what makes this tractable
by hand: a table of 127 rows can be built, read, argued with and checked by one
person in a day, and it is small enough that every row can carry its own
provenance.

The distribution is steeply unequal. The busiest tag,
`#м_Нікополь_та_Нікопольська_територіальна_громада`, occurs 2,703 times; the
quietest western raions occur 56 times each. Nothing in the middle is missing:
the register lists 36 raions across the eight western oblasts, and 36 western
tags appear, so **the west is fully covered at raion resolution**. It is quiet,
not absent, and the two are very different findings.

## 5. Joining the tags to the state register

The join against the KATOTTG codifier (D-016) resolves **126 of 127 tags to a
unique administrative code**. The result is `data/reference/tag_map.csv`: tag,
occurrence count, unit, register name, oblast, KATOTTG code, status, note.

Two rules were needed and both are recorded in the file rather than hidden in
code:

**Composite city-and-hromada tags.** Seven tags take the form
`м_Харків_та_Харківська_територіальна_громада`, naming a city and its hromada
together. The rule is to take the member after `_та_`, which resolves all seven.

**Name drift between the two vocabularies.** `#ВолодимирВолинський_район` has no
entry in the register, which lists `Володимирський` after a renaming. The
channel is still using the older name. This is one instance of a general problem
and it is the reason the file carries a `note` column: **the register and the
channel are two independently evolving vocabularies, and either can change
first.** A single mapping is not enough; an alias table is owed.

The one unresolved tag is `Покровська_територіальна_громада`, which matches four
hromadas in different oblasts. It needs either a hand decision or the oblast
context of the message carrying it, and it is marked `ambiguous_4` rather than
assigned to whichever candidate the register happened to list first.

## 6. The east-west split is the product

Of 69,676 tag occurrences, **2,456 (3.5%) belong to western oblasts** and the
rest to front-line oblasts in the east and south.

For a reader on the Polish side, those 96.5% carry nothing: an alert in Kharkiv
or Zaporizhzhia raion is a fact about a place 900 kilometres away, and a feed
relaying it is noise regardless of how correct it is. The western 3.5% are the
alerts that can plausibly end in an incursion.

**The channel labels the difference itself, in 99.34% of messages.** That is the
filter this project needed and did not have, and it arrives for free rather than
as a classifier that has to be trained, tuned or trusted.

It also means the volume problem solves itself. A western-only report has a
naturally small volume because the west is naturally quiet, without any
artificial rate limit standing in for judgement. The exact figure is what
`tools/west_activity.py` measures, in episodes rather than messages, because an
alert and its all-clear are one event.

**One inference, labelled as such.** Western raion tags cluster in a narrow band:
most raions of Lviv, Ivano-Frankivsk and Zakarpattia oblast occur exactly 56 or
58 times, with Volyn, Rivne and Khmelnytskyi higher at 66 to 134. Independent
local alerts would not produce that uniformity. The reading is that the west is
alerted **simultaneously, as a block**, in multi-raion messages [inference, from
the shape of the distribution; `tools/west_activity.py` reports episode breadth,
which confirms or refutes it directly].

## 6a. What a western-only report would actually say

Measured with `tools/west_activity.py` over the design window, episodes rather
than messages, because an alert and its all-clear are one event.

| Quantity | Value |
| --- | --- |
| Messages carrying a western tag | 1,006 of 48,540 (2.07%) |
| Nights with any western activity | 51 of 99 |
| Episodes | 81 |
| Episodes per week, over all 99 nights | **5.73** |
| Episodes touching 10 or more areas, per week | 2.55 |
| Episodes touching all 36 western raions, per week | **1.56** |

**The distribution is bimodal and that decides the shape of the report.** 22
episodes touch all 36 western raions at once, which is a western-wide alert. 39
touch one to four areas, which is local. The middle is thin. Two message forms
are therefore needed rather than one parameterised form: a western-wide alert is
one line, a local alert is a list of one to four areas with distances. A single
template either sends a 36-item list to a phone at three in the morning or loses
the fact that an alert is local.

The rate that matters is **1.56 western-wide episodes per week**, and it arrived
from the data rather than from a limit anyone imposed. This is the concrete form
of the argument that removed the alarm budget (D-014): the west is quiet enough
that volume regulates itself.

**A correction to an earlier figure in this project's own tooling.** The first
version of the tool divided episodes by *active* nights and reported 11.12 per
week. The denominator was the subset in which the phenomenon occurs, and a rate
computed that way is not a rate a recipient experiences. Corrected to 99 nights
throughout. Same class as F59: a restriction that flatters the number.

## 6b. Tag against prose: the exhaustive check

The channel writes the area name twice, in prose and as a tag, and the two can
be compared without a person. Measured with `tools/consistency_check.py` over
the design window.

| Quantity | Value |
| --- | --- |
| Comparable messages (both a tag and a prose name the map knows) | 38,521 |
| Tag and prose naming the same area | **38,520 (99.997%)** |
| Disagreements | 1, an oblast-tagged damage report whose prose names the raion |
| Messages carrying a tag and no recognised prose area | 9,701 |
| Areas per message | one in 86.7%, tail to eight, nothing above |
| Messages carrying a continuation list | 2,000 (5.2%), naming 4,064 areas |

**Two message classes this check discovered by first disagreeing with itself.**

An all-clear can carry a continuation list: `Відбій ... Зверніть увагу, тривога
ще триває у: - Запорізька область - Пологівський район`. The tag names what was
cleared; the list names where the alert continues. Compared as one set they
produced 1,203 false disagreements, and separating them moved agreement from
96.972% to 99.997%. **The pipeline records none of the continuation areas**
(T37), which for a report whose product is completeness is the sharpest loss it
currently has.

The one tag the register could not disambiguate resolves by context.
`Покровська_територіальна_громада` matches four hromadas by name; in the corpus
it appears beside `Нікопольський район` and `Дніпропетровська область`, which
identifies the one in Dnipropetrovsk oblast. Context settles what a name cannot.

**The limit of this number.** Internal consistency is not truth: a channel
naming the wrong raion in both places would be agreed with. And 9,701 messages,
20% of the corpus, carry a tag with no prose area to compare against, so the
check is silent about them. That population is where the hand sample now points
(T36), rather than at the population an exhaustive check already covers.

## 7. What this corrects

**F23 is now explained rather than only recorded.** The shipped table searched
for oblast names in message text. The channel puts areas in hashtags, mostly at
raion level, and emits an oblast tag in only 515 of 69,676 occurrences. A table
looking for oblast names in prose could not have scored above zero, and its
score was not a matter of an incomplete vocabulary.

**Stem matching is retired as an approach.** The first attempt at this
measurement matched truncated register names against text and reported 16.56%,
attributing the busiest match to Lviv oblast. A one-line grep showed the text
was `Миколаївський район`, a raion of *Mykolaiv* oblast listed beside its
neighbours: the tool had presented an arbitrary first match as an attribution,
and restricting the register to western oblasts had made a colliding stem look
clean. Both defects are fixed in `tools/register_probe.py` and the episode is in
the log as F59.

**The threshold sweep's interpretation is corrected.** Its hourly axis found a
real gradient, and 96.5% of the messages it counted were eastern. The gradient
is a fact about the channel's total volume; reading it as a measure of western
intensification was not supported, and the tag filter is what makes the correct
version measurable.

**The register's role changes.** It is not a search vocabulary. It is a table to
validate tags against and to geocode them with, which is exactly what D-016
argued it should be and is now the only role it has.

## 8. What follows for the parser

The redesign is smaller than planned and its acceptance criterion is sharper.

Parse tags, not prose. Resolve them through `tag_map.csv` to a KATOTTG code, an
oblast and a unit type. Attach the distance to the Polish border from the
precomputed column (T32). Report the message's own wording for means of attack
rather than inferring it. Everything the report needs is then present without a
single inference about geography.

The acceptance criterion for S7 stops being "a better hit rate" and becomes two
countable things: **every one of the 127 tags resolves or is explicitly marked
unresolved**, and a hand-labelled sample of messages agrees with the resolved
area. Presence is already measured at 99.34%; what remains to be checked is
correctness on the message the tag sits in, which no automated probe can assert.

## 9. What is still unknown

- **Whether 127 is stable.** It is 127 across 99 nights. A quiet quarter may
  simply not have exercised every tag, and the holdout is the obvious place to
  test that without spending anything else.
- **Whether tags are ever wrong or missing.** 0.66% of messages carry no tag at
  all and nothing yet says what they are. They may be administrative posts, or
  they may be the ones that matter most.
- **Whether the alias problem is one entry or many.** One name drift was found
  by accident. Nothing has systematically compared the two vocabularies for
  others, and the comparison is cheap.
- **Whether a western episode means anything about a crossing.** Nothing in this
  document touches that, and under D-015 nothing is claimed about it. Measured
  anyway, because the question will be asked: the four busiest western nights in
  the design window coincide with no reported Polish airspace violation, and the
  one confirmed crossing of the corpus period falls in the holdout. A predictive
  rule would have scored 0 of 22 here. See METHODOLOGY, sprint 7.

**A standing assumption, recorded as speculation and used nowhere in the code.**
Incursions are expected to be *deliberately organised against the Polish border*
rather than spillover from strikes deeper in Ukraine. If that is right, no
volume-based predictor could work even with a corpus fifteen times longer,
because the intent it would need to observe is not a function of the intensity
it can see. The reason to write this down is not to act on it. It is to stop
anyone reviving the predictive framing on the grounds that more data would fix
it, and to keep the product where it belongs: reporting what is happening now,
faster than anything else a private person can reach.
