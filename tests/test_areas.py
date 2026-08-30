"""Sprint 7 regressions: area resolution by the channel's own hashtags.

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
    assert area.border_centre_km is not None


def test_classify_prefers_the_tag_over_the_oblast_table(table: AreaTable) -> None:
    """F23's repair, asserted rather than described.

    The message names an oblast in prose *and* carries a tag for a raion inside
    a different oblast. The tag wins, because the tag is what the channel
    asserts and the prose is incidental.
    """
    text = "Львівська область #Харківський_район Повітряна тривога"
    tagged = classify(text, table)
    assert tagged is not None
    assert tagged[0].startswith("UA")
    # The tag names a Kharkiv-oblast raion; the prose names Lviv oblast. The
    # resolved area must belong to the oblast the tag asserts.
    area = table.by_code(tagged[0])
    assert area is not None and area.oblast == "Харківська", (
        "the tag must decide, or sprint 7 changed nothing"
    )


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
    # Amended at 0.22.0.0 (F90). The second half of this assertion used to read
    # `classify(text) is not None`, checking that the untabled path still
    # produced the oblast guess. That path was the pre-sprint-7 implementation
    # reachable by forgetting an argument, and `probe` forgot it, so the guess
    # this test was protecting the product from was what the product shipped.
    # The fallback is gone; an untabled call now resolves the same way.
    assert classify(text) is None, "no caller may reach the oblast guess"


def test_f63_a_duplicate_tag_in_the_map_is_refused(tmp_path: Path) -> None:
    """F63. Two rows claiming one tag must not resolve by file order.

    ``csv.DictReader`` yields both rows and the dict write makes the later one
    win silently, so a duplicated tag in the versioned map would change what an
    area resolves to based on row order - absorbed, never reported. The map is
    the single artifact area resolution trusts; a contradiction inside it is a
    refusal, not a coin toss.
    """
    from mavo.errors import DuplicateTag

    path = tmp_path / "dupe.csv"
    path.write_text(
        "tag,count,unit,register_name,oblast,katottg_code,status,note\n"
        "Львівський_район,1,P,Львівський,Львівська,UA0001,ok,\n"
        "Львівський_район,1,P,Самбірський,Львівська,UA0002,ok,\n",
        encoding="utf-8",
    )
    with pytest.raises(DuplicateTag):
        AreaTable.from_csv(path)


def test_prose_resolves_an_area_whose_register_name_differs_from_its_tag() -> None:
    """A renamed raion must be findable by the name the register carries.

    ``_by_name`` was built from the hashtag stem alone, so an area whose tag
    keeps a former name and whose ``register_name`` carries the current one was
    reachable by tag and unreachable by prose. Volodymyr-Volynskyi raion became
    Volodymyr in 2021 and the map records both: tag
    ``ВолодимирВолинський_район``, register name ``Володимирський``. It is a
    border raion in Volyn, which is to say one of the areas this project exists
    to watch, and prose naming it resolved to nothing.

    The channel writes its continuation list in prose (T37), and an API that
    publishes only prose makes this the sole path to a name. Either way the
    failure is silent: an area nobody can resolve is an area nobody is told
    about.
    """
    areas = AreaTable.from_csv()
    by_tag = areas.resolve("ВолодимирВолинський_район")
    assert by_tag is not None, "fixture assumes the map still carries this tag"

    found = areas.resolve_prose("Володимирський район")

    assert [ref.code for ref in found] == [by_tag.code]


def test_prose_still_refuses_a_name_two_areas_share(tmp_path: Path) -> None:
    """F59 holds after the register name joins the index.

    Indexing a second string per row is a chance to reintroduce the defect the
    first index was written to avoid: a name reachable from two rows must
    resolve to neither, whether the collision arrives through the tag stem or
    through the register name.
    """
    path = tmp_path / "clash.csv"
    path.write_text(
        "tag,count,unit,register_name,oblast,katottg_code,status,note\n"
        "Перший_район,1,P,Спільний,Львівська,UA0001,ok,\n"
        "Другий_район,1,P,Спільний,Волинська,UA0002,ok,\n",
        encoding="utf-8",
    )
    areas = AreaTable.from_csv(path)

    assert areas.resolve_prose("Спільний район") == ()


def test_prose_tells_an_oblast_from_a_hromada_of_the_same_name() -> None:
    """Zaporizhzhia is two areas with one register name, and prose says which.

    Indexing the register name put ``Запорізька`` on both the oblast and the
    hromada, which F59 would refuse as ambiguous and so lose an oblast that
    resolved before. The unit word sits beside the name in the prose and is
    exactly the distinction the two rows differ by, so it decides between them
    rather than the pair being dropped.
    """
    areas = AreaTable.from_csv()

    oblast = areas.resolve_prose("Запорізька область")
    hromada = areas.resolve_prose("Запорізька громада")

    assert [ref.unit for ref in oblast] == ["O"]
    assert [ref.unit for ref in hromada] == ["H"]
    assert oblast[0].code != hromada[0].code


def test_the_full_register_form_of_a_hromada_resolves_from_prose() -> None:
    """`X територіальна громада` is the form the API publishes (F128).

    A candidate is a run of tokens ending at the unit word, so the filler in
    the middle landed inside every name it preceded and four areas the table
    already holds were unreachable from prose - Nikopol, Marhanets,
    Chervonohryhorivka and the Kharkiv hromada, all of them alerting on the
    day the API became the primary source. The tag path never saw this because
    the channel's hashtag drops the middle word.
    """
    table = AreaTable.from_csv()

    for prose, oblast in (
        ("м. Нікополь та Нікопольська територіальна громада", "Дніпропетровська"),
        ("м. Харків та Харківська територіальна громада", "Харківська"),
        ("Червоногригорівська територіальна громада", "Дніпропетровська"),
    ):
        resolved = table.resolve_prose(prose)
        assert len(resolved) == 1, prose
        assert resolved[0].oblast == oblast


def test_a_name_the_table_does_not_hold_stays_unresolved() -> None:
    """Stepping over the filler must not turn a miss into a guess.

    Volchansk and Luhansk are outside the table by design, and the repair for
    the form must leave them exactly as unresolvable as they were: a name the
    map does not know is a finding about coverage, not a candidate to be
    matched loosely.
    """
    table = AreaTable.from_csv()

    assert table.resolve_prose("Вовчанська територіальна громада") == ()
    assert table.resolve_prose("Луганська область") == ()
