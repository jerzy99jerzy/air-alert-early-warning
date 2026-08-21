"""F109. The connect budget, and the one retry that is safe to make.

Measured on the production host on 2026-08-20, over 180 requests in four
series: 10.6% of connections were never answered, every successful connect
completed in 23 to 55 ms, and every failure spent its whole budget with
`time_connect` at exactly zero. In 7 of 7 observed cases an immediate second
attempt connected. The rate agrees with three windows of the journal, which
read 9.74%, 9.86% and 9.85%.

Two changes follow, and each has a way of being wrong that these tests exist
to catch. A cap that also cuts off slow-but-working connections would trade a
known failure for an invented one. A retry that fires after the far end has
already received the request would turn our own timeout into a decision about
somebody else's state.
"""

from __future__ import annotations

import socket
import urllib.error
from typing import Any

import pytest

from mavo.errors import SourceUnavailable
from mavo.transport import (
    CONNECT_BUDGET_S,
    CONNECT_RETRIES,
    UrllibTransport,
    _attempt_one,
    _Progress,
    connect_within,
    resolve_stream,
)


class _Clock:
    """A clock that moves only when something spends the budget."""

    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def spend(self, seconds: float) -> None:
        self.now += seconds


def _two_addresses(host: str, port: int) -> list[Any]:
    return [
        (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", port, 0, 0)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
    ]


def test_one_silent_address_does_not_spend_the_whole_fetch_budget() -> None:
    """The measured shape: a SYN goes out and nothing comes back.

    Before this cap, one unanswered address consumed the entire ten seconds
    waiting for a packet that measurement says was not coming, and the caller
    learned in ten seconds what it could have learned in two.
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
        )

    assert handed == [CONNECT_BUDGET_S, CONNECT_BUDGET_S], handed
    assert clock.now == 1004.0, "two capped attempts, not one ten-second wait"


def test_the_cap_never_exceeds_what_is_left_of_the_deadline() -> None:
    """F98 still binds. The cap bounds an attempt, the deadline bounds the fetch.

    With less than one cap remaining, the attempt gets the remainder rather
    than the cap, or a retry would run past the budget its caller set.
    """
    clock = _Clock()
    handed: list[float] = []

    def stalls(resolved: Any, budget: float) -> Any:
        handed.append(budget)
        clock.spend(budget)
        raise TimeoutError("timed out")

    with pytest.raises(OSError):
        connect_within(
            clock.now + 0.75,
            ("example.invalid", 443),
            resolve=_two_addresses,
            attempt=stalls,
            clock=clock,
        )

    assert handed == [0.75], handed


def test_a_working_connection_is_not_cut_off_by_the_cap() -> None:
    """The cap is thirty-six times the slowest success measured on the host.

    A cap that severed connections which were going to succeed would trade a
    measured failure for an invented one, and the invented one would be
    invisible: it looks exactly like the failure it replaced.
    """
    clock = _Clock()
    opened = object()

    def quick(resolved: Any, budget: float) -> Any:
        assert budget >= 0.055, f"a 55 ms connect must fit in {budget}"
        clock.spend(0.055)
        return opened

    assert connect_within(
        clock.now + 10.0,
        ("example.invalid", 443),
        resolve=_two_addresses,
        attempt=quick,
        clock=clock,
    ) is opened


def test_a_request_that_never_reached_the_far_end_is_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The measured case: 7 of 7 retries connected after an unanswered SYN."""
    seen: list[int] = []

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self, _cap: int) -> bytes:
            return b"second time"

    def flaky(request: Any, timeout_s: float, deadline: float,
              progress: Any = None) -> Any:
        seen.append(1)
        if len(seen) == 1:
            raise urllib.error.URLError("no answer")
        return _Response()

    monkeypatch.setattr("mavo.transport._open", flaky)
    assert UrllibTransport().fetch("https://example.invalid") == "second time"
    assert len(seen) == 2, seen


def test_a_request_that_reached_the_far_end_is_never_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The safety argument, and the whole of it.

    A request that connected may have been received and acted on, so repeating
    it is a decision about the far side rather than about our own timeout. That
    every fetch here is a `GET` does not make it safe: a `GET` that arrived is
    still a `GET` that arrived.
    """
    seen: list[int] = []

    def stalls_after_connecting(request: Any, timeout_s: float, deadline: float,
                                progress: Any = None) -> Any:
        seen.append(1)
        if progress is not None:
            progress.connected = True
        raise TimeoutError("read timed out")

    monkeypatch.setattr("mavo.transport._open", stalls_after_connecting)
    with pytest.raises(SourceUnavailable):
        UrllibTransport().fetch("https://example.invalid")
    assert len(seen) == 1, "a connected request must not be sent twice"


def test_a_retry_is_not_attempted_with_no_room_left_for_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A retry with two hundred milliseconds left is engineered to fail.

    It would report a second failure that measures the clock rather than the
    network, and this project counts refusals.
    """
    seen: list[int] = []

    def refuses(request: Any, timeout_s: float, deadline: float,
                progress: Any = None) -> Any:
        seen.append(1)
        raise urllib.error.URLError("no answer")

    monkeypatch.setattr("mavo.transport._open", refuses)
    with pytest.raises(SourceUnavailable):
        UrllibTransport(timeout_s=0.2).fetch("https://example.invalid")
    assert len(seen) == 1, seen


