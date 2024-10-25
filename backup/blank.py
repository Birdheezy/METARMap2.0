from config import *  # Import settings from config.py
import board
import neopixel

# Create NeoPixel object using PIXEL_PIN and NUM_PIXELS from config.py
pixels = neopixel.NeoPixel(getattr(board, PIXEL_PIN), NUM_PIXELS, brightness=0.0, auto_write=False)

# Blank the LEDs
pixels.fill((0, 0, 0))  # Set all pixels to 'off' (black)
pixels.show()            # Apply the changes
