"""Scripted attacks, one per threat-model row. Catalogue in CATALOGUE.md.

These are not unit tests of the modules they touch. Each one plays an adversary
and asserts the product's observable response, so that a refactor which keeps
the unit tests green but loses a control still fails here.
"""

from __future__ import annotations

import random
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.baserate import Contingency, assess_rule, gate
from mavo.evaluate import run_policy
from mavo.policy import Regime, policy_of
from mavo.rules import CANDIDATE_RULES, conjunction, drone_conjunction
from mavo.schema import AlertState, ThreatEvent, ThreatKind, is_clear
from mavo.sources.fixture import FixtureSource, build_night, generate_history
from mavo.store import EventStore

T0 = datetime(2026, 9, 1, 21, 0, 0, tzinfo=UTC)
MISSILE = (Regime.MISSILE, "CONJ-missile", conjunction)
DRONE = (Regime.DRONE, "CONJ-drone", drone_conjunction)


def test_a1_broad_simultaneous_activation_raises_nothing() -> None:
    """MT1. A source claiming the whole country is alight must produce no alarm."""
    night = build_night(T0, "poisoned-feed", random.Random(1))
    fired = {name: rule(night) for name, rule in CANDIDATE_RULES.items()}
    assert set(fired.values()) == {None}, f"suppression walked through: {fired}"


def test_a2_a_silent_feed_is_not_an_all_clear() -> None:
    """MT2. Degradation must not read as safety, in either direction."""
    night = build_night(T0, "degraded-feed", random.Random(1))
    assert conjunction(night) is None
    assert is_clear(AlertState.UNKNOWN) is False


def test_a3_one_fabricated_alert_cannot_raise_an_alarm() -> None:
    """MT3. A single area with no vector behind it is not an inbound raid."""
    assert conjunction(build_night(T0, "border-only", random.Random(1))) is None


def test_a4_perfect_recall_does_not_buy_past_the_lift_floor() -> None:
    """MT4. A rule that fires on nearly everything cannot pass by never missing.

    F38, in its original form: the earlier table failed on association as well
    as on the gated condition, and the assertion looked for a substring the
    *passing* reason also contained, so both halves were satisfiable with the
    control disabled. The table below clears recall and association, leaving the
    lift floor as the only condition able to fail, and the assertion names it.

    Rewritten at 0.8.0.0 (D-014). The gated condition used to be the alarm rate;
    it is now the lower bound on lift. The attack is the same attack, because
    what it always tested was whether a rule can buy an alarm by firing broadly
    enough to be right eventually.
    """
    # A calendar: 12 events over 1460 windows, firing on 57% of them and
    # catching all of them. Recall is perfect, the association is significant,
    # and the firing still tells the recipient nothing they did not have from
    # the date. The old table used here fired often *and* carried information,
    # so under the lift floor it passes, correctly: firing often is no longer
    # the offence. Firing uninformatively is.
    assessment = assess_rule(
        "calendar", Contingency(a=12, b=820, c=0, d=628), observation_weeks=208
    )
    verdict = gate(assessment)
    assert assessment.recall == 1.0
    assert assessment.p_value < 0.05, "the table must clear association, or this proves nothing"
    assert verdict.passes is False
    assert any("lift lower bound" in reason and "below floor" in reason
               for reason in verdict.reasons)


def test_a6_a_partial_policy_cannot_read_as_complete() -> None:
    """MT6. An unserved crossing kind is counted and printed, never absorbed."""
    run = run_policy(policy_of([MISSILE]), generate_history(weeks=208))
    assert run.combined.assessment.recall == 1.0
    assert run.has_coverage_gap is True
    assert "COVERAGE GAP" in run.summary()


def test_a7_hostile_payloads_do_not_become_an_outage() -> None:
    """MT7. A parser that raises turns a hostile string into an outage.

    Fixture path only. No live adapter exists, and the catalogue says so rather
    than implying coverage this does not have.
    """
    source = FixtureSource([])
    assert list(source.poll()) == []

    for scenario in ("quiet", "poisoned-feed", "degraded-feed"):
        night = build_night(T0, scenario, random.Random(3))
        assert FixtureSource([night]).poll() is not None


def test_a8_replaying_a_feed_does_not_grow_the_log(tmp_path: Path) -> None:
    """MT8. Re-polling an unchanged transition must cost nothing."""
    store = EventStore(tmp_path / "attack.sqlite")
    event = ThreatEvent(
        area_id="lviv",
        state=AlertState.ACTIVE,
        ts_source=T0,
        ts_ingest=T0 + timedelta(seconds=30),
        source_id="attacker",
        kind=ThreatKind.MISSILE,
    )
    # An attacker replaying the same transition with a fresh ingest time every
    # 30 seconds for an hour must not be able to grow the log.
    for minute in range(120):
        store.append([replace(event, ts_ingest=T0 + timedelta(minutes=minute))])
    assert store.count() == 1


def test_a9_hostile_bodies_to_the_live_adapter_do_not_raise() -> None:
    """MT7. The Telegram adapter absorbs content failures and reports them."""
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import StubTransport

    # F39. These were single-quoted, and the page serves double quotes, so the
    # message regex matched nothing and every hostile body was absorbed without
    # the parser ever seeing it. The attack passed by not arriving. The same
    # rule holds under the block parser (F50): a message must carry the
    # data-post anchor the live page always carries, or it never becomes a
    # message at all - so every hostile body below except the first two is
    # anchored, and the reached-counter still guards against a silent miss.
    txt = '<div class="tgme_widget_message_text js-message_text">'

    def anchored(inner: str, post: int) -> str:
        return f'<div class="tgme_widget_message" data-post="air_alert_ua/{post}">{inner}</div>'

    hostile = [
        "",
        "not html",
        anchored(f'<time datetime="nonsense"></time>{txt}Львів тривога</div>', 901),
        anchored(f"{txt}{'А' * 80_000}</div>", 902),
        anchored(f"{txt}\x00\x01\x02</div>", 903),
        anchored(
            f'{txt}wording nobody anticipated</div>'
            f'<time datetime="2026-09-01T21:00:00+00:00"></time>',
            904,
        ),
    ]
    reached = 0
    for body in hostile:
        source = TelegramChannelSource(StubTransport(body))
        assert source.poll() is not None
        assert source.report.parsed <= source.report.messages
        reached += source.report.messages
    assert reached > 0, "no hostile body reached the parser; this attack proves nothing"


def test_a10_an_unreachable_source_is_not_a_quiet_one() -> None:
    """MT11. An outage must not be indistinguishable from an empty sky."""
    from mavo.errors import SourceUnavailable
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import FailingTransport

    with pytest.raises(SourceUnavailable):
        TelegramChannelSource(FailingTransport()).poll()


def test_a11_a_skipped_window_cannot_pass_as_a_quiet_channel() -> None:
    """MT12. A mass alert overflows the page; the skip must be observable.

    Two failure shapes in one attack. Messages that pass between polls are
    counted, and a page that carries no post ids reports unknown rather than
    zero, because losing the observable must not look like observing calm.
    """
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import StubTransport

    def page(ids: list[int]) -> str:
        txt = '<div class="tgme_widget_message_text js-message_text">'
        return "".join(
            f'<div class="tgme_widget_message" data-post="air_alert_ua/{post}">'
            f'<time datetime="2026-09-01T21:00:00+00:00"></time>'
            f"{txt}Львівська область<br/>Повітряна тривога</div></div>"
            for post in ids
        )

    source = TelegramChannelSource(StubTransport(page([500, 501])))
    source.poll()
    source.transport = StubTransport(page([560, 561]))
    source.poll()
    assert source.report.skipped == 58, "a skipped window passed as continuity"
    assert source.report.gap_is_known is True

    # F40. The first version of this attack asserted unknown only for a page
    # with no ids, which `_window` answers before reaching the code that decides
    # unknown-versus-zero. The first-poll case is the one that governs it.
    fresh = TelegramChannelSource(StubTransport(page([700, 701])))
    fresh.poll()
    assert fresh.report.skipped is None, "a first poll invented a baseline it does not have"

    blind = TelegramChannelSource(StubTransport("<html>no post ids</html>"))
    blind.poll()
    assert blind.report.skipped is None, "an unmeasurable gap reported as zero"


