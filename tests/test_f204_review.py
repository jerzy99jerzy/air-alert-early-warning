"""F204: the 2026-10-25 review's critical and high findings, each pinned.

`docs/reviews/0.63.0.0.md` names them: P-1 (an alarm that ended inside an API
gap never closed), P-2 (a well-formed body that is not the alerts list cleared
the map), P-3 (a redirect carried the key off its origin), P-4 (the publish
loop died on three unguarded callables), P-5 (the bare verb `zakończono` read
an alert as an all-clear), N-F7 (the canary vouched for a walk it could not
see) and X-1 (a blind cycle wrote counted zeros). Every case here was seen
failing on 0.62.0.0 and has a control beside it that passes on both trees.
"""

from __future__ import annotations

import contextlib
import http.server
import io
import json
import threading
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

import mavo.cli as cli
from mavo.errors import SourceUnavailable
from mavo.poland import classify
from mavo.report import FeedState, compose, publish, write_contract
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind
from mavo.sources import rso
from mavo.sources.ukrainealarm_source import UkrainealarmSource
from mavo.store import EventStore
from mavo.transport import UrllibTransport

LVIV = "Львівський район"
LUTSK = "Луцький район"
LUTSK_ID = "UA07080000000034745"


def _body(regions: list[str]) -> str:
    began = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    return json.dumps([
        {"regionId": str(1000 + i), "regionName": name,
         "activeAlerts": [{"regionId": str(1000 + i), "regionType": "District",
                           "type": "AIR", "lastUpdate": began}]}
        for i, name in enumerate(regions)
    ])


class _Feed:
    """One body, swappable, for the source the CLI builds."""

    body = _body([])

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        return self.body


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> _Feed:
    feed = _Feed()

    class Injected(UkrainealarmSource):
        def __init__(self, key: str, **kw: Any) -> None:
            kw["transport"] = feed
            super().__init__(key, **kw)

    monkeypatch.setattr(cli, "UkrainealarmSource", Injected)
    monkeypatch.setattr(cli, "read_key", lambda path=None: "test-key")
    return feed


def _collect(store: Path, snapshot: Path) -> str:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(["collect-api", "--store", str(store), "--snapshot", str(snapshot)])
    assert code == 0, out.getvalue()
    return out.getvalue()


def _age_snapshot(snapshot: Path, seconds: float) -> None:
    payload = json.loads(snapshot.read_text())
    saved = datetime.fromisoformat(payload["saved_at"]) - timedelta(seconds=seconds)
    payload["saved_at"] = saved.isoformat()
    snapshot.write_text(json.dumps(payload))


def _newest(store: Path, area_id: str) -> ThreatEvent:
    return next(event for (area, _kind), event in
                EventStore(store).newest_by_area_kind().items() if area == area_id)


# -- P-1 (D-066): an alarm that ends inside a gap is closed by the next read --


def test_an_alarm_that_ended_inside_a_gap_is_closed_by_the_read_after_it(
    api: _Feed, tmp_path: Path
) -> None:
    store, snapshot = tmp_path / "events", tmp_path / "snapshot.json"
    api.body = _body([LVIV, LUTSK])
    _collect(store, snapshot)
    _age_snapshot(snapshot, 400)
    api.body = _body([LVIV])
    out = _collect(store, snapshot)
    assert "closed 1 alarm(s) the API no longer lists" in out
    closed = _newest(store, LUTSK_ID)
    assert closed.state is AlertState.CLEAR
    assert closed.provenance is Provenance.INFERENCE
    assert closed.raw_fields["reason"] == "absent after observation gap"
    assert closed.raw_fields["snapshot"] == "stale"
    # Dated by the read, never by anything inside the gap.
    assert closed.ts_source == closed.ts_ingest
    assert closed.ts_source > datetime.now(UTC) - timedelta(minutes=1)


def test_an_alarm_still_listed_after_a_gap_is_not_closed(api: _Feed, tmp_path: Path) -> None:
    store, snapshot = tmp_path / "events", tmp_path / "snapshot.json"
    api.body = _body([LVIV, LUTSK])
    _collect(store, snapshot)
    _age_snapshot(snapshot, 400)
    out = _collect(store, snapshot)
    assert "the API no longer lists" not in out
    assert _newest(store, LUTSK_ID).state is AlertState.ACTIVE


def test_a_lost_snapshot_closes_against_the_store_too(api: _Feed, tmp_path: Path) -> None:
    store, snapshot = tmp_path / "events", tmp_path / "snapshot.json"
    api.body = _body([LVIV, LUTSK])
    _collect(store, snapshot)
    snapshot.unlink()
    api.body = _body([LVIV])
    _collect(store, snapshot)
    assert _newest(store, LUTSK_ID).state is AlertState.CLEAR


