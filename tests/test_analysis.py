"""Weeks set against weeks: `analysis.json` (D-064).

Most of these hold `mavo.analysis.analyse` to windows written by hand, small
enough that every expected figure is worked out in the test itself rather than
read back from the code under test. Two hold the seam: the store reading over
the week the production store recorded, and the command over the same store,
because an instrument tested only through its module is untested as a command
(F157).

The window of the hand-written cases is the thirteen Warsaw weeks ending on
Sunday 2026-10-18 at noon: it opens at 00:00 on Monday 2026-07-20, and the
switch from the channel to the API sits where D-040 put it, on 2026-08-30.
"""

from __future__ import annotations

import hashlib
import json
import lzma
import math
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from mavo import analysis
from mavo.analysis import Inputs, analyse, band_raions
from mavo.areas import AreaTable
from mavo.cli import main
from mavo.liveness import PRODUCTION_FEEDS
from mavo.report import write_analysis
from mavo.store import EventStore
from tests.test_timeline_recorded_week import DIGEST, FIXTURE

TABLE = AreaTable.from_csv()
BAND = band_raions(TABLE)
#: The nearest border raion (Sambir, 0 km), and the nearest inner one (Uzhhorod, 7.2 km).
BORDER = next(r for r in BAND if r.border)
INNER = next(r for r in BAND if not r.border)
#: An area of the 150-225 km ring, for the leads.
RING = "UA-RING-200"

END = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)
START = analysis.window_start(END)
SWITCH = datetime(2026, 8, 30, 15, 9, tzinfo=UTC)
#: Monday 00:00 in Warsaw of the last week, the current one.
LAST_MONDAY = datetime(2026, 10, 11, 22, 0, tzinfo=UTC)


def at(day: str, hhmm: str = "12:00") -> datetime:
    """A Warsaw wall-clock moment, summer time, as an instant."""
    local = datetime.fromisoformat(f"{day}T{hhmm}:00+02:00")
    return local.astimezone(UTC)


def places() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {
        raion.code: {"katottg": raion.code, "border_km_lower": raion.km_lower,
                     "border_km_upper": raion.km_upper} for raion in BAND}
    out[RING] = {"katottg": RING, "border_km_lower": 200.0, "border_km_upper": 260.0}
    return out


def busy(first: datetime, last: datetime, every: timedelta = timedelta(minutes=50)
         ) -> list[tuple[str, str, datetime, datetime | None]]:
    """A quiet country does not exist: some far area changes every `every`.

    Without changes anywhere the record would read as a silent source, which
    is the rule under test in one case and noise in every other.
    """
    spans = []
    moment = first
    while moment < last:
        spans.append(("UA-FAR", "active", moment, moment + timedelta(minutes=10)))
        moment += every
    return spans


def make(alarms: Sequence[tuple[str, str, datetime, datetime | None]], *,
         record_from: datetime | None = None, api_gaps: Sequence[tuple[datetime, datetime]] = (),
         rcb: dict[str, Any] | None = None, reads: Sequence[datetime] = (),
         noise_until: datetime | None = None) -> Inputs:
    first = record_from or at("2026-08-11", "00:00")
    spans = busy(first, noise_until or END) + list(alarms)
    where = places()
    where["UA-FAR"] = {"katottg": "UA-FAR", "border_km_lower": 900.0, "border_km_upper": 950.0}
    return Inputs(
        start=START, end=END, places=where, spans=spans, band=BAND,
        api_since=SWITCH, channel_since=at("2026-08-29", "16:39"),
        api_gaps=list(api_gaps), channel_gaps=[], rcb=rcb, rso_reads=list(reads),
        rso_silence_s=1800.0,
    )


def week_of(payload: dict[str, Any], monday: str) -> dict[str, Any]:
    return next(w for w in payload["weeks"] if w["first_day"] == monday)


def comparison(payload: dict[str, Any], n: int, m: int) -> dict[str, Any]:
    return next(c for c in payload["comparisons"] if c["n"] == n and c["m"] == m)


# ---- what counts as observed


def test_the_window_is_thirteen_warsaw_weeks_starting_on_a_monday() -> None:
    assert datetime(2026, 7, 19, 22, 0, tzinfo=UTC) == START
    payload = analyse(make([]))
    assert [w["first_day"] for w in payload["weeks"]][:2] == ["2026-07-20", "2026-07-27"]
    assert len(payload["weeks"]) == 13
    assert payload["weeks"][-1]["partial"] is True
    assert payload["weeks"][-2]["partial"] is False


def test_an_unseen_minute_is_in_neither_numerator_nor_denominator() -> None:
    """Two weeks with the same alarm each day; one of them loses two days to a gap.

    Two hours of alarm a day, one onset a day. The week with the gap keeps
    exactly that rate over the five days it saw: a gap is not a quiet stretch.
    """
    alarms = []
    for day in range(14):
        moment = at("2026-09-21", "08:00") + timedelta(days=day)
        alarms.append((INNER.code, "active", moment, moment + timedelta(hours=2)))
    gap = (at("2026-09-30", "00:00"), at("2026-10-02", "00:00"))
    payload = analyse(make(alarms, api_gaps=[gap]))
    whole, cut = week_of(payload, "2026-09-21"), week_of(payload, "2026-09-28")
    assert whole["seen_min"] == 7 * 1440
    assert cut["seen_min"] == 5 * 1440
    assert whole["values"]["episodes"] == cut["values"]["episodes"] == 1.0
    assert whole["values"]["band_h"] == cut["values"]["band_h"] == 2.0
    assert whole["values"]["duration"] == 120.0


def test_a_week_seen_less_than_half_is_not_compared() -> None:
    gap = (at("2026-09-28", "00:00"), at("2026-10-02", "06:00"))
    payload = analyse(make([], api_gaps=[gap]))
    week = week_of(payload, "2026-09-28")
    assert week["usable"] is False
    assert set(week["values"].values()) == {None}
    usable = payload["choices"]["usable_weeks"]
    assert payload["weeks"].index(week) not in usable


