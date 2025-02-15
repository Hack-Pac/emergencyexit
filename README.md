## NOTE FOR SCRAPYARD REVIEWERS:
Our project is unable to be hosted live due to it requiring more compute than we have available to host 24/7. We have demos in the video, which is in the demo section of the form. Thank you! Please reach out with any questions.

# Emergency Exit

This project is a Python-based application that calculates safe routes to avoid areas with active fires. It uses OpenStreetMap data and the A* algorithm to dynamically reroute around active fire zones, making use of custom road networks stored in GraphML format.

## Features

- **Graph-Based Routing**: Uses OpenStreetMap road networks to calculate routes.
- **Fire Avoidance**: Dynamically adjusts route weights to avoid areas close to active fire coordinates.
- **Interactive Input**: Takes user inputs for start and end addresses and calculates the safest route.
- **Visualization**: Visualizes the computed routes using Matplotlib.

## Prerequisites

- Python 3.x
- Required Python packages:
  - `osmnx`
  - `networkx`
  - `requests`
  - `geopy`
  - `matplotlib`
  - `xml.etree.ElementTree`

You can install the required Python packages with the following command:

```sh
pip install osmnx networkx requests geopy matplotlib
```

## Setup Instructions

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/emergency-exit.git
   cd emergency-exit
   ```

2. Download the OpenStreetMap data for the relevant area:
   - Use `osmnx` to download and save the GraphML file for Southern California or any other region.
   - Example:
     ```python
     import osmnx as ox
     G = ox.graph_from_place("Southern California, USA", network_type="drive")
     ox.save_graphml(G, "socal.graphml")
     ```

3. Place the `socal.graphml` file in the project directory.

4. Run the Python script:
   ```sh
   python emergency_exit.py
   ```

## Usage

- **Input**: Enter the start and end addresses when prompted.
- **Output**: The script will print the route steps and visualize the route on a map.

## Logging

- Logs are written to both the console and a log file (`emergency_exit.log`). This provides detailed information about route calculations and any errors encountered.

## Important Notes

- **GraphML File**: The road network (`.graphml` file) is not included in the repository due to its size.
  - You must generate or download the file separately as described in the setup instructions.
- **API Limitations**: The script uses OpenStreetMap's Nominatim geocoding API, which has rate limits. Consider using your own instance if frequent requests are required.

## Contributing

Feel free to contribute to this project by submitting a pull request or opening an issue.

## License

This project is licensed under the MIT License.
