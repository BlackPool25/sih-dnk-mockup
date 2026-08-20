"""Quote state machine — exhaustive match, versioned draft→sent→counter→approved→paid_held."""

from __future__ import annotations

from typing import Final, Literal

QuoteStateLiteral = Literal["draft", "sent", "counter", "approved", "paid_held"]
QuoteTransition = Literal["send", "reject", "revise", "approve", "pay"]

ALLOWED_TRANSITIONS: Final[dict[QuoteStateLiteral, set[QuoteTransition]]] = {
    "draft": {"send"},
    "sent": {"reject", "approve"},
    "counter": {"revise", "approve"},
    "approved": {"pay"},
    "paid_held": set(),
}

# State resulting from each transition
TRANSITION_TARGET: Final[dict[QuoteTransition, QuoteStateLiteral]] = {
    "send": "sent",
    "reject": "counter",
    "revise": "sent",
    "approve": "approved",
    "pay": "paid_held",
}


class QuoteStateError(ValueError):
    """Raised when a transition is not allowed from the current state."""

    def __init__(self, current: str, transition: str) -> None:
        super().__init__(f"Cannot '{transition}' from state '{current}'")
        self.current = current
        self.transition = transition


def assert_transition_allowed(current: QuoteStateLiteral, transition: QuoteTransition) -> None:
    """Validate transition using exhaustive match — no if/elif chains."""
    allowed: set[QuoteTransition]
    match current:
        case "draft":
            allowed = ALLOWED_TRANSITIONS["draft"]
        case "sent":
            allowed = ALLOWED_TRANSITIONS["sent"]
        case "counter":
            allowed = ALLOWED_TRANSITIONS["counter"]
        case "approved":
            allowed = ALLOWED_TRANSITIONS["approved"]
        case "paid_held":
            allowed = ALLOWED_TRANSITIONS["paid_held"]
        case _:  # pyright: ignore[reportUnnecessaryComparison]
            raise QuoteStateError(str(current), transition)
    if transition not in allowed:
        raise QuoteStateError(current, transition)


def next_state(current: QuoteStateLiteral, transition: QuoteTransition) -> QuoteStateLiteral:
    """Return next state after validating transition."""
    assert_transition_allowed(current, transition)
    match transition:
        case "send":
            return "sent"
        case "reject":
            return "counter"
        case "revise":
            return "sent"
        case "approve":
            return "approved"
        case "pay":
            return "paid_held"


def is_terminal(state: QuoteStateLiteral) -> bool:
    """paid_held is terminal — no further transitions."""
    match state:
        case "paid_held":
            return True
        case "draft" | "sent" | "counter" | "approved":
            return False