def test_a12_the_footer_time_cannot_shift_onto_a_neighbour() -> None:
    """MT13. Timestamps must pair within a message block, never across one.

    The live page carries each message's time in its footer, after the text. A
    page-wide scan that requires time-then-text pairs message N's time with
    message N+1's text: every event one message late, the first text dropped,
    the last time orphaned (F50). In the missile regime the whole warning
    budget is about six minutes, so a one-message shift in ``ts_source`` is not
    cosmetic; it is the lead-time measurement quietly poisoned. The assertion
    is exact equality on both pairs, so a shift in either direction goes red.
    """
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import StubTransport

    txt = '<div class="tgme_widget_message_text js-message_text">'
    page = (
        '<div class="tgme_widget_message" data-post="air_alert_ua/601">'
        f"{txt}🔴 Повітряна тривога в Львівський район #Львівський_район</div>"
        '<time datetime="2026-09-01T21:04:00+00:00"></time></div>'
        '<div class="tgme_widget_message" data-post="air_alert_ua/602">'
        f"{txt}🔴 Повітряна тривога в Луцький район #Луцький_район</div>"
        '<time datetime="2026-09-01T21:11:00+00:00"></time></div>'
    )
    source = TelegramChannelSource(StubTransport(page))
    stamped = {event.area_id: event.ts_source.isoformat() for event in source.poll()}
    # Codes rather than the old `lviv`/`volyn` slugs: this attack's page was
    # written in oblast prose, a shape the channel does not emit, so it was
    # exercising the parser against the fixture's own assumption (F90).
    assert stamped == {
        "UA46060000000042587": "2026-09-01T21:04:00+00:00",
        "UA07080000000034745": "2026-09-01T21:11:00+00:00",
    }, "a footer timestamp crossed a message boundary"


def test_a13_an_unknown_tag_is_not_replaced_by_a_prose_guess() -> None:
    """MT14. The area the channel named, but the map cannot read, stays unread.

    F60. The sprint 7 fallback fired whenever the tag path produced nothing,
    which is wider than its justification. A message tagging an area the map
    does not know, and mentioning an oblast in prose, resolved to that oblast
    from the table that scores 0 of 20 on real content. The unknown tag was
    still reported, so the failure looked like an accounting quirk rather than
    what it was: an event carrying a guess about where the danger is.

    The adversarial reading is the one that makes it an attack rather than a
    bug. The channel's vocabulary drifts on its own schedule, and an attacker
    who can get one unrecognised tag into a message with an oblast name in it
    obtains a warning that names the wrong place. A report naming the wrong
    place is worse than no report, because it is actionable.
    """
    from mavo.areas import AreaTable
    from mavo.sources.telegram import classify

    table = AreaTable.from_csv()
    misleading = "Львівська область #Вигаданський_район Повітряна тривога"
    assert classify(misleading, table) is None, "a prose guess replaced an unknown tag"
    # F90 widened this. The oblast fallback the attack targeted was not merely
    # reachable when a caller opted out of the table: it was what `probe` ran,
    # so the live path was the attack's own scenario. The fallback is removed
    # rather than guarded, and no call shape reaches a prose guess.
    assert classify(misleading) is None, "no call shape may reach the oblast guess"


