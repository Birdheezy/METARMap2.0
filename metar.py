#metar.py test
import json
import time
import signal
import sys
import board
import neopixel
from config import *
import weather
import datetime
import subprocess


current_time = datetime.datetime.now().time()

# Determine brightness level based on the time of day
def get_current_brightness():
    """Determine the current brightness level based on the time."""
    current_time = datetime.datetime.now().time()
    if DAYTIME_DIMMING:
        if BRIGHT_TIME_START <= current_time < DIM_TIME_START:
            return BRIGHTNESS  # Full brightness during the day
        else:
            return DAYTIME_DIM_BRIGHTNESS  # Dim brightness outside of daytime hours
    else:
        return BRIGHTNESS  # Full brightness if daytime dimming is disabled

def update_led_brightness(pixels):
    """Check the time and update LED brightness if needed."""
    new_brightness = get_current_brightness()
    if pixels.brightness != new_brightness:
        pixels.brightness = new_brightness
        pixels.show()  # Update LEDs to reflect the brightness change
        print(f"Brightness updated to {new_brightness} based on time.")


# Initialize NeoPixel object with the appropriate brightness level
pixels = neopixel.NeoPixel(getattr(board, PIXEL_PIN), NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)

if DAYTIME_DIMMING:
    print(f"Daytime dimming is enabled. Current brightness level: {get_current_brightness()}")
else:
    print(f"Daytime dimming is disabled. Using full brightness: {get_current_brightness()}")

def cleanup(signal, frame):
    """Turn off all LEDs and exit."""
    pixels.fill((0, 0, 0))  # Turn off all LEDs
    pixels.show()
    sys.exit(0)

# Attach the signal handler to SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, cleanup)

def check_lights_off():
    """Check if the current time is within the lights off period and run blank.py if needed."""
    current_time = datetime.datetime.now().time()  # Get the current time

    # Check if the lights off feature is enabled
    if ENABLE_LIGHTS_OFF:
        # Case 1: LIGHTS_OFF_TIME is later in the day than LIGHTS_ON_TIME (e.g., 19:05 to 17:05 overnight)
        if LIGHTS_OFF_TIME > LIGHTS_ON_TIME:
            if current_time >= LIGHTS_OFF_TIME or current_time < LIGHTS_ON_TIME:
                # Current time is either later than LIGHTS_OFF_TIME or earlier than LIGHTS_ON_TIME
                subprocess.run(["sudo", "/home/pi/metar/bin/python3", "/home/pi/blank.py"])
                print("Lights turned off due to time restrictions.")
                return True  # Indicate that lights are off

        # Case 2: LIGHTS_OFF_TIME is earlier or equal to LIGHTS_ON_TIME (e.g., 06:00 to 19:00)
        elif LIGHTS_OFF_TIME <= current_time < LIGHTS_ON_TIME:
            # Current time is within the regular lights off time period
            subprocess.run(["sudo", "/home/pi/metar/bin/python3", "/home/pi/blank.py"])
            print("Lights turned off due to time restrictions.")
            return True  # Indicate that lights are off

    print("Lights remain on.")  # Debugging statement to know if lights are staying on
    return False  # Indicate that lights should remain on


#######------ ANIMATIONS ------#######

def animate_lightning_airports(lightning_airports, weather_data):
    """Animate the airports with detected lightning by flashing the LEDs."""
    # Scale white color by BRIGHTNESS to maintain consistent brightness
    scaled_lightning_color = tuple(int(c * BRIGHTNESS) for c in (255, 255, 255))

    for _ in range(LIGHTNING_FLASH_COUNT):  # Flash twice
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
    step_delay = WIND_FADE_TIME / NUM_STEPS  # Calculate delay per step

    # Step 1: Gradual fade to DIM_BRIGHTNESS
    for step in range(NUM_STEPS):
        brightness = BRIGHTNESS - (BRIGHTNESS - DIM_BRIGHTNESS) * (step / NUM_STEPS)
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
    for step in range(NUM_STEPS):
        brightness = DIM_BRIGHTNESS + (BRIGHTNESS - DIM_BRIGHTNESS) * (step / NUM_STEPS)
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
    
    if check_lights_off():
        # If lights are off, skip updating the LEDs
        pixels.fill((0,0,0))
        pixels.show()
        return
        
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
            print(f"{airport_code:<10} {flt_cat:<12} {str(wind_speed) + ' kt':<12} {str(wind_gust) + ' kt':<12} {is_windy:<6} {is_lightning:<10} {get_current_brightness():<10}")

            # Update LED colors based on flt_cat, applying the BRIGHTNESS factor
            base_color = weather.get_flt_cat_color(flt_cat)
            pixels[index] = tuple(int(c * BRIGHTNESS) for c in base_color)

    pixels.show()


# Main loop
while True:
    # Check if the lights should be off based on current time
    lights_off = check_lights_off()

    if not lights_off:
        # Read the weather data and update the LEDs if lights are on
        weather_data = weather.read_weather_data()
        update_leds(weather_data)
        update_led_brightness(pixels)
        time.sleep(ANIMATION_PAUSE)

        # Check for windy airports and animate if any, if WIND_ANIMATION is True
        if WIND_ANIMATION:
            windy_airports = weather.get_windy_airports(weather_data)
            if windy_airports:
                animate_windy_airports(windy_airports, weather_data)

        # Check for lightning airports and animate if any, if LIGHTENING_ANIMATION is True
        if LIGHTENING_ANIMATION:
            lightning_airports = weather.get_lightning_airports(weather_data)
            if lightning_airports:
                animate_lightning_airports(lightning_airports, weather_data)

        # Check for snowy airports and animate if any, if SNOWY_ANIMATION is True
        if SNOWY_ANIMATION:
            snowy_airports = weather.get_snowy_airports(weather_data)
            if snowy_airports:
                animate_snowy_airports(snowy_airports, weather_data)

    else:
        # If lights should be off, ensure LEDs are off
        pixels.fill((0, 0, 0))
        pixels.show()