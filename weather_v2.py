import requests
import logging
import config  # Import config as module for defaults
from config_manager import manager # Import manager for dynamic config
import json
import re
import datetime
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)

# Helper to get config value with fallback
def get_config_value(key, default=None):
    # Try dynamic config first
    val = manager.get(key)
    if val is not None:
        return val
    # Fallback to static config module
    return getattr(config, key, default)

# Cache for airport lists
_airport_cache = {
    'valid': {'mtime': 0, 'data': []},
    'skip': {'mtime': 0, 'data': []}
}

def _get_file_mtime(file_path):
    try:
        return os.path.getmtime(file_path)
    except OSError:
        return 0

def get_valid_airports(file_path):
    """Read airport IDs from a file and return a list of valid airport codes.
    Cached based on file modification time.
    """
    global _airport_cache
    current_mtime = _get_file_mtime(file_path)
    
    if current_mtime > _airport_cache['valid']['mtime']:
        try:
            with open(file_path, 'r') as file:
                data = [line.strip() for line in file.readlines() if line.strip() != "SKIP"]
                _airport_cache['valid'] = {'mtime': current_mtime, 'data': data}
                logger.debug(f"Reloaded valid airports from {file_path}")
        except Exception as e:
            logger.error("Failed to read the airport file: %s", e)
            return []
            
    return _airport_cache['valid']['data']

def get_airports_with_skip(file_path):
    """Read airport IDs from a file and return a list including 'SKIP' entries.
    Cached based on file modification time.
    """
    global _airport_cache
    current_mtime = _get_file_mtime(file_path)
    
    if current_mtime > _airport_cache['skip']['mtime']:
        try:
            with open(file_path, 'r') as file:
                data = [line.strip() for line in file.readlines()]
                _airport_cache['skip'] = {'mtime': current_mtime, 'data': data}
                logger.debug(f"Reloaded airports with skip from {file_path}")
        except Exception as e:
            logger.error("Failed to read the airport file: %s", e)
            return []
            
    return _airport_cache['skip']['data']

