"""S9's observability layer, against the acceptance written before the code.

`docs/OBSERVABILITY.md` section 9 lists seven criteria. Five are testable
without a delivery path and are here. Two are not, and saying which is part of
the sprint being declared partial rather than rounded up:

- **"A refused poll produces a degradation notification within one cycle"**
  needs a notifier, which is S10. The publishing loop's blindness accounting
  already exists and is tested in `test_sprint10.py`; the notification does
  not.
- **"tools/progress.py replaying a finished file produces the same recap the
  live view produced"** needs a live view. There is no channel-polling loop
  yet - `mavo watch` waits on T25, which is a decision rather than an
  implementation - so there is no second rendering to agree with. The reader is
  tested against files instead.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from mavo.obs import LOG_BODIES, SCHEMA, RunLog, Unknown, from_environment

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.progress import read  # noqa: E402


def _lines(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_an_unmeasurable_quantity_is_null_with_a_reason_never_zero(
    tmp_path: Path,
) -> None:
    """The criterion this whole module exists to satisfy.

    A stage that could not measure emits `null` beside a `*_reason`, and the
    renderer prints `unknown`. A rendering containing `skipped=0` fails.
    Mutation: make `Unknown` serialise to 0, or drop the reason.
    """
    log = RunLog(tmp_path / "run.jsonl")
    log.line(
        "parse", "parse.report", cycle="7f2a1c", messages=20, parsed=20,
        skipped=Unknown("first_poll_has_no_baseline"),
    )
    record = _lines(tmp_path / "run.jsonl")[-1]
    assert record["skipped"] is None
    assert record["skipped_reason"] == "first_poll_has_no_baseline"

    rendered = read(tmp_path / "run.jsonl").render()
    assert "first_poll_has_no_baseline" in rendered
    assert "skipped=0" not in rendered


def test_a_bare_none_never_reaches_the_line(tmp_path: Path) -> None:
    """A null with no reason beside it is dropped rather than written.

    This is the mechanism behind the rule above: if a bare `None` could be
    written, a consumer would eventually meet one and guess. Mutation: keep
    `None` values in `_compose`.
    """
    log = RunLog(tmp_path / "run.jsonl")
    log.line("fetch", "fetch.done", cycle="a1", bytes_read=None, ms=4)
    record = _lines(tmp_path / "run.jsonl")[-1]
    assert "bytes_read" not in record, "a null with no reason must not be written"


def test_the_sink_carries_no_message_text_by_default(tmp_path: Path) -> None:
    """T24, and the fourth acceptance criterion.

    A hostile fixture carrying a recognisable token in every body must not
    produce that token anywhere in the file. The design and holdout split was
    frozen before any content was read (D-012a), and a log that echoes bodies
    spends it without anyone deciding to. Mutation: drop the BODY_FIELDS
    redaction.
    """
    token = "HOLDOUT-CANARY-9f31"
    log = RunLog(tmp_path / "run.jsonl", allow_bodies=False)
    for field in ("text", "body", "message", "raw", "sample", "unparsed"):
        log.line("parse", "parse.failed", cycle="a1", **{field: f"{token} {field}"})
    contents = (tmp_path / "run.jsonl").read_text(encoding="utf-8")
    assert token not in contents
    assert "bodies_not_logged" in contents, "the redaction must be visible, not silent"


def test_enabling_bodies_leaves_a_mark_in_the_record_it_weakened(
    tmp_path: Path,
) -> None:
    """A switch that disables an evidential guarantee is itself logged.

    Otherwise a log written with bodies on is indistinguishable, to a later
    reader, from one written with them off - and the difference is whether the
    file may contain holdout content. Mutation: drop the `sink.bodies_enabled`
    line.
    """
    log = RunLog(tmp_path / "run.jsonl", allow_bodies=True)
    log.line("parse", "parse.failed", cycle="a1", text="a real body")
    events = [record["event"] for record in _lines(tmp_path / "run.jsonl")]
    assert "sink.bodies_enabled" in events
    recap = read(tmp_path / "run.jsonl")
    assert recap.bodies_enabled
    assert "MAVO_LOG_BODIES=1" in recap.render()


def test_the_retention_policy_is_stated_in_the_sinks_own_first_line(
    tmp_path: Path,
) -> None:
    """A reader holding one file must learn the policy from that file.

    A log that silently dropped its oldest evidence would let a post-mortem
    read a partial history as a complete one. Mutation: remove the
    `sink.opened` line.
    """
    RunLog(tmp_path / "run.jsonl", max_bytes=4096, retain=3)
    first = _lines(tmp_path / "run.jsonl")[0]
    assert first["event"] == "sink.opened"
    assert first["rotation"] == "rename"
    assert first["retain"] == 3
    assert first["v"] == SCHEMA


def test_a_fragment_with_no_opened_line_says_so_rather_than_guessing(
    tmp_path: Path,
) -> None:
    """A file that does not start at the run's start must not read as if it did."""
    target = tmp_path / "fragment.jsonl"
    target.write_text(
        json.dumps({"v": 1, "ts": "z", "stage": "parse", "event": "parse.report"}) + "\n",
        encoding="utf-8",
    )
    assert "retention: unknown" in read(target).render()


