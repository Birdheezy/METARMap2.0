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
import os

# Configure logging with more detailed format for CLI mode
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Let journald handle timestamp in service mode
)

logger = logging.getLogger(__name__)

# Global variables for WiFi checking
last_wifi_check_time = 0
last_wifi_status = False

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

def set_pixel_color(index, rgb_color):
    """Set the pixel color at the given index.
    rgb_color is in RGB order, the NeoPixel library handles the conversion to LED order."""
    pixels[index] = rgb_color

try:
    pixel_pin = f"D{PIXEL_PIN}"  # Create "D18"
    pixels = neopixel.NeoPixel(
        getattr(board, pixel_pin),
        NUM_PIXELS,
        brightness=BRIGHTNESS,
        auto_write=False,
        pixel_order=LED_COLOR_ORDER
    )
    logger.info(f"LED strip initialized on pin D{PIXEL_PIN} with {LED_COLOR_ORDER} order")
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
                for i in range(NUM_PIXELS):
                    set_pixel_color(i, (0, 0, 0))
                pixels.show()
                return True

        # Case 2: LIGHTS_OFF_TIME is earlier or equal to LIGHTS_ON_TIME
        elif LIGHTS_OFF_TIME <= current_time < LIGHTS_ON_TIME:
            for i in range(NUM_PIXELS):
                set_pixel_color(i, (0, 0, 0))
            pixels.show()
            return True

    return False

def calculate_dimmed_color(base_color, dim_brightness):
    """Calculate the dimmed color by applying the brightness factor."""
    return tuple(int(c * dim_brightness) for c in base_color)

def get_available_leds():
    """Calculate the number of LEDs available for airports (excluding legend LEDs)."""
    if LEGEND:
        try:
            legend_vfr = LEGEND_VFR
        except NameError:
            legend_vfr = True
        try:
            legend_mvfr = LEGEND_MVFR
        except NameError:
            legend_mvfr = True
        try:
            legend_ifr = LEGEND_IFR
        except NameError:
            legend_ifr = True
        try:
            legend_lifr = LEGEND_LIFR
        except NameError:
            legend_lifr = True
        try:
            legend_snowy = LEGEND_SNOWY
        except NameError:
            legend_snowy = True
        try:
            legend_lightning = LEGEND_LIGHTNING
        except NameError:
            legend_lightning = True
        try:
            legend_windy = LEGEND_WINDY
        except NameError:
            legend_windy = True
        try:
            legend_missing = LEGEND_MISSING
        except NameError:
            legend_missing = True
        
        # Count enabled legend items
        enabled_legend_count = sum([legend_vfr, legend_mvfr, legend_ifr, legend_lifr, 
                                   legend_snowy, legend_lightning, legend_windy, legend_missing])
        return NUM_PIXELS - enabled_legend_count
    else:
        return NUM_PIXELS

