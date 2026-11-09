
import os
from pathlib import Path
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.function_tool import FunctionTool


# --------------------------------------------------
# 1. Environment configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

MAPS_API_KEY = os.getenv("MAPS_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
PLACES_URL = "https://places.googleapis.com/v1/places:searchText"

if not MAPS_API_KEY:
    raise RuntimeError("MAPS_API_KEY is missing from .env")


# --------------------------------------------------
# 2. Common API error handler
# --------------------------------------------------

def api_error(response):
    try:
        details = response.json()
    except ValueError:
        details = response.text

    return {
        "status": "error",
        "http_status": response.status_code,
        "details": details
    }


# --------------------------------------------------
# 3. Decode Google's encoded polyline
# --------------------------------------------------

def decode_polyline(encoded):
    coordinates = []
    index = 0
    latitude = 0
    longitude = 0

    while index < len(encoded):

        values = []

        for _ in range(2):
            result = 0
            shift = 0

            while True:
                byte = ord(encoded[index]) - 63
                index += 1

                result |= (byte & 0x1f) << shift
                shift += 5

                if byte < 0x20:
                    break

            delta = (
                ~(result >> 1)
                if result & 1
                else result >> 1
            )

            values.append(delta)

        latitude += values[0]
        longitude += values[1]

        coordinates.append((
            latitude / 100000,
            longitude / 100000
        ))

    return coordinates


# --------------------------------------------------
# 4. Common Routes API function
# --------------------------------------------------

def calculate_route(origin, destination, mode="DRIVE"):

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": MAPS_API_KEY,
        "X-Goog-FieldMask": (
            "routes.distanceMeters,"
            "routes.duration,"
            "routes.polyline.encodedPolyline"
        )
    }

    payload = {
        "origin": {
            "address": origin
        },
        "destination": {
            "address": destination
        },
        "travelMode": mode,
        "units": "METRIC",
        "languageCode": "en-IN"
    }

    response = requests.post(
        ROUTES_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    if not response.ok:
        return api_error(response)

    data = response.json()
    routes = data.get("routes", [])

    if not routes:
        return {
            "status": "error",
            "message": "No route found."
        }

    route = routes[0]

    return {
        "status": "success",
        "distance_meters": route["distanceMeters"],
        "duration": route["duration"],
        "encoded_polyline": (
            route.get("polyline", {}).get("encodedPolyline")
        )
    }


# --------------------------------------------------
# 5. Get directions between two locations
# --------------------------------------------------

def get_directions(
    origin: str,
    destination: str,
    mode: str = "driving"
) -> dict:
    """
    Calculate route distance and duration.

    Args:
        origin: Starting location.
        destination: Destination location.
        mode: driving, walking, bicycling or transit.
    """

    mode_mapping = {
        "driving": "DRIVE",
        "walking": "WALK",
        "bicycling": "BICYCLE",
        "transit": "TRANSIT"
    }

    travel_mode = mode_mapping.get(mode.lower())

    if not travel_mode:
        return {
            "status": "error",
            "message": "Unsupported travel mode."
        }

    try:
        result = calculate_route(
            origin,
            destination,
            travel_mode
        )

        if result["status"] != "success":
            return result

        distance_km = (
            result["distance_meters"] / 1000
        )

        google_maps_link = (
            "https://www.google.com/maps/dir/?"
            + urlencode({
                "api": "1",
                "origin": origin,
                "destination": destination,
                "travelmode": mode.lower()
            })
        )

        return {
            "origin": origin,
            "destination": destination,
            "distance": f"{distance_km:.2f} km",
            "duration": result["duration"],
            "google_maps_link": google_maps_link
        }

    except requests.RequestException as error:
        return {
            "status": "error",
            "message": str(error)
        }


# --------------------------------------------------
# 6. Search places near route midpoint
# --------------------------------------------------

def search_places_on_route(
    origin: str,
    destination: str,
    place_type: str
) -> dict:
    """
    Search for businesses near the midpoint of a route.

    Args:
        origin: Starting location.
        destination: Destination location.
        place_type: restaurant, hospital, hotel,
                    petrol pump, ATM, etc.
    """

    try:

        # Step 1: Calculate route
        route = calculate_route(
            origin,
            destination
        )

        if route["status"] != "success":
            return route

        encoded = route.get("encoded_polyline")

        if not encoded:
            return {
                "status": "error",
                "message": "Route geometry unavailable."
            }

        # Step 2: Decode route polyline
        coordinates = decode_polyline(encoded)

        if not coordinates:
            return {
                "status": "error",
                "message": "Unable to decode route."
            }

        # Step 3: Identify route midpoint
        midpoint = coordinates[len(coordinates) // 2]

        latitude, longitude = midpoint

        # Step 4: Search Places API (New)
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": MAPS_API_KEY,
            "X-Goog-FieldMask": (
                "places.id,"
                "places.displayName,"
                "places.formattedAddress,"
                "places.rating,"
                "places.googleMapsUri"
            )
        }

        payload = {
            "textQuery": place_type,
            "pageSize": 5,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": 5000
                }
            }
        }

        response = requests.post(
            PLACES_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if not response.ok:
            return api_error(response)

        data = response.json()

        # Step 5: Format results
        places = []

        for place in data.get("places", []):

            places.append({
                "name": place.get(
                    "displayName", {}
                ).get("text"),

                "address": place.get(
                    "formattedAddress"
                ),

                "rating": place.get(
                    "rating", "N/A"
                ),

                "maps_link": place.get(
                    "googleMapsUri"
                )
            })

        return {
            "query": place_type,
            "origin": origin,
            "destination": destination,
            "search_center": {
                "latitude": latitude,
                "longitude": longitude
            },
            "total_results": len(places),
            "places": places
        }

    except requests.RequestException as error:
        return {
            "status": "error",
            "message": str(error)
        }


# --------------------------------------------------
# 7. Register ADK tools
# --------------------------------------------------

directions_tool = FunctionTool(get_directions)
places_tool = FunctionTool(search_places_on_route)


# --------------------------------------------------
# 8. Create Maps Agent
# --------------------------------------------------

root_agent = LlmAgent(
    model=GEMINI_MODEL,

    name="Maps_Agent",

    description=(
        "Google Maps assistant using Places API "
        "and Routes API."
    ),

    instruction="""
    You are a helpful Google Maps assistant.

    You have access to two tools:

    1. get_directions:
       Calculate distance and duration between
       two locations.

    2. search_places_on_route:
       Search for businesses near the midpoint
       of a route.

    Guidelines:

    - Always use tools for Maps information.
    - Never invent distances, durations or places.
    - Display business names, addresses and ratings.
    - Include Google Maps links when available.
    - Clearly mention when no results are found.
    - Keep answers concise and user friendly.
    """,

    tools=[
        directions_tool,
        places_tool
    ]
)
