# MAVO

**An early-warning system for air threats, built after hours. A private
project, pre-alpha, and nobody receives a notification from it today.**

For a reader who does not write code.

```
Document:  docs/BRIEF.md, version 2.3
Measured:  2026-08-17, against STATUS.json at 0.32.9.0
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

One public Telegram channel on which Ukrainian services declare alerts.
**61,041 messages** were collected, contiguous, with no gaps, and with a
checksum recorded over the whole set. The measurements in this document come
from the design window, which is **99 nights and 48,540 messages**; the rest of
the corpus is held back, and that is covered below.

A single source is a serious weakness and the documentation says so. Two
commercial APIs that looked like an independent alternative turned out to read
the same channel, so using them would have produced the feeling of
corroboration without any.

The channel has one property that determined the whole design: **99.3% of
messages carry a hashtag naming the district**, in the nominative, with
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
would have scored 22 wake-ups and 0 hits in that window. For scale: western
districts see 5.73 alert episodes a week on average, and episodes covering the
whole west 1.56 a week.

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

## How you would know the author is not fooling himself

With a private project this question matters more than the technology, so here
are specifics instead of assurances.

**The defect log holds 87 entries.** Each states what broke, why nobody
noticed, and what class of error it was. Entries against the project's own
interest are in there too, including the 0 of 20 above, and one where the
documentation claimed something was checked and it was not. Separately, **31
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

**The gate is single and mechanical.** One command runs 410 tests, of which 13
are scripted attacks against the project's own controls; code coverage is
96.61% against a floor of 95% that is never lowered. The attacks are themselves
checked: 12 of 13 were verified by deliberately breaking the control they guard
and requiring the attack to catch it. The one without such verification is
printed as unverified on every run rather than passed over.

## Where it actually is, without flattery

Working: collection, district recognition from hashtags, distance to the
border, the report, the file that feeds a web page, the map, and the web page
itself, publicly running at a temporary address. The permanent address does not
exist yet, and the temporary one is not fit to circulate.

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

Not started: the things that decide whether this ever reaches people. There is
no legal position on distributing warnings to strangers, and not one
conversation has happened with anybody who would receive them.

**Nobody receives a notification today and nobody will until those two things
happen.** A public page is not a public warning service, and the documentation
says so in those words.

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

If the people this is being built for say they do not want it, it ends. They
have not been asked yet, and that is currently the largest hole in the project.

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

*Which figures in this document are enforced mechanically?* Every measured one
comes from `STATUS.json`, and a disagreement between it and the tree fails the
gate. Figures labelled as somebody else's, as an illustration, or as coming
from a release review are not enforced, and they say so.

---

**One-line version:** MAVO reads public Ukrainian air-raid alerts and shows, in
Polish, which border district is under alert right now and how far that is from
the border; it deliberately predicts nothing, because with three violations a
year no predictive rule can be honestly defended; it is pre-alpha and nobody
receives notifications yet.
