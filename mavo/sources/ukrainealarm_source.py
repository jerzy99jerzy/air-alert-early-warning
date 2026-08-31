"""The API as the primary feed, adopted the day the channel died (D-040).

**This is the switch the probe module refuses to be, and it is deliberate.**
`mavo/sources/ukrainealarm.py` states that it must never become an input to
`state.json`, and for that module it stands: the prohibition guarded against
*mixing* a second view of one upstream into a contract carrying one
observation, producing a picture whose provenance nobody could state. This
module does not mix, it replaces the primary: every event carries
`source_id="ukrainealarm"`, so the store says which pipe each observation came
down. The channel collector keeps running beside it - not as a second source
but as the watchman for the publisher's return, and should the channel come
back, its events land labelled and distinguishable rather than remembered.
Two views are still never two sources, and nothing here licenses the sentence
"two sources confirm".

**Why it is primary now rather than a fallback later.** On 2026-08-29 at
04:55 UTC the Telegram channel stopped publishing, and stayed silent through
an attack that ISW measured at over 28 hours. The collector polled normally
throughout and could not tell a dead publisher from a quiet sky, because it
had one pipe and no second one to ask. The API was measured live the next
day: authenticated, ~0.25 s to answer, carrying 62 alerts begun after the
channel fell silent - a working upstream behind a dead output, as a number. A
waiting period before switching was considered and rejected: its passage
would have added no information, and every hour spent polling a dead output
while a live path stood measured is an hour of manufactured blindness. D-040
records the argument in full.

**The model differs from the channel's and that is the whole difficulty.** The
channel is a log: it announces a transition and this project records it. The
API is a snapshot: it lists the areas alerting *now* and says nothing at all
about the ones that stopped. An all-clear therefore has to be synthesised from
the difference between two polls, and the rule that makes that safe is the one
this project already holds everywhere else - an absence is only evidence when
the observation succeeded. A poll that fails yields nothing rather than
clearing the map, and the first poll of a process yields no clears unless a
persisted snapshot young enough to trust stands in for the previous one,
because a snapshot compared against nothing cannot say what ended.
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from mavo.areas import AreaTable
from mavo.errors import SourceUnavailable
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind
from mavo.sources.ukrainealarm import API_BASE, TIMEOUT_S, ApiAlert, parse_alerts
from mavo.transport import Transport, UrllibTransport

#: The API's `type` to this project's classification, and the mapping is
#: mostly a refusal to classify (D-042).
#:
#: **`AIR` is UNKNOWN, not MISSILE.** The channel named the means of attack -
#: ballistic, drone, glide bomb - because it wrote them in prose. The API has
#: one type for everything that flies and says nothing about what it is. Mapping
#: it to MISSILE would put a classification on the page that the source never
#: made: the reader would see a missile icon over an alert the operator called
#: only "air". This project has a kind for exactly this case and a legend entry
#: explaining it, and the schema's rule is that unknown is a state rather than a
#: gap to be filled with the likeliest guess.
#:
#: `URBAN_FIGHTS` maps to UNKNOWN for a different reason: it is ground combat,
#: it carries no timing regime that could reach the Polish border, and inventing
#: a kind for it would put a word in the schema that no rule can act on.
_KIND = {
    "AIR": ThreatKind.UNKNOWN,
    "ARTILLERY": ThreatKind.ARTILLERY,
    "URBAN_FIGHTS": ThreatKind.UNKNOWN,
}

#: How old a persisted snapshot may be, in seconds, and still license clears.
#: Three cycles of the 120 s cadence the `collect-api` timer runs at
#: (`docs/DEPLOYMENT.md`, the D-040 switchover): one missed run survives it,
#: a real gap does not. The
#: asymmetry is deliberate and points the safe way - a ceiling set too low
#: delays an all-clear by one cycle, a ceiling set too high lets a host that
#: was down for an evening come back and clear everything that ended while
#: nothing observed.
SNAPSHOT_MAX_AGE_S = 360.0

_Snapshot = dict[tuple[str, ThreatKind], datetime]


def _load_snapshot(
    path: Path, max_age_s: float, now: datetime
) -> tuple[str, float | None, _Snapshot | None, dict[tuple[str, ThreatKind], str]]:
    """`(state, age_s, previous, oblasts)` from a persisted snapshot.

    Every way this can go wrong resolves to "license nothing": a missing file
    is a cold start, an unreadable or malformed one is a broken cache, and a
    stale one - including one stamped in the future, because a clock that ran
    backwards is not a clock to trust - means the observation had a gap. None
    of those may clear an alert, and none of those may stop collection either,
    so nothing here raises.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "missing", None, None, {}
    except OSError:
        return "corrupt", None, None, {}
    try:
        payload = json.loads(raw)
        saved_at = datetime.fromisoformat(payload["saved_at"])
        if saved_at.tzinfo is None:
            raise ValueError("saved_at carries no timezone")
        previous: _Snapshot = {}
        oblasts: dict[tuple[str, ThreatKind], str] = {}
        for entry in payload["areas"]:
            key = (str(entry["area"]), ThreatKind[str(entry["kind"])])
            previous[key] = datetime.fromisoformat(entry["began"])
            oblasts[key] = str(entry["oblast"])
    except (ValueError, KeyError, TypeError):
        return "corrupt", None, None, {}
    age = (now - saved_at).total_seconds()
    if age < 0 or age > max_age_s:
        return "stale", age, None, {}
    return "fresh", age, previous, oblasts