def test_a14_a_still_dangerous_area_is_not_silently_dropped() -> None:
    """MT16. An all-clear must not speak for the areas it says are still alight.

    The channel writes the cleared area as a tag and the areas where the alert
    continues as prose after a marker. Reading only the tags produced an
    all-clear and nothing else, which is the system going quiet about a place
    its own source had just called dangerous. The attack is the message itself,
    verbatim in shape from the corpus.
    """
    from mavo.areas import AreaTable
    from mavo.schema import AlertState, AreaRole
    from mavo.sources.telegram import TelegramChannelSource
    from mavo.transport import StubTransport

    text = (
        "🟢 15:53 Відбій тривоги в Куп’янський район.\n"
        "Зверніть увагу, тривога ще триває у:\n- Пологівський район\n#Купянський_район"
    )
    body = (
        '<div class="tgme_widget_message" data-post="air_alert_ua/7001">'
        f'<div class="tgme_widget_message_text js-message_text">{text}</div>'
        '<a class="tgme_widget_message_date">'
        '<time datetime="2026-09-01T21:00:00+00:00"></time></a></div>'
    )
    events = TelegramChannelSource(StubTransport(body), areas=AreaTable.from_csv()).poll()

    continuing = [event for event in events if event.role is AreaRole.CONTINUATION]
    assert continuing, "the still-running area left no trace; the all-clear spoke alone"
    assert all(event.state is AlertState.ACTIVE for event in continuing)
    cleared = [event for event in events if event.role is AreaRole.SUBJECT]
    assert [event.state for event in cleared] == [AlertState.CLEAR]
    assert continuing[0].area_id != cleared[0].area_id


def test_a15_a_night_read_as_empty_is_not_a_total_of_zero() -> None:
    """MT17. A night whose launched list read empty must never total 0.

    `all(...)` is true of nothing, so "sum when every item carries a count" is
    satisfied by a night the reader failed to read, and the total it yields is
    a zero the Air Force never stated. Reader v3 stored 01.08 with an empty
    launched list and reported the night consistent. The attack empties a real
    night's launched list and reads what the product would keep and publish.
    """
    from mavo import strike
    from mavo.sources import kpszsu

    recording = Path(__file__).parent.parent / "fixtures" / "kpszsu" / "79455.html"
    body = 'data-post="kpszsu/79455"' + recording.read_text(encoding="utf-8")
    [reading] = kpszsu.read_page(body).readings
    assert reading.tally is not None
    emptied = replace(reading.tally, launched=())
    assert kpszsu.launched_sum(emptied) is None, "an empty launched list was totalled"
    assert strike.tally_json(emptied)["launched_sum"] is None, "the stored reading carries a total"



def _listed_level_picture(listed: list[tuple[str, float, float]],
                          rows: list[tuple[str, float]], at: float,
                          elapsed_s: float = 0.0) -> dict[str, object]:
    """The contract's area entry for one area at minute `at` of a raid.

    `listed` is `(word, stamped at, newest read that listed it)` and `rows` the
    alert rows `(state, minute)`, all in minutes from 10:00; the API is read
    every two minutes and each read has its page `elapsed_s` after asking.
    Built through the product's own fold and serialiser.
    """
    from mavo.levels import LevelIndex, Listed
    from mavo.report import compose, to_contract
    from mavo.schema import AreaRole, Provenance, ThreatEvent

    t0 = datetime(2026, 9, 20, 10, 0, tzinfo=UTC)
    area = "UA68060000000040570"

    def minute(value: float) -> datetime:
        return t0 + timedelta(minutes=value)

    events = [ThreatEvent(area_id=area, state=AlertState(state), ts_source=minute(m),
                          ts_ingest=minute(m), source_id="ukrainealarm",
                          kind=ThreatKind.UNKNOWN, provenance=Provenance.REPORTED,
                          raw_fields={}, oblast="", role=AreaRole.SUBJECT)
              for state, m in rows]
    levels = LevelIndex.build(
        [Listed(area, ThreatKind.UNKNOWN, word, minute(stamped), minute(last))
         for word, stamped, last in listed],
        [(minute(m), elapsed_s) for m in range(-60, 181, 2)],
        first_listing=minute(-60), recorded_since=minute(-60))
    report = compose([e for e in events if e.ts_source <= minute(at)], as_of=minute(at),
                     history_days=(7,), levels=levels)
    [published] = to_contract(report)["areas"]  # type: ignore[misc]
    return published  # type: ignore[no-any-return]


