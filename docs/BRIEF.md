# MAVO

**An early-warning system for air threats, built after hours. A private
project, pre-alpha, and nobody receives a notification from it today.**

For a reader who does not write code.

```
Document:  docs/BRIEF.md, version 2.5
Measured:  2026-08-31, against STATUS.json at 0.50.0.0, and this time the
           figures were recomputed rather than carried over. Version 2.4 bore
           the same line while four figures inside it came from 0.32.9.0; what
           that means is set out under "What you do not have to take on trust".
           The corpus figures were measured on 2026-08-17 and are unchanged;
           what moved is the source, and that is said where it happened
Audience:  anyone who wants to understand this project without reading the
           code: a journalist, an analyst from another field, a prospective
           recipient, a reviewer deciding whether the author is careful
Companion: BRIEF-PL (the same document in Polish, and the original),
           FOUNDATIONS (the same claims with provenance labels), METHODOLOGY
           (the defect log)
Note:      no term is used before it is explained. Every number carries the
           same provenance label it carries everywhere else in this
           repository, and every measured one is pinned in STATUS.json
```

---

## The whole thing in one paragraph

When missiles or drones fly over Ukraine, Ukrainian authorities declare alerts
for named districts. Those declarations are public and they appear
immediately. If you live in Hrubieszow, the fact that an alert has just been
declared for a district 40 kilometres away is relevant, and it is available
earlier than anything the Polish side will say. MAVO reads those declarations
and shows them in Polish: which district, what kind of threat, how many
kilometres to the border.

That is all of it. It does not predict whether anything will cross into
Poland.

## Where it came from

On the night of 29 to 30 July 2026, during a mass Russian missile attack on
Ukraine, a Kh-101 cruise missile entered Polish airspace. It was detected at
03:40 and lost from radar at 03:46, six minutes later, and came down in a field
near Tarnawa-Kolonia in Lubelskie, roughly a hundred kilometres inside the
country `[reported; Polish operational command via national press]`.

Six minutes. In that window the fastest information available to a resident
was the sirens, which sound only once something is already heading this way.

The starting point for this project is not those six minutes. It is **the hour
before them**. Alerts in Ukrainian border districts are declared considerably
earlier, and nobody puts them in front of a Polish reader in a form that can be
read in three seconds at half past three in the morning.

One detail from that night belongs here rather than in a footnote, because it
is the clearest statement of what this project refuses to do. Ukrainian
fighters pursued the missiles up to the border and tried to destroy them, and
their radar signature was hard to tell apart from the missiles themselves,
which delayed the decision on the Polish side `[reported]`. Whether anything
crosses depends on that: on interceptions, on pursuits, on decisions taken in
the air. None of it is in any feed this project can read.

## Where the data comes from

**This section changed on 2026-08-30, and the change is the most instructive
thing in this document.**

Until then, the source was one public Telegram channel on which Ukrainian
services declare alerts. **61,041 messages** were collected from it,
contiguous, with no gaps, and with a checksum recorded over the whole set. The
measurements below still come from that corpus, and specifically from the
design window of **99 nights and 48,540 messages**; the rest is held back, and
that is covered further down.

On 2026-08-29 at 04:55 UTC that channel stopped publishing. It stayed silent
for about thirty-four hours, through a night of attacks that other reporting
described as continuous. Nothing was wrong with this project: it kept saying
its picture was old, and how old, which is what it was built to do. But a
system that reports its own blindness accurately is still blind, so the next
day the source was switched to the official Ukrainian alerting API, which had
been publishing throughout. The channel is still read, not as a second source
but as a watchman: if the publisher comes back, this project will notice and
will say which of the two spoke.

**Two feeds is not two sources, and the distinction is the whole point.** Both
draw from the same upstream, so agreement between them measures the delivery
path and nothing else. A single source is a serious weakness and this
documentation says so rather than dressing it up. The commercial APIs that
looked like an independent alternative turned out to read the same channel,
which is why using them would have produced the feeling of corroboration
without any of the substance.

