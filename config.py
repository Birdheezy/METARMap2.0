import datetime

AIRPORTS_FILE = 'airports.txt'
PIXEL_PIN = 18
NUM_PIXELS = 50
BRIGHTNESS = 0.5
DAYTIME_DIM_BRIGHTNESS = 0.2
LED_COLOR_ORDER = 'GRB'

# Animation Configuration
WIND_THRESHOLD = 20
WIND_FADE_TIME = 0.5
WIND_PAUSE = 2
ANIMATION_PAUSE = 15
DIM_BRIGHTNESS = 0.05
NUM_STEPS = 100
LIGHTNING_FLASH_COUNT = 3
WEATHER_UPDATE_INTERVAL = 300
WIFI_CHECK_INTERVAL = 300

# Snow animation settings
SNOW_BLINK_COUNT = 3
SNOW_BLINK_PAUSE = 0.4

#Time Variables
LIGHTS_ON_TIME = datetime.time(6, 30)
LIGHTS_OFF_TIME = datetime.time(22, 0)
BRIGHT_TIME_START = datetime.time(7, 0)
DIM_TIME_START = datetime.time(17, 0)

# LED Configuration
LED_COLOR_ORDER = 'GRB'  # Options: 'RGB' for RGB LEDs, 'GRB' for most NeoPixels

# Define true RGB colors (standard order)
_VFR = (0, 255, 0)      # Green
_MVFR = (0, 0, 255)     # Blue
_IFR = (255, 0, 0)      # Red
_LIFR = (255, 0, 255)   # Magenta
_MISSING = (255, 165, 0) # Orange
_LIGHTNING = (255, 255, 255) # White
_SNOWY = (255, 165, 255) # Pink-ish
_STALE = (75, 75, 0)    # Dark yellow
_WIFI_DISC = (75, 0, 0) # Dark red

# Convert colors to GRB order if needed
if LED_COLOR_ORDER == 'GRB':
    def _to_grb(rgb_color):
        r, g, b = rgb_color
        return (g, r, b)  # Swap R and G

    VFR_COLOR = _to_grb(_VFR)
    MVFR_COLOR = _to_grb(_MVFR)
    IFR_COLOR = _to_grb(_IFR)
    LIFR_COLOR = _to_grb(_LIFR)
    MISSING_COLOR = _to_grb(_MISSING)
    LIGHTENING_COLOR = _to_grb(_LIGHTNING)
    SNOWY_COLOR = _to_grb(_SNOWY)
    STALE_DATA_COLOR = _to_grb(_STALE)
    WIFI_DISCONNECTED_COLOR = _to_grb(_WIFI_DISC)
else:
    # Use RGB colors directly
    VFR_COLOR = _VFR
    MVFR_COLOR = _MVFR
    IFR_COLOR = _IFR
    LIFR_COLOR = _LIFR
    MISSING_COLOR = _MISSING
    LIGHTENING_COLOR = _LIGHTNING
    SNOWY_COLOR = _SNOWY
    STALE_DATA_COLOR = _STALE
    WIFI_DISCONNECTED_COLOR = _WIFI_DISC

#True/False Configuration
WIND_ANIMATION = True
LIGHTENING_ANIMATION = True
SNOWY_ANIMATION = True
DAYTIME_DIMMING = True
ENABLE_LIGHTS_OFF = True
LEGEND = False
ENABLE_HTTPS = False
UPDATE_WEATHER = True
STALE_INDICATION = True
WIFI_INDICATION = True
