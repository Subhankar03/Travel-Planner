"""LangGraph state definition for the Travel Planner agent."""
from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


# ── State ──────────────────────────────────────────────────────────────────────
class TravelState(TypedDict):
    """Shared state across all agents in the graph."""

    # Chat history (automatically appended via `add_messages` reducer)
    messages: Annotated[list, add_messages]

    # Structured trip context produced by the Booking Agent
    itinerary: dict[str, Any] | None

    # Next agent to route to (set by Supervisor)
    next: str
