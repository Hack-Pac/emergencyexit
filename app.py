from flask import Flask, render_template, request, jsonify
import requests
import json
import time
import logging
from geopy.distance import geodesic
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

FIRE_PROXIMITY_THRESHOLD_MILES = 0.1
CACHE_FILE = 'route_cache.json'

fake_fire_coords = [
    (33.721286, -117.7709814)  # Fake fire coordinate for testing
]

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.debug(f"Geocode response for '{address}': {response.text}")
    except requests.RequestException as e:
        logging.error(f"Network error while geocoding address '{address}': {e}")
        return None

    if response.status_code != 200:
        logging.error(f"Failed to geocode address '{address}'. Status Code: {response.status_code}")
        return None

    data = response.json()
    if len(data) > 0:
        coords = data[0]
        return [float(coords['lat']), float(coords['lon'])]
    else:
        logging.error(f"No results found for address '{address}'.")
        return None

def get_current_incidents():
    API_URL = "https://incidents.fire.ca.gov/umbraco/api/IncidentApi/List?inactive=false"
    logging.info("Fetching current incidents from CAL FIRE API.")
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        logging.debug(f"Incidents response: {response.text}")
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
            logging.debug(f"Distance from {coord} to fire at {fire_coord}: {distance} miles")
            if distance <= max_distance_miles:
                return True
        except ValueError as e:
            logging.error(f"Error calculating distance: {e}")
            continue
    return False

def get_routes(start_coords, end_coords, num_alternatives=10, deviation_factor=2):
    try:
        GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/directions/json'
        GOOGLE_MAPS_API_KEY = 'AIzaSyCmKuPaMS9lHzKSd2r1nVFlvoJ6Fd8YFTQ'  # Replace with your Google Maps API key
        params = {
            'origin': f"{start_coords[0]},{start_coords[1]}",
            'destination': f"{end_coords[0]},{end_coords[1]}",
            'key': GOOGLE_MAPS_API_KEY,
            'avoid': 'tolls,highways',  # You can add more avoidance options here
            'alternatives': 'true'
        }
        response = requests.get(
            GOOGLE_MAPS_API_URL,
            params=params,
            timeout=15
        )
        response.raise_for_status()
        logging.debug(f"Route API response: {response.text}")
        routes_data = response.json()

        # Implementing the Stack Overflow workaround idea
        routes = routes_data.get('routes', [])
        valid_routes = []
        for route in routes:
            route_coordinates = [
                (step['end_location']['lat'], step['end_location']['lng'])
                for leg in route.get('legs', [])
                for step in leg.get('steps', [])
            ]
            route_passes_near_fire = any(
                is_near_fire((coord[0], coord[1]), get_fire_coordinates(get_current_incidents()))
                for coord in route_coordinates
            )
            if not route_passes_near_fire:
                valid_routes.append(route)
            else:
                # Add alternate points to avoid the fire and re-run directions
                for fire_coord in fake_fire_coords:
                    params['waypoints'] = f"{fire_coord[0]},{fire_coord[1]}"
                    response = requests.get(GOOGLE_MAPS_API_URL, params=params, timeout=15)
                    response.raise_for_status()
                    logging.debug(f"Re-routing API response: {response.text}")
                    rerouted_data = response.json()
                    rerouted_routes = rerouted_data.get('routes', [])
                    for rerouted_route in rerouted_routes:
                        rerouted_coordinates = [
                            (step['end_location']['lat'], step['end_location']['lng'])
                            for leg in rerouted_route.get('legs', [])
                            for step in leg.get('steps', [])
                        ]
                        if not any(is_near_fire((coord[0], coord[1]), get_fire_coordinates(get_current_incidents())) for coord in rerouted_coordinates):
                            valid_routes.append(rerouted_route)
                            break

        return {'routes': valid_routes}
    except requests.RequestException as e:
        logging.error(f"Network error while getting directions: {e}")
        return None

@app.route('/calculate_route', methods=['POST'])
def calculate_route():
    data = request.get_json()
    start_address = data.get('start_address')
    end_address = data.get('end_address')
    num_alternatives = data.get('num_alternatives', 10)  # Allow customization via the request
    deviation_factor = data.get('deviation_factor', 2)  # Allow customization via the request

    start_coords = geocode_address(start_address)
    end_coords = geocode_address(end_address)

    if not start_coords or not end_coords:
        logging.error("Unable to geocode one or both addresses.")
        return jsonify({'error': 'Unable to geocode one or both addresses.'}), 400

    incidents = get_current_incidents()
    fires = get_fire_coordinates(incidents)

    if is_near_fire(end_coords, fires, max_distance_miles=1):
        logging.warning("The destination is within 10 miles of an active fire.")
        return jsonify({'warning': 'The destination is within 10 miles of an active fire. Proceed with caution or consider an alternative destination.'}), 200

    directions = get_routes(start_coords, end_coords, num_alternatives=num_alternatives, deviation_factor=deviation_factor)
    if not directions:
        logging.error("Unable to get route directions.")
        return jsonify({'error': 'Unable to get route directions.'}), 500

    valid_routes = directions.get('routes', [])
    invalid_routes = []

    for route in directions.get('routes', []):
        route_coordinates = [
            (step['end_location']['lat'], step['end_location']['lng'])
            for leg in route.get('legs', [])
            for step in leg.get('steps', [])
        ]
        route_passes_near_fire = any(
            is_near_fire((coord[0], coord[1]), fires)
            for coord in route_coordinates
        )

        if route_passes_near_fire:
            logging.warning("Route passes near an active fire.")
            invalid_routes.append(route)
        else:
            logging.info("Safe route found.")

    # Save all routes to cache
    with open(CACHE_FILE, 'w') as cache_file:
        json.dump({
            "valid_routes": valid_routes,
            "invalid_routes": invalid_routes
        }, cache_file, indent=2)

    if valid_routes:
        # Convert the valid route to a GeoJSON-like structure for use in Leaflet
        features = []
        for leg in valid_routes[0].get('legs', []):
            coordinates = []
            for step in leg.get('steps', []):
                coordinates.append([step['start_location']['lat'], step['start_location']['lng']])
                coordinates.append([step['end_location']['lat'], step['end_location']['lng']])

            # Add as a feature to the list
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                }
            })

        # Format the response in a way that can be interpreted by your map
        return jsonify({
            "type": "FeatureCollection",
            "features": features,
            "invalid_routes": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [step['end_location']['lat'], step['end_location']['lng']]
                            for leg in route.get('legs', [])
                            for step in leg.get('steps', [])
                        ]
                    }
                }
                for route in invalid_routes
            ],
            "fires": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [fire[1], fire[0]]  # Longitude, Latitude
                    }
                }
                for fire in fires
            ]
        }), 200
    else:
        logging.error("Unable to find a safe route.")
        return jsonify({'error': 'Unable to find a safe route.'}), 500

@app.route('/route_data', methods=['GET'])
def route_data():
    # Return cached route data if available
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as cache_file:
            return jsonify(json.load(cache_file))
    else:
        return jsonify({'error': 'No cached route data available.'}), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/map')
def map_view():
    return render_template('map.html')

if __name__ == '__main__':
    app.run(debug=True)
