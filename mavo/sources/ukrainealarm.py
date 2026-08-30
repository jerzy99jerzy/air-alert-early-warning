"""A second view of the same alerts, for measuring the first one.

**This is not a second source.** `api.ukrainealarm.com` and `alerts.in.ua`
draw from the same upstream that feeds the Telegram channel this project
reads, which the contract negotiation established and which
`docs/DECISIONS.md` records. Two views of one origin agreeing tells you the
views agree; it says nothing about whether the origin is right. Any sentence in
this project that reads "two sources confirm" would be false, and this module
exists partly so that the temptation has somewhere to be refused in writing.

**What it is for.** Two numbers nobody currently has.

*Latency.* The API publishes a state change with its own timestamp. Comparing
that against the moment the channel posted the same change gives an
end-to-end distribution rather than the fetch time per poll this project
measures today, which is T40 and one of two things standing between here and
beta.

*Coverage.* How many alerts the API reports that the parser did not, and the
reverse. That is a number about the completeness of the pattern table, and no
amount of hand-labelling produces it, because a hand-labeller reads the same
messages the parser reads.

**What it must never become.** An input to `state.json`. The contract carries
one observation of the world, and mixing a second view of the same upstream
into it would produce a picture whose provenance nobody could state. The
adapter has no `poll()` and does not implement `ThreatSource`, deliberately:
it cannot be dropped into the collector by accident. Since D-040 a sibling
module, `ukrainealarm_source.py`, *does* feed the contract - as the labelled
primary that replaced the dead channel, not as a second view mixed in - and
that is this prohibition being honoured, not broken.

**The key is a secret**, unlike the maps key. It identifies this project to
the provider and lives in an environment variable or a file the process reads,
never in the repository and never in anything served.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mavo.areas import AreaTable, oblast_slug
from mavo.errors import SourceUnavailable
from mavo.transport import Transport, UrllibTransport

API_BASE = "https://api.ukrainealarm.com/api/v3"

#: Environment variable holding the key. Named for the provider rather than
#: for this project, so an operator with several keys can tell them apart.
KEY_ENV = "MAVO_UKRAINEALARM_KEY"

#: Same ceiling as the channel transport, for the same reason: a stall must
#: end in a refusal rather than in a hung measurement run.
TIMEOUT_S = 10.0

#: The provider states a rate limit in its terms; this is well inside it and
#: exists so a measurement run cannot become the reason the key is revoked.
MIN_INTERVAL_S = 15.0


def read_key(explicit: str | None = None, path: Path | None = None) -> str:
    """The key, from an argument, a file or the environment, in that order.

    A file is offered because an environment variable is visible in
    `/proc/<pid>/environ` to anything running as the same user, and a
    deployment that already writes a unit file can write a `0600` file just as
    easily. Neither is offered as more secure than the other in general; the
    choice belongs to whoever runs it.
    """
    if explicit:
        return explicit.strip()
    if path is not None:
        return path.read_text(encoding="utf-8").strip()
    key = os.environ.get(KEY_ENV, "").strip()
    if not key:
        raise SourceUnavailable(
            f"no API key: pass one, point at a file, or set {KEY_ENV}"
        )
    return key


@dataclass(frozen=True, slots=True)
class ApiAlert:
    """One region's alert state as the API reports it.

    Deliberately thin. This is a measuring instrument's reading, not a
    `ThreatEvent`: it has no place in the store and no `content_hash`, and
    giving it either would be the first step towards it reaching the contract.
    """

    region_id: str
    region_name: str
    oblast: str | None
    alert_type: str
    started_at: datetime | None
    raw: dict[str, Any]


#: Words the API appends to a region name and the channel's hashtags do not.
#: `oblast_slug` was written against the hashtag form, so the two vocabularies
#: differ by exactly this suffix and joining them without stripping it produced
#: an empty slug for every region - a coverage measurement that would have
#: reported the parser missing everything.
_REGION_SUFFIXES = (" \u043e\u0431\u043b\u0430\u0441\u0442\u044c",
                    " \u041e\u0431\u043b\u0430\u0441\u0442\u044c")


def _stem(name: str) -> str:
    """The region name in the form `oblast_slug` was built for.

    Kyiv city arrives as `\u043c. \u041a\u0438\u0457\u0432` and is left
    alone: it is a city rather than an oblast, `oblast_slug` returns nothing
    for it, and inventing a mapping here would be this project guessing an
    administrative identity - the thing F90 and T44 exist to prevent.
    """
    stem = name.strip()
    for suffix in _REGION_SUFFIXES:
        if stem.endswith(suffix):
            return stem[: -len(suffix)].strip()
    return stem


def _stamp(value: Any) -> datetime | None:
    """An ISO timestamp, or None. Never `now` as a fallback.

    A missing timestamp substituted with the read time would make every
    latency measurement zero for exactly the records that have no timestamp,
    which is a bias towards the answer this module is meant to test.
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def parse_alerts(payload: Any, areas: AreaTable | None = None) -> tuple[ApiAlert, ...]:
    """Turn the API's answer into readings, dropping nothing silently.

    A record this cannot understand becomes an `ApiAlert` with
    `alert_type="unparsed"` rather than being skipped, because a coverage
    measurement whose denominator quietly shrinks is a coverage measurement
    that flatters whichever side it was built to test.
    """
    if not isinstance(payload, list):
        return ()
    out: list[ApiAlert] = []
    for region in payload:
        if not isinstance(region, dict):
            out.append(ApiAlert("", "", None, "unparsed", None, {"raw": repr(region)}))
            continue
        region_id = str(region.get("regionId") or "")
        name = str(region.get("regionName") or "")
        # The slug goes through the same function the channel parser uses, so
        # a coverage comparison is joining on one vocabulary rather than on
        # two that happen to look alike. `areas` is accepted and used to mark
        # a region the register does not know, rather than to drop it: an
        # unknown region is a finding about the register, and dropping it here
        # would hide the finding inside the measurement.
        slug = oblast_slug(_stem(name)) if name else None
        if areas is not None and slug and not any(
            ref.oblast and oblast_slug(ref.oblast) == slug
            for ref in (areas.resolve(tag) for tag in areas.tags)
            if ref is not None
        ):
            slug = None
        active = region.get("activeAlerts")
        if not isinstance(active, list) or not active:
            continue
        for alert in active:
            if not isinstance(alert, dict):
                out.append(
                    ApiAlert(region_id, name, slug, "unparsed", None,
                             {"raw": repr(alert)})
                )
                continue
            out.append(
                ApiAlert(
                    region_id=region_id,
                    region_name=name,
                    oblast=slug,
                    alert_type=str(alert.get("type") or "unknown"),
                    started_at=_stamp(alert.get("lastUpdate")),
                    raw=alert,
                )
            )
    return tuple(out)


