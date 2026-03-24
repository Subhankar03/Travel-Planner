"""AI Travel Planner — Streamlit Frontend."""
# ── Imports ────────────────────────────────────────────────────────────────────
import json
import os
import urllib.parse
from pathlib import Path
from typing import Any, cast

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from streamlit_js_eval import streamlit_js_eval

from agent import build_graph
from logger import TravelPlannerLogger

# ── Testing Cache (For rapid UI testing) ───────────────────────────────────────
# NOTE: This caching system is strictly for testing purposes to avoid hitting 
# the LLM and SerpAPI repeatedly. It saves the user prompt, tool output, and 
# AI response in a local JSON file. It will be removed in the future.
TESTING_CACHE_FILE = Path('logs/testing_cache.json')

def load_testing_cache():
    """Load the testing cache containing prompts, tool outputs, and AI responses."""
    if TESTING_CACHE_FILE.exists():
        try:
            with open(TESTING_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_testing_cache(cache_data):
    """Save the testing cache data to the JSON file."""
    os.makedirs(TESTING_CACHE_FILE.parent, exist_ok=True)
    with open(TESTING_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)


# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='✈️ AI Travel Planner',
    page_icon='✈️',
    layout='wide',
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.html('styles.css')



# ── Header ─────────────────────────────────────────────────────────────────────
st.html("""
<div class="header-container">
    <h1>✈️ AI Travel Planner</h1>
    <p>Powered by Gemini &bull; LangGraph &bull; SerpAPI</p>
</div>
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('### 🛠️ Agent Capabilities')
    st.html(
        '<span class="status-badge badge-flights">🛫 Flight Search</span>'
        '<span class="status-badge badge-hotels">🏨 Hotel Search</span>'
        '<span class="status-badge badge-local">📍 Local Places</span>'
    )

    st.divider()
    st.markdown('### 💡 Example Prompts')
    examples = [
        "Hey there! I'm planning a chill trip from Delhi to Goa with my partner for next week, leaving on Wednesday and coming back on Sunday. Could you find us some direct flights? We also need a nice 4-star or 5-star hotel near the beach. Once you have that, can you suggest some cool beach shacks or highly-rated seafood joints near the hotel, along with a couple of fun water sports places?",
        "I'm organising a family get-together in Ooty for the first weekend of next month. There will be 6 of us in total (4 adults and 2 kids). I don't need flights, but I am looking for a nice vacation rental or villa instead of a regular hotel. We'd prefer something with at least 3 bedrooms and maybe some decent amenities. Also, could you suggest some family-friendly local attractions and a few good places to grab lunch around Ooty?",
        "Planning a quick business trip from Mumbai to Bangalore arriving on the 15th of next month and leaving on the 17th. I'm looking for business class flights if they aren't insanely expensive, otherwise premium economy works. I also need a 5-star hotel close to Koramangala or Indiranagar. Since I'll have some free time in the evenings, hit me up with some popular brewpubs and highly-rated cafes in that area to check out.",
        "Hey, me and my 2 friends are looking to do a budget trip from Kolkata to Guwahati around the middle of next month for 5 days. Can you find us the absolute cheapest flights possible? We don't mind layovers. For accommodation, we want budget-friendly options, maybe hostels or cheap hotels under 2000 INR per night. What are some must-visit highly-rated local spots and cheap street food areas to explore while we're there?",
        "I'm already in Jaipur for the weekend and I just want to explore! I don't need any flights or hotels. Can you put together a list of the absolute best places to get authentic Rajasthani thalis? Also, what are the top 3 historical forts or monuments I should visit nearby? I'd love to know what people are saying in the reviews if they are highly rated.",
        "Hey, it's my anniversary next month and I want to surprise my partner with a luxurious trip from Chennai to Kochi. We want to fly out on a Friday and return on Monday. We are looking for top-tier 5-star hotels or luxury resorts in Kochi, preferably something really highly rated and luxurious. Also, could you find us some romantic fine-dining restaurants and maybe a few quiet, scenic spots or backwater cruise options nearby?",
    ]
    for ex in examples:
        if st.button(ex, key=f'ex_{hash(ex)}', width='stretch'):
            st.session_state['prefill'] = ex

    st.divider()

    # Show log file path when the logger is ready
    if 'logger' in st.session_state:
        log_path = st.session_state.logger.log_path
        st.html(
            f'<p style="font-size:0.72rem; color:#64748b;">'
            f'📝 Session log<br><code style="font-size:0.68rem; color:#475569;">{log_path.name}</code>'
            f'</p>'
        )

    st.html(
        '<p style="font-size:0.75rem; color:#64748b; text-align:center;">'
        'Built with ❤️ using LangGraph Multi-Agent Architecture'
        '</p>'
    )

# ── Session State ──────────────────────────────────────────────────────────────
if 'user_location' not in st.session_state:
    with st.spinner('📍 Getting your location...'):
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

# Store tool results alongside messages for card rendering
if 'tool_results' not in st.session_state:
    st.session_state.tool_results = {}  # msg_index -> list of parsed tool data

if 'graph' not in st.session_state:
    with st.spinner('🔧 Initialising agents…'):
        st.session_state.graph = build_graph()

# Initialise the session logger once per browser session
if 'logger' not in st.session_state:
    st.session_state.logger = TravelPlannerLogger()


# ── Card Rendering Helpers ─────────────────────────────────────────────────────
def _render_flight_cards(flights_data: dict) -> None:
    """Render flight results as cards."""
    # Get the search/booking link
    search_url = flights_data.get('search_url', '')
    link_html = f' · <a href="{search_url}" target="_blank" style="color:#818cf8; font-size: 0.9rem;">View on Google Flights →</a>' if search_url else ''

    all_flights = flights_data.get('best_flights', []) + flights_data.get('other_flights', [])
    if not all_flights:
        return

    st.html(f'<h4 style="color:white; margin-bottom:0.5rem;">✈️ Flights Found{link_html}</h4>')
    for flight in all_flights[:6]:
        legs = flight.get('legs', [])
        if not legs:
            continue

        first_leg = legs[0]
        # Use group-level logo first, then leg-level logo
        logo_url = flight.get('airline_logo') or first_leg.get('airline_logo', '')
        airline = first_leg.get('airline', 'Unknown')
        price = flight.get('price')
        total_min = flight.get('total_duration_min', 0)
        hours, mins = divmod(total_min, 60) if total_min else (0, 0)
        flight_nums = ' + '.join(leg.get('flight_number', '') for leg in legs if leg.get('flight_number'))
        travel_class = first_leg.get('travel_class', '')
        airplane = first_leg.get('airplane', '')
        price_str = f'₹{price:,}' if price else 'N/A'

        # Build route: CCU → BOM → BLR
        route_parts = [first_leg.get('departure', '').split(' at ')[0]]
        for leg in legs:
            route_parts.append(leg.get('arrival', '').split(' at ')[0])
        route = ' → '.join(route_parts)

        # Departure / arrival times
        depart_time = first_leg.get('departure', '').split(' at ')[-1] if ' at ' in first_leg.get('departure', '') else ''
        arrive_time = legs[-1].get('arrival', '').split(' at ')[-1] if ' at ' in legs[-1].get('arrival', '') else ''

        # Per-flight Google Flights deep link via booking_token
        booking_token = flight.get('booking_token', '')
        book_url = (
            f'https://www.google.com/travel/flights?tfs={urllib.parse.quote(booking_token)}'
            if booking_token else search_url
        )

        # Airline logo HTML
        if logo_url:
            img_inner = f'<img src="{logo_url}" class="logo-img" alt="{airline}">'
        else:
            img_inner = '<span class="fallback-emoji">✈️</span>'

        # Book now button HTML
        book_html = f'<a href="{book_url}" target="_blank" class="book-btn"><span>Book Now →</span></a>' if book_url else ''

        st.html(f"""
<div class="result-card">
    <div class="card-img-wrap">{img_inner}</div>
    <div class="card-body">
        <div class="card-top-row">
            <div>
                <div class="card-title">{airline} &middot; {flight_nums}</div>
                <div class="card-subtitle">{route} &middot; {hours}h {mins}m &middot; {flight.get('type', '')}</div>
            </div>
            <span class="card-price">{price_str}</span>
        </div>
        <div class="card-bottom-row">
            <div style="display:flex; gap:1rem; align-items:center; flex-wrap:wrap;">
                <span class="card-meta">🛫 {depart_time}</span>
                <span class="card-meta">🛬 {arrive_time}</span>
                <span class="card-badge">{travel_class}</span>
                <span class="card-meta">{airplane}</span>
            </div>
            {book_html}
        </div>
    </div>
</div>
        """)



@st.dialog("Hotel Images", width="large")
def show_hotel_images(images: list):
    """Show hotel images in a carousel dialog."""
    if not images:
        st.info("No images available.")
        return
    imgs_html = "".join([f'<img src="{u}" />' for u in images])
    st.html(f'<div class="carousel">{imgs_html}</div>')


def _render_hotel_cards(hotels_data: list, msg_idx: int = 0) -> None:
    """Render hotel results as cards with thumbnails."""
    if not hotels_data:
        return

    st.markdown('#### 🏨 Hotels Found')
    for i, hotel in enumerate(hotels_data[:6]):
        thumb = hotel.get('thumbnail')
        name = hotel.get('name', 'Hotel')
        rating = hotel.get('overall_rating', '')
        reviews = hotel.get('reviews', '')
        rate = hotel.get('rate_per_night', '')
        hotel_class = hotel.get('hotel_class', '')
        amenities = hotel.get('amenities', [])[:5]
        link = hotel.get('link', '')

        amenity_badges = ''.join(f'<span class="card-badge">{a}</span>' for a in amenities)

        hotel_images = hotel.get('images', [])
        has_images = len(hotel_images) > 0
        img_wrap_id = f"img-wrap-{msg_idx}-{i}"
        
        overlay_html = '<div class="img-overlay">📷</div>' if has_images else ''
        cursor_style = 'cursor: pointer;' if has_images else ''

        # Image / fallback
        if thumb:
            img_inner = f'<img src="{thumb}" alt="{name}">{overlay_html}'
        else:
            img_inner = f'<span class="fallback-emoji">🏨</span>{overlay_html}'

        # Book now button
        book_html = f'<a href="{link}" target="_blank" class="book-btn"><span>Book Now →</span></a>' if link else ''

        subtitle_parts = []
        if hotel_class:
            subtitle_parts.append(hotel_class)
        if rating:
            subtitle_parts.append(f'<span class="card-rating">⭐ {rating}</span>')
        if reviews:
            subtitle_parts.append(f'<span class="card-meta">({reviews} reviews)</span>')
        subtitle_html = ' &middot; '.join(subtitle_parts)

        st.html(f"""
<div class="result-card">
    <div class="card-img-wrap" id="{img_wrap_id}" style="{cursor_style}">{img_inner}</div>
    <div class="card-body">
        <div class="card-top-row">
            <div>
                <div class="card-title">{name}</div>
                <div class="card-subtitle">{subtitle_html}</div>
            </div>
            <span class="card-price">{rate}<span style="color:#94a3b8; font-size:0.75rem; font-weight:400;">/night</span></span>
        </div>
        <div class="card-bottom-row">
            <div>{amenity_badges}</div>{book_html}
        </div>
    </div>
</div>
        """)

        if has_images:
            btn_key = f"hotel_img_btn_{msg_idx}_{i}"
            if st.button(f"HiddenViewBtn_{msg_idx}_{i}", key=btn_key, help="View images"):
                show_hotel_images(hotel_images)
            
            st.html(f"""
            <script>
            (function() {{
                var btns = document.querySelectorAll('button');
                var myBtn = null;
                for (var b of btns) {{
                    if (b.innerText.includes('HiddenViewBtn_{msg_idx}_{i}')) {{
                        myBtn = b;
                        let container = b.closest('div[data-testid="stElementContainer"]');
                        if (container) container.style.display = 'none';
                        break;
                    }}
                }}
                var imgWrap = document.getElementById('{img_wrap_id}');
                if (imgWrap && myBtn) {{
                    imgWrap.onclick = function() {{ myBtn.click(); }};
                }}
            }})();
            </script>
            """, unsafe_allow_javascript=True)


def _render_place_cards(places_data: list) -> None:
    """Render local place results as cards with thumbnails."""
    if not places_data:
        return

    st.markdown('#### 📍 Places Found')
    for place in places_data[:8]:
        thumb = place.get('thumbnail')
        title = place.get('title', 'Place')
        ptype = place.get('type', '')
        rating = place.get('rating', '')
        reviews = place.get('reviews', '')
        price = place.get('price', '')
        desc = place.get('description', '')
        address = place.get('address', '')

        # Image / fallback
        if thumb:
            img_inner = f'<img src="{thumb}" alt="{title}">'
        else:
            img_inner = '<span class="fallback-emoji">📍</span>'

        # Price at top-right
        price_html = f'<span class="card-price">{price}</span>' if price else ''

        # Description row (optional)
        # Trim description so it doesn't overflow easily
        if desc and len(desc) > 80:
            desc = desc[:77] + '...'
        desc_html = f'<div class="card-meta">{desc}</div>' if desc else ''

        subtitle_parts = []
        if ptype or address:
            subtitle_parts.append(f"{ptype} &middot; {address}" if ptype and address else (ptype or address))
        if rating:
            subtitle_parts.append(f'<span class="card-rating">⭐ {rating}</span>')
        if reviews:
            subtitle_parts.append(f'<span class="card-meta">({reviews} reviews)</span>')
        subtitle_html = ' &middot; '.join(subtitle_parts)

        st.html(f"""
<div class="result-card">
    <div class="card-img-wrap">{img_inner}</div>
    <div class="card-body">
        <div class="card-top-row">
            <div>
                <div class="card-title">{title}</div>
                <div class="card-subtitle">{subtitle_html}</div>
            </div>{price_html}
        </div>
        <div class="card-bottom-row" style="margin-top:0;">
            {desc_html}
        </div>
    </div>
</div>
        """)


def _render_tool_results(tool_data_list: list, msg_idx: int = 0) -> None:
    """Route tool results to the correct card renderer."""
    for item in tool_data_list:
        tool_name = item.get('tool_name', '')
        data = item.get('data')
        if not data:
            continue
        if tool_name == 'search_flights':
            _render_flight_cards(data)
        elif tool_name == 'search_hotels':
            _render_hotel_cards(data, msg_idx)
        elif tool_name == 'search_local_places':
            _render_place_cards(data)


# ── Display Chat History ───────────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
    with st.chat_message(role):
        content = getattr(msg, 'text', msg.content)
        st.markdown(content)
        # If this message has associated tool results, render cards
        if i in st.session_state.tool_results:
            _render_tool_results(st.session_state.tool_results[i], i)

# ── Chat Input ─────────────────────────────────────────────────────────────────
prefill = st.session_state.pop('prefill', None)
user_input = st.chat_input('Where would you like to travel?') or prefill

if user_input:
    # Display user message
    with st.chat_message('user'):
        st.markdown(user_input)

    user_msg = HumanMessage(content=user_input)
    st.session_state.messages.append(user_msg)

    # ── Log the user's turn ────────────────────────────────────────────────
    _log: TravelPlannerLogger = st.session_state.logger
    _log.log_separator('New Turn')
    _log.log_user(user_input)

    # ── Check Testing Cache ────────────────────────────────────────────────────
    testing_cache = load_testing_cache()
    cached_turn = testing_cache.get(user_input)

    if cached_turn:
        with st.chat_message('assistant'):
            st.info('⚡ **Testing Cache Hit:** Loaded response instantly!')
            ai_text = cached_turn['ai_response']
            tool_data_list = cached_turn['tool_data_list']
            
            st.markdown(ai_text)
            
            if tool_data_list:
                msg_idx = len(st.session_state.messages)
                _render_tool_results(tool_data_list, msg_idx)
                
            cached_ai_msg = AIMessage(content=ai_text)
            st.session_state.messages.append(cached_ai_msg)
            
            if tool_data_list:
                msg_idx = len(st.session_state.messages) - 1
                st.session_state.tool_results[msg_idx] = tool_data_list
                
            _log.log_ai(ai_text)
    else:
        # Run the graph
        with st.chat_message('assistant'):
            status_container = st.status('✨ Thinking…', expanded=True)

            tool_data_list = []
            final_ai_response = None
            _seen_tool_ids: set[str] = set()

            # ── Stream updates and log incrementally ────────────────────────────
            for chunk in st.session_state.graph.stream(
                cast(Any, {
                    'messages': st.session_state.messages,
                    'user_location': st.session_state.get('user_location'),
                    'itinerary': None,
                }),
                stream_mode='updates',
            ):
                for node_name, node_output in chunk.items():
                    # Update status to show current node
                    status_container.update(label=f'✨ Thinking… (Current: {node_name})')
                    
                    # Log node
                    _log.log_node(node_name)

                    if not node_output or not isinstance(node_output, dict):
                        continue

                    node_messages = node_output.get('messages', [])
                    for msg in node_messages:
                        if isinstance(msg, AIMessage):
                            # Log any tool calls embedded in AI messages
                            for tc in getattr(msg, 'tool_calls', []) or []:
                                tc_id = tc.get('id', '')
                                if tc_id not in _seen_tool_ids:
                                    _seen_tool_ids.add(tc_id)
                                    _log.log_tool_call(tc.get('name', 'unknown'), tc.get('args'))
                            if msg.content:
                                final_ai_response = msg
                        elif isinstance(msg, ToolMessage):
                            _log.log_tool_output(msg.name or 'tool', msg.content)

                            # Extract tool results for card rendering
                            if isinstance(msg.content, str):
                                try:
                                    parsed = json.loads(msg.content)
                                    tool_data_list.append({
                                        'tool_name': msg.name,
                                        'data': parsed,
                                    })
                                except (json.JSONDecodeError, TypeError):
                                    pass

            status_container.update(label='✨ Finished!', state='complete', expanded=False)

            if final_ai_response and final_ai_response.content:
                ai_text = getattr(final_ai_response, 'text', final_ai_response.content)
                if not isinstance(ai_text, str):
                    ai_text = str(ai_text)

                st.markdown(ai_text)

                # Log the AI's final response
                _log.log_ai(ai_text)

                # Render cards if we have structured tool data
                if tool_data_list:
                    msg_idx = len(st.session_state.messages)
                    _render_tool_results(tool_data_list, msg_idx)

                st.session_state.messages.append(final_ai_response)

                # Store tool results keyed to the message index for replay
                if tool_data_list:
                    msg_idx = len(st.session_state.messages) - 1
                    st.session_state.tool_results[msg_idx] = tool_data_list
                    
                # Save to testing cache
                testing_cache[user_input] = {
                    'ai_response': ai_text,
                    'tool_data_list': tool_data_list
                }
                save_testing_cache(testing_cache)
            else:
                fallback = "I couldn't find any results. Could you try rephrasing your request?"
                st.markdown(fallback)
                st.session_state.messages.append(AIMessage(content=fallback))
                _log.log_ai(fallback)
