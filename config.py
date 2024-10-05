# config.py
import datetime

PIXEL_PIN = "D18"
NUM_PIXELS = 50
BRIGHTNESS = 0.5
DAYTIME_DIM_BRIGHTNESS = 0.2

# Animation Configuration
WIND_THRESHOLD = 10
WIND_FADE_TIME = 0.5
WIND_PAUSE = 1.5
ANIMATION_PAUSE = 10
DIM_BRIGHTNESS = 0.05
NUM_STEPS = 100

# Snow animation settings
SNOW_BLINK_COUNT = 2
SNOW_BLINK_PAUSE = 0.3

BRIGHT_TIME_START = datetime.time(7, 00)
DIM_TIME_START = datetime.time(19, 00)

AIRPORTS_FILE = 'airports.txt'

# Color Definitions in GRB order
VFR_COLOR = (255, 0, 0)             # Green 
MVFR_COLOR = (0, 0, 255)            # Blue 
IFR_COLOR = (0, 255, 0)             # Red 
LIFR_COLOR = (0, 255, 255)          # Magenta
MISSING_COLOR = (165, 255, 0)       # Orange
LIGHTENING_COLOR = (255, 255, 255)  # White


VFR_COLOR = (255, 0, 0)             # Green 
MVFR_COLOR = (0, 0, 255)            # Blue 
IFR_COLOR = (0, 255, 0)             # Red 
LIFR_COLOR = (0, 255, 255)          # Magenta
MISSING_COLOR = (165, 255, 0)       # Orange
LIGHTENING_COLOR = (255, 255, 255)  # White


WIND_ANIMATION = True
LIGHTENING_ANIMATION = True
SNOWY_ANIMATION = True
DAYTIME_DIMMING = True
