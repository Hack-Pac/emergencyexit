import requests
import json
import time
import logging
from geopy.distance import geodesic

FIRE_PROXIMITY_THRESHOLD_MILES = 0.1

fake_fire_coords = [
    (34.104499, -117.199153)  # Fake fire coordinate for testing
]

def geocode_address(address):
    NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org/search'

    try:
        response = requests.get(
            NOMINATIM_BASE_URL,
            params={
                'q': address,
                'format': 'json'
            },
            headers={
                'User-Agent': 'emergency-exit-app'
            },
            timeout=10
        )
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return None

    if response.status_code != 200:
        print(f"Error: Failed to geocode address '{address}'. Status Code: {response.status_code}")
        return None

    data = response.json()
    if len(data) > 0:
        coords = data[0]
        return [float(coords['lat']), float(coords['lon'])]
    else:
        print(f"Error: No results found for address '{address}'.")
        return None

def get_current_incidents():
    API_URL = "https://incidents.fire.ca.gov/umbraco/api/IncidentApi/List?inactive=false"
    logging.info("Fetching current incidents from CAL FIRE API.")
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        incidents = response.json()
        logging.info(f"Fetched {len(incidents)} incidents.")
        return incidents
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while fetching the incidents: {e}")
        return []

def get_fire_coordinates(incidents):
    fire_coords = fake_fire_coords[:]  # Start with the fake fire coordinates
    for incident in incidents:
        if incident.get('Latitude') and incident.get('Longitude'):
            lat = float(incident['Latitude'])
            lon = float(incident['Longitude'])
            fire_coords.append((lat, lon))
    return fire_coords

def is_near_fire(coord, fires, max_distance_miles=FIRE_PROXIMITY_THRESHOLD_MILES):
    for fire_coord in fires:
        try:
            distance = geodesic(coord, fire_coord).miles
            if distance <= max_distance_miles:
                return True
        except ValueError:
            continue
    return False

def get_route(start_coords, end_coords, avoid_polygons=None, route_differentiation=0.5):
    try:
        params = {
            'api_key': ORS_API_KEY,
            'start': f"{start_coords[1]},{start_coords[0]}",
            'end': f"{end_coords[1]},{end_coords[0]}",
            'alternative_routes': json.dumps({
                'share_factor': route_differentiation,
                'target_count': 1
            })
        }
        if avoid_polygons:
            params['options'] = json.dumps({
                "avoid_polygons": {
                    "type": "Polygon",
                    "coordinates": [avoid_polygons]
                }
            })
        response = requests.get(
            ORS_BASE_URL,
            params=params,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Network error while getting directions: {e}")
        return None

def create_avoidance_box(center_coord, distance_miles=1):
    delta_lat = distance_miles / 69.0  # Approximate miles per degree latitude
    delta_lon = distance_miles / (69.0 * abs(center_coord[0]))  # Adjust for longitude
    lat, lon = center_coord
    return [
        [lon - delta_lon, lat - delta_lat],
        [lon + delta_lon, lat - delta_lat],
        [lon + delta_lon, lat + delta_lat],
        [lon - delta_lon, lat + delta_lat],
        [lon - delta_lon, lat - delta_lat]
    ]

ORS_API_KEY = '5b3ce3597851110001cf624827e2ea9c22414c99883a500d4dfb27e8'
ORS_BASE_URL = 'https://api.openrouteservice.org/v2/directions/driving-car'

start_address = '11 Lindberg, Irvine CA'
end_address = '7701 Church St, Highland, CA 92346'

MAX_RETRIES = 3
for i in range(MAX_RETRIES):
    start_coords = geocode_address(start_address)
    end_coords = geocode_address(end_address)
    if start_coords and end_coords:
        break
    else:
        print(f"Retrying... ({i + 1}/{MAX_RETRIES})")
        time.sleep(2)

if not start_coords or not end_coords:
    print('Error: Unable to geocode one or both addresses.')
else:
    incidents = get_current_incidents()
    fires = get_fire_coordinates(incidents)

    if is_near_fire(end_coords, fires, max_distance_miles=10):
        print("Warning: The destination is within 10 miles of an active fire.")
        print("Proceed with caution or consider an alternative destination.")

    avoid_polygons = []
    processed_coords = set()
    num_routes_to_generate = 50
    current_route_differentiation = 0.5
    while num_routes_to_generate > 0:
        directions = get_route(start_coords, end_coords, avoid_polygons, current_route_differentiation)
        if not directions:
            print("Error: Unable to get route directions.")
            break

        route_passes_near_fire = False
        for feature in directions.get('features', []):
            if 'geometry' in feature:
                for coord in feature['geometry']['coordinates']:
                    if len(coord) >= 2 and tuple(coord) not in processed_coords and is_near_fire((coord[1], coord[0]), fires):
                        print(f"Route passes near an active fire at coordinates: {coord}")
                        route_passes_near_fire = True
                        processed_coords.add(tuple(coord))
                        avoid_box = create_avoidance_box((coord[1], coord[0]))
                        avoid_polygons.append(avoid_box)
                        break
                if route_passes_near_fire:
                    break

        if route_passes_near_fire:
            print("Recalculating route to avoid active fires...")
            time.sleep(2)  # Delay before recalculating
            num_routes_to_generate -= 1
            current_route_differentiation += 5  # Increase differentiation to try a more diverse route
        else:
            print("Safe route found.")
            print(json.dumps(directions, indent=2))
            break
