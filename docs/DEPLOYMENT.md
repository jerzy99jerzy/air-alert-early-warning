# Deployment profile

Version: 1.22 / 2026-09-04
Status: **partly built and running, and the document is behind it.** The
collector runs unattended on a host from 2026-08-11 and the publishing loop
writes the contract; the daemon this document plans is still the shape of what
comes next. What follows describes the endpoint the daemon will present. What
is running today is described in the section immediately below, which was
written after the fact rather than before, and says so.

## What is installed on the hosts, and how far behind it is

Host state measured: 2026-08-31

**This section is the state. The rest of this document is the shape**, and the
two diverged silently once already (F102), which is why the line above exists
and why `tools/docs_audit.py` fails the gate when it falls more than fourteen
days behind the release being cut. The gate cannot reach this machine and never
will; freshness is the only property of a host claim a repository can hold.

**How every figure below was obtained**, so that a later reader can repeat it
rather than trust it: `gcloud compute ssh vm-mavo --tunnel-through-iap`, then
`systemctl cat`, `systemctl list-timers`, `sudo journalctl -u <unit>`, and the
installed package read through its own interpreter.

### Units, and there are five rather than one

An earlier revision of this table said four and omitted `mavo-collect-api`,
the unit that has fed the entire project since D-040 (F134). The omission is
repaired from reads, not from memory.

| Unit | Type | Cadence | What it does |
| --- | --- | --- | --- |
| `mavo-collect-api.service` | `oneshot`; `Deactivated successfully` after each run, journal 2026-08-31 | `mavo-collect-api.timer`, 121 s (timer read 2026-08-30); consecutive completions 120 s apart re-read 2026-08-31 06:22:53 to 06:24:53 | **the primary source since D-040**: one API poll into `/var/lib/mavo/events`, snapshot at `/var/lib/mavo/ukrainealarm.snapshot.json`, freshness ceiling 360 s |
| `mavo-collect.service` | `oneshot`, `User=mavo` | `mavo-collect.timer`, 30 s + 5 s jitter, `AccuracySec=1s` | the watchman: one channel poll into the same store, so a returned publisher lands labelled |
| `mavo-push.service` | `oneshot` | `mavo-push.timer`, 30 s with `AccuracySec=1s` since 2026-08-24 (F116); `RandomizedDelaySec` read as 15 s on 2026-08-21 and **not re-read since** | pushes `state.json` and `feed.json` to the site |
| `mavo-report.service` | long-running | continuous, `--interval 30` with `--feed`, read from `ExecStart` 2026-08-31 after F137 settled; the duelling `feed.conf` drop-in is deleted and `interval.conf` alone carries the line | writes the report |
| `mavo-adsb.service` | long-running | continuous | the sampler, `mavo-adsb` repository |

**There is no daemon and the collector is not one.** A timer plus a `oneshot`
unit is the supervision mechanism this project actually runs on, and it was
never a decision until D-031 wrote it down.

### The installed package, and how it was verified

