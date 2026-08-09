"""Sprint 7 regressions: area resolution by the channel's own hashtags.

This file is the sprint's regression record, required by `lint_domain`. It is
the same suite as `tests/test_areas.py`, which is the module's own home; the
duplication is deliberate and cheap, and the alternative, a sprint whose
regressions live only under a module name, loses the ability to run one sprint's
claims in isolation.

F23. The shipped table keyed on oblast names and scored 0 of 20 against real
content. `docs/CHANNEL.md` records why: the channel labels 99.34% of messages
with a hashtag carrying the area and unit type explicitly, and emits an oblast
tag in 515 of 69,676 occurrences. A table searching prose for oblast names could
not have scored above zero.

T33. The channel and the register are two independently evolving vocabularies.
A tag the table does not know is a finding, and these tests hold that it stays
one rather than becoming a default or an outage.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mavo.areas import AreaTable, parse_tags
from mavo.sources.telegram import TelegramChannelSource, classify
from mavo.transport import StubTransport

TXT = '<div class="tgme_widget_message_text js-message_text">'


def _page(post_id: int, when: str, text: str) -> str:
    return (
        f'<div class="tgme_widget_message" data-post="air_alert_ua/{post_id}">'
        f"{TXT}{text}</div>"
        f'<a class="tgme_widget_message_date"><time datetime="{when}"></time></a></div>'
    )


@pytest.fixture(scope="module")
def table() -> AreaTable:
    return AreaTable.from_csv()


def test_the_map_loads_and_carries_its_one_ambiguity(table: AreaTable) -> None:
    # 126 of 127 tags resolve; the exception is recorded rather than assigned to
    # whichever candidate the register happened to list first.
    assert len(table) == 126
    assert table.unresolved == frozenset({"Покровська_територіальна_громада"})


def test_tags_are_parsed_in_order_without_duplicates() -> None:
    text = "🔴 #Львівський_район #Яворівський_район #Львівський_район тривога"
    assert parse_tags(text) == ("Львівський_район", "Яворівський_район")


def test_a_tag_resolves_to_a_register_code_and_an_oblast(table: AreaTable) -> None:
    (area,) = table.resolve_all("#Яворівський_район Повітряна тривога")[0]
    assert area.oblast == "Львівська"
    assert area.code.startswith("UA")
    assert area.is_western is True


def test_an_eastern_tag_resolves_and_is_not_western(table: AreaTable) -> None:
    (area,) = table.resolve_all("#Харківський_район Повітряна тривога")[0]
    assert area.is_western is False
    assert table.western("#Харківський_район Повітряна тривога") == ()


def test_an_unknown_tag_is_reported_not_absorbed(table: AreaTable) -> None:
    """T33. A tag nobody has seen is a finding, and it must reach the caller.

    The failure this refuses: a fallback that maps an unrecognised area onto
    something plausible, so the day the channel names a new raion looks exactly
    like every other day.
    """
    resolved, unknown = table.resolve_all("#Вигаданський_район Повітряна тривога")
    assert resolved == ()
    assert unknown == ("Вигаданський_район",)


def test_the_border_distance_is_unknown_rather_than_zero(table: AreaTable) -> None:
    # S8 (T32) supplies it. Until then unknown prints as unknown, and a caller
    # that renders None as 0 km would put a Polish reader on the border.
    (area,) = table.resolve_all("#Луцький_район тривога")[0]
    assert area.border_km is None


def test_classify_prefers_the_tag_over_the_oblast_table(table: AreaTable) -> None:
    """F23's repair, asserted rather than described.

    The message names an oblast in prose *and* carries a tag for a raion inside
    a different oblast. The tag wins, because the tag is what the channel
    asserts and the prose is incidental.
    """
    text = "Львівська область #Харківський_район Повітряна тривога"
    tagged = classify(text, table)
    untagged = classify(text)
    assert tagged is not None and untagged is not None
    assert tagged[0] != untagged[0], "the tag must decide, or sprint 7 changed nothing"
    assert tagged[0].startswith("UA")


def test_an_unknown_tag_does_not_become_an_outage(table: AreaTable) -> None:
    """The never-raise contract extends to the new path.

    A novel or hostile tag is content, and content must never become an
    exception: that conversion is what turns a channel wording change into a
    silent feed.
    """
    page = _page(701, "2026-09-01T21:04:00+00:00", "#Вигаданський_район Повітряна тривога")
    source = TelegramChannelSource(StubTransport(page), areas=table)
    events = source.poll()
    assert events == []
    assert source.report.unknown_tags == ("Вигаданський_район",)


def test_a_western_tag_produces_an_event_with_the_register_code(table: AreaTable) -> None:
    page = _page(702, "2026-09-01T21:04:00+00:00", "🔴 #Яворівський_район Повітряна тривога")
    source = TelegramChannelSource(StubTransport(page), areas=table)
    (event,) = source.poll()
    assert event.area_id.startswith("UA")
    assert source.report.unknown_tags == ()


def test_the_map_file_is_where_the_package_expects_it() -> None:
    # A versioned data file that the package silently stops finding would degrade
    # to the 0-of-20 fallback with no visible change. Assert the path, not the
    # contents, which the tests above cover.
    from mavo.areas import DEFAULT_MAP

    assert Path(DEFAULT_MAP).is_file()


def test_f60_an_unknown_tag_does_not_fall_back_to_the_oblast_table(table: AreaTable) -> None:
    """A tag the map does not know must not be overwritten by a prose guess.

    The message names an oblast in prose and tags a raion the map has never
    seen. Before 0.10.2.0 the tag path returned nothing, the oblast fallback
    fired, and the message resolved to a plausible area drawn from the table
    that scores 0 of 20 on real content. The unknown tag was still reported, but
    the event carried a guess beside it, which is worse than no event: a report
    naming the wrong place is actionable.

    The fallback exists for messages carrying no tag at all, and only for those.
    """
    text = "Львівська область #Вигаданський_район Повітряна тривога"
    assert classify(text, table) is None
    assert classify(text) is not None, "the fallback must still work without tags"
