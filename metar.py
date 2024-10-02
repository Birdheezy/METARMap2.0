import json
import time
import signal
import sys
import board
import neopixel
from config import *
import weather


# Initialize NeoPixel object using full module reference
pixels = neopixel.NeoPixel(getattr(board, PIXEL_PIN), NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)

def cleanup(signal, frame):
    """Turn off all LEDs and exit."""
    pixels.fill((0, 0, 0))  # Turn off all LEDs
    pixels.show()
    sys.exit(0)

# Attach the signal handler to SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, cleanup)

#######------ ANIMATIONS ------#######

def animate_lightning_airports(lightning_airports, weather_data):
    """Animate the airports with detected lightning by flashing the LEDs."""
    # Scale white color by BRIGHTNESS to maintain consistent brightness
    scaled_lightning_color = tuple(int(c * BRIGHTNESS) for c in (255, 255, 255))

    for _ in range(2):  # Flash twice
        for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
            if airport_code in lightning_airports:
                # Set LED to scaled white color for flash
                pixels[index] = scaled_lightning_color
        pixels.show()
        time.sleep(0.1)  # Short delay for rapid flash

        for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
            if airport_code in lightning_airports:
                # Revert back to flt_cat color
                flt_cat, _, _, _ = weather.get_airport_weather(airport_code, weather_data)
                if flt_cat == 'VFR':
                    pixels[index] = tuple(int(c * BRIGHTNESS) for c in VFR_COLOR)
                elif flt_cat == 'MVFR':
                    pixels[index] = tuple(int(c * BRIGHTNESS) for c in MVFR_COLOR)
                elif flt_cat == 'IFR':
                    pixels[index] = tuple(int(c * BRIGHTNESS) for c in IFR_COLOR)
                elif flt_cat == 'LIFR':
                    pixels[index] = tuple(int(c * BRIGHTNESS) for c in LIFR_COLOR)
                else:
                    pixels[index] = tuple(int(c * BRIGHTNESS) for c in MISSING_COLOR)
        pixels.show()
        time.sleep(0.2)  # Short delay before the next flash


def animate_windy_airports(windy_airports, weather_data):
    """Animate the windy airports by dimming and brightening LEDs."""
    num_steps = 100  # Number of steps for the animation
    step_delay = WIND_FADE_TIME / num_steps  # Calculate delay per step

    # Step 1: Gradual fade to DIM_BRIGHTNESS
    for step in range(num_steps):
        brightness = BRIGHTNESS - (BRIGHTNESS - DIM_BRIGHTNESS) * (step / num_steps)
        for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
            if airport_code in windy_airports:
                flt_cat, _, _, _ = weather.get_airport_weather(airport_code, weather_data)
                color = weather.get_flt_cat_color(flt_cat)
                pixel_color = tuple(int(c * brightness) for c in color)
                pixels[index] = pixel_color
        pixels.show()
        time.sleep(step_delay)

    # Pause at DIM_BRIGHTNESS
    time.sleep(WIND_PAUSE)

    # Step 2: Gradual fade back to full BRIGHTNESS
    for step in range(num_steps):
        brightness = DIM_BRIGHTNESS + (BRIGHTNESS - DIM_BRIGHTNESS) * (step / num_steps)
        for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
            if airport_code in windy_airports:
                flt_cat, _, _, _ = weather.get_airport_weather(airport_code, weather_data)
                color = weather.get_flt_cat_color(flt_cat)
                pixel_color = tuple(int(c * brightness) for c in color)
                pixels[index] = pixel_color
        pixels.show()
        time.sleep(step_delay)

def animate_snowy_airports(snowy_airports, weather_data):
    """Animate the snowy airports with a twinkling white effect."""
    # Use a dim white color to represent snow
    snowy_color = tuple(int(c * BRIGHTNESS) for c in (128, 128, 128))  # Dim white color

    # Twinkling effect: alternate between on and off state
    for _ in range(SNOW_BLINK_COUNT):  # Use SNOW_BLINK_COUNT for the number of twinkles
        for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
            if airport_code in snowy_airports:
                # Set LED to snowy color
                pixels[index] = snowy_color
        pixels.show()
        time.sleep(SNOW_BLINK_PAUSE)  # Use SNOW_BLINK_PAUSE for twinkle on duration

        for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
            if airport_code in snowy_airports:
                # Turn off LED to create a twinkling effect
                pixels[index] = (0, 0, 0)
        pixels.show()
        time.sleep(SNOW_BLINK_PAUSE)  # Use SNOW_BLINK_PAUSE for twinkle off duration

    # Revert back to the original flight category colors after animation
    for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
        if airport_code in snowy_airports:
            flt_cat, _, _, _ = weather.get_airport_weather(airport_code, weather_data)
            pixels[index] = tuple(int(c * BRIGHTNESS) for c in weather.get_flt_cat_color(flt_cat))
    pixels.show()


#from config import BRIGHTNESS  # Import BRIGHTNESS from config.py

def update_leds(weather_data):
    """Update LEDs based on flt_cat from weather data."""
    # Get list of airports, including "SKIP" entries
    airport_list = weather.get_airports_with_skip(AIRPORTS_FILE)

    # Detect windy airports
    windy_airports = weather.get_windy_airports(weather_data)

    # Detect lightning airports
    lightning_airports = weather.get_lightning_airports(weather_data)

    # Print header
    print(f"{'Airport':<10} {'Flight Cat':<12} {'Wind Speed':<12} {'Wind Gust':<12} {'Windy':<6} {'Lightning':<10}")
    print("-" * 70)  # Separator line for better readability

    # Update LEDs based on flt_cat and print details
    for index, airport_code in enumerate(airport_list):
        if airport_code == "SKIP":
            pixels[index] = (0, 0, 0)  # Turn off LED if airport is SKIP
        else:
            # Get flight category, wind data, and lightning status for the airport
            flt_cat, wind_speed, wind_gust, lightning = weather.get_airport_weather(airport_code, weather_data)
            
            # Check if the airport is in the windy_airports and lightning_airports dictionaries
            is_windy = "Yes" if airport_code in windy_airports else "No"
            is_lightning = "Yes" if airport_code in lightning_airports else "No"  # Based on lightning detection

            # Print each airport, flight category, wind speed, wind gust, whether it is windy, and lightning
            print(f"{airport_code:<10} {flt_cat:<12} {str(wind_speed) + ' kt':<12} {str(wind_gust) + ' kt':<12} {is_windy:<6} {is_lightning:<10}")

            # Update LED colors based on flt_cat, applying the BRIGHTNESS factor
            base_color = weather.get_flt_cat_color(flt_cat)
            pixels[index] = tuple(int(c * BRIGHTNESS) for c in base_color)

    pixels.show()


# Main loop
while True:
    # Read the weather data and update the LEDs
    weather_data = weather.read_weather_data()
    update_leds(weather_data)

    time.sleep(ANIMATION_PAUSE)

    # Check for lightning airports and animate if any, if LIGHTENING_ANIMATION is True
    if LIGHTENING_ANIMATION:
        lightning_airports = weather.get_lightning_airports(weather_data)
        if lightning_airports:
            animate_lightning_airports(lightning_airports, weather_data)

    # Check for windy airports and animate if any, if WIND_ANIMATION is True
    if WIND_ANIMATION:
        windy_airports = weather.get_windy_airports(weather_data)
        if windy_airports:
            animate_windy_airports(windy_airports, weather_data)

    # Check for snowy airports and animate if any
    snowy_airports = weather.get_snowy_airports(weather_data)
    if snowy_airports:
        animate_snowy_airports(snowy_airports, weather_data)  # We'll define this function next