def fetch_metar():
    """Fetch METAR data from aviation weather API."""
    airports_file = get_config_value('AIRPORTS_FILE', 'airports.txt')
    airport_ids = get_valid_airports(airports_file)
    if not airport_ids:
        logger.error("No valid airport IDs found in airport file")
        return None

    base_url = "https://aviationweather.gov/api/data/metar"
    params = {
        'ids': ','.join(airport_ids),
        'format': 'geojson'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        start_time = time.time()
        response = requests.get(base_url, params=params, headers=headers, timeout=10) # Added timeout
        elapsed_time = time.time() - start_time
        
        logger.info(f"API response received in {elapsed_time:.2f} seconds. Status code: {response.status_code}")
        
        if response.status_code == 204:
            logger.warning("API returned 204 No Content")
            return None
        
        response.raise_for_status()
        
        data = response.json()
        if 'features' in data:
            airport_count = len(data['features'])
            logger.info(f"Successfully retrieved data for {airport_count} airports")
        else:
            logger.warning(f"Response is missing 'features' key.")
            
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch METAR data: {e}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return None

def read_weather_data():
    """Read and return the weather data from weather.json."""
    try:
        # Use absolute path to ensure consistency
        with open('/home/pi/weather.json', 'r') as json_file:
            data = json.load(json_file)
            return data
    except Exception as e:
        logger.error(f"Failed to read weather.json: {e}")
        return {}

def get_windy_airports(weather_data):
    """Detect and return a dictionary of windy airports with their corresponding colors."""
    windy_airports = {}
    wind_threshold = get_config_value('WIND_THRESHOLD', 20)
    
    for airport_code, weather_info in weather_data.items():
        wind_speed = weather_info.get('wind_speed', 0)
        wind_gust = weather_info.get('wind_gust', 0)
        flt_cat = weather_info.get('flt_cat', 'MISSING')
        
        wind_speed = wind_speed if wind_speed is not None else 0
        wind_gust = wind_gust if wind_gust is not None else 0

        if wind_speed > wind_threshold or wind_gust > wind_threshold:
            flt_cat_color = get_flt_cat_color(flt_cat)
            windy_airports[airport_code] = flt_cat_color

    return windy_airports

LIGHTNING_KEYWORDS = ["TS", "LTG", "VCTS"]

def get_lightning_airports(weather_data):
    """Detect and return a dictionary of airports with lightning and their corresponding colors."""
    lightning_airports = {}
    for airport_code, weather_info in weather_data.items():
        raw_observation = weather_info.get('raw_observation', '')
        flt_cat = weather_info.get('flt_cat', 'MISSING')

        if any(re.search(rf'\b{keyword}\b', raw_observation) for keyword in LIGHTNING_KEYWORDS):
            flt_cat_color = get_flt_cat_color(flt_cat)
            lightning_airports[airport_code] = flt_cat_color

    return lightning_airports

SNOW_KEYWORDS = ["SN", "BLSN", "DRSN", "GS", "SG", "SNINCR", "SP"]

def get_snowy_airports(weather_data):
    """Detect and return a dictionary of airports with snow and their corresponding colors."""
    snowy_airports = {}
    for airport_code, weather_info in weather_data.items():
        raw_observation = weather_info.get('raw_observation', '')
        flt_cat = weather_info.get('flt_cat', 'MISSING')

        if any(re.search(rf'\b{keyword}\b', raw_observation) for keyword in SNOW_KEYWORDS):
            flt_cat_color = get_flt_cat_color(flt_cat)
            snowy_airports[airport_code] = flt_cat_color

    return snowy_airports


def determine_flight_category(raw_metar):
    """Determine flight category from raw METAR string."""
    if not raw_metar or not isinstance(raw_metar, str):
        return 'MISSING'
    
    try:
        visibility = _parse_visibility(raw_metar)
        ceiling = _parse_ceiling(raw_metar)
        
        if visibility is None:
            return 'MISSING'
        
        if visibility >= 5.0:
            if ceiling is None or ceiling >= 3000:
                return 'VFR'
            else:
                return 'MVFR'
        elif visibility >= 3.0:
            if ceiling is None or ceiling >= 1000:
                return 'MVFR'
            else:
                return 'IFR'
        elif visibility >= 1.0:
            if ceiling is None or ceiling >= 500:
                return 'IFR'
            else:
                return 'LIFR'
        else:
            return 'LIFR'
            
    except Exception as e:
        logger.error(f"Error determining flight category from METAR '{raw_metar}': {e}")
        return 'MISSING'


def _parse_visibility(raw_metar):
    """Parse visibility from METAR string."""
    try:
        visibility_pattern = re.compile(r'(\d{1,2}|\d/\d|M\d/\d)SM')
        
        parts = raw_metar.split()
        for part in parts:
            vis_match = visibility_pattern.match(part)
            if vis_match:
                vis_str = vis_match.group(1)
                
                if vis_str.startswith('M'):
                    vis_str = vis_str[1:]
                
                if '/' in vis_str:
                    numerator, denominator = vis_str.split('/')
                    return float(numerator) / float(denominator)
                else:
                    return float(vis_str)
        return None
    except Exception as e:
        logger.error(f"Error parsing visibility from METAR: {e}")
        return None


def _parse_ceiling(raw_metar):
    """Parse ceiling from METAR string."""
    try:
        cloud_pattern = re.compile(r'(FEW|SCT|BKN|OVC|VV)(\d{3})?(CB|TCU)?')
        
        parts = raw_metar.split()
        ceiling_layers = []
        
        for part in parts:
            cloud_match = cloud_pattern.match(part)
            if cloud_match:
                type_str, altitude_str, cloud_type = cloud_match.groups()
                
                if type_str in ['BKN', 'OVC'] and altitude_str:
                    altitude = int(altitude_str) * 100
                    ceiling_layers.append(altitude)
        
        return min(ceiling_layers) if ceiling_layers else None
        
    except Exception as e:
        logger.error(f"Error parsing ceiling from METAR: {e}")
        return None


def get_flt_cat_color(flt_cat):
    """Return the color corresponding to the flight category."""
    if flt_cat == 'VFR':
        return get_config_value('VFR_COLOR', (0, 255, 0))
    elif flt_cat == 'MVFR':
        return get_config_value('MVFR_COLOR', (0, 0, 255))
    elif flt_cat == 'IFR':
        return get_config_value('IFR_COLOR', (255, 0, 0))
    elif flt_cat == 'LIFR':
        return get_config_value('LIFR_COLOR', (255, 0, 255))
    else:
        return get_config_value('MISSING_COLOR', (255, 255, 0))

def get_airport_weather(airport_code, weather_data):
    """Retrieve and format weather data for a given airport."""
    airport_weather = weather_data.get(airport_code, {})
    
    flt_cat = airport_weather.get('flt_cat')
    if flt_cat is None:
        raw_observation = airport_weather.get('raw_observation', '')
        flt_cat = determine_flight_category(raw_observation)
    elif flt_cat == 'MISSING':
        flt_cat = 'MISSING'
    
    wind_speed = airport_weather.get('wind_speed', 0)
    wind_gust = airport_weather.get('wind_gust', 0)
    raw_observation = airport_weather.get('raw_observation', '')
    lightning = any(keyword in raw_observation for keyword in LIGHTNING_KEYWORDS)

    return flt_cat, wind_speed, wind_gust, lightning

def parse_weather(metar_data):
    if not metar_data or 'features' not in metar_data:
        logger.error("Invalid METAR data received for parsing.")
        return {}

    parsed_data = {}
    for feature in metar_data['features']:
        airport_id = feature['properties'].get('icaoId', feature['properties'].get('id', 'UNKNOWN'))
        raw_observation = feature['properties'].get('rawOb', 'N/A')

        coords = feature.get('geometry', {}).get('coordinates', [])
        lat = coords[1] if len(coords) >= 2 else None
        lon = coords[0] if len(coords) >= 2 else None

        lightning = any(keyword in raw_observation for keyword in LIGHTNING_KEYWORDS)

        def safe_get_numeric(properties, key, default=0):
            value = properties.get(key, default)
            return value if value is not None else default
        
        def safe_get_visibility(properties, key, default=0):
            value = properties.get(key, default)
            if value is None:
                return default
            if isinstance(value, str):
                match = re.search(r'\d+', str(value))
                return int(match.group()) if match else default
            return value if isinstance(value, (int, float)) else default
        
        def safe_get_precip(properties, key, default='MISSING'):
            value = properties.get(key, default)
            return value if value is not None else default
        
        api_flt_cat = feature['properties'].get('fltcat')
        if api_flt_cat is not None:
            flt_cat = api_flt_cat
        else:
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
            "cloud_coverage": feature['properties'].get('clouds', []),
            "cover": feature['properties'].get('cover', 'MISSING'),
            "ceiling": safe_get_numeric(feature['properties'], 'ceil', 0),
            "precip": safe_get_precip(feature['properties'], 'wx', 'MISSING'),
            "raw_observation": raw_observation,
            "lightning": lightning,
            "latitude": lat,
            "longitude": lon,
            "site": feature['properties'].get('site', airport_id)
        }
        parsed_data[airport_id] = airport_weather

    return parsed_data