| | |
| --- | --- |
| Installed | `air-alert-early-warning 0.49.0.0`, `/opt/mavo/venv`, python3.11 |
| Installed at | **2026-08-31**, second deploy of the day; first `collect-api` cycle under it completed 12:14:41 UTC (journal). The `.dist-info` mtime was not read this session either, and is owed for the second consecutive visit |
| Wheel | sha256 `955739db…81efa`, 165 KiB, verified by `sha256sum -c` on the host before `pip`; `gcloud compute scp` over the IAP tunnel, no stall |
| Point of return | `events.pre-0.49.0.0`, 20,811,776 B, sha256 `25643014…05d95`, taken with both collect timers stopped and with no `-wal` or `-shm` beside it - the listing that shows this was itself re-run, because the first attempt expanded the glob in a shell that cannot read the directory and proved nothing |
| Collection gap | **192 s**, 12:11:28 to 12:14:40, both timers. Inside the 360 s snapshot ceiling, so no clear was withheld across the window |
| Discriminators | on the installed source, not the version string: `kinds_open` 7 in `report.py`, `self.unparsed` 2 and `ts_source_origin` 1 in `sources/ukrainealarm_source.py` - all three exist only after F138 and F135 |
| First post-install poll | `active=0 cleared=0 unresolved=5 declined=1 unparsed=0 latency=0.227s snapshot=fresh(193s)`. The `unparsed` field is itself the proof of version: 0.48.0.0 could not print it. Zero means the API's type vocabulary still covers what arrives |
| Contract after | `state.json` v3, `state=ok`, 38 areas active, `recent_7d` 19 oblasts of which **8 carry an open episode** (`still_under_alert`), and one carries `alert_seconds` **604,800**: a full seven-day window unbroken. That figure is the F138 repair visible from outside - before it, a concurrent kind's all-clear tore such an episode apart and the count could never reach the ceiling |
| Earlier deploy the same day | 0.48.0.0 at 06:22:53 UTC: wheel `76fb176f…b564d0`, return point `events.pre-0.48.0.0` `a5585436…c205b4`, first poll `snapshot=fresh(120s)`, then `reconcile --unmask` closing the eight-area Donetsk `glide_bomb` belt (ghosts=8, masked=0, second apply 0) |
| `main` | 0.52.0.0 |
| Behind by | **six** releases, 0.50.0.0 to 0.52.0.0, and the sixth is the first since 0.49.0.0 that changes package code: `INFO` records no longer raise an alert and unmapped type strings are named (T83). Five documents-only releases were cut against this row's own install-next judgement; this one carries a change the host has never run, which ends the argument that the wheel would differ in nothing a reader can see. The next act on this host is bringing it to 0.52.0.0, with `reconcile --dry-run` read before and after the first poll |

**The first poll after installing 0.41.0.0 changes the store, in place, and
says so.** `feed_attempts` gains `elapsed_s`; the column is added by
`ALTER TABLE`, nullable, so every row this host wrote earlier reads NULL rather
than a duration nobody measured. `mavo collect` prints

```
[STORE-MIGRATED] added feed_attempts.elapsed_s, NULL for every earlier row
[STORE-MIGRATED] added feed_attempts.first_id, NULL for every earlier row
[STORE-MIGRATED] added feed_attempts.last_id, NULL for every earlier row
```

**once**, on the first invocation, three lines from 0.40.0.0 and the last two
only from 0.41.0.0.

Read from the host, 2026-08-29 14:39:05 UTC, exactly as predicted and exactly
once: all three lines on the first post-install poll, none on the second, no
row lost (the pre-install copy `events.pre-0.42.0.0`, sha256 `2490e966…d2892`,
is the point of return and stays on the host). The same first poll printed
`skipped=unknown` with `no earlier page bound`; the second printed
`skipped=0`, which closed F123 in production - eighteen days after deployment
first made it observable. Zero is correct there, not suspicious: the channel
had been silent since 04:55 UTC, nine and a half hours the state machine spent
in `degraded` with `observation_age_s` 34,214 - D-034's argument, live, in its
extreme form. The dist-info mtime read owed above:

    sudo stat -c %y /opt/mavo/venv/lib/python3.11/site-packages/air_alert_early_warning-0.42.0.0.dist-info That line appearing on every poll would mean
the migration is not sticking and the store is being reopened one column short
each time, which is a different failure with the same symptom. The reading to
take after the deploy is therefore the count of that line over a window, not
its presence.

**Why the store is not rebuilt instead**, which is what `docs/DECISIONS.md`
D-013 says to do and what this guard used to print: `feed_attempts` and
`communiques` are not derived from the corpus and a rebuild deletes them. F124.

**An earlier version of this table carried two different answers in one
document**: 0.32.2.0 here and 0.32.7.0 in the deploy record below, both under
one measured-on date. Both were true of different moments and the section had
no rule about which moment it describes. The rule now: this table is the
newest reading, the deploy history below is every reading, and they share no
rows.

