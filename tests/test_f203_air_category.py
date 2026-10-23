"""F203, D-065: RCB's air alerts moved to a category the walk did not read.

On 2026-10-21 the publisher gave air-attack communiques a category of their
own, `atak-z-powietrza`, and they left `ogolne`. Every read of `ogolne`
succeeded for two days, so the map, the slider and the forty-eight-hour
register published a quiet country while RCB raised alerts in both border
voivodeships. These tests replay that shape: the map scope is two addresses
from `poland.AIR_URL_SINCE`, a moment that needs the second without a read of
it is `null` and unread rather than quiet, and an alert listed only in the
new category paints, on the live cycle and on the slider alike.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from mavo import poland, rcb_recent
from mavo.sources import rso
from mavo.store import EventStore
from mavo.timeline import rcb_layer, warnings_record
from tests.test_timeline import serve

SINCE = poland.AIR_URL_SINCE

#: An all-clear and an alert as `atak-z-powietrza` served them on 2026-10-23,
#: bodies shortened; the alert raised at 04:10 Warsaw time.
AIR_PAGE = b"""<?xml version="1.0" encoding="utf-8"?>
<newses>
  <pagination_info totalItems="1" itemsPerPage="20"></pagination_info>
  <news>
    <id>23441700</id>
    <title>ALERT RCB</title>
    <shortcut>UWAGA! Rosyjski atak powietrzny na terenie Ukrainy. Sytuacja jest
    monitorowana. W przestrzeni RP operuje polskie lotnictwo.</shortcut>
    <content>Zgodnie z decyzja dyrektora RCB wyslano Alert RCB o tresci: UWAGA!
    Rosyjski atak powietrzny na terenie Ukrainy.</content>
    <valid_from>2026-10-23 04:10:00</valid_from>
    <valid_to>2026-10-23 23:59:00</valid_to>
    <created_at>2026-10-23 04:10:31</created_at>
    <updated_at>2026-10-23 04:10:31</updated_at>
    <provinces><province slug="lubelskie">Lubelskie</province></provinces>
  </news>
</newses>
"""


def air_alert() -> list[Any]:
    return list(rso.parse_page(AIR_PAGE).communiques)


def painted(block: poland.Block) -> set[tuple[str, str]]:
    assert block.published and block.value is not None
    return {(row["slug"], str(item["id"])) for row in block.value
            for item in row["communiques"]}


# ---- the joined read and list


def test_the_scope_is_one_address_before_the_air_category_and_two_from_it() -> None:
    assert poland.warnings_urls(SINCE - timedelta(seconds=1)) == (poland.WARNINGS_URL,)
    assert poland.warnings_urls(SINCE) == (poland.WARNINGS_URL, poland.AIR_URL)
    assert rso.page_url("atak-z-powietrza", 0) == poland.AIR_URL


def test_a_list_is_as_current_as_its_stalest_address_and_unread_without_one() -> None:
    moment = SINCE + timedelta(days=1)
    early, late = moment - timedelta(minutes=9), moment - timedelta(minutes=1)
    assert poland.joined_read({poland.WARNINGS_URL: late, poland.AIR_URL: early},
                              moment) == early
    assert poland.joined_read({poland.WARNINGS_URL: late, poland.AIR_URL: None},
                              moment) is None, "an unread address read as current"
    assert poland.joined_read({poland.WARNINGS_URL: late}, SINCE - timedelta(hours=1)) == late


def test_the_joined_list_keeps_each_digest_once_and_needs_every_address() -> None:
    moment = SINCE + timedelta(days=1)
    joined = poland.joined_members({poland.WARNINGS_URL: ["a", "b"],
                                    poland.AIR_URL: ["b", "c"]}, moment)
    assert joined == ["a", "b", "c"]
    assert poland.joined_members({poland.WARNINGS_URL: ["a"], poland.AIR_URL: None},
                                 moment) is None
    assert poland.joined_members({poland.WARNINGS_URL: []}, SINCE - timedelta(1)) == []


# ---- the live cycle


def test_a_quiet_ogolne_without_the_air_category_is_null_and_not_quiet(
        tmp_path: Path) -> None:
    """F203 itself: every read of `ogolne` fresh and empty, the air category
    never read. Until 0.62.0.0 this published an empty list, which the page
    renders as no communique, while RCB's alert sat in the other category."""
    store = EventStore(tmp_path / "events")
    moment = datetime(2026, 10, 23, 2, 30, tzinfo=UTC)
    for minutes in (30, 20, 10):
        at = moment - timedelta(minutes=minutes)
        store.record_snapshot(rso.FEED, poland.WARNINGS_URL, at, [])
        store.record_read(rso.FEED, poland.WARNINGS_URL, at, 0, 0)
    warnings, cleared = poland.warnings_blocks(store, moment)
    assert warnings.published and warnings.value is None, "silence rendered as calm"
    assert cleared.published and cleared.value is None


