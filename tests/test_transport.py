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
from mavo.transport import (
    EXPIRED_BUDGET_FLOOR_S,
    MAX_BYTES,
    UrllibTransport,
    connect_within,
    remaining_budget,
)


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
    # The seam moved at 0.28.1.0: the fetch no longer calls `urlopen`, because
    # `urlopen` cannot be given a deadline that spans connect and read (F98).
    # It grew a fourth argument at 0.36.0.0, the record saying whether an
    # attempt reached the far end, which is what decides a retry (F109).
    monkeypatch.setattr(
        "mavo.transport._open",
        lambda request, timeout_s, deadline, progress=None: _Response(payload),
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
    def refuse(
        request: Any, timeout_s: float, deadline: float, progress: Any = None
    ) -> Any:
        raise urllib.error.URLError("injected")

    monkeypatch.setattr("mavo.transport._open", refuse)
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


class _Clock:
    """A clock that only moves when something spends the budget."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def spend(self, seconds: float) -> None:
        self.now += seconds


def _two_addresses(host: str, port: int) -> list[Any]:
    import socket

    return [
        (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", port, 0, 0)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
    ]


def test_f98_the_budget_is_spent_across_addresses_rather_than_repeated() -> None:
    """F98. Two addresses must not cost two timeouts.

    ``socket.create_connection`` gives every resolved address the full timeout,
    so a ten-second bound on a host with an A and an AAAA record is a
    twenty-second bound in fact, which is what the production host measured
    twice. The second attempt has to inherit what the first left.
    """
    clock = _Clock()
    handed: list[float] = []

    def stalls(resolved: Any, budget: float) -> Any:
        handed.append(budget)
        clock.spend(budget)
        raise TimeoutError("timed out")

    with pytest.raises(OSError):
        connect_within(
            clock.now + 10.0,
            ("example.invalid", 443),
            resolve=_two_addresses,
            attempt=stalls,
            clock=clock,
            # Named explicitly at 0.36.0.0. F109 caps each attempt at two
            # seconds by default, and this test is about the *deadline* being
            # spent rather than repeated. Letting the new cap change the
            # expected numbers here would quietly retire an F98 regression to
            # make an F109 feature pass, which is how a suite stops defending
            # the thing it was written for.
            connect_budget=10.0,
        )

    assert handed == [10.0]
    assert clock.now == 1010.0


def test_f98_a_deadline_already_passed_tries_nothing_and_says_so() -> None:
    clock = _Clock()

    def unreachable(resolved: Any, budget: float) -> Any:
        raise AssertionError("no attempt may be made after the deadline")

    with pytest.raises(TimeoutError):
        connect_within(
            clock.now - 1.0,
            ("example.invalid", 443),
            resolve=_two_addresses,
            attempt=unreachable,
            clock=clock,
        )


def test_f98_the_read_gets_what_the_connect_left_not_a_second_full_timeout() -> None:
    clock = _Clock()
    deadline = clock.now + 10.0
    clock.spend(7.5)
    assert remaining_budget(deadline, clock) == pytest.approx(2.5)


def test_f98_a_spent_budget_still_refuses_rather_than_blocking() -> None:
    # A floor rather than zero: zero puts the socket into non-blocking mode,
    # where a slow server raises `BlockingIOError` and the refusal names the
    # wrong thing.
    clock = _Clock()
    deadline = clock.now + 1.0
    clock.spend(30.0)
    assert remaining_budget(deadline, clock) == EXPIRED_BUDGET_FLOOR_S


def test_f98_the_connection_hands_the_socket_what_is_left_of_the_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The arithmetic is used, not merely correct.

    A budget computed and never applied is the shape of defect this repository
    keeps finding, so the wiring is pinned separately from the sum.
    """
    import http.client
    import time

    from mavo.transport import _BoundedHTTPConnection

    class _Socket:
        def __init__(self) -> None:
            self.timeouts: list[float] = []

        def settimeout(self, value: float) -> None:
            self.timeouts.append(value)

    sock = _Socket()

    def connected(self: Any) -> None:
        self.sock = sock

    monkeypatch.setattr(http.client.HTTPConnection, "connect", connected)
    connection = _BoundedHTTPConnection("example.invalid")
    connection.deadline = time.monotonic() + 4.0
    connection.connect()

    assert len(sock.timeouts) == 1
    assert 3.0 < sock.timeouts[0] <= 4.0


def test_f98_one_attempt_binds_the_budget_to_the_socket_it_opens() -> None:
    import socket as socket_module

    from mavo.transport import _attempt_one

    opened: list[Any] = []

    class _FakeSocket:
        def __init__(self, *_: object) -> None:
            self.timeout: float | None = None
            self.connected: Any = None
            self.closed = False
            opened.append(self)

        def settimeout(self, value: float) -> None:
            self.timeout = value

        def connect(self, sockaddr: Any) -> None:
            self.connected = sockaddr

        def close(self) -> None:
            self.closed = True

    resolved = (
        socket_module.AF_INET,
        socket_module.SOCK_STREAM,
        6,
        "",
        ("127.0.0.1", 443),
    )
    import mavo.transport as transport_module

    original = transport_module.socket.socket
    transport_module.socket.socket = _FakeSocket  # type: ignore[misc, assignment]
    try:
        _attempt_one(resolved, 4.25)
    finally:
        transport_module.socket.socket = original  # type: ignore[misc]

    assert opened[0].timeout == 4.25
    assert opened[0].connected == ("127.0.0.1", 443)
    assert not opened[0].closed


def test_f98_a_refused_attempt_closes_its_socket_before_it_raises() -> None:
    import socket as socket_module

    from mavo.transport import _attempt_one

    opened: list[Any] = []

    class _RefusingSocket:
        def __init__(self, *_: object) -> None:
            self.closed = False
            opened.append(self)

        def settimeout(self, value: float) -> None:
            return None

        def connect(self, sockaddr: Any) -> None:
            raise ConnectionRefusedError("no listener")

        def close(self) -> None:
            self.closed = True

    resolved = (socket_module.AF_INET, socket_module.SOCK_STREAM, 6, "", ("127.0.0.1", 1))
    import mavo.transport as transport_module

    original = transport_module.socket.socket
    transport_module.socket.socket = _RefusingSocket  # type: ignore[misc, assignment]
    try:
        with pytest.raises(ConnectionRefusedError):
            _attempt_one(resolved, 1.0)
    finally:
        transport_module.socket.socket = original  # type: ignore[misc]

    # A descriptor leaked on every refusal is F94's failure in another module.
    assert opened[0].closed


def test_f98_both_connection_classes_route_through_the_shared_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import http.client

    from mavo.transport import _BoundedHTTPConnection, _BoundedHTTPSConnection

    seen: list[float] = []

    def record(deadline: float, address: Any, **kwargs: Any) -> Any:
        seen.append(deadline)
        raise TimeoutError("not connecting in a test")

    monkeypatch.setattr("mavo.transport.connect_within", record)

    for cls in (_BoundedHTTPConnection, _BoundedHTTPSConnection):
        connection = cls("example.invalid")
        connection.deadline = 4321.0
        with pytest.raises(TimeoutError):
            connection._within(("example.invalid", 443))

    assert seen == [4321.0, 4321.0]
    assert issubclass(_BoundedHTTPSConnection, http.client.HTTPSConnection)


def test_f98_the_https_connection_bounds_the_read_after_the_handshake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import http.client
    import time

    from mavo.transport import _BoundedHTTPSConnection

    class _Socket:
        def __init__(self) -> None:
            self.timeouts: list[float] = []

        def settimeout(self, value: float) -> None:
            self.timeouts.append(value)

    sock = _Socket()

    def handshaken(self: Any) -> None:
        self.sock = sock

    monkeypatch.setattr(http.client.HTTPSConnection, "connect", handshaken)
    connection = _BoundedHTTPSConnection("example.invalid")
    connection.deadline = time.monotonic() + 6.0
    connection.connect()

    assert len(sock.timeouts) == 1
    assert 5.0 < sock.timeouts[0] <= 6.0


def test_f98_the_handlers_hand_the_deadline_to_the_connection_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The deadline has to survive the trip through urllib's own machinery.

    `do_open` constructs the connection itself, so the only way through is the
    class. A handler that built the class and forgot the number would pass
    every arithmetic test in this file.
    """
    import urllib.request as request_module

    from mavo.transport import _BoundedHTTPHandler, _BoundedHTTPSHandler

    built: list[Any] = []

    def capture(self: Any, http_class: Any, req: Any, **kwargs: Any) -> str:
        built.append(http_class)
        return "opened"

    monkeypatch.setattr(request_module.AbstractHTTPHandler, "do_open", capture)
    plain = _BoundedHTTPHandler(11.0).http_open(request_module.Request("http://example.invalid"))
    secure = _BoundedHTTPSHandler(22.0).https_open(request_module.Request("https://example.invalid"))

    assert plain == "opened"
    assert secure == "opened"
    assert [cls.deadline for cls in built] == [11.0, 22.0]
