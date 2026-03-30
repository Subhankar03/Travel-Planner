"""LangGraph multi-agent workflow for the Travel Planner."""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Literal

import requests
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
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
    """Supervisor decides which specialist agent should handle the request.

    Routing options:
    - booking_agent   → flight / hotel / itinerary requests
    - research_agent  → local discovery / directions requests
    - DIRECT_RESPONSE → general / meta questions answered by the supervisor
    - FINISH          → conversation complete
    """
    model = ChatGoogleGenerativeAI(model='gemini-3.1-flash-lite-preview')
    system_template = (_PROMPT_DIR / 'supervisor.md').read_text(encoding='utf-8')

    # ── Step 1: routing decision ───────────────────────────────────────────────
    routing_instructions = (
        'Given the conversation above, what should happen next?\n'
        "Choose EXACTLY ONE of: 'booking_agent', 'research_agent', "
        "'DIRECT_RESPONSE', 'FINISH'\n"
        'Reply with ONLY that word — nothing else.'
    )

    routing_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_template),
        MessagesPlaceholder(variable_name='messages'),
        HumanMessage(content=routing_instructions),
    ])

    routing_response = model.invoke(routing_prompt.invoke({
        'messages': state['messages'],
    }))

    raw = routing_response.text.strip().lower()

    if 'booking' in raw:
        next_agent = 'booking_agent'
    elif 'research' in raw:
        next_agent = 'research_agent'
    elif 'direct' in raw:
        next_agent = 'DIRECT_RESPONSE'
    else:
        next_agent = 'FINISH'

    # ── Step 2: if direct response, generate the reply now ────────────────────
    if next_agent == 'DIRECT_RESPONSE':
        reply_instructions = (
            'The user asked a general or meta question. '
            'Using your knowledge of the system capabilities described in your system prompt, '
            'compose a helpful, friendly reply in markdown. '
            'Do NOT mention internal agent names or technical routing details.'
        )
        reply_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            MessagesPlaceholder(variable_name='messages'),
            HumanMessage(content=reply_instructions),
        ])
        reply_response = model.invoke(reply_prompt.invoke({
            'messages': state['messages'],
        }))
        return {
            'next': 'DIRECT_RESPONSE',
            'messages': [AIMessage(content=reply_response.text.strip())],
        }

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
    if next_agent in ('FINISH', 'DIRECT_RESPONSE'):
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
def build_graph(checkpointer=None):
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

    # Supervisor routes to an agent, answers directly, or finishes
    graph.add_conditional_edges(
        'supervisor',
        route_supervisor,
        {
            'booking_agent': 'booking_agent',
            'research_agent': 'research_agent',
            END: END,  # covers both FINISH and DIRECT_RESPONSE
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

    return graph.compile(checkpointer=checkpointer)