def test_rotation_renames_so_no_evidence_is_truncated_away(tmp_path: Path) -> None:
    """Rotation moves the old file aside; it never truncates it.

    Mutation: rotate by truncating in place. The sibling then does not exist
    and the older lines are gone.
    """
    target = tmp_path / "run.jsonl"
    log = RunLog(target, max_bytes=800, retain=2)
    for index in range(60):
        log.line("publish", "publish.cycle", cycle=f"c{index}", written=index)
    assert target.with_suffix(".jsonl.1").is_file(), "the old file was not kept"
    older = _lines(target.with_suffix(".jsonl.1"))
    assert any(record.get("event") == "publish.cycle" for record in older)


def test_a_truncated_tail_is_reported_as_a_gap_not_skipped(tmp_path: Path) -> None:
    """F51's shape, on the reading side.

    The sink writes whole lines, so a partial one means something outside it
    cut the file. Dropping it silently would turn evidence of a problem into an
    absence of evidence. Mutation: ignore an unparseable final line.
    """
    target = tmp_path / "run.jsonl"
    log = RunLog(target)
    log.line("publish", "publish.cycle", cycle="a1", written=1)
    with target.open("a", encoding="utf-8") as handle:
        handle.write('{"v":1,"stage":"publish","eve')
    recap = read(target)
    assert recap.truncated_tail
    assert "GAP:" in recap.render()


def test_a_line_is_whole_or_absent_after_an_abrupt_death(tmp_path: Path) -> None:
    """F51 asserted against a killed process rather than described.

    A child writes lines and is killed without a chance to flush. Every line in
    the file must parse; a buffered writer would leave a half-record here.
    Mutation: write through a buffered handle instead of one `os.write` on an
    O_APPEND descriptor.
    """
    target = tmp_path / "run.jsonl"
    script = (
        "import sys, time\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "from mavo.obs import RunLog\n"
        f"log = RunLog({str(target)!r})\n"
        "n = 0\n"
        "while True:\n"
        "    log.line('publish', 'publish.cycle', cycle='c%d' % n, written=n)\n"
        "    n += 1\n"
        "    time.sleep(0.001)\n"
    )
    child = subprocess.Popen([sys.executable, "-c", script])
    time.sleep(0.3)
    child.kill()
    child.wait(timeout=5)
    text = target.read_text(encoding="utf-8")
    assert text, "the child wrote nothing; the test measured nothing"
    for line in text.splitlines():
        if line.strip():
            json.loads(line)  # raises if any line is half-written
    assert read(target).truncated_tail is False


