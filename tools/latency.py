#!/usr/bin/env python3
"""Moved into the package at 0.54.0.0 (D-038, T84). This shim is the
forwarding address, kept for one thing only: a command line somebody wrote
down before the move keeps working, and prints where the instrument now lives.
The discriminator that moved it is the one that moved `attempts.py` a release
earlier: this reads the **store**, so it must run where the store is, and
`tools/` is never installed. Everything else in `tools/` reads the tree and
stays, which `tests/lint_domain.py` now checks rather than trusts.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mavo.latency import main  # noqa: E402,F401

if __name__ == "__main__":
    print("note: this instrument ships in the package now; prefer `mavo latency`",
          file=sys.stderr)
    sys.exit(main())