**Deploy history since this section was first written:**

| Version | Installed at (UTC) | Fate |
| --- | --- | --- |
| 0.49.0.0 | 2026-08-31, first cycle under it 12:14:41; `.dist-info` mtime owed | **current**; F138, the per-kind episode counters |
| 0.48.0.0 | 2026-08-31, first post-install poll completed 06:22:53; `.dist-info` mtime owed | superseded the same day; D-044 and D-045, the per-kind repair |
| 0.47.0.0 | 2026-08-30 evening, from the session record rather than a host read (F117's honesty rule, applied to our own gap) | superseded; brought `mavo reconcile` |
| 0.45.0.0 | 2026-08-30 16:46:13, the `.dist-info` mtime | superseded |
| 0.44.0.0 | 2026-08-30 15:02:10, the `.dist-info` mtime | superseded the next day; the D-040 switchover. An earlier revision of this table still called it current while the table above said 0.45.0.0 - the two-answers-in-one-document defect this section's own rule forbids, caught at this revision |
| 0.43.0.0 | 2026-08-30 08:40:44, the `.dist-info` mtime | superseded the same day |
| 0.42.0.0 | 2026-08-29 14:38:38, the `.dist-info` mtime read on 2026-08-30, paying the reading the previous revision of this file owed | superseded |
| 0.32.2.0 | 2026-08-14 18:13:09 | superseded |
| 0.32.7.0 | 2026-08-17 11:02:06 | superseded; its restart opened the S9 window |
| 0.36.0.0 | 2026-08-20 18:19:43 | **withdrawn after 14 hours.** F110: 168 polls died with a traceback and exit `1/FAILURE`, and the refusal line stopped being written |
| 0.36.0.1 | 2026-08-21 08:52:36 | superseded |
| the seven releases in between | `[unknown]` | whether any of them was ever installed cannot be recovered: the filesystem keeps only the current install and this table was not written at the time. Named rather than reconstructed from the version numbers (F117) |
| 0.39.0.0 | 2026-08-23 13:40:15 | superseded; recorded on 2026-08-24, a day after the fact, by reading the host rather than by anyone remembering |
| 0.40.0.0 | 2026-08-26 19:39:24 | superseded 2026-08-29; recorded the same evening, from the host, during the deploy rather than after it |

**Verified by content, not by version string** [measured, 2026-08-26]. The
wheel was checked by `sha256sum -c` on the host before `pip` touched anything
(`1b5b248b...`), and the *installed* source was then grepped for three strings
the release added, with the counts fixed in advance rather than read
afterwards: `clock_skew_s` and `SKEW_TOLERANCE_S` four times each in
`mavo/report.py`, `_strip` five times in `mavo/backfill.py`. Identical counts
were taken from inside the wheel before transfer, so a stale archive would have
failed before reaching the machine. The version string alone has reported
success against a host running different code once, and it cost an hour.

**The proof that the new code is running is the contract, not the unit state**
[measured, 2026-08-26]. `state.json` written at 19:41:03 carries
`clock_skew_s: 0.0`, a field the previous release cannot produce, with
`observation_age_s: 271` seconds against `source_last_message_at` at 19:36:32 - the
subtraction agrees. 25 `publish.cycle` records were written in the eleven
minutes after installation. The same field was read back over public HTTP from
the site at 19:42:03, so it crossed the push path and the consumer at 4.58.0.0
ignored it as an additive field should. `NRestarts=0`.

**The report loop was restarted twice, at 19:40:09 and 19:40:37, and only one
restart was intended.** Session 838 and session 839 each ran the same pair of
commands, 28 seconds apart, from one invocation on the operator's side
[measured, from `journalctl`]. Why the second session opened is
**[nieustalone]**; the likely cause is `gcloud compute ssh --command` retrying
a dropped tunnel and re-running the whole command, which would make **every
step of this deploy path non-idempotent** - it cost a window here and would
have run `pip install` twice as quietly. Recorded because D-032 counts planned
restarts of this loop, and the count for this deploy is two.

**Four rows of this table were false for two releases while the freshness line
above it passed the gate.** That is F117, and the rows are re-measured here
rather than nudged.

### F98 on the wire, measured before and after

The strongest evidence in this document, and it is an accident of the journal
rather than a designed experiment:

| | |
| --- | --- |
| Last fetch over 15 s | **2026-08-14 18:12:34 UTC**, 20.08 s |
| Package installed | **2026-08-14 18:13:09 UTC** |
| Gap | **35 seconds** |
| Fetches over 15 s in the whole journal | 366, **every one before that moment** |
| Timeouts in the seven days since | 14, **all between 10.0 s and 10.2 s** |
| ~~Failure rate~~ | ~~14 in roughly 18,350 polls, 0.076%~~ **withdrawn at 0.36.0.0, F109** |

**The withdrawn row is left in place rather than deleted**, because a figure
that was quoted for six days and repaired into `README.md` at 0.33.0.2 should
not vanish from the document that held it. It divided a numerator counted over
seven days by a denominator counted over nine, and described the quotient as a
failure rate.

| Refusal rate, measured 2026-08-20 | Attempts | Refusals | Rate |
| --- | --- | --- | --- |
| 08-14 18:13 → 08-17 11:02, the window above | 7,074 | 689 | **9.7%** |
| 08-17 11:02 → 08-20 11:02, the S9 window | 7,850 | 774 | **9.9%** |
| Whole journal | 19,956 | 1,966 | **9.9%** |

A refusal does not print `Finished mavo-collect`; it prints `Failed to start`
with `status=3`. Attempts are the sum of the two, which is what makes the S9
window's arithmetic close: 7,850 attempts over 259,200 seconds is a 33.0 s
cadence against a measured median of 33.0 s.

The ten-second bound holds on the host. F98 is deployed and this is what
deployed looks like from outside the code. **F98 bounded the cost of a failure
and not its frequency**, and the withdrawn row above read the bound as the
frequency (F109).

### The timers, quoted rather than described

**Every drop-in below existed only on this host until 0.39.1.0.** The base
units ship nowhere: this repository has no `deploy/` directory, so four files
that decide how often the instrument runs sat outside `git ls-files` while the
gate's whole perimeter is `git ls-files`. Pasting them here does not put them
under version control in the sense that a change to one would be noticed - only
a re-reading does that - but it ends the state where the tree held no copy at
all. `systemctl cat`, read 2026-08-24.

```
# /etc/systemd/system/mavo-collect.timer
[Unit]
Description=poll the channel every two minutes

[Timer]
OnBootSec=60
OnUnitActiveSec=120
RandomizedDelaySec=18

[Install]
WantedBy=timers.target

# /etc/systemd/system/mavo-collect.timer.d/description.conf
[Unit]
Description=poll the channel every thirty seconds (D-027)

# /etc/systemd/system/mavo-collect.timer.d/interval.conf
[Timer]
OnUnitActiveSec=
OnUnitActiveSec=30
RandomizedDelaySec=5
AccuracySec=1s

# /etc/systemd/system/mavo-push.timer
[Unit]
Description=push state.json every two minutes

[Timer]
OnBootSec=90
OnUnitActiveSec=120
RandomizedDelaySec=15

[Install]
WantedBy=timers.target

# /etc/systemd/system/mavo-push.timer.d/interval.conf
[Timer]
OnUnitActiveSec=
OnUnitActiveSec=30
AccuracySec=1s
```

Effective values, `systemctl show`, same reading:

```
mavo-collect.timer  OnUnitActiveUSec=30s  AccuracyUSec=1s  RandomizedDelayUSec=5s
mavo-push.timer     OnUnitActiveUSec=30s  AccuracyUSec=1s  RandomizedDelayUSec=15s
```

**Three things the paste says that no prose about it had.**

`mavo-push.timer` still describes itself as running every two minutes. The
collector carries a `description.conf` drop-in for exactly this reason and the
delivery timer never got one, so its `Description` outlived its cadence by the
same mechanism F116 describes, one layer down and inside F116's own repair.

`RandomizedDelaySec` on the delivery timer is 15 s and D-033 declined to touch
it without a reading. The reading exists now: the ceiling is 30 + 15 + 1 = 46 s
against the collector's 36, so the jitter is half the interval where the
collector's is a sixth. Under the consumer's 120 s threshold either way, which
is why this is a consistency question and still not a correctness one.

The service units are **not** reproduced here. `mavo-push.service` carries an
internal address and a key path, and how much of the deployment a public
repository publishes is a threat-model question rather than a documentation
one. The two `mavo-report.service` drop-ins are quoted in the section below,
because a defect there needs them.

### Cadence, measured over a full day

Start-to-start intervals over 24 hours, 2026-08-16 to 2026-08-17:

```
n=2619   min=30.06   p50=33.00   p90=35.00   p99=35.01   max=36.06
```

The configuration's theoretical ceiling is 36 s. The measured maximum is
36.06 s over 2,619 observations, so the distribution is inside what the
configuration promises. D-027's one-hour figure (n=107) is confirmed at
twenty-four times the scale, and the caveat attached to it is discharged.

### Delivery cadence, and the measurement this section is still owed

**The collector's drop-in was applied to the collector and to nothing else.**
`mavo-push.timer` sat at the base `OnUnitActiveSec=120` with no `AccuracySec`
until 2026-08-24, while the loop it delivers composes every 30 s. Measured
before the change: 645 delivery rounds against 2,861 compositions in a day, and
start-to-start gaps of median 139 s, p95 139 s, maximum 162 s against a nominal
120 [measured, `sshd` records on `vm-site`, 1,289 gaps, 2026-08-23 to
2026-08-24]. That is **F116**, and its cost fell on the consumer rather than
here.

Applied 2026-08-24, `/etc/systemd/system/mavo-push.timer.d/interval.conf`:

```
[Timer]
OnUnitActiveSec=
OnUnitActiveSec=30
AccuracySec=1s
```

Confirmed through `systemctl show mavo-push.timer` as `OnUnitActiveUSec=30s`
and `AccuracyUSec=1s`, with three completions of `mavo-push.service` observed
inside 80 s [measured, 2026-08-24].

**Two figures this section does not have and will not invent.** The 24-hour gap
distribution after the change, which is the only thing showing the ceiling
actually fell; and `RandomizedDelaySec` on this timer, carried above from the
2026-08-21 reading and not re-read, so the theoretical ceiling cannot be stated
the way the collector's can. Both are outstanding in the sense D-027's
`AccuracySec` was outstanding for a release: named with the command that closes
them rather than estimated.

```
sudo journalctl -u ssh -u sshd --since "-24 hours" -o short-iso --no-pager
```

Count `Accepted publickey for mavo-push` and halve it, because one delivery is
two connections: `accept-state` takes one target per invocation and the unit
sends `state` and `feed`.

**No delivery appears in `run.jsonl`.** This repository records that it composed
a report and records nothing about handing one over, so every figure above came
from `sshd` by accident rather than from this project by design. That is the
open half of F116 and the drop-in does not touch it.

### The run log, and the claim about it that was wrong

Both `mavo-collect.service` and `mavo-report.service` carry
`Environment=MAVO_LOG_FILE=/var/lib/mavo/run.jsonl`, and
**`mavo-report.service` has carried it since it was written.** 0.32.7.0 stated
here that the variable sat on the collector and belonged on the loop, and
scheduled a `systemctl edit` to move it. That was false, drawn from reading one
unit and not the other, and it is **F106**. Quoted rather than described, which
is the repair T64 proposes to enforce:

```
# systemctl cat mavo-report.service
[Service]
Type=simple
User=mavo
Environment=MAVO_LOG_FILE=/var/lib/mavo/run.jsonl
ExecStart=/opt/mavo/venv/bin/mavo report --store /var/lib/mavo/events ... --watch --interval 120
ReadWritePaths=/var/lib/mavo
# .d/interval.conf overrides ExecStart with --feed and --interval 30
```

**Correction, 2026-08-21, to the quoted comment's last line**: `systemctl cat`
read on the host shows **two** drop-in `ExecStart` pairs after the base line,
not one - the first adds `--feed` at `--interval 120`, the second re-states
`--feed` at `--interval 30`, and the last one wins. The quote above described
one override because one file was read. Same class as the error the quote
exists to record.

The single fault was that **no code read the variable**:
`mavo.obs.from_environment` had no caller (F103). Repaired in 0.32.7.0 by one
argument at one call site, so the deploy was an install and a restart with no
unit edit at all.

### 0.32.7.0 on the host, and what proved it

Deployed 2026-08-17. Wheel built from the commit under `v0.32.7.0`
(`air_alert_early_warning-0.32.7.0-py3-none-any.whl`, sha256 `5741a156…21c0ad`),
`mavo-collect.timer` stopped for the install and restarted, then
`mavo-report.service` restarted.

| Evidence | Reading |
| --- | --- |
| `sink_from_environment` in the installed `mavo/cli.py` | `True` |
| `publish.cycle` in the installed `mavo/report.py` | `True` |
| First journal line after restart | `run-log=/var/lib/mavo/run.jsonl` |
| `/var/lib/mavo/run.jsonl` after four minutes | 19 lines, 9 `publish.cycle` records |
| `NRestarts` | 0 |

**The last two rows are the only ones that close F103.** Every other indicator
reported healthy for nine releases while nothing was written, so a version
string and a running unit prove nothing here by construction.

**Run log growth, measured rather than estimated.** 443 bytes per cycle
(`publish.cycle` 243 + `publish.interval` 200) at ~2,880 cycles a day is
**1.28 MB/day**. `DEFAULT_MAX_BYTES` is 8 MiB with `DEFAULT_RETAIN` 5, so the
first rotation falls at about **6.6 days** and the steady-state ceiling is
48 MiB. **The S9 window ends before the first rotation**, which is stated in
D-032 as a thing that window does not test.

### The S9 window

```
Start: 2026-08-17 11:02:06 UTC   (restart of mavo-report.service)
End:   2026-08-20 11:02:06 UTC
```

`mavo-collect.timer` is untouched for the duration: it produces the evidence
and it feeds T40. Up to two planned restarts of `mavo-report.service` are
permitted and each is reported as its own segment (**D-032**, an amendment made
inside the window and argued there).

**Outcome, read 2026-08-20 after the window closed** `[measured]`:
`NRestarts=0`, `ActiveEnterTimestamp` equal to the window's opening second, and
7,850 attempts - 7,076 finishes plus 774 refusals - over 259,200 s, a 33.0 s
cadence against a measured median of 33.0 s. Continuity held with zero
restarts against the two the amendment permitted. **The refusal half of that
journal is F109's evidence**: the 774 are 9.9% of attempts, against a rate this
document pinned at 0.076% until the pin was withdrawn.

### The network this host actually has

Measured 2026-08-20, because a check written without these facts hangs and its
author reads the hang as an outage.

| | |
| --- | --- |
| Internal IPv4 | `10.20.0.2/32`, and the push to the site travels over it |
| External IPv4 | **none.** `curl -4` to anywhere hangs to its own ceiling; packets leave by the default route and die without ICMP |
| External IPv6 | `2600:1900:4140:3cb::/128`, the only public egress |
| `mavo.org.pl` | **A record only.** This host cannot reach its own public site, over either family |

Two consequences worth stating as rules. **Never probe the public site from
`vm-mavo`** - the probe measures the missing route, not the site, and this
session did exactly that once. And when an IPv6 connection fails, **the IPv4
fallback does not rescue the attempt, it doubles its cost**: the black hole
consumes whatever budget the attempt has left, which is why every refusal in
the journal sits exactly on the timeout.

### Files staged on this host

`/var/tmp`, not `/tmp`. On 2026-08-20 a store snapshot written to `/tmp`
existed at 16:31 with a size and an owner, and was gone before 17:17, with the
reboot, `systemd-tmpfiles-clean` and permissions all excluded by measurement
and the cause **never established**. `/var/tmp` survives what `/tmp` is allowed
to lose, and the snapshot procedure, the wheels and the probe outputs moved
there the same day. The unexplained deletion stays unexplained; the rule
removes the class rather than the mystery.

### Counting refusals without repeating F110

A refusal prints `Failed to start` with `status=3` and **never** prints
`Finished mavo-collect`; a crash prints a traceback with `status=1` and no
refusal line at all. For fourteen hours under 0.36.0.0 the second was
happening and a count of `[UNREACHABLE]` lines read zero, and that zero was
read as a quiet network.

So the reading is three numbers or it is nothing:

1. attempts = `Starting mavo-collect` lines,
2. finishes = `Finished mavo-collect` lines,
3. refusals = `[UNREACHABLE]` lines,

and **1 minus 2 must equal 3**. When it does not, the difference is processes
dying some third way, and the rate computed from any single token is a
measurement of that token's printer, not of the network.

### Reading this host without lying to yourself

`journalctl -u <unit>` **without membership of `adm` or `systemd-journal`
returns the operator's own journal, which is empty, and exits zero.** That zero
is not a measurement of the service. The same query under `sudo` returns 77,162
lines over seven days. Every journal figure in this document was taken with
`sudo`, and any future one must be, or it is the project's own central error
committed against its own machine.

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

## The `scp` stall, and the workaround that is now a documented path

Twice during the 0.43.0.0 deploy, `gcloud compute scp` over the IAP tunnel
stalled at 0%, and the first attempt left a **zero-byte file under the full
destination name** - an artefact shaped exactly like a delivered wheel, one
`sha256sum -c` away from being installed as one. The control channel was
healthy throughout; the fault sits in `scp`'s data channel (the SFTP
subsystem), cause `[unestablished]`, and it is not bandwidth: the workaround
moved the same bytes through the same tunnel immediately after.

