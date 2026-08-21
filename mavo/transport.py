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

# F109. A connect that has not completed in this long is not a slow connect.
# Measured on the production host 2026-08-20 over 180 requests: every
# successful connection completed in 23 to 55 ms, and every failure consumed
# the whole budget with `time_connect` at exactly zero, which is a SYN that
# went out and was never answered. Two seconds is thirty-six times the slowest
# success observed, so it cannot cut off a connection that was going to work,
# and it costs a fifth of what the old ceiling did when nothing was coming
# back.
CONNECT_BUDGET_S = 2.0

# The exceptions a failed fetch is expected to raise, and the only ones a
# retry is considered for. **F110 is why this is a named constant and not why
# it is narrow.** It was a guess about what `http.client` plus `ssl` can
# raise, the guess was wrong, and `NotImplementedError` walked out of `fetch`,
# past `_cmd_collect`, and killed 168 polls with a traceback and the wrong
# exit code. `fetch` now maps *anything* to `SourceUnavailable`; this tuple
# survives only to decide what is worth attempting twice, where narrow is
# correct: an exception nobody predicted is not evidence that a second attempt
# would go better.
RETRYABLE = (urllib.error.URLError, OSError, ValueError)

# F109. One retry, and one only. Over the same 180 requests the refusal rate
# was 10.6%, and in 7 of 7 observed cases an immediate second attempt
# connected in 24 to 33 ms, so the failures are not correlated at this
# timescale `[measured, n=7; the one-sided 95% lower bound on retry success is
# 65%]`. A second attempt therefore removes most of the rate; a third would be
# arithmetic on a number nobody has measured, and would start to compete with
# the 30 s collection interval.
CONNECT_RETRIES = 1

# F98. The floor a read is given once the budget is spent. Zero would put the
# socket into non-blocking mode, where a slow server produces `BlockingIOError`
# rather than a timeout, so the refusal would name the wrong thing.
EXPIRED_BUDGET_FLOOR_S = 0.05

_Resolved = tuple[socket.AddressFamily, socket.SocketKind, int, str, Any]
Resolver = Callable[[str, int], Sequence[_Resolved]]
Attempt = Callable[[_Resolved, float], socket.socket]
Clock = Callable[[], float]


def resolve_stream(host: str, port: int) -> Sequence[_Resolved]:
    """Resolve ``host`` to stream addresses only.

    **F110.** ``socket.getaddrinfo(host, port)`` with no ``type`` returns
    **three** entries per family, not one: `SOCK_STREAM`, `SOCK_DGRAM` and
    `SOCK_RAW`. A loop that walks them will, after the stream address fails,
    reach the datagram one, and `connect()` on a UDP socket returns
    immediately because there is nothing to negotiate. What comes back is a
    connected-looking socket that TLS then refuses, from inside the standard
    library, with an exception no caller here was catching.

    This was latent from 0.28.1.0 and unreachable until 0.36.0.0: the first
    attempt spent the whole ten-second deadline, so the loop always broke on
    an exhausted budget before it could try a datagram. Capping the attempt
    left budget behind, and the bug was one release old the moment it became
    reachable.
    """
    return socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)


def _attempt_one(resolved: _Resolved, budget: float) -> socket.socket:
    """Open one connection to one resolved address, bounded by ``budget``.

    **F110.** Refuses a candidate that is not a stream, because the resolver
    is an injectable seam and a fix that lives only in the default resolver
    protects the production path and nothing else. The test that found this
    passes a datagram address deliberately.
    """
    family, kind, proto, _canonical, sockaddr = resolved
    if kind != socket.SOCK_STREAM:
        raise OSError(
            f"refusing a {kind.name} address: this transport speaks TLS over "
            f"streams, and connect() on a socket that is not one succeeds "
            f"without having connected to anything"
        )
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
    resolve: Resolver = resolve_stream,
    attempt: Attempt = _attempt_one,
    clock: Clock = time.monotonic,
    connect_budget: float = CONNECT_BUDGET_S,
) -> socket.socket:
    """Connect to ``address``, with every attempt sharing one deadline.

    **F98.** ``socket.create_connection`` gives *each* resolved address the
    full timeout, so a host with an A and an AAAA record costs twice the number
    the caller passed, and a host with four costs four times it. On an
    IPv6-only machine the address that cannot work is tried anyway. The budget
    here is spent, not repeated: the second attempt gets what the first left.

    **F109.** Each attempt is additionally capped at ``connect_budget``. The
    deadline bounds the fetch; this bounds one silence inside it. Without the
    cap a single unanswered SYN spends the entire fetch budget waiting for a
    packet that measurement says is not coming, and the caller learns nothing
    it could not have learned in two seconds.

    Raises the last ``OSError`` seen, or ``TimeoutError`` if the deadline
    passed before any address could be tried.
    """
    host, port = address
    failure: OSError | None = None
    for candidate in resolve(host, port):
        budget = min(deadline - clock(), connect_budget)
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


class _Progress:
    """Whether one attempt got as far as an open connection.

    **F109.** A retry is only safe, and only useful, before the other end has
    said anything. This records the one bit that decides it, and it is a
    mutable object rather than a return value because the connection classes
    are constructed by ``urllib`` and hand nothing back to the caller.
    """

    def __init__(self) -> None:
        self.connected = False


