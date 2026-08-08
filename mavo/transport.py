"""The only place in the package that reaches the network.

Isolated behind a protocol so every adapter is testable without a network, and
so a reader can answer "what can this thing talk to" by reading one file.

Convention borrowed from `pirx`: the adapter is tested against an injected
transport, and the limit of that testing is stated rather than implied. That a
live service returns what the tests assume is **not** tested here.
"""

from __future__ import annotations

import urllib.error
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

    def fetch(self, url: str) -> str:
        """Return the document body as text.

        Raises ``SourceUnavailable`` and nothing else. A transport that leaks a
        library-specific exception forces every caller to know which library is
        underneath, which is the coupling this protocol exists to prevent.
        """
        ...


class UrllibTransport:
    """Standard-library transport. No third-party dependency to audit."""

    def __init__(self, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        self.timeout_s = timeout_s

    def fetch(self, url: str) -> str:
        """Fetch ``url``, capped in size and time."""
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw = response.read(MAX_BYTES + 1)
        except (urllib.error.URLError, OSError, ValueError) as failure:
            raise SourceUnavailable(f"{url}: {failure}") from failure
        if len(raw) > MAX_BYTES:
            raise SourceUnavailable(f"{url}: response exceeds {MAX_BYTES} bytes")
        body: str = bytes(raw).decode("utf-8", errors="replace")
        return body


class StubTransport:
    """Returns a fixed body. For tests, and for `mavo collect --stub`."""

    def __init__(self, body: str) -> None:
        self.body = body
        self.calls = 0

    def fetch(self, url: str) -> str:
        """Return the canned body, counting calls."""
        self.calls += 1
        return self.body


class FailingTransport:
    """Always refuses. Models an unreachable source, distinct from a quiet one."""

    def fetch(self, url: str) -> str:
        """Always raise ``SourceUnavailable``."""
        raise SourceUnavailable(f"{url}: injected failure")