def test_a_row_stored_after_the_read_began_is_not_closed(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    moment = datetime.now(UTC)
    store.append([ThreatEvent(
        area_id=LUTSK_ID, state=AlertState.ACTIVE, ts_source=moment, source_id="ukrainealarm",
        ts_ingest=moment + timedelta(seconds=5), kind=ThreatKind.UNKNOWN,
        provenance=Provenance.REPORTED, raw_fields={}, oblast="",
    )])
    source = UkrainealarmSource("key", transport=_Feed())
    source.poll()
    source.polled_at = moment
    assert cli._clears_after_gap(store, source, ()) == ()


def test_reconcile_closes_an_api_ghost_already_on_record(api: _Feed, tmp_path: Path) -> None:
    """The phantoms 0.62.0.0 and earlier left behind, found by the widened filter."""
    store, snapshot = tmp_path / "events", tmp_path / "snapshot.json"
    api.body = _body([LVIV, LUTSK])
    _collect(store, snapshot)
    # The pre-0.63.0.0 behaviour, reproduced: a fresh snapshot that no longer
    # lists Lutsk while the store still holds it open.
    payload = json.loads(snapshot.read_text())
    payload["areas"] = [entry for entry in payload["areas"] if entry["area"] != LUTSK_ID]
    payload["saved_at"] = datetime.now(UTC).isoformat()
    snapshot.write_text(json.dumps(payload))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(["reconcile", "--store", str(store), "--snapshot", str(snapshot),
                         "--apply"])
    assert code == 0, out.getvalue()
    assert "ghosts=1" in out.getvalue()
    assert _newest(store, LUTSK_ID).state is AlertState.CLEAR


# -- P-2: a body that is not the alerts list is refused, not read as `[]` -----


@pytest.mark.parametrize("body", [
    "{}", "null", '"x"', "7", '{"message": "Unauthorized"}',
    '{"data": [{"regionName": "x", "activeAlerts": []}]}',
    "[{}, {}]", "[1, 2, 3]", '[{"regionName": "x", "activeAlerts": {"a": 1}}]',
])
def test_a_body_that_is_not_the_alerts_list_clears_nothing(body: str) -> None:
    feed = _Feed()
    feed.body = _body([LVIV])
    source = UkrainealarmSource("key", transport=feed)
    source.poll()
    feed.body = body
    with pytest.raises(SourceUnavailable, match="not the alerts list"):
        source.poll()
    feed.body = _body([LVIV])
    assert source.poll() == ()


def test_the_real_quiet_sky_still_clears() -> None:
    feed = _Feed()
    feed.body = _body([LVIV])
    source = UkrainealarmSource("key", transport=feed)
    source.poll()
    feed.body = "[]"
    (event,) = source.poll()
    assert event.state is AlertState.CLEAR


# -- P-3: credentials do not follow a redirect off their origin ---------------


@contextlib.contextmanager
def _server(host: str, handler: type[http.server.BaseHTTPRequestHandler]
            ) -> Iterator[http.server.HTTPServer]:
    server = http.server.HTTPServer((host, 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


def _recorder(seen: list[str | None]) -> type[http.server.BaseHTTPRequestHandler]:
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            seen.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"[]")

        def log_message(self, *args: object) -> None:
            pass
    return Handler


def _redirector(target: str) -> type[http.server.BaseHTTPRequestHandler]:
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path.startswith("/landed"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"[]")
                return
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()

        def log_message(self, *args: object) -> None:
            pass
    return Handler


def test_a_redirect_to_another_host_does_not_carry_the_key() -> None:
    seen: list[str | None] = []
    with _server("127.0.0.1", _recorder(seen)) as other:
        elsewhere = f"http://127.0.0.1:{other.server_port}/alerts"
        with _server("127.0.0.1", _redirector(elsewhere)) as origin:
            url = f"http://127.0.0.1:{origin.server_port}/alerts"
            with pytest.raises(SourceUnavailable, match="another origin"):
                UrllibTransport(timeout_s=5).fetch(url, headers={"Authorization": "k" * 41})
    assert seen == []


def test_a_redirect_without_credentials_is_followed() -> None:
    seen: list[str | None] = []
    with _server("127.0.0.1", _recorder(seen)) as other:
        elsewhere = f"http://127.0.0.1:{other.server_port}/alerts"
        with _server("127.0.0.1", _redirector(elsewhere)) as origin:
            url = f"http://127.0.0.1:{origin.server_port}/alerts"
            assert UrllibTransport(timeout_s=5).fetch(url) == "[]"
    assert seen == [None]


def test_a_same_origin_redirect_keeps_the_key() -> None:
    holder: dict[str, str] = {}

    class Same(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/landed":
                holder["auth"] = self.headers.get("Authorization") or ""
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"[]")
                return
            self.send_response(302)
            self.send_header("Location", "/landed")
            self.end_headers()

        def log_message(self, *args: object) -> None:
            pass

    with _server("127.0.0.1", Same) as origin:
        url = f"http://127.0.0.1:{origin.server_port}/alerts"
        assert UrllibTransport(timeout_s=5).fetch(url, headers={"Authorization": "key"}) == "[]"
    assert holder["auth"] == "key"


# -- P-4: the publish loop outlives its observers ----------------------------


def test_a_compose_that_raises_publishes_blind_and_keeps_going(tmp_path: Path) -> None:
    def broken(*_args: object) -> tuple[()]:
        raise OSError("database is locked")

    target = tmp_path / "state.json"
    outcome = publish(lambda: [], target, interval_s=0.01, max_cycles=2,
                      sleep=lambda _s: None, sources=broken)
    assert outcome.written == 2
    assert json.loads(target.read_text())["state"] == "blind"


def test_a_run_log_that_fails_is_dropped_not_fatal(tmp_path: Path) -> None:
    class Full:
        def cycle_id(self) -> str:
            return "c"

        def line(self, *_args: object, **_fields: object) -> None:
            raise OSError(28, "No space left on device")

    target = tmp_path / "state.json"
    outcome = publish(lambda: [], target, interval_s=0.01, max_cycles=3,
                      sleep=lambda _s: None, log=Full())  # type: ignore[arg-type]
    assert outcome.written == 3


def test_the_cli_sources_closure_publishes_null_on_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def locked(*_args: object, **_kw: object) -> tuple[()]:
        raise OSError("database is locked")

    monkeypatch.setattr(cli, "measure_liveness", locked)
    store = tmp_path / "events"
    EventStore(store)
    target = tmp_path / "state.json"
    with contextlib.redirect_stdout(io.StringIO()):
        code = cli.main(["report", "--store", str(store), "--watch", "--max-cycles", "1",
                         "--interval", "1", "--json", str(target)])
    assert code == 0
    assert json.loads(target.read_text())["sources"] is None


# -- P-5 / N-1: a reassurance inside an alert is not its all-clear ------------


def test_a_bare_zakonczono_does_not_end_an_alert() -> None:
    verdict = classify("Alert RCB", "Atak powietrzny. Zakończono ewakuację szkół.")
    assert verdict is not None and verdict[0] == "threat"


def test_the_measured_all_clear_sentence_still_ends_one() -> None:
    verdict = classify("Alert RCB", "Atak powietrzny. Zakończył się atak z powietrza.")
    assert verdict is not None and verdict[0] == "all_clear"


# -- N-F7: the canary vouches only for what it can see -----------------------

_GOOD = """<?xml version="1.0" encoding="utf-8"?>
<newses>
  <pagination_info totalItems="2" itemsPerPage="20"/>
  <news><id>23441700</id><title>ALERT RCB</title></news>
  <news><id>23441746</id><title>komunikat</title></news>
</newses>
"""
_DRIFTED = _GOOD.replace("<news>", "<item>").replace("</news>", "</item>")


def test_a_renamed_record_is_unreadable_not_absent() -> None:
    page = rso.parse_page(_DRIFTED.encode())
    assert page.communiques == ()
    assert page.unreadable == 2
    assert rso.parse_page(_GOOD.encode()).unreadable == 0


def test_a_canary_blind_to_what_the_walk_read_does_not_vouch() -> None:
    scope = rso.parse_page(_GOOD.encode())
    reason = cli._rso_unvouched(scope, {"23441700", "9"}, 0, {"23441700", "9"})
    assert reason is not None and reason.startswith("[UNVOUCHED]")
    assert "does not list 1" in reason


def test_a_row_of_the_category_the_scope_omits_is_not_held_against_it() -> None:
    scope = rso.parse_page(_GOOD.encode())
    walked = {"23441700", "23441746", "9"}
    assert cli._rso_unvouched(scope, walked, 0, {"23441700", "23441746"}) is None


def test_a_drifted_feed_end_to_end_is_refused(tmp_path: Path) -> None:
    stub = tmp_path / "drifted.xml"
    stub.write_text(_DRIFTED, encoding="utf-8")
    store = tmp_path / "events"
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(["rso", "--stub", str(stub), "--store", str(store)])
    assert code == 3, out.getvalue()
    assert "[UNKNOWN-CATEGORY]" in out.getvalue()


def test_a_clean_feed_end_to_end_is_vouched(tmp_path: Path) -> None:
    stub = tmp_path / "good.xml"
    stub.write_text(_GOOD, encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(["rso", "--stub", str(stub), "--store", str(tmp_path / "events")])
    assert code == 0, out.getvalue()


# -- X-1: a blind cycle counts nothing it can stand behind --------------------


def test_a_blind_cycle_writes_null_counts(tmp_path: Path) -> None:
    report = compose([], as_of=datetime.now(UTC))
    assert report.feed_state is FeedState.BLIND
    payload = json.loads(write_contract(report, tmp_path / "state.json").read_text())
    assert payload["counts_24h"] == {"west": None, "rest": None, "total": None}


def test_a_counted_cycle_still_writes_integers(tmp_path: Path) -> None:
    now = datetime.now(UTC)
    event = ThreatEvent(
        area_id="UA46060000000042587", state=AlertState.ACTIVE,
        ts_source=now - timedelta(minutes=5), ts_ingest=now - timedelta(minutes=5),
        source_id="ukrainealarm", kind=ThreatKind.UNKNOWN,
        provenance=Provenance.REPORTED, raw_fields={}, oblast="Львівська",
    )
    report = compose([event], as_of=now)
    assert report.feed_state is not FeedState.BLIND
    payload = json.loads(write_contract(report, tmp_path / "state.json").read_text())
    counts = payload["counts_24h"]
    assert all(isinstance(counts[key], int) for key in ("west", "rest", "total"))
