"""Sprint 4 regressions: live ingestion without an access blocker.

Defect class: a network seam that leaks its library's exceptions, and a parser
whose failure mode is an outage rather than a report.

F17. `poll` raising on malformed content converts a hostile string into silence
     during the only window that matters. Every adapter now absorbs content
     failures and reports them; only an unreachable source refuses.
F18. A stale pattern table making a live channel look quiet. Unmatched messages
     are counted and exposed, so the gap between the table and reality shows up
     in the output instead of as an absence of events.

Verified red against a scratch copy of 0.2.1.0: `mavo/transport.py` and
`mavo/sources/telegram.py` do not exist there, so this file errors on import.
That is an import-level red, weaker than a behavioural one, and it is stated
here rather than implied otherwise.
"""

from __future__ import annotations

import pytest

from mavo.errors import SourceUnavailable
from mavo.sources.telegram import TelegramChannelSource
from mavo.transport import FailingTransport, StubTransport, Transport, UrllibTransport

TXT = "<div class='tgme_widget_message_text'>"

HOSTILE = [
    "",
    "<time datetime=''></time>",
    TXT + "\u0000" * 1000 + "</div>",
    f"<time datetime='2026-13-45T99:99:99'></time>{TXT}Львів тривога</div>",
]


def test_f17_no_hostile_body_can_raise() -> None:
    for body in HOSTILE:
        assert TelegramChannelSource(StubTransport(body)).poll() is not None


def test_f17_only_an_unreachable_source_refuses() -> None:
    with pytest.raises(SourceUnavailable):
        TelegramChannelSource(FailingTransport()).poll()


def test_f18_a_stale_pattern_table_is_visible_not_silent() -> None:
    body = (
        '<time datetime="2026-09-01T21:00:00+00:00"></time>'
        '<div class="tgme_widget_message_text">Wording nobody anticipated</div>'
    )
    source = TelegramChannelSource(StubTransport(body))
    assert list(source.poll()) == []
    assert source.report.messages == 1
    assert source.report.unparsed_count == 1


def test_the_network_seam_is_one_file() -> None:
    # A reader answering "what can this thing talk to" should have one file to
    # read. Anything importing urllib outside mavo/transport.py breaks that.
    from pathlib import Path

    package = Path(__file__).resolve().parent.parent / "mavo"
    offenders = [
        path.name
        for path in package.rglob("*.py")
        if path.name != "transport.py" and "urllib" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_transports_satisfy_one_protocol() -> None:
    for transport in (UrllibTransport(), StubTransport(""), FailingTransport()):
        assert isinstance(transport, Transport)
