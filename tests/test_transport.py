"""The stdlib transport's local logic, tested without a network.

The module docstring in ``mavo/transport.py`` states, correctly, that a live
service's behaviour cannot be tested from here. Until 0.6.0.0 that true claim
quietly covered three pieces of *local* logic that can be: the size cap, the
exception mapping, and the lossy decode. The size cap is a threat-model control
(an oversized hostile body), and a control without a test is, by this
repository's own standard, an unmeasured one (review RV-5).
"""

from __future__ import annotations

import urllib.error
from typing import Any

import pytest

from mavo.errors import SourceUnavailable
from mavo.transport import MAX_BYTES, UrllibTransport


class _Response:
    """The minimum surface ``fetch`` touches on a urllib response."""

    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        return None


def _serving(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
    monkeypatch.setattr(
        "mavo.transport.urllib.request.urlopen",
        lambda request, timeout: _Response(payload),
    )


def test_a_body_at_exactly_the_cap_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    _serving(monkeypatch, b"a" * MAX_BYTES)
    assert len(UrllibTransport().fetch("https://example.invalid")) == MAX_BYTES


def test_a_body_over_the_cap_is_a_refusal_not_a_truncation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Truncating would hand the parser a page that is silently missing its
    # tail, which during a mass alert is exactly the window that matters.
    _serving(monkeypatch, b"a" * (MAX_BYTES + 1))
    with pytest.raises(SourceUnavailable):
        UrllibTransport().fetch("https://example.invalid")


def test_a_url_error_maps_to_the_one_refusal_type(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(request: Any, timeout: float) -> Any:
        raise urllib.error.URLError("injected")

    monkeypatch.setattr("mavo.transport.urllib.request.urlopen", refuse)
    with pytest.raises(SourceUnavailable):
        UrllibTransport().fetch("https://example.invalid")


def test_invalid_utf8_is_replaced_rather_than_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    # A hostile byte sequence must degrade to replacement characters, not to an
    # exception: a decode error raised here would turn content into an outage,
    # the same conversion the parser's never-raise contract exists to prevent.
    _serving(monkeypatch, b"\xff\xfe alert")
    body = UrllibTransport().fetch("https://example.invalid")
    assert "alert" in body


def test_f62_a_non_http_scheme_is_refused() -> None:
    """F62. The transport speaks to the web, not to the filesystem.

    ``urllib.request.urlopen`` accepts ``file://`` and would return local file
    contents as though they were a fetched page. The URL is a constant today,
    but a transport that will read ``/etc/passwd`` when handed the wrong string
    is a latent local-file-read, and the refusal costs two lines.
    """
    with pytest.raises(SourceUnavailable):
        UrllibTransport().fetch("file:///etc/hostname")
    with pytest.raises(SourceUnavailable):
        UrllibTransport().fetch("ftp://example.invalid/x")