def test_console_verbosity_cannot_change_the_sink(tmp_path: Path) -> None:
    """The first acceptance criterion, and it is structural here.

    The sink takes no verbosity argument at all, so two runs over identical
    input produce identical JSONL by construction rather than by discipline.
    The test asserts the structure that makes it true, because a later
    refactor adding a level to `RunLog.line` would be the thing to catch.
    """
    import inspect

    parameters = inspect.signature(RunLog.__init__).parameters
    assert "verbosity" not in parameters and "quiet" not in parameters
    first, second = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    for target in (first, second):
        log = RunLog(target, now=lambda: __import__("datetime").datetime(
            2026, 8, 11, tzinfo=__import__("datetime").UTC))
        log.line("parse", "parse.report", cycle="fixed", messages=20, parsed=20)
    assert first.read_bytes() == second.read_bytes()


def test_no_log_file_means_no_sink_rather_than_a_silent_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`from_environment` returns None, not a no-op writer.

    A silent null object lets a run believe it is recording when it is not,
    which is the failure mode this whole module is against. Mutation: return a
    do-nothing RunLog.
    """
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    assert from_environment() is None
    monkeypatch.setenv("MAVO_LOG_FILE", str(tmp_path / "run.jsonl"))
    assert isinstance(from_environment(), RunLog)


def test_an_unknown_stage_is_refused_at_the_writer(tmp_path: Path) -> None:
    """STAGES is the vocabulary, and the reader imports it from here.

    A stage invented at a call site would render as a column the reader does
    not count, so the run would look smaller than it was.
    """
    log = RunLog(tmp_path / "run.jsonl")
    with pytest.raises(ValueError, match="unknown stage"):
        log.line("guessing", "some.event")


def test_an_unknown_without_a_reason_cannot_be_constructed() -> None:
    """"Unknown" with no explanation is the shape that gets read as zero."""
    with pytest.raises(ValueError, match="reason"):
        Unknown("")


def test_the_timer_records_a_stage_that_raised(tmp_path: Path) -> None:
    """A record that exists only for the happy path is a record of that path."""
    log = RunLog(tmp_path / "run.jsonl")
    with pytest.raises(OSError, match="upstream gone"), log.timed(
        "fetch", "fetch.done", cycle="a1"
    ):
        raise OSError("upstream gone")
    record = _lines(tmp_path / "run.jsonl")[-1]
    assert record["level"] == "ERROR"
    assert record["error"] == "OSError"
    assert isinstance(record["ms"], int)


def test_bodies_are_refused_even_when_the_environment_asks_but_the_caller_says_no(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit argument beats the environment, in the safe direction."""
    monkeypatch.setenv(LOG_BODIES, "1")
    log = RunLog(tmp_path / "run.jsonl", allow_bodies=False)
    log.line("parse", "parse.failed", cycle="a1", text="CANARY")
    assert "CANARY" not in (tmp_path / "run.jsonl").read_text(encoding="utf-8")


def test_the_pipeline_does_not_import_the_reader() -> None:
    """The seventh criterion, asserted here as well as in the domain lint.

    Two readers of one rule, deliberately: the lint runs in `make verify` and
    this runs in the suite, and a rule enforced in one place is a rule that
    survives exactly as long as that place does.
    """
    offenders = [
        module.relative_to(ROOT)
        for module in sorted((ROOT / "mavo").rglob("*.py"))
        if "tools.progress" in module.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_the_reader_reports_a_newer_schema_rather_than_reinterpreting_it(
    tmp_path: Path,
) -> None:
    """A line from a future version is counted and left alone."""
    target = tmp_path / "run.jsonl"
    target.write_text(
        json.dumps({"v": SCHEMA + 1, "stage": "publish", "event": "publish.cycle"})
        + "\n",
        encoding="utf-8",
    )
    assert read(target).future_schema == 1
    assert "newer than" in read(target).render()

