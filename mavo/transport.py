"""The only place in the package that reaches the network.

Isolated behind a protocol so every adapter is testable without a network, and
so a reader can answer "what can this thing talk to" by reading one file.

Convention borrowed from `pirx`: the adapter is tested against an injected
transport, and the limit of that testing is stated rather than implied. That a
live service returns what the tests assume is **not** tested here.
"""

from __future__ import annotations

import http.client
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from typing import Any, Protocol, runtime_checkable

from mavo import __version__
from mavo.errors import SourceUnavailable

# Derived from the package version rather than typed here. A version string
# duplicated outside its single source of truth drifts on the first bump it is
# not part of, which is exactly how this constant shipped saying 0.3.0.0 at
# 0.3.1.0 (F36).
USER_AGENT = f"mavo/{__version__} (+https://github.com/jerzy99jerzy)"
DEFAULT_TIMEOUT_S = 10.0
MAX_BYTES = 4_000_000

# F98. The floor a read is given once the budget is spent. Zero would put the
# socket into non-blocking mode, where a slow server produces `BlockingIOError`
# rather than a timeout, so the refusal would name the wrong thing.
EXPIRED_BUDGET_FLOOR_S = 0.05

_Resolved = tuple[socket.AddressFamily, socket.SocketKind, int, str, Any]
Resolver = Callable[[str, int], Sequence[_Resolved]]
Attempt = Callable[[_Resolved, float], socket.socket]
Clock = Callable[[], float]


def _attempt_one(resolved: _Resolved, budget: float) -> socket.socket:
    """Open one connection to one resolved address, bounded by ``budget``."""
    family, kind, proto, _canonical, sockaddr = resolved
    sock = socket.socket(family, kind, proto)
    try:
        sock.settimeout(budget)
        sock.connect(sockaddr)
    except OSError:
        sock.close()
        raise
    return sock


def connect_within(
    deadline: float,
    address: tuple[str, int],
    *,
    resolve: Resolver = socket.getaddrinfo,
    attempt: Attempt = _attempt_one,
    clock: Clock = time.monotonic,
) -> socket.socket:
    """Connect to ``address``, with every attempt sharing one deadline.

    **F98.** ``socket.create_connection`` gives *each* resolved address the
    full timeout, so a host with an A and an AAAA record costs twice the number
    the caller passed, and a host with four costs four times it. On an
    IPv6-only machine the address that cannot work is tried anyway. The budget
    here is spent, not repeated: the second attempt gets what the first left.

    Raises the last ``OSError`` seen, or ``TimeoutError`` if the deadline
    passed before any address could be tried.
    """
    host, port = address
    failure: OSError | None = None
    for candidate in resolve(host, port):
        budget = deadline - clock()
        if budget <= 0:
            break
        try:
            return attempt(candidate, budget)
        except OSError as refused:
            failure = refused
    if failure is not None:
        raise failure
    raise TimeoutError(f"{host}:{port}: no address was reached within the budget")


def remaining_budget(deadline: float, clock: Clock = time.monotonic) -> float:
    """What is left of the deadline, floored so a spent budget still refuses."""
    return max(deadline - clock(), EXPIRED_BUDGET_FLOOR_S)


class _BoundedHTTPConnection(http.client.HTTPConnection):
    """An http connection that spends one deadline across connect and read."""

    deadline: float = 0.0

    def _within(
        self,
        address: tuple[str, int],
        timeout: float | None = None,
        source_address: tuple[str, int] | None = None,
    ) -> socket.socket:
        return connect_within(self.deadline, address)

    def connect(self) -> None:
        """Connect under the deadline, then hand the read what is left of it."""
        self._create_connection = self._within
        super().connect()
        if self.sock is not None:
            self.sock.settimeout(remaining_budget(self.deadline))


class _BoundedHTTPSConnection(http.client.HTTPSConnection):
    """The https connection. The TLS handshake inherits the connect budget."""

    deadline: float = 0.0

    def _within(
        self,
        address: tuple[str, int],
        timeout: float | None = None,
        source_address: tuple[str, int] | None = None,
    ) -> socket.socket:
        return connect_within(self.deadline, address)

    def connect(self) -> None:
        """Connect and handshake under the deadline, then bound the read."""
        self._create_connection = self._within
        super().connect()
        if self.sock is not None:
            self.sock.settimeout(remaining_budget(self.deadline))


def _bound_to(
    base: type[http.client.HTTPConnection], deadline: float
) -> type[http.client.HTTPConnection]:
    """A connection class carrying this request's deadline.

    ``AbstractHTTPHandler.do_open`` constructs the connection itself and passes
    only what it knows about, so the deadline travels on the class rather than
    through an argument urllib has no reason to forward.
    """

    class _Bound(base):  # type: ignore[valid-type, misc]
        deadline = 0.0

    _Bound.deadline = deadline
    return _Bound


class _BoundedHTTPHandler(urllib.request.HTTPHandler):
    """Opens http connections that share one deadline."""

    def __init__(self, deadline: float) -> None:
        super().__init__()
        self.deadline = deadline

    def http_open(self, req: urllib.request.Request) -> Any:
        """Open ``req`` on a deadline-bounded connection."""
        return self.do_open(_bound_to(_BoundedHTTPConnection, self.deadline), req)