def test_three_hours_without_a_change_anywhere_is_a_silent_source() -> None:
    """A stretch with no change in all of Ukraine is the source saying nothing.

    The noise stops for five hours on one day and for two on another: the first
    is blind, the second is a quiet afternoon and stays seen.
    """
    first = at("2026-08-11", "00:00")
    spans = [s for s in busy(first, END)
             if not (at("2026-09-23", "10:00") <= s[2] < at("2026-09-23", "15:00"))
             and not (at("2026-09-24", "10:00") <= s[2] < at("2026-09-24", "12:00"))]
    payload = analyse(replace(make([]), spans=spans))
    silences = [b for b in payload["blind"] if b["kind"] == "silence"]
    assert [b["from"][:10] for b in silences] == ["2026-09-23"]
    assert silences[0]["minutes"] >= analysis.SILENCE_MIN
    day = next(d for d in payload["days"] if d["date"] == "2026-09-23")
    assert day["seen_min"] == 1440 - silences[0]["minutes"]


def test_two_raions_under_alarm_together_are_one_episode() -> None:
    """The band is counted as a whole: a summed count would measure subdivision (F76)."""
    a = at("2026-10-06", "03:00")
    alarms = [(BORDER.code, "active", a, a + timedelta(minutes=40)),
              (INNER.code, "active", a + timedelta(minutes=10), a + timedelta(minutes=70))]
    payload = analyse(make(alarms))
    week = week_of(payload, "2026-10-05")
    assert week["episodes"] == 1
    assert week["band_min"] == 70
    assert week["raion_min"] == 40 + 60
    assert week["border_min"] == 40
    episode = next(e for e in payload["episodes"] if e["start"].startswith("2026-10-06"))
    assert episode["minutes"] == 70 and episode["peak_raions"] == 2 and episode["border"]


def test_an_onset_never_straddles_the_switch_of_instruments() -> None:
    """An alarm running when the API took over starts no episode at the switch."""
    half = timedelta(minutes=30)
    alarms = [(INNER.code, "active", SWITCH - half, SWITCH + half),
              (INNER.code, "active", SWITCH + timedelta(hours=3), SWITCH + timedelta(hours=4))]
    payload = analyse(make(alarms))
    starts = [e for e in payload["episodes"] if e["start"].startswith("2026-08-30")]
    assert [e["source"] for e in starts] == ["channel", "api"]
    assert starts[0]["censored"] is True
    assert payload["record"]["switch"] == "2026-08-30T17:09+02:00"


def test_a_state_that_is_not_a_reading_blinds_the_band() -> None:
    """A raion of the band standing `unknown` is not a raion without an alarm."""
    a = at("2026-10-07", "01:00")
    payload = analyse(make([(INNER.code, "unknown", a, a + timedelta(hours=1))]))
    kinds = [b["kind"] for b in payload["blind"] if b["from"].startswith("2026-10-07")]
    assert kinds == ["unclear"]
    day = next(d for d in payload["days"] if d["date"] == "2026-10-07")
    assert day["seen_min"] == 1440 - 60


# ---- comparisons


def test_the_verdict_is_against_the_range_of_the_background() -> None:
    v = analysis._verdict
    assert v([5.0, 6.0], [1.0, 2.0, 3.0])["verdict"] == "all_above"
    assert v([2.0, 6.0], [1.0, 2.0, 3.0])["verdict"] == "some_above"
    assert v([2.0, 3.0], [1.0, 2.0, 3.0])["verdict"] == "in_range"
    assert v([0.5], [1.0, 2.0])["verdict"] == "all_below"
    assert v([0.5, 2.0], [1.0, 2.0, 3.0])["verdict"] == "some_below"
    assert v([0.5, 6.0], [1.0, 2.0, 3.0])["verdict"] == "some_above"
    assert v([5.0], [1.0])["verdict"] == "thin"
    assert v([None, 6.0], [1.0, 2.0])["verdict"] == "not_computable"
    out = v([2.0, 6.0], [1.0, 2.0, 3.0])
    assert (out["above"], out["last_above"], out["median"], out["max"]) == (1, True, 2.0, 3.0)


def test_every_choice_of_weeks_is_carried_and_the_page_opens_on_two_against_five() -> None:
    payload = analyse(make([]))
    usable = payload["choices"]["usable_weeks"]
    assert len(usable) == 10
    pairs = {(c["n"], c["m"]) for c in payload["comparisons"]}
    assert pairs == {(n, m) for n in range(1, 5) for m in range(2, len(usable) - n + 1)}
    assert payload["choices"]["default"] == {"n": 2, "m": 5}
    for c in payload["comparisons"]:
        cur, base = payload["groups"][c["current"]], payload["groups"][c["baseline"]]
        assert cur["weeks"] == usable[-c["n"]:]
        assert base["weeks"] == usable[-c["n"] - c["m"]:-c["n"]]
        assert set(c["metrics"]) == set(analysis.METRICS)


def test_a_rising_count_of_episodes_is_above_the_background_and_says_so() -> None:
    """One onset a day for eleven weeks, then four a day for the last two."""
    alarms = []
    day = at("2026-08-11", "06:00")
    while day < END - timedelta(hours=8):
        many = day >= at("2026-10-05", "00:00")
        for k in range(4 if many else 1):
            moment = day + timedelta(hours=3 * k)
            alarms.append((INNER.code, "active", moment, moment + timedelta(minutes=30)))
        day += timedelta(days=1)
    payload = analyse(make(alarms))
    metric = comparison(payload, 2, 5)["metrics"]["episodes"]
    assert metric["verdict"] == "all_above"
    assert metric["max"] == 1.0
    assert comparison(payload, 2, 5)["robust"] == [
        {"merge_min": m, "verdict": "all_above"} for m in analysis.MERGES_MIN]
    assert comparison(payload, 2, 5)["metrics"]["duration"]["verdict"] == "in_range"


def rcb_summary(alerts: Sequence[datetime], since: datetime) -> dict[str, Any]:
    return {
        "recorded_since": since.isoformat(),
        "unread": [{"from": START.isoformat(), "to": since.isoformat()}],
        "voivodeships": [{
            "slug": "lubelskie", "voivodeship": "lubelskie",
            "alerts": [{"id": str(k), "valid_from": moment.isoformat(),
                        "painted": [{"from": (moment + timedelta(minutes=3)).isoformat(),
                                     "to": (moment + timedelta(minutes=40)).isoformat()}]}
                       for k, moment in enumerate(alerts)],
        }],
    }


