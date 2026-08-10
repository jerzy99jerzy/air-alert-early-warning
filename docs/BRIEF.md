# BRIEF

What this project is, why the hard part is not the programming, and how to
tell whether any of it is true. Written for a reader who does not write code.

```
Document:  docs/BRIEF.md, version 1.2
Audience:  anyone who wants to understand this project without reading the
           code: a colleague from another field, a potential recipient of the
           warnings, a reviewer deciding whether the author is careful
Companion: FOUNDATIONS (the same claims with provenance labels), COMPUTATION
           (the same arithmetic in full), METHODOLOGY (the defect log)
Note:      no term is used here before it is explained. Where this document
           simplifies, it says so. Every number carries the same label it
           carries everywhere else in this repository
```

## Contents

1. [The one-paragraph version](#1-the-one-paragraph-version)
2. [The observation, and why it is not enough](#2-the-observation-and-why-it-is-not-enough)
3. [Why 57 percent ruins everything](#3-why-57-percent-ruins-everything)
4. [What the system says, and what it refuses to say](#4-what-the-system-says-and-what-it-refuses-to-say)
5. [What separates a detector from a calendar](#5-what-separates-a-detector-from-a-calendar)
6. [The three rules the whole design obeys](#6-the-three-rules-the-whole-design-obeys)
7. [The null result this project was built around](#7-the-null-result-this-project-was-built-around)
8. [Two real defects, told plainly](#8-two-real-defects-told-plainly)
9. [Why you should not simply trust this](#9-why-you-should-not-simply-trust-this)
10. [Where it actually is right now](#10-where-it-actually-is-right-now)
11. [What would make the author stop](#11-what-would-make-the-author-stop)
12. [Glossary](#12-glossary)
13. [Good questions to ask](#13-good-questions-to-ask)

---

## 1. The one-paragraph version

Ukraine publishes air-raid alerts, publicly and within seconds. This project
turns that stream into a picture a person on the Polish side can actually use:
which areas are under alert right now, how intense it is, what is being flown,
and how many kilometres the nearest alerted area is from the border.

It does **not** predict what will cross into Poland, and that is a deliberate
refusal rather than a missing feature. Whether a munition crosses depends on
what Ukrainian air defence brings down, where the debris of an intercepted one
falls, whether a drone loses its way, and on decisions made by an adversary
minutes earlier. None of that is visible in any public feed, so a tool
predicting crossings would be claiming to see something that is not there.

What it does instead is worth more than a bad prediction: on 30 July 2026 a
Russian cruise missile came down in Lubelskie, and the entire episode, from
detection to impact, lasted thirteen minutes. Nothing available to a private
person filled the minutes before that. A live picture of the Ukrainian side does
not tell you to take cover, and it does tell you that tonight is not an ordinary
night.

---

## 2. The observation, and why it is not enough

The starting observation, from public reporting: every violation of Polish
airspace in the observed period happened on a night of heavy strikes against
western Ukraine. Not most. All of them, within the coverage available.

That sounds like a finding. Read it again slowly and it is much weaker than it
first appears, because it describes the wrong direction. It says: *given a
crossing, there was a campaign*. What a warning system needs is the opposite:
*given a campaign, will there be a crossing?*

Those two questions have wildly different answers, and confusing them is one of
the oldest mistakes in reasoning about risk. Almost everyone who drowns was
near water. Being near water is nonetheless a poor predictor of drowning. The
first sentence is true and the second is why it does not help.

---

## 3. Why 57 percent ruins everything

Here is the number that nearly kills the project, and the reason it is stated
on page one rather than buried.

Nights of massed strikes against Ukraine cover roughly **57 percent of days**
in the period studied. Meanwhile, actual crossings into Polish airspace number
roughly **a dozen over four years**.

Now imagine the simplest possible warning system: it fires on every campaign
night. What have you built? A device that lights up on more than half of all
nights, forever, and is right about a crossing perhaps once a year. It has
perfect recall (it never misses a crossing, because it fires on essentially
everything), and it is useless. Worse, it is *dangerously* useless, because it
feels informative. After two months of nightly warnings, the recipient stops
reading them, and the one that mattered arrives into an inbox nobody opens.

The technical name for the 57 percent is the **base rate**: how often the thing
happens anyway, with no system at all. The entire difficulty of this project
sits in one sentence: **a warning is only worth anything if it beats the base
rate**, and beating a base rate of 57 percent with a dozen positive events to
learn from is genuinely hard. Not hard like "needs more code". Hard like
"might be impossible, and the project has to be honest about that."

Consequently the code contains a component whose only job is to try to prove
that each proposed warning rule is worthless. A rule is not allowed to wake
anyone up until it survives that attempt.

---

## 4. What the system says, and what it refuses to say

What it can say:

> 23:41. Alert active in 7 areas of Lviv and Volyn oblast. Nearest: Yavorivskyi
> rajon, 34 km from the border. The channel names cruise missiles. Activity in
> the last hour is above anything in the past thirty days.

What it will never say:

> There is a 12 percent chance of a drone entering Polish airspace tonight.

The second sentence is what everyone wants and it is the one thing this system
cannot honestly produce. A probability of impact would require modelling the
intentions of a hostile actor, and nothing here has access to those. There is
an automated check in the codebase that fails the build if anyone, including
the author in a hurry, adds a function that produces a number of that shape.
The refusal is enforced mechanically rather than left to good intentions.

That distinction, between *this pattern historically preceded events* and *this
is the chance of an event*, is the single most important thing a non-technical
reader can take from this document.

---

## 5. What separates a detector from a calendar

Suppose a rule fires on every night of heavy attacks. It catches every crossing,
so it never misses, and the connection is statistically solid. It is also
useless, and seeing why is the whole game.

More than half of all nights are heavy-attack nights. A rule that fires on all
of them has told you what a calendar would have: it is nearly always on. The
technical name for the trap is the **base rate**, and the measure of escaping it
is **lift**: how much the rule's firing changes the odds compared to knowing
nothing. Lift of 1.0 means it changed nothing.

So the system's second admission test is a floor on lift, and specifically on
the *pessimistic end* of the lift estimate. With about a dozen real events to
learn from, a favourable estimate can be produced by one lucky night, so the
question asked is not "how good does this look" but "how good can we still claim
it is if the sample flattered us". A rule firing on more than half of all nights
fails that test. A rule firing on one night in seven passes it comfortably.

Until August 2026 this test was something else: a ceiling of two alarms per week,
on the theory that a noisier channel trains people to ignore it. The theory is
reasonable and nobody had measured it, and this project's standing rule is that
an unmeasured assumption does not get to be a hard constraint. It was replaced
with the lift floor, which says the same thing where it is actually true: the
problem was never how often a warning arrives, it was warnings that carry no
information. What the change costs is written down in the decision that made it.

## 6. The three rules the whole design obeys

Everything else in the repository is detail. These three are the spine.

**Refuse rather than warn.** The default answer is silence. Every alarm is a
claim, and a claim has to survive an attempt to falsify it before it is
allowed out. A system that warns when unsure is not being cautious, it is
being loud, and loudness is exactly what destroys the channel.

**Unknown is never zero.** If the feed goes silent, that is not calm. If a page
of messages cannot be read, that is not "no alerts". If a statistic cannot be
computed, the output prints the word `unknown`, never the digit 0. This sounds
obvious and is violated constantly in real systems, because zero renders
nicely in a dashboard and "unknown" does not. Several defects in this project's
own log are versions of exactly this mistake, caught and recorded. There is a
deliberate consequence for the phone: if the system goes blind, it sends a
message saying so. Silence must never be the way you learn that something is
wrong.

**Every number comes from measurement, never from memory.** Figures in the
documentation are produced by running the code, and there is an automated audit
that fails the build when a number in the README disagrees with the file the
code writes. The reason is not pedantry. It is that a document which drifts
from reality one number at a time still reads as authoritative, and by the time
anyone notices, the whole thing has to be re-checked from scratch.

---

## 7. The null result this project was built around

This matters more than any feature, so it is told in full.

Before this project existed, the author looked at a long record of attacks and
found something that appeared to explain when they happen. It was plausible, it
had a satisfying story attached, and it looked convincing on a chart. Nearly
everything that goes wrong in this kind of work starts exactly there.

It was then tested properly, against the whole record: 738 nights of attacks
and 87,093 individual munitions, spanning three and a half years. The
correlation came back at 0.013 on a scale where 1.0 is perfect and 0 is nothing
at all, with a p-value of 0.95, which is about as clean a "no effect" as data
ever produces. Two further tests on the same series agreed. The explanation was
abandoned and the variable behind it is now permanently excluded, enforced by
an automated check rather than by a note in a document.

The lesson taken was not "test more carefully next time". It was structural:
with a small number of real events, any flexible statistical method will find a
beautiful pattern in noise, because there is not enough data to punish it for
being wrong. That is why this project uses explicit, readable rules with
thresholds you can argue about, and no machine learning of any kind. A
threshold can be challenged in a sentence. A trained model's weights cannot.

What survived is worth more than what was discarded: the attack record itself,
738 nights of it, is the reference dataset for how attacks distribute in time,
and the procedure is now the standing rule. Any new candidate explanation gets
a directional test on the full series, declared in advance, before it is
allowed anywhere near a rule that could wake someone up.

The habit generalises. There is an entry in the defect log where a rule turned
out to add nothing at all to the one beside it, and it is written down rather
than quietly dropped, which is the same discipline applied to a smaller
embarrassment.

---

## 8. Two real defects, told plainly

From the defect log, which currently holds 54 entries, each with what it was,
why it survived, and what class of mistake it belongs to. Two recent ones,
translated out of jargon.

**The timestamps were all off by one message.** The program reads a public
channel page, which is a list of messages, each with its text and the time it
was posted. The program assumed the time appears *before* the text. On the real
page the time sits at the bottom of each message, *after* the text. So the
program paired every message with its neighbour's clock time. Every event was
recorded a few minutes late, silently, forever.

Why it survived unnoticed for months: the automated test used a fake page,
written by hand by the author, in the order the program expected. The test was
therefore asking the program whether it agreed with itself. It always did. The
class of mistake has a name in this log, "the fixture flattered the code", and
this was its fourth appearance in a different disguise. It matters because in
the fastest threat category the total warning time is about six minutes, so a
few minutes of error is not a rounding issue, it is most of the product.

**Two spellings of the same moment counted as two moments.** Times can be
written with a timezone offset: 21:00 in Warsaw and 19:00 UTC are the same
instant, spelled differently. The storage layer sorted events by comparing the
written text of the time, which only sorts correctly if everything is written
the same way. Nothing enforced that. It had never gone wrong because, by
coincidence, two components that used different spellings had never yet been
run together. The fix refuses timestamps without a timezone outright, rather
than guessing which timezone was meant, because guessing here means inventing
data.

Both defects were found by an outside review that read the project
adversarially. Neither was catchable by any check the project owned, and the
review says so in those words, which is more useful than a claim that the
checks are comprehensive.

---

## 9. Why you should not simply trust this

You should not, and the repository is built so that you do not have to. Four
things a non-technical reader can verify or ask about directly.

**The defect log.** 54 entries, each stating what broke, why nobody noticed,
and what family of mistake it belongs to. Nobody fabricates a document like
that. Its existence is the strongest available evidence about how the work is
actually done, and it is far more informative than any list of features.

**The tests attack the system rather than confirm it.** There is a catalogue of
13 scripted attacks, each corresponding to a specific way the system could be
fooled: a feed that lights up everything at once, a feed that goes silent, a
replayed message, a message flood that overflows the page.

**The tests are themselves tested.** This is the part most projects skip. A
test that never fails is indistinguishable from a test that checks nothing. So
a tool deliberately breaks each protection in a scratch copy of the code, one
at a time, and confirms the corresponding attack test starts failing. If
breaking a protection changes nothing, the test was decorative. Currently 12 of
13 attacks are verified this way, and the one without a mutation is **printed as
unverified on every single run** rather than quietly counted as passing.

**One command checks everything.** `make verify` runs the tests, the coverage
floor, the style and type checks, the documentation audits and the
break-things-on-purpose run. It either says OK or it says which claim is now
false. There is no second, softer path.

---

## 10. Where it actually is right now

Plainly, without flattery.

Working: the machinery. Data collection from the live channel, a corpus of
61,240 real messages spanning 118 days, the storage layer, the statistical
gate, the attack harness, the documentation and its audits.

Not working: the part that reads the meaning of a message. Tested against 20
real messages from the channel, the component that identifies *which region* an
alert refers to matched **0 of 20**. Zero. The reason is instructive: the region
table was written from careful reasoning about how the channel probably words
its messages, and the reasoning was coherent and wrong. The channel names
smaller administrative units than the ones the table expected. No amount of
code review would have caught it, only real messages did, and the failure is
now pinned as a test so it cannot be quietly forgotten.

That redesign is the next block of work, and it deliberately waits for real
data rather than for the calendar.

Nobody receives any notification today, and nobody will until: the redesigned
reader passes its evaluation on a portion of the data that was **sealed away
before anyone looked at any of it** (this is how you keep yourself honest: you
cannot tune a system against evidence you have not seen); a written position
exists on the legal side of distributing warnings; and the intended recipients
have actually been asked whether they want this.

No date is promised, for a reason worth stating: crossings happen a few times a
year, so no four-week trial can demonstrate that the system catches them. That
is a property of the phenomenon, not a scheduling failure, and a promised date
would be a comfortable fiction.

---

## 11. What would make the author stop

A project that cannot say what would falsify it is not a project, it is a
hobby with a build system. The stopping conditions are written down in advance,
which is the only time such a list means anything.

- **No rule beats the calendar.** If, on real data, no rule achieves a
  meaningful improvement over simply knowing that a campaign is underway, there
  is nothing to build and the correct output is a written negative result.
- **The warning time is too short to act on.** If the honest median comes to a
  couple of minutes, the system cannot buy a useful decision and should say so.
- **Official warning gets fast enough.** If Polish public alerting reaches
  people quickly and reliably, this project is redundant, which would be good
  news that happens to end it.
- **The feeds stop being independent enough to be evidence**, or access is
  withdrawn. Both public Ukrainian services in use are already known to draw
  from one and the same upstream channel, which means they are one source
  wearing two hats. This is recorded rather than hidden, and it is the reason a
  second, physically different kind of data (aircraft transponder signals) is a
  prerequisite for one whole category of warning rather than an optional extra.

---

## 12. Glossary

**Base rate.** How often something happens anyway, without any system. The
number every warning has to beat to be worth anything.

**Recall.** Of the events that happened, what fraction did the system catch. A
system with poor recall sleeps through the thing it exists for.

**Precision.** Of the times the system fired, what fraction were real. Poor
precision spends attention.

**Lift.** How much the system's firing changes the odds compared to the base
rate. Lift of 1.0 means it changed nothing, which is the polite way of saying
it is a calendar.

**p-value.** Roughly: the chance of seeing a pattern this strong purely by luck
if there were no real connection. Small is better. It is a filter against
coincidence, not a proof of a mechanism.

**Confidence interval.** The honest range around a number measured on few
events. "7 out of 7" is not certainty, it is a small sample, and the interval
says so out loud.

**Holdout.** A portion of the data locked away, untouched, before any analysis
began. It is spent once, to check whether a result survives contact with
evidence that was not available to shape it. Moving that boundary after seeing
a result is the classic way of fooling yourself.

**Provenance label.** A tag on every load-bearing claim: measured, reported,
inference or speculation. It tells a reader what they are entitled to conclude
from a sentence.

**Shadow mode.** The system runs, decides and logs what it *would* have sent,
but sends nothing. This is how the first weeks of live operation are spent.

---

## 13. Good questions to ask

If you want to test whether this holds up, these are the questions that
actually probe it, phrased so that a vague answer is visible as one.

- What is the base rate, and by how much does your best rule beat it?
- How many real events is that conclusion based on? (The answer is about a
  dozen, and everything follows from that.)
- What have you found that argues against your own thesis?
- Which of your numbers come from real data and which from a synthetic
  generator? (Today, most gate results are the latter, and the code prints that
  caveat on every run.)
- What happens when the feed dies at three in the morning?
- Who asked for this, and at what rate of messages would they stop reading?

The last question is currently unanswered, and it is the one that most needs
answering before anyone's phone rings.