def test_a16_a_new_alarm_never_wears_the_colour_its_predecessor_ended_on() -> None:
    """MT18. A level stands only while the source still lists it.

    The level stream keys a declaration on its word and its moment, so the
    predecessor's Red is still the newest row on the key after it ended: a
    join on the key paints the next alarm with it. The attack plays a red
    alarm, its all-clear and a second alarm the API has not levelled, through
    the product's own fold, and reads the contract a reader is shown.
    """
    published = _listed_level_picture([("Red", 20, 58)],
                                      [("active", 0), ("clear", 60), ("active", 90)], 95)
    assert published["alert"] == "active"
    assert published["level"] is None, "the new alarm wears its predecessor's colour"


def test_a17_a_level_the_source_stopped_listing_leaves_a_running_alarm() -> None:
    """MT18. The second road to the same wrong colour, with no all-clear at all.

    Two alerts of one kind on one area fold into one row (`AIR` and
    `URBAN_FIGHTS` are both UNKNOWN): the chronic one carries a Red, the air
    alert a Yellow the API lists as current while it runs. When the air alert
    ends the alarm goes on and the API lists the Red again. A rule that keeps
    the newest declaration since the alarm began shows the Yellow for ever.
    """
    published = _listed_level_picture([("Red", -60, 180), ("Yellow", 0, 40)],
                                      [("active", -60)], 50)
    assert published["alert"] == "active"
    level = published["level"]
    assert isinstance(level, dict) and level["word"] == "Red", (
        "a level the source stopped listing stayed on the map")


def test_a18_an_alarm_keeps_its_level_until_the_alarm_itself_ends() -> None:
    """MT18. The other direction: a level withheld from the alarm it belongs to.

    The read that stops listing a Red because its alarm ended asks at 10:32
    and has its page 1.5 s later; the all-clear it derives is stamped when the
    page arrived, 0.8 s after asking. A read that speaks from the moment it
    asked takes the Red away before the alarm ends, and a reader shown that
    moment is told the source lists no level for a red alarm. Every levelled
    alarm ends this way, so the week would carry the sliver at each end.
    """
    second = 1 / 60
    published = _listed_level_picture([("Red", 0, 30)],
                                      [("active", 0), ("clear", 32 + 0.8 * second)],
                                      32 + 0.5 * second, elapsed_s=1.5)
    assert published["alert"] == "active"
    level = published["level"]
    assert isinstance(level, dict) and level["word"] == "Red", (
        "the level left before the alarm it belongs to")


def _rso_feed(by_url: dict[str, str]) -> object:
    """A transport answering each RSO address with its own body, an empty list otherwise."""
    empty = '<newses><pagination_info totalItems="0" itemsPerPage="20"/></newses>'

    class Feed:
        def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
            return by_url.get(url, empty)

    return Feed()


