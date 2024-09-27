import json
import time
import signal
import sys
import board
import neopixel
from config import *
import weather


# Initialize NeoPixel object using full module reference
#pixels = neopixel.NeoPixel(getattr(board, PIXEL_PIN), NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False)
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness = LED_BRIGHTNESS_DIM if (ACTIVATE_DAYTIME_DIMMING and bright == False) else LED_BRIGHTNESS, pixel_order = LED_ORDER, auto_write = False)

def cleanup(signal, frame):
    """Turn off all LEDs and exit."""
    pixels.fill((0, 0, 0))  # Turn off all LEDs
    pixels.show()
    sys.exit(0)

# Attach the signal handler to SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, cleanup)

def read_weather_data():
    """Read and return the weather data from weather.json."""
    try:
        with open('weather.json', 'r') as json_file:
            return json.load(json_file)
    except Exception as e:
        print(f"Failed to read weather.json: {e}")
        return {}

def get_airport_weather(airport_code, weather_data):
    """Retrieve and format weather data for a given airport."""
    airport_weather = weather_data.get(airport_code, {})
    flt_cat = airport_weather.get('flt_cat', 'MISSING')
    wind_speed = airport_weather.get('wind_speed', 0)  # Default to 0 if missing
    wind_gust = airport_weather.get('wind_gust', 0)    # Default to 0 if missing
    return flt_cat, wind_speed, wind_gust
    
def get_flt_cat_color(flt_cat):
    """Return the color corresponding to the flight category."""
    if flt_cat == 'VFR':
        return VFR_COLOR
    elif flt_cat == 'MVFR':
        return MVFR_COLOR
    elif flt_cat == 'IFR':
        return IFR_COLOR
    elif flt_cat == 'LIFR':
        return LIFR_COLOR
    else:
        return MISSING_COLOR

def get_windy_airports(weather_data):
    """Detect and return a dictionary of windy airports with their corresponding colors."""
    windy_airports = {}
    for airport_code, weather_info in weather_data.items():
        wind_speed = weather_info.get('wind_speed', 0)
        wind_gust = weather_info.get('wind_gust', 0)
        flt_cat = weather_info.get('flt_cat', 'MISSING')

        # Check if wind speed or wind gust exceeds the threshold
        if wind_speed > WIND_THRESHOLD or wind_gust > WIND_THRESHOLD:
            # Get the color based on flight category
            flt_cat_color = get_flt_cat_color(flt_cat)
            
            # Add airport and color to windy_airports dictionary
            windy_airports[airport_code] = flt_cat_color

    return windy_airports

def update_leds():
    """Update LEDs based on flt_cat from weather data."""
    weather_data = read_weather_data()

    # Get list of airports, including "SKIP" entries
    airport_list = weather.get_airports_with_skip(AIRPORTS_FILE)

    # Detect windy airports
    windy_airports = get_windy_airports(weather_data)

    # Print header
    print(f"{'Airport':<10} {'Flight Cat':<12} {'Wind Speed':<12} {'Wind Gust':<12} {'Windy':<6}")
    print("-" * 60)  # Separator line for better readability

    # Update LEDs based on flt_cat and print details
    for index, airport_code in enumerate(airport_list):
        if airport_code == "SKIP":
            pixels[index] = (0, 0, 0)  # Turn off LED if airport is SKIP
        else:
            # Get flight category and wind data for the airport
            flt_cat, wind_speed, wind_gust = get_airport_weather(airport_code, weather_data)
            
            # Check if the airport is in the windy_airports dictionary
            is_windy = "Yes" if airport_code in windy_airports else "No"

            # Print each airport, flight category, wind speed, wind gust, and whether it is windy
            print(f"{airport_code:<10} {flt_cat:<12} {str(wind_speed) + ' kt':<12} {str(wind_gust) + ' kt':<12} {is_windy:<6}")

            # Update LED colors based on flt_cat
            if flt_cat == 'VFR':
                pixels[index] = VFR_COLOR
            elif flt_cat == 'MVFR':
                pixels[index] = MVFR_COLOR
            elif flt_cat == 'IFR':
                pixels[index] = IFR_COLOR
            elif flt_cat == 'LIFR':
                pixels[index] = LIFR_COLOR
            else:
                pixels[index] = MISSING_COLOR

    pixels.show()







# Main loop
while True:
    update_leds()
    time.sleep(60)  # Update every 60 seconds
