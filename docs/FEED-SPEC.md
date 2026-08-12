# What a machine-readable Polish alerting feed would have to be

Version: 1.4 / 2026-08-12
A specification, written from the position of someone who tried to build against
one and found there was nothing to build against. The Ukrainian equivalent was
consumed and measured over a corpus of 118 days; the work of building against it
is a weekend project, and the parser at the centre of it took two afternoons.
Both facts are stated because the argument below rests on the second: what the
convention enables is cheap to exploit, and that is the point. Companion:
[`docs/CHANNEL.md`](CHANNEL.md), which is the measurement this rests on, and
T8a in [`../TODO.md`](../TODO.md), which is where the gap was first recorded.
T8a is the measurement this document argues from and has not yet made: a
verdict per Polish source against the five properties in section 3. Until it
exists, section 2 rests on `[reported]` and `[assumption, unmeasured]` rows
rather than on a survey.

```
Note: this document describes a feed that does not exist. It is not a claim
      about anyone's competence and makes none. It is a technical description of
      an interface, written by someone who consumed the Ukrainian equivalent for
      118 days of it and can therefore say precisely which properties turned out
      to matter and which did not
```

## Contents

1. [The difference is a hashtag](#1-the-difference-is-a-hashtag)
2. [What is available on the Polish side today](#2-what-is-available-on-the-polish-side-today)
3. [The specification, which is mostly not mine](#3-the-specification-which-is-mostly-not-mine)
4. [Silence must not mean safety](#4-silence-must-not-mean-safety)
5. [The objection, and the answer](#5-the-objection-and-the-answer)
6. [What this is not asking for](#6-what-this-is-not-asking-for)
7. [How to disagree with this document](#7-how-to-disagree-with-this-document)

---

## 1. The difference is a hashtag

Measured, on 48,540 real messages from the public Ukrainian air-alert channel
over 99 nights ([`docs/CHANNEL.md`](CHANNEL.md)):

| Quantity | Value |
| --- | --- |
| Messages labelled with the affected area and its unit type | **99.34%** |
| Distinct area labels in the whole period | 127 |
| Labels resolving to a unique code in the state register | 126 automatically, 127 with one contextual decision |
| Agreement between the label and the message's own prose | **99.997%** on 38,521 comparable messages |

The label is a hashtag: `#Харківський_район`, `#Львівський_район`,
`#м_Харків_та_Харківська_територіальна_громада`. Nominative case, underscores
for spaces, unit type spelled out.

**What that convention cost the publisher: nothing.** It is a formatting rule in
a message a person writes anyway. **What it enabled on the receiving side:** one
person, in an afternoon, built a parser that resolves every area to a national
register code with a measured error rate of zero on the design window. No API,
no token, no agreement, no procurement, no funding.

A country under daily attack on its own territory found the time to adopt a
naming convention in its public alert messages. That is the entire technical gap
being described here.

## 2. What is available on the Polish side today

Stated without evaluation, because the point is the interface rather than the
institution.

| Channel | Reaches | Machine-readable |
| --- | --- | --- |
| Sirens | People within earshot | No, and cannot be |
| RCB alert (SMS) | Roughly 14 million recipients | No. Free text to a phone |
| RSO application | Its installed base | Partially, and not as an open stream |
| The announced MSWiA application | Not yet released | Unknown |

**Measured rather than assumed, 2026-08-09.** The full metadata catalogue of the
open data portal was downloaded and searched: 1,510,768 resources, filtered on
alarm, warning, siren, RCB, civil protection, crisis management and evacuation.
Twenty-nine datasets matched and none is a stream. The Government Centre for
Security is present in the catalogue and publishes two datasets, both documents,
neither flagged as dynamic data. IMGW publishes meteorological warnings, so that
category of warning did reach open data. Dynamic feeds exist on the portal and
the portal supports them: air quality is published with an API and flagged
dynamic. What is missing is not the capability and not the publisher; it is this
one category of data.

**What the publisher's own entries look like, measured.** The Government Centre
for Security publishes four resources across those two datasets: XML and HTML,
all at **openness level 3**, all with an update frequency of *not applicable*.
Read against the standard, that is not a formatting failure. XML is permitted at
level 3 and HTML is only discouraged above it, so the entries are correct. What
they are is **static documents**, correctly declared as such.

Level 3 is also the exact level at which the standard says API delivery is
recommended, precisely so that data can be machine-processed. The publisher is
therefore already at the threshold the standard describes, and publishing files.

The conclusion this points to is narrower and harder to answer than the one this
document originally reached for. **The gap is not competence, format or
platform. It is that alerting messages are not treated as data at all.** The
category exists on the portal for air quality, complete with a dynamic API. For
alerting it does not exist, and the publisher who would own it is already
present, already compliant, and already publishing something else.

The consequence is one sentence long. **Nobody outside the state can build
anything on Polish alerting data**, however competent, however willing, and
regardless of what they intend to build: a research dataset, an accessibility
tool for deaf users, a display for a school, a check on how fast the system
actually is.

This project hit that wall directly. The Ukrainian side of the border is
measured down to the raion, 118 days of it, 60,680 messages. The Polish side is
zero. The asymmetry is not about data volume; it is about format.

The catalogue search is reproducible: download the portal's own catalogue
metadata, unpack, and filter the description fields. The command is in this
repository's history and the figures above come from running it, not from
browsing the site.

## 3. The specification, which is mostly not mine

**Four of the five properties below are already required or recommended by the
Polish state's own technical standard for public data** (*Standard techniczny*,
Ministry of Digital Affairs, defining the minimum technical requirements for
public data published in the Central Repository of Public Information). This
section is therefore not a proposal. It is a note that an existing standard has
not been applied to one category of data.

The fifth property is genuinely absent from the standard, and it is the one that
matters most for alerting. It is marked as a gap rather than as a request.

| Property | Status in the standard |
| --- | --- |
| Public, no application process | Portal states that data may be re-used without submitting a request |
| Area by register code, not prose | The standard names TERYT as the authoritative register and defines the *universal address*, stating outright that it is not for human reading but for a system |
| Timestamped transitions | ISO 8601 required, `yyyy-mm-ddThh:mm` |
| Versioned schema, served over an API | Openness level 3 and above: API recommended, JSON per RFC 8259 with the JSON API standard; level 4 requires JSON-LD with full semantic context. A separate API Standard exists |
| **A heartbeat** | **Absent.** See section 4 |

The four rows above need no argument from me. What follows is the reasoning for
each in the specific case of alerting, and then the gap.

**One. Public, unauthenticated, no application process.** A feed behind an
application form is not public infrastructure; it is a permission regime with an
RSS icon. The Ukrainian channel needs no token, which is why anyone can verify
the measurements in this repository rather than take them on trust.

**Two. Areas identified by register code, not by prose.** The standard makes
this point better than I can: it introduces the universal address specifically
so that a system, rather than a person, can resolve a location, and it names
TERYT as the register that holds the codes. A message saying `powiat
biłgorajski` in a sentence forces every consumer to write a name matcher and get
it subtly wrong. This project spent a measurement discovering exactly that: name
matching against a register reached 6.06% where the source's own structured
labels reached 99.34%.

**Three. State transitions, timestamped, both directions.** An alert beginning
and an alert ending are two events and both matter. A feed publishing only the
beginning leaves every consumer to guess when it is over, and guessing produces
the failure this project refuses everywhere: an unknown state resolving to a
safe-looking one.

**Four. A versioned schema, served over an API.** The standard already
recommends API delivery from openness level 3 and warns, in its own words, that
level 3 data still requires a human to work out what each field means. Alerting
data is exactly where that ambiguity is expensive, which is the argument for
going to level 4 rather than stopping at a published file.

**Five. A heartbeat.** Not in the standard, and the standard is not wrong to
omit it in general: it describes how a *dataset* is formatted and described,
which is a different problem from how a *stream* signals that it is alive.
DCAT-AP carries `accrualPeriodicity`, but that is a declared update frequency in
the metadata, not a signal in the data. For alerting the difference is the whole
thing, and it is section 4.

## 4. Silence must not mean safety

The single most important property, and the one that is invisible until the day
it matters.

If a feed publishes only when something happens, then **a dead feed and a quiet
sky look identical**. Every consumer that renders silence as "nothing is
happening" is one outage away from telling people they are safe at the moment
they are not. This is not hypothetical: it is the founding invariant of this
repository, that unknown never resolves to clear, and several entries in its
defect log are instances of getting it wrong internally.

The fix is trivial and has to be designed in from the start: a periodic
heartbeat carrying "as of this timestamp, the state is X", published whether or
not the state changed. A consumer that has not seen a heartbeat within the
stated interval knows it is blind, and can say so, instead of displaying calm.

An alerting feed without a heartbeat is a system that fails silently by design.

**Measured, and it is worse than the argument above assumed.** This project
ran its own collector against the Ukrainian channel unattended for a night and
counted: **eleven of ninety-five polls failed** in a twelve-hour journal, and
nine of sixty in the two-hour window measured most closely. Consecutive
failures happen; the longest run was two and the longest gap between
successful reads was seven minutes, against a ten-minute staleness threshold.

The number that matters is not the failure rate. It is that **the consumer
could tell**, on every one of those eleven occasions, because the channel
publishes continuously enough that absence is legible. A feed that publishes
only on transitions would have made all eleven indistinguishable from a quiet
sky, and the consumer's own instrumentation could not have recovered the
difference from the outside at any cost.

The heartbeat is therefore not a courtesy to consumers who want a liveness
signal. It is the only thing that makes a consumer's error rate measurable at
all.

**Why the standard does not cover this, and why that is not a criticism of it.**
The technical standard describes how a dataset is formatted, described and
licensed. A dataset is a thing that sits still; a stream is a thing that must be
observed to be running. The two need different guarantees, and only the first is
in scope. DCAT-AP's `accrualPeriodicity` declares an intended update frequency
in the metadata, which tells a consumer what to expect and nothing about what is
happening now. For most public data that gap costs nothing. For alerting it is
the difference between a quiet night and a dead system, and a consumer cannot
tell them apart from the outside.

## 4a. Three properties learned by shipping, not by specifying

Sections 1 to 4 were written before this project had a consumer in production.
It has had one since 2026-08-11, and three requirements emerged that the
original five did not cover. They are numbered separately because they are
weaker claims: each rests on one deployment rather than on a corpus.

**Six. A cap, published, and a flag saying when it bound.** [measured]

The producer here caps its event window at 5,000 and publishes a `truncated`
flag. Building the consumer showed why both halves are necessary. Without the
cap, a window that grows for any reason - a clock skew, a backfill, a schema
change - is unbounded work for every reader at once; measured on the site, an
unbounded window rendered a 5.6 MiB page from 20,000 events. Without the flag,
a bounded list and a quiet window look identical, which is section 4's failure
wearing a different hat.

**The consumer must also bound it independently**, which is the part that is
easy to get wrong. This project's own site delegated the bound to the producer
and did not check it, and the two are deployed separately by hand. A limit
that lives only on the publishing side is a limit that holds until the day the
two versions differ.

**Seven. The window's left edge, published rather than derived.** [measured]

A feed carrying "here are the transitions in the last twenty minutes" is not
enough. The consumer needs the timestamp the window starts at, because a
device that was asleep for twenty-five minutes cannot otherwise tell a gap
from a quiet stretch, and neither can the person holding it. Deriving the edge
from the publication time works only while the consumer's clock and the
producer's agree, and the case that matters is exactly the one where the
consumer has been away.

Cost to the producer: one field. Value to the consumer: the difference between
"nothing happened" and "you did not see what happened", which is section 4's
invariant applied to the reader rather than to the system.

**Eight. A version policy that says what happens during the changeover.**
[measured, and it cost a deployment window]

The fourth property asks for a versioned schema. That is necessary and not
sufficient. When this project moved its own contract from v2 to v3 the payload
was a strict superset - every field a v2 consumer required was still there -
and the consumer still refused it, correctly, because it refuses versions it
does not recognise. The two had to be deployed inside one window with the
producer first by minutes, and the page was blind in between.

A version number without a stated overlap period pushes that coordination onto
every consumer, and a public feed has consumers it has never met. What the
policy has to state: how long the previous version keeps being served, what
ends that period, and whether a consumer may treat an unknown minor version as
readable. This project has not written its own policy yet, which is recorded
in its backlog as the unfinished half of the task that introduced v3. The
omission is survivable here because there is one consumer and the same author
controls it. That is exactly the circumstance a public feed does not have.

## 5. The objection, and the answer

**"A public alerting feed helps an adversary measure our response."**

The objection deserves an answer rather than a dismissal, and there is one.

Ukraine, attacked daily, publishes exactly this and has done so throughout the
war. The alert state is already observable to anyone with ears, a window, or a
phone: sirens are audible, RCB messages go to fourteen million people, and both
are public the moment they are issued. What is currently unpublished is not the
information. It is **the format**.

An unreadable format does not protect an adversary's target from being
observed. It excludes citizens, researchers, municipalities and accessibility
tooling from using information that was already published, while an adversary
with a receiver, a phone, or someone standing outside is unaffected.

If some specific field genuinely carries risk, the answer is to specify that
field out of the feed and say so, which is what a specification is for. It is
not an argument against publishing the rest.

## 6. What this is not asking for

- **Not a change to who decides.** The state decides what an alert is and when
  to issue one. This concerns the format in which an already-taken decision is
  published.
- **Not a new detection system, sensor or budget line.** The information exists
  the moment the siren sounds.
- **Not an obligation on anyone to consume it.** A feed nobody reads costs
  nothing; a feed that does not exist costs every potential reader.
- **Not a replacement for anything.** Sirens will remain the fastest channel to
  a person who is asleep, and nothing here changes that.

## 7. How to disagree with this document

Written as a specification rather than an opinion so that disagreement can be
specific. Useful forms:

- A property in section 3 that is wrong, or one that is missing and turns out to
  matter in practice. Note that four of the five are quotations of the state's
  own technical standard, so disagreement there is disagreement with that
  document rather than with me.
- A concrete reason why TERYT codes in the payload are harder than they look.
- A pointer to a Polish source that already meets some of this and that the
  author has not found. **This would be the most useful reply of all**, and T8a
  in the backlog exists precisely because the search was inconclusive rather
  than exhaustive.
- Evidence that the security objection in section 5 has a stronger form than the
  one answered here.

Corrections to this document are recorded like every other finding in this
repository: with what was wrong, who found it, and what changed.