def _resolve(areas: AreaTable, alert: ApiAlert) -> tuple[str, str] | None:
    """`(area_id, oblast)`, or `("", "")` when the register declines, or None.

    Three answers rather than two (F131). `("", "")` means the register knows
    a name in this region and will not resolve it: ambiguous, codeless, or held
    only at another level. None means the vocabulary is absent. The caller
    reports the two differently, because they have different repairs: a
    declined name needs a disambiguation, an absent one needs a row.

    The API names regions in prose and the map is keyed on the channel's
    hashtags, so this goes through `resolve_prose`, which reaches both the
    hashtag stem and the register name. An unresolved region returns None and
    the caller counts it: a region the map does not know is a finding about the
    map, and silently dropping it would hide the finding inside the feed.
    """
    refs, declined = areas.resolve_prose_detail(alert.region_name)
    if len(refs) != 1:
        return None if not declined else ("", "")
    ref = refs[0]
    return ref.code, ref.oblast


class UkrainealarmSource:
    """Snapshot feed presented as the transitions the collector expects.

    The previous snapshot may outlive the process, and the ceiling on its age
    is what makes that safe. Production runs collectors as `oneshot` units
    under timers, so every poll is a new process; a previous snapshot held
    only in memory would never exist there, `cleared` would stay zero forever,
    and every episode the API opened would stay open - the frozen-episode
    pathology this project refuses from the channel, manufactured locally.
    Persisted without a ceiling, the opposite failure appears: a host down for
    an evening would come back and clear everything that ended while nothing
    observed. So the snapshot is written with the moment it describes and read
    back only while younger than `SNAPSHOT_MAX_AGE_S`; older, and the gap
    licenses nothing, because silence is not an all-clear on either side of a
    restart. `snapshot_state` says which of these happened, so the caller can
    put it on stdout rather than leaving a withheld clear looking like a calm
    reading.
    """

    source_id = "ukrainealarm"

    def __init__(
        self,
        key: str,
        areas: AreaTable | None = None,
        base: str = API_BASE,
        transport: Transport | None = None,
        snapshot: Path | None = None,
        snapshot_max_age_s: float = SNAPSHOT_MAX_AGE_S,
    ) -> None:
        self._key = key
        self._areas = areas if areas is not None else AreaTable.from_csv()
        self._base = base.rstrip("/")
        self._transport = transport or UrllibTransport(timeout_s=TIMEOUT_S)
        self._snapshot = snapshot
        #: `(area_id, kind)` seen alerting on the previous successful poll, to
        #: the timestamp the API gave. None until the first one succeeds, and
        #: distinct from an empty dict: "nothing observed yet" and "observed,
        #: nothing alerting" differ by exactly the clears they license. Seeded
        #: from the persisted snapshot when one exists and is young enough.
        self._previous: _Snapshot | None = None
        #: The oblast last seen for an area, so a clear can name the oblast the
        #: area sits in after the API has stopped mentioning it at all.
        self._oblast_seen: dict[tuple[str, ThreatKind], str] = {}
        #: Why the persisted snapshot did or did not seed `_previous`:
        #: `disabled` (no path given), `missing`, `corrupt`, `stale`, `fresh`.
        #: Every state but `fresh` withholds clears, and the caller is expected
        #: to say so rather than let the withholding read as a calm sky.
        self.snapshot_state: str = "disabled"
        self.snapshot_age_s: float | None = None
        if snapshot is not None:
            self.snapshot_state, self.snapshot_age_s, loaded, oblasts = (
                _load_snapshot(snapshot, snapshot_max_age_s, datetime.now(UTC))
            )
            if loaded is not None:
                self._previous = loaded
                self._oblast_seen = oblasts
        #: Regions the map could not resolve on the last poll, for the caller
        #: to report. A count that rises means the two vocabularies are drifting.
        self.unresolved: tuple[str, ...] = ()
        #: Regions the register knows and will not resolve (F131): a different
        #: population from `unresolved`, with a different repair. Reported
        #: separately so an operator reading the journal can tell "add a row"
        #: from "settle an ambiguity" without opening the table.
        self.declined: tuple[str, ...] = ()
        #: Regions whose alert type the vocabulary could not read (F135). A
        #: rising count means the API's type vocabulary is drifting, and the
        #: recap prints it for the same reason the channel path prints its own.
        self.unparsed: tuple[str, ...] = ()

    def poll(self) -> Sequence[ThreatEvent]:
        """Transitions since the previous successful poll.

        Raises only when the source is unreachable, never on its content: a
        malformed body yields no events and leaves the previous snapshot
        untouched, so a hostile payload cannot clear the map either.
        """
        body = self._transport.fetch(
            f"{self._base}/alerts",
            headers={"Authorization": self._key, "Accept": "application/json"},
        )
        now = datetime.now(UTC)
        try:
            payload = json.loads(body)
        except ValueError as malformed:
            raise SourceUnavailable(
                f"{self._base}/alerts: malformed JSON ({malformed})"
            ) from malformed

        current: dict[tuple[str, ThreatKind], datetime] = {}
        oblast_of: dict[tuple[str, ThreatKind], str] = {}
        unresolved: list[str] = []
        declined: list[str] = []
        unparsed: list[str] = []
        substituted: set[tuple[str, ThreatKind]] = set()
        for alert in parse_alerts(payload):
            if alert.alert_type == "unparsed":
                # F135. Counted, never silently dropped: the parser one layer
                # down marks these records for exactly this recap, and a
                # coverage denominator that quietly shrinks flatters whichever
                # side it was built to test. A named region still resolves and
                # lands below under UNKNOWN - a type this vocabulary cannot
                # read is not the absence of an alert - while an unreadable
                # region is counted here and can land nowhere until it has a
                # name.
                unparsed.append(alert.region_name or "<unreadable region>")
                if not alert.region_name:
                    continue
            resolved = _resolve(self._areas, alert)
            if resolved is None:
                unresolved.append(alert.region_name)
                continue
            area_id, oblast = resolved
            if not area_id:
                declined.append(alert.region_name)
                continue
            kind = _KIND.get(alert.alert_type, ThreatKind.UNKNOWN)
            key = (area_id, kind)
            if alert.started_at is None:
                # F136. The read time stands in for a stamp the payload did
                # not carry - the exact act `_stamp` refuses one layer down,
                # done here because an alert without a start is still an
                # alert - and the substitution is marked on the stored row,
                # because a substituted stamp zeroes the latency measurement
                # for exactly the records that lack one, and E-0 must be able
                # to leave them out by reading rather than by guessing.
                substituted.add(key)
            current[key] = alert.started_at or now
            oblast_of[key] = oblast
        self.unresolved = tuple(dict.fromkeys(unresolved))
        self.declined = tuple(dict.fromkeys(declined))
        self.unparsed = tuple(dict.fromkeys(unparsed))

        previous = self._previous
        events: list[ThreatEvent] = []

        for key, started in current.items():
            if previous is not None and key in previous:
                continue
            area_id, kind = key
            events.append(
                ThreatEvent(
                    area_id=area_id,
                    state=AlertState.ACTIVE,
                    ts_source=started,
                    ts_ingest=now,
                    source_id=self.source_id,
                    kind=kind,
                    provenance=Provenance.REPORTED,
                    raw_fields=(
                        {"api_region": area_id, "api_type": kind.name,
                         "ts_source_origin": "observed"}
                        if key in substituted
                        else {"api_region": area_id, "api_type": kind.name}
                    ),
                    oblast=oblast_of[key],
                )
            )

        if previous is not None:
            for key, started in previous.items():
                if key in current:
                    continue
                area_id, kind = key
                events.append(
                    ThreatEvent(
                        area_id=area_id,
                        state=AlertState.CLEAR,
                        # The API does not say when an alert ended; it stops
                        # listing it. The end is therefore this observation,
                        # not the start it carried, and dating it from the
                        # start would report an all-clear as having happened
                        # hours before anything observed it.
                        ts_source=now,
                        ts_ingest=now,
                        source_id=self.source_id,
                        kind=kind,
                        provenance=Provenance.INFERENCE,
                        raw_fields={"api_region": area_id, "began": started.isoformat()},
                        oblast=self._oblast_seen.get(key, ""),
                    )
                )

        self._oblast_seen.update(oblast_of)
        self._previous = current
        return tuple(events)

    def save_snapshot(self) -> None:
        """Persist the current snapshot for the next process to clear against.

        Atomic by rename: the payload lands on a `.partial` name first and
        takes the real one only whole, because a half-written file with the
        target's name is exactly the artefact the 0.43.0.0 deploy's failed
        `scp` left behind, and a loader finding one would read it as corrupt
        and withhold clears for a cycle nothing required. The caller decides
        *when* - after the store accepted the events, so a failed append
        leaves the old snapshot standing and the same clears are derived
        again next run rather than lost. A no-op without a path or before a
        successful poll: there is nothing to persist, and writing an empty
        claim would be a claim.
        """
        if self._snapshot is None or self._previous is None:
            return
        payload = {
            "saved_at": datetime.now(UTC).isoformat(),
            "areas": [
                {
                    "area": area_id,
                    "kind": kind.name,
                    "began": began.isoformat(),
                    "oblast": self._oblast_seen.get((area_id, kind), ""),
                }
                for (area_id, kind), began in sorted(
                    self._previous.items(), key=lambda item: (item[0][0], item[0][1].name)
                )
            ],
        }
        self._snapshot.parent.mkdir(parents=True, exist_ok=True)
        partial = self._snapshot.with_name(self._snapshot.name + ".partial")
        partial.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(partial, self._snapshot)
