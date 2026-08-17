"""T23: the sink is attached to the live loop, and its absence is detectable.

`publish` has accepted a `log` since the sink shipped at 0.23.0.0 and no caller
ever passed one. `mavo/report.py` imported `RunLog` and used it as the type of
a parameter nothing filled; `mavo.obs.from_environment` had no caller anywhere
in the package; the production unit set `MAVO_LOG_FILE` and no file was ever
written. Every place a person would look reported healthy. That is F103.

The repair is one argument. **These tests are the part that matters**, because
the defect was never that the sink was wrong: it was that the sink was absent,
and no criterion in `docs/OBSERVABILITY.md` section 9 could tell those apart.
A test asserting the log's contents passes vacuously when there is no log to
read only if it is written carelessly; each one here fails when nothing writes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mavo.cli import main


def _store(tmp_path: Path) -> Path:
    """An empty store. The loop publishes blindness, which is still a cycle."""
    return tmp_path / "events"


def _run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, log: Path | None,
    cycles: int = 2,
) -> int:
    if log is None:
        monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    else:
        monkeypatch.setenv("MAVO_LOG_FILE", str(log))
    return main([
        "report",
        "--store", str(_store(tmp_path)),
        "--json", str(tmp_path / "state.json"),
        "--watch",
        "--interval", "0",
        "--max-cycles", str(cycles),
    ])


def test_the_loop_writes_the_run_log_the_environment_names(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The whole of F103, as an assertion.

    Red against the tree at 0.32.6.0: the file is never created, because
    nothing constructs the sink. This is the test whose absence let a
    configured, documented, 98%-covered module go uncalled for nine releases.
    """
    target = tmp_path / "run.jsonl"
    _run(monkeypatch, tmp_path, log=target)
    assert target.exists(), (
        "MAVO_LOG_FILE names a path and the loop wrote nothing to it; this is "
        "the state the production host was in while every other indicator "
        "reported healthy"
    )
    records = [json.loads(line) for line
               in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert records, "the sink was created and never written to, which is F103 again"
    # Asserting on `publish.cycle` and not merely on the file being non-empty.
    # `RunLog.__init__` writes its own first line stating the retention policy,
    # so a sink constructed and then handed to nobody still produces a file
    # with content in it. The first version of this test asserted `lines` and
    # passed against a tree with the wiring removed, which would have made it a
    # test of the sink's constructor wearing the name of a test of the loop.
    assert any(record.get("event") == "publish.cycle" for record in records), (
        "the log holds no cycle record; the sink exists and the loop is not "
        "writing to it"
    )


def test_every_cycle_reaches_the_log(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A log carrying one cycle out of three is worse than none.

    The count is the property an operator reads to answer "did the loop run",
    so a sink attached to only the first iteration would satisfy the test above
    and lie about exactly the question the log exists for.
    """
    target = tmp_path / "run.jsonl"
    _run(monkeypatch, tmp_path, log=target, cycles=3)
    records = [json.loads(line) for line
               in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    cycles = {record["cycle"] for record in records if record.get("cycle")}
    assert len(cycles) == 3, f"three cycles ran and the log names {len(cycles)}"


def test_no_environment_variable_means_no_file_and_no_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`from_environment` returns `None` and the loop runs without a log.

    The sink is instrumentation, not a dependency. A loop that refused to
    publish because nobody asked for a diagnostic would have turned an
    observability feature into an outage.
    """
    assert _run(monkeypatch, tmp_path, log=None) == 0
    assert not (tmp_path / "run.jsonl").exists()


def test_the_operator_is_told_where_the_log_went(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Announced on stdout, because a silent sink is how F103 stayed hidden.

    An operator who set the variable and sees no mention of it on startup can
    tell within one line that it did not take, rather than discovering it by
    looking for a file three days later.
    """
    target = tmp_path / "run.jsonl"
    _run(monkeypatch, tmp_path, log=target)
    assert f"run-log={target}" in capsys.readouterr().out


def test_the_sink_is_constructed_by_the_caller_and_not_inside_publish() -> None:
    """`publish` must not reach into the environment for its own instrument.

    A function that builds its own sink from `os.environ` cannot be run without
    one in a test, and the decision to operate without a log stops being
    visible at the call site. `from_environment` returns `None` rather than a
    no-op writer for the same reason, and that reasoning is only honoured if
    the call stays in the CLI.
    """
    source = (Path(__file__).resolve().parent.parent
              / "mavo" / "report.py").read_text(encoding="utf-8")
    assert "from_environment" not in source
