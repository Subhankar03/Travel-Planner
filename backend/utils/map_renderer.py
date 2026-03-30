import folium
from streamlit_folium import st_folium
import streamlit as st


# ── Map Rendering Logic ───────────────────────────────────────────────────────
def create_map(locations: list):
    """
    Create a folium Map object for a list of locations.
    Each location should be a dict with:
    - name: str
    - gps_coordinates: {latitude: float, longitude: float}
    - thumbnail: str (optional)
    - price: str or rate_per_night (optional)
    - rating: float (optional)
    """
    if not locations:
        return None

    # Filter out locations without coordinates
    valid_locations = [
        loc for loc in locations 
        if loc.get('gps_coordinates') and 
           loc['gps_coordinates'].get('latitude') and 
           loc['gps_coordinates'].get('longitude')
    ]

    if not valid_locations:
        return None

    # Center the map at the average of all coordinates
    avg_lat = sum(loc['gps_coordinates']['latitude'] for loc in valid_locations) / len(valid_locations)
    avg_lng = sum(loc['gps_coordinates']['longitude'] for loc in valid_locations) / len(valid_locations)

    m = folium.Map(location=[avg_lat, avg_lng], zoom_start=12, control_scale=True)

    color_palette = ['blue', 'green', 'purple', 'orange', 'darkred', 'cadetblue', 'darkpurple', 'pink', 'lightblue', 'lightgreen']
    category_colors = {}

    for loc in valid_locations:
        category = loc.get('category', 'Default')
        if category not in category_colors:
            # Hardcode red for Hotels if it's the specific Hotels category
            if category == 'Hotels' or "hotel" in str(loc.get('type', '')).lower():
                category_colors[category] = 'red'
            else:
                cc_idx = len([c for c in category_colors.values() if c != 'red']) % len(color_palette)
                category_colors[category] = color_palette[cc_idx]

        coords = [loc['gps_coordinates']['latitude'], loc['gps_coordinates']['longitude']]
        name = loc.get('name') or loc.get('title', 'Location')
        
        # Determine price/rate
        price = loc.get('price') or loc.get('rate_per_night') or loc.get('rate')
        if isinstance(price, dict):
            price = price.get('lowest') or price.get('before_taxes_fees')
            
        thumb = loc.get('thumbnail')
        rating = loc.get('overall_rating') or loc.get('rating')

        # Construct Popup HTML (Compact Thumbnail + Name + Price)
        popup_html = """
        <div style="font-family: 'Inter', sans-serif; width: 180px; padding: 5px;">
        """
        if thumb:
            popup_html += f'<img src="{thumb}" style="width: 100%; height: 100px; object-fit: cover; border-radius: 8px; margin-bottom: 8px;">'
        
        popup_html += f'<div style="font-weight: 600; font-size: 14px; color: #1e293b; margin-bottom: 4px;">{name}</div>'
        
        if rating:
            popup_html += f'<div style="color: #f59e0b; font-size: 12px; margin-bottom: 4px;">⭐ {rating}</div>'
            
        if price:
            popup_html += f'<div style="font-weight: 700; color: #0f172a; font-size: 14px;">{price}</div>'
            
        popup_html += "</div>"
        
        iframe = folium.IFrame(popup_html, width=200, height=180 if thumb else 100)  # type: ignore
        popup = folium.Popup(iframe, max_width=200)

        folium.Marker(
            location=coords,
            popup=popup,
            tooltip=name,
            icon=folium.Icon(color=category_colors[category], icon="info-sign")
        ).add_to(m)

    return m

def render_map_in_streamlit(locations: list, key: str = "map"):
    """Render the folium map using st_folium."""
    m = create_map(locations)
    if m:
        st_folium(m, width=None, height=500, key=key, use_container_width=True)
    else:
        st.info("📍 No locations with coordinates found to display on the map.")