def test_the_refusal_says_how_many_attempts_it_made(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A journal line that hides a retry understates what the network cost.

    The count appears only when there was more than one, so the shape of every
    line written before this release is unchanged.
    """
    def refuses(request: Any, timeout_s: float, deadline: float,
                progress: Any = None) -> Any:
        raise urllib.error.URLError("no answer")

    monkeypatch.setattr("mavo.transport._open", refuses)
    with pytest.raises(SourceUnavailable) as refusal:
        UrllibTransport().fetch("https://example.invalid")
    assert "2 attempts" in str(refusal.value), str(refusal.value)


def test_the_worst_case_stays_inside_the_collection_interval() -> None:
    """Two capped connects plus the retry guard must fit inside 30 seconds.

    The collector fires every 30 s. A refusal path longer than that would let
    one poll overlap the next, which is a different failure from the one this
    release is repairing.
    """
    worst = CONNECT_BUDGET_S * (1 + CONNECT_RETRIES) * 2
    assert worst < 30.0, worst


def test_the_progress_record_starts_disconnected() -> None:
    """A record defaulting to connected would silently disable every retry."""
    assert _Progress().connected is False


# --------------------------------------------------------------------------
# F110. The address list has three entries per family, not one.
# --------------------------------------------------------------------------


def _stream_then_datagram(host: str, port: int) -> list[Any]:
    """What `getaddrinfo` actually returns, which is not what a stub returned.

    The regression that missed F110 handed `connect_within` two addresses and
    made both of them `SOCK_STREAM`, because that is what the author believed
    the resolver returns. It returns `SOCK_STREAM`, `SOCK_DGRAM` and
    `SOCK_RAW` for **each** family: six entries for a host with an A and an
    AAAA record. A fixture arranged from the implementation's belief rather
    than from the interface is how this survived eight releases.
    """
    return [
        (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", port, 0, 0)),
        (socket.AF_INET6, socket.SOCK_DGRAM, 17, "", ("::1", port, 0, 0)),
        (socket.AF_INET6, socket.SOCK_RAW, 0, "", ("::1", port, 0, 0)),
    ]


def test_a_datagram_address_is_refused_rather_than_connected() -> None:
    """`connect()` on UDP succeeds without connecting to anything.

    It negotiates nothing, so it returns immediately and hands back a socket
    that looks open. TLS then refuses it from inside the standard library with
    `NotImplementedError`, which is not an `OSError` and was caught by nobody.
    """
    clock = _Clock()

    with pytest.raises(OSError) as refusal:
        connect_within(
            clock.now + 10.0,
            ("example.invalid", 443),
            # The datagram entry alone, so the refusal names the kind under
            # test rather than whichever entry happened to be walked last.
            resolve=lambda host, port: _stream_then_datagram(host, port)[1:2],
            attempt=_attempt_one,
            clock=clock,
        )
    assert "SOCK_DGRAM" in str(refusal.value), str(refusal.value)


def test_the_default_resolver_asks_for_streams_only() -> None:
    """The repair at its source: six entries become two.

    Checked against the real resolver on a name that always resolves, because
    a test that stubs `getaddrinfo` here would be testing the stub.
    """
    every = socket.getaddrinfo("localhost", 443)
    kinds = {row[1] for row in every}
    assert socket.SOCK_DGRAM in kinds, "the premise of F110 no longer holds"

    streams = resolve_stream("localhost", 443)
    assert {row[1] for row in streams} == {socket.SOCK_STREAM}, streams


def test_a_capped_attempt_leaves_budget_and_that_is_what_exposed_this() -> None:
    """The mechanism, stated as a test rather than as a changelog line.

    Before the cap the first attempt spent the whole deadline, so the loop
    always broke on an exhausted budget and never reached a second entry. The
    latent defect was unreachable for eight releases for that reason alone.
    """
    clock = _Clock()
    reached: list[str] = []

    def stalls(resolved: Any, budget: float) -> Any:
        reached.append(resolved[1].name)
        clock.spend(budget)
        raise TimeoutError("timed out")

    with pytest.raises(OSError):
        connect_within(
            clock.now + 10.0,
            ("example.invalid", 443),
            resolve=_stream_then_datagram,
            attempt=stalls,
            clock=clock,
        )
    assert reached == ["SOCK_STREAM", "SOCK_DGRAM", "SOCK_RAW"], reached
    assert clock.now == 1006.0, "three capped attempts, not one ten-second wait"


def test_an_unforeseen_exception_still_leaves_fetch_as_a_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The whole of F110's damage was one exception nobody had listed.

    `NotImplementedError` is a `RuntimeError`, so it passed through the fetch,
    through `_cmd_collect`'s handler, and out of the process: 168 polls died
    with a traceback and exit 1 where the contract says 3. The type is named
    in the message so that widening the net does not also hide what happened.
    """
    def surprises(request: Any, timeout_s: float, deadline: float,
                  progress: Any = None) -> Any:
        raise NotImplementedError("only stream sockets are supported")

    monkeypatch.setattr("mavo.transport._open", surprises)
    with pytest.raises(SourceUnavailable) as refusal:
        UrllibTransport().fetch("https://example.invalid")
    assert "NotImplementedError" in str(refusal.value), str(refusal.value)


def test_an_unforeseen_exception_is_not_worth_a_second_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Narrow where it decides a retry, wide where it decides a refusal.

    An exception nobody predicted is not evidence that trying again would go
    better, and a retry on a programming error doubles the cost of finding it.
    """
    seen: list[int] = []

    def surprises(request: Any, timeout_s: float, deadline: float,
                  progress: Any = None) -> Any:
        seen.append(1)
        raise NotImplementedError("only stream sockets are supported")

    monkeypatch.setattr("mavo.transport._open", surprises)
    with pytest.raises(SourceUnavailable):
        UrllibTransport().fetch("https://example.invalid")
    assert len(seen) == 1, seen