def get_missing_airports(weather_data):
    """Return a list of airports with missing weather data."""
    missing_airports = []
    for airport_code, weather_info in weather_data.items():
        if weather_info.get('flt_cat', 'MISSING') == 'MISSING':
            missing_airports.append(airport_code)
    return missing_airports

def backup_airports_file():
    """Create a backup of the airports file."""
    try:
        airports_file = get_config_value('AIRPORTS_FILE', 'airports.txt')
        with open(airports_file, 'r') as source:
            with open(f"{airports_file}.backup", 'w') as backup:
                backup.write(source.read())
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of airports file: {e}")
        return False

def restore_airports_file():
    """Restore the airports file from backup."""
    try:
        airports_file = get_config_value('AIRPORTS_FILE', 'airports.txt')
        backup_file = f"{airports_file}.backup"
        if not os.path.exists(backup_file):
            logger.error("No backup file found to restore from")
            return False

        with open(backup_file, 'r') as backup:
            with open(airports_file, 'w') as target:
                target.write(backup.read())
        return True
    except Exception as e:
        logger.error(f"Failed to restore airports file from backup: {e}")
        return False

def update_airports_file(airport_codes):
    """Update the airports file with new airport codes, maintaining original positions."""
    try:
        airports_file = get_config_value('AIRPORTS_FILE', 'airports.txt')
        backup_file = f"{airports_file}.backup"
        if not os.path.exists(backup_file):
            if not backup_airports_file():
                return False

        with open(backup_file, 'r') as backup:
            original_content = backup.read()
            original_lines = original_content.splitlines()

        airport_codes = [code.upper() for code in airport_codes]
        updated_lines = ["SKIP"] * len(original_lines)

        for airport in airport_codes:
            try:
                original_pos = original_lines.index(airport)
                updated_lines[original_pos] = airport
            except ValueError:
                logger.warning(f"Airport {airport} not found in original configuration")
                continue

        with open(airports_file, 'w', newline='') as file:
            for i, line in enumerate(updated_lines):
                file.write(line)
                if i < len(updated_lines) - 1:
                    file.write('\n')

        return True
    except Exception as e:
        logger.error(f"Failed to update airports file: {e}")
        return False

STATIONS_FILE = '/home/pi/stations.json'

