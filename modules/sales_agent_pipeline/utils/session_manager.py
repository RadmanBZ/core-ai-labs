import re
from dataclasses import dataclass

from modules.sales_agent_pipeline.core.sandbox_engine import (
    extract_customer_identity,
    has_introduction_marker,
)
from modules.sales_agent_pipeline.models import PipelineState

NEW_SESSION_COMMANDS = frozenset({"/new", "/reset", "/session"})


@dataclass(frozen=True)
class SessionRoutingDecision:
    should_cycle: bool
    incoming_identity: str | None
    reason: str


def format_session_label(session_id: str) -> str:
    """Render a dashboard-friendly session hash label."""
    return f"RZ-{session_id[:6].upper()}"


def is_new_session_command(user_input: str) -> bool:
    return user_input.strip().lower() in NEW_SESSION_COMMANDS


def _normalize_identity(name: str) -> str:
    collapsed = re.sub(r"\s+", " ", name.strip())
    return collapsed.casefold() if collapsed.isascii() else collapsed


def identities_match(left: str | None, right: str | None) -> bool:
    """Compare lead identities with tolerant matching for partial English names."""
    if not left or not right:
        return False

    normalized_left = _normalize_identity(left)
    normalized_right = _normalize_identity(right)
    if normalized_left == normalized_right:
        return True

    if normalized_left.isascii() and normalized_right.isascii():
        return (
            normalized_left in normalized_right
            or normalized_right in normalized_left
        )

    return False


def _active_lead_established(state: PipelineState) -> bool:
    return bool(
        state.extracted_data.customer_name
        or state.conversation_history
        or state.evaluation is not None
    )


def evaluate_session_routing(state: PipelineState, user_input: str) -> SessionRoutingDecision:
    """
    Enterprise session router — inspect inbound text before any agent execution.
    Cycles whenever a new self-introduction conflicts with the active lead identity.
    """
    if is_new_session_command(user_input):
        return SessionRoutingDecision(True, None, "manual /new command")

    incoming_identity = extract_customer_identity(user_input)
    current_identity = state.extracted_data.customer_name
    intro_detected = has_introduction_marker(user_input)

    if incoming_identity and current_identity:
        if not identities_match(incoming_identity, current_identity):
            return SessionRoutingDecision(
                True,
                incoming_identity,
                f"identity shift: {current_identity} -> {incoming_identity}",
            )

    if _active_lead_established(state) and intro_detected and incoming_identity:
        if not current_identity or not identities_match(incoming_identity, current_identity):
            return SessionRoutingDecision(
                True,
                incoming_identity,
                f"context shift introduction: {incoming_identity}",
            )

    if _active_lead_established(state) and incoming_identity and not current_identity:
        return SessionRoutingDecision(
            True,
            incoming_identity,
            f"late-bound identity lock: {incoming_identity}",
        )

    return SessionRoutingDecision(False, incoming_identity, "continue active session")


def should_cycle_session(state: PipelineState, user_input: str) -> bool:
    """Backward-compatible boolean wrapper around the routing evaluator."""
    return evaluate_session_routing(state, user_input).should_cycle
