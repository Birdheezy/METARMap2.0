# config.py
import datetime

PIXEL_PIN = "D18"
NUM_PIXELS = 50
BRIGHTNESS = 0.5

# Animation Configuration
WIND_THRESHOLD = 5          # Airprots with steady state or gusts over this value will be considered "windy"
WIND_FADE_TIME = 0.5        # Time in seconds for the LED to fade in/out
WIND_PAUSE = 1.5            # Pause time in seconds at DIM_BRIGHTNESS level
ANIMATION_PAUSE = 2         # Time in seconds between animation cycles
DIM_BRIGHTNESS = 0.05
NUM_STEPS = 100             # The number of steps the LED takes to dim

BRIGHT_TIME_START = datetime.time(7, 25)
DIM_TIME_START = datetime.time(20, 35)


# Snow animation settings
SNOW_BLINK_COUNT = 4        # Number of times to blink for snowy airports
SNOW_BLINK_PAUSE = 0.4      # Pause duration in seconds between blinks


AIRPORTS_FILE = 'airports.txt'

# Color Definitions in GRB order
VFR_COLOR = (255, 0, 0)             # Green 
MVFR_COLOR = (0, 0, 255)            # Blue 
IFR_COLOR = (0, 255, 0)             # Red 
LIFR_COLOR = (0, 255, 255)          # Magenta
MISSING_COLOR = (165, 255, 0)       # Orange
LIGHTENING_COLOR = (255, 255, 255)  # White


WIND_ANIMATION = True           # Turn windy animation on or off
LIGHTENING_ANIMATION = True     # Turn lightening animation on or off
SNOWY_ANIMATION = True          # Turn snowy animation on or off
VFR_COLOR = (255, 0, 0)             # Green 
MVFR_COLOR = (0, 0, 255)            # Blue 
IFR_COLOR = (0, 255, 0)             # Red 
LIFR_COLOR = (0, 255, 255)          # Magenta
MISSING_COLOR = (165, 255, 0)       # Orange
LIGHTENING_COLOR = (255, 255, 255)  # White


WIND_ANIMATION = True           # Turn windy animation on or off
LIGHTENING_ANIMATION = True     # Turn lightening animation on or off
SNOWY_ANIMATION = True          # Turn snowy animation on or off