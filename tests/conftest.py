"""Shared fixtures. No credential ever appears here; one would be generated."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind

T0 = datetime(2026, 3, 1, 22, 0, 0, tzinfo=UTC)


@pytest.fixture
def event() -> ThreatEvent:
    return ThreatEvent(
        area_id="lviv",
        state=AlertState.ACTIVE,
        ts_source=T0,
        ts_ingest=T0 + timedelta(seconds=45),
        source_id="test",
        kind=ThreatKind.MISSILE,
        provenance=Provenance.REPORTED,
    )


@pytest.fixture
def store_path(tmp_path: Path) -> Iterator[Path]:
    yield tmp_path / "events.sqlite"
