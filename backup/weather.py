import requests
import logging
from config import *
import json

LIGHTNING_KEYWORDS = ["TS", "LTG", "VCTS"]

def get_valid_airports(file_path):
    """Read airport IDs from a file and return a list of valid airport codes."""
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines() if line.strip() != "SKIP"]
    except Exception as e:
        logging.error("Failed to read the airport file: %s", e)
        return []

def get_airports_with_skip(file_path):
    """Read airport IDs from a file and return a list including 'SKIP' entries."""
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        logging.error("Failed to read the airport file: %s", e)
        return []

def fetch_metar():
    airport_ids = get_valid_airports(AIRPORTS_FILE)
    if not airport_ids:
        logging.warning("No valid airport IDs found.")
        return None
    
    base_url = "https://aviationweather.gov/api/data/metar"
    params = {
        'ids': ','.join(airport_ids),  # Comma-separated list of airport IDs
        'format': 'geojson'  # Request GeoJSON format
    }

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

# Add this function to weather.py

def read_weather_data():
    """Read and return the weather data from weather.json."""
    try:
        with open('weather.json', 'r') as json_file:
            return json.load(json_file)
    except Exception as e:
        print(f"Failed to read weather.json: {e}")
        return {}

def get_windy_airports(weather_data):
    """Detect and return a dictionary of windy airports with their corresponding colors."""
    windy_airports = {}
    for airport_code, weather_info in weather_data.items():
        wind_speed = weather_info.get('wind_speed', 0)
        wind_gust = weather_info.get('wind_gust', 0)
        flt_cat = weather_info.get('flt_cat', 'MISSING')

        # Check if wind speed or wind gust exceeds the threshold
        if wind_speed > WIND_THRESHOLD or wind_gust > WIND_THRESHOLD:
            # Get the color based on flight category
            flt_cat_color = get_flt_cat_color(flt_cat)
            
            # Add airport and color to windy_airports dictionary
            windy_airports[airport_code] = flt_cat_color

    return windy_airports

def get_lightning_airports(weather_data):
    """Detect and return a dictionary of airports with lightning and their corresponding colors."""
    lightning_airports = {}
    for airport_code, weather_info in weather_data.items():
        # Use raw_observation as the standard key name
        raw_observation = weather_info.get('raw_observation', '')
        flt_cat = weather_info.get('flt_cat', 'MISSING')

        # Check for lightning using the imported keywords
        if any(keyword in raw_observation for keyword in LIGHTNING_KEYWORDS):
            # Get the color based on flight category
            flt_cat_color = get_flt_cat_color(flt_cat)
            
            # Add airport and color to lightning_airports dictionary
            lightning_airports[airport_code] = flt_cat_color

    return lightning_airports

SNOW_KEYWORDS = ["SN", "BLSN", "DRSN"]  # Add this line near the top with the other keyword definitions

def get_snowy_airports(weather_data):
    """Detect and return a dictionary of airports with snow and their corresponding colors."""
    snowy_airports = {}
    for airport_code, weather_info in weather_data.items():
        # Use raw_observation as the standard key name
        raw_observation = weather_info.get('raw_observation', '')
        flt_cat = weather_info.get('flt_cat', 'MISSING')

        # Check for snow using the imported keywords
        if any(keyword in raw_observation for keyword in SNOW_KEYWORDS):
            # Get the color based on flight category
            flt_cat_color = get_flt_cat_color(flt_cat)
            
            # Add airport and color to snowy_airports dictionary
            snowy_airports[airport_code] = flt_cat_color

    return snowy_airports


def get_flt_cat_color(flt_cat):
    """Return the color corresponding to the flight category."""
    if flt_cat == 'VFR':
        return VFR_COLOR
    elif flt_cat == 'MVFR':
        return MVFR_COLOR
    elif flt_cat == 'IFR':
        return IFR_COLOR
    elif flt_cat == 'LIFR':
        return LIFR_COLOR
    else:
        return MISSING_COLOR

def get_airport_weather(airport_code, weather_data):
    """Retrieve and format weather data for a given airport."""
    airport_weather = weather_data.get(airport_code, {})
    flt_cat = airport_weather.get('flt_cat', 'MISSING')
    wind_speed = airport_weather.get('wind_speed', 0)  # Default to 0 if missing
    wind_gust = airport_weather.get('wind_gust', 0)    # Default to 0 if missing
    
    # Use raw_observation as the standard key name
    raw_observation = airport_weather.get('raw_observation', '')
    # Check for lightning using the defined keywords
    lightning = any(keyword in raw_observation for keyword in LIGHTNING_KEYWORDS)

    return flt_cat, wind_speed, wind_gust, lightning

def parse_weather(metar_data):
    if not metar_data or 'features' not in metar_data:
        logging.error("Invalid METAR data received for parsing.")
        return {}

    parsed_data = {}
    for feature in metar_data['features']:
        airport_id = feature['properties'].get('id', 'UNKNOWN')
        raw_observation = feature['properties'].get('rawOb', 'N/A')

        # Check for lightning indicators in raw observation
        lightning = any(keyword in raw_observation for keyword in LIGHTNING_KEYWORDS)

        airport_weather = {
            "observation_time": feature['properties'].get('obsTime', None),
            "temperature": feature['properties'].get('temp', 0),
            "dew_point": feature['properties'].get('dewp', 0),
            "wind_direction": feature['properties'].get('wdir', 0),
            "wind_speed": feature['properties'].get('wspd', 0),
            "wind_gust": feature['properties'].get('wgst', 0),
            "flt_cat": feature['properties'].get('fltcat', 'MISSING'),
            "visibility": feature['properties'].get('visib', 0),
            "altimeter": feature['properties'].get('altim', 0),
            "cloud_coverage": [],  # Process cloud layers later
            "ceiling": feature['properties'].get('ceil', 0),
            "precip": feature['properties'].get('wx', 'MISSING'),
            "raw_observation": raw_observation,
            "lightning": lightning  # Add the lightning indicator
        }
        # Append parsed data for the airport
        parsed_data[airport_id] = airport_weather

    return parsed_data

def main():
    # Fetch METAR data
    metar_data = fetch_metar()
    if metar_data:
        # Parse the fetched data
        parsed_data = parse_weather(metar_data)
        if parsed_data:
            # Save parsed data to weather.json
            with open('weather.json', 'w') as json_file:
                json.dump(parsed_data, json_file, indent=4)
            logging.info("Parsed weather data saved to weather.json")
        else:
            logging.error("Parsed data is empty.")
    else:
        logging.error("Failed to fetch METAR data.")

if __name__ == "__main__":
    main()
