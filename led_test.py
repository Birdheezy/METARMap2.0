from config import *  # Import settings from config.py
import board
import neopixel

pixel_pin = f"D{PIXEL_PIN}"  # Create "D18"
pixels = neopixel.NeoPixel(getattr(board, pixel_pin), NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False, pixel_order=LED_COLOR_ORDER)

def test_leds(color):
    """Test all LEDs with a given color"""
    pixels.fill(color)
    pixels.show()

def turn_off_leds():
    """Turn off all LEDs"""
    pixels.fill((0, 0, 0))
    pixels.show()

def update_brightness(brightness):
    """Update the brightness of all LEDs"""
    pixels.brightness = brightness
    pixels.show()

if __name__ == "__main__":
    # Example usage
    test_leds((255, 0, 0))  # Test with red 