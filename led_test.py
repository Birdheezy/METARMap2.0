from config import * # Import settings from config.py
import board
import neopixel

pixel_pin = f"D{PIXEL_PIN}"  # Create "D18"
pixels = neopixel.NeoPixel(getattr(board, pixel_pin), NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False, pixel_order=LED_COLOR_ORDER)

def test_leds(color):
    """Test all LEDs with a given color"""
    pixels.fill(color)
    pixels.show()

def test_specific_leds(color, start_pixel=None, end_pixel=None):
    """
    Test specific LEDs with a given color

    Args:
        color: RGB tuple (r, g, b)
        start_pixel: Starting pixel index (0-based)
        end_pixel: Ending pixel index (inclusive)
    """
    # If no range specified, test all LEDs
    if start_pixel is None and end_pixel is None:
        pixels.fill(color)
    else:
        # Validate pixel range
        if start_pixel is None:
            start_pixel = 0
        if end_pixel is None:
            end_pixel = NUM_PIXELS - 1

        # Ensure values are within valid range
        start_pixel = max(0, min(start_pixel, NUM_PIXELS - 1))
        end_pixel = max(0, min(end_pixel, NUM_PIXELS - 1))

        # Ensure start is less than or equal to end
        if start_pixel > end_pixel:
            start_pixel, end_pixel = end_pixel, start_pixel

        # Set the specified range of pixels to the color
        for i in range(start_pixel, end_pixel + 1):
            pixels[i] = color

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
    pass
