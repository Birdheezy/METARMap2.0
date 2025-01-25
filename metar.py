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
import logging

# Configure logging with more detailed format for CLI mode
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Let journald handle timestamp in service mode
)

logger = logging.getLogger(__name__)

# Log startup with basic system info
logger.info("METAR service starting up...")
logger.info(f"Python version: {sys.version.split()[0]}")
logger.info(f"Board: {board.board_id}")
logger.info(f"Pixel count: {NUM_PIXELS}")
logger.info(f"Daytime dimming: {'enabled' if DAYTIME_DIMMING else 'disabled'}")

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
        logger.info(f"Brightness updated to {new_brightness:.2f}")

try:
    pixel_pin = f"D{PIXEL_PIN}"  # Create "D18"
    pixels = neopixel.NeoPixel(getattr(board, pixel_pin), NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)
    logger.info(f"LED strip initialized on pin D{PIXEL_PIN}")
except Exception as e:
    logger.error(f"Failed to initialize LED strip: {e}")
    sys.exit(1)

if DAYTIME_DIMMING:
    logger.info(f"Daytime dimming is enabled. Current brightness level: {get_current_brightness()}")
else:
    logger.info(f"Daytime dimming is disabled. Using full brightness: {get_current_brightness()}")

def cleanup(signal, frame):
    """Turn off all LEDs and exit."""
    logger.info("Received shutdown signal, cleaning up...")
    pixels.fill((0, 0, 0))  # Turn off all LEDs
    pixels.show()
    sys.exit(0)

# Attach the signal handler to SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, cleanup)

def check_lights_off():
    """Check if the current time is within the lights off period."""
    current_time = datetime.datetime.now().time()

    if ENABLE_LIGHTS_OFF:
        # Case 1: LIGHTS_OFF_TIME is later than LIGHTS_ON_TIME
        if LIGHTS_OFF_TIME > LIGHTS_ON_TIME:
            if current_time >= LIGHTS_OFF_TIME or current_time < LIGHTS_ON_TIME:
                logger.info("Lights turned off - outside operational hours")
                pixels.fill((0, 0, 0))
                pixels.show()
                return True

        # Case 2: LIGHTS_OFF_TIME is earlier or equal to LIGHTS_ON_TIME
        elif LIGHTS_OFF_TIME <= current_time < LIGHTS_ON_TIME:
            logger.info("Lights turned off - outside operational hours")
            pixels.fill((0, 0, 0))
            pixels.show()
            return True

    return False

def calculate_dimmed_color(base_color, dim_brightness):
    """Calculate the dimmed color by applying the brightness factor."""
    return tuple(int(c * dim_brightness) for c in base_color)

def update_legend(pixels):
    """Update the legend LEDs at the end of the strand if LEGEND is enabled."""
    if not LEGEND:
        return  # Do nothing if the legend is disabled

    # Dynamically calculate the WINDY color
    WINDY_COLOR = calculate_dimmed_color(VFR_COLOR, DIM_BRIGHTNESS)

    legend_colors = [
        VFR_COLOR,
        MVFR_COLOR,
        IFR_COLOR,
        LIFR_COLOR,
        MISSING_COLOR,
        LIGHTENING_COLOR,
        WINDY_COLOR,
        SNOWY_COLOR
    ]

    # Start from the end of the strand
    start_index = NUM_PIXELS - len(legend_colors)

    for i, color in enumerate(legend_colors):
        if start_index + i < NUM_PIXELS:  # Ensure we don't go out of bounds
            # Adjust for GRB color order if needed
            pixels[start_index + i] = (color[0], color[1], color[2])  # GRB

    pixels.show()


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
    snowy_color = tuple(int(c * BRIGHTNESS) for c in SNOWY_COLOR)

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
        return
        
    # Get list of airports, including "SKIP" entries
    airport_list = weather.get_airports_with_skip(AIRPORTS_FILE)

    # Detect special conditions
    windy_airports = weather.get_windy_airports(weather_data)
    lightning_airports = weather.get_lightning_airports(weather_data)
    snowy_airports = weather.get_snowy_airports(weather_data)
    missing_airports = weather.get_missing_airports(weather_data)

    if windy_airports:
        logger.info(f"Detected windy conditions at: {', '.join(windy_airports)}")
    if lightning_airports:
        logger.info(f"Detected lightning at: {', '.join(lightning_airports)}")
    if snowy_airports:
        logger.info(f"Detected snow at: {', '.join(snowy_airports)}")

    # Only print status information in CLI mode
    if __name__ == "__main__":
        logger.info("\nAirport Status:")
        logger.info(f"{'Airport':<10} {'Flight Cat':<12} {'Wind Speed':<12} {'Wind Gust':<12} {'Windy':<6} {'Lightning':<10} {'Snowy':<6} {'Brightness':<10}")
        logger.info("-" * 80)

        for index, airport_code in enumerate(airport_list):
            if airport_code != "SKIP":
                flt_cat, wind_speed, wind_gust, lightning = weather.get_airport_weather(airport_code, weather_data)
                is_windy = airport_code in windy_airports
                is_snowy = airport_code in snowy_airports
                logger.info(f"{airport_code:<10} {flt_cat:<12} {wind_speed:<2} kt {' '*8} {wind_gust:<2} kt {' '*8} {'Yes' if is_windy else 'No':<6} {'Yes' if lightning else 'No':<10} {'Yes' if is_snowy else 'No':<6} {get_current_brightness():<10}")

    # Update LEDs based on flt_cat
    try:
        for index, airport_code in enumerate(airport_list):
            if airport_code == "SKIP":
                pixels[index] = (0, 0, 0)
            else:
                flt_cat, wind_speed, wind_gust, lightning = weather.get_airport_weather(airport_code, weather_data)
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
                    logger.warning(f"Missing flight category data for {airport_code}")

        pixels.show()
    except Exception as e:
        logger.error(f"Error updating LEDs: {e}")


# Main loop
while True:
    try:
        # Check if the lights should be off based on current time
        lights_off = check_lights_off()

        if not lights_off:
            # Read the weather data and update the LEDs if lights are on
            weather_data = weather.read_weather_data()
            if weather_data is None:
                logger.error("Failed to read weather data")
                time.sleep(5)  # Wait before retry
                continue

            update_leds(weather_data)
            update_led_brightness(pixels)
            
            if LEGEND:
                update_legend(pixels)
                
            time.sleep(ANIMATION_PAUSE)

            # Run animations if enabled and conditions are met
            if WIND_ANIMATION and weather.get_windy_airports(weather_data):
                animate_windy_airports(weather.get_windy_airports(weather_data), weather_data)

            if LIGHTENING_ANIMATION and weather.get_lightning_airports(weather_data):
                animate_lightning_airports(weather.get_lightning_airports(weather_data), weather_data)

            if SNOWY_ANIMATION and weather.get_snowy_airports(weather_data):
                animate_snowy_airports(weather.get_snowy_airports(weather_data), weather_data)

        else:
            # If lights should be off, ensure LEDs are off
            pixels.fill((0, 0, 0))
            pixels.show()
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
        time.sleep(5)  # Wait before retrying
