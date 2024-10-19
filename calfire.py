import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API URL for CAL FIRE incidents
API_URL = "https://incidents.fire.ca.gov/umbraco/api/IncidentApi/List?inactive=false"

def get_current_incidents():
    logging.info("Fetching current incidents from CAL FIRE API.")
    try:
        # Send a GET request to fetch the incidents
        response = requests.get(API_URL)
        response.raise_for_status()
        incidents = response.json()
        logging.info(f"Fetched {len(incidents)} incidents.")
        return incidents
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while fetching the incidents: {e}")
        return []

def print_incidents(incidents):
    # Print each incident with all available information
    for incident in incidents:
        print(f"Incident: {incident['Name']}\n"
              f"Started: {incident['Started']}\n"
              f"Location: {incident['Location']}\n"
              f"County: {incident['County']}\n"
              f"Acres Burned: {incident['AcresBurned']}\n"
              f"Percent Contained: {incident['PercentContained']}%\n"
              f"Admin Unit: {incident['AdminUnit']}\n"
              f"Type: {incident['Type']}\n"
              f"URL: {incident['Url']}\n"
              f"Latitude: {incident['Latitude']}\n"
              f"Longitude: {incident['Longitude']}\n"
              f"Agency Names: {incident['AgencyNames']}\n"
              f"Updated: {incident['Updated']}\n"
              f"Is Active: {incident['IsActive']}\n")

def main():
    # Fetch current incidents from the API
    incidents = get_current_incidents()
    if incidents:
        print_incidents(incidents)
    else:
        print("No current incidents found.")

if __name__ == "__main__":
    main()