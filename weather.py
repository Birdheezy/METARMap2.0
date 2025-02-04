import requests
import logging
from config import *
import json
import re
import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Only include the message, let journald handle the timestamp
)

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
    """Fetch METAR data from aviation weather API."""
    airport_ids = get_valid_airports(AIRPORTS_FILE)
    if not airport_ids:
        return None
    
    base_url = "https://aviationweather.gov/api/data/metar"
    params = {
        'ids': ','.join(airport_ids),
        'format': 'geojson'
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch METAR data: {e}")
        return None

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

LIGHTNING_KEYWORDS = ["TS", "LTG", "VCTS"]

def get_lightning_airports(weather_data):
    """Detect and return a dictionary of airports with lightning and their corresponding colors."""
    lightning_airports = {}
    for airport_code, weather_info in weather_data.items():
        # Use raw_observation as the standard key name
        raw_observation = weather_info.get('raw_observation', '')
        flt_cat = weather_info.get('flt_cat', 'MISSING')

        # Check for lightning using regular expressions for whole word matching
        if any(re.search(rf'\b{keyword}\b', raw_observation) for keyword in LIGHTNING_KEYWORDS):
            # Get the color based on flight category
            flt_cat_color = get_flt_cat_color(flt_cat)
            
            # Add airport and color to lightning_airports dictionary
            lightning_airports[airport_code] = flt_cat_color

    return lightning_airports

SNOW_KEYWORDS = ["SN", "BLSN", "DRSN", "GS", "SG", "SNINCR", "SP"]

def get_snowy_airports(weather_data):
    """Detect and return a dictionary of airports with snow and their corresponding colors."""
    snowy_airports = {}
    for airport_code, weather_info in weather_data.items():
        # Use raw_observation as the standard key name
        raw_observation = weather_info.get('raw_observation', '')
        flt_cat = weather_info.get('flt_cat', 'MISSING')

        # Check for snow using regular expressions for whole word matching
        if any(re.search(rf'\b{keyword}\b', raw_observation) for keyword in SNOW_KEYWORDS):
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

def get_missing_airports(weather_data):
    """Return a list of airports with missing weather data."""
    missing_airports = []
    for airport_code, weather_info in weather_data.items():
        if weather_info.get('flt_cat', 'MISSING') == 'MISSING':
            missing_airports.append(airport_code)
    return missing_airports

def main():
    """Main function to fetch and process weather data."""
    metar_data = fetch_metar()
    if not metar_data:
        return
        
    parsed_data = parse_weather(metar_data)
    if not parsed_data:
        return
        
    # Check if data has changed
    try:
        with open('weather.json', 'r') as json_file:
            old_data = json.load(json_file)
            if old_data == parsed_data:
                return  # No change in weather data
    except:
        pass  # Continue if weather.json doesn't exist
        
    # Save new data
    with open('weather.json', 'w') as json_file:
        json.dump(parsed_data, json_file, indent=4)
    
    # Only log status table if called by scheduler (check parent process)
    ppid = os.getppid()
    try:
        with open(f'/proc/{ppid}/cmdline', 'r') as f:
            parent_cmd = f.read()
            if 'scheduler.py' in parent_cmd:
                # Log weather update with essential information
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logging.info(f"\nWeather Update at {current_time}")
                
                # Get all condition states
                airport_list = get_airports_with_skip(AIRPORTS_FILE)
                
                # Print status table
                logging.info("\nAirport Status:")
                logging.info(f"{'Airport':<10} {'Flight Cat':<12} {'Wind Speed':<12} {'Wind Gust':<12} {'Windy':<6} {'Lightning':<10} {'Snowy':<6}")
                logging.info("-" * 80)
                
                # Log status for each airport
                windy_airports = get_windy_airports(parsed_data)
                lightning_airports = get_lightning_airports(parsed_data)
                snowy_airports = get_snowy_airports(parsed_data)
                
                for airport_code in airport_list:
                    if airport_code != "SKIP":
                        flt_cat, wind_speed, wind_gust, lightning = get_airport_weather(airport_code, parsed_data)
                        is_windy = airport_code in windy_airports
                        is_snowy = airport_code in snowy_airports
                        logging.info(f"{airport_code:<10} {flt_cat:<12} {wind_speed:<2} kt {' '*8} {wind_gust:<2} kt {' '*8} {'Yes' if is_windy else 'No':<6} {'Yes' if lightning else 'No':<10} {'Yes' if is_snowy else 'No':<6}")
    except:
        # If we can't check parent process, assume it's not from scheduler
        pass

if __name__ == "__main__":
    main()
