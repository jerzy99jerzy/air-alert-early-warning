# Deployment profile

Version: 1.4 / 2026-08-14
Status: **partly built and running, and the document is behind it.** The
collector runs unattended on a host from 2026-08-11 and the publishing loop
writes the contract; the daemon this document plans is still the shape of what
comes next. What follows describes the endpoint the daemon will present. What
is running today is described in the section immediately below, which was
written after the fact rather than before, and says so.

## What is installed on the hosts, and how far behind it is

[measured where a command output is quoted, otherwise reported]

**This section exists because the rest of this document describes a shape and
not a state, and the two diverged without anything saying so.** Added at
0.32.1.0, carried in from a handover written outside version control, which is
where it had been living.

| Host | Installed | `main` | Consequence |
| --- | --- | --- | --- |
| `vm-mavo` | pre-0.28.1.0 [reported, from a 20.12 s timeout observed in the journal on 2026-08-13] | 0.32.0.0 | F98 is not deployed: the fetch timeout means 20 s per resolved address, not 10 s for the whole fetch. Every margin computed against the constant is wrong on this host |
| `vm-site` | see the consumer repository | | |

Tracked as **T57**, which is tier 1 not because it changes code but because
measurements are being read off a host two releases behind the instrument this
repository documents.

**Installing is not verifying, and the version string is not evidence.** A
repaired archive reissued under an already-built version number makes `pip`
report success while the host runs different code; that has happened here and
cost an hour. The deploy step is therefore: build, copy, `pip install --no-deps
--force-reinstall`, restart, **and then grep the installed module for a string
the release added**. Only the last of those is a check.

## What is actually deployed, as of 2026-08-12

[measured, by reading the host]

Two hosts. The producer polls the channel on a timer and appends to its own
store; a report service renders `state.json` beside it; a push timer carries
the file to the site host over SSH under a forced command that validates it
and installs it atomically.

**Two files from 0.25.0.0 onward, not one.** `mavo report` writes
`state.json` and `feed.json` in the same cycle from the same composition, and
both must cross the push channel. The consequences, each of which is a step
somebody has to take and none of which the gate can check:

- The report unit needs `--feed /var/lib/mavo/feed.json` beside its `--json`.
  Without the flag the file is never written and the consumer's history panel
  is permanently empty with nothing anywhere saying why: absence looking like
  calm, which is the failure this whole project refuses.
- The push unit needs to carry both files, naming its target on each
  invocation. The forced command takes the target as its argument.
- The forced command on the site host is `deploy/accept-state` in the
  `mavo-site` repository. Until 2026-08-12 its only copy was on the host,
  with no version, no test and no history; the entry in `authorized_keys`
  must point at the version-controlled copy, not at whatever is there now.

**The producer and the consumer deploy in one window.** The consumer refuses
any schema version it does not recognise, so a producer at v3 in front of a
consumer at v2 turns the public page blind. Producer first, by minutes.
Companion: `docs/MOBILE.md` (phase M0, the daemon), `docs/OBSERVABILITY.md`
(what it writes while running), `docs/THREAT-MODEL.md` (what it defends
against).

## Contents

