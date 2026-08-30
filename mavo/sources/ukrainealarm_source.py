"""The API as a feed, for when the channel this project was built on stops.

**This is the switch the probe module refuses to be, and it is deliberate.**
`mavo/sources/ukrainealarm.py` states that it must never become an input to
`state.json`, and that stands: mixing a second view of one upstream into a
contract carrying one observation would produce a picture whose provenance
nobody could state. This module does not mix. It *replaces*: when it runs, the
channel source does not, and every event carries `source_id="ukrainealarm"` so
the store says which pipe an observation came down. Two views are still never
two sources, and nothing here licenses the sentence "two sources confirm".

**Why it exists.** On 2026-08-29 at 04:55 UTC the Telegram channel stopped
publishing, and stayed silent through an attack that ISW measured at over 28
hours. The collector polled normally throughout and could not tell a dead
publisher from a quiet sky, because it had one pipe and no second one to ask.
The API was measured live that day: it carried 62 alerts begun after the
channel fell silent, which is what "the upstream is alive and the output is
dead" looks like when it is a number rather than a hunch.

**The model differs from the channel's and that is the whole difficulty.** The
channel is a log: it announces a transition and this project records it. The
API is a snapshot: it lists the areas alerting *now* and says nothing at all
about the ones that stopped. An all-clear therefore has to be synthesised from
the difference between two polls, and the rule that makes that safe is the one
this project already holds everywhere else - an absence is only evidence when
the observation succeeded. A poll that fails yields nothing rather than
clearing the map, and the first poll of a process yields no clears at all,
because a snapshot compared against no previous snapshot cannot say what ended.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime

from mavo.areas import AreaTable
from mavo.errors import SourceUnavailable
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind
from mavo.sources.ukrainealarm import API_BASE, TIMEOUT_S, ApiAlert, parse_alerts
from mavo.transport import Transport, UrllibTransport

#: The API's `type` to this project's classification. `URBAN_FIGHTS` maps to
#: UNKNOWN rather than gaining a member: it is ground combat, it carries no
#: timing regime that could reach the Polish border, and inventing a kind for
#: it would put a word in the schema that no rule can act on.
_KIND = {
    "AIR": ThreatKind.MISSILE,
    "ARTILLERY": ThreatKind.ARTILLERY,
    "URBAN_FIGHTS": ThreatKind.UNKNOWN,
}

#: The unit word as prose spells it, keyed to the code the area map stores.
_UNIT_WORD = {"P": "район", "H": "громада", "O": "область"}


def _resolve(areas: AreaTable, alert: ApiAlert) -> tuple[str, str] | None:
    """`(area_id, oblast)` for an API region, or None when the map lacks it.

    The API names regions in prose and the map is keyed on the channel's
    hashtags, so this goes through `resolve_prose`, which reaches both the
    hashtag stem and the register name. An unresolved region returns None and
    the caller counts it: a region the map does not know is a finding about the
    map, and silently dropping it would hide the finding inside the feed.
    """
    refs = areas.resolve_prose(alert.region_name)
    if len(refs) != 1:
        return None
    ref = refs[0]
    return ref.code, ref.oblast


class UkrainealarmSource:
    """Snapshot feed presented as the transitions the collector expects.

    Holds the previous snapshot in memory, which is the honest scope: a process
    that restarts has no previous snapshot and issues no clears until it has
    polled twice. The alternative, persisting the snapshot so a restart can
    clear areas against a reading from before the gap, would let a restart
    announce all-clears for a window nothing observed.
    """

    source_id = "ukrainealarm"

    def __init__(
        self,
        key: str,
        areas: AreaTable | None = None,
        base: str = API_BASE,
        transport: Transport | None = None,
    ) -> None:
        self._key = key
        self._areas = areas if areas is not None else AreaTable.from_csv()
        self._base = base.rstrip("/")
        self._transport = transport or UrllibTransport(timeout_s=TIMEOUT_S)
        #: `(area_id, kind)` seen alerting on the previous successful poll, to
        #: the timestamp the API gave. None until the first one succeeds, and
        #: distinct from an empty dict: "nothing observed yet" and "observed,
        #: nothing alerting" differ by exactly the clears they license.
        self._previous: dict[tuple[str, ThreatKind], datetime] | None = None
        #: The oblast last seen for an area, so a clear can name the oblast the
        #: area sits in after the API has stopped mentioning it at all.
        self._oblast_seen: dict[tuple[str, ThreatKind], str] = {}
        #: Regions the map could not resolve on the last poll, for the caller
        #: to report. A count that rises means the two vocabularies are drifting.
        self.unresolved: tuple[str, ...] = ()

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
        for alert in parse_alerts(payload):
            if alert.alert_type == "unparsed":
                continue
            resolved = _resolve(self._areas, alert)
            if resolved is None:
                unresolved.append(alert.region_name)
                continue
            area_id, oblast = resolved
            kind = _KIND.get(alert.alert_type, ThreatKind.UNKNOWN)
            key = (area_id, kind)
            current[key] = alert.started_at or now
            oblast_of[key] = oblast
        self.unresolved = tuple(dict.fromkeys(unresolved))

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
                    raw_fields={"api_region": area_id, "api_type": kind.name},
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
