# config.py
PIXEL_PIN = "D18"
NUM_PIXELS = 50

# NeoPixel Configuration
BRIGHTNESS = 0.3
WIND_THRESHOLD = 5  # Set your desired threshold value here
WIND_FADE_TIME = 0.5  # Time in seconds for the LED to fade in/out
WIND_PAUSE = 1.5  # Pause time in seconds at DIM_BRIGHTNESS level
ANIMATION_PAUSE = 2  # Time in seconds between animation cycles
DIM_BRIGHTNESS = 0.05  # Minimum brightness level for the animation

# File path for airports.txt
AIRPORTS_FILE = 'airports.txt'

# Color Definitions in GRB order
VFR_COLOR = (255, 0, 0)      # Green in GRB format
MVFR_COLOR = (0, 0, 255)     # Blue in GRB format
IFR_COLOR = (0, 255, 0)      # Red in GRB format
LIFR_COLOR = (0, 255, 255)   # Magenta in GRB format
MISSING_COLOR = (165, 255, 0) # Orange in GRB format
LIGHTENING_COLOR = (255, 255, 255)

WIND_ANIMATION = True
num_steps = 100