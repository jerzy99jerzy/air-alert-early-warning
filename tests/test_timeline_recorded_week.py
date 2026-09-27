"""The timeline against a week the production store recorded (D-058).

`tests/fixtures/store_week_2026-09-26.sqlite3.xz` is the week ending
2026-09-26T00:00:00Z as `vm-mavo` held it on 2026-09-27, recorded there by
`mavo/recorder.py` (sha256 `63aa2f73...a8576e0`), run with the host's own
interpreter because the release carrying it was not installed yet:

    sudo /usr/bin/python3 - /var/lib/mavo/events OUT 2026-09-26T00:00:00+00:00 7

It holds the rows the week's check reads and nothing else: 7,491 events, 147
lists of the communique scope and the updated plan, the 81 communiques and the
2,544 zones they name with 351 outlines, and 28,772 polls. Compressed here with
`xz -9e` and otherwise unedited; the digest below is the host's own
`sha256sum` of the file it wrote, so a fixture changed by hand fails before
anything else runs. Read before it was committed: no address, credential,
path or host name in any text column, and the polls' URLs are the public
endpoints.

Nobody chose these rows. The week has 188 area and kind keys standing at its
start, the ukrainealarm pipe's own timeouts, RCB and PAŻP whose record begins
inside it at 18:38 UTC on 2026-09-19, and the channel's gaps; the check has to
hold on all of it.
"""

from __future__ import annotations

import hashlib
import lzma
import random
from datetime import UTC, datetime
from pathlib import Path

import pytest

from mavo import timeline
from mavo.liveness import PRODUCTION_FEEDS
from mavo.schema import ThreatEvent
from mavo.store import EventStore
from mavo.timeline import TICK
from tests.test_timeline import TABLE, boundaries, normalised

FIXTURE = Path(__file__).parent / "fixtures" / "store_week_2026-09-26.sqlite3.xz"
DIGEST = "3a88310d7ca1b5a3629400af692d2be8aa0579aacc46f58d86dd5b0b37942e86"
END = datetime(2026, 9, 26, 0, 0, tzinfo=UTC)
#: The first poll of both Polish feeds, measured in the recording.
POLISH_RECORD = datetime(2026, 9, 19, 18, 38, 28, tzinfo=UTC)


@pytest.fixture(scope="module")
def week(tmp_path_factory: pytest.TempPathFactory
         ) -> tuple[EventStore, list[ThreatEvent], dict[str, object]]:
    raw = lzma.decompress(FIXTURE.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == DIGEST, "the recording was edited"
    path = tmp_path_factory.mktemp("week") / "events"
    path.write_bytes(raw)
    store = EventStore(path)
    events = list(store.replay())
    payload = normalised(timeline.build(store, events, END, table=TABLE,
                                        feeds=PRODUCTION_FEEDS))
    assert isinstance(payload, dict)
    return store, events, payload


def layered_moments(payload: dict[str, object], rng: random.Random) -> list[datetime]:
    """Random instants, plus boundaries drawn from each layer on its own.

    Drawn per layer because the areas carry thousands of boundaries and the
    other layers tens: a sample over all of them together would almost never
    land on an edge of the airspace or of a gap, which is where those layers
    could disagree.
    """
    start = datetime.fromisoformat(str(payload["window"]["start"]))  # type: ignore[index]
    span = (END - start).total_seconds()
    chosen = {start, END}
    chosen.update(start + (END - start) * rng.random() for _ in range(60))
    assert span > 0
    per_layer = {"areas": 15, "rcb": 10, "airspace": 15, "coverage": 20}
    for layer, count in per_layer.items():
        found = sorted(boundaries({layer: payload[layer]}))
        for edge in rng.sample(found, min(count, len(found))):
            chosen.update({edge - TICK, edge, edge + TICK})
    return sorted(moment for moment in chosen if start <= moment <= END)


def test_the_recorded_week_agrees_with_the_rules(
    week: tuple[EventStore, list[ThreatEvent], dict[str, object]],
) -> None:
    """Some two hundred instants: the file's picture, chosen, against the rules, asked."""
    store, events, payload = week
    rng = random.Random(58)
    chosen = layered_moments(payload, rng)
    assert len(chosen) >= 190
    for moment in chosen:
        from_file = normalised(timeline.picture_from_file(payload, moment))
        from_store = normalised(timeline.picture_from_store(
            store, events, moment, table=TABLE, feeds=PRODUCTION_FEEDS))
        assert from_file == from_store, f"the file and the rules disagree at {moment.isoformat()}"


def test_the_polish_record_starts_where_the_recording_says(
    week: tuple[EventStore, list[ThreatEvent], dict[str, object]],
) -> None:
    """A moment before the first poll has no record, which is not a quiet map."""
    _store, _events, payload = week
    before = timeline.picture_from_file(payload, datetime(2026, 9, 19, 18, 0, tzinfo=UTC))
    assert before["rcb"] == timeline.ABSENT and before["airspace"] == timeline.ABSENT
    assert before["coverage"]["rso"] == "unrecorded"  # type: ignore[index]
    assert before["coverage"]["pansa"] == "unrecorded"  # type: ignore[index]
    after = timeline.picture_from_file(payload, datetime(2026, 9, 19, 18, 40, tzinfo=UTC))
    assert after["rcb"] != timeline.ABSENT and after["airspace"] != timeline.ABSENT
    assert payload["rcb"]["recorded_since"] == POLISH_RECORD.replace(  # type: ignore[index]
        microsecond=168793).isoformat()


def test_the_week_is_drawn_from_every_layer(
    week: tuple[EventStore, list[ThreatEvent], dict[str, object]],
) -> None:
    """A recording that exercised one layer would test one layer."""
    _store, _events, payload = week
    counts = timeline.interval_counts(payload)
    assert counts["areas"] > 1000 and counts["rcb"] > 1 and counts["airspace"] > 10
    assert counts["gaps"] > 0, "the channel's timeouts are in the week"
    assert payload["areas"]["log_reaches_window_start"] is True  # type: ignore[index]
