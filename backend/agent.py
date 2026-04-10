"""LangGraph multi-agent workflow for the Travel Planner."""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal
import warnings

import requests
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from backend.state import TravelState
from backend.tools import (
    search_flights,
    search_hotels,
    search_local_places,
    get_route_directions,
)

load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning)


# ── Load prompts and LLMs
_PROMPT_DIR = Path(__file__).parent / "prompts"
_compiled_graph: CompiledStateGraph | None = None
_checkpointer: MemorySaver | None = None

supervisor_template = (_PROMPT_DIR / "supervisor.md").read_text(encoding="utf-8")
booking_template = (_PROMPT_DIR / "booking_agent.md").read_text(encoding="utf-8")
research_template = (_PROMPT_DIR / "research_agent.md").read_text(encoding="utf-8")
supported_locations = (
    _PROMPT_DIR.parent / "serpapi_schemas" / "locations.csv"
).read_text(encoding="utf-8")

# supervisor_model = ChatNVIDIA(
#     model='nvidia/nemotron-3-nano-30b-a3b',
#     api_key=os.getenv('NVIDIA_API_KEY'),
#     chat_template_kwargs={'enable_thinking': False}
# )
supervisor_model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview")
specialist_model = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview", thinking_level="low"
)


# ── Helpers ────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_current_location() -> str:
    """Get the user's current location via IP-based geolocation."""
    try:
        response = requests.get(
            "https://ipinfo.io/json", headers={"User-Agent": "Mozilla/5.0"}, timeout=5
        )
        response.raise_for_status()
        data = response.json()
        city = data.get("city", "Unknown City")
        region = data.get("region", "Unknown Region")
        return f"{city}, {region}"
    except requests.RequestException, ValueError:
        return "Unknown Location"


def _prefix_response(response: AIMessage, agent_name: str) -> None:
    """Wrap the response content with agent identifiers in-place."""
    if not response.content:
        return

    prefix = f"[AGENT: {agent_name}]\n"
    suffix = "\n[END AGENT]"

    if isinstance(response.content, str):
        response.content = f"{prefix}{response.content}{suffix}"
        return

    if not isinstance(response.content, list) or not response.content:
        return

    # Handle list-based content (e.g., multi-modal or block-based)
    text_parts = [
        p for p in response.content if isinstance(p, dict) and p.get("type") == "text"
    ]
    if text_parts:
        text_parts[0]["text"] = f"{prefix}{text_parts[0]['text']}"
        text_parts[-1]["text"] = f"{text_parts[-1]['text']}{suffix}"


class SupervisorDecision(BaseModel):
    """The structured decision output for the supervisor."""

    route: Literal["booking_agent", "research_agent", "DIRECT_RESPONSE"] = Field(
        description="The next step in the workflow."
    )
    response: str | None = Field(
        default=None,
        description="If you choose 'DIRECT_RESPONSE', write your response here.",
    )


def supervisor_node(state: TravelState) -> dict:
    """Supervisor decides which specialist agent should handle the request."""

    # Identify user location (from state or IP fallback)
    location = state.get("user_location") or get_current_location()

    routing_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(supervisor_template),
            MessagesPlaceholder("messages"),
            HumanMessage(
                name="system",
                content="""**system:**
Review the conversation and route to the correct agent.
If all needs are addressed in the user request, choose "DIRECT_RESPONSE" and give your final answer.""",
            ),
        ]
    )

    supervisor_with_structure = supervisor_model.with_structured_output(
        SupervisorDecision
    )

    decision = supervisor_with_structure.invoke(
        routing_prompt.invoke(
            {
                "messages": state["messages"],
                "location": location,
            }
        )
    )

    route = getattr(decision, "route")
    if route == "DIRECT_RESPONSE":
        return {
            "next": "DIRECT_RESPONSE",
            "messages": [
                AIMessage(name="supervisor", content=getattr(decision, "response", ""))
            ],
        }
    return {"next": route}


def booking_agent_node(state: TravelState) -> dict:
    """Booking agent: finds flights and hotels."""
    model_with_tools = specialist_model.bind_tools([search_flights, search_hotels])

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(booking_template),
            MessagesPlaceholder("messages"),
            HumanMessage(
                name="system",
                content="""**system:**
Search for the flights and/or hotels requested. 
Once you have results, respond directly with a structured summary and recommendation.""",
            ),
        ]
    )

    # Identify user location (from state or IP fallback)
    location = state.get("user_location") or get_current_location()

    response = model_with_tools.invoke(
        prompt.invoke(
            {
                "today": datetime.now().strftime("%A, %Y-%m-%d"),
                "location": location,
                "messages": state["messages"],
            }
        )
    )

    _prefix_response(response, "booking_agent")
    response.name = "booking_agent"

    return {"messages": [response]}


