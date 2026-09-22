"""The `@kpszsu` reader against recordings, never against drawings (D-056).

**Every expected figure below was read by hand from the message**, on
2026-09-22, and written down before the reader ran on it. That order is the
point of this file. The project's most persistent error class is a fixture
chosen by the implementation (F50, F154, F157): data that cannot tell a right
reading from a wrong one, so a mutation survives. Reading the eighteen messages
by hand found four defects that 98 runs of the reader over the corpus could not
see, because 86 of the nights publish no launched total to check against: three
air-launched missiles read as three Banderols (73939), an unnumbered ballistic
missile dropped from the launched side (74748), unnumbered impacts filtered out
(66637, 68010, 79455) and a day tally's second sentence never read (78115).

The recordings are `tests/fixtures/kpszsu/<post>.html`, the raw block the
public preview served after the post's `data-post` marker, and `<post>.txt`,
the text the harvester took from it with `telegram._strip`. The first test
here reads every `.html` through the adapter and requires the `.txt`: two
readers of one recording, a year of code apart, agreeing.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from mavo.errors import SourceUnavailable
from mavo.sources import kpszsu
from mavo.sources.kpszsu import Reading, Tally
from mavo.transport import StubTransport

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "kpszsu"

N = None
#: Read by hand from each message. (class, count) in the order the message
#: names them; None where the message gives no numeral. `loc` is hit
#: locations and debris locations; `as_of` is the hour as the message states
#: it, Kyiv time.
EXPECTED: dict[str, dict[str, object]] = {
    "66440": dict(kind="night", night="2026-06-26", as_of="09:00",
                  launched=[("ballistic", 7), ("drone", 189)],
                  downed=[("ballistic", 3), ("drone", 174)],
                  impacts=[("ballistic", 4), ("drone", 11)], loc=(12, 6)),
    "66637": dict(kind="night", night="2026-06-28", as_of="08:30",
                  launched=[("anti_ship", 2), ("ballistic", 6), ("drone", 142)],
                  downed=[("anti_ship", 1), ("ballistic", 6), ("drone", 125)],
                  impacts=[("other", N), ("drone", 14)], loc=(11, 13)),
    "66963": dict(kind="night", night="2026-07-01", as_of="07:30",
                  launched=[("ballistic", N), ("air_launched", N), ("drone", 151)],
                  downed=[("air_launched", N), ("drone", 130)],
                  impacts=[("drone", 17)], loc=(16, 4)),
    "67095": dict(kind="night", night="2026-07-02", as_of="09:00",
                  launched=[("anti_ship", 4), ("ballistic", 24), ("cruise", 34), ("cruise", 8),
                            ("air_launched", 4), ("drone", 496)],
                  downed=[("ballistic", 4), ("cruise", 32), ("cruise", 8), ("air_launched", 4),
                          ("drone", 476)],
                  impacts=[("ballistic", 25), ("drone", 12)], loc=(33, 18)),
    "67183": dict(kind="night", night="2026-07-03", as_of="08:30",
                  launched=[("air_launched", 2), ("drone", 105)],
                  downed=[("air_launched", 1), ("drone", 82)],
                  impacts=[("air_launched", 1), ("drone", 21)], loc=(16, 5)),
    "68010": dict(kind="night", night="2026-07-11", as_of="08:30",
                  launched=[("ballistic", 6), ("air_launched", 4), ("anti_radar", 2),
                            ("drone", 121)],
                  downed=[("air_launched", 2), ("drone", 111)],
                  impacts=[("ballistic", N), ("air_launched", 2), ("drone", 7)], loc=(11, 3)),
    "69144": dict(kind="night", night="2026-07-19", as_of="08:30",
                  launched=[("anti_ship", 10), ("ballistic", 25), ("anti_ship", 3),
                            ("air_launched", 3), ("drone", 125)],
                  downed=[("other", 17), ("air_launched", 1), ("drone", 108)],
                  impacts=[("other", 23), ("drone", 10)], loc=(20, 18)),
    "71026": dict(kind="night", night="2026-08-01", as_of="09:30",
                  launched=[("anti_ship", 4), ("ballistic", 27), ("anti_radar", 2),
                            ("air_launched", 2), ("drone", 185)],
                  downed=[("ballistic", 1), ("air_launched", 1), ("drone", 154)],
                  impacts=[("anti_ship", 4), ("ballistic", 26), ("drone", 23)], loc=(21, 2)),
    "72214": dict(kind="night", night="2026-08-10", as_of="09:00",
                  launched=[("air_launched", N), ("banderol", 3), ("drone", 126)],
                  downed=[("drone", 92), ("banderol", 3)],
                  impacts=[("drone", 31)], loc=(22, 2)),
    "73939": dict(kind="night", night="2026-08-22", as_of="09:00",
                  launched=[("ballistic", N), ("other", 3), ("banderol", N), ("drone", 217)],
                  downed=[("other", 3), ("banderol", 6), ("drone", 182)],
                  impacts=[], loc=(41, 12)),
    "74294": dict(kind="night", night="2026-08-24", as_of="09:00",
                  launched=[("anti_ship", 2), ("air_launched", 6), ("drone", 143)],
                  downed=[("anti_ship", 1), ("air_launched", 2), ("banderol", 2), ("drone", 109)],
                  impacts=[], loc=(22, 5)),
    "74748": dict(kind="night", night="2026-08-27", as_of="09:00",
                  launched=[("anti_ship", 2), ("ballistic", N), ("drone", 258)],
                  downed=[("anti_ship", 1), ("ballistic", 7), ("banderol", 3), ("drone", 222)],
                  impacts=[], loc=(15, 11)),
    "75719": dict(kind="night", night="2026-09-01", as_of="08:30",
                  launched=[("ballistic", N), ("anti_ship", N), ("cruise", N), ("anti_radar", N),
                            ("banderol", N), ("drone", 218)],
                  downed=[("ballistic", 5), ("banderol", 2), ("cruise", 5), ("drone", 187)],
                  impacts=[("other", N), ("drone", N)], loc=(28, 10)),
    "78115": dict(kind="day", night="2026-09-13", as_of="18:00",
                  launched=[("drone", 323), ("banderol", N)],
                  downed=[("drone", 310)],
                  impacts=[("drone", 10)], loc=(N, N)),
    "79268": dict(kind="night", night="2026-09-21", as_of="08:00",
                  launched=[("drone", 172), ("banderol", N)],
                  downed=[("drone", 147), ("banderol", 1)],
                  impacts=[], loc=(14, 4)),
    "79455": dict(kind="night", night="2026-09-22", as_of="08:00",
                  launched=[("anti_ship", N), ("ballistic", N), ("cruise", 4), ("banderol", 8),
                            ("drone", 212)],
                  downed=[("cruise", 1), ("banderol", 8), ("drone", 177)],
                  impacts=[("other", N), ("drone", N)], loc=(22, 4)),
}
CORRECTIONS = ("69965", "72080")
RECORDED = sorted(EXPECTED) + list(CORRECTIONS)


def _page_of(post: str) -> str:
    """The recording as the preview served it: the marker, then the raw block."""
    return f'data-post="kpszsu/{post}"' + (FIXTURES / f"{post}.html").read_text(encoding="utf-8")


def _reading(post: str) -> Reading:
    page = kpszsu.read_page(_page_of(post))
    assert len(page.readings) == 1
    return page.readings[0]


def _tally(post: str) -> Tally:
    tally = _reading(post).tally
    assert tally is not None
    return tally


def _pairs(items: tuple[kpszsu.Item, ...]) -> list[tuple[str, int | None]]:
    return [(item.cls, item.count) for item in items]


def _corpus() -> list[dict[str, str]]:
    lines = (FIXTURES / "summaries.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def _corpus_tallies() -> list[tuple[str, Tally]]:
    out = []
    for row in _corpus():
        tally = kpszsu.parse(row["text"], datetime.fromisoformat(row["posted_at"]))
        if tally is not None:
            out.append((row["id"], tally))
    return out


@pytest.mark.parametrize("post", RECORDED)
def test_a_recorded_block_reads_to_its_recorded_text(post: str) -> None:
    page = kpszsu.read_page(_page_of(post))
    assert (page.messages, page.unreadable) == (1, 0)
    assert page.first_id == page.last_id == int(post)
    expected = (FIXTURES / f"{post}.txt").read_text(encoding="utf-8")
    assert page.readings[0].message.text == expected
    assert page.readings[0].message.posted_at.tzinfo is not None
    assert page.readings[0].message.source_url == f"https://t.me/kpszsu/{post}"


@pytest.mark.parametrize("post", sorted(EXPECTED))
def test_the_figures_are_the_ones_read_by_hand(post: str) -> None:
    expected = EXPECTED[post]
    tally = _tally(post)
    assert tally.kind == expected["kind"]
    assert _pairs(tally.launched) == expected["launched"]
    assert _pairs(tally.downed) == expected["downed"]
    assert _pairs(tally.impacts) == expected["impacts"]
    assert (tally.hit_locations, tally.debris_locations) == expected["loc"]
    assert tally.as_of is not None
    assert tally.as_of.tzinfo is UTC
    assert tally.as_of.astimezone(kpszsu.KYIV).strftime("%H:%M") == expected["as_of"]
    assert str(tally.night) == expected["night"]


@pytest.mark.parametrize("post", CORRECTIONS)
def test_a_correction_is_refused_and_never_read_into_figures(post: str) -> None:
    reading = _reading(post)
    assert (reading.status, reading.tally) == ("refused", None)


def test_72080_carries_the_night_phrase_and_is_still_a_correction() -> None:
    """The trap the fixture was kept for: `у ніч на` in mid-sentence."""
    text = (FIXTURES / "72080.txt").read_text(encoding="utf-8")
    assert "у ніч на" in text
    assert kpszsu.classify_message(text) == "correction"


def test_a_source_gap_is_flagged_and_not_repaired() -> None:
    """10.08: a headline of 96 over items of 95. Flagged, never made to add up."""
    reading = _reading("72214")
    assert reading.status == "flagged"
    assert reading.tally is not None
    assert reading.tally.checks == ("headline 96 against items 95",)
    assert not any(item.derived for item in reading.tally.downed)
    assert kpszsu.downed_total(reading.tally) == 96


@pytest.mark.parametrize("post", ["74294", "74748"])
def test_one_unnumbered_item_is_closed_by_their_own_total_and_marked(post: str) -> None:
    tally = _tally(post)
    derived = [item for item in tally.downed if item.derived]
    assert [(item.cls, item.count) for item in derived] == [("anti_ship", 1)]
    assert tally.ok


@pytest.mark.parametrize(("post", "assets", "missiles", "drones"),
                         [("67095", 570, 74, 496), ("69144", 166, 41, 125),
                          ("71026", 220, 35, 185)])
def test_an_inventory_is_read_and_equals_its_items(post: str, assets: int, missiles: int,
                                                    drones: int) -> None:
    tally = _tally(post)
    assert tally.shape == "combined"
    assert tally.launched_total == kpszsu.Inventory(assets, missiles, drones)
    assert kpszsu.launched_sum(tally) == assets


def test_the_combined_shape_is_known_by_its_inventory_not_its_opening_phrase() -> None:
    """01.08 opens with `завдав удару із застосуванням`; v3 stored it as prose
    with an empty launched list and called the night consistent."""
    text = (FIXTURES / "71026.txt").read_text(encoding="utf-8")
    assert "масованого комбінованого" not in text
    assert _tally("71026").shape == "combined"


def test_did_not_reach_is_kept_verbatim_with_the_count_they_gave() -> None:
    assert _tally("71026").not_reached == kpszsu.NotReached(
        "Крім того, три ракети не досягли своїх цілей.", 3)
    not_reached = _tally("72214").not_reached
    assert not_reached is not None
    assert not_reached.count is None
    assert "ворожа ракета цілей не досягла" in not_reached.text


def test_a_count_is_never_zero_and_never_invented() -> None:
    """Decision 9. No launched total from an empty list or from an unknown."""
    full = _tally("71026")
    assert kpszsu.launched_sum(replace(full, launched=())) is None
    assert kpszsu.launched_sum(_tally("74748")) is None
    assert kpszsu.launched_sum(_tally("67183")) == 107
    assert kpszsu.downed_total(_tally("68010")) == 113
    assert kpszsu.downed_total(_tally("66963")) is None
    day = _tally("78115")
    assert kpszsu.downed_total(day) == 310
    assert kpszsu.downed_total(replace(day, downed=())) is None


def test_the_corpus_reads_as_it_was_measured() -> None:
    """98 messages: one summary a night for 91 nights, six day tallies, one
    correction. Three shapes. One night flagged, and it is the source's own
    gap. Every inventory equals its items and no night names nothing launched."""
    rows = _corpus()
    kinds = [kpszsu.classify_message(row["text"]) for row in rows]
    assert (len(rows), kinds.count("night"), kinds.count("day"),
            kinds.count("correction")) == (98, 91, 6, 1)
    tallies = _corpus_tallies()
    nights = [tally for _post, tally in tallies if tally.kind == "night"]
    shapes = [tally.shape for tally in nights]
    assert (shapes.count("prose"), shapes.count("list"), shapes.count("combined")) == (79, 7, 5)
    assert [post for post, tally in tallies if not tally.ok] == ["72214"]
    assert all(tally.launched for tally in nights)
    combined = [tally for tally in nights if tally.shape == "combined"]
    assert [kpszsu.launched_sum(t) for t in combined] == [570, 419, 166, 358, 220]
    assert all(t.launched_total and kpszsu.launched_sum(t) == t.launched_total.assets
               for t in combined)
    dates = sorted(tally.night for tally in nights if tally.night)
    assert len(set(dates)) == 91
    assert (dates[0], dates[-1]) == (date(2026, 6, 24), date(2026, 9, 22))
    assert all(tally.as_of is not None for tally in nights)


def test_the_not_reached_clause_is_never_a_downed_item() -> None:
    """67362 and 75536 close the downed sentence with a missile that did not
    reach its target; reading it as downed flagged two consistent nights."""
    tallies = dict(_corpus_tallies())
    for post in ("67362", "75536"):
        assert tallies[post].ok
        assert tallies[post].not_reached is not None
        assert all(item.count is not None for item in tallies[post].downed)


def test_a_surface_to_air_missile_is_not_read_as_air_launched() -> None:
    tallies = dict(_corpus_tallies())
    assert _pairs(tallies["71936"].launched) == [("ballistic", 6), ("sam", None), ("drone", 151)]


def test_a_numeral_in_any_case_is_a_count() -> None:
    """`однієї ракети Онікс` (71719) is one missile, not an unknown."""
    tallies = dict(_corpus_tallies())
    assert _pairs(tallies["71719"].impacts) == [("drone", 29), ("other", 1)]


def test_as_of_is_kyiv_time_in_summer_and_in_winter() -> None:
    summer = datetime(2026, 9, 22, 5, 1, tzinfo=UTC)
    winter = datetime(2026, 12, 1, 6, 1, tzinfo=UTC)
    assert kpszsu.as_of_instant("станом на 08:00", summer) == summer.replace(minute=0)
    assert kpszsu.as_of_instant("станом на 08.00", winter) == winter.replace(minute=0)
    assert kpszsu.as_of_instant("станом на 25:00", summer) is None
    assert kpszsu.as_of_instant("без часу", summer) is None


def test_the_night_date_takes_the_year_of_the_post_or_the_one_before() -> None:
    new_year = datetime(2027, 1, 1, 5, 0, tzinfo=UTC)
    assert kpszsu.night_date("у ніч на 31 грудня", new_year) == date(2026, 12, 31)
    assert kpszsu.night_date("у ніч на 1 січня", new_year) == date(2027, 1, 1)
    assert kpszsu.night_date("у ніч на 31 лютого", new_year) is None
    assert kpszsu.night_date("у ніч на 3 брумера", new_year) is None


def test_garbage_page_never_raises_and_reads_as_empty() -> None:
    page = kpszsu.read_page("\x00\xff<<<>>> data-post= not a page")
    assert (page.messages, page.unreadable, page.first_id, page.readings) == (0, 0, None, ())


def test_truncated_block_never_raises_and_yields_no_figure() -> None:
    whole = _page_of("79455")
    page = kpszsu.read_page(whole[: len(whole) // 3])
    assert page.messages == 1
    assert all(reading.status != "ok" for reading in page.readings)


def test_oversized_page_never_raises_and_still_finds_the_summary() -> None:
    page = kpszsu.read_page("<div>" + "x" * 3_000_000 + "</div>" + _page_of("79455"))
    assert [reading.message.post_id for reading in page.readings] == [79455]


def test_malformed_timestamp_is_counted_unreadable_not_dropped() -> None:
    raw = _page_of("79455")
    naive = raw.replace('datetime="2026-09-22T05:01', 'datetime="2026-09-22T05:01:00" x="', 1)
    naive = naive.replace("+00:00", "", 1)
    page = kpszsu.read_page(naive)
    assert (page.messages, page.unreadable, page.readings) == (1, 1, ())


def test_hostile_post_id_is_unreadable_and_does_not_raise() -> None:
    page = kpszsu.read_page(_page_of("79455").replace("79455", "9" * 5000, 1))
    assert (page.messages, page.unreadable) == (0, 1)


def test_hostile_numerals_do_not_raise() -> None:
    """`²` passes `isdigit` and fails `int`; 5000 digits hit the conversion limit."""
    text = "⚡️ ЗБИТО/ПОДАВЛЕНО ² ЦІЛЕЙ\nУ ніч на 22 вересня противник атакував " + "9" * 5000
    tally = kpszsu.parse(text, datetime(2026, 9, 22, 5, 0, tzinfo=UTC))
    assert tally is not None
    assert not tally.ok


def test_a_post_that_is_not_a_summary_is_counted_and_not_kept() -> None:
    raw = _page_of("79455")
    other = raw.replace("ЗБИТО/ПОДАВЛЕНО", "ПОВІДОМЛЕННЯ", 1)
    page = kpszsu.read_page(other)
    assert (page.messages, page.readings) == (1, ())


class _Refusing:
    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        raise SourceUnavailable(f"refused {url}")


def test_a_fetch_returns_the_page_and_a_refusal_propagates() -> None:
    page, elapsed = kpszsu.poll_once(StubTransport(_page_of("79455")))
    assert [reading.status for reading in page.readings] == ["ok"]
    assert elapsed >= 0
    with pytest.raises(SourceUnavailable):
        kpszsu.poll_once(_Refusing())


def test_the_page_address_pages_back_by_post_id() -> None:
    assert kpszsu.page_url() == "https://t.me/s/kpszsu"
    assert kpszsu.page_url(79440) == "https://t.me/s/kpszsu?before=79440"


#: Each check, and the one-figure change to a recording that must fire it. A
#: check never observed failing is not evidence (F14); the corpus is clean, so
#: without these the failure branches would never run at all.
CHECKS_FIRE = [
    ("68010", (("ТА 111 ВОРОЖИХ БПЛА", "ТА 112 ВОРОЖИХ БПЛА"),),
     "headline drones 112 against items 111"),
    ("68010", (("ЗБИТО/ПОДАВЛЕНО 2 РАКЕТИ", "ЗБИТО/ПОДАВЛЕНО 3 РАКЕТИ"),),
     "headline missiles 3 against items 2"),
    ("75719", (("- 5 балістичних", "- балістичних"), ("- 5 крилатих", "- крилатих")),
     "2 downed items without a count"),
    ("67095", (("Усього радіотехнічними", "Радіотехнічними"),),
     "massed phrase without an inventory"),
    ("67095", (("Усього радіотехнічними", "Радіотехнічними"),), "no launched items"),
    ("67095", (("570 засобів повітряного нападу – 74 ракети і 496 БпЛА різних типів:",
                "570 засобів повітряного нападу різних типів:"),), "inventory not read"),
    ("67095", (("- 34 крилаті", "- 35 крилаті"),), "inventory 570 against items 571"),
    ("67183", (("105 ударними", "15 ударними"),), "drone: 82 downed against 15 launched"),
    ("67183", (("У ніч на 3 липня", "У ніч на 3 брумера"),), "night date not read"),
    ("71026", (("протиповітряною обороною збито/подавлено 156 цілей",
                "протиповітряною обороною знешкоджено 156 цілей"),), "no downed items"),
]


@pytest.mark.parametrize(("post", "edits", "reason"), CHECKS_FIRE)
def test_every_check_fires_on_a_recording_altered_in_one_figure(
        post: str, edits: tuple[tuple[str, str], ...], reason: str) -> None:
    text = (FIXTURES / f"{post}.txt").read_text(encoding="utf-8")
    for old, new in edits:
        assert text.count(old) == 1
        text = text.replace(old, new)
    tally = kpszsu.parse(text, _reading(post).message.posted_at)
    assert tally is not None
    assert reason in tally.checks


def test_a_counted_not_reached_clause_is_not_downed_either() -> None:
    row = next(row for row in _corpus() if row["id"] == "67362")
    text = row["text"].replace("протирадіолокаційною ракетою Х-31 не досягла",
                               "2 протирадіолокаційні ракети Х-31 не досягли")
    tally = kpszsu.parse(text, datetime.fromisoformat(row["posted_at"]))
    assert tally is not None
    assert tally.ok
    assert _pairs(tally.downed) == [("drone", 112), ("air_launched", 3)]


def test_a_missile_named_without_a_class_is_kept_as_other() -> None:
    text = (FIXTURES / "66963.txt").read_text(encoding="utf-8").replace(
        "збито/подавлено керовану авіаційну ракету Х-59", "збито/подавлено ракету Х-59")
    tally = kpszsu.parse(text, _reading("66963").message.posted_at)
    assert tally is not None
    assert _pairs(tally.downed) == [("other", None), ("drone", 130)]
    assert tally.ok


def test_an_empty_post_is_not_a_summary() -> None:
    assert kpszsu.classify_message("") is None
    assert kpszsu.classify_message("  \n \n") is None