The switch cost something specific and it is named rather than hidden: the API
has one type for everything that flies, so where the channel would say what
was in the air, the API often does not. For a few hours the map translated
that silence into "missile", which was this project's error and not the
publisher's word; it now reads **type not stated**, which is what is actually
known.

The channel had one property that determined the whole design, and it is why
the corpus below is worth what it is: **99.3% of messages carry a hashtag
naming the district**, in the nominative, with
underscores for spaces. The channel labels its own messages and this project
reads the label. There is no machine learning and no name recognition in prose,
because there is nothing to recognise. The design window holds 127 distinct
hashtags, and **126 of them resolve unambiguously** to a code in the Ukrainian
state register.

The first version of that reader worked differently: it searched message text
for oblast names. Checked against twenty real messages it matched **0 out of
20**. Not because it was badly written, but because it was built on an idea of
how the channel words things rather than on how it words them. That result is
recorded in the repository as a numbered defect, along with why no amount of
code review would have found it.

The rebuilt version resolves an area in **20 messages out of 20** on the same
kind of real sample, and the result is pinned as an assertion so it cannot be
broken quietly. Separately, the hashtag was checked against what the message
says in prose: across **38,521 comparable messages the two agree more than 99.99% of the
time**. That is the only internal check on the geocoder available without a
second source, and it is described as such rather than as independent
confirmation.

## Why it does not predict a crossing

This is the most important part and the only one that needs numbers.

The observation the project started from: every violation of Polish airspace in
the period studied fell on a night of massed strikes against western Ukraine.
That sounds like a ready-made predictor.

The problem: **nights of massed strikes cover roughly 57% of days** `[somebody
else's figure, for a period and an area this project did not measure]`. There
were about a dozen violations in four years, so around three a year.

Build the simplest possible system from that: an alarm on every strike night.
It will fire more than 200 times a year and be right 3 times. It will miss
nothing. And it will tell nobody anything the calendar does not.

There is also a figure of this project's own, measured on this corpus rather
than borrowed. In the design window an alert covered the whole of western
Ukraine on **22 nights**, and the number of reported violations of Polish
airspace on those nights is **zero**. A rule waking people on every such night
would have scored 22 wake-ups and 0 hits in that window. For scale: those 99
nights held 81 alert episodes in western districts, 22 of which covered the
whole west, which is **5.7 and 1.6 episodes a week**. One decimal place,
because with twenty-two events the second one would describe noise rather than
a rate; the full quotients are in `docs/CHANNEL.md`, where they are read by
somebody checking the arithmetic.

You could ask whether such a system is not, even so, slightly better than
nothing. Probably yes, slightly. **But with three events a year that cannot be
demonstrated.** One unusual night moves the whole result. It is like claiming a
coin is loaded after twelve tosses: it might be, but not on that evidence.

So the project contains a component whose only job is to **try to prove each
proposed alarm rule worthless**. It measures how far the rule beats the
calendar and takes the pessimistic end of the confidence interval, asking not
"what did we get" but "what can still be claimed if we happened to be lucky". A
rule may not wake anyone until it survives that. One has, for missile threats.

There is also a reason deeper than the statistics. Whether something crosses
the border depends on air defence, falling debris, navigation failures and an
adversary's decisions. None of those is visible in the available data. More
data will not change that, because what is missing is not volume but a kind of
observation.

## What it says, and what it refuses to say

It says: which western Ukrainian districts are reporting an alert right now,
of what kind, how far they are from the Polish border, and at what moment that
picture was assembled.

It refuses three things, and these are decisions rather than technical limits:

**No probability of anything.** It computes none.

**No instructions.** State services instruct. This reports.

**No single distance, only an interval.** "0-46 km" `[illustration]` means the
nearest edge of that district lies somewhere in that range. A single figure
would imply a precision that does not exist, and false precision with a decimal
point on it is worse than stated uncertainty. Distances are computed for 127
areas; 5 intervals reach zero, meaning the area touches the border, and the
nearest area centre lies 14.2 km from it.

There is a fourth refusal, less obvious and the most important: **silence never
means "safe"**. If collection stops working, the page says "I do not know what
is happening", rather than showing an empty map. An empty map and a broken
system look identical and mean the opposite, and the entire design is arranged
around that distinction.

