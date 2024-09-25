#!/usr/bin/env python3

# Import standard libraries
import time  # For delay/sleep functionality
import logging  # For logging application activities and errors

# Import third-party libraries
import requests  # For making HTTP requests to fetch weather data
from neopixel import NeoPixel  # For controlling WS2811 LEDs
import board  # For identifying GPIO pins (specific to Raspberry Pi)

# Import custom configuration
from config import *

# Setting up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize NeoPixel object with the LED_ORDER
pixels = NeoPixel(
    getattr(board, PIXEL_PIN), 
    NUM_PIXELS, 
    brightness=BRIGHTNESS, 
    auto_write=False, 
    pixel_order=getattr(NeoPixel, LED_ORDER)
)

logging.info("NeoPixel strip initialized on GPIO %s with %d LEDs in %s order.", PIXEL_PIN, NUM_PIXELS, LED_ORDER)

# Function to read airport identifiers when needed
def get_airports():
    """Read the airport identifiers from the file."""
    try:
        with open(AIRPORTS_FILE, 'r') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        logging.error("Failed to read the airport file: %s", e)
        return []

# Example usage of reading the airport identifiers
airport_identifiers = get_airports()
logging.info("Loaded %d airport identifiers.", len(airport_identifiers))
