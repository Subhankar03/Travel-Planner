"""LangGraph multi-agent workflow for the Travel Planner."""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal

import requests
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from state import TravelState
from tools import search_flights, search_hotels, search_local_places, get_route_directions

load_dotenv()
_PROMPT_DIR = Path(__file__).parent / 'prompts'


# ── Helpers ────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def get_current_location() -> str:
    """Get the user's current location via IP-based geolocation."""
    try:
        response = requests.get("https://ipinfo.io/json", headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        response.raise_for_status()
        data = response.json()
        city = data.get("city", "Unknown City")
        region = data.get("region", "Unknown Region")
        return f"{city}, {region}"
    except Exception:
        return "Unknown Location"


# ── Agent Nodes ────────────────────────────────────────────────────────────────
def supervisor_node(state: TravelState) -> dict:
    """Supervisor decides which specialist agent should handle the request."""
    model = ChatGoogleGenerativeAI(model='gemini-3.1-flash-lite-preview')
    system_template = (_PROMPT_DIR/'supervisor.md').read_text(encoding='utf-8')

    # Ask the model to choose the next agent
    routing_instructions = (
        'Given the conversation above, who should act next?\n'
        "Choose one of: 'booking_agent', 'research_agent', 'FINISH'\n"
        'Respond with ONLY the name of the agent (or FINISH), nothing else.'
    )

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        MessagesPlaceholder(variable_name="messages"),
        SystemMessage(content=routing_instructions)
    ])

    response = model.invoke(prompt.invoke({
        "messages": state['messages']
    }))

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
    model = ChatGoogleGenerativeAI(model='gemini-3-flash-preview')
    model_with_tools = model.bind_tools([search_flights, search_hotels])

    system_template = (_PROMPT_DIR/'booking_agent.md').read_text(encoding='utf-8')
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    # Identify user location (from state or IP fallback)
    location = state.get('user_location') or get_current_location()

    response = model_with_tools.invoke(prompt.invoke({
        "today": datetime.now().strftime('%A, %Y-%m-%d'),
        "location": location,
        "messages": state['messages']
    }))

    return {'messages': [response]}


def research_agent_node(state: TravelState) -> dict:
    """Research agent: finds local restaurants and attractions, and gets directions."""
    model = ChatGoogleGenerativeAI(model='gemini-3-flash-preview')
    model_with_tools = model.bind_tools([search_local_places, get_route_directions])

    system_template = (_PROMPT_DIR/'research_agent.md').read_text(encoding='utf-8')
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        MessagesPlaceholder(variable_name="messages")
    ])
    # Identify user location (from state or IP fallback)
    location = state.get('user_location') or get_current_location()

    response = model_with_tools.invoke(prompt.invoke({
        "today": datetime.now().strftime('%A, %Y-%m-%d'),
        "location": location,
        "messages": state['messages']
    }))

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
        if 'search_local_places' in tool_names or 'get_route_directions' in tool_names:
            return 'research_tools'
        return 'booking_tools'
    # No tool calls → go back to supervisor
    return 'supervisor'


# ── Graph Builder ──────────────────────────────────────────────────────────────
def build_graph():
    """Build and compile the LangGraph multi-agent workflow."""
    booking_tools = ToolNode([search_flights, search_hotels])
    research_tools = ToolNode([search_local_places, get_route_directions])

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