def load_stations():
    """Load station data from the local JSON file."""
    try:
        if os.path.exists(STATIONS_FILE):
            with open(STATIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load stations file: {e}")
    return {}

def save_stations(stations_data):
    """Save station data to the local JSON file."""
    try:
        with open(STATIONS_FILE, 'w') as f:
            json.dump(stations_data, f, indent=4)
            logger.info(f"Saved {len(stations_data)} stations to {STATIONS_FILE}")
    except Exception as e:
        logger.error(f"Failed to save stations file: {e}")

def fetch_station_info(airport_ids):
    """Fetch station information (coordinates) for specific airports."""
    if not airport_ids:
        return {}

    base_url = "https://aviationweather.gov/api/data/stationinfo"
    params = {
        'ids': ','.join(airport_ids),
        'format': 'geojson'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        station_info = {}
        if 'features' in data:
            for feature in data['features']:
                airport_id = feature['properties'].get('icaoId', feature['properties'].get('id', 'UNKNOWN'))
                coords = feature.get('geometry', {}).get('coordinates', [])
                if len(coords) >= 2:
                    station_info[airport_id] = {
                        'latitude': coords[1],
                        'longitude': coords[0],
                        'site': feature['properties'].get('site', airport_id)
                    }
        return station_info
    except Exception as e:
        logger.error(f"Failed to fetch station info: {e}")
        return {}

def main():
    """Main function to fetch and process weather data."""
    # 1. Load static station data (coordinates)
    stations_data = load_stations()
    stations_updated = False

    # 2. Get the list of expected airports
    airports_file = get_config_value('AIRPORTS_FILE', 'airports.txt')
    expected_airports = get_valid_airports(airports_file)
    
    # 3. Fetch new data
    metar_data = fetch_metar()
    if not metar_data:
        logger.error("Failed to fetch METAR data")
        return

    # 4. Parse new data
    new_weather_data = parse_weather(metar_data)
    if not new_weather_data:
        logger.error("Failed to parse METAR data")
        return

    # 5. Merge data: Ensure all expected airports are present
    final_weather_data = {}
    missing_coords_airports = []
    
    for airport_code in expected_airports:
        # Strategy:
        # 1. Prefer fresh METAR data.
        # 2. If missing, use cached station data (coords) + MISSING status.
        # 3. If no cached station data, queue for fetch.
        
        if airport_code in new_weather_data:
            # We have fresh data
            final_weather_data[airport_code] = new_weather_data[airport_code]
            
            # Opportunistically update station cache if we have new valid coords
            entry = new_weather_data[airport_code]
            if entry.get('latitude') and entry.get('longitude'):
                if airport_code not in stations_data:
                    stations_data[airport_code] = {
                        'latitude': entry['latitude'],
                        'longitude': entry['longitude'],
                        'site': entry.get('site', airport_code)
                    }
                    stations_updated = True
                    
        elif airport_code in stations_data:
            # Missing from API, but we have static coords
            logger.warning(f"Airport {airport_code} missing from API response. Using cached coordinates from stations.json.")
            final_weather_data[airport_code] = {
                "flt_cat": "MISSING",
                "raw_observation": "No data available",
                "site": stations_data[airport_code].get('site', airport_code),
                "latitude": stations_data[airport_code]['latitude'],
                "longitude": stations_data[airport_code]['longitude'],
                "observation_time": "Unknown"
            }
        else:
            # Missing from API and no static coords
            logger.warning(f"Airport {airport_code} missing from API and no cached coordinates. Queuing for station info fetch.")
            missing_coords_airports.append(airport_code)
            # Placeholder
            final_weather_data[airport_code] = {
                "flt_cat": "MISSING",
                "raw_observation": "No data available",
                "site": airport_code
            }

    # 6. Fetch missing coordinates if necessary
    if missing_coords_airports:
        logger.info(f"Fetching station info for {len(missing_coords_airports)} airports: {', '.join(missing_coords_airports)}")
        new_station_info = fetch_station_info(missing_coords_airports)
        
        for airport_code in missing_coords_airports:
            if airport_code in new_station_info:
                # Update final data
                final_weather_data[airport_code]['latitude'] = new_station_info[airport_code]['latitude']
                final_weather_data[airport_code]['longitude'] = new_station_info[airport_code]['longitude']
                final_weather_data[airport_code]['site'] = new_station_info[airport_code]['site']
                
                # Update station cache
                stations_data[airport_code] = new_station_info[airport_code]
                stations_updated = True
                
                logger.info(f"Recovered coordinates for {airport_code}")
            else:
                logger.error(f"Could not find coordinates for {airport_code} even via Station API.")

    # 7. Save station cache if updated
    if stations_updated:
        save_stations(stations_data)

    # 8. Save the combined weather data
    try:
        with open('/home/pi/weather.json', 'w') as json_file:
            json.dump(final_weather_data, json_file, indent=4)
            logger.info(f"Weather data saved to /home/pi/weather.json. Total airports: {len(final_weather_data)}")
    except Exception as e:
        logger.error(f"Failed to write weather data to file: {e}")

if __name__ == "__main__":
    main()
