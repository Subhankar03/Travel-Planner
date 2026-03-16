"""SerpAPI-backed tools for the Travel Planner agent."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import serpapi
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

# ── SerpAPI Client ─────────────────────────────────────────────────────────────
_client = serpapi.Client(api_key=os.getenv('SERPAPI_KEY'))

# ── Schema Loader ──────────────────────────────────────────────────────────────
_SCHEMA_DIR = Path(__file__).parent / 'serpapi_schemas'


def _load_schema(engine: str) -> dict:
    """Load the parameter schema for a given SerpAPI engine."""
    path = _SCHEMA_DIR / f'{engine}.json'
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# ── Date Helper ────────────────────────────────────────────────────────────────
def resolve_date(date_str: str) -> str:
    """Resolve a date string to YYYY-MM-DD format.

    Accepts absolute dates (2026-03-20) or relative expressions
    like 'today', 'tomorrow', '3 days later', 'next week', etc.
    """
    date_str = date_str.strip().lower()
    today = datetime.now().date()

    if date_str == 'today':
        return today.isoformat()
    if date_str == 'tomorrow':
        return (today + timedelta(days=1)).isoformat()
    if 'days later' in date_str or 'days from now' in date_str:
        parts = date_str.split()
        try:
            n = int(parts[0])
            return (today + timedelta(days=n)).isoformat()
        except (ValueError, IndexError):
            pass
    if date_str == 'next week':
        return (today + timedelta(weeks=1)).isoformat()

    # Assume it's already YYYY-MM-DD
    return date_str


# ── Tools ──────────────────────────────────────────────────────────────────────
@tool
def search_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: str | None = None,
    adults: int = 1,
    travel_class: int = 1,
    currency: str = 'INR',
    stops: int = 0,
    sort_by: int = 1,
    trip_type: int = 1,
) -> str:
    """Search for flights on Google Flights via SerpAPI.

    Args:
        departure_id: Departure airport IATA code (e.g. 'CCU', 'DEL').
        arrival_id: Arrival airport IATA code (e.g. 'BLR', 'BOM').
        outbound_date: Outbound date (YYYY-MM-DD or relative like 'tomorrow').
        return_date: Return date (YYYY-MM-DD or relative). Required for round trips.
        adults: Number of adults.
        travel_class: 1=Economy, 2=Premium Economy, 3=Business, 4=First.
        currency: Currency code (e.g. 'INR', 'USD').
        stops: 0=Any, 1=Nonstop, 2=1 stop or fewer, 3=2 stops or fewer.
        sort_by: 1=Top flights, 2=Price, 3=Departure time, 4=Arrival time, 5=Duration.
        trip_type: 1=Round trip, 2=One way.

    Returns:
        A JSON string with the best flights and other flights found.
    """
    outbound_date = resolve_date(outbound_date)
    params: dict = {
        'engine': 'google_flights',
        'hl': 'en',
        'gl': 'in',
        'departure_id': departure_id.upper(),
        'arrival_id': arrival_id.upper(),
        'outbound_date': outbound_date,
        'currency': currency,
        'type': str(trip_type),
        'travel_class': str(travel_class),
        'adults': str(adults),
        'stops': str(stops),
        'sort_by': str(sort_by),
    }
    if return_date and trip_type == 1:
        params['return_date'] = resolve_date(return_date)

    results = _client.search(params)

    # Extract relevant data
    output: dict = {}
    if 'best_flights' in results:
        output['best_flights'] = _summarise_flights(results['best_flights'])
    if 'other_flights' in results:
        output['other_flights'] = _summarise_flights(results['other_flights'])
    if 'airports' in results:
        output['airports'] = results['airports']

    return json.dumps(output, indent=2, ensure_ascii=False)


@tool
def search_hotels(
    query: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 2,
    currency: str = 'INR',
    sort_by: int | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    rating: int | None = None,
    hotel_class: str | None = None,
    free_cancellation: bool | None = None,
) -> str:
    """Search for hotels on Google Hotels via SerpAPI.

    Args:
        query: Search query (e.g. 'hotels in Bangalore').
        check_in_date: Check-in date (YYYY-MM-DD or relative).
        check_out_date: Check-out date (YYYY-MM-DD or relative).
        adults: Number of adults.
        currency: Currency code (e.g. 'INR', 'USD').
        sort_by: 3=Lowest price, 8=Highest rating, 13=Most reviewed.
        min_price: Minimum price filter.
        max_price: Maximum price filter.
        rating: 7=3.5+, 8=4.0+, 9=4.5+.
        hotel_class: Hotel star class, e.g. '3' or '3,4,5'.
        free_cancellation: Filter for free cancellation.

    Returns:
        A JSON string with hotel properties.
    """
    params: dict = {
        'engine': 'google_hotels',
        'q': query,
        'hl': 'en',
        'gl': 'in',
        'check_in_date': resolve_date(check_in_date),
        'check_out_date': resolve_date(check_out_date),
        'adults': str(adults),
        'currency': currency,
    }
    if sort_by is not None:
        params['sort_by'] = str(sort_by)
    if min_price is not None:
        params['min_price'] = str(min_price)
    if max_price is not None:
        params['max_price'] = str(max_price)
    if rating is not None:
        params['rating'] = str(rating)
    if hotel_class is not None:
        params['hotel_class'] = hotel_class
    if free_cancellation is not None:
        params['free_cancellation'] = str(free_cancellation).lower()

    results = _client.search(params)

    # Extract relevant data
    properties = results.get('properties', [])
    output = [_summarise_hotel(p) for p in properties[:10]]

    return json.dumps(output, indent=2, ensure_ascii=False)


@tool
def search_local_places(
    query: str,
    location: str,
) -> str:
    """Search for local places (restaurants, attractions, etc.) via Google Local.

    Args:
        query: What to search for (e.g. 'best pizza restaurants').
        location: Location string (e.g. 'Bangalore, Karnataka, India').

    Returns:
        A JSON string with local results including name, rating, address, etc.
    """
    params: dict = {
        'engine': 'google_local',
        'q': query,
        'location': location,
        'google_domain': 'google.com',
        'gl': 'in',
        'hl': 'en',
    }

    results = _client.search(params)

    local_results = results.get('local_results', [])
    output = [_summarise_local(r) for r in local_results[:10]]

    return json.dumps(output, indent=2, ensure_ascii=False)


# ── Summarisers ────────────────────────────────────────────────────────────────
def _summarise_flights(flight_groups: list[dict]) -> list[dict]:
    """Extract the most useful fields from a list of flight groups."""
    summaries = []
    for group in flight_groups:
        legs = []
        for leg in group.get('flights', []):
            legs.append({
                'airline': leg.get('airline'),
                'flight_number': leg.get('flight_number'),
                'departure': f"{leg.get('departure_airport', {}).get('id')} at {leg.get('departure_airport', {}).get('time')}",
                'arrival': f"{leg.get('arrival_airport', {}).get('id')} at {leg.get('arrival_airport', {}).get('time')}",
                'duration_min': leg.get('duration'),
                'airplane': leg.get('airplane'),
                'travel_class': leg.get('travel_class'),
                'legroom': leg.get('legroom'),
            })
        layovers = []
        for lo in group.get('layovers', []):
            layovers.append({
                'airport': lo.get('name'),
                'duration_min': lo.get('duration'),
                'overnight': lo.get('overnight', False),
            })
        summaries.append({
            'legs': legs,
            'layovers': layovers,
            'total_duration_min': group.get('total_duration'),
            'price': group.get('price'),
            'type': group.get('type'),
        })
    return summaries


def _summarise_hotel(prop: dict) -> dict:
    """Extract the most useful fields from a hotel property."""
    return {
        'name': prop.get('name'),
        'description': prop.get('description'),
        'hotel_class': prop.get('hotel_class'),
        'overall_rating': prop.get('overall_rating'),
        'reviews': prop.get('reviews'),
        'rate_per_night': prop.get('rate_per_night', {}).get('lowest'),
        'total_rate': prop.get('total_rate', {}).get('lowest'),
        'check_in': prop.get('check_in_time'),
        'check_out': prop.get('check_out_time'),
        'amenities': prop.get('amenities', []),
        'nearby_places': [
            {
                'name': np.get('name'),
                'transport': np.get('transportations', [{}])[0].get('type'),
                'duration': np.get('transportations', [{}])[0].get('duration'),
            }
            for np in prop.get('nearby_places', [])
        ],
        'link': prop.get('link'),
    }


def _summarise_local(result: dict) -> dict:
    """Extract the most useful fields from a local result."""
    return {
        'title': result.get('title'),
        'type': result.get('type'),
        'rating': result.get('rating'),
        'reviews': result.get('reviews'),
        'price': result.get('price'),
        'description': result.get('description'),
        'address': result.get('address'),
        'service_options': result.get('service_options'),
    }