def update_legend(pixels):
    """Update the legend LEDs at the end of the strand if LEGEND is enabled."""
    if not LEGEND:
        return  # Do nothing if the legend is disabled

    # Get legend visibility settings with fallbacks
    try:
        legend_vfr = LEGEND_VFR
    except NameError:
        legend_vfr = True
    try:
        legend_mvfr = LEGEND_MVFR
    except NameError:
        legend_mvfr = True
    try:
        legend_ifr = LEGEND_IFR
    except NameError:
        legend_ifr = True
    try:
        legend_lifr = LEGEND_LIFR
    except NameError:
        legend_lifr = True
    try:
        legend_snowy = LEGEND_SNOWY
    except NameError:
        legend_snowy = True
    try:
        legend_lightning = LEGEND_LIGHTNING
    except NameError:
        legend_lightning = True
    try:
        legend_windy = LEGEND_WINDY
    except NameError:
        legend_windy = True
    try:
        legend_missing = LEGEND_MISSING
    except NameError:
        legend_missing = True

    # Define legend items with their colors and visibility settings in fixed order
    legend_items = [
        ('VFR', VFR_COLOR, legend_vfr),
        ('MVFR', MVFR_COLOR, legend_mvfr),
        ('IFR', IFR_COLOR, legend_ifr),
        ('LIFR', LIFR_COLOR, legend_lifr),
        ('SNOWY', SNOWY_COLOR, legend_snowy),
        ('LIGHTNING', LIGHTENING_COLOR, legend_lightning),
        ('WINDY', calculate_dimmed_color(VFR_COLOR, DIM_BRIGHTNESS), legend_windy),
        ('MISSING', MISSING_COLOR, legend_missing)
    ]

    # Work from the end backwards - last LED is first legend item
    # Only use as many LEDs as there are enabled legend items
    enabled_items = [(name, color) for name, color, enabled in legend_items if enabled]
    
    for i, (name, color) in enumerate(enabled_items):
        led_index = NUM_PIXELS - 1 - i  # Start from last LED and work backwards
        if led_index >= 0:  # Ensure we don't go out of bounds
            set_pixel_color(led_index, color)

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
                set_pixel_color(index, scaled_lightning_color)
        pixels.show()
        time.sleep(0.1)  # Short delay for rapid flash

        for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
            if airport_code in lightning_airports:
                # Revert back to flt_cat color
                flt_cat, _, _, _ = weather.get_airport_weather(airport_code, weather_data)
                if flt_cat == 'VFR':
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in VFR_COLOR))
                elif flt_cat == 'MVFR':
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in MVFR_COLOR))
                elif flt_cat == 'IFR':
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in IFR_COLOR))
                elif flt_cat == 'LIFR':
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in LIFR_COLOR))
                else:
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in MISSING_COLOR))
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
                set_pixel_color(index, pixel_color)
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
                set_pixel_color(index, pixel_color)
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
                set_pixel_color(index, snowy_color)
        pixels.show()
        time.sleep(SNOW_BLINK_PAUSE)  # Use SNOW_BLINK_PAUSE for twinkle on duration

        for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
            if airport_code in snowy_airports:
                # Turn off LED to create a twinkling effect
                set_pixel_color(index, (0, 0, 0))
        pixels.show()
        time.sleep(SNOW_BLINK_PAUSE)  # Use SNOW_BLINK_PAUSE for twinkle off duration

    # Revert back to the original flight category colors after animation
    for index, airport_code in enumerate(weather.get_airports_with_skip(AIRPORTS_FILE)):
        if airport_code in snowy_airports:
            flt_cat, _, _, _ = weather.get_airport_weather(airport_code, weather_data)
            set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in weather.get_flt_cat_color(flt_cat)))
    pixels.show()


#from config import BRIGHTNESS  # Import BRIGHTNESS from config.py

def is_weather_stale():
    try:
        weather_file_time = os.path.getmtime('weather.json')
        current_time = time.time()
        time_since_update = current_time - weather_file_time
        stale_threshold = WEATHER_UPDATE_INTERVAL * 2
        is_stale = time_since_update > stale_threshold

        # Add debug logging
        logger.info(f"Weather staleness check: Time since update: {time_since_update:.1f}s, Threshold: {stale_threshold:.1f}s, Is stale: {is_stale}")

        return is_stale
    except Exception as e:
        logger.error(f"Error checking weather staleness: {e}")
        return True  # If we can't check the file, assume data is stale

def is_wifi_connected():
    """Check if connected to an external WiFi network by verifying both connection state and IP address."""
    try:
        # First check if we have a valid IP address that's not localhost/link-local
        ip_check = subprocess.run(
            ['ip', 'addr', 'show', 'wlan0'],
            capture_output=True, text=True, check=True
        )

        # Look for an inet (IPv4) address that's not a link-local address
        has_valid_ip = False
        for line in ip_check.stdout.splitlines():
            if 'inet ' in line and not '169.254.' in line:
                has_valid_ip = True
                break

        if not has_valid_ip:
            return False

        # Then verify we have an actual connection
        connection_check = subprocess.run(
            ['iwconfig', 'wlan0'],
            capture_output=True, text=True, check=True
        )

        # Check for "ESSID" and "Access Point" entries
        has_connection = False
        for line in connection_check.stdout.splitlines():
            if 'ESSID:' in line and 'ESSID:off/any' not in line:
                has_connection = True
            if 'Access Point: ' in line and 'Not-Associated' not in line:
                has_connection = True

        return has_connection

    except Exception as e:
        logger.error(f"Error checking WiFi connection: {e}")
        return False  # If we can't check, assume disconnected