The workaround, now the fallback of record: base64 the wheel through the SSH
control channel, write to a `.partial` name on the host, verify sha256, and
rename atomically. ~199 KB crossed without incident. Two rules follow. A
transfer that can fail must never write under the destination name - the
rename comes after the digest agrees, never before. And a zero-byte file
where an artefact should be is a finding, not a retry: name it before
deleting it.

## Switching the primary source (D-040) - the 0.44.0.0 deploy, written before it runs

The channel died as an output on 2026-08-29 04:55 UTC; the API was measured
live the next day; D-040 adopts it as the primary immediately, with no
waiting period, and keeps the channel collector running as the watchman for
the publisher's return. This section is the order of that deploy. Each step
carries its stop condition; a step whose reading disagrees stops the
switchover, and the readings marked `[to be read]` are owed to the revision
of this file that follows the deploy.

**1. The key onto the host.** `/etc/mavo/ukrainealarm.key`, mode `0600`,
owner `mavo:mavo`, typed interactively - never through the clipboard, which
has already overwritten this key once with 262 characters of unrelated
buffer, and never through shell history, which the key has already crossed
once (rotation is a named follow-up, not a blocker). Validate **before**
anything reads it, not after: byte count 41 and shape
`^[0-9a-f]{8}:[0-9a-f]{32}$`. Stop if either disagrees.