def reads_between(first: datetime, last: datetime, every_s: int) -> list[datetime]:
    out = []
    moment = first
    while moment < last:
        out.append(moment)
        moment += timedelta(seconds=every_s)
    return out


def test_weekly_rcb_counts_read_at_two_cadences_are_not_compared() -> None:
    """A short alert can slip between reads fifteen minutes apart, not one apart."""
    since = at("2026-08-31", "00:00")
    alerts = [at("2026-09-02", "10:00") + timedelta(days=2 * k) for k in range(24)]
    change = at("2026-09-28", "00:00")
    mixed = reads_between(since, change, 930) + reads_between(change, END, 60)
    payload = analyse(make([], rcb=rcb_summary(alerts, since), reads=mixed))
    assert comparison(payload, 2, 5)["metrics"]["rcb"]["verdict"] == "not_assessed"
    assert [run["cadence"] for run in payload["rcb"]["cadence"]] == ["coarse", "fine"]
    fine = analyse(make([], rcb=rcb_summary(alerts, since), reads=reads_between(since, END, 60)))
    assert fine["rcb"]["cadence"] == [{"cadence": "fine", "from": "2026-08-31T00:00+02:00",
                                       "to": fine["rcb"]["cadence"][0]["to"], "every_s": 60}]
    assert comparison(fine, 2, 5)["metrics"]["rcb"]["verdict"] != "not_assessed"


def test_an_alert_at_an_unseen_minute_is_not_an_alert_without_an_alarm() -> None:
    since = at("2026-09-19", "20:00")
    seen, blind = at("2026-10-06", "09:00"), at("2026-10-08", "09:00")
    alarm = (INNER.code, "active", seen - timedelta(minutes=20), seen + timedelta(minutes=20))
    gap = (blind - timedelta(hours=1), blind + timedelta(hours=1))
    payload = analyse(make([alarm], api_gaps=[gap], rcb=rcb_summary([seen, blind], since),
                           reads=reads_between(since, END, 60)))
    one, two = payload["rcb"]["alerts"]
    assert one["band_raions_at_alert"] == 1 and one["band_alarm_since"]["minutes_before"] == 20
    assert one["nearest"] == BAND.index(INNER) and one["seen_after_min"] == 3.0
    assert two["band_raions_at_alert"] is None and two["border_at_alert"] is None
    assert two["band_raions_series"][36] is None
    rules = payload["rcb"]["rules"]
    assert rules["alerts"] == 1 and rules["alerts_without_reading"] == 1
    k1 = next(r for r in rules["rules"] if r["key"] == "k1")
    assert (k1["covered"], k1["recall"]) == (1, 1.0)


def test_an_alert_without_its_own_time_is_seen_after_an_unknown_not_zero() -> None:
    since = at("2026-09-19", "20:00")
    summary = rcb_summary([at("2026-10-06", "09:00"), at("2026-10-08", "09:00")], since)
    summary["voivodeships"][0]["alerts"][1]["valid_from"] = None
    payload = analyse(make([], rcb=summary, reads=reads_between(since, END, 60)))
    declared, listed = payload["rcb"]["alerts"]
    assert declared["declared"] and declared["seen_after_min"] == 3.0
    assert not listed["declared"] and listed["seen_after_min"] is None
    assert payload["rcb"]["seen_after"]["fine"]["n"] == 1


def test_a_run_of_long_days_does_not_step_over_a_day_the_record_missed() -> None:
    long_days = [(INNER.code, "active", at(day, "06:00"), at(day, "15:00"))
                 for day in ("2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-17")]
    whole = analyse(make(long_days))
    assert comparison(whole, 2, 5)["streak"] == {
        "days": 5, "notable": True, "from": "2026-10-13", "to": "2026-10-17",
        "baseline_long_days": 0}
    blind = (at("2026-10-15", "16:00"), at("2026-10-15", "20:00"))
    half_day = (at("2026-10-07", "00:00"), at("2026-10-07", "12:00"))
    broken = analyse(make(long_days, api_gaps=[blind, half_day]))
    streak = comparison(broken, 2, 5)["streak"]
    assert (streak["days"], streak["notable"], streak["from"]) == (2, False, "2026-10-16")
    # Four hours of a week to Sunday noon is under the 5% a week may miss;
    # twelve hours of a whole week is over it.
    assert not week_of(broken, "2026-10-12")["short_record"]
    assert week_of(broken, "2026-10-05")["short_record"]
    assert not week_of(whole, "2026-10-05")["short_record"]


def test_oblasts_tied_at_a_voivodeships_alerts_are_all_named() -> None:
    """Rivne and Volyn both at 11 of 15: the page names both, not the first in band order."""
    def row(oblast: str, pod: int, lub: int, ratio: float | None) -> dict[str, Any]:
        return {"oblast": oblast, "by_voivodeship": {
            "podkarpackie": {"alerts": 15, "with_alarm": pod, "to_minute_share": ratio},
            "lubelskie": {"alerts": 31, "with_alarm": lub, "to_minute_share": 1.2}}}

    top = analysis._oblast_top([row("lviv", 4, 4, 14.9), row("volyn", 11, 28, 7.7),
                                row("zakarpattia", 0, 0, None), row("rivne", 11, 29, 3.9)])
    assert top["podkarpackie"] == {"oblasts": ["volyn", "rivne"], "with_alarm": 11,
                                   "alerts": 15, "well_above_usual": True}
    assert top["lubelskie"] == {"oblasts": ["rivne"], "with_alarm": 29, "alerts": 31,
                                "well_above_usual": False}
    quiet = analysis._oblast_top([row("zakarpattia", 0, 0, None)])
    assert quiet["podkarpackie"] == {"oblasts": [], "with_alarm": 0, "alerts": 15,
                                     "well_above_usual": False}


