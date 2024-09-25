import requests
import logging
from config import *

def get_valid_airports(file_path):
    """Read airport IDs from a file and return a list of valid airport codes."""
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines() if line.strip() != "SKIP"]
    except Exception as e:
        logging.error("Failed to read the airport file: %s", e)
        return []

def fetch_metar():
    """Fetch METAR data from the Aviation Weather API for all valid airports."""
    airport_ids = get_valid_airports(AIRPORTS_FILE)
    if not airport_ids:
        logging.warning("No valid airport IDs found.")
        return None
    
    # Construct the base URL and parameters
    base_url = "https://aviationweather.gov/api/data/metar"
    params = {
        'ids': ','.join(airport_ids),  # Comma-separated list of airport IDs
        'format': 'geojson'  # Request GeoJSON format
    }

    # Print the encoded URL using the requests library's prepared request
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        # Print the fully constructed URL that was requested
        print(f"Encoded URL: {response.url}")
        logging.info("Fetched METAR data for airports: %s", ','.join(airport_ids))
        return response.json()  # Return the response as JSON
    except requests.exceptions.RequestException as e:
        logging.error("Failed to fetch METAR data: %s", e)
        return None

# Call the fetch_metar() function to execute the code
fetch_metar()
