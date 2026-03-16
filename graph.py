"""LangGraph multi-agent workflow for the Travel Planner."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from state import TravelState
from tools import search_flights, search_hotels, search_local_places

load_dotenv()

# ── Prompt Loader ──────────────────────────────────────────────────────────────
_PROMPT_DIR = Path(__file__).parent / 'prompts'


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = _PROMPT_DIR / f'{name}.md'
    text = path.read_text(encoding='utf-8')
    return text.replace('{today}', str(datetime.now().date()))


# ── Models ─────────────────────────────────────────────────────────────────────
def _get_model():
    """Instantiate the Gemini model via Vertex AI (ADC authentication)."""
    return ChatGoogleGenerativeAI(
        model='gemini-3.1-flash-lite-preview',
        thinking_level="low",
    )


# ── Agent Nodes ────────────────────────────────────────────────────────────────
MEMBERS = ['booking_agent', 'research_agent']


def supervisor_node(state: TravelState) -> dict:
    """Supervisor decides which specialist agent should handle the request."""
    model = _get_model()
    system_prompt = _load_prompt('supervisor')

    # Ask the model to choose the next agent
    options = MEMBERS + ['FINISH']
    routing_prompt = (
        f'{system_prompt}\n\n'
        f'Given the conversation above, who should act next?\n'
        f'Choose one of: {options}\n'
        f'Respond with ONLY the name of the agent (or FINISH), nothing else.'
    )

    messages = [SystemMessage(content=routing_prompt)] + state['messages']
    response = model.invoke(messages)

    # Parse the response to get the next agent
    next_agent = response.text.strip().lower()

    # Normalise the response
    if 'booking' in next_agent:
        next_agent = 'booking_agent'
    elif 'research' in next_agent:
        next_agent = 'research_agent'
    else:
        next_agent = 'FINISH'

    return {'next': next_agent}


def booking_agent_node(state: TravelState) -> dict:
    """Booking agent: finds flights and hotels."""
    model = _get_model()
    tools = [search_flights, search_hotels]
    model_with_tools = model.bind_tools(tools)

    system_prompt = _load_prompt('booking_agent')
    messages = [SystemMessage(content=system_prompt)] + state['messages']
    response = model_with_tools.invoke(messages)

    return {'messages': [response]}


def research_agent_node(state: TravelState) -> dict:
    """Research agent: finds local restaurants and attractions."""
    model = _get_model()
    tools = [search_local_places]
    model_with_tools = model.bind_tools(tools)

    system_prompt = _load_prompt('research_agent')
    messages = [SystemMessage(content=system_prompt)] + state['messages']
    response = model_with_tools.invoke(messages)

    return {'messages': [response]}


# ── Routing Logic ──────────────────────────────────────────────────────────────
def route_supervisor(state: TravelState) -> str:
    """Route based on the supervisor's decision stored in state."""
    next_agent = state.get('next', 'FINISH')
    if next_agent == 'FINISH':
        return END
    return next_agent


def route_agent_tools(state: TravelState) -> Literal['booking_tools', 'research_tools', 'supervisor']:
    """Check if the last message has tool calls; if so route to the correct ToolNode."""
    last_message = state['messages'][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        # Determine which tool node based on the tool name
        tool_names = {tc['name'] for tc in last_message.tool_calls}
        if 'search_local_places' in tool_names:
            return 'research_tools'
        return 'booking_tools'
    # No tool calls → go back to supervisor
    return 'supervisor'


# ── Graph Builder ──────────────────────────────────────────────────────────────
def build_graph():
    """Build and compile the LangGraph multi-agent workflow."""
    booking_tools = ToolNode([search_flights, search_hotels])
    research_tools = ToolNode([search_local_places])

    graph = StateGraph(TravelState)

    # Add nodes
    graph.add_node('supervisor', supervisor_node)
    graph.add_node('booking_agent', booking_agent_node)
    graph.add_node('research_agent', research_agent_node)
    graph.add_node('booking_tools', booking_tools)
    graph.add_node('research_tools', research_tools)

    # Entry point
    graph.add_edge(START, 'supervisor')

    # Supervisor routes to an agent or finishes
    graph.add_conditional_edges(
        'supervisor',
        route_supervisor,
        {
            'booking_agent': 'booking_agent',
            'research_agent': 'research_agent',
            END: END,
        },
    )

    # Each agent either calls tools or returns to supervisor
    graph.add_conditional_edges(
        'booking_agent',
        route_agent_tools,
        {
            'booking_tools': 'booking_tools',
            'supervisor': 'supervisor',
        },
    )
    graph.add_conditional_edges(
        'research_agent',
        route_agent_tools,
        {
            'research_tools': 'research_tools',
            'supervisor': 'supervisor',
        },
    )

    # After tools execute, go back to the agent that invoked them
    graph.add_edge('booking_tools', 'booking_agent')
    graph.add_edge('research_tools', 'research_agent')

    return graph.compile()