def check_wifi_status():
    """Check WiFi status only every WIFI_CHECK_INTERVAL seconds."""
    global last_wifi_check_time, last_wifi_status
    current_time = time.time()

    # Only check if enough time has passed since last check
    if current_time - last_wifi_check_time >= WIFI_CHECK_INTERVAL:  # Now using from config.py
        last_wifi_status = is_wifi_connected()
        last_wifi_check_time = current_time
        logger.info(f"WiFi check performed: {'Connected' if last_wifi_status else 'Disconnected'}")

    return last_wifi_status

def update_leds(weather_data):
    """Update LEDs based on flt_cat from weather data."""
    logger.info("update_leds called")

    if check_lights_off():
        logger.info("Lights are off, returning early")
        return

    # Get list of airports, including "SKIP" entries first
    airport_list = weather.get_airports_with_skip(AIRPORTS_FILE)
    logger.info(f"Airport list: {airport_list}")

    # Determine how many LEDs are available for airports
    available_leds = get_available_leds()
    
    logger.info(f"Available LEDs for airports: {available_leds}")

    # Check for WiFi disconnection if the feature is enabled
    if WIFI_INDICATION and not check_wifi_status():
        logger.info("WiFi disconnected, showing warning color")
        for index, airport_code in enumerate(airport_list):
            if index >= available_leds:  # Skip if beyond available LEDs
                break
            if airport_code == "SKIP":
                set_pixel_color(index, (0, 0, 0))  # Keep SKIP LEDs off
            else:
                set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in WIFI_DISCONNECTED_COLOR))
        pixels.show()
        logger.warning("WiFi disconnected - displaying warning color")
        return

    # Check for stale weather data if the feature is enabled
    if STALE_INDICATION and is_weather_stale():
        logger.info("Weather data is stale, showing warning color")
        for index, airport_code in enumerate(airport_list):
            if index >= available_leds:  # Skip if beyond available LEDs
                break
            if airport_code == "SKIP":
                set_pixel_color(index, (0, 0, 0))  # Keep SKIP LEDs off
            else:
                set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in STALE_DATA_COLOR))
        pixels.show()
        logger.warning("Weather data is stale - displaying warning color")
        return

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
            if index >= available_leds:  # Skip if beyond available LEDs
                break
            if airport_code != "SKIP":
                flt_cat, wind_speed, wind_gust, lightning = weather.get_airport_weather(airport_code, weather_data)
                is_windy = airport_code in windy_airports
                is_snowy = airport_code in snowy_airports
                # Convert all values to strings to handle None values gracefully
                flt_cat_str = str(flt_cat) if flt_cat is not None else "None"
                wind_speed_str = str(wind_speed) if wind_speed is not None else "None"
                wind_gust_str = str(wind_gust) if wind_gust is not None else "None"
                logger.info(f"{airport_code:<10} {flt_cat_str:<12} {wind_speed_str:<2} kt {' '*8} {wind_gust_str:<2} kt {' '*8} {'Yes' if is_windy else 'No':<6} {'Yes' if lightning else 'No':<10} {'Yes' if is_snowy else 'No':<6} {get_current_brightness():<10}")

    # Update LEDs based on flt_cat
    try:
#        logger.info("Updating LEDs based on flight categories")
        for index, airport_code in enumerate(airport_list):
            if index >= available_leds:  # Skip if beyond available LEDs
                break
            if airport_code == "SKIP":
                set_pixel_color(index, (0, 0, 0))
            else:
                flt_cat, wind_speed, wind_gust, lightning = weather.get_airport_weather(airport_code, weather_data)