**2. The pre-switch reading.** `mavo report --store /var/lib/mavo/events` as
`mavo`, and record which areas the contract currently holds ACTIVE - the
channel's frozen legacy, open since it fell silent mid-wave. This set is
what D-040's second named cost is about, and it must be read *before* the
API writes anything, because afterwards the two pipes' contributions can
only be separated by `source_id`, not by memory. `[to be read]`

**3. First poll by hand**, as `mavo`, with the full production flags:

```
mavo collect-api --key-file /etc/mavo/ukrainealarm.key \
  --store /var/lib/mavo/events \
  --snapshot /var/lib/mavo/ukrainealarm.snapshot.json
```

Expected: `snapshot=missing` (a cold start, correctly), `cleared=0`, an
`unresolved` list that is entirely eastern names outside the area table.
Stop if any western area appears unresolved, or if `[NO-SNAPSHOT]` prints -
the latter means the flag was dropped and the deployment would raise alerts
that never end. `[to be read]`

**4. The frozen set, established.** Areas from step 2 absent from step 3's
snapshot ended at an unverifiable moment during the channel's silence; the
API cannot close what it never saw, and they will not close themselves
(T81). If the set is empty, this cost never materialised and the row saying
so goes here. If it is not, reconciling it becomes a named task before the
next release - never a silent one, and never by editing the store by hand.
`[to be read]`