def test_an_alert_listed_only_in_the_air_category_paints(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    moment = datetime(2026, 10, 23, 2, 30, tzinfo=UTC)
    for minutes in (30, 20, 10):
        serve(store, moment - timedelta(minutes=minutes), [], air_alert())
    warnings, _cleared = poland.warnings_blocks(store, moment)
    assert painted(warnings) == {("lubelskie", "23441700")}


def test_before_the_air_category_ogolne_alone_is_the_whole_scope(tmp_path: Path) -> None:
    """The week before 2026-10-21 reads as it always did: nothing retroactive
    happens to a moment the second address did not exist for."""
    from tests.test_poland import PAGE

    store = EventStore(tmp_path / "events")
    moment = SINCE - timedelta(hours=2)
    serve(store, moment - timedelta(minutes=5), list(rso.parse_page(PAGE).communiques))
    warnings, _cleared = poland.warnings_blocks(store, moment)
    assert ("malopolskie", "1") in painted(warnings)


# ---- the slider and the register


@pytest.fixture
def across(tmp_path: Path) -> tuple[EventStore, datetime, datetime]:
    """`ogolne` read every ten minutes across the widening, the air category
    first read four hours after it, as the install of 0.62.0.0 will be, and
    holding an alert from then on."""
    store = EventStore(tmp_path / "events")
    # Off the ten-minute grid by three minutes, so no read falls on
    # `AIR_URL_SINCE` itself: the widening has to be found, not stumbled on.
    start = SINCE - timedelta(hours=2, minutes=3)
    first_air = SINCE + timedelta(hours=4)
    moment = start
    while moment <= first_air + timedelta(hours=1):
        if moment < first_air:
            # The ogolne half of the walk the host ran before the release.
            store.record_snapshot(rso.FEED, poland.WARNINGS_URL, moment, [])
            store.record_read(rso.FEED, poland.WARNINGS_URL, moment, 0, 0)
        else:
            serve(store, moment, [], air_alert())
        moment += timedelta(minutes=10)
    return store, start, first_air


def test_the_slider_paints_what_the_live_cycle_paints_across_the_widening(
        across: tuple[EventStore, datetime, datetime]) -> None:
    store, start, first_air = across
    end = first_air + timedelta(hours=1)
    layer = rcb_layer(store, start, end)
    for offset in range(0, int((end - start).total_seconds()), 600):
        moment = start + timedelta(seconds=offset, minutes=3)
        live = poland.warnings_blocks(store, moment)[0]
        [span] = [one for one in layer.spans
                  if one.span.start <= moment and (one.span.end is None or moment < one.span.end)]
        assert span.warnings == live, moment


def test_the_register_calls_the_stretch_before_the_first_air_read_unread(
        across: tuple[EventStore, datetime, datetime]) -> None:
    store, start, first_air = across
    end = first_air + timedelta(hours=1)
    value = rcb_recent.summarise(rcb_recent.record(store, start, end), start, end, hours=6)
    assert value is not None
    unread = [(item["from"], item["to"]) for item in value["unread"]]
    assert unread, "two days nobody could see read as two quiet days"
    opened, closed = (datetime.fromisoformat(one) for one in unread[0])
    assert opened <= SINCE and closed >= first_air - timedelta(minutes=10), unread
    [row] = value["voivodeships"]
    assert row["slug"] == "lubelskie"
    assert [alert["id"] for alert in row["alerts"]] == ["23441700"]


def test_the_scope_record_joins_the_lists_and_reads_as_the_composer_does(
        across: tuple[EventStore, datetime, datetime]) -> None:
    store, start, first_air = across
    record = warnings_record(store, start, first_air + timedelta(hours=1))
    assert record.read_at(SINCE + timedelta(minutes=1)) is None
    assert record.members_at(SINCE + timedelta(minutes=1)) is None
    assert record.read_at(SINCE - timedelta(minutes=1)) is not None
    reads = record.joined_reads()
    assert all(a < b for a, b in zip(reads, reads[1:], strict=False))
    assert not [one for one in reads if SINCE <= one < first_air - timedelta(minutes=10)]
    [digest] = record.lists[poland.AIR_URL][0][1]
    first_read = record.reads[poland.AIR_URL][0]
    assert first_read >= first_air
    assert record.members_at(first_read - timedelta(seconds=1)) is None
    assert record.members_at(first_read) == [digest]


# ---- the canary


def test_a_communique_the_walk_never_returned_is_named_once() -> None:
    scope = rso.Page(communiques=tuple(rso.parse_page(AIR_PAGE).communiques), unreadable=1)
    assert rso.unwalked(scope, ["1", "2"]) == ("23441700", "")
    assert rso.unwalked(scope, ["23441700"]) == ("",), "an unreadable row is not seen nothing"
    assert rso.unwalked(rso.Page(communiques=scope.communiques), ["23441700"]) == ()


# ---- what the review of 0.62.0.0 found


def test_the_widening_is_pinned_to_the_earliest_instant_the_record_cannot_rule_out() -> None:
    """Eight hours lie between this and the portal's build stamp; moved to the
    later one, they would read as quiet instead of unread."""
    assert datetime(2026, 10, 21, 2, 46, 22, tzinfo=UTC) == SINCE


def test_an_air_list_whose_read_aged_out_is_null_beside_a_fresh_ogolne(
        tmp_path: Path) -> None:
    """The air address read two hours ago, `ogolne` a minute ago: the list is as
    old as its stalest half, past the hour ceiling."""
    store = EventStore(tmp_path / "events")
    moment = SINCE + timedelta(days=2)
    serve(store, moment - timedelta(hours=2), [], air_alert())
    store.record_snapshot(rso.FEED, poland.WARNINGS_URL, moment - timedelta(minutes=1), [])
    store.record_read(rso.FEED, poland.WARNINGS_URL, moment - timedelta(minutes=1), 0, 0)
    warnings, _cleared = poland.warnings_blocks(store, moment)
    assert warnings.published and warnings.value is None


def test_a_read_with_no_list_behind_it_is_null_and_not_empty(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    moment = SINCE - timedelta(days=2)
    store.record_read(rso.FEED, poland.WARNINGS_URL, moment - timedelta(minutes=5), 0, 0)
    warnings, _cleared = poland.warnings_blocks(store, moment)
    assert warnings.published and warnings.value is None


def test_a_list_no_read_vouched_for_is_never_the_one_shown(tmp_path: Path) -> None:
    """The review's D1. A walk the canary rejected writes its lists and no
    reads; taken at the moment, they were shown under the previous walk's
    read, so the walk built to say "cannot vouch" painted a quiet country.
    Each address's list is the one its own read vouched for."""
    store = EventStore(tmp_path / "events")
    vouched = SINCE + timedelta(days=2)
    serve(store, vouched, [], air_alert())
    rejected = vouched + timedelta(minutes=1)
    # The rejected walk's air list holds another alert, one that has run out
    # three minutes on: its end is an instant the slider stops at, where a
    # list taken at the moment rather than at its read would show nothing.
    other = [rso.Communique(id="23441800",
                            provinces=(rso.Province("podkarpackie", "Podkarpackie"),),
                            fields={"title": "ALERT RCB", "valid_to": "2026-10-23 04:50:22"})]
    store.append_communiques(rso.FEED, other)
    for url, items in ((poland.WARNINGS_URL, []), (poland.AIR_URL, other)):
        store.record_snapshot(rso.FEED, url, rejected, [item.digest() for item in items])
        store.record_refusal(rso.FEED, url, rejected, "[UNKNOWN-CATEGORY] 1")
    moment = rejected + timedelta(minutes=5)
    warnings, _cleared = poland.warnings_blocks(store, moment)
    assert painted(warnings) == {("lubelskie", "23441700")}, "a rejected walk's list was shown"
    layer = rcb_layer(store, vouched - timedelta(minutes=1), moment)
    [span] = [one for one in layer.spans if one.span.start <= moment
              and (one.span.end is None or moment < one.span.end)]
    assert span.warnings == warnings, "the slider showed what the live map does not"
    late = vouched + timedelta(hours=1, minutes=1)
    assert poland.warnings_blocks(store, late)[0].value is None, "an unvouched hour read as current"


def test_a_walk_that_read_both_before_the_widening_paints_on_the_slider_as_live(
        tmp_path: Path) -> None:
    """The review's D2: the scope widens at an instant no read marks. Both
    addresses read once, ten minutes before it, the alert in the air list:
    before the widening only `ogolne` counts, after it both do."""
    store = EventStore(tmp_path / "events")
    serve(store, SINCE - timedelta(minutes=10), [])
    items = air_alert()
    store.append_communiques(rso.FEED, items)
    store.record_snapshot(rso.FEED, poland.AIR_URL, SINCE - timedelta(minutes=10),
                          [item.digest() for item in items])
    store.record_read(rso.FEED, poland.AIR_URL, SINCE - timedelta(minutes=10), 1, 0)
    moment = SINCE + timedelta(minutes=5)
    live = poland.warnings_blocks(store, moment)[0]
    assert painted(live) == {("lubelskie", "23441700")}
    layer = rcb_layer(store, SINCE - timedelta(minutes=10), SINCE + timedelta(minutes=30))
    [span] = [one for one in layer.spans if one.span.start <= moment
              and (one.span.end is None or moment < one.span.end)]
    assert span.warnings == live
    end = SINCE + timedelta(minutes=30)
    value = rcb_recent.summarise(rcb_recent.record(store, SINCE - timedelta(minutes=10), end),
                                 SINCE - timedelta(minutes=10), end, hours=1)
    assert value is not None
    assert [row["slug"] for row in value["voivodeships"]] == ["lubelskie"]


def test_a_list_a_rejected_walk_wrote_shows_from_the_next_read_that_vouches_for_it(
        tmp_path: Path) -> None:
    """A rejected walk finds the alert in the air list; the next walk is
    vouched and reads the same list, so no new list is written. The alert
    shows from that read, on the slider as on the live map."""
    store = EventStore(tmp_path / "events")
    first = SINCE + timedelta(days=2)
    serve(store, first, [])
    items = air_alert()
    store.append_communiques(rso.FEED, items)
    rejected = first + timedelta(minutes=1)
    store.record_snapshot(rso.FEED, poland.WARNINGS_URL, rejected, [])
    store.record_snapshot(rso.FEED, poland.AIR_URL, rejected, [item.digest() for item in items])
    for url in poland.WARNINGS_URLS:
        store.record_refusal(rso.FEED, url, rejected, "[UNVOUCHED] 1 address(es) refused")
    second = rejected + timedelta(minutes=1)
    for url in poland.WARNINGS_URLS:
        store.record_read(rso.FEED, url, second, 0, 0)
    for moment in (rejected + timedelta(seconds=30), second + timedelta(seconds=30)):
        live = poland.warnings_blocks(store, moment)[0]
        layer = rcb_layer(store, first, second + timedelta(minutes=5))
        [span] = [one for one in layer.spans if one.span.start <= moment
                  and (one.span.end is None or moment < one.span.end)]
        assert span.warnings == live, moment
    assert painted(poland.warnings_blocks(store, second + timedelta(seconds=30))[0]) == {
        ("lubelskie", "23441700")}


def test_the_air_address_alone_going_unread_is_a_stretch_of_the_register(
        tmp_path: Path) -> None:
    """The review's R2: `ogolne` read every five minutes for an hour, the air
    address refused for forty-five of them. The register's reads are the
    scope's, so the stretch is unread though `ogolne` never stopped."""
    store = EventStore(tmp_path / "events")
    t0 = SINCE + timedelta(days=2)
    for step in range(13):
        at = t0 + timedelta(minutes=5 * step)
        if 2 <= step <= 10:
            store.record_snapshot(rso.FEED, poland.WARNINGS_URL, at, [])
            store.record_read(rso.FEED, poland.WARNINGS_URL, at, 0, 0)
            store.record_refusal(rso.FEED, poland.AIR_URL, at, "HTTP Error 503")
        else:
            serve(store, at, [])
    end = t0 + timedelta(hours=1)
    value = rcb_recent.summarise(rcb_recent.record(store, t0, end), t0, end, hours=1)
    assert value is not None and value["unread"], "half a scope read as the whole one"


# ---- the slider against the live cycle, over histories nobody chose


_FUZZ_ALERT = """<newses><pagination_info totalItems="1" itemsPerPage="20"/><news>
<id>{id}</id><title>ALERT RCB</title><shortcut>UWAGA! Rosyjski atak powietrzny na terenie
Ukrainy.</shortcut><valid_from>2026-10-20 00:00:00</valid_from><valid_to>{valid_to}</valid_to>
<provinces><province slug="lubelskie">Lubelskie</province></provinces></news></newses>"""


def _random_history(store: EventStore, seed: int, air_before: bool) -> tuple[datetime, datetime]:
    """Two addresses read at random intervals across the widening: refusals,
    gaps past the hour ceiling, alerts that expire, and one list in ten written
    with no read, as a walk the canary rejected writes it. The review of
    0.62.0.0 found the D2 and window-start disagreements with this generator."""
    import random

    rng = random.Random(seed)
    start, end = SINCE - timedelta(hours=3), SINCE + timedelta(hours=5)
    for url in poland.WARNINGS_URLS:
        at = start - timedelta(minutes=rng.randint(0, 90))
        first_air = SINCE + timedelta(minutes=rng.randint(-120 if air_before else 0, 180))
        while at < end:
            if url == poland.AIR_URL and at < first_air:
                at += timedelta(minutes=rng.choice([1, 5, 15]))
                continue
            if rng.random() < 0.15:
                store.record_refusal(rso.FEED, url, at, "HTTP Error 503")
            else:
                items: list[rso.Communique] = []
                if rng.random() < 0.4:
                    valid_to = rng.choice(["2026-10-21 06:00:00", "2026-10-21 03:30:00",
                                           "2099-01-01 00:00:00"])
                    body = _FUZZ_ALERT.format(id=rng.randint(1, 3), valid_to=valid_to)
                    items = list(rso.parse_page(body.encode("utf-8")).communiques)
                store.append_communiques(rso.FEED, items)
                store.record_snapshot(rso.FEED, url, at, [item.digest() for item in items])
                if rng.random() < 0.9:
                    store.record_read(rso.FEED, url, at, len(items), 0)
            at += timedelta(minutes=rng.choice([1, 7, 15, 15, 30, 70]), seconds=rng.randint(0, 59))
    return start, end


@pytest.mark.parametrize("air_before", [False, True])
@pytest.mark.parametrize("seed", [0, 7, 21, 22])
def test_the_slider_and_the_live_cycle_agree_over_a_random_history(
        tmp_path: Path, seed: int, air_before: bool) -> None:
    from mavo.timeline import TICK

    store = EventStore(tmp_path / "events")
    start, end = _random_history(store, seed, air_before)
    layer = rcb_layer(store, start, end)
    probes = {SINCE - TICK, SINCE, SINCE + TICK}
    for one in layer.spans:
        probes |= {one.span.start - TICK, one.span.start, one.span.start + TICK}
    probes |= {start + timedelta(seconds=97 * step)
               for step in range(int((end - start).total_seconds() // 97))}
    for moment in sorted(probe for probe in probes if start <= probe <= end):
        live = poland.warnings_blocks(store, moment)
        spans = [one for one in layer.spans if one.span.start <= moment
                 and (one.span.end is None or moment < one.span.end)]
        if not spans:
            assert not live[0].published, moment
            continue
        [span] = spans
        assert (span.warnings, span.all_clear) == live, moment
    assert rcb_recent.summarise(rcb_recent.record(store, start, end), start, end,
                                hours=8) is not None