#                logger.info(f"Airport {airport_code}: {flt_cat}")
                if flt_cat == 'VFR':
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in VFR_COLOR))
                elif flt_cat == 'MVFR':
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in MVFR_COLOR))
                elif flt_cat == 'IFR':
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in IFR_COLOR))
                elif flt_cat == 'LIFR':
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in LIFR_COLOR))
                else:
                    set_pixel_color(index, tuple(int(c * BRIGHTNESS) for c in MISSING_COLOR))
                    logger.warning(f"Missing flight category data for {airport_code}")

        pixels.show()
        logger.info("LEDs updated successfully")
    except Exception as e:
        logger.error(f"Error updating LEDs: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

def handle_kiosk_timeout():
    """Handle kiosk mode timeout by restoring normal operation."""
    logger.info("Kiosk mode timeout - restoring normal operation")
    if weather.restore_airports_file():
        logger.info("Successfully restored airports file from backup")
        # Force a weather update
        weather_data = weather.fetch_metar()
        if weather_data:
            parsed_data = weather.parse_weather(weather_data)
            with open('weather.json', 'w') as json_file:
                json.dump(parsed_data, json_file, indent=4)
            return True
    else:
        logger.error("Failed to restore normal operation")
        return False

def update_kiosk_airports(airport_codes):
    """Update airports for kiosk mode."""
    logger.info(f"Updating kiosk airports: {airport_codes}")
    if weather.update_airports_file(airport_codes):
        logger.info("Successfully updated airports file")
        # Force a weather update
        weather_data = weather.fetch_metar()
        if weather_data:
            parsed_data = weather.parse_weather(weather_data)
            with open('weather.json', 'w') as json_file:
                json.dump(parsed_data, json_file, indent=4)
            return True
    else:
        logger.error("Failed to update kiosk airports")
        return False

# Main loop
previous_lights_off = False  # Track previous state
logger.info("Starting main loop...")
logger.info(f"ENABLE_LIGHTS_OFF: {ENABLE_LIGHTS_OFF}")
logger.info(f"LIGHTS_ON_TIME: {LIGHTS_ON_TIME}")
logger.info(f"LIGHTS_OFF_TIME: {LIGHTS_OFF_TIME}")
logger.info(f"Current time: {datetime.datetime.now().time()}")

while True:
    try:
        # Check if the lights should be off based on current time
        lights_off = check_lights_off()

        # Only log when state changes from on to off
        if lights_off and not previous_lights_off:
            logger.info("Lights turned off - outside operational hours")
        elif not lights_off and previous_lights_off:
            logger.info("Lights turned on - within operational hours")

        previous_lights_off = lights_off  # Update previous state

        if not lights_off:
            # Read the weather data and update the LEDs if lights are on
            weather_data = weather.read_weather_data()
            if weather_data is None:
                logger.error("Failed to read weather data")
                time.sleep(5)  # Wait before retry
                continue

            # Update LEDs - this will handle WiFi and stale data states
            update_leds(weather_data)
            update_led_brightness(pixels)
            pixels.show()  # Ensure LEDs are updated
            if LEGEND:
                update_legend(pixels)

            time.sleep(ANIMATION_PAUSE)

            # Only run animations if we have good data and at least one airport needs animation
            if not (STALE_INDICATION and is_weather_stale()) and not (WIFI_INDICATION and not check_wifi_status()):
                windy = weather.get_windy_airports(weather_data)
                lightning = weather.get_lightning_airports(weather_data)
                snowy = weather.get_snowy_airports(weather_data)

                for animation_name in ANIMATION_ORDER:
                    if animation_name == "WINDY" and WIND_ANIMATION and windy:
                        animate_windy_airports(windy, weather_data)
                    elif animation_name == "LIGHTNING" and LIGHTENING_ANIMATION and lightning:
                        animate_lightning_airports(lightning, weather_data)
                    elif animation_name == "SNOWY" and SNOWY_ANIMATION and snowy:
                        animate_snowy_airports(snowy, weather_data)
        else:
            # If lights should be off, ensure LEDs are off and sleep
            pixels.fill((0, 0, 0))
            pixels.show()
            time.sleep(10)  # Sleep longer when lights are off to reduce CPU usage
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        time.sleep(5)  # Wait before retrying
