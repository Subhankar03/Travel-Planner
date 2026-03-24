"""SerpAPI-backed tools for the Travel Planner agent."""
import json
import os
from pathlib import Path

import serpapi
from dotenv import load_dotenv
from langchain_core.tools import tool
from pydantic import BaseModel, Field

load_dotenv()
_client = serpapi.Client(api_key=os.getenv('SERPAPI_KEY'))


# ── Schema Data ────────────────────────────────────────────────────────────────
_SCHEMAS_DIR = Path(__file__).parent / 'serpapi_schemas'

_HOTEL_PROPERTY_TYPES = (_SCHEMAS_DIR / 'google-hotels-property-types.json').read_text(encoding='utf-8').strip('{}')
_VR_PROPERTY_TYPES = (_SCHEMAS_DIR / 'google-hotels-vacation-rentals-property-types.json').read_text(encoding='utf-8').strip('{}')
_HOTEL_AMENITIES = (_SCHEMAS_DIR / 'google-hotels-amenities.json').read_text(encoding='utf-8').strip('{}')
_VR_AMENITIES = (_SCHEMAS_DIR / 'google-hotels-vacation-rentals-amenities.json').read_text(encoding='utf-8').strip('{}')


# ── Input Schemas ──────────────────────────────────────────────────────────────
class SearchFlightsInput(BaseModel):
    """Input schema for the search_flights tool."""

    departure_id: str = Field(
        description='Departure airport IATA code or location kgmid. An airport code is an uppercase 3-letter code (e.g. "CCU" for Kolkata, "DEL" for Delhi). A location kgmid starts with "/m/" (e.g. "/m/0vzm" for Austin, TX). Multiple airports can be separated by commas.'
    )
    arrival_id: str = Field(
        description='Arrival airport IATA code or location kgmid. An airport code is an uppercase 3-letter code (e.g. "BLR" for Bangalore, "BOM" for Mumbai). A location kgmid starts with "/m/". Multiple airports can be separated by commas.'
    )
    outbound_date: str = Field(
        description='Outbound date in YYYY-MM-DD format (e.g. "2026-01-15").'
    )
    return_date: str | None = Field(
        default=None,
        description='Return date in YYYY-MM-DD format (e.g. "2026-01-21"). Required when trip_type is 1 (Round trip).',
    )
    adults: int = Field(
        default=1,
        description='Number of adult passengers. Default is 1.',
    )
    children: int = Field(
        default=0,
        description='Number of child passengers. Default is 0.',
    )
    max_price: int | None = Field(
        default=None,
        description='Maximum ticket price filter (in the selected currency).',
    )
    travel_class: int = Field(
        default=1,
        description='Cabin class: 1 = Economy (default), 2 = Premium economy, 3 = Business, 4 = First.',
    )
    currency: str = Field(
        default='INR',
        description='Currency code for returned prices (e.g. "INR", "USD", "EUR"). Defaults to "INR".',
    )
    stops: int = Field(
        default=0,
        description='Maximum number of stops: 0 = Any number of stops (default), 1 = Nonstop only, 2 = 1 stop or fewer, 3 = 2 stops or fewer.',
    )
    sort_by: int = Field(
        default=1,
        description='Sorting order of results: 1 = Top flights (default), 2 = Price, 3 = Departure time, 4 = Arrival time, 5 = Duration, 6 = Emissions.',
    )
    trip_type: int = Field(
        default=1,
        description='Type of trip: 1 = Round trip (default), 2 = One way.',
    )


class SearchHotelsInput(BaseModel):
    """Input schema for the search_hotels tool."""

    query: str = Field(
        description='Search query for hotels, just like a regular Google Hotels search (e.g. "hotels in Bangalore", "5 star hotels near Connaught Place Delhi").'
    )
    check_in_date: str = Field(
        description='Check-in date in YYYY-MM-DD format (e.g. "2026-01-15").'
    )
    check_out_date: str = Field(
        description='Check-out date in YYYY-MM-DD format (e.g. "2026-01-16").'
    )
    adults: int = Field(
        default=2,
        description='Number of adult guests. Default is 2.',
    )
    children: int = Field(
        default=0,
        description='Number of child guests. Default is 0.',
    )
    currency: str = Field(
        default='INR',
        description='Currency code for returned prices (e.g. "INR", "USD", "EUR"). Defaults to "INR".',
    )
    sort_by: int | None = Field(
        default=None,
        description='Sort order for results (omit for relevance): 3 = Lowest price, 8 = Highest rating, 13 = Most reviewed.',
    )
    min_price: int | None = Field(
        default=None,
        description='Minimum price per night filter (in the selected currency).',
    )
    max_price: int | None = Field(
        default=None,
        description='Maximum price per night filter (in the selected currency).',
    )
    rating: int | None = Field(
        default=None,
        description='Minimum guest rating filter: 7 = 3.5+, 8 = 4.0+, 9 = 4.5+.',
    )
    hotel_class: str | None = Field(
        default=None,
        description='Hotel star class filter. Single value or comma-separated: "2" = 2-star, "3" = 3-star, "4" = 4-star, "5" = 5-star. Example: "4" or "3,4,5".',
    )
    vacation_rentals: bool = Field(
        default=False,
        description='If True, search for vacation rentals instead of hotels. This changes which property_types and amenities codes are valid.',
    )
    property_types: str | None = Field(
        default=None,
        description=f'Filter by property type. Single code or comma-separated. Hotels: {_HOTEL_PROPERTY_TYPES}. Vacation rentals: {_VR_PROPERTY_TYPES}. Example: "17" or "17,18".',
    )
    amenities: str | None = Field(
        default=None,
        description=f'Filter by amenities. Single code or comma-separated. Hotels: {_HOTEL_AMENITIES}. Vacation rentals: {_VR_AMENITIES}. Example: "35,7" or "15,32".',
    )
    bedrooms: int | None = Field(
        default=None,
        description='Minimum number of bedrooms. Only applicable when vacation_rentals is True.',
    )
    bathrooms: int | None = Field(
        default=None,
        description='Minimum number of bathrooms. Only applicable when vacation_rentals is True.',
    )


