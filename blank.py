from config import *  # Import settings from config.py
import board
import neopixel


pixel_pin = f"D{PIXEL_PIN}"  # Create "D18"
pixels = neopixel.NeoPixel(getattr(board, pixel_pin), NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)

# Blank the LEDs
pixels.fill((0, 0, 0))  # Set all pixels to 'off' (black)
pixels.show()            # Apply the changes
