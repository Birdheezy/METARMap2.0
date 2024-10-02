import board
import neopixel

# Configuration
PIXEL_PIN = board.D18  # Replace with your pin if different
NUM_PIXELS = 30  # Replace with the number of LEDs in your strip
BRIGHTNESS = 0.5  # Adjust the brightness (0.0 to 1.0)

# Initialize NeoPixel object
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)

# Light up the first LED with red color
pixels[0] = (255, 0, 0)  # Red
pixels.show()