class _BoundedHTTPSHandler(urllib.request.HTTPSHandler):
    """Opens https connections that share one deadline."""

    def __init__(self, deadline: float) -> None:
        super().__init__()
        self.deadline = deadline

    def https_open(self, req: urllib.request.Request) -> Any:
        """Open ``req`` on a deadline-bounded connection, TLS included."""
        # No context argument: `HTTPSConnection` builds the same default
        # `ssl` context urllib would have handed it, and reaching for the
        # handler's private attribute to pass it along buys nothing.
        return self.do_open(_bound_to(_BoundedHTTPSConnection, self.deadline), req)


def _open(request: urllib.request.Request, timeout_s: float, deadline: float) -> Any:
    """Perform the request under one deadline. The seam the tests replace."""
    opener = urllib.request.build_opener(
        _BoundedHTTPHandler(deadline), _BoundedHTTPSHandler(deadline)
    )
    return opener.open(request, timeout=timeout_s)


@runtime_checkable
class Transport(Protocol):
    """Fetches a document. The one seam between this package and the internet."""

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        """Return the document body as text.

        Raises ``SourceUnavailable`` and nothing else. A transport that leaks a
        library-specific exception forces every caller to know which library is
        underneath, which is the coupling this protocol exists to prevent.

        `headers` was added at 0.28.0.0 for the measurement adapter, which has
        to send an API key. It goes through this seam rather than around it:
        the alternative was a second module opening its own connections, which
        the architecture check caught immediately and which would have put
        network behaviour in two files instead of one.

        **A key belongs in a header and never in a URL**, where it would reach
        every proxy log between here and the other end.
        """
        ...


class UrllibTransport:
    """Standard-library transport. No third-party dependency to audit."""

    def __init__(self, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        """``timeout_s`` is the budget for the whole fetch, not per operation.

        F98. Until this release the number was handed to ``urlopen``, where it
        bounds every blocking socket operation separately: a connect that
        stalls and a read that stalls each got the full ten seconds, and each
        resolved address got ten more. Measured twice on the production host, a
        ten-second timeout took twenty. It now names a deadline, which is what
        every caller and every calculation already assumed it named.
        """
        self.timeout_s = timeout_s

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        """Fetch ``url``, capped in size and time. Refuses any non-http(s) scheme.

        F62. ``urlopen`` also speaks ``file://`` and would return local file
        contents as though they were a fetched page. The URLs here are
        constants, but a transport that reads the filesystem when handed the
        wrong string is a latent local-file-read, and the refusal is two lines.
        """
        scheme = urllib.parse.urlsplit(url).scheme.lower()
        if scheme not in ("http", "https"):
            raise SourceUnavailable(
                f"{url}: scheme {scheme!r} refused; this transport speaks http(s)"
            )
        sent = {"User-Agent": USER_AGENT}
        if headers:
            # Caller headers second, so a caller cannot silently replace the
            # user agent this package identifies itself with. Anything else it
            # sends is its own business and is visible at the call site.
            sent = {**sent, **headers}
        request = urllib.request.Request(url, headers=sent)
        started = time.monotonic()
        try:
            with _open(request, self.timeout_s, started + self.timeout_s) as response:
                raw = response.read(MAX_BYTES + 1)
        except (urllib.error.URLError, OSError, ValueError) as failure:
            # T55. The refusal carries how long it waited and what was raised,
            # because without them a stall that hit the ten-second ceiling and
            # a rejection that bounced in twenty milliseconds are the same line
            # in a journal. F98 is why the ceiling now means what it says;
            # before it, this line was the evidence that it did not.
            # Eleven refusals were logged over one night before
            # anybody noticed the line answers no question - F44 in the
            # diagnostics rather than in the schedule.
            #
            # Monotonic rather than wall clock: an NTP step during a ten-second
            # wait would otherwise produce a negative duration or a wild one,
            # and a diagnostic that reports nonsense under load is worse than
            # one that reports nothing.
            waited = time.monotonic() - started
            raise SourceUnavailable(
                f"{url}: {failure} "
                f"[after {waited:.2f}s, {type(failure).__name__}]"
            ) from failure
        if len(raw) > MAX_BYTES:
            raise SourceUnavailable(f"{url}: response exceeds {MAX_BYTES} bytes")
        body: str = bytes(raw).decode("utf-8", errors="replace")
        return body


class StubTransport:
    """Returns a fixed body. For tests, and for `mavo collect --stub`."""

    def __init__(self, body: str) -> None:
        self.body = body
        self.calls = 0
        self.last_headers: dict[str, str] = {}

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        """Return the canned body, counting calls.

        Headers are accepted and ignored, and the last call's are kept so a
        test can assert on what a caller sent without the stub pretending to
        be a network.
        """
        self.calls += 1
        self.last_headers = dict(headers or {})
        return self.body


class FailingTransport:
    """Always refuses. Models an unreachable source, distinct from a quiet one."""

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        """Always raise ``SourceUnavailable``."""
        raise SourceUnavailable(f"{url}: injected failure")