class SearchLocalPlacesInput(BaseModel):
    """Input schema for the search_local_places tool."""

    query: str = Field(
        description='What to search for, just like a regular Google Local search (e.g. "best pizza restaurants", "tourist attractions", "coffee shops").'
    )
    location: str = Field(
        description='Location from which the search should originate. Specify at the city level for best results (e.g. "Bangalore, Karnataka, India", "Paris, France").'
    )


# ── Tools ──────────────────────────────────────────────────────────────────────
@tool(args_schema=SearchFlightsInput)
def search_flights(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: str | None = None,
    adults: int = 1,
    children: int = 0,
    travel_class: int = 1,
    currency: str = 'INR',
    stops: int = 0,
    sort_by: int = 1,
    trip_type: int = 1,
    max_price: int | None = None,
) -> str:
    """Search for flights on Google Flights via SerpAPI.

    Returns a JSON string with the best flights and other flights found.
    """
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
    if children:
        params['children'] = str(children)
    if max_price:
        params['max_price'] = str(max_price)
    if return_date and trip_type == 1:
        params['return_date'] = return_date

    results = _client.search(params)

    # Extract relevant data
    output: dict = {}
    if 'best_flights' in results:
        output['best_flights'] = _summarise_flights(results['best_flights'])
    if 'other_flights' in results:
        output['other_flights'] = _summarise_flights(results['other_flights'])
    if 'airports' in results:
        output['airports'] = results['airports']
    
    # Add the overall search link for booking
    output['search_url'] = results.get('search_metadata', {}).get('google_flights_url')

    return json.dumps(output, indent=2, ensure_ascii=False)


@tool(args_schema=SearchHotelsInput)
def search_hotels(
    query: str,
    check_in_date: str,
    check_out_date: str,
    adults: int = 2,
    children: int = 0,
    currency: str = 'INR',
    sort_by: int | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    rating: int | None = None,
    hotel_class: str | None = None,
    vacation_rentals: bool = False,
    property_types: str | None = None,
    amenities: str | None = None,
    bedrooms: int | None = None,
    bathrooms: int | None = None,
) -> str:
    """Search for hotels or vacation rentals on Google Hotels via SerpAPI.

    Returns a JSON string with hotel/rental properties.
    """
    params: dict = {
        'engine': 'google_hotels',
        'q': query,
        'hl': 'en',
        'gl': 'in',
        'check_in_date': check_in_date,
        'check_out_date': check_out_date,
        'adults': str(adults),
        'currency': currency,
    }
    # `children` is not supported by the vacation-rentals engine
    if children and not vacation_rentals:
        params['children'] = str(children)
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
    if vacation_rentals:
        params['vacation_rentals'] = 'true'
    if property_types is not None:
        params['property_types'] = property_types
    if amenities is not None:
        params['amenities'] = amenities
    if bedrooms is not None:
        params['bedrooms'] = str(bedrooms)
    if bathrooms is not None:
        params['bathrooms'] = str(bathrooms)

    results = _client.search(params)

    # Extract relevant data
    properties = results.get('properties', [])
    output = [_summarise_hotel(p) for p in properties[:10]]

    return json.dumps(output, indent=2, ensure_ascii=False)


@tool(args_schema=SearchLocalPlacesInput)
def search_local_places(
    query: str,
    location: str,
) -> str:
    """Search for local places (restaurants, attractions, etc.) via Google Local.

    Returns a JSON string with local results including name, rating, address, etc.
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
                'airline_logo': leg.get('airline_logo'),
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
            'airline_logo': group.get('airline_logo'),
            'booking_token': group.get('booking_token'),
        })
    return summaries


def _summarise_hotel(prop: dict) -> dict:
    """Extract the most useful fields from a hotel property."""
    images = prop.get('images', [])
    thumbnail = images[0].get('thumbnail') if images else None
    original_images = [img.get('original_image') for img in images if img.get('original_image')]
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
        'thumbnail': thumbnail,
        'images': original_images,
        'link': prop.get('link'),
        'nearby_places': [
            {
                'name': np.get('name'),
                'transport': np.get('transportations', [{}])[0].get('type'),
                'duration': np.get('transportations', [{}])[0].get('duration'),
            }
            for np in prop.get('nearby_places', [])
        ],
    }


def _summarise_local(result: dict) -> dict:
    """Extract the most useful fields from a local result."""
    description = result.get('description')
    if description:
        description = description.strip('" ')
    return {
        'title': result.get('title'),
        'type': result.get('type'),
        'rating': result.get('rating'),
        'reviews': result.get('reviews'),
        'price': result.get('price'),
        'description': description,
        'address': result.get('address'),
        'thumbnail': result.get('thumbnail'),
        'service_options': result.get('service_options'),
    }
