import datetime
import pytz
from astral import LocationInfo
from astral.sun import sun

AIRPORTS_FILE = 'airports.txt'
PIXEL_PIN = 18
NUM_PIXELS = 30
BRIGHTNESS = 0.5
DAYTIME_DIM_BRIGHTNESS = 0.2
LED_COLOR_ORDER = 'RGB'
WIND_THRESHOLD = 20
WIND_FADE_TIME = 0.5
WIND_PAUSE = 2
ANIMATION_PAUSE = 5
DIM_BRIGHTNESS = 0.05
NUM_STEPS = 100
LIGHTNING_FLASH_COUNT = 4
WEATHER_UPDATE_INTERVAL = 300
WIFI_CHECK_INTERVAL = 300
SNOW_BLINK_COUNT = 4
SNOW_BLINK_PAUSE = 0.4
LIGHTS_ON_TIME = datetime.time(6, 30)
LIGHTS_OFF_TIME = datetime.time(22, 0)
BRIGHT_TIME_START = datetime.time(5, 56)
DIM_TIME_START = datetime.time(20, 15)
VFR_COLOR = (0, 255, 0)
MVFR_COLOR = (0, 0, 255)
IFR_COLOR = (255, 0, 0)
LIFR_COLOR = (255, 0, 255)
MISSING_COLOR = (255, 255, 0)
LIGHTENING_COLOR = (255, 255, 255)
SNOWY_COLOR = (0, 255, 255)
STALE_DATA_COLOR = (75, 75, 0)
WIFI_DISCONNECTED_COLOR = (75, 0, 0)
WIND_ANIMATION = True
LIGHTENING_ANIMATION = True
SNOWY_ANIMATION = True
DAYTIME_DIMMING = True
ENABLE_LIGHTS_OFF = False
LEGEND = False
ENABLE_HTTPS = True
UPDATE_WEATHER = True
STALE_INDICATION = True
WIFI_INDICATION = True
MAP_CENTER_LAT = 39.98974718404572
MAP_CENTER_LON = '-104.69421386718751'
MAP_ZOOM = 8
SELECTED_CITY = 'Denver, CO'
USE_SUNRISE_SUNSET = True

# Legend item visibility settings
LEGEND_VFR = True
LEGEND_MVFR = True
LEGEND_IFR = True
LEGEND_LIFR = True
LEGEND_SNOWY = True
LEGEND_LIGHTNING = True
LEGEND_WINDY = True
LEGEND_MISSING = True

CITIES = [{'name': 'New York, NY', 'lat': 40.7128, 'lon': -74.006, 'timezone': 'America/New_York'}, {'name': 'Miami, FL', 'lat': 25.7617, 'lon': -80.1918, 'timezone': 'America/New_York'}, {'name': 'Atlanta, GA', 'lat': 33.749, 'lon': -84.388, 'timezone': 'America/New_York'}, {'name': 'Boston, MA', 'lat': 42.3601, 'lon': -71.0589, 'timezone': 'America/New_York'}, {'name': 'Philadelphia, PA', 'lat': 39.9526, 'lon': -75.1652, 'timezone': 'America/New_York'}, {'name': 'Washington, DC', 'lat': 38.9072, 'lon': -77.0369, 'timezone': 'America/New_York'}, {'name': 'Chicago, IL', 'lat': 41.8781, 'lon': -87.6298, 'timezone': 'America/Chicago'}, {'name': 'Houston, TX', 'lat': 29.7604, 'lon': -95.3698, 'timezone': 'America/Chicago'}, {'name': 'Dallas, TX', 'lat': 32.7767, 'lon': -96.797, 'timezone': 'America/Chicago'}, {'name': 'New Orleans, LA', 'lat': 29.9511, 'lon': -90.0715, 'timezone': 'America/Chicago'}, {'name': 'Minneapolis, MN', 'lat': 44.9778, 'lon': -93.265, 'timezone': 'America/Chicago'}, {'name': 'Denver, CO', 'lat': 39.7392, 'lon': -104.9903, 'timezone': 'America/Denver'}, {'name': 'Phoenix, AZ', 'lat': 33.4484, 'lon': -112.074, 'timezone': 'America/Phoenix'}, {'name': 'Salt Lake City, UT', 'lat': 40.7608, 'lon': -111.891, 'timezone': 'America/Denver'}, {'name': 'Albuquerque, NM', 'lat': 35.0844, 'lon': -106.6504, 'timezone': 'America/Denver'}, {'name': 'Los Angeles, CA', 'lat': 34.0522, 'lon': -118.2437, 'timezone': 'America/Los_Angeles'}, {'name': 'San Francisco, CA', 'lat': 37.7749, 'lon': -122.4194, 'timezone': 'America/Los_Angeles'}, {'name': 'Seattle, WA', 'lat': 47.6062, 'lon': -122.3321, 'timezone': 'America/Los_Angeles'}, {'name': 'Portland, OR', 'lat': 45.5152, 'lon': -122.6784, 'timezone': 'America/Los_Angeles'}, {'name': 'San Diego, CA', 'lat': 32.7157, 'lon': -117.1611, 'timezone': 'America/Los_Angeles'}, {'name': 'Las Vegas, NV', 'lat': 36.1699, 'lon': -115.1398, 'timezone': 'America/Los_Angeles'}, {'name': 'Anchorage, AK', 'lat': 61.2181, 'lon': -149.9003, 'timezone': 'America/Anchorage'}, {'name': 'Fairbanks, AK', 'lat': 64.8378, 'lon': -147.7164, 'timezone': 'America/Anchorage'}, {'name': 'Honolulu, HI', 'lat': 21.3099, 'lon': -157.8581, 'timezone': 'Pacific/Honolulu'}]