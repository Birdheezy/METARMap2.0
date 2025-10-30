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
        logging.error("No valid airport IDs found in airport file")
        return None

    base_url = "https://aviationweather.gov/api/data/metar"
    params = {
        'ids': ','.join(airport_ids),
        'format': 'geojson'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    logging.info(f"Sending request with User-Agent: {headers['User-Agent']}")

    try:
        # Construct the full URL for debugging
        full_url = f"{base_url}?ids={','.join(airport_ids)}&format=geojson"
        logging.info(f"Making API request to {base_url} with {len(airport_ids)} airports")
        logging.info(f"Full URL: {full_url}")
        logging.info(f"Request parameters: {params}")
        
        start_time = datetime.datetime.now()
        # Pass the 'headers' dictionary to the request
        response = requests.get(base_url, params=params, headers=headers)
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
        
        logging.info(f"API response received in {elapsed_time:.2f} seconds. Status code: {response.status_code}")
        
        # Log response headers to check for rate limiting
        important_headers = ['content-type', 'content-length', 'date', 'x-rate-limit', 'retry-after']
        header_info = {k: v for k, v in response.headers.items() if k.lower() in important_headers}
        logging.info(f"Response headers: {header_info}")
        
        # Handle new API response codes
        if response.status_code == 204:
            logging.warning("API returned 204 No Content - no data available for requested airports")
            return None
        
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
            data = json.load(json_file)
            return data
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
        
        # Ensure wind values are not None before comparison
        wind_speed = wind_speed if wind_speed is not None else 0
        wind_gust = wind_gust if wind_gust is not None else 0

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


def determine_flight_category(raw_metar):
    """
    Determine flight category from raw METAR string when API doesn't provide it.
    
    Args:
        raw_metar: Raw METAR string (e.g., "METAR KMHR 162035Z AUTO 30005KT 10SM 34/09 A2991 RMK AO2")
        
    Returns:
        str: Flight category ('VFR', 'MVFR', 'IFR', 'LIFR', or 'MISSING')
    """
    if not raw_metar or not isinstance(raw_metar, str):
        return 'MISSING'
    
    try:
        # Parse visibility and ceiling from METAR
        visibility = _parse_visibility(raw_metar)
        ceiling = _parse_ceiling(raw_metar)
        
        # If visibility is missing, cannot determine flight category
        if visibility is None:
            return 'MISSING'
        
        # Determine flight category based on visibility and ceiling
        if visibility >= 5.0:
            # VFR: Visibility ≥ 5 SM AND (Ceiling ≥ 3,000 ft OR no ceiling reported)
            if ceiling is None or ceiling >= 3000:
                return 'VFR'
            else:
                return 'MVFR'  # Good visibility but low ceiling
        elif visibility >= 3.0:
            # MVFR: Visibility 3-5 SM AND (Ceiling ≥ 1,000 ft OR no ceiling reported)
            if ceiling is None or ceiling >= 1000:
                return 'MVFR'
            else:
                return 'IFR'  # Marginal visibility with low ceiling
        elif visibility >= 1.0:
            # IFR: Visibility 1-3 SM AND (Ceiling ≥ 500 ft OR no ceiling reported)
            if ceiling is None or ceiling >= 500:
                return 'IFR'
            else:
                return 'LIFR'  # Poor visibility with very low ceiling
        else:
            # LIFR: Visibility < 1 SM
            return 'LIFR'
            
    except Exception as e:
        logging.error(f"Error determining flight category from METAR '{raw_metar}': {e}")
        return 'MISSING'


def _parse_visibility(raw_metar):
    """
    Parse visibility from METAR string.
    
    Args:
        raw_metar: Raw METAR string
        
    Returns:
        float: Visibility in statute miles, or None if not found
    """
    try:
        # Visibility pattern: Must end with SM (statute miles)
        visibility_pattern = re.compile(r'(\d{1,2}|\d/\d|M\d/\d)SM')
        
        parts = raw_metar.split()
        for part in parts:
            vis_match = visibility_pattern.match(part)
            if vis_match:
                vis_str = vis_match.group(1)  # Get the visibility value
                
                # Handle different visibility formats
                if vis_str.startswith('M'):
                    # Less than format (e.g., M1/4)
                    vis_str = vis_str[1:]  # Remove M
                
                if '/' in vis_str:
                    # Fractional visibility (e.g., 1/4)
                    numerator, denominator = vis_str.split('/')
                    return float(numerator) / float(denominator)
                else:
                    # Integer visibility
                    return float(vis_str)
        
        return None
        
    except Exception as e:
        logging.error(f"Error parsing visibility from METAR: {e}")
        return None


def _parse_ceiling(raw_metar):
    """
    Parse ceiling from METAR string.
    
    Args:
        raw_metar: Raw METAR string
        
    Returns:
        int: Ceiling height in feet AGL, or None if no ceiling
    """
    try:
        # Cloud pattern: FEW/SCT/BKN/OVC/VV followed by altitude
        cloud_pattern = re.compile(r'(FEW|SCT|BKN|OVC|VV)(\d{3})?(CB|TCU)?')
        
        parts = raw_metar.split()
        ceiling_layers = []
        
        for part in parts:
            cloud_match = cloud_pattern.match(part)
            if cloud_match:
                type_str, altitude_str, cloud_type = cloud_match.groups()
                
                # Only BKN and OVC layers count as ceilings
                if type_str in ['BKN', 'OVC'] and altitude_str:
                    altitude = int(altitude_str) * 100  # Convert to feet
                    ceiling_layers.append(altitude)
        
        # Return the lowest ceiling (most restrictive)
        return min(ceiling_layers) if ceiling_layers else None
        
    except Exception as e:
        logging.error(f"Error parsing ceiling from METAR: {e}")
        return None


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
    
    # Handle null flight category - determine from raw METAR if needed
    flt_cat = airport_weather.get('flt_cat')
    if flt_cat is None:
        raw_observation = airport_weather.get('raw_observation', '')
        flt_cat = determine_flight_category(raw_observation)
    elif flt_cat == 'MISSING':
        flt_cat = 'MISSING'  # Keep as is
    else:
        flt_cat = flt_cat  # Use the provided value
    
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
        # API changed: id property removed from GeoJSON, use icaoId instead
        airport_id = feature['properties'].get('icaoId', feature['properties'].get('id', 'UNKNOWN'))
        raw_observation = feature['properties'].get('rawOb', 'N/A')

        # Get coordinates from geometry
        coords = feature.get('geometry', {}).get('coordinates', [])
        lat = coords[1] if len(coords) >= 2 else None
        lon = coords[0] if len(coords) >= 2 else None

        # Check for lightning indicators in raw observation
        lightning = any(keyword in raw_observation for keyword in LIGHTNING_KEYWORDS)

        # Handle None values from API - convert to 0 for numeric fields
        def safe_get_numeric(properties, key, default=0):
            value = properties.get(key, default)
            return value if value is not None else default
        
        # Handle visibility field that can be string (like "10+") or number
        def safe_get_visibility(properties, key, default=0):
            value = properties.get(key, default)
            if value is None:
                return default
            if isinstance(value, str):
                # Handle string values like "10+" - extract the number part
                import re
                match = re.search(r'\d+', str(value))
                return int(match.group()) if match else default
            return value if isinstance(value, (int, float)) else default
        
        # Handle precip field that can be null
        def safe_get_precip(properties, key, default='MISSING'):
            value = properties.get(key, default)
            return value if value is not None else default
        
        # Handle flight category - use API value if available, otherwise determine from raw METAR
        api_flt_cat = feature['properties'].get('fltcat')
        if api_flt_cat is not None:
            flt_cat = api_flt_cat
        else:
            # API didn't provide flight category, determine it from raw METAR
            flt_cat = determine_flight_category(raw_observation)
        
        airport_weather = {
            "observation_time": feature['properties'].get('obsTime', None),
            "temperature": safe_get_numeric(feature['properties'], 'temp', 0),
            "dew_point": safe_get_numeric(feature['properties'], 'dewp', 0),
            "wind_direction": safe_get_numeric(feature['properties'], 'wdir', 0),
            "wind_speed": safe_get_numeric(feature['properties'], 'wspd', 0),
            "wind_gust": safe_get_numeric(feature['properties'], 'wgst', 0),
            "flt_cat": flt_cat,
            "visibility": safe_get_visibility(feature['properties'], 'visib', 0),
            "altimeter": safe_get_numeric(feature['properties'], 'altim', 0),
            "cloud_coverage": feature['properties'].get('clouds', []),  # Use the clouds array from API
            "cover": feature['properties'].get('cover', 'MISSING'),  # Overall cloud cover
            "ceiling": safe_get_numeric(feature['properties'], 'ceil', 0),
            "precip": safe_get_precip(feature['properties'], 'wx', 'MISSING'),
            "raw_observation": raw_observation,
            "lightning": lightning,  # Add the lightning indicator
            "latitude": lat,  # Add latitude
            "longitude": lon,  # Add longitude
            "site": feature['properties'].get('site', airport_id)  # Add site name
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