## What you do not have to take on trust

With a private project this weighs more than the technology, so specifics
instead of assurances. Every one of them can be checked without asking the
author for an opinion.

**The defect log holds 121 entries.** Each states what broke, why nobody
noticed, and what class of error it was. Entries against the project's own
interest are in there too, including the 0 of 20 above, and one where the
documentation claimed something was checked and it was not. Separately, **46
design decisions** are recorded, each with the condition that would reopen it.

**Part of the data was sealed before anyone read any of it.** 20.01% of the
collected messages is set aside and has not been opened. You cannot tune a
system against evidence you have not seen, and that is the only way a later
result means anything. The whole corpus carries a recorded checksum and a
confirmed contiguity, so substituting or excising a stretch of it is
detectable.

**Every figure in the documentation carries a provenance label:** measured,
reported, inferred, assumed. The 57% above is somebody else's figure and is
labelled as such, including a note that the source may have meant a different
area than this project does.

**The gate is single and mechanical.** One command runs 646 tests, of which 13
are scripted attacks against the project's own controls; code coverage is
95.45% against a floor of 95% that is never lowered. The attacks are themselves
checked: 12 of 13 were verified by deliberately breaking the control they guard
and requiring the attack to catch it. The one without such verification is
printed as unverified on every run rather than passed over.

**And this is the place where this document tripped over itself.** Four of the
figures above were untrue in version 2.4 of this file: 87 defects against
the 118 logged at the time, 31 decisions instead of 45, 410 tests instead of 642, and coverage of
96.61% instead of 95.42%. They came from a release seventeen numbers back. The
prose around them was rewritten when the data source changed, nobody recomputed
the figures, and the document header claimed somebody had. No check saw it,
because the gate compared the two briefs against each other and against two
pins, one of which was disabled by a condition cutting off values below a
thousand. A defect against the project's own interest, in the section whose
entire content is the claim that the figures are guarded. Logged as F140 and
closed by a check that reads this file figure by figure, compares the two
language versions by value and by count, and **was shown failing before it was
allowed to pass**: six deliberately introduced errors, six caught.

## Where it actually is, without flattery

Working: collection, district recognition from hashtags, distance to the
border, the report, the file that feeds a web page, the map, and the web page
itself, **publicly reachable at mavo.org.pl since 2026-08-12**. The address is
printed here because a document that says "publicly running" without saying
where is asking to be trusted on the one claim a reader could check in a
second.

On 18 August, during a real raid, an alert covered eight western districts
across four oblasts and the author read that page against the channel while it
was happening. That is the only time this instrument was watched doing the job
it exists for, and **no record was written from it**. The contract files from
that night were preserved, but reading them back with a script compares the
instrument against its own reference tables, so the snapshot alone proves
nothing; the verdicts stayed with the person who made them. A worksheet that
would turn such a night into rows a reader can audit exists, and for 18 August
it holds the questions with none of the answers filled in.

One thing about that page is counted, though, and it is worth saying because
the project had nothing of the kind before: **somebody opens it every day.**
Nobody promotes it, nobody receives notifications from it, and for as long as
traffic has been measured the number of visitors has held at a similar level
from one day to the next. That is an answer to the question of whether anybody
reaches for such an instrument at all, and it is the first affirmative answer
this project has. With the caveat that belongs to it rather than to a footnote:
a counter cannot tell a reader from an indexing robot, so it says that
something fetches this page, not that somebody reads it.

It is tempting to add a second sentence to that: that on the night of an attack
people reach for it more often. **That cannot be defended from the data
collected and it is not claimed here.** The rise on the night of 18 August does
not come from more people arriving, it comes from somebody refreshing, and the
person who refreshed that page all that night was the author. The measurement
begins on the night of the raid itself, so there is no quiet baseline to set it
against, and it falls in the first days after the public launch, when any new
address carries traffic from novelty alone. In the same period there was a
completely quiet day on which visits went deeper than on that night, and a
night of raids during which the source was silent and the traffic showed
nothing at all. A hypothesis to test, not a result to announce.

