"""AI Travel Planner — Streamlit Frontend."""
import warnings
warnings.filterwarnings('ignore', message='.*Pydantic V1 functionality.*')

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from langchain_core.messages import HumanMessage, AIMessage

from typing import Any, cast

from agent import build_graph

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='✈️ AI Travel Planner',
    page_icon='✈️',
    layout='wide',
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }

    /* Header styling */
    .header-container {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .header-container h1 {
        color: #ffffff;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.25rem;
    }
    .header-container p {
        color: #a0aec0;
        font-size: 1.1rem;
        font-weight: 300;
    }

    /* Chat messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(12px);
        padding: 1rem !important;
        margin-bottom: 0.75rem !important;
    }

    /* Chat input */
    .stChatInput > div {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: white !important;
    }
    .stChatInput textarea {
        color: #ffffff !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #e2e8f0 !important;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.15rem;
    }
    .badge-flights { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
    .badge-hotels  { background: linear-gradient(135deg, #f093fb, #f5576c); color: white; }
    .badge-local   { background: linear-gradient(135deg, #4facfe, #00f2fe); color: white; }
    .badge-active  { background: linear-gradient(135deg, #43e97b, #38f9d7); color: #1a1a2e; }

    /* Spinner */
    .stSpinner > div { color: #a78bfa !important; }

    /* General text */
    .stMarkdown p, .stMarkdown li { color: #e2e8f0; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #ffffff; }
    .stMarkdown strong { color: #c4b5fd; }
    .stMarkdown code { background: rgba(139, 92, 246, 0.2); color: #c4b5fd; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-container">
    <h1>✈️ AI Travel Planner</h1>
    <p>Powered by Gemini &bull; LangGraph &bull; SerpAPI</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('### 🛠️ Agent Capabilities')
    st.markdown(
        '<span class="status-badge badge-flights">🛫 Flight Search</span>'
        '<span class="status-badge badge-hotels">🏨 Hotel Search</span>'
        '<span class="status-badge badge-local">📍 Local Places</span>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown('### 💡 Example Prompts')
    examples = [
        'I want to fly from Kolkata to Bangalore on March 20, returning March 25. Find me economy flights and a 3-star hotel under ₹2000/night.',
        'What are the best pizza restaurants in Bangalore?',
        'Find me a round trip from Delhi to Mumbai next week. I need a 4-star hotel with free cancellation.',
    ]
    for ex in examples:
        if st.button(ex, key=f'ex_{hash(ex)}', use_container_width=True):
            st.session_state['prefill'] = ex

    st.divider()
    st.markdown(
        '<p style="font-size:0.75rem; color:#64748b; text-align:center;">'
        'Built with ❤️ using LangGraph Multi-Agent Architecture'
        '</p>',
        unsafe_allow_html=True,
    )

# ── Session State ──────────────────────────────────────────────────────────────
if 'user_location' not in st.session_state:
    with st.spinner('📍 Getting your location...'):
        # This will fetch the user's location based on their IP/browser
        loc_data = streamlit_js_eval(
            js_expressions="fetch('https://ipinfo.io/json').then(r => r.json())",
            key='loc_fetch'
        )
        if loc_data:
            st.session_state.user_location = f"{loc_data.get('city', '')}, {loc_data.get('region', '')}"
        else:
            st.session_state.user_location = None

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'graph' not in st.session_state:
    with st.spinner('🔧 Initialising agents…'):
        st.session_state.graph = build_graph()

# ── Display Chat History ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
    with st.chat_message(role):
        # AI messages have .text (Gemini 3.1), Human messages only have .content
        content = getattr(msg, 'text', msg.content)
        st.markdown(content)

# ── Chat Input ─────────────────────────────────────────────────────────────────
# Check for prefill from sidebar example buttons
prefill = st.session_state.pop('prefill', None)
user_input = st.chat_input('Where would you like to travel?') or prefill

if user_input:
    # Display user message
    with st.chat_message('user'):
        st.markdown(user_input)

    user_msg = HumanMessage(content=user_input)
    st.session_state.messages.append(user_msg)

    # Run the graph
    with st.chat_message('assistant'):
        with st.spinner('✨ Thinking…'):
            result = st.session_state.graph.invoke(
                cast(
                    Any,
                    {
                        'messages': st.session_state.messages,
                        'user_location': st.session_state.get('user_location'),
                        'itinerary': None,
                    },
                ),
            )

        # Extract the final AI response
        ai_messages = [
            m for m in result.get('messages', [])
            if isinstance(m, AIMessage) and m.content
        ]

        if ai_messages:
            final_response = ai_messages[-1]
            st.markdown(final_response.text)
            st.session_state.messages.append(final_response)
        else:
            fallback = 'I couldn\'t find any results. Could you try rephrasing your request?'
            st.markdown(fallback)
            st.session_state.messages.append(AIMessage(content=fallback))
