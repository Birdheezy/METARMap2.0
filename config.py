# config.py
import datetime

AIRPORTS_FILE = 'airports.txt'
PIXEL_PIN = "D18"
NUM_PIXELS = 50
BRIGHTNESS = 0.4
DAYTIME_DIM_BRIGHTNESS = 0.3

# Animation Configuration
WIND_THRESHOLD = 8
WIND_FADE_TIME = 0.5
WIND_PAUSE = 1.2
ANIMATION_PAUSE = 4
DIM_BRIGHTNESS = 0.05
NUM_STEPS = 100
LIGHTNING_FLASH_COUNT = 3

# Snow animation settings
SNOW_BLINK_COUNT = 3
SNOW_BLINK_PAUSE = 0.4

#Time Variables
LIGHTS_OFF_TIME = datetime.time(22, 0)
LIGHTS_ON_TIME = datetime.time(6, 30)
BRIGHT_TIME_START = datetime.time(7, 15)
DIM_TIME_START = datetime.time(18, 10)

# Color Definitions in GRB order
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
ENABLE_LIGHTS_OFF = True