The distance column was checked three ways, and only one of them is an
independent source: a different geometry and method puts three spot-check
points within 1.1 kilometres. The second re-checks the same outline simplified
differently and finds 0.04 kilometres, which tests the arithmetic rather than
the source. The third measures how wrong the source itself can be, about a
kilometre, and that is a floor rather than a confirmation. `[these three
figures come from a release review, not from the gate]`

Not working well: recognising the **kind** of threat. A kind marker is present
in **19.6% of messages**, and after joining it to the alert state **17.0%**
survives. The rest displays as "type unknown", which is an honest rendering and
not a good result, and it is not described as one. This is a ceiling of the
channel rather than of the parser: every proposed vocabulary extension was
tested against the full corpus and returned no new matches.

Not started: the things that turn a public page into a warning service. There
is no legal position on distributing warnings to people the operator does not
know, and there is no notification channel of any kind: the page is opened,
nothing arrives by itself.

A verification with somebody who would be a recipient has been carried out. It
is written here in the form in which it can be defended rather than the form in
which it looks better: **the conversation happened, there is no record of it,
so until one is written it is testimony rather than measurement.** The check of
18 August has the same shape here and is labelled the same way. Closing this
item takes two conversations and one number: at what alarm rate a recipient
would stop reading them. Until that number is written down, the alarm threshold
stays calibrated against a tolerance nobody has measured, and it is described
that way in this repository.

Correspondence with institutions is under way and deliberately does not live in
this repository: it describes people rather than software, and the gate blocks
such files from entering the tree. This document does not report its state and
its silence should not be read as information in either direction.

**Nobody receives a notification today and nobody will until the legal position
and T11 are closed.** A public page is not a public warning service, and the
documentation says so in those words.

No date is promised, deliberately. Violations happen a few times a year, so no
four-week trial can show whether the system catches them. That is a property of
the phenomenon rather than a scheduling failure, and a promised date would be a
comfortable fiction.

## What would make the author stop

Written in advance, because that is the only time such a list means anything.

If a Polish public alert feed appears, the project loses its purpose and gets
closed rather than repositioned. Whether one already exists was checked: 1,510,768
resources in the Polish open-data catalogue were searched, 29 of them concern
alerting, and the number of machine-readable streams among them is **zero**.
That search covered one catalogue and is not proof that nothing of the kind
exists anywhere; it is proof that none was found where one would sit.

If it turns out that reporting in Polish helps somebody direct fire, work
stops. That looks unlikely, since the data is public and available faster in
Ukrainian, but likelihood is not the argument here.

If the people this is being built for say they do not want it, it ends. The
first such conversation has happened and was not written down, so this
condition stays unchecked rather than met.

## Questions worth asking

For somebody who would rather verify than take this on trust:

*What happens when collection dies in the middle of an attack?* The answer
must be "the page says it does not know", not "the page looks calm". That is
checkable in the code and in the tests.

*How many of these numbers are measured, and how many are reasonable guesses?*
Each carries a label. Check a few at random.

*What does the system do on a night when nothing happens?* It must say "no
western district is reporting an alert", not "safe". The difference is not
cosmetic.

*What has the author not measured yet?* The list is in the repository, sorted
into three priority tiers, and it is longer than the list of what has been.

*Which figures in this document are enforced mechanically?* Until version 2.5
fewer than this document claimed, and that is the place to start. The gate
compared the two briefs against each other only for figures of four digits and
more; everything below a thousand passed unchecked, and that is how four
figures in the section about checking came to drift. From 2.5 every measured
figure in this file is compared against `STATUS.json` by value, and the two
language versions against each other by value and by count; a disagreement
fails the gate. Figures labelled as somebody else's, as an illustration, or as
coming from a release review are not enforced at all, and they say so.

---

**One-line version:** MAVO reads public Ukrainian air-raid alerts and shows, in
Polish, which border district is under alert right now and how far that is from
the border; it deliberately predicts nothing, because with three violations a
year no predictive rule can be honestly defended; it is pre-alpha and nobody
receives notifications yet.
