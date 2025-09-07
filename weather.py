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

def parse_visibility(visibility_str):
    """Parse visibility string from API (e.g., '10+', '1.5', etc.) to numeric value."""
    if not visibility_str:
        return 0
    
    # Handle string format
    if isinstance(visibility_str, str):
        # Remove '+' and convert to float
        visibility_clean = visibility_str.replace('+', '')
        try:
            return float(visibility_clean)
        except ValueError:
            logging.warning(f"Could not parse visibility: {visibility_str}")
            return 0
    
    # Handle numeric format (in case API sometimes returns numbers)
    if isinstance(visibility_str, (int, float)):
        return float(visibility_str)
    
    return 0

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
        logging.error("No valid airport IDs found in airport file")
        return None

    base_url = "https://aviationweather.gov/api/data/metar"
    params = {
        'ids': ','.join(airport_ids),
        'format': 'geojson'
    }

    try:
        logging.info(f"Making API request to {base_url} with {len(airport_ids)} airports")
        logging.info(f"Request parameters: {params}")
        
        start_time = datetime.datetime.now()
        response = requests.get(base_url, params=params)
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
        
        logging.info(f"API response received in {elapsed_time:.2f} seconds. Status code: {response.status_code}")
        
        # Log response headers to check for rate limiting
        important_headers = ['content-type', 'content-length', 'date', 'x-rate-limit', 'retry-after']
        header_info = {k: v for k, v in response.headers.items() if k.lower() in important_headers}
        logging.info(f"Response headers: {header_info}")
        
        response.raise_for_status()
        
        # Check if we got valid JSON
        data = response.json()
        if 'features' in data:
            airport_count = len(data['features'])
            logging.info(f"Successfully retrieved data for {airport_count} airports")
            if airport_count == 0:
                logging.warning("API returned 0 airports - response may be empty despite 200 status")
        else:
            logging.warning(f"Response is missing 'features' key. Raw response preview: {str(response.text)[:200]}...")
            
        return data
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch METAR data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Error response status: {e.response.status_code}")
            logging.error(f"Error response body: {e.response.text[:500]}")
        return None
    except ValueError as e:
        logging.error(f"Failed to parse JSON response: {e}")
        logging.error(f"Raw response preview: {response.text[:500]}")
        return None

def read_weather_data():
    """Read and return the weather data from weather.json."""
    try:
        # Use absolute path to ensure consistency
        with open('/home/pi/weather.json', 'r') as json_file:
            return json.load(json_file)
    except Exception as e:
        logging.error(f"Failed to read weather.json: {e}")
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
    flt_cat = airport_weather.get('flt_cat', 'MISSING') or 'MISSING'
    wind_speed = airport_weather.get('wind_speed', 0) or 0  # Default to 0 if missing or None
    wind_gust = airport_weather.get('wind_gust', 0) or 0    # Default to 0 if missing or None

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

        # Get coordinates from geometry
        coords = feature.get('geometry', {}).get('coordinates', [])
        lat = coords[1] if len(coords) >= 2 else None
        lon = coords[0] if len(coords) >= 2 else None

        # Check for lightning indicators in raw observation
        lightning = any(keyword in raw_observation for keyword in LIGHTNING_KEYWORDS)

        airport_weather = {
            "observation_time": feature['properties'].get('obsTime', None),
            "temperature": feature['properties'].get('temp', 0) or 0,
            "dew_point": feature['properties'].get('dewp', 0) or 0,
            "wind_direction": feature['properties'].get('wdir', 0) or 0,
            "wind_speed": feature['properties'].get('wspd', 0) or 0,
            "wind_gust": feature['properties'].get('wgst', 0) or 0,
            "flt_cat": feature['properties'].get('fltcat', 'MISSING') or 'MISSING',
            "visibility": parse_visibility(feature['properties'].get('visib', '0')),
            "altimeter": feature['properties'].get('altim', 0) or 0,
            "cloud_coverage": feature['properties'].get('clouds', []),
            "ceiling": feature['properties'].get('ceil', 0) or 0,
            "precip": feature['properties'].get('wx', 'MISSING') or 'MISSING',
            "raw_observation": raw_observation,
            "lightning": lightning,  # Add the lightning indicator
            "latitude": lat,  # Add latitude
            "longitude": lon,  # Add longitude
            "site": feature['properties'].get('site', airport_id) or airport_id  # Add site name
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
        logging.error("Failed to fetch METAR data")
        return

    parsed_data = parse_weather(metar_data)
    if not parsed_data:
        logging.error("Failed to parse METAR data")
        return

    # Always save the data to update the file timestamp
    try:
        with open('/home/pi/weather.json', 'w') as json_file:
            json.dump(parsed_data, json_file, indent=4)
            logging.info("Weather data saved to /home/pi/weather.json with updated timestamp")
    except Exception as e:
        logging.error(f"Failed to write weather data to file: {e}")

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

def backup_airports_file():
    """Create a backup of the airports file."""
    try:
        with open(AIRPORTS_FILE, 'r') as source:
            with open(f"{AIRPORTS_FILE}.backup", 'w') as backup:
                backup.write(source.read())
        return True
    except Exception as e:
        logging.error(f"Failed to create backup of airports file: {e}")
        return False

def restore_airports_file():
    """Restore the airports file from backup."""
    try:
        backup_file = f"{AIRPORTS_FILE}.backup"
        if not os.path.exists(backup_file):
            logging.error("No backup file found to restore from")
            return False

        with open(backup_file, 'r') as backup:
            with open(AIRPORTS_FILE, 'w') as target:
                target.write(backup.read())
        return True
    except Exception as e:
        logging.error(f"Failed to restore airports file from backup: {e}")
        return False

def update_airports_file(airport_codes):
    """Update the airports file with new airport codes, maintaining original positions."""
    try:
        # First create a backup if it doesn't exist
        backup_file = f"{AIRPORTS_FILE}.backup"
        if not os.path.exists(backup_file):
            if not backup_airports_file():
                return False

        # Read the original structure with all lines to preserve exact format
        with open(backup_file, 'r') as backup:
            original_content = backup.read()
            original_lines = original_content.splitlines()

        # Convert airport codes to uppercase for consistency
        airport_codes = [code.upper() for code in airport_codes]

        # Create new list with all SKIPs, maintaining exact length
        updated_lines = ["SKIP"] * len(original_lines)

        # For each requested airport, if it existed in the original file,
        # put it in its original position
        for airport in airport_codes:
            try:
                original_pos = original_lines.index(airport)
                updated_lines[original_pos] = airport
            except ValueError:
                # Airport wasn't in original file, log warning
                logging.warning(f"Airport {airport} not found in original configuration")
                continue

        # Write the updated content, preserving original line endings
        with open(AIRPORTS_FILE, 'w', newline='') as file:
            for i, line in enumerate(updated_lines):
                file.write(line)
                # Add newline if not the last line
                if i < len(updated_lines) - 1:
                    file.write('\n')

        return True
    except Exception as e:
        logging.error(f"Failed to update airports file: {e}")
        return False

if __name__ == "__main__":
    main()
