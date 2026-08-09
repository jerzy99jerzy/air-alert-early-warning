"""Sprint 5 regression: the source layer must not lie about what it saw.

Two defects found by reading real channel content in 0.3.1.0, both in the same
class. F26: a message announces an all-clear and says the alert continues, and a
three-state model has nowhere to put it, so it would resolve to CLEAR. F27: the
page is a twenty-message window, so messages can pass between polls without
leaving a trace, and an unmeasured gap would read as no gap.

Neither is fixed by classifying better. Both are fixed by having a state, and a
count, for the case the model previously could not express.
"""

from __future__ import annotations

from mavo.schema import AlertState, is_actionable, is_clear
from mavo.sources.telegram import TelegramChannelSource, classify_state
from mavo.transport import StubTransport

TXT = '<div class="tgme_widget_message_text js-message_text">'

PARTIAL = (
    "🟡 15:53 Відбій тривоги в Куп'янський район.\n"
    "Зверніть увагу, тривога ще триває у:\n- Куп'янський район"
)
PLAIN_CLEAR = "🟢 15:53 Відбій тривоги в Чугуївський район."
PLAIN_ACTIVE = "🔴 15:44 Повітряна тривога в Павлоградський район"


def _page(ids: list[int]) -> str:
    """A channel page carrying the given post ids, one message each."""
    return "".join(
        f'<div class="tgme_widget_message" data-post="air_alert_ua/{post_id}">'
        f'<time datetime="2026-09-01T21:0{index}:00+00:00"></time>'
        f"{TXT}Львівська область<br/>Повітряна тривога</div></div>"
        for index, post_id in enumerate(ids)
    )


# --- F26, the fourth state ---------------------------------------------------

def test_f26_a_partial_all_clear_is_its_own_state() -> None:
    assert classify_state(PARTIAL) is AlertState.PARTIAL_CLEAR


def test_f26_a_partial_all_clear_never_resolves_to_clear() -> None:
    # The whole point. Before this sprint the clear marker matched and the
    # continuation went unread, which is the flattering reading of the two.
    state = classify_state(PARTIAL)
    assert state is not None
    assert is_clear(state) is False
    assert is_actionable(state) is False


def test_f26_an_ordinary_all_clear_is_still_clear() -> None:
    # A new state earns nothing if it swallows the case it was carved out of.
    assert classify_state(PLAIN_CLEAR) is AlertState.CLEAR
    assert classify_state(PLAIN_ACTIVE) is AlertState.ACTIVE


def test_f26_the_state_layer_is_measurable_without_the_area_layer() -> None:
    # The state layer was correct on real content (15 of 20) and could only be
    # exercised through a conjunct that matches nothing. Splitting it out is
    # what makes this sprint's assertions possible at all.
    assert classify_state("wording nobody anticipated") is None


# --- F27, the window ---------------------------------------------------------

def test_f27_a_skipped_window_is_counted() -> None:
    source = TelegramChannelSource(StubTransport(_page([100, 101, 102])))
    source.poll()
    source.transport = StubTransport(_page([110, 111]))
    source.poll()
    # 103 to 109 passed unseen. Seven messages, reported rather than inferred
    # from the absence of events.
    assert source.report.skipped == 7
    assert source.report.gap_is_known is True


def test_f27_contiguous_polls_report_no_gap() -> None:
    source = TelegramChannelSource(StubTransport(_page([100, 101])))
    source.poll()
    source.transport = StubTransport(_page([102, 103]))
    source.poll()
    assert source.report.skipped == 0


def test_f27_the_first_poll_reports_unknown_not_zero() -> None:
    # There is no baseline on a first poll. Zero would be a claim; None is the
    # truth, and this is the same defect class as unknown resolving to clear.
    source = TelegramChannelSource(StubTransport(_page([100, 101])))
    source.poll()
    assert source.report.skipped is None
    assert source.report.gap_is_known is False
    assert source.report.window_line() == "skipped=unknown"


def test_f27_a_page_without_post_ids_reports_unknown_not_zero() -> None:
    # A restructured or hostile page loses the only observable that makes a skip
    # visible. Losing the observable must not look like observing continuity.
    source = TelegramChannelSource(StubTransport(f"{TXT}Львів тривога</div>"))
    source.poll()
    assert source.report.skipped is None
    assert source.report.first_id is None


def test_f27_a_repeated_page_does_not_invent_a_gap() -> None:
    body = _page([100, 101, 102])
    source = TelegramChannelSource(StubTransport(body))
    source.poll()
    source.poll()
    assert source.report.skipped == 0