def test_a19_a_category_the_walk_does_not_know_is_not_a_quiet_country(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MT19. The two days of 2026-10-21, with one category more than the walk knows.

    The publisher lists an RCB air alert in a category no address of the walk
    returns, and every address answers. A walk that records a read for each
    vouches for an empty `ogolne` and an empty air list, and the page says
    RCB raised nothing. The attack runs the product's own command and reads
    the block the page is given.
    """
    from mavo import poland
    from mavo.cli import main
    from mavo.sources import rso

    alert = ('<newses><pagination_info totalItems="1" itemsPerPage="20"/><news>'
             '<id>23441700</id><title>ALERT RCB</title><shortcut>UWAGA! Rosyjski atak '
             'powietrzny na terenie Ukrainy.</shortcut><valid_to>2099-01-01 00:00:00</valid_to>'
             '<provinces><province slug="lubelskie">Lubelskie</province></provinces>'
             '</news></newses>')
    monkeypatch.setattr("mavo.cli.UrllibTransport", lambda: _rso_feed({rso.ALL_SCOPE_URL: alert}))
    path = tmp_path / "events"
    main(["rso", "--store", str(path)])
    warnings, _cleared = poland.warnings_blocks(EventStore(path), datetime.now(UTC))
    assert warnings.published
    assert warnings.value is None, "a feed with an alert in it read as a quiet country"


def test_a20_a_scope_with_an_address_nobody_read_is_not_read_as_quiet(
        tmp_path: Path) -> None:
    """MT19. The same failure one layer down, in the composer.

    From `AIR_URL_SINCE` the communiques that may paint are in two addresses.
    `ogolne` read fresh and empty with the air category never read is half a
    list, and half a list of nothing renders as a whole one.
    """
    from mavo import poland
    from mavo.sources import rso

    store = EventStore(tmp_path / "events")
    moment = poland.AIR_URL_SINCE + timedelta(days=2)
    for minutes in (25, 15, 5):
        at = moment - timedelta(minutes=minutes)
        store.record_snapshot(rso.FEED, poland.WARNINGS_URL, at, [])
        store.record_read(rso.FEED, poland.WARNINGS_URL, at, 0, 0)
    warnings, _cleared = poland.warnings_blocks(store, moment)
    assert warnings.published
    assert warnings.value is None, "half a list of nothing read as a whole one"


# -- 0.63.0.0: the 2026-10-25 review (F204, D-066, D-067) --------------------


def _api_regions(names: list[str]) -> str:
    import json

    began = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    return json.dumps([
        {"regionId": str(1000 + i), "regionName": name,
         "activeAlerts": [{"regionId": str(1000 + i), "regionType": "District",
                           "type": "AIR", "lastUpdate": began}]}
        for i, name in enumerate(names)
    ])


def test_a21_an_alarm_that_ended_inside_a_gap_does_not_stand_for_ever(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MT20. Two alarms stand, the host misses six minutes, one ends inside them.

    The first read after the gap no longer lists it. Before 0.63.0.0 nothing
    ever closed it: the stale snapshot withheld the diff and the next one was
    taken against the shorter list. The attack runs the product's command
    twice and reads the store's fold.
    """
    import contextlib
    import io
    import json

    from mavo import cli
    from mavo.sources.ukrainealarm_source import UkrainealarmSource

    body = {"text": _api_regions(["Львівський район", "Луцький район"])}

    class Feed:
        def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
            return body["text"]

    class Injected(UkrainealarmSource):
        def __init__(self, key: str, **kw: object) -> None:
            kw["transport"] = Feed()
            super().__init__(key, **kw)  # type: ignore[arg-type]

    monkeypatch.setattr(cli, "UkrainealarmSource", Injected)
    monkeypatch.setattr(cli, "read_key", lambda path=None: "key")
    store, snapshot = tmp_path / "events", tmp_path / "snapshot.json"
    args = ["collect-api", "--store", str(store), "--snapshot", str(snapshot)]
    with contextlib.redirect_stdout(io.StringIO()):
        cli.main(args)
        saved = json.loads(snapshot.read_text())
        saved["saved_at"] = (datetime.fromisoformat(saved["saved_at"])
                             - timedelta(seconds=400)).isoformat()
        snapshot.write_text(json.dumps(saved))
        body["text"] = _api_regions(["Львівський район"])
        cli.main(args)
        cli.main(args)
    standing = [key for key, event in EventStore(store).newest_by_area_kind().items()
                if event.state is AlertState.ACTIVE]
    assert [area for area, _kind in standing] == ["UA46060000000042587"], (
        f"an alarm that ended inside the gap still stands: {standing}")


def test_a22_a_body_that_is_not_the_list_is_not_a_quiet_sky() -> None:
    """MT11. An error envelope that parses as JSON, sent while an alarm stands.

    The API's quiet sky is `[]` and nothing else. `{"message": ...}` used to
    read as no alerts and clear every open alarm under a fresh snapshot.
    """
    from mavo.errors import SourceUnavailable
    from mavo.sources.ukrainealarm_source import UkrainealarmSource

    body = {"text": _api_regions(["Львівський район"])}

    class Feed:
        def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
            return body["text"]

    source = UkrainealarmSource("key", transport=Feed())
    source.poll()
    body["text"] = '{"message": "Unauthorized"}'
    with pytest.raises(SourceUnavailable):
        cleared = source.poll()
        pytest.fail(f"an error envelope read as a quiet sky: {cleared}")


def test_a23_a_feed_renamed_one_tag_is_not_a_quiet_country(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MT19. The publisher renames its record element and every address answers.

    `<item>` where `<news>` stood parsed as no record at all, in every
    category and in the canary, so the canary vouched for an empty walk.
    """
    from mavo import poland
    from mavo.cli import main
    from mavo.sources import rso

    renamed = ('<newses><pagination_info totalItems="1" itemsPerPage="20"/><item>'
               '<id>23441700</id><title>ALERT RCB</title><shortcut>UWAGA! Rosyjski atak '
               'powietrzny na terenie Ukrainy.</shortcut><valid_to>2099-01-01 00:00:00'
               '</valid_to><provinces><province slug="lubelskie">Lubelskie</province>'
               '</provinces></item></newses>')
    pages = {rso.ALL_SCOPE_URL: renamed}
    pages.update({rso.page_url(category, 0): renamed for category in rso.CATEGORIES})
    monkeypatch.setattr("mavo.cli.UrllibTransport", lambda: _rso_feed(pages))
    path = tmp_path / "events"
    assert main(["rso", "--store", str(path)]) == 3
    warnings, _cleared = poland.warnings_blocks(EventStore(path), datetime.now(UTC))
    assert warnings.published
    assert warnings.value is None, "a renamed feed read as a quiet country"


def test_a24_a_canary_blind_to_the_walk_does_not_vouch_for_it(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MT19. The partial scope answers empty while `ogolne` holds a communique.

    A scope that sees nothing vouched for everything by comparing nothing:
    the canary must have seen what the walk read in the categories it covers.
    """
    from mavo.cli import main
    from mavo.sources import rso

    one = ('<newses><pagination_info totalItems="1" itemsPerPage="20"/><news>'
           '<id>23441700</id><title>komunikat</title></news></newses>')
    pages = {rso.ALL_SCOPE_URL: "<newses></newses>", rso.page_url("ogolne", 0): one}
    monkeypatch.setattr("mavo.cli.UrllibTransport", lambda: _rso_feed(pages))
    assert main(["rso", "--store", str(tmp_path / "events")]) == 3


def test_a25_a_reassurance_inside_an_alert_is_not_its_all_clear() -> None:
    """MT2. The alert itself says something ended, and the ambiguity read as safety.

    "Zakończono ewakuację szkół" inside an air alert was the bare verb
    `zakończono`, and the communique read as an all-clear.
    """
    from mavo.poland import classify

    verdict = classify("Alert RCB", "Atak powietrzny. Zakończono ewakuację szkół.")
    assert verdict is not None and verdict[0] == "threat", f"read as {verdict}"


def test_a26_a_blind_cycle_does_not_publish_a_counted_zero(tmp_path: Path) -> None:
    """MT2. The store cannot be read and the day's count goes out as 0 transitions.

    Unknown is three nulls, the one shape the site reads as "not counted".
    """
    import json

    from mavo.report import compose, write_contract

    payload = json.loads(write_contract(compose([], as_of=T0), tmp_path / "s.json").read_text())
    assert payload["state"] == "blind"
    assert payload["counts_24h"] == {"west": None, "rest": None, "total": None}


def _analysis_inputs(end: datetime, *, api_gap: tuple[datetime, datetime] | None = None,
                     unread: list[dict[str, str]] | None = None) -> object:
    from mavo.analysis import BandRaion, Inputs, window_start

    start = window_start(end)
    band = [BandRaion("UA46060000000042587", "Lvivskyi", "lviv", "Львівська", 16.0, 97.0)]
    spans = []
    moment, on = start, True
    while moment < end:
        step = min(end, moment + timedelta(hours=2))
        if on:
            spans.append(("UA80000000000000000", "active", moment, step))
        on, moment = not on, step
    reads = []
    moment = start
    while moment <= end:
        reads.append(moment)
        moment += timedelta(minutes=10)
    return Inputs(
        start=start, end=end, places={}, spans=spans, band=band,
        api_since=start, channel_since=None,
        api_gaps=[api_gap] if api_gap else [], channel_gaps=[],
        rcb={"recorded_since": start.isoformat(), "unread": unread or [], "voivodeships": []},
        rso_reads=tuple(reads), rso_silence_s=1800.0,
    )


def test_a27_an_unobserved_week_is_not_a_quiet_week() -> None:
    """MT6. The pipe is down for a whole week and the analysis compares it.

    A minute the record did not see counts in neither numerator nor
    denominator (D-064), so a week without a record is unusable rather than a
    week without alarms.
    """
    from mavo.analysis import analyse

    end = datetime(2026, 10, 20, 19, 0, tzinfo=UTC)
    monday = datetime(2026, 10, 12, 0, 0, tzinfo=UTC) - timedelta(hours=2)
    out = analyse(_analysis_inputs(end, api_gap=(monday, monday + timedelta(days=7))))
    week = out["weeks"][-2]  # type: ignore[index]
    assert week["usable"] is False and week["values"]["episodes"] is None, week


def test_a28_an_unread_rso_list_is_not_a_week_without_alerts() -> None:
    """MT2. The RSO list was not read for a week, and the week reads as no alerts.

    The register's unread stretch is a hole in RCB's denominator, never a zero.
    """
    from mavo.analysis import analyse

    end = datetime(2026, 10, 20, 19, 0, tzinfo=UTC)
    monday = datetime(2026, 10, 12, 0, 0, tzinfo=UTC) - timedelta(hours=2)
    unread = [{"from": monday.isoformat(), "to": (monday + timedelta(days=7)).isoformat()}]
    out = analyse(_analysis_inputs(end, unread=unread))
    week = out["weeks"][-2]  # type: ignore[index]
    assert week["values"]["rcb"] is None, f"an unread week counted {week['values']['rcb']}"


def test_a29_a_rejected_walk_is_never_painted_on_the_slider(tmp_path: Path) -> None:
    """MT19. A walk the canary rejected wrote an alert's list and no read.

    The live map takes each address's list at its own read; the slider must
    too, or the week repaints what the canary refused.
    """
    from mavo import poland, timeline
    from mavo.sources import rso

    store = EventStore(tmp_path / "events")
    moment = poland.AIR_URL_SINCE + timedelta(days=2)
    for url in poland.WARNINGS_URLS:
        store.record_snapshot(rso.FEED, url, moment - timedelta(minutes=10), [])
        store.record_read(rso.FEED, url, moment - timedelta(minutes=10), 0, 0)
    store.record_snapshot(rso.FEED, poland.WARNINGS_URL, moment - timedelta(minutes=5),
                          ["rejected"])
    record = timeline.warnings_record(store, moment - timedelta(hours=1), moment)
    assert record.members_at(moment) == [], "the slider painted a list the canary refused"
