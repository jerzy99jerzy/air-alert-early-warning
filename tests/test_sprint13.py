"""Sprint 13: a second view of the same alerts, for measuring the first one.

**Read the module docstring before reading these.** The adapter is a measuring
instrument, not a source. Half of what is checked here is that it cannot
become one by accident.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from mavo.errors import SourceUnavailable
from mavo.sources.ukrainealarm import (
    KEY_ENV,
    MIN_INTERVAL_S,
    ApiAlert,
    UkrainealarmProbe,
    parse_alerts,
    read_key,
)

#: Shaped after the provider's documented response. Region names carry the
#: suffix the channel's hashtags do not, which is the whole reason `_stem`
#: exists and the reason this fixture keeps it rather than tidying it away.
SAMPLE: list[dict[str, Any]] = [
    {
        "regionId": "31",
        "regionName": "\u041b\u044c\u0432\u0456\u0432\u0441\u044c\u043a\u0430 "
                      "\u043e\u0431\u043b\u0430\u0441\u0442\u044c",
        "activeAlerts": [{"type": "AIR", "lastUpdate": "2026-08-13T04:12:00Z"}],
    },
    {
        "regionId": "14",
        "regionName": "\u0414\u043e\u043d\u0435\u0446\u044c\u043a\u0430 "
                      "\u043e\u0431\u043b\u0430\u0441\u0442\u044c",
        "activeAlerts": [{"type": "AIR", "lastUpdate": "2026-08-13T04:20:00Z"}],
    },
    {"regionId": "12", "regionName": "X", "activeAlerts": []},
]


def test_the_probe_is_not_a_source() -> None:
    """The absence of `poll` is the design, not an omission.

    `ThreatSource` is what the collector accepts. This class does not
    implement it, so the only way an API reading reaches `state.json` is if
    somebody writes that adapter deliberately and argues with the module
    docstring first. Two views of one upstream are not two sources, and a
    contract carrying both would have a provenance nobody could state.
    Mutation: add a `poll` method.
    """
    assert not hasattr(UkrainealarmProbe, "poll")
    assert not hasattr(ApiAlert, "content_hash"), (
        "a reading gained the shape of a stored event"
    )


def test_region_names_join_on_the_channel_vocabulary() -> None:
    """The API appends a word the hashtags do not, and joining without
    stripping it produced an empty slug for every region.

    A coverage measurement built on that would have reported the parser
    missing everything, which is the most flattering possible error for the
    API and the most damning for the thing being measured. Mutation: drop
    `_stem`.
    """
    alerts = parse_alerts(SAMPLE)
    assert [a.oblast for a in alerts] == ["lviv", "donetsk"]


def test_kyiv_city_gets_no_oblast_and_that_is_correct() -> None:
    """It is a city, not an oblast. Inventing a mapping here would be this
    project guessing an administrative identity, which is what F90 and T44
    exist to prevent. Mutation: map it to `kyiv`."""
    payload = [{
        "regionId": "80",
        "regionName": "\u043c. \u041a\u0438\u0457\u0432",
        "activeAlerts": [{"type": "AIR", "lastUpdate": "2026-08-13T04:22:00Z"}],
    }]
    assert parse_alerts(payload)[0].oblast == ""


def test_a_record_it_cannot_read_is_kept_and_marked() -> None:
    """A coverage measurement whose denominator quietly shrinks flatters
    whichever side it was built to test.

    Mutation: skip unreadable records, which is the obvious way and silently
    improves whichever number the reader was hoping for.
    """
    alerts = parse_alerts([
        "rubbish",
        {"regionId": "1", "regionName": "Y", "activeAlerts": ["rubbish"]},
    ])
    assert [a.alert_type for a in alerts] == ["unparsed", "unparsed"]


def test_a_missing_timestamp_is_none_and_never_now() -> None:
    """Substituting the read time would make latency zero for exactly the
    records that have no timestamp: a bias towards the answer this module was
    built to test. Mutation: default to `datetime.now`."""
    payload = [{"regionId": "1", "regionName": "Y",
                "activeAlerts": [{"type": "AIR"}]}]
    assert parse_alerts(payload)[0].started_at is None


def test_a_timestamp_without_a_zone_is_read_as_utc() -> None:
    """The API publishes UTC. A naive datetime compared against an aware one
    raises, and a latency run that dies halfway is a latency run with a
    silently truncated sample."""
    payload = [{"regionId": "1", "regionName": "Y",
                "activeAlerts": [{"type": "AIR", "lastUpdate": "2026-08-13T04:12:00"}]}]
    stamp = parse_alerts(payload)[0].started_at
    assert stamp == datetime(2026, 8, 13, 4, 12, tzinfo=UTC)


def test_the_key_comes_from_a_file_or_the_environment_and_never_the_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unlike the maps key, this one identifies the project to the provider.

    Mutation: give `read_key` a default, which is how a secret ends up in a
    repository.
    """
    monkeypatch.delenv(KEY_ENV, raising=False)
    with pytest.raises(SourceUnavailable):
        read_key()

    keyfile = tmp_path / "key"
    keyfile.write_text("  abc:def  \n", encoding="utf-8")
    assert read_key(path=keyfile) == "abc:def"

    monkeypatch.setenv(KEY_ENV, "env:key")
    assert read_key() == "env:key"
    assert read_key("explicit:key") == "explicit:key"


def test_the_key_travels_in_a_header_and_not_in_the_url() -> None:
    """A key in a query string reaches every proxy log between here and the
    provider.

    Checked through the package's own stub transport rather than by patching
    urllib, because the probe now goes through the one network seam: the first
    version opened its own connection and the architecture check caught it.
    Mutation: append the key to the URL.
    """
    from mavo.transport import StubTransport

    stub = StubTransport(json.dumps(SAMPLE))
    probe = UkrainealarmProbe("secret:key", transport=stub)
    assert len(probe.alerts()) == 2
    assert stub.last_headers.get("Authorization") == "secret:key"


def test_a_refusal_reaches_the_caller_as_a_refusal() -> None:
    """The transport raises `SourceUnavailable` and nothing else, and it
    already carries the elapsed time and exception class (T55). The probe adds
    nothing and hides nothing: a second layer of wrapping would bury the
    duration the diagnostic exists for."""
    from mavo.transport import FailingTransport

    probe = UkrainealarmProbe("k", transport=FailingTransport())
    with pytest.raises(SourceUnavailable) as refusal:
        probe.alerts()
    assert "injected failure" in str(refusal.value)


def test_the_probe_paces_itself() -> None:
    """A measurement run must not become the reason the key is revoked.

    Mutation: remove the wait, which is invisible in a test suite and visible
    to the provider.
    """
    assert MIN_INTERVAL_S >= 15.0
    import inspect

    source = inspect.getsource(UkrainealarmProbe.alerts)
    assert "self._wait()" in source
