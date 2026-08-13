"""The only place in the package that reaches the network.

Isolated behind a protocol so every adapter is testable without a network, and
so a reader can answer "what can this thing talk to" by reading one file.

Convention borrowed from `pirx`: the adapter is tested against an injected
transport, and the limit of that testing is stated rather than implied. That a
live service returns what the tests assume is **not** tested here.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Protocol, runtime_checkable

from mavo import __version__
from mavo.errors import SourceUnavailable

# Derived from the package version rather than typed here. A version string
# duplicated outside its single source of truth drifts on the first bump it is
# not part of, which is exactly how this constant shipped saying 0.3.0.0 at
# 0.3.1.0 (F36).
USER_AGENT = f"mavo/{__version__} (+https://github.com/jerzy99jerzy)"
DEFAULT_TIMEOUT_S = 10.0
MAX_BYTES = 4_000_000


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
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw = response.read(MAX_BYTES + 1)
        except (urllib.error.URLError, OSError, ValueError) as failure:
            # T55. The refusal carries how long it waited and what was raised,
            # because without them a stall that hit the ten-second ceiling and
            # a rejection that bounced in twenty milliseconds are the same line
            # in a journal. Eleven refusals were logged over one night before
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