class _BoundedHTTPConnection(http.client.HTTPConnection):
    """An http connection that spends one deadline across connect and read."""

    deadline: float = 0.0
    progress: _Progress = _Progress()

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
        self.progress.connected = True
        if self.sock is not None:
            self.sock.settimeout(remaining_budget(self.deadline))


class _BoundedHTTPSConnection(http.client.HTTPSConnection):
    """The https connection. The TLS handshake inherits the connect budget."""

    deadline: float = 0.0
    progress: _Progress = _Progress()

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
        self.progress.connected = True
        if self.sock is not None:
            self.sock.settimeout(remaining_budget(self.deadline))


def _bound_to(
    base: type[http.client.HTTPConnection], deadline: float, progress: _Progress
) -> type[http.client.HTTPConnection]:
    """A connection class carrying this request's deadline.

    ``AbstractHTTPHandler.do_open`` constructs the connection itself and passes
    only what it knows about, so the deadline travels on the class rather than
    through an argument urllib has no reason to forward.
    """

    class _Bound(base):  # type: ignore[valid-type, misc]
        deadline = 0.0

    _Bound.deadline = deadline
    _Bound.progress = progress
    return _Bound


class _BoundedHTTPHandler(urllib.request.HTTPHandler):
    """Opens http connections that share one deadline."""

    def __init__(self, deadline: float, progress: _Progress | None = None) -> None:
        super().__init__()
        self.deadline = deadline
        # Optional so the handler can be constructed for what it was built to
        # do before F109 existed: carry a deadline. A handler with no record to
        # write into gets a private one rather than a `None` to guard on.
        self.progress = progress if progress is not None else _Progress()

    def http_open(self, req: urllib.request.Request) -> Any:
        """Open ``req`` on a deadline-bounded connection."""
        return self.do_open(
            _bound_to(_BoundedHTTPConnection, self.deadline, self.progress), req
        )


class _BoundedHTTPSHandler(urllib.request.HTTPSHandler):
    """Opens https connections that share one deadline."""

    def __init__(self, deadline: float, progress: _Progress | None = None) -> None:
        super().__init__()
        self.deadline = deadline
        # Optional so the handler can be constructed for what it was built to
        # do before F109 existed: carry a deadline. A handler with no record to
        # write into gets a private one rather than a `None` to guard on.
        self.progress = progress if progress is not None else _Progress()

    def https_open(self, req: urllib.request.Request) -> Any:
        """Open ``req`` on a deadline-bounded connection, TLS included."""
        # No context argument: `HTTPSConnection` builds the same default
        # `ssl` context urllib would have handed it, and reaching for the
        # handler's private attribute to pass it along buys nothing.
        return self.do_open(
            _bound_to(_BoundedHTTPSConnection, self.deadline, self.progress), req
        )


def _open(
    request: urllib.request.Request,
    timeout_s: float,
    deadline: float,
    progress: _Progress | None = None,
) -> Any:
    """Perform the request under one deadline. The seam the tests replace."""
    record = progress if progress is not None else _Progress()
    opener = urllib.request.build_opener(
        _BoundedHTTPHandler(deadline, record), _BoundedHTTPSHandler(deadline, record)
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

    def _attempt(
        self, request: urllib.request.Request, deadline: float, tried: list[int]
    ) -> bytes:
        """Fetch, retrying only a request that never reached the other end.

        **F109.** The condition is `progress.connected`, and it is the whole
        safety argument. A request that connected may have been received and
        acted on, so repeating it is a decision about the far side rather than
        about our own timeout; a request whose SYN was never answered cannot
        have been. That every fetch here is a `GET` is not the reason this is
        safe, because a `GET` that arrived is still a `GET` that arrived.

        Attempts share the outer deadline, so a retry cannot extend the fetch
        past the budget its caller set. It is only made when what remains is
        enough for a whole connect budget, since a retry with two hundred
        milliseconds left is an attempt engineered to fail and would report a
        second failure that measures nothing but the clock.

        ``tried`` is appended to rather than returned, because the count has
        to survive the raise: a refusal that hid a retry would understate what
        the network cost, and the caller writing the journal line is on the
        other side of the exception.
        """
        failure: Exception | None = None
        for _attempt in range(1 + CONNECT_RETRIES):
            progress = _Progress()
            tried.append(1)
            try:
                with _open(request, self.timeout_s, deadline, progress) as response:
                    return bytes(response.read(MAX_BYTES + 1))
            except RETRYABLE as refused:
                failure = refused
                if progress.connected:
                    raise
                if time.monotonic() + CONNECT_BUDGET_S > deadline:
                    raise
        assert failure is not None  # unreachable: the loop runs at least once
        raise failure

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
        deadline = started + self.timeout_s
        tried: list[int] = []
        try:
            raw = self._attempt(request, deadline, tried)
        except Exception as failure:
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
            attempts = "" if len(tried) <= 1 else f", {len(tried)} attempts"
            raise SourceUnavailable(
                f"{url}: {failure} "
                f"[after {waited:.2f}s, {type(failure).__name__}{attempts}]"
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