class UkrainealarmProbe:
    """Reads the API. Has no `poll`, and that absence is the design.

    `ThreatSource` is the interface the collector accepts. This class does not
    implement it and does not want to: the only way this reading reaches
    `state.json` is if somebody writes the adapter code on purpose, at which
    point they will have to argue with the module docstring first.
    """

    source_id = "ukrainealarm-probe"

    def __init__(self, key: str, base: str = API_BASE,
                 transport: Transport | None = None) -> None:
        self._key = key
        self._base = base.rstrip("/")
        # Through the package's one network seam rather than around it. The
        # first version of this opened its own connection and the architecture
        # check caught it in the same run: network behaviour in two files is
        # network behaviour nobody can audit in one place.
        self._transport = transport or UrllibTransport(timeout_s=TIMEOUT_S)
        self._last_call = 0.0

    def _wait(self) -> None:
        elapsed = time.monotonic() - self._last_call
        if self._last_call and elapsed < MIN_INTERVAL_S:
            time.sleep(MIN_INTERVAL_S - elapsed)

    def alerts(self) -> tuple[ApiAlert, ...]:
        """Current alerts, or a refusal that says how long it waited.

        Same refusal shape as the channel transport (T55): elapsed seconds and
        the exception class, so a measurement run that fails leaves a journal
        line that can be read rather than a mystery.
        """
        self._wait()
        try:
            # The key travels in a header. In a URL it would reach every proxy
            # log between here and the provider.
            body = self._transport.fetch(
                f"{self._base}/alerts",
                headers={"Authorization": self._key,
                         "Accept": "application/json"},
            )
        finally:
            self._last_call = time.monotonic()
        try:
            return parse_alerts(json.loads(body))
        except ValueError as malformed:
            raise SourceUnavailable(
                f"{self._base}/alerts: malformed JSON ({malformed})"
            ) from malformed
