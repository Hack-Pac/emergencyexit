import osmnx as ox
import networkx as nx
import json
import time
import logging
import os
from geopy.distance import geodesic
import requests
import matplotlib.pyplot as plt
from xml.etree import ElementTree as ET

# Set up logging to output to a file and to the console
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("emergency_exit.log"),
    logging.StreamHandler()
])

FIRE_PROXIMITY_THRESHOLD_MILES = 0.1
CACHE_FILE_PATH = 'socal.graphml'

# Custom function to load the graph from a GraphML file with specific key parsing
def load_custom_graph(graphml_path):
    logging.info("Loading custom road network from GraphML file...")
    try:
        tree = ET.parse(graphml_path)
        root = tree.getroot()

        # Define the GraphML namespaces
        ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}

        # Create an empty directed graph
        G = nx.DiGraph()

        # Extract nodes and their coordinates
        for node in root.findall('graphml:graph/graphml:node', ns):
            node_id = node.attrib['id']
            lat = lon = None
            for data in node.findall('graphml:data', ns):
                if data.attrib['key'] == 'd3':  # y-coordinate (latitude)
                    lat = float(data.text)
                elif data.attrib['key'] == 'd4':  # x-coordinate (longitude)
                    lon = float(data.text)
            if lat is not None and lon is not None:
                G.add_node(node_id, y=lat, x=lon)
            else:
                logging.warning(f"Node {node_id} is missing coordinates.")

        # Extract edges
        for edge in root.findall('graphml:graph/graphml:edge', ns):
            source = edge.attrib['source']
            target = edge.attrib['target']
            # Add the edge between source and target
            if source in G and target in G:
                G.add_edge(source, target)
            else:
                logging.warning(f"Edge between {source} and {target} references missing nodes.")

        logging.info(f"Custom road network loaded successfully with {len(G.nodes)} nodes and {len(G.edges)} edges.")
        return G

    except Exception as e:
        logging.error(f"Failed to load road network from GraphML: {e}")
        exit(1)


# Load the graph using the custom function
G = load_custom_graph(CACHE_FILE_PATH)

# Convert the graph to an undirected graph if needed
if G.is_directed():
    G = G.to_undirected()

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
        logging.error(f"Network error: {e}")
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
            logging.error(f"Error calculating distance for coord {coord} and fire_coord {fire_coord}")
            continue
    return False

def reroute_around_fire(G, fire_coords, max_distance_miles=FIRE_PROXIMITY_THRESHOLD_MILES):
    # Mark edges near fires with high cost to avoid them
    for u, v, data in G.edges(data=True):
        try:
            midpoint = ((G.nodes[u]['y'] + G.nodes[v]['y']) / 2,
                        (G.nodes[u]['x'] + G.nodes[v]['x']) / 2)
            if is_near_fire(midpoint, fire_coords, max_distance_miles):
                data['weight'] = data.get('length', 1) * 5  # Increase cost to avoid fire zones
            else:
                data['weight'] = data.get('length', 1)
        except Exception as e:
            logging.error(f"Error processing edge data for edge ({u}, {v}): {e}")
            continue

def find_safe_route(start_coords, end_coords, fire_coords):
    # Find the nearest nodes to the start and end coordinates
    try:
        start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
        end_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])
        logging.debug(f"Start node: {start_node}, End node: {end_node}")
        logging.debug(f"Start node coordinates: (lat: {G.nodes[start_node]['y']}, lon: {G.nodes[start_node]['x']})")
        logging.debug(f"End node coordinates: (lat: {G.nodes[end_node]['y']}, lon: {G.nodes[end_node]['x']})")
    except Exception as e:
        logging.error(f"Error finding nearest nodes: {e}")
        return None

    # Reroute around fire
    reroute_around_fire(G, fire_coords)

    # Find the shortest path avoiding fires
    try:
        route = nx.astar_path(G, start_node, end_node, weight='weight')
        logging.debug(f"Route length: {len(route)} nodes.")
        return route
    except nx.NetworkXNoPath:
        logging.error("No path found between start and end nodes using A* algorithm.")
        return None

def print_route(route):
    if not route:
        logging.error("No valid route to print.")
        return

    logging.info("Printing route directions:")
    logging.debug(f"Total route steps: {len(route)}")
    for idx, node in enumerate(route):
        point = G.nodes[node]
        lat, lon = point.get('y'), point.get('x')
        logging.info(f"Step {idx + 1}: Coordinates: ({lat}, {lon})")

    # Plotting the route on the map
    if len(G.edges) > 0:
        fig, ax = ox.plot_graph_route(G, route, route_linewidth=4, node_size=0, bgcolor='k')
        plt.show()
    else:
        logging.critical("Cannot plot route as the graph contains no edges.")

# Ask for user input for addresses if the graph is already loaded
while True:
    start_address = input('Enter the start address (or type "exit" to quit): ')
    if start_address.lower() == 'exit':
        break
    end_address = input('Enter the end address (or type "exit" to quit): ')
    if end_address.lower() == 'exit':
        break

    start_coords = geocode_address(start_address)
    end_coords = geocode_address(end_address)

    if not start_coords or not end_coords:
        logging.error('Unable to geocode one or both addresses.')
        continue

    incidents = get_current_incidents()
    fire_coords = get_fire_coordinates(incidents)

    if is_near_fire(end_coords, fire_coords, max_distance_miles=10):
        logging.warning("The destination is within 10 miles of an active fire.")
        logging.warning("Proceed with caution or consider an alternative destination.")

    route = find_safe_route(start_coords, end_coords, fire_coords)
    if route:
        print_route(route)
    else:
        logging.error("Unable to find a safe route.")
