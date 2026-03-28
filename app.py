"""AI Travel Planner — Streamlit Frontend."""

# ── Imports ────────────────────────────────────────────────────────────────────
import json
import os
import re
import urllib.parse
from pathlib import Path
from typing import Any, cast

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from streamlit_js_eval import streamlit_js_eval

from agent import build_graph
from utils import TravelPlannerLogger, render_map_in_streamlit

# ── Testing Cache (For rapid UI testing) ───────────────────────────────────────
# NOTE: This caching system is strictly for testing purposes to avoid hitting
# the LLM and SerpAPI repeatedly. It saves the user prompt, tool output, and
# AI response in a local JSON file. It will be removed in the future.
TESTING_CACHE_FILE = Path("logs/testing_cache.json")


def load_testing_cache():
    """Load the testing cache containing prompts, tool outputs, and AI responses."""
    if TESTING_CACHE_FILE.exists():
        try:
            with open(TESTING_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_testing_cache(cache_data):
    """Save the testing cache data to the JSON file."""
    os.makedirs(TESTING_CACHE_FILE.parent, exist_ok=True)
    with open(TESTING_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)


# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="✈️ AI Travel Planner",
    page_icon="✈️",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.html("styles.css")


# ── Header ─────────────────────────────────────────────────────────────────────
st.html("""
<div class="header-container">
    <h1>✈️ AI Travel Planner</h1>
    <p>Powered by Gemini &bull; LangGraph &bull; SerpAPI</p>
</div>
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛠️ Agent Capabilities")
    st.html(
        '<span class="status-badge badge-flights">🛫 Flight Search</span>'
        '<span class="status-badge badge-hotels">🏨 Hotel Search</span>'
        '<span class="status-badge badge-local">📍 Local Places</span>'
    )

    st.divider()
    st.markdown("### 💡 Example Prompts")
    examples = [
        "Hey there! I'm planning a chill trip from Delhi to Goa with my partner for next week, leaving on Wednesday and coming back on Sunday. Could you find us some direct flights? We also need a nice 4-star or 5-star hotel near the beach. Once you have that, can you suggest some cool beach shacks or highly-rated seafood joints near the hotel, along with a couple of fun water sports places?",
        "I'm organising a family get-together in Ooty for the first weekend of next month. There will be 6 of us in total (4 adults and 2 kids). I don't need flights, but I am looking for a nice vacation rental or villa instead of a regular hotel. We'd prefer something with at least 3 bedrooms and maybe some decent amenities. Also, could you suggest some family-friendly local attractions and a few good places to grab lunch around Ooty?",
        "Planning a quick business trip from Mumbai to Bangalore arriving on the 15th of next month and leaving on the 17th. I'm looking for business class flights if they aren't insanely expensive, otherwise premium economy works. I also need a 5-star hotel close to Koramangala or Indiranagar. Since I'll have some free time in the evenings, hit me up with some popular brewpubs and highly-rated cafes in that area to check out.",
        "Hey, me and my 2 friends are looking to do a budget trip from Kolkata to Guwahati around the middle of next month for 5 days. Can you find us the absolute cheapest flights possible? We don't mind layovers. For accommodation, we want budget-friendly options, maybe hostels or cheap hotels under 2000 INR per night. What are some must-visit highly-rated local spots and cheap street food areas to explore while we're there?",
        "I'm already in Jaipur for the weekend and I just want to explore! I don't need any flights or hotels. Can you put together a list of the absolute best places to get authentic Rajasthani thalis? Also, what are the top 3 historical forts or monuments I should visit nearby? I'd love to know what people are saying in the reviews if they are highly rated.",
        "Hey, it's my anniversary next month and I want to surprise my partner with a luxurious trip from Chennai to Kochi. We want to fly out on a Friday and return on Monday. We are looking for top-tier 5-star hotels or luxury resorts in Kochi, preferably something really highly rated and luxurious. Also, could you find us some romantic fine-dining restaurants and maybe a few quiet, scenic spots or backwater cruise options nearby?",
    ]
    for ex in examples:
        short_label = ex[:72] + "…" if len(ex) > 72 else ex
        if st.button(short_label, key=f"ex_{hash(ex)}", width="stretch", help=ex):
            st.session_state["pending_prefill"] = ex

    st.divider()

    # Show log file path when the logger is ready
    if "logger" in st.session_state:
        log_path = st.session_state.logger.log_path
        st.html(
            f'<p style="font-size:0.72rem; color:#64748b;">'
            f'📝 Session log<br><code style="font-size:0.68rem; color:#475569;">{log_path.name}</code>'
            f"</p>"
        )

    st.html(
        '<p style="font-size:0.75rem; color:#64748b; text-align:center;">'
        "Built with ❤️ using LangGraph Multi-Agent Architecture"
        "</p>"
    )

# ── Session State ──────────────────────────────────────────────────────────────
if "user_location" not in st.session_state:
    with st.spinner("📍 Getting your location..."):
        loc_data = streamlit_js_eval(
            js_expressions="fetch('https://ipinfo.io/json').then(r => r.json())",
            key="loc_fetch",
        )
        if loc_data:
            st.session_state.user_location = (
                f"{loc_data.get('city', '')}, {loc_data.get('region', '')}"
            )
        else:
            st.session_state.user_location = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# Store tool results alongside messages for card rendering
if "tool_results" not in st.session_state:
    st.session_state.tool_results = {}  # msg_index -> list of parsed tool data

if "traces" not in st.session_state:
    st.session_state.traces = {}  # msg_index -> list of trace dicts

if "graph" not in st.session_state:
    with st.spinner("🔧 Initialising agents…"):
        st.session_state.graph = build_graph()

# Initialise the session logger once per browser session
if "logger" not in st.session_state:
    st.session_state.logger = TravelPlannerLogger()

# Latest tool results for the side panel
if "latest_spatial_data" not in st.session_state:
    st.session_state.latest_spatial_data = []
if "latest_route_data" not in st.session_state:
    st.session_state.latest_route_data = None


# ── Card Rendering Helpers ─────────────────────────────────────────────────────
def _render_flight_cards(flights_data: dict) -> None:
    """Render flight results as cards."""
    search_url = flights_data.get("search_url", "")

    all_flights = flights_data.get("best_flights", []) + flights_data.get(
        "other_flights", []
    )
    if not all_flights:
        return

    html_parts = []
    html_parts.append(
        '<details class="custom-details" open><summary class="custom-summary">✈️ Flights Found</summary>'
    )
    html_parts.append('<div class="details-content">')
    for flight in all_flights[:6]:
        legs = flight.get("legs", [])
        if not legs:
            continue

        first_leg = legs[0]
        # Use group-level logo first, then leg-level logo
        logo_url = flight.get("airline_logo") or first_leg.get("airline_logo", "")
        airline = first_leg.get("airline", "Unknown")
        price = flight.get("price")
        total_min = flight.get("total_duration_min", 0)
        hours, mins = divmod(total_min, 60) if total_min else (0, 0)
        flight_nums = " + ".join(
            leg.get("flight_number", "") for leg in legs if leg.get("flight_number")
        )
        travel_class = first_leg.get("travel_class", "")
        airplane = first_leg.get("airplane", "")
        price_str = f"₹{price:,}" if price else "N/A"

        # Build route: CCU → BOM → BLR
        route_parts = [first_leg.get("departure", "").split(" at ")[0]]
        for leg in legs:
            route_parts.append(leg.get("arrival", "").split(" at ")[0])
        route = " → ".join(route_parts)

        # Departure / arrival times
        depart_time = (
            first_leg.get("departure", "").split(" at ")[-1]
            if " at " in first_leg.get("departure", "")
            else ""
        )
        arrive_time = (
            legs[-1].get("arrival", "").split(" at ")[-1]
            if " at " in legs[-1].get("arrival", "")
            else ""
        )

        # Per-flight Google Flights deep link via booking_token
        booking_token = flight.get("booking_token", "")
        book_url = (
            f"https://www.google.com/travel/flights?tfs={urllib.parse.quote(booking_token)}"
            if booking_token
            else search_url
        )

        # Airline logo HTML
        if logo_url:
            img_inner = f'<img src="{logo_url}" class="logo-img" alt="{airline}">'
        else:
            img_inner = '<span class="fallback-emoji">✈️</span>'

        # Book now button HTML
        book_html = (
            f'<a href="{book_url}" target="_blank" class="book-btn"><span>Book Now →</span></a>'
            if book_url
            else ""
        )

        html_parts.append(f"""
<div class="result-card">
    <div class="card-img-wrap">{img_inner}</div>
    <div class="card-body">
        <div class="card-top-row">
            <div>
                <div class="card-title">{airline} &middot; {flight_nums}</div>
                <div class="card-subtitle">{route} &middot; {hours}h {mins}m &middot; {flight.get("type", "")}</div>
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
    html_parts.append("</div></details>")
    st.html("\n".join(html_parts))


# ── Maps Button Helper ─────────────────────────────────────────────────────────
def _maps_btn(gps: dict | None) -> str:
    """Return an anchor HTML string that opens Google Maps at given coordinates."""
    if not gps:
        return ""
    lat = gps.get("latitude")
    lng = gps.get("longitude")
    if not lat or not lng:
        return ""
    url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
    return (
        f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="maps-btn">'
        f"<span>🗺 View in Maps</span></a>"
    )


@st.dialog("Hotel Images", width="large")
def show_hotel_images(images: list):
    """Show hotel images in a carousel dialog."""
    if not images:
        st.info("No images available.")
        return
    imgs_html = "".join([f'<img src="{u}" />' for u in images])
    st.html(f'<div class="carousel">{imgs_html}</div>')


def _render_hotel_cards(
    hotels_data: list, msg_idx: int = 0, block_idx: int = 0
) -> None:
    """Render hotel results as cards with thumbnails."""
    if not hotels_data:
        return

    # First, render hidden buttons for image modal so they exist in the DOM
    for i, hotel in enumerate(hotels_data[:6]):
        hotel_images = hotel.get("images", [])
        if len(hotel_images) > 0:
            btn_key = f"hotel_img_btn_{msg_idx}_{block_idx}_{i}"
            if st.button(
                f"HiddenViewBtn_{msg_idx}_{block_idx}_{i}",
                key=btn_key,
                help="View images",
            ):
                show_hotel_images(hotel_images)

    html_parts = []
    html_parts.append(
        '<details class="custom-details" open><summary class="custom-summary">🏨 Hotels Found</summary>'
    )
    html_parts.append('<div class="details-content">')
    for i, hotel in enumerate(hotels_data[:6]):
        thumb = hotel.get("thumbnail")
        name = hotel.get("name", "Hotel")
        rating = hotel.get("overall_rating", "")
        reviews = hotel.get("reviews", "")
        rate = hotel.get("rate_per_night", "")
        hotel_class = hotel.get("hotel_class", "")
        amenities = hotel.get("amenities", [])[:5]
        link = hotel.get("link", "")

        amenity_badges = "".join(
            f'<span class="card-badge">{a}</span>' for a in amenities
        )

        hotel_images = hotel.get("images", [])
        has_images = len(hotel_images) > 0
        img_wrap_id = f"img-wrap-{msg_idx}-{i}"

        overlay_html = '<div class="img-overlay">📷</div>' if has_images else ""
        cursor_style = "cursor: pointer;" if has_images else ""

        # Image / fallback
        if thumb:
            img_inner = f'<img src="{thumb}" alt="{name}">{overlay_html}'
        else:
            img_inner = f'<span class="fallback-emoji">🏨</span>{overlay_html}'

        # Book now + Maps buttons
        gps = hotel.get("gps_coordinates")
        maps_html = _maps_btn(gps)
        book_html = (
            f'<a href="{link}" target="_blank" class="book-btn"><span>Book Now →</span></a>'
            if link
            else ""
        )

        subtitle_parts = []
        if hotel_class:
            subtitle_parts.append(hotel_class)
        if rating:
            subtitle_parts.append(f'<span class="card-rating">⭐ {rating}</span>')
        if reviews:
            subtitle_parts.append(f'<span class="card-meta">({reviews} reviews)</span>')
        subtitle_html = " &middot; ".join(subtitle_parts)

        html_parts.append(f"""
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
            <div>{amenity_badges}</div>
            <div style="display:flex; gap:8px; align-items:center;">{maps_html}{book_html}</div>
        </div>
    </div>
</div>
        """)

        if has_images:
            html_parts.append(f"""
            <script>
            (function() {{
                var btns = document.querySelectorAll('button');
                var myBtn = null;
                for (var b of btns) {{
                    if (b.innerText.includes('HiddenViewBtn_{msg_idx}_{block_idx}_{i}')) {{
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
            """)

    html_parts.append("</div></details>")
    st.html("\n".join(html_parts), unsafe_allow_javascript=True)


def _render_place_cards(
    places_data: list, category_label: str = "Places Found"
) -> None:
    """Render local place results as cards with thumbnails."""
    if not places_data:
        return

    display_label = category_label
    if not display_label.lower().endswith("found"):
        display_label = f"{category_label} found"

    html_parts = []
    html_parts.append(
        f'<details class="custom-details" open><summary class="custom-summary">📍 {display_label}</summary>'
    )
    html_parts.append('<div class="details-content">')
    for place in places_data[:8]:
        thumb = place.get("thumbnail")
        title = place.get("title", "Place")
        ptype = place.get("type", "")
        rating = place.get("rating", "")
        reviews = place.get("reviews", "")
        price = place.get("price", "")
        desc = place.get("description", "")
        address = place.get("address", "")

        # Image / fallback
        if thumb:
            img_inner = f'<img src="{thumb}" alt="{title}">'
        else:
            img_inner = '<span class="fallback-emoji">📍</span>'

        # Price at top-right
        price_html = f'<span class="card-price">{price}</span>' if price else ""

        # Description row (optional)
        # Trim description so it doesn't overflow easily
        if desc and len(desc) > 80:
            desc = desc[:77] + "..."
        desc_html = f'<div class="card-meta">{desc}</div>' if desc else ""

        subtitle_parts = []
        if ptype or address:
            subtitle_parts.append(
                f"{ptype} &middot; {address}"
                if ptype and address
                else (ptype or address)
            )
        if rating:
            subtitle_parts.append(f'<span class="card-rating">⭐ {rating}</span>')
        if reviews:
            subtitle_parts.append(f'<span class="card-meta">({reviews} reviews)</span>')
        subtitle_html = " &middot; ".join(subtitle_parts)

        gps_place = place.get("gps_coordinates")
        maps_html_place = _maps_btn(gps_place)

        html_parts.append(f"""
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
            <div style="display:flex; justify-content:flex-end; margin-top:6px;">{maps_html_place}</div>
        </div>
    </div>
</div>
        """)
    html_parts.append("</div></details>")
    st.html("\n".join(html_parts))


def _render_tool_results(tool_data_list: list, msg_idx: int = 0) -> None:
    """Route tool results to the correct card renderer."""
    spatial_data = []
    for block_idx, item in enumerate(tool_data_list):
        tool_name = item.get("tool_name", "")
        data = item.get("data")
        if not data:
            continue

        if tool_name == "search_flights":
            _render_flight_cards(data)
        elif tool_name == "search_hotels":
            _render_hotel_cards(data, msg_idx, block_idx)
            for p in data:
                p["category"] = "Hotels"
            spatial_data.extend(data)
        elif tool_name == "search_local_places":
            # Handle new format (dict with category_label) and old format (list fallback)
            if isinstance(data, dict):
                label = data.get("category_label", "Places Found")
                places = data.get("places", [])
            else:
                label = "Places Found"
                places = data

            _render_place_cards(places, category_label=label)

            # Inject category into places for map differentiation
            for p in places:
                p["category"] = label

            spatial_data.extend(places)
        elif tool_name == "get_route_directions":
            _render_route_summary(data)

    if spatial_data:
        st.session_state.latest_spatial_data = spatial_data
        with st.container(border=True):
            st.markdown("### 📍 Location Map")
            render_map_in_streamlit(spatial_data, key=f"map_{msg_idx}")


def _render_route_summary(route_data: dict) -> None:
    """Render a rich, premium route summary card in the chat."""
    if not route_data:
        return

    origin = route_data.get("origin", "Origin")
    dest = route_data.get("destination", "Destination")
    dist = route_data.get("distance", "—")
    dur = route_data.get("duration", "—")
    summary = route_data.get("summary", "")
    steps = route_data.get("steps", [])
    mode = route_data.get("mode", "driving")

    _MODE_ICON = {"driving": "🚗", "walking": "🚶", "transit": "🚌", "bicycling": "🚲"}
    mode_icon = _MODE_ICON.get(mode, "🧭")

    # Strip HTML tags from step instructions
    def _strip(html: str) -> str:
        return re.sub(r"<[^>]+>", " ", html).strip()

    steps_html = ""
    for i, step in enumerate(steps[:5], 1):
        instr = _strip(step.get("instruction", ""))
        sdist = step.get("distance", "")
        steps_html += f"""
        <div class="route-step-row">
            <div class="route-step-number">{i}</div>
            <div class="route-step-content">
                <span class="route-step-instruction">{instr}</span>
                <span class="route-step-distance">· {sdist}</span>
            </div>
        </div>"""

    steps_section = (
        f"""
        <div class="route-steps-section">
            <div class="route-steps-title">Turn-by-turn</div>
            {steps_html}
        </div>"""
        if steps_html
        else ""
    )

    via_line = f'<div class="route-via-line">via {summary}</div>' if summary else ""

    st.html(
        f"""
    <div class="route-summary-card">

        <!-- Header row -->
        <div class="route-header-row">
            <div class="route-header-icon">{mode_icon}</div>
            <div>
                <div class="route-header-title">Route Found</div>
                <div class="route-header-subtitle">Directions · {mode.title()}</div>
            </div>
        </div>

        <!-- Origin → Destination -->
        <div class="route-locations-row">
            <div class="route-origin-badge" title="{origin}">{origin}</div>
            <div class="route-arrow">→</div>
            <div class="route-destination-badge" title="{dest}">{dest}</div>
        </div>
        {via_line}

        <!-- Stats row -->
        <div class="route-stats-row">
            <div class="route-stat-box">
                <span class="route-stat-icon">📏</span>
                <div>
                    <div class="route-stat-label">Distance</div>
                    <div class="route-stat-value">{dist}</div>
                </div>
            </div>
            <div class="route-stat-box">
                <span class="route-stat-icon">⏱️</span>
                <div>
                    <div class="route-stat-label">Duration</div>
                    <div class="route-stat-value">{dur}</div>
                </div>
            </div>
        </div>

        {steps_section}
    </div>
    """,
        unsafe_allow_javascript=True,
    )


# ── Main Layout ────────────────────────────────────────────────────────────────
# ── Display Chat History ───────────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for i, msg in enumerate(st.session_state.messages):
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            content = getattr(msg, "text", msg.content)

            # If this is an assistant message, render its research traces
            if role == "assistant" and i in st.session_state.traces:
                with st.status("Researched", state="complete", expanded=False):
                    for step in st.session_state.traces[i]:
                        for line in step.get("friendly_items", []):
                            with st.expander(line["text"], expanded=False):
                                if line.get("data"):
                                    st.json(line["data"], expanded=1)

            # If this message has associated tool results, render cards
            if i in st.session_state.tool_results:
                _render_tool_results(st.session_state.tool_results[i], i)
            st.markdown(content)


# ── Chat Input ─────────────────────────────────────────────────────────────────
# Handle chat input outside columns to keep it fixed at the bottom (Standard Streamlit)
# ── Example prompt prefill via JS ─────────────────────────────────────────────
# st.chat_input has no `value` param, so we inject the text into the DOM instead.
pending = st.session_state.pop("pending_prefill", None)
if pending:
    # Escape for JS string literal
    escaped = pending.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    st.html(
        f"""
    <script>
        (function tryInject() {{
            const inputs = document.querySelectorAll('textarea[data-testid="stChatInputTextArea"]');
            if (inputs.length === 0) {{ setTimeout(tryInject, 150); return; }}
            const input = inputs[inputs.length - 1];
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(input, `{escaped}`);
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.focus();
        }})();
    </script>
    """,
        unsafe_allow_javascript=True,
    )

user_input = st.chat_input("Where would you like to travel?")

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    user_msg = HumanMessage(content=user_input)
    st.session_state.messages.append(user_msg)

    # ── Log the user's turn ────────────────────────────────────────────────
    _log: TravelPlannerLogger = st.session_state.logger
    _log.log_separator("New Turn")
    _log.log_user(user_input)

    # ── Check Testing Cache ────────────────────────────────────────────────────
    testing_cache = load_testing_cache()
    cached_turn = testing_cache.get(user_input)

    if cached_turn:
        with st.chat_message("assistant"):
            st.info("⚡ **Testing Cache Hit:** Loaded response instantly!")
            ai_text = cached_turn["ai_response"]
            tool_data_list = cached_turn["tool_data_list"]

            if tool_data_list:
                msg_idx = len(st.session_state.messages)
                _render_tool_results(tool_data_list, msg_idx)

            st.markdown(ai_text)

            cached_ai_msg = AIMessage(content=ai_text)
            st.session_state.messages.append(cached_ai_msg)

            if tool_data_list:
                msg_idx = len(st.session_state.messages) - 1
                st.session_state.tool_results[msg_idx] = tool_data_list

            _log.log_ai(ai_text)
    else:
        # Run the graph
        with st.chat_message("assistant"):
            status_container = st.status("Researching…", expanded=False)

            current_traces = []
            tool_data_list = []
            final_ai_response = None
            _seen_tool_ids: set[str] = set()

            # ── Label & phrase maps ──────────────────────────────────────────────
            # Nodes to silently skip logging/displaying if they have no messages
            _SKIP_NODES = {"supervisor"}

            # Human-friendly tool call phrases
            _TOOL_CALL_PHRASES = {
                "search_flights": "🛫 Searching for flights",
                "search_hotels": "🏨 Searching for hotels",
                "search_local_places": "📍 Looking up local places",
                "get_route_directions": "🗺️ Getting route directions",
            }

            # Human-friendly tool output phrases
            _TOOL_OUTPUT_PHRASES = {
                "search_flights": "Flight results",
                "search_hotels": "Hotel results",
                "search_local_places": "Local places",
                "get_route_directions": "Route details",
            }

            # ── Stream updates and log incrementally ────────────────────────────
            for chunk in st.session_state.graph.stream(
                cast(
                    Any,
                    {
                        "messages": st.session_state.messages,
                        "user_location": st.session_state.get("user_location"),
                        "itinerary": None,
                    },
                ),
                stream_mode="updates",
            ):
                for node_name, node_output in chunk.items():
                    # Silently skip internal routing nodes unless they contain messages
                    if node_name in _SKIP_NODES and not node_output.get("messages"):
                        _log.log_node(node_name)
                        continue

                    _log.log_node(node_name)

                    # Update top-level status header
                    status_container.update(
                        label="Researching…",
                    )

                    if not node_output or not isinstance(node_output, dict):
                        continue

                    node_messages = node_output.get("messages", [])

                    # ── Collect tool calls & outputs ────────────────────────────
                    node_tool_calls: list[dict] = []
                    node_tool_outputs: list[dict] = []
                    friendly_lines: list[str] = []

                    for msg in node_messages:
                        if isinstance(msg, AIMessage):
                            for tc in getattr(msg, "tool_calls", []) or []:
                                tc_id = tc.get("id", "")
                                if tc_id not in _seen_tool_ids:
                                    _seen_tool_ids.add(tc_id)
                                    _log.log_tool_call(
                                        tc.get("name", "unknown"), tc.get("args")
                                    )
                                    node_tool_calls.append(tc)
                            if msg.content:
                                final_ai_response = msg

                        elif isinstance(msg, ToolMessage):
                            _log.log_tool_output(msg.name or "tool", msg.content)
                            raw_output = msg.content
                            parsed_output = None
                            if isinstance(raw_output, str):
                                try:
                                    parsed_output = json.loads(raw_output)
                                    tool_data_list.append(
                                        {
                                            "tool_name": msg.name,
                                            "data": parsed_output,
                                        }
                                    )
                                except json.JSONDecodeError, TypeError:
                                    pass
                            node_tool_outputs.append(
                                {
                                    "name": msg.name or "tool",
                                    "raw": raw_output,
                                    "parsed": parsed_output,
                                }
                            )

                    # ── Build friendly items for this step ──────────────────────
                    friendly_items: list[dict] = []
                    for tc in node_tool_calls:
                        phrase = _TOOL_CALL_PHRASES.get(
                            tc.get("name", ""), f"🔧 Running {tc.get('name', 'tool')}…"
                        )
                        friendly_items.append({"text": phrase, "data": tc.get("args")})

                    for out in node_tool_outputs:
                        phrase = _TOOL_OUTPUT_PHRASES.get(
                            out["name"], f"📦 Got output from {out['name']}"
                        )
                        # Prefer parsed JSON for the data display
                        data = (
                            out["parsed"] if out["parsed"] is not None else out["raw"]
                        )
                        friendly_items.append({"text": phrase, "data": data})

                    # ── Render as separate expanders ──────────────────
                    if friendly_items:
                        for item in friendly_items:
                            with status_container.expander(
                                item["text"], expanded=False
                            ):
                                if item.get("data"):
                                    st.json(item["data"], expanded=1)

                    current_traces.append(
                        {
                            "friendly_items": friendly_items,
                        }
                    )

            status_container.update(label="Done", state="complete", expanded=True)

            if final_ai_response and final_ai_response.content:
                ai_text = getattr(final_ai_response, "text", final_ai_response.content)
                if not isinstance(ai_text, str):
                    ai_text = str(ai_text)

                msg_idx = len(st.session_state.messages)
                st.session_state.traces[msg_idx] = current_traces

                # Render cards if we have structured tool data
                if tool_data_list:
                    _render_tool_results(tool_data_list, msg_idx)

                st.markdown(ai_text)

                # Log the AI's final response
                _log.log_ai(ai_text)

                st.session_state.messages.append(final_ai_response)

                # Store tool results keyed to the message index for replay
                if tool_data_list:
                    msg_idx = len(st.session_state.messages) - 1
                    st.session_state.tool_results[msg_idx] = tool_data_list

                # Save to testing cache
                testing_cache[user_input] = {
                    "ai_response": ai_text,
                    "tool_data_list": tool_data_list,
                }
                save_testing_cache(testing_cache)
            else:
                fallback = "I couldn't find any results. Could you try rephrasing your request?"
                st.markdown(fallback)
                st.session_state.messages.append(AIMessage(content=fallback))
                _log.log_ai(fallback)