1. [The daemon is the first component with an identity](#1-the-daemon-is-the-first-component-with-an-identity)
2. [Egress inventory](#2-egress-inventory)
3. [Jitter is not cosmetic](#3-jitter-is-not-cosmetic)
4. [Endpoint identity on macOS](#4-endpoint-identity-on-macos)
5. [The scheduling shape is the part that goes wrong](#5-the-scheduling-shape-is-the-part-that-goes-wrong)
6. [TCC, and where the data directory lives](#6-tcc-and-where-the-data-directory-lives)
7. [Endpoint identity on Linux](#7-endpoint-identity-on-linux)
8. [Containers: when they do not earn their place, and when they do](#8-containers-when-they-do-not-earn-their-place-and-when-they-do)
9. [A lock that a container would quietly break](#9-a-lock-that-a-container-would-quietly-break)
10. [Open decisions](#10-open-decisions)

## 1. The daemon is the first component with an identity

Everything shipped so far is a command someone runs. `mavo watch` is different:
it persists, it is scheduled by the operating system, and it makes outbound
network requests on a timer without anyone present. That combination is an
object that security tooling has opinions about, and the opinions are formed
whether or not anyone declares an intent.

The goal of this document is **attribution**, not concealment. The tool polls a
public channel and writes files in its own directory; there is nothing here to
hide and any sensor will see exactly what it does. What attribution buys is that
the job can be allowlisted as a deliberate decision once, instead of reappearing
as an unrecognised object after every interpreter upgrade.

## 2. Egress inventory

Stated completely, because a warning system whose network behaviour is
undocumented cannot be reasoned about by whoever runs it.

| Destination | Purpose | Auth | Frequency |
| --- | --- | --- | --- |
| `t.me` (channel preview) | the only signal source | none. The channel is public | one request per cycle, and the cycle interval is the whole schedule |
| ntfy host (operator-controlled) | notification delivery, phase M1 onward | token, write-side only | on decision and on degradation, bounded by the alarm budget |
| `opensky-network.org` | ADS-B state vectors over the Jasionka box, T42's sampler | OAuth2 client credentials, held on the host in `/etc/mavo-adsb/env` | one request per 60 s from 2026-08-14, 1,440 per day against a 4,000/day allowance |
| `auth.opensky-network.org` | the token endpoint for the row above | the same credentials | once per token lifetime, roughly every 30 minutes |

Nothing else. All reach lives in `mavo/transport.py`, and
`network_reach_is_one_file` in `tests/lint_limitations.py` fails the build if a
second module acquires it, which is what makes the table above checkable rather
than aspirational.

**Correction, 0.31.0.0.** Until this release that check scanned `mavo/` only,
so `tools/` - which the `Makefile` calls "inside the net", and where half of
`STATUS.json`'s measured numbers are produced - was outside the check this
paragraph rested on. Nothing had slipped through; the scope was narrower than
the claim, which is a failure that only becomes visible on the day something
does slip. The scope now covers both. Found while adding the first tool whose
purpose is to reach a second destination, which is the circumstance that would
have exercised it.

**The ADS-B sampler is deliberately not in this tree.** It runs from
`/opt/mavo-adsb` on `vm-mavo` as its own systemd unit, its own user and its own
store, so a fault in it cannot reach the collector this repository is
responsible for. T42 acceptance already requires its snapshots to live outside
the tree; the sampler follows them. When it moves in, it either routes through
`mavo/transport.py` or the lint above stops it, and that is the intended
outcome rather than an obstacle to work around.

**TLS interception.** Under an intercepting proxy the transport sees the
proxy's certificate. The stdlib default verifies against the system trust store,
so a corporate root already installed there works and an unknown one produces a
refusal rather than a silent downgrade. That is the correct behaviour and it has
a consequence worth stating: on a machine with interception, the message stream
has passed through a middlebox, and the `reported` provenance label on every
event is doing more work than usual.

## 3. Jitter is not cosmetic

**What actually runs, as of 0.28.2.0** [measured on the host, 2026-08-13].
Thirty seconds plus jitter, under D-027, not the sixty this section was written
against. Three things learned by running it that the design note did not
anticipate, all of them worth carrying here rather than only in the decision
log:

- **A systemd timer measures `OnUnitActiveSec` from activation, and coalesces.**
  Start-to-start gaps measured 60, 37, 53, 33, 37, 37, 33 s against a nominal 30
  plus 5 of jitter: mean 41. `AccuracySec` defaults to a minute, which is larger
  than the interval it is pacing. A drop-in setting it to `1s` was issued and
  its effect is the outstanding measurement.
- **A failed fetch costs its own wall clock, not one interval.** `timeout_s`
  bounded each socket operation rather than the fetch, so a connect and a read
  each got the full value and an IPv6-only host trying an unusable address
  first paid twice. Measured at 20 s against a constant of 10.0. F98 made it a
  deadline for the whole fetch.
- **Therefore D-027's arithmetic was optimistic.** It assumed a failure costs
  one interval; a failure costs its wall clock *plus* an interval restarting
  from activation *plus* the accuracy slack. The decision survives with a
  smaller margin and the entry now says the margin is an estimate until the
  host reports a measured cadence.

The design reasoning below is unchanged and is why the interval is jittered at
all.



A fixed 60-second interval is the worst available choice for two independent
reasons that happen to have the same fix.

To a sensor it is a textbook beacon profile: constant period, small responses,
one destination, no human at the keyboard. To the upstream it is a perfectly
regular load with no backoff behaviour, from a client with no agreement in
place.

Jitter of roughly ten to twenty percent costs one line and addresses both. It
belongs in M0 from the first commit rather than later, because adding it
afterwards invalidates every interval measurement taken before it, and the
interval measurements are the evidence that would justify tightening the poll.

## 4. Endpoint identity on macOS

A LaunchAgent pointing straight at the interpreter produces a process called
`python3.x` with no identity of its own. Against generic detection content that
is an anonymous interpreter with scheduled persistence making periodic outbound
requests: three weak signals stacked, and the fact that the tool is benign is
not visible to anything that reads them.

The remedy is the same one used elsewhere in this portfolio: a signed wrapper
bundle, so the job is attributable rather than anonymous.

The bundle executable must be a **real Mach-O, not a script**. A shebang script
is replaced by the interpreter image at `execve`, so the process is called
`python3` again and the bundle signature has no relationship to what actually
runs. The launcher does one thing: `posix_spawn` the interpreter and pass the
exit code back.

Known limits, stated plainly rather than discovered later:

- An ad-hoc signature carries no Team ID. Against a "block unsigned" policy this
  is still untrusted code. What it does give is a deterministic `cdhash`.
- The `cdhash` does not change when Python is upgraded, because the wrapper
  calls the interpreter internally. It does change on any rebuild of the
  launcher, so a hash-based allowlist entry needs updating after a rebuild.
- Interpreter and script paths are compiled in. Moving the repository requires
  rebuilding the bundle.
- The launcher binary is built locally and **not committed**. This repository
  declares zero runtime dependencies and runs its gate on two Python versions; a
  committed Mach-O plus a compile step would be a new claim surface with no
  audit behind it, which is the defect class the pins exist to prevent.

## 5. The scheduling shape is the part that goes wrong

This is where copying a timer's configuration would quietly destroy the point of
M0, and it is the single most important paragraph in this document.

A timer job spawns a fresh process per run, which is correct for a tool that
computes something and exits. `mavo watch` needs the opposite. The skipped
message counter exists because the channel preview is a rolling window of about
twenty messages, and it is computed by comparing post ids **between consecutive
polls of one live source instance**. A process respawned every minute has no
previous poll, so `skipped` resolves to `unknown` forever, and that counter is
the reason the daemon exists at all.

Therefore: `KeepAlive` with a long-lived process, never `StartInterval`. A
plist copied from a timer-shaped job would run, log cleanly, and silently
deliver none of M0's value. The observability acceptance criteria catch it
after the fact, since a run whose `skipped` is permanently unknown is visible in
the recap, but the failure is cheap to avoid and expensive to diagnose.

## 6. TCC, and where the data directory lives

Under launchd the job does not inherit Terminal's TCC grants. The repository
currently lives under `~/Documents`, which is a protected location, so snapshot
and store writes can return `Operation not permitted`.

The consequence is specific to this project and unpleasant: a permissions
failure would surface as a refusal in the same place the system reports source
degradation, so **a TCC denial and a dead feed would look alike** until someone
read the log. That is unknown-resolving-to-the-wrong-known, at the operational
layer.

Two fixes, and the second is preferred: grant Full Disk Access to the bundle, or
put the data directory outside protected locations and leave the code where it
is. The second needs no grant, survives a rebuild, and does not widen what the
job is permitted to touch.

## 7. Endpoint identity on Linux

On an always-on Linux host the same attribution comes free. A named systemd unit
gives the job an identity, `Restart=always` and `WatchdogSec` give it
supervision, and the journal gives its output a home that survives the process.
No wrapper, no signature, no `cdhash` to maintain.

This matters for the choice below: the macOS work is real work, and it is worth
doing only if the daemon is going to live on a Mac.

## 8. Containers: when they do not earn their place, and when they do

**Not for what containers are usually for.** MAVO has zero runtime
dependencies, lint-enforced, and its gate proves green on 3.11 and 3.14
simultaneously. The environment drift a container isolates barely exists here.
Adding a `Dockerfile` now buys reproducibility that is already present and pays
for it with a base image pin that no audit in this repository checks: a
document-shaped claim with no guard, in a project that pins its defect count in
three places.

**Two places where a container genuinely pays.**

*The onboarding probe, T7, now.* The acceptance is "a fresh clone into an empty
directory, README followed from zero, with the point of failure recorded". A
laptop with a venv, an installed package and a warm pip cache measures the
author's environment rather than a stranger's. One command gives a clean one:

```
docker run --rm -v "$PWD:/repo" -w /repo python:3.11-slim \
  bash -c 'pip install -e ".[dev]" && make verify'
```

That is a container used as an instrument, not shipped as an artifact. Nothing
enters the repository and no new claim surface is created.

*Audience D, later.* A publicly available system has an availability target,
which is the first component here that would have one at all. Restart policy,
health check, deterministic deployment, state separated from code: at that point
the container stops being fashion and becomes the unit of deployment. That is
after sprint 7 and after M0, not before.

## 9. A lock that a container would quietly break

`DirectoryLock` protects a data directory from two concurrent runs, because two
runs double the request rate against a service whose tolerance was measured over
a burst of twenty. Its liveness check is `os.kill(pid, 0)` against a pid read
from a lock file.

Process ids are per namespace. Two containers mounting the same data volume each
count pids from 1, so process `7` in container A reads a lock held by `7`,
concludes it is its own, and takes it. The control that protects the upstream
becomes silently false, in the one deployment shape that would need it most.

[inference, unreproduced: derived from the code and from pid namespace
semantics. Two containers on one volume have not been run to observe it. This
does not become a threat-model row on the strength of my reasoning; T26 is to
reproduce it first, and if it does not reproduce, that result is recorded too.]

The fix is small and belongs **before** any containerised or multi-host run, not
after: carry a host identifier alongside the pid, or take the lock with `flock`
on a descriptor so liveness is the kernel's problem rather than a numeric
comparison.

## 10. Open decisions

The question underneath all of the above, and it is not answered yet.

**Where does the daemon live?** `docs/MOBILE.md` assumes an
operator-controlled always-on host. A laptop that sleeps is not a host for a
system whose product is minutes of lead time, and shadow mode on a sleeping
machine produces a record with holes that look like quiet nights. If the answer
is a Mac, sections 4 through 6 are the work. If the answer is a Linux box,
section 7 replaces them and most of this document becomes background.

Deciding this changes what M0 costs by more than any other open item here, and
it is recorded as T25 rather than left to be settled by whichever machine was
convenient on the day.