def test_leads_read_the_latest_onset_east_of_the_band_within_six_hours() -> None:
    a = at("2026-10-07", "04:00")
    alarms = [(RING, "active", a - timedelta(minutes=95), a + timedelta(minutes=30)),
              (INNER.code, "active", a, a + timedelta(minutes=30))]
    payload = analyse(make(alarms))
    episode = next(e for e in payload["episodes"] if e["start"].startswith("2026-10-07"))
    assert episode["leads"][0] == 95
    assert episode["leads"][1:] == [None] * (len(analysis.RING_EDGES_KM) - 2)


def test_the_file_round_trips_through_its_writer(tmp_path: Path) -> None:
    payload = analyse(make([]))
    written = write_analysis(payload, tmp_path / "analysis.json")
    back = json.loads(written.read_text(encoding="utf-8"))
    assert back["v"] == analysis.ANALYSIS_VERSION == 1
    assert back["generated_at"] == END.isoformat()
    assert back == json.loads(json.dumps(payload))
    assert written.read_bytes().rstrip(b"\n").count(b"\n") == 0, "one line, as timeline.json"


# ---- the seam: the store reading, and the command


@pytest.fixture(scope="module")
def recorded(tmp_path_factory: pytest.TempPathFactory) -> Path:
    raw = lzma.decompress(FIXTURE.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == DIGEST, "the recording was edited"
    path = tmp_path_factory.mktemp("week") / "events"
    path.write_bytes(raw)
    return path


WEEK_END = datetime(2026, 9, 26, 0, 0, tzinfo=UTC)


def test_the_recorded_week_reads_as_one_usable_week_and_its_eight_alerts(recorded: Path) -> None:
    """The week ending 2026-09-26 as `vm-mavo` held it: every earlier week is unknown.

    The recording holds that week and the rows standing at its start, so twelve
    of the thirteen weeks have no record and must say so, never zero. Its RCB
    record starts at 18:38 UTC on 2026-09-19 and holds eight air alerts, read
    about every fifteen minutes: the cadence the operator measured that month.
    """
    store = EventStore(recorded)
    payload = analysis.build(store, list(store.replay()), WEEK_END, table=TABLE,
                             feeds=PRODUCTION_FEEDS)
    assert payload["choices"]["usable_weeks"] == [12]
    assert payload["comparisons"] == [] and payload["choices"]["default"] is None
    assert all(set(w["values"].values()) == {None} for w in payload["weeks"][:12])
    alerts = payload["rcb"]["alerts"]
    assert len(alerts) == 8
    assert {a["slug"] for a in alerts} == {"lubelskie", "podkarpackie"}
    assert {a["read_cadence"] for a in alerts} == {"coarse"}
    assert payload["rcb"]["recorded_since"] == "2026-09-19T20:38+02:00"
    (run,) = payload["rcb"]["cadence"]
    assert run["cadence"] == "coarse" and 900 <= run["every_s"] <= 960
    assert payload["weeks"][12]["rcb_alerts"] == 8


def test_the_command_writes_the_file_and_says_what_it_cost(
        recorded: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    copy = tmp_path / "events"
    copy.write_bytes(recorded.read_bytes())
    out = tmp_path / "analysis.json"
    assert main(["analysis", "--store", str(copy), "--out", str(out),
                 "--as-of", WEEK_END.isoformat()]) == 0
    line = capsys.readouterr().out.strip().splitlines()[-1]
    assert line.startswith(f"analysis={out} bytes=")
    assert "usable_weeks=1 comparisons=0" in line
    assert json.loads(out.read_text(encoding="utf-8"))["generated_at"] == WEEK_END.isoformat()


def test_the_command_refuses_a_moment_without_an_offset(
        recorded: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "analysis.json"
    assert main(["analysis", "--store", str(recorded), "--out", str(out),
                 "--as-of", "2026-09-26T00:00:00"]) == 2
    assert "no offset" in capsys.readouterr().err
    assert not out.exists()


def test_a_recent_week_without_the_measure_is_not_compared() -> None:
    """No episode in the last week: its average length is not a length inside the range."""
    alarms = [(INNER.code, "active", at(day, "06:00"), at(day, "07:00"))
              for day in ("2026-09-02", "2026-09-09", "2026-09-16", "2026-09-23", "2026-09-30",
                          "2026-10-07")]
    payload = analyse(make(alarms))
    metric = comparison(payload, 1, 5)["metrics"]["duration"]
    assert metric["verdict"] == "not_computable" and metric["current"] is None
    assert (metric["above"], metric["last_above"]) == (None, None)
    assert comparison(payload, 2, 5)["metrics"]["duration"]["verdict"] == "not_computable"
    assert comparison(payload, 1, 5)["metrics"]["episodes"]["verdict"] == "all_below"


def test_breaks_are_counted_into_lengths_beside_what_chance_would_give() -> None:
    """The page's bars: every break in one length, and the exponential share there."""
    block = analysis._waits_block([{"minutes": m} for m in (5, 20, 45, 90, 200, 500, 900, 2000)])
    assert block is not None
    buckets = block["buckets"]
    assert [b["from_min"] for b in buckets] == list(analysis.WAIT_BUCKETS_MIN)
    assert buckets[-1]["to_min"] is None
    assert [b["n"] for b in buckets] == [1] * 8
    assert sum(b["n"] for b in buckets) == block["n"]
    assert abs(sum(b["random"] for b in buckets) - 1) < 1e-3
    mean = block["mean"]
    assert buckets[0]["random"] == round(1 - math.exp(-10 / mean), 4)
    assert block["under_30_share"] == 0.25
    assert analysis._waits_block([]) is None


# ---- held to figures worked out by hand
#
# The release's review set sixty hand mutants on this module and found that
# fifty-eight of them changed nothing these tests looked at, thirty-three of
# those while changing the file the production export writes. The cases below
# are each a small window whose every expected figure is worked out here, one
# rule to a case, and each names the rules it holds.


def without_noise(spans: Sequence[tuple[str, str, datetime, datetime | None]],
                  holes: Sequence[tuple[datetime, datetime]]
                  ) -> list[tuple[str, str, datetime, datetime | None]]:
    """The far area's changes, less those that begin inside any hole."""
    return [s for s in spans
            if s[0] != "UA-FAR" or not any(a <= s[2] < b for a, b in holes)]


def test_what_is_not_a_reading_is_counted_out_and_nothing_else_is() -> None:
    """Silence, gaps, the switch, and states that are not readings, each at its edge.

    The far area's changes stop for 240 minutes on 23 September, which is a
    silent source; for 200 minutes on 24 September with an hour of API gap
    inside, which leaves 140 minutes the record saw, too few to be silence;
    and for the last four hours of the window. A far area standing `unknown`
    blinds nothing, a channel gap after the switch is not a gap, and an alarm
    that starts in the switch's own minute or right after a gap starts no
    episode, since its minute before was measured otherwise or not at all.
    """
    holes = [(at("2026-09-23", "10:00"), at("2026-09-23", "13:20")),
             (at("2026-09-24", "10:00"), at("2026-09-24", "12:40")),
             (END - timedelta(hours=4), END)]
    alarms = [(INNER.code, "active", SWITCH, SWITCH + timedelta(minutes=40)),
              (INNER.code, "active", at("2026-10-07", "11:00"), at("2026-10-07", "11:30")),
              (INNER.code, "active", at("2026-10-08", "11:00"), at("2026-10-08", "11:30")),
              ("UA-FAR2", "unknown", at("2026-09-25", "01:00"), at("2026-09-25", "02:00"))]
    gaps = [(at("2026-09-24", "11:00"), at("2026-09-24", "12:00")),
            (at("2026-10-07", "10:00"), at("2026-10-07", "11:00"))]
    src = make(alarms, api_gaps=gaps)
    src = replace(src, spans=without_noise(src.spans, holes),
                  channel_gaps=[(SWITCH + timedelta(days=1), SWITCH + timedelta(days=1, hours=2))])
    payload = analyse(src)
    blind = [(b["from"], b["to"], b["kind"]) for b in payload["blind"]]
    assert ("2026-09-23T09:50+02:00", "2026-09-23T13:50+02:00", "silence") in blind
    assert [b for b in blind if b[0].startswith("2026-09-24")] == [
        ("2026-09-24T11:00+02:00", "2026-09-24T12:00+02:00", "gap")]
    tail = [b for b in blind if b[1] == "2026-10-18T12:00+02:00"]
    assert len(tail) == 1 and tail[0][2] == "silence"
    assert not [b for b in blind if b[0].startswith(("2026-09-25", "2026-08-31"))]
    starts = {e["start"] for e in payload["episodes"]}
    assert "2026-08-30T17:09+02:00" not in starts
    assert "2026-10-07T11:00+02:00" not in starts
    assert "2026-10-08T11:00+02:00" in starts
    assert week_of(payload, "2026-08-24")["band_min"] == 40


def test_an_episode_is_cut_where_the_record_is_and_a_break_is_seen_end_to_end() -> None:
    """Censoring, the peak, and which breaks are waits.

    An alarm still running at the end of the window and one ending into a gap
    are censored; a second raion under alarm only while the record was blind
    is not in the peak; a break is a wait only when the record saw all of it,
    on one instrument.
    """
    alarms = [(INNER.code, "active", at("2026-10-18", "11:00"), None),
              (INNER.code, "active", at("2026-10-09", "08:00"), at("2026-10-09", "09:00")),
              (INNER.code, "active", at("2026-10-10", "08:00"), at("2026-10-10", "10:00")),
              (BORDER.code, "active", at("2026-10-10", "08:30"), at("2026-10-10", "08:50")),
              (INNER.code, "active", at("2026-10-13", "08:00"), at("2026-10-13", "08:30")),
              (INNER.code, "active", at("2026-10-13", "10:00"), at("2026-10-13", "10:30")),
              (INNER.code, "active", at("2026-10-14", "08:00"), at("2026-10-14", "08:30")),
              (INNER.code, "active", at("2026-10-14", "10:00"), at("2026-10-14", "10:30")),
              (INNER.code, "active", at("2026-08-30", "15:00"), at("2026-08-30", "15:30")),
              (INNER.code, "active", at("2026-08-30", "18:00"), at("2026-08-30", "18:30"))]
    gaps = [(at("2026-10-09", "09:00"), at("2026-10-09", "10:00")),
            (at("2026-10-10", "08:20"), at("2026-10-10", "09:00")),
            (at("2026-10-14", "09:00"), at("2026-10-14", "09:30"))]
    payload = analyse(make(alarms, api_gaps=gaps))
    episodes = {e["start"]: e for e in payload["episodes"]}
    assert episodes["2026-10-18T11:00+02:00"]["censored"] is True
    assert episodes["2026-10-09T08:00+02:00"]["censored"] is True
    assert episodes["2026-10-10T08:00+02:00"]["peak_raions"] == 1
    assert episodes["2026-10-13T08:00+02:00"]["censored"] is False
    waits = {w["before"]: w["minutes"] for w in payload["waits"]}
    assert waits["2026-10-13T10:00+02:00"] == 90
    assert "2026-10-14T10:00+02:00" not in waits
    assert episodes["2026-08-30T18:00+02:00"]["source"] == "api"
    assert "2026-08-30T18:00+02:00" not in waits


def test_a_lead_is_the_latest_onset_of_the_ring_and_needs_the_record_between() -> None:
    """Two hundred minutes is inside the six-hour window; a gap between voids a lead.

    Two areas of one ring under alarm in overlapping spans are one onset, the
    earlier: the ring's alarm began then, not when its second area joined.
    """
    ring2 = "UA-RING-210"
    alarms = [(RING, "active", at("2026-10-01", "01:00"), at("2026-10-01", "05:00")),
              (INNER.code, "active", at("2026-10-01", "04:20"), at("2026-10-01", "04:50")),
              (RING, "active", at("2026-10-02", "03:00"), at("2026-10-02", "05:00")),
              (INNER.code, "active", at("2026-10-02", "04:00"), at("2026-10-02", "04:30")),
              (RING, "active", at("2026-10-03", "02:00"), at("2026-10-03", "03:00")),
              (ring2, "active", at("2026-10-03", "02:30"), at("2026-10-03", "04:00")),
              (INNER.code, "active", at("2026-10-03", "03:30"), at("2026-10-03", "04:00"))]
    src = make(alarms, api_gaps=[(at("2026-10-02", "03:30"), at("2026-10-02", "03:40"))])
    src.places[ring2] = {"katottg": ring2, "border_km_lower": 210.0, "border_km_upper": 270.0}
    payload = analyse(src)
    leads = {e["start"][:10]: e["leads"][0] for e in payload["episodes"]}
    assert leads == {"2026-10-01": 200, "2026-10-02": None, "2026-10-03": 90}


def test_the_speed_is_fitted_through_the_rings_up_to_four_hundred_and_fifty_km() -> None:
    """Leads of 30, 60, 90 and 120 minutes over the first four rings: 75 km in 30 minutes.

    The two rings beyond the fit carry leads that would bend the line if they
    entered it; every resample of identical episodes draws the same line.
    """
    episodes = [{"leads": [30, 60, 90, 120, 600, 900]} for _ in range(5)]
    block = analysis._rings_block(episodes)
    speed = block["speed"]
    assert [r["median"] for r in block["rings"]] == [30.0, 60.0, 90.0, 120.0, 600.0, 900.0]
    assert speed["rings_used"] == 4
    assert speed["km_per_h"] == speed["km_per_h_p05"] == speed["km_per_h_p95"] == 150.0
    assert speed["minutes_per_km"] == 0.4 and speed["intercept_min"] == -45.0


def test_a_break_of_exactly_the_merge_length_keeps_its_onset() -> None:
    a = at("2026-10-05", "08:00")
    alarms = [(INNER.code, "active", a, a + timedelta(minutes=30)),
              (INNER.code, "active", a + timedelta(minutes=40), a + timedelta(minutes=60))]
    rec = analysis._Record(make(alarms))
    second = rec.minute(a + timedelta(minutes=40))
    assert second in analysis._merged_onsets(rec, 10)
    assert second not in analysis._merged_onsets(rec, 30)


def test_the_list_read_sets_the_cadence_and_an_alert_is_dated_by_its_own_time() -> None:
    """Reads every minute, two days every fifteen, an hour every fifteen, seven hours none.

    The two days make their week a week read coarsely; the hour is a hiccup
    inside the fine cadence and is neither a cadence nor a coarse week; the
    seven hours are a hole, listed as unread and out of the minutes read,
    never a cadence. An alert dated before the window is not in it; one
    listed three and a half minutes after its own time was seen 3.5 minutes
    after; an alert at the moment of a read is measured from that read; the
    raion nearest the border is the one named; and an alarm that began
    right after a gap began at an unknown time.
    """
    since = at("2026-08-31", "00:00")
    c1, c2 = at("2026-09-08", "00:00"), at("2026-09-10", "00:00")
    h1, h2 = at("2026-09-22", "10:00"), at("2026-09-22", "11:00")
    hole = (at("2026-09-24", "01:00"), at("2026-09-24", "08:00"))
    reads = (reads_between(since, c1, 60) + reads_between(c1, c2, 900)
             + reads_between(c2, h1, 60) + reads_between(h1, h2, 900)
             + reads_between(h2, hole[0], 60) + reads_between(hole[1], END, 60))
    moments = [at("2026-07-19", "23:00"), at("2026-09-15", "10:00"), c2,
               at("2026-09-29", "10:00"), at("2026-09-30", "10:00"), at("2026-10-01", "10:00"),
               at("2026-10-06", "09:00")]
    summary = rcb_summary(moments, since)
    summary["unread"].append({"from": hole[0].isoformat(), "to": hole[1].isoformat()})
    summary["voivodeships"][0]["alerts"][1]["painted"][0]["from"] = (
        moments[1] + timedelta(minutes=3, seconds=30)).isoformat()
    alarms = [(INNER.code, "active", at("2026-10-06", "08:40"), at("2026-10-06", "10:00")),
              (BORDER.code, "active", at("2026-10-06", "08:50"), at("2026-10-06", "10:00"))]
    gap = (at("2026-10-06", "08:00"), at("2026-10-06", "08:40"))
    payload = analyse(make(alarms, api_gaps=[gap], rcb=summary, reads=reads))
    assert [(r["cadence"], r["from"], r["every_s"]) for r in payload["rcb"]["cadence"]] == [
        ("fine", "2026-08-31T00:00+02:00", 60), ("coarse", "2026-09-08T00:00+02:00", 900),
        ("fine", "2026-09-10T00:00+02:00", 60)]
    assert week_of(payload, "2026-09-07")["rso_cadence"] == "coarse"
    assert week_of(payload, "2026-09-21")["rso_cadence"] == "fine"
    assert week_of(payload, "2026-09-21")["rcb_seen_min"] == 7 * 1440 - 7 * 60
    assert week_of(payload, "2026-09-28")["values"]["rcb"] == 3.0
    alerts = {a["at"]: a for a in payload["rcb"]["alerts"]}
    assert not [at_ for at_ in alerts if at_.startswith("2026-07")]
    assert alerts["2026-09-15T10:00+02:00"]["seen_after_min"] == 3.5
    at_read = alerts["2026-09-10T00:00+02:00"]
    assert (at_read["read_every_s"], at_read["read_cadence"]) == (60, "fine")
    joined = alerts["2026-10-06T09:00+02:00"]
    assert joined["band_raions_at_alert"] == 2 and joined["nearest"] == BAND.index(BORDER)
    assert joined["band_alarm_since"] == {"at": "2026-10-06T08:40+02:00", "minutes_before": 20,
                                          "cut_by_gap": True}


def test_a_comparison_of_rcb_counts_is_held_to_the_weeks_that_carry_one() -> None:
    """A week read three days carries no count and so no cadence into a verdict.

    Its reads were fifteen minutes apart and every week with a count was read
    every minute: the comparison is assessed. Twelve hours of reads in the
    current week are under the day a pooled count needs.
    """
    since = at("2026-08-28", "00:00")
    turn = at("2026-08-31", "00:00")
    reads = reads_between(since, turn, 900) + reads_between(turn, END, 60)
    payload = analyse(make([], rcb=rcb_summary([], since), reads=reads))
    assert week_of(payload, "2026-08-24")["values"]["rcb"] is None
    assert week_of(payload, "2026-08-24")["rso_cadence"] == "coarse"
    assert comparison(payload, 4, 6)["metrics"]["rcb"]["verdict"] == "in_range"
    late = at("2026-10-18", "00:00")
    short = analyse(make([], rcb=rcb_summary([], late), reads=reads_between(late, END, 60)))
    metric = comparison(short, 1, 2)["metrics"]["rcb"]
    assert (metric["verdict"], metric["current"]) == ("thin", None)


def test_a_rule_is_judged_only_where_the_list_was_read_and_against_every_alert() -> None:
    """One raion's hour of alarm on seven days, held to the RCB record.

    Before the record and before the API took over the hour is no firing;
    on the day the list went unread it is no firing either, since nobody
    could have seen whether it was idle. Of the five that count, the one with
    no alert and the one whose alert came half an hour after it are idle;
    the one whose alert came in its first minute did not precede it; and the
    one with an alert at a minute the band was not observed at is not idle,
    though that alert is not one recall is asked of.
    """
    since = at("2026-08-25", "00:00")
    off = (at("2026-10-08", "00:00"), at("2026-10-09", "00:00"))
    days = ("2026-08-20", "2026-08-27", "2026-09-10", "2026-09-11", "2026-09-12", "2026-09-13",
            "2026-10-08", "2026-10-10")
    alarms = [(INNER.code, "active", at(day, "10:00"), at(day, "11:00")) for day in days]
    alarms.append((BORDER.code, "unknown", at("2026-10-10", "10:20"), at("2026-10-10", "10:40")))
    alerts = [at("2026-09-11", "10:30"), at("2026-09-12", "11:30"), at("2026-09-13", "10:00"),
              at("2026-10-10", "10:30")]
    summary = rcb_summary(alerts, since)
    summary["unread"].append({"from": off[0].isoformat(), "to": off[1].isoformat()})
    reads = reads_between(since, off[0], 60) + reads_between(off[1], END, 60)
    payload = analyse(make(alarms, rcb=summary, reads=reads))
    rules = payload["rcb"]["rules"]
    observed = ((END - SWITCH) // timedelta(minutes=1)) - 1440 - 20
    assert rules["observed_days"] == round(observed / 1440, 2)
    assert (rules["alerts"], rules["alerts_without_reading"]) == (3, 1)
    k1 = next(r for r in rules["rules"] if r["key"] == "k1")
    assert (k1["firings"], k1["idle"], k1["covered"], k1["recall"]) == (5, 2, 1, 0.3333)
    assert k1["idle_per_day"] == round(2 / (observed / 1440), 3)
    episodes = {e["start"][:10]: e for e in payload["episodes"]}
    assert (episodes["2026-09-10"]["rcb"], episodes["2026-09-10"]["rcb_recorded"]) == (False, True)
    assert episodes["2026-10-08"]["rcb_recorded"] is False
    assert episodes["2026-08-20"]["rcb_recorded"] is False
    inner = next(o for o in payload["rcb"]["oblasts"] if o["oblast"] == INNER.oblast)
    assert inner["minute_share"] == round((4 * 60 + 40) / observed, 4)


def test_a_week_of_figures_worked_out_by_hand() -> None:
    """Two raions under alarm every morning, and more alarm in the two recent weeks.

    Uzhhorod from 08:00 to 10:00 and Sambir, on the border, from 08:30 to
    09:30, every day; in the last week before the gap a second alarm from
    10:20 to 11:00, in the week before it from 10:20 to 10:40. The current
    week is blinded to under half by a gap, so the two recent weeks are the
    two full ones before it. Every figure below is the arithmetic of those
    hours.
    """
    alarms = []
    day = at("2026-08-11", "08:00")
    while day < at("2026-10-18", "00:00"):
        alarms.append((INNER.code, "active", day, day + timedelta(hours=2)))
        alarms.append((BORDER.code, "active", day + timedelta(minutes=30),
                       day + timedelta(minutes=90)))
        extra = (40 if day >= at("2026-10-05", "00:00") else
                 20 if day >= at("2026-09-28", "00:00") else 0)
        if extra:
            alarms.append((INNER.code, "active", day + timedelta(minutes=140),
                           day + timedelta(minutes=140 + extra)))
        day += timedelta(days=1)
    gap = (at("2026-10-12", "00:00"), at("2026-10-15", "12:00"))
    payload = analyse(make(alarms, api_gaps=[gap]))
    assert payload["choices"]["usable_weeks"] == list(range(3, 12))
    regular = week_of(payload, "2026-08-31")
    assert regular["values"] == {"episodes": 1.0, "band_h": 2.0, "duration": 120.0,
                                 "breadth": 1.5, "border_h": 1.0, "rcb": None}
    assert (week_of(payload, "2026-08-10")["source"], regular["source"]) == ("channel", "api")
    c = comparison(payload, 2, 5)
    band = c["metrics"]["band_h"]
    assert band["weeks_values"] == [round(140 * 7 / 10080 * 24, 4), round(160 * 7 / 10080 * 24, 4)]
    assert band["current"] == 2.5 and band["max"] == 2.0 and band["verdict"] == "all_above"
    assert band["last_to_max"] == round(160 * 7 / 10080 * 24 / 2.0, 3)
    assert c["metrics"]["episodes"]["verdict"] == "all_above"
    assert c["metrics"]["duration"]["verdict"] == "all_below"
    assert [r["verdict"] for r in c["robust"]] == ["all_above", "in_range", "in_range"]
    base = payload["groups"][c["baseline"]]
    assert base["raions_h"][BAND.index(INNER)] == 2.0
    assert base["raions_h"][BAND.index(BORDER)] == 1.0
    assert comparison(payload, 4, 5)["channel_weeks"] == 3
    assert comparison(payload, 2, 7)["channel_weeks"] == 3


def test_a_group_counts_its_days_hours_and_episodes_by_their_start() -> None:
    """An hour seen for twenty minutes is not an hour of the profile; an alarm unseen is no alarm.

    An episode that begins on a Sunday before midnight belongs to that
    Sunday's week. The record begins at noon, so its first day and the day
    before it are not the weakest days of a choice that holds them.
    """
    alarms = [(INNER.code, "active", at("2026-08-12", "08:00") + timedelta(days=k),
               at("2026-08-12", "09:00") + timedelta(days=k)) for k in range(67)]
    alarms += [(INNER.code, "active", at("2026-09-17", "07:05"), at("2026-09-17", "07:15")),
               (INNER.code, "active", at("2026-09-27", "23:30"), at("2026-09-28", "00:30"))]
    gaps = [(at("2026-09-16", "10:00"), at("2026-09-16", "10:40")),
            (at("2026-09-17", "07:00"), at("2026-09-17", "07:20"))]
    payload = analyse(make(alarms, record_from=at("2026-08-11", "12:00"), api_gaps=gaps))
    base = payload["groups"][comparison(payload, 3, 2)["baseline"]]
    assert (base["first_day"], base["last_day"]) == ("2026-09-14", "2026-09-27")
    assert base["episodes"]["count"] == 14 + 1
    assert base["hours"][10] == {"days": 13, "with_alarm": 0}
    assert base["hours"][8] == {"days": 14, "with_alarm": 14}
    assert base["hours"][7] == {"days": 14, "with_alarm": 0}
    assert base["hours"][23] == {"days": 14, "with_alarm": 1}
    coverage = comparison(payload, 4, 6)["coverage"]
    assert (coverage["weakest_day"], coverage["weakest_share"]) == (
        "2026-09-16", round(1400 / 1440, 4))


def test_the_coverage_of_a_choice_is_the_coverage_of_its_own_weeks() -> None:
    """A week the gap left unusable sits between two chosen ones and is in neither."""
    gap = (at("2026-09-14", "00:00"), at("2026-09-21", "00:00"))
    payload = analyse(make([], api_gaps=[gap]))
    assert 8 not in payload["choices"]["usable_weeks"]
    c = comparison(payload, 2, 5)
    assert payload["groups"][c["baseline"]]["weeks"] == [5, 6, 7, 9, 10]
    assert c["coverage"]["seen_share"] == 1.0 and c["coverage"]["weakest_share"] == 1.0


def test_the_window_ends_on_its_last_whole_minute() -> None:
    """A file written in a Monday's first minute holds the thirteen weeks before it.

    And an alert of the minute the window does not hold waits for the next
    file, instead of reaching the list while no week or day counts it.
    """
    monday = datetime(2026, 10, 18, 22, 0, 30, tzinfo=UTC)
    src = make([])
    payload = analyse(replace(src, start=analysis.window_start(monday), end=monday))
    assert len(payload["weeks"]) == 13
    assert payload["weeks"][-1]["first_day"] == "2026-10-12"
    assert payload["weeks"][-1]["partial"] is False
    since = at("2026-09-19", "20:00")
    late = END + timedelta(seconds=30)
    summary = rcb_summary([END + timedelta(seconds=10)], since)
    edge = analyse(replace(make([], rcb=summary, reads=reads_between(since, END, 60)), end=late))
    assert edge["rcb"]["alerts"] == []
    assert sum(w["rcb_alerts"] for w in edge["weeks"]) == 0


def test_the_run_of_long_days_closes_the_recent_weeks_on_a_monday_too() -> None:
    """On a Wednesday the week still running is not usable yet, and the run ends on Sunday.

    Nine hours of alarm a day from 21 September, except five on 1 October:
    the recent weeks are the two ending on 11 October, and their run of long
    days is the ten days after the short one. The background's long days are
    the seven of the week of 21 September.
    """
    wednesday = datetime(2026, 10, 14, 10, 0, tzinfo=UTC)
    alarms = []
    day = at("2026-09-21", "06:00")
    while day < wednesday:
        hours = 5 if day.astimezone(analysis.ZONE).date().isoformat() == "2026-10-01" else 9
        alarms.append((INNER.code, "active", day, day + timedelta(hours=hours)))
        day += timedelta(days=1)
    src = make(alarms, noise_until=wednesday)
    payload = analyse(replace(src, start=analysis.window_start(wednesday), end=wednesday))
    assert payload["weeks"][-1]["usable"] is False
    assert comparison(payload, 2, 5)["streak"] == {
        "days": 10, "notable": True, "from": "2026-10-02", "to": "2026-10-11",
        "baseline_long_days": 7}


def test_two_speeds_whose_spreads_part_are_not_the_same_speed() -> None:
    """Rings leading the band by 30, 60, 90 and 120 minutes, then by half that.

    Every episode of a group alike, so each group's spread is its own speed:
    150 km/h for the background, 300 for the recent weeks, which do not overlap.
    """
    rings = {"UA-R1": 200.0, "UA-R2": 260.0, "UA-R3": 340.0, "UA-R4": 420.0}
    alarms = []
    day = at("2026-08-31", "06:00")
    while day < at("2026-10-18", "00:00"):
        recent = day >= at("2026-10-05", "00:00")
        for k, area in enumerate(rings):
            lead = timedelta(minutes=(15 if recent else 30) * (k + 1))
            alarms.append((area, "active", day - lead, day + timedelta(minutes=30)))
        alarms.append((INNER.code, "active", day, day + timedelta(minutes=30)))
        day += timedelta(days=1)
    src = make(alarms)
    for area, km in rings.items():
        src.places[area] = {"katottg": area, "border_km_lower": km, "border_km_upper": km + 50}
    payload = analyse(src)
    c = comparison(payload, 2, 5)
    current = payload["groups"][c["current"]]["rings"]["speed"]
    baseline = payload["groups"][c["baseline"]]["rings"]["speed"]
    assert (baseline["km_per_h"], baseline["km_per_h_p05"], baseline["km_per_h_p95"]) == (
        150.0, 150.0, 150.0)
    assert (current["km_per_h"], current["km_per_h_p05"], current["km_per_h_p95"]) == (
        300.0, 300.0, 300.0)
    assert c["speeds_overlap"] is False
    assert comparison(payload, 1, 2)["speeds_overlap"] is True