**5. The unit and the timer.** A separate pair, deliberately - the channel's
`mavo-collect.timer` is not touched and not stopped:

```
[Unit]
Description=poll the alerting API

[Service]
Type=oneshot
User=mavo
ExecStart=/opt/mavo/venv/bin/mavo collect-api --key-file /etc/mavo/ukrainealarm.key --store /var/lib/mavo/events --snapshot /var/lib/mavo/ukrainealarm.snapshot.json
```

with `OnUnitActiveSec=120` and `AccuracySec=1s` on the timer. 120 s is the
cadence the snapshot's 360 s freshness ceiling was set against - three
cycles, so one missed run survives and a real gap does not - and it sits an
order of magnitude inside the provider's rate terms. Changing the cadence
means revisiting `SNAPSHOT_MAX_AGE_S`, and that coupling is written at the
constant rather than remembered.

**6. The reading that proves the repair.** Within the first day the journal
must show `cleared=` greater than zero at least once, with
`snapshot=fresh(…)` on the same line - the property no amount of polling
on the previous release could ever produce, and the reason 0.44.0.0 exists. Absence of that
line after a day of real alert traffic reopens the bloker, whatever the
exit codes say. `[to be read]`

## The release order, and why the obvious one cannot run

**apply → add → manifest-write → verify → manifest → commit → tag.**

