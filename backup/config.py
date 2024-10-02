# config.py

# NeoPixel Configuration
NUM_PIXELS = 30  # Replace with the number of LEDs in your strip
PIXEL_PIN = "D18"  # GPIO Pin for NeoPixel (using string format for board import)
BRIGHTNESS = 0.5  # Brightness of the LEDs (0.0 to 1.0)
LED_ORDER = "GRB"  # NeoPixel color order

# File path for airports.txt
AIRPORTS_FILE = 'airports.txt'

# Color Definitions in GRB order
VFR_COLOR = (255, 0, 0)      # Green in GRB format
MVFR_COLOR = (0, 0, 255)     # Blue in GRB format
IFR_COLOR = (0, 255, 0)      # Red in GRB format
LIFR_COLOR = (0, 255, 255)   # Magenta in GRB format
MISSING_COLOR = (165, 255, 0) # Orange in GRB format
