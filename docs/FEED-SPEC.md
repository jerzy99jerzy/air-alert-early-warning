# What a machine-readable Polish alerting feed would have to be

Version: 1.0 / 2026-08-09
A specification, written from the position of someone who tried to build against
one and found there was nothing to build against. Companion:
[`docs/CHANNEL.md`](CHANNEL.md), which is the measurement this rests on, and
T8 in [`../TODO.md`](../TODO.md), which is where the gap was first recorded.

```
Note: this document describes a feed that does not exist. It is not a claim
      about anyone's competence and makes none. It is a technical description of
      an interface, written by someone who consumed the Ukrainian equivalent for
      four months and can therefore say precisely which properties turned out to
      matter and which did not
```

## Contents

1. [The difference is a hashtag](#1-the-difference-is-a-hashtag)
2. [What is available on the Polish side today](#2-what-is-available-on-the-polish-side-today)
3. [The specification](#3-the-specification)
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

The consequence is one sentence long. **Nobody outside the state can build
anything on Polish alerting data**, however competent, however willing, and
regardless of what they intend to build: a research dataset, an accessibility
tool for deaf users, a display for a school, a check on how fast the system
actually is.

This project hit that wall directly. The Ukrainian side of the border is
measured down to the raion, four months of it, 60,680 messages. The Polish side
is zero. The asymmetry is not about data volume; it is about format.

## 3. The specification

Five properties, in the order they turned out to matter while consuming a feed
that has them. Nothing here requires new detection capability, new
infrastructure, or a change to what is decided or when. It describes how an
already-published decision is expressed.

**One. Public, unauthenticated, no application process.** A feed behind an
application form is not public infrastructure; it is a permission regime with an
RSS icon. The Ukrainian channel needs no token, and that is why anyone could
verify the measurements in this repository rather than take them on trust.

**Two. Areas identified by register code, not by prose.** Poland has
[TERYT](https://eteryt.stat.gov.pl/), the state register of territorial units,
which is the exact counterpart of the KATOTTG codifier this project resolves
Ukrainian areas against. A message saying `powiat biłgorajski` in a sentence
forces every consumer to write a name matcher and get it subtly wrong. A message
carrying the TERYT code forces nobody to write anything. This one property is
the difference between a feed and a press release.

**Three. State transitions, timestamped, both directions.** An alert beginning
and an alert ending are two events and both matter. A feed that publishes only
the beginning leaves every consumer to guess when it is over, and guessing
produces exactly the failure this project refuses everywhere: an unknown state
resolving to a safe-looking one.

**Four. A versioned schema, and a stated deprecation policy.** Not because the
schema will be elegant, but because consumers appear over years and a silent
field rename breaks all of them at once. Version in the payload, old readers
supported for a stated period.

**Five. A heartbeat.** See the next section, because it is the property most
often left out and the one whose absence is most dangerous.

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
  matter in practice.
- A concrete reason why TERYT codes in the payload are harder than they look.
- A pointer to a Polish source that already meets some of this and that the
  author has not found. **This would be the most useful reply of all**, and T8
  in the backlog exists precisely because the search was inconclusive rather
  than exhaustive.
- Evidence that the security objection in section 5 has a stronger form than the
  one answered here.

Corrections to this document are recorded like every other finding in this
repository: with what was wrong, who found it, and what changed.