The order after F108 was written as apply → add → verify → manifest, and it
**cannot be executed when a release adds a file**. `manifest-completeness` is
inside `verify`, and it fails on a file that is tracked and not listed, which
is exactly what a new file is after `git add` and before `check_manifest.py
--write`. Measured twice in one session while shipping 0.34.0.0.

| Step | Command | What would go wrong without it |
| --- | --- | --- |
| apply | `git apply --check` first, then `git apply` | a patch half-applied leaves a tree nobody can name |
| add | `git add -A` | F108: `check_manifest.py` reads `git ls-files`, so an untracked file is not a file to it |
| manifest-write | `make manifest-write` | `verify` cannot pass while a tracked file is unlisted |
| verify | `make verify` | the gate |
| manifest | `make manifest` | digests describe *this* tree; deliberately outside `verify`, which runs on trees under edit |
| commit | `verify && commit` as one chain | a commit made after a failed gate looks identical to one made after a passing gate |
| tag | assert first, in the same chain: `git show "$V:pyproject.toml"` must print the version being tagged, **then** `git tag` on that same hash | six tagging failures across this project family, and on 2026-08-20 the assertion caught a hand-pasted hash that was the wrong commit **before** the tag existed |

**Regeneration is a release step, not a repair step.** Running `manifest-write`
to make a red check green is the same act as moving a tag, and the tool's own
error message says so.

**After tagging, read the tag rather than trusting it**: `git show
<tag>:pyproject.toml` prints the version the tag actually points at, which has
disagreed with the worktree before.