def research_agent_node(state: TravelState) -> dict:
    """Research agent: finds local restaurants and attractions, and gets directions."""
    model_with_tools = specialist_model.bind_tools(
        [search_local_places, get_route_directions]
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(research_template),
            MessagesPlaceholder("messages"),
            HumanMessage(
                name="system",
                content="""**system:**
Search for the restaurants, attractions, or directions requested. 
Once you have results, respond directly with a structured summary and recommendation.""",
            ),
        ]
    )
    # Identify user location (from state or IP fallback)
    location = state.get("user_location") or get_current_location()

    response = model_with_tools.invoke(
        prompt.invoke(
            {
                "today": datetime.now().strftime("%A, %Y-%m-%d"),
                "location": location,
                "supported_locations": supported_locations,
                "messages": state["messages"],
            }
        )
    )

    _prefix_response(response, "research_agent")
    response.name = "research_agent"

    return {"messages": [response]}


# ── Routing Logic ──────────────────────────────────────────────────────────────
def route_supervisor(state: TravelState) -> str:
    """Route based on the supervisor's decision stored in state."""
    next_agent = state.get("next", "DIRECT_RESPONSE")
    if next_agent == "DIRECT_RESPONSE":
        return END
    return next_agent


def route_agent_tools(
    state: TravelState,
) -> Literal["booking_tools", "research_tools", "supervisor"]:
    """Check if the last message has tool calls; if so route to the correct ToolNode."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # Determine which tool node based on the tool name
        tool_names = {tc["name"] for tc in last_message.tool_calls}
        if "search_local_places" in tool_names or "get_route_directions" in tool_names:
            return "research_tools"
        return "booking_tools"
    # No tool calls → go back to supervisor
    return "supervisor"


# ── Graph Builder ──────────────────────────────────────────────────────────────
def build_graph(checkpointer: MemorySaver | None = None) -> CompiledStateGraph:
    """Build and compile the LangGraph multi-agent workflow."""
    booking_tools = ToolNode([search_flights, search_hotels])
    research_tools = ToolNode([search_local_places, get_route_directions])

    graph = StateGraph(TravelState)  # noqa

    # Add nodes
    graph.add_node("supervisor", supervisor_node)  # noqa
    graph.add_node("booking_agent", booking_agent_node)  # noqa
    graph.add_node("research_agent", research_agent_node)  # noqa
    graph.add_node("booking_tools", booking_tools)
    graph.add_node("research_tools", research_tools)

    # Entry point
    graph.add_edge(START, "supervisor")

    # Supervisor routes to an agent, answers directly, or finishes
    graph.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "booking_agent": "booking_agent",
            "research_agent": "research_agent",
            END: END,  # covers DIRECT_RESPONSE
        },
    )

    # Each agent either calls tools or returns to supervisor
    graph.add_conditional_edges(
        "booking_agent",
        route_agent_tools,
        {
            "booking_tools": "booking_tools",
            "supervisor": "supervisor",
        },
    )
    graph.add_conditional_edges(
        "research_agent",
        route_agent_tools,
        {
            "research_tools": "research_tools",
            "supervisor": "supervisor",
        },
    )

    # After tools execute, go back to the agent that invoked them
    graph.add_edge("booking_tools", "booking_agent")
    graph.add_edge("research_tools", "research_agent")

    return graph.compile(checkpointer=checkpointer)


# ── Lifecycle helpers (called from FastAPI lifespan) ───────────────────────────
async def init_graph() -> None:
    """Initialize the checkpointer and compile the graph once."""
    global _checkpointer, _compiled_graph  # noqa: PLW0603

    _checkpointer = MemorySaver()
    _compiled_graph = build_graph(checkpointer=_checkpointer)


async def shutdown_graph() -> None:
    """Tear down resources cleanly."""
    global _checkpointer, _compiled_graph  # noqa: PLW0603

    _checkpointer = None
    _compiled_graph = None


def get_graph() -> CompiledStateGraph:
    """Return the compiled graph (lazily initializes if needed)."""
    global _compiled_graph, _checkpointer
    if _compiled_graph is None:
        _checkpointer = MemorySaver()
        _compiled_graph = build_graph(checkpointer=_checkpointer)
    return _compiled_graph
