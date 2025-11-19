from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import subprocess
import os
from config import *
import datetime
import config
import shutil
import re
import time
import threading
import importlib
import logging
import json
import signal
import sys
import schedule
import weather
import functools
import socket
from scheduler import weather_update_lock, update_weather as scheduler_update_weather, calculate_sun_times
from led_test import test_leds, turn_off_leds, update_brightness

# Import the update manager
from update_manager import (
    check_for_updates, 
    perform_update, 
    get_config_validation_status,
    validate_config_file,
    parse_config_file, # Added for robust config handling
    write_config_file  # Added for robust config handling
)
import ast
from typing import Dict

def parse_config_file(config_path: str) -> Dict:
    """Parse a config.py file and extract all variable assignments."""
    try:
        with open(config_path, 'r') as f:
            content = f.read()

        # Parse the Python code
        tree = ast.parse(content)

        config_dict = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Convert the value to a string representation
                        try:
                            # For simple values, we can evaluate them
                            if isinstance(node.value, (ast.Constant, ast.Num, ast.Str)):
                                config_dict[target.id] = ast.literal_eval(node.value)
                            elif isinstance(node.value, ast.Tuple):
                                config_dict[target.id] = ast.literal_eval(node.value)
                            elif isinstance(node.value, ast.List):
                                config_dict[target.id] = ast.literal_eval(node.value)
                            elif isinstance(node.value, ast.Dict):
                                config_dict[target.id] = ast.literal_eval(node.value)
                            elif isinstance(node.value, ast.NameConstant):  # True, False, None
                                config_dict[target.id] = ast.literal_eval(node.value)
                            else:
                                # For complex expressions, store as string
                                config_dict[target.id] = ast.unparse(node.value)
                        except:
                            # If we can't evaluate, store as string
                            config_dict[target.id] = ast.unparse(node.value)

        # Validate that we got some config
        if not config_dict:
            raise Exception("No configuration variables found in file")

        return config_dict

    except Exception as e:
        print(f"Error parsing config file: {e}")
        raise Exception(f"Failed to parse config file: {str(e)}")

def write_config_file(config_dict: Dict, config_path: str):
    """Write a config dictionary back to a config.py file."""
    try:
        # Read the original file to preserve imports and comments
        with open(config_path, 'r') as f:
            original_content = f.read()

        # Parse to get the structure
        tree = ast.parse(original_content)

        # Create new content
        new_lines = []

        # Add imports first
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                try:
                    new_lines.append(ast.unparse(node))
                except AttributeError:
                    # Fallback for older Python versions
                    new_lines.append(ast.dump(node))

        if new_lines:
            new_lines.append('')  # Add blank line after imports

        # Add variables in the order they appear in the new config
        for key, value in config_dict.items():
            # Heuristic to differentiate between a code snippet (like 'datetime.time(...)')
            # and a literal string value (like 'airports.txt').
            if isinstance(value, str) and '(' in value and ')' in value:
                # Assume it's a complex expression that should not be quoted.
                new_lines.append(f"{key} = {value}")
            else:
                # It's a simple value (int, bool, tuple, or a literal string).
                # Use repr() to get the correct Python representation (e.g., adds quotes to strings).
                new_lines.append(f"{key} = {repr(value)}")

        # Write the new config file
        with open(config_path, 'w') as f:
            f.write('\n'.join(new_lines))

    except Exception as e:
        print(f"Error writing config file: {e}")
        # Fallback: write simple format
        with open(config_path, 'w') as f:
            f.write('# METARMap Configuration\n\n')
            for key, value in config_dict.items():
                f.write(f'{key} = {repr(value)}\n')

def after_this_response(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return
    return wrapper

app = Flask(__name__, 
           template_folder='/home/pi/templates',
           static_folder='static')
app.secret_key = os.urandom(24)


def reload_config():
    importlib.reload(config)

    # Update global variables dynamically
    for key in dir(config):
        if key.isupper():  # Only update uppercase variables (configuration constants)
            globals()[key] = getattr(config, key)

    # Update global values from the loaded config
    BRIGHTNESS = globals().get('BRIGHTNESS', None)
    DIM_BRIGHTNESS = globals().get('DIM_BRIGHTNESS', None)
    BRIGHT_TIME_START = globals().get('BRIGHT_TIME_START', None)
    DIM_TIME_START = globals().get('DIM_TIME_START', None)
    WIND_THRESHOLD = globals().get('WIND_THRESHOLD', None)
    WIND_FADE_TIME = globals().get('WIND_FADE_TIME', None)
    WIND_PAUSE = globals().get('WIND_PAUSE', None)
    ANIMATION_PAUSE = globals().get('ANIMATION_PAUSE', None)
    NUM_STEPS = globals().get('NUM_STEPS', None)
    SNOW_BLINK_COUNT = globals().get('SNOW_BLINK_COUNT', None)
    SNOW_BLINK_PAUSE = globals().get('SNOW_BLINK_PAUSE', None)
    SNOWY_ANIMATION_DURATION = globals().get('SNOWY_ANIMATION_DURATION', None)
    SNOW_CYCLE_MIN_DURATION = globals().get('SNOW_CYCLE_MIN_DURATION', None)
    SNOW_CYCLE_MAX_DURATION = globals().get('SNOW_CYCLE_MAX_DURATION', None)
    SNOW_START_OFFSET_MAX = globals().get('SNOW_START_OFFSET_MAX', None)
    SNOW_MIN_BRIGHTNESS = globals().get('SNOW_MIN_BRIGHTNESS', None)
    WIND_ANIMATION = globals().get('WIND_ANIMATION', None)
    LIGHTENING_ANIMATION = globals().get('LIGHTENING_ANIMATION', None)
    SNOWY_ANIMATION = globals().get('SNOWY_ANIMATION', None)
    VFR_COLOR = globals().get('VFR_COLOR', None)
    MVFR_COLOR = globals().get('MVFR_COLOR', None)
    IFR_COLOR = globals().get('IFR_COLOR', None)
    LIFR_COLOR = globals().get('LIFR_COLOR', None)
    MISSING_COLOR = globals().get('MISSING_COLOR', None)
    LIGHTENING_COLOR = globals().get('LIGHTENING_COLOR', None)
    DAYTIME_DIMMING = globals().get('DAYTIME_DIMMING', None)
    DAYTIME_DIM_BRIGHTNESS = globals().get('DAYTIME_DIM_BRIGHTNESS', None)
    LIGHTS_OFF_TIME = globals().get('LIGHTS_OFF_TIME', None)
    LIGHTS_ON_TIME = globals().get('LIGHTS_ON_TIME', None)
    ENABLE_LIGHTS_OFF = globals().get('ENABLE_LIGHTS_OFF', None)
    NUM_PIXELS = globals().get('NUM_PIXELS', None)
    LEGEND = globals().get('LEGEND', None)
    PIXEL_PIN = globals().get('PIXEL_PIN', None)
    WEATHER_UPDATE_INTERVAL = globals().get('WEATHER_UPDATE_INTERVAL', None)
    UPDATE_WEATHER = globals().get('UPDATE_WEATHER', None)
    STALE_INDICATION = globals().get('STALE_INDICATION', None)
    STALE_DATA_COLOR = globals().get('STALE_DATA_COLOR', None)
    WIFI_DISCONNECTED_COLOR = globals().get('WIFI_DISCONNECTED_COLOR', None)
    WIFI_INDICATION = globals().get('WIFI_INDICATION', True)
    LED_COLOR_ORDER = globals().get('LED_COLOR_ORDER', None)


@app.route('/leds/on', methods=['POST'])
def turn_on_leds():
    subprocess.run(['sudo', 'systemctl', 'start', 'metar.service'])
    return jsonify({"status": "LEDs turned on"}), 200

@app.route('/leds/off', methods=['POST'])
def turn_off_leds():
    subprocess.run(['sudo', 'systemctl', 'stop', 'metar.service'])
    subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'])
    return jsonify({"status": "LEDs turned off"}), 200

@app.route('/update-weather')
def update_weather_page():
    try:
        # Use the scheduler's update_weather function
        scheduler_update_weather()
        flash('Weather Has Been Updated!', 'success')
    except Exception as e:
        flash(f'Weather Update Has Failed... {str(e)}', 'danger')
    return redirect(url_for('edit_settings'))

@app.route('/update-weather', methods=['POST'])
def refresh_weather():
    """Endpoint to manually trigger a weather update."""
    try:
        scheduler_update_weather(force=True)  # Force update regardless of service state
        return jsonify({'status': 'success', 'message': 'Weather update requested'})
    except Exception as e:
        app.logger.error(f"Error requesting weather update: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/leds/status', methods=['GET'])
def get_led_status():
    try:
        # Check if the metar.service is active
        result = subprocess.run(
            ['systemctl', 'is-active', 'metar.service'],
            capture_output=True, text=True
        )
        # Determine LED status based on service status
        led_status = "on" if result.stdout.strip() == "active" else "off"
        return jsonify({"status": led_status}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "off", "error": str(e)}), 500


@app.route('/', methods=['GET', 'POST'])
def edit_settings():
    if request.method == 'POST':
        try:
            # Parse the current config.py to get a dictionary
            current_config = parse_config_file('/home/pi/config.py')

            # Extract and validate form data, updating the dictionary
            try:
                current_config["PIXEL_PIN"] = int(request.form.get('pixel_pin', current_config.get("PIXEL_PIN")))
                current_config["LEGEND"] = 'legend' in request.form
                current_config["ENABLE_LIGHTS_OFF"] = 'enable_lights_off' in request.form
                current_config["DAYTIME_DIMMING"] = 'daytime_dimming' in request.form
                current_config["WIND_ANIMATION"] = 'wind_animation' in request.form
                current_config["LIGHTENING_ANIMATION"] = 'lightening_animation' in request.form
                current_config["SNOWY_ANIMATION"] = 'snowy_animation' in request.form
                current_config["ENABLE_HTTPS"] = 'enable_https' in request.form
                current_config["UPDATE_WEATHER"] = 'update_weather' in request.form
                current_config["STALE_INDICATION"] = 'stale_indication' in request.form
                
                # Legend item visibility settings
                current_config["LEGEND_VFR"] = 'legend_vfr' in request.form
                current_config["LEGEND_MVFR"] = 'legend_mvfr' in request.form
                current_config["LEGEND_IFR"] = 'legend_ifr' in request.form
                current_config["LEGEND_LIFR"] = 'legend_lifr' in request.form
                current_config["LEGEND_SNOWY"] = 'legend_snowy' in request.form
                current_config["LEGEND_LIGHTNING"] = 'legend_lightning' in request.form
                current_config["LEGEND_WINDY"] = 'legend_windy' in request.form
                current_config["LEGEND_MISSING"] = 'legend_missing' in request.form

                # Float or Integer Settings
                current_config["BRIGHTNESS"] = float(request.form.get('brightness', current_config.get("BRIGHTNESS")))
                current_config["DIM_BRIGHTNESS"] = float(request.form.get('dim_brightness', current_config.get("DIM_BRIGHTNESS")))
                current_config["DAYTIME_DIM_BRIGHTNESS"] = float(request.form.get('daytime_dim_brightness', current_config.get("DAYTIME_DIM_BRIGHTNESS")))
                current_config["WIND_THRESHOLD"] = int(request.form.get('wind_threshold', current_config.get("WIND_THRESHOLD")))
                current_config["WIND_FADE_TIME"] = float(request.form.get('wind_fade_time', current_config.get("WIND_FADE_TIME")))
                current_config["WIND_PAUSE"] = float(request.form.get('wind_pause', current_config.get("WIND_PAUSE")))
                current_config["ANIMATION_PAUSE"] = int(request.form.get('animation_pause', current_config.get("ANIMATION_PAUSE")))
                current_config["LIGHTNING_FLASH_COUNT"] = int(request.form.get('lightning_flash_count', current_config.get("LIGHTNING_FLASH_COUNT")))
                current_config["SNOW_BLINK_COUNT"] = int(request.form.get('snow_blink_count', current_config.get("SNOW_BLINK_COUNT")))
                current_config["SNOW_BLINK_PAUSE"] = float(request.form.get('snow_blink_pause', current_config.get("SNOW_BLINK_PAUSE")))
                current_config["SNOWY_ANIMATION_DURATION"] = float(request.form.get('snowy_animation_duration', current_config.get("SNOWY_ANIMATION_DURATION")))
                current_config["SNOW_CYCLE_MIN_DURATION"] = float(request.form.get('snow_cycle_min_duration', current_config.get("SNOW_CYCLE_MIN_DURATION")))
                current_config["SNOW_CYCLE_MAX_DURATION"] = float(request.form.get('snow_cycle_max_duration', current_config.get("SNOW_CYCLE_MAX_DURATION")))
                current_config["SNOW_START_OFFSET_MAX"] = float(request.form.get('snow_start_offset_max', current_config.get("SNOW_START_OFFSET_MAX")))
                current_config["SNOW_MIN_BRIGHTNESS"] = float(request.form.get('snow_min_brightness', current_config.get("SNOW_MIN_BRIGHTNESS")))
                current_config["NUM_STEPS"] = int(request.form.get('num_steps', current_config.get("NUM_STEPS")))
                current_config["NUM_PIXELS"] = int(request.form.get('num_pixels', current_config.get("NUM_PIXELS")))
                current_config["LED_COLOR_ORDER"] = request.form.get('led_color_order', current_config.get("LED_COLOR_ORDER"))

                # Time Settings
                current_config["BRIGHT_TIME_START"] = f"datetime.time({request.form.get('bright_time_start_hour')}, {request.form.get('bright_time_start_minute')})"
                current_config["DIM_TIME_START"] = f"datetime.time({request.form.get('dim_time_start_hour')}, {request.form.get('dim_time_start_minute')})"
                current_config["LIGHTS_OFF_TIME"] = f"datetime.time({request.form.get('lights_off_time_hour')}, {request.form.get('lights_off_time_minute')})"
                current_config["LIGHTS_ON_TIME"] = f"datetime.time({request.form.get('lights_on_time_hour')}, {request.form.get('lights_on_time_minute')})"

                # Weather update interval
                minutes = float(request.form.get('weather_update_interval', 5))
                current_config["WEATHER_UPDATE_INTERVAL"] = int(minutes * 60)

            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid input for a setting: {e}")

            # Color fields
            color_fields = {
                'vfr_color': 'VFR_COLOR', 'mvfr_color': 'MVFR_COLOR', 'ifr_color': 'IFR_COLOR',
                'lifr_color': 'LIFR_COLOR', 'missing_color': 'MISSING_COLOR', 'lightening_color': 'LIGHTENING_COLOR',
                'snowy_color': 'SNOWY_COLOR', 'stale_data_color': 'STALE_DATA_COLOR', 'wifi_disconnected_color': 'WIFI_DISCONNECTED_COLOR'
            }
            for form_key, config_key in color_fields.items():
                if form_key in request.form:
                    rgb_hex = request.form[form_key].lstrip('#')
                    current_config[config_key] = tuple(int(rgb_hex[i:i+2], 16) for i in (0, 2, 4))
            
            # Animation sequence
            if 'animation_sequence' in request.form:
                sequence_list = request.form['animation_sequence'].split(',')
                current_config["ANIMATION_ORDER"] = [item.strip() for item in sequence_list]

            # Sunrise/sunset settings
            current_config["USE_SUNRISE_SUNSET"] = 'use_sunrise_sunset' in request.form
            if 'selected_city' in request.form and request.form['selected_city']:
                selected_city = request.form['selected_city']
                current_config["SELECTED_CITY"] = selected_city
                if current_config["USE_SUNRISE_SUNSET"]:
                    try:
                        sunrise, sunset = calculate_sun_times(selected_city)
                        if sunrise and sunset:
                            current_config["BRIGHT_TIME_START"] = f"datetime.time({sunrise.hour}, {sunrise.minute})"
                            current_config["DIM_TIME_START"] = f"datetime.time({sunset.hour}, {sunset.minute})"
                    except Exception as e:
                        flash(f'Error calculating sun times: {str(e)}', 'warning')

            # Write the updated dictionary back to config.py
            write_config_file(current_config, '/home/pi/config.py')

            # Reload the configuration to reflect the changes
            reload_config()

            # Update airports.txt
            if "airports" in request.form:
                with open('/home/pi/airports.txt', 'w') as f:
                    f.write(request.form["airports"])

            flash('Configuration updated successfully!', 'success')

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

        return redirect(url_for('edit_settings'))

    # After reloading, get the updated values for display
    bright_time_start_hour = config.BRIGHT_TIME_START.hour
    bright_time_start_minute = config.BRIGHT_TIME_START.minute
    dim_time_start_hour = config.DIM_TIME_START.hour
    dim_time_start_minute = config.DIM_TIME_START.minute
    lights_off_time_hour = config.LIGHTS_OFF_TIME.hour
    lights_off_time_minute = config.LIGHTS_OFF_TIME.minute
    lights_on_time_hour = config.LIGHTS_ON_TIME.hour
    lights_on_time_minute = config.LIGHTS_ON_TIME.minute

    # Convert LED colors to RGB hex for display
    def led_to_hex(color_tuple):
        """Convert a color tuple to RGB hex format for display.
        If LED_COLOR_ORDER is 'GRB', colors in config.py are stored with R and G swapped,
        so we need to swap them back for the web interface.
        If LED_COLOR_ORDER is 'RGB', colors are already in RGB order."""
        if config.LED_COLOR_ORDER == 'GRB':
            g, r, b = color_tuple  # Unpack as GRB
            return '#{:02x}{:02x}{:02x}'.format(r, g, b)  # Format as RGB
        else:  # RGB order
            r, g, b = color_tuple  # Already in RGB order
            return '#{:02x}{:02x}{:02x}'.format(r, g, b)

    # Convert all colors to RGB hex format for display
    vfr_color = led_to_hex(config.VFR_COLOR)
    mvfr_color = led_to_hex(config.MVFR_COLOR)
    ifr_color = led_to_hex(config.IFR_COLOR)
    lifr_color = led_to_hex(config.LIFR_COLOR)
    missing_color = led_to_hex(config.MISSING_COLOR)
    lightening_color = led_to_hex(config.LIGHTENING_COLOR)
    snowy_color = led_to_hex(config.SNOWY_COLOR)
    stale_data_color = led_to_hex(config.STALE_DATA_COLOR)
    wifi_disconnected_color = led_to_hex(config.WIFI_DISCONNECTED_COLOR)

    # Get the last modified date of weather.json
    weather_file_path = '/home/pi/weather.json'  # Adjust this path if necessary
    try:
        last_modified_timestamp = os.path.getmtime(weather_file_path)
        weather_last_modified = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%m-%d-%Y %H:%M:%S')
    except FileNotFoundError:
        weather_last_modified = "Weather data not available"

    # Calculate the weather update threshold in minutes
    weather_update_threshold = (config.WEATHER_UPDATE_INTERVAL / 60) * 2

    # Load the airport list from airports.txt
    with open('/home/pi/airports.txt', 'r') as f:
        airports = f.read()

    # Get the local IP address
    local_ip = get_local_ip()

    # Add dynamic styles for the map colors
    map_styles = {
        'vfr_color': vfr_color,
        'mvfr_color': mvfr_color,
        'ifr_color': ifr_color,
        'lifr_color': lifr_color,
        'missing_color': missing_color,
        'lightening_color': lightening_color,
        'snowy_color': snowy_color
    }

    # Render the template with the updated values, including weather_last_modified
    return render_template(
        'settings.html',
        bright_time_start_hour=bright_time_start_hour,
        bright_time_start_minute=bright_time_start_minute,
        dim_time_start_hour=dim_time_start_hour,
        dim_time_start_minute=dim_time_start_minute,
        lights_off_time_hour=lights_off_time_hour,
        lights_off_time_minute=lights_off_time_minute,
        lights_on_time_hour=lights_on_time_hour,
        lights_on_time_minute=lights_on_time_minute,
        airports=airports,
        weather_last_modified=weather_last_modified,
        config=globals(),
        local_ip=local_ip,
        vfr_color=vfr_color,
        mvfr_color=mvfr_color,
        ifr_color=ifr_color,
        lifr_color=lifr_color,
        missing_color=missing_color,
        lightening_color=lightening_color,
        snowy_color=snowy_color,
        stale_data_color=stale_data_color,
        enable_lights_off=config.ENABLE_LIGHTS_OFF,
        legend=config.LEGEND,
        num_pixels=config.NUM_PIXELS,
        num_steps=config.NUM_STEPS,
        brightness=config.BRIGHTNESS,
        dim_brightness=config.DIM_BRIGHTNESS,
        daytime_dim_brightness=config.DAYTIME_DIM_BRIGHTNESS,
        wind_threshold=config.WIND_THRESHOLD,
        wind_fade_time=config.WIND_FADE_TIME,
        wind_pause=config.WIND_PAUSE,
        animation_pause=config.ANIMATION_PAUSE,
        lightning_flash_count=config.LIGHTNING_FLASH_COUNT,
        snow_blink_count=config.SNOW_BLINK_COUNT,
        snow_blink_pause=config.SNOW_BLINK_PAUSE,
        snowy_animation_duration=getattr(config, 'SNOWY_ANIMATION_DURATION', 5.0),
        snow_cycle_min_duration=getattr(config, 'SNOW_CYCLE_MIN_DURATION', 2.0),
        snow_cycle_max_duration=getattr(config, 'SNOW_CYCLE_MAX_DURATION', 4.0),
        snow_start_offset_max=getattr(config, 'SNOW_START_OFFSET_MAX', 1.0),
        snow_min_brightness=getattr(config, 'SNOW_MIN_BRIGHTNESS', 0.05),
        wind_animation=config.WIND_ANIMATION,
        lightening_animation=config.LIGHTENING_ANIMATION,
        snowy_animation=config.SNOWY_ANIMATION,
        daytime_dimming=config.DAYTIME_DIMMING,
        enable_https=config.ENABLE_HTTPS,
        pixel_pin=config.PIXEL_PIN,
        weather_update_interval=config.WEATHER_UPDATE_INTERVAL,
        weather_update_threshold=weather_update_threshold,  # Pass the calculated value
        stale_indication=config.STALE_INDICATION,
        wifi_disconnected_color=wifi_disconnected_color,
        map_styles=map_styles,
        show_save_button=True,
        # Sunrise/sunset settings
        use_sunrise_sunset=getattr(config, 'USE_SUNRISE_SUNSET', False),
        selected_city=getattr(config, 'SELECTED_CITY', None),
        cities=getattr(config, 'CITIES', []),
        # Animation settings
        animation_order=getattr(config, 'ANIMATION_ORDER', ['WINDY', 'LIGHTNING', 'SNOWY'])
    )



# Route to restart the METAR service
@app.route('/restart_metar')
def restart_metar():
    try:
        # Restart the metar service
        subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)
        flash('METAR service restarted successfully!', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Error restarting METAR service: {str(e)}', 'danger')

    return redirect(url_for('edit_settings'))


@app.route('/restart_settings', methods=['GET'])
def restart_settings():
    try:
        threading.Thread(target=restart_service_thread).start()
        return jsonify({"message": "Settings service is restarting."}), 200
    except Exception as e:
        return jsonify({"error": f"Error restarting settings service: {str(e)}"}), 500


def restart_service_thread():
    """Perform the service restart in a separate thread."""
    try:
        print("Delaying restart to allow proxy to respond...")
        time.sleep(2)  # Optional delay to allow proxy to handle response
        subprocess.run(['sudo', 'systemctl', 'restart', 'settings.service'], check=True)
        print("Settings service restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error restarting settings service: {e}")

def restart_service():
    """Restart the settings service in a separate thread."""
    try:
        print("Restarting settings service...")
        subprocess.run(['sudo', 'systemctl', 'restart', 'settings.service'], check=True)
        print("Settings service restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error restarting settings service: {e}")

@app.route('/restarting', methods=['GET'])
def restarting():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Restarting...</title>
        <meta http-equiv="refresh" content="10; url=/" />
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin-top: 50px;
            }
        </style>
    </head>
    <body>
        <h1>Restarting Settings Service...</h1>
        <p>Please wait. You will be redirected shortly.</p>
    </body>
    </html>
    """

@app.route('/stop_and_blank')
def stop_and_blank():
    try:
        # Run the 'stopmetar' and 'blank' commands
        subprocess.run(['sudo', 'systemctl', 'stop', 'metar.service'], check=True)
        subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'], check=True)
        flash('METAR service stopped and LEDs blanked!', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Error stopping METAR service or blanking LEDs: {str(e)}', 'danger')

    return redirect(url_for('edit_settings'))

@app.route('/scan-networks', methods=['GET'])
def scan_networks():


    logging.basicConfig(level=logging.DEBUG)

    try:
        # Scan for WiFi networks using nmcli
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'SSID,SIGNAL', 'dev', 'wifi', 'list'],
            capture_output=True, text=True, check=True
        )
        logging.debug(f"nmcli output: {result.stdout}")

        # Parse networks, filtering out empty SSIDs and keeping the strongest signal for each SSID
        networks = {}
        for line in result.stdout.splitlines():
            parts = line.split(':')
            if len(parts) >= 2 and parts[0].strip():  # Ignore empty SSIDs
                ssid, signal = parts[0], parts[1]
                signal = int(signal)  # Convert signal strength to integer

                # Keep the entry with the highest signal strength
                if ssid not in networks or networks[ssid] < signal:
                    networks[ssid] = signal

        # Convert the dictionary to a sorted list of networks
        sorted_networks = sorted(
            [{'ssid': ssid, 'signal': str(signal)} for ssid, signal in networks.items()],
            key=lambda x: int(x['signal']), reverse=True
        )
        logging.debug(f"Parsed networks: {sorted_networks}")

        return {'networks': sorted_networks}

    except subprocess.CalledProcessError as e:
        logging.error(f"nmcli error: {e.stderr}")
        return {'error': f"Failed to scan networks: {e.stderr}"}, 500
    except Exception as e:
        logging.error(f"General error: {str(e)}")
        return {'error': str(e)}, 500


@app.route('/connect-to-network', methods=['POST'])
def connect_to_network():

    data = request.get_json()
    ssid = data.get('ssid')
    password = data.get('password')

    if not ssid:
        return jsonify({'success': False, 'error': 'SSID is required.'}), 400

    try:
        # Command to connect to the network
        if password:
            command = ['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password]
        else:
            command = ['nmcli', 'dev', 'wifi', 'connect', ssid]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': result.stderr.strip()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/service/status/<service_name>', methods=['GET'])
def get_service_status(service_name):
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', f'{service_name}.service'],
            capture_output=True, text=True
        )
        status = result.stdout.strip()
        is_running = status == "active"
        return jsonify({
            "status": "running" if is_running else "stopped",
            "message": f"Service is {status}"
        })
    except Exception as e:
        return jsonify({
            "status": "unknown",
            "message": str(e)
        }), 500

@app.route('/service/control/<service_name>/<action>', methods=['POST'])
def control_service(service_name, action):
    if action not in ['start', 'stop', 'restart']:
        return jsonify({"error": "Invalid action"}), 400

    try:
        if service_name == 'settings' and action == 'restart':
            # For settings service restart, send success response before restarting
            response = jsonify({
                "message": "Settings service restart initiated",
                "status": "restarting",
                "special_case": "settings_restart"
            })
            # Force the response to be sent immediately
            response.headers['Connection'] = 'close'

            # Schedule the restart to happen after response is sent
            def restart_after_response():
                time.sleep(1)  # Brief delay to ensure response is sent
                subprocess.run(['sudo', 'systemctl', 'restart', 'settings.service'], check=True)

            threading.Thread(target=restart_after_response).start()
            return response

        elif service_name == 'metar' and action == 'stop':
            # First stop the service
            subprocess.run(['sudo', 'systemctl', 'stop', 'metar.service'], check=True)
            # Then run blank.py to turn off the LEDs
            subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'], check=True)
        else:
            # Handle all other service control actions normally
            subprocess.run(['sudo', 'systemctl', action, f'{service_name}.service'], check=True)

        return jsonify({
            "message": f"Service {action} successful",
            "status": "running" if action in ['start', 'restart'] else "stopped"
        })
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to {action} service: {str(e)}"}), 500

@app.route('/service/logs/<service_name>', methods=['GET'])
def get_service_logs(service_name):
    try:
        # Get logs for any service with consistent formatting, limited to last 200 lines
        result = subprocess.run(
            ['sudo', 'journalctl', '-u', f'{service_name}.service', '-n', '200',
             '-o', 'short-precise', '--no-pager', '--no-hostname'],
            capture_output=True,
            text=True,
            check=True  # This will raise an exception if the command fails
        )

        if result.stderr:
            print(f"Warning getting logs for {service_name}: {result.stderr}")

        return jsonify({
            "logs": result.stdout if result.stdout else "No logs available",
            "success": True
        })
    except subprocess.CalledProcessError as e:
        error_msg = f"Error getting logs for {service_name}: {e.stderr}"
        print(error_msg)
        return jsonify({
            "error": error_msg,
            "success": False
        }), 500
    except Exception as e:
        error_msg = f"Unexpected error getting logs for {service_name}: {str(e)}"
        print(error_msg)
        return jsonify({
            "error": error_msg,
            "success": False
        }), 500


@app.route('/weather-status')
def weather_status():
    try:
        # Get the last modified time of weather.json
        weather_file = '/home/pi/weather.json'
        if os.path.exists(weather_file):
            last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(weather_file))
            
            formatted_date = last_modified.strftime('%m-%d-%Y %H:%M:%S')
            
            # Calculate time difference in minutes
            now = datetime.datetime.now()
            diff_minutes = (now - last_modified).total_seconds() / 60
            
            # The threshold should be 2x the update interval
            weather_update_threshold = (config.WEATHER_UPDATE_INTERVAL / 60) * 2  # 2x the update interval in minutes
            
            return jsonify({
                'success': True,
                'last_updated': formatted_date,
                'formatted_date': formatted_date,
                'diff_minutes': diff_minutes,
                'threshold': weather_update_threshold
            })
        else:
            app.logger.warning("Weather file not found")
            return jsonify({
                'success': False,
                'error': 'Weather data not available'
            })
    except Exception as e:
        app.logger.error(f"Error in weather-status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Add back the original endpoint for Home Assistant compatibility
@app.route('/weather-status', methods=['GET'])
def get_weather_status():
    weather_file_path = '/home/pi/weather.json'
    try:
        last_modified_timestamp = os.path.getmtime(weather_file_path)
        
        # For Home Assistant: YYYY-MM-DD HH:MM:SS
        ha_format = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # For web UI: MM-DD-YYYY HH:MM:SS
        ui_format = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%m-%d-%Y %H:%M:%S')
        
        return jsonify({
            "last_updated": ha_format,  # Keep original key for HA compatibility
            "formatted_date": ui_format,  # Add new key for UI
            "success": True
        }), 200
    except FileNotFoundError:
        return jsonify({
            "last_updated": "Weather data not available",
            "formatted_date": "Weather data not available",
            "success": False,
            "error": "Weather file not found"
        }), 404
    except Exception as e:
        return jsonify({
            "last_updated": "Weather data not available",
            "formatted_date": "Weather data not available",
            "success": False,
            "error": str(e)
        }), 500

@app.route('/get_timezones', methods=['GET'])
def get_timezones():
    try:
        # Common US/North American timezones
        common_timezones = [
            'America/New_York',     # Eastern
            'America/Chicago',      # Central
            'America/Denver',       # Mountain
            'America/Phoenix',      # Arizona (no DST)
            'America/Los_Angeles',  # Pacific
            'America/Anchorage',    # Alaska
            'Pacific/Honolulu',     # Hawaii
            'America/Puerto_Rico',  # Atlantic
            'America/Vancouver',    # Pacific Canada
            'America/Edmonton',     # Mountain Canada
            'America/Winnipeg',     # Central Canada
            'America/Toronto',      # Eastern Canada
            'America/Halifax'       # Atlantic Canada
        ]

        # Get current system timezone
        current_tz = subprocess.run(['timedatectl', 'show', '--property=Timezone'],
                                  capture_output=True, text=True).stdout.strip().split('=')[1]

        return jsonify({
            'timezones': common_timezones,
            'current': current_tz
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/set_timezone', methods=['POST'])
def set_timezone():
    try:
        timezone = request.json.get('timezone')
        if not timezone:
            return jsonify({'error': 'No timezone provided'}), 400

        # Validate timezone by checking if it exists in the list
        result = subprocess.run(['timedatectl', 'list-timezones'],
                              capture_output=True, text=True, check=True)
        available_timezones = result.stdout.strip().split('\n')

        if timezone not in available_timezones:
            return jsonify({'error': 'Invalid timezone'}), 400

        # Set system timezone
        subprocess.run(['sudo', 'timedatectl', 'set-timezone', timezone], check=True)

        # Restart scheduler service to apply timezone change
        subprocess.run(['sudo', 'systemctl', 'restart', 'scheduler.service'], check=True)

        return jsonify({
            'message': f'Timezone updated to {timezone}',
            'success': True
        })
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Failed to set timezone: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check_for_updates')
def check_for_updates_route():
    """Check for available updates using the update manager."""
    try:
        result = check_for_updates()
        return jsonify(result)
    except Exception as e:
        error_msg = f"Error checking for updates: {str(e)}"
        app.logger.error(error_msg)
        return jsonify({
            'error': error_msg
        }), 500

@app.route('/apply_update', methods=['POST'])
def apply_update():
    """Apply system updates using the update manager."""
    try:
        # Perform the update using the update manager
        result = perform_update()
        
        if result['success']:
            # Schedule service restart to happen after the response is sent
            def restart_services():
                time.sleep(2)  # Wait a moment for the response to be sent
                try:
                    # Restart the METAR service to apply config changes
                    subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)
                    app.logger.info("METAR service restarted after update")
                    
                    # Restart the scheduler service
                    subprocess.run(['sudo', 'systemctl', 'restart', 'scheduler.service'], check=True)
                    app.logger.info("Scheduler service restarted after update")
                    
                    # Restart the settings service
                    subprocess.run(['sudo', 'systemctl', 'restart', 'settings.service'], check=True)
                    app.logger.info("Settings service restarted after update")
                    
                except subprocess.CalledProcessError as e:
                    app.logger.error(f"Error restarting services after update: {e}")

            threading.Thread(target=restart_services).start()
            
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        app.logger.error(f"Error in apply_update: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Update failed: {str(e)}"
        }), 500

def get_local_ip():
    """Get the local IP address of the Raspberry Pi."""
    try:
        # Get IP address using hostname
        ip_address = subprocess.check_output(['hostname', '-I']).decode().split()[0]
        return ip_address
    except Exception as e:
        return "IP not available"

@app.route('/airport-conditions')
def get_airport_conditions():
    try:
        # Read weather data from the correct path
        with open('/home/pi/weather.json', 'r') as f:
            weather_data = json.load(f)

        airports = []
        for icao, data in weather_data.items():
            airport_info = {
                'icao': icao,
                'site': data.get('site', icao),
                'lat': data.get('latitude'),
                'lon': data.get('longitude'),
                'fltCat': data.get('flt_cat', 'MISSING'),
                'raw_observation': data.get('raw_observation', 'No data available')
            }
            airports.append(airport_info)

        return jsonify({'airports': airports})

    except FileNotFoundError:
        return jsonify({'error': 'Weather data file not found'}), 404

@app.route('/map-settings', methods=['GET', 'POST'])
def map_settings():
    try:
        if request.method == 'POST':
            data = request.json
            if not data or 'center' not in data or 'zoom' not in data:
                return jsonify({'error': 'Invalid request data'}), 400

            # Parse the current config.py
            current_config_dict = parse_config_file('/home/pi/config.py')

            # Update the values
            current_config_dict["MAP_CENTER_LAT"] = data['center'][0]
            current_config_dict["MAP_CENTER_LON"] = data['center'][1]
            current_config_dict["MAP_ZOOM"] = data['zoom']

            # Write the updated dictionary back to config.py
            write_config_file(current_config_dict, '/home/pi/config.py')

            # Reload the config module to get the new values
            reload_config()

            return jsonify({'success': True})

        # GET request - return current settings
        return jsonify({
            'center': [config.MAP_CENTER_LAT, config.MAP_CENTER_LON],
            'zoom': config.MAP_ZOOM
        })

    except Exception as e:
        logger.error(f"Error in map_settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/kiosk')
def kiosk():
    # Get the last modified date of weather.json
    weather_file_path = '/home/pi/weather.json'  # Adjust this path if necessary
    try:
        last_modified_timestamp = os.path.getmtime(weather_file_path)
        # Ensure consistent date format: MM-DD-YYYY HH:MM:SS
        weather_last_modified = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%m-%d-%Y %H:%M:%S')
    except FileNotFoundError:
        weather_last_modified = "Weather data not available"

    # Calculate the weather update threshold in minutes
    weather_update_threshold = (WEATHER_UPDATE_INTERVAL / 60) * 2

    return render_template('kiosk.html',
        vfr_color='rgb({}, {}, {})'.format(*VFR_COLOR),
        mvfr_color='rgb({}, {}, {})'.format(*MVFR_COLOR),
        ifr_color='rgb({}, {}, {})'.format(*IFR_COLOR),
        lifr_color='rgb({}, {}, {})'.format(*LIFR_COLOR),
        missing_color='rgb({}, {}, {})'.format(*MISSING_COLOR),
        lightening_color='rgb({}, {}, {})'.format(*LIGHTENING_COLOR),
        snowy_color='rgb({}, {}, {})'.format(*SNOWY_COLOR),
        wind_threshold=WIND_THRESHOLD,
        weather_last_modified=weather_last_modified,
        weather_update_interval=WEATHER_UPDATE_INTERVAL,
        weather_update_threshold=weather_update_threshold,  # Pass the calculated value
        animation_pause=ANIMATION_PAUSE,
        config=config,
        show_save_button=False
    )

@app.route('/kiosk/apply-filters', methods=['POST'])
def apply_kiosk_filters():
    try:
        # First, create a backup of the original airports file if it doesn't exist
        if not os.path.exists(AIRPORTS_FILE + '.backup'):
            shutil.copy(AIRPORTS_FILE, AIRPORTS_FILE + '.backup')
            logger.info(f"Created backup of {AIRPORTS_FILE}")

        data = request.get_json()
        filters = data.get('filters', [])
        major_airports = data.get('majorAirports', [])
        manual_airports = data.get('manualAirports', [])

        # Read the original airport configuration to validate against
        with open(AIRPORTS_FILE + '.backup', 'r') as f:
            original_airports = [line.strip() for line in f.readlines()]

        # Validate manual airports against original configuration
        invalid_airports = [code for code in manual_airports if code not in original_airports]
        if invalid_airports:
            return jsonify({
                'success': False,
                'error': f"The following airports are not in the original configuration: {', '.join(invalid_airports)}"
            }), 400

        # Collect airports based on filters
        selected_airports = set()

        # Add major airports if selected
        if 'major' in filters:
            valid_major = [code for code in major_airports if code in original_airports]
            selected_airports.update(valid_major)

        # Add condition-based airports from existing weather data
        weather_data = weather.read_weather_data()
        if weather_data:
            if 'windy' in filters:
                windy = weather.get_windy_airports(weather_data)
                selected_airports.update(windy.keys())
            if 'lightning' in filters:
                lightning = weather.get_lightning_airports(weather_data)
                selected_airports.update(lightning.keys())
            if 'snow' in filters:
                snowy = weather.get_snowy_airports(weather_data)
                selected_airports.update(snowy.keys())

        # Add manual airports (already validated)
        selected_airports.update(manual_airports)

        # Write directly to airports.txt while preserving structure
        with open(AIRPORTS_FILE, 'w') as f:
            for original_airport in original_airports:
                if original_airport in selected_airports:
                    f.write(f"{original_airport}\n")
                else:
                    f.write("SKIP\n")

        # Restart only the LED display service
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)
            return jsonify({
                'success': True,
                'count': len(selected_airports)
            })
        except subprocess.CalledProcessError as e:
            return jsonify({
                'success': False,
                'error': f'Failed to restart METAR service: {str(e)}'
            }), 500

    except Exception as e:
        logger.error(f"Error applying kiosk filters: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/kiosk/reset', methods=['POST'])
def reset_kiosk():
    try:
        # Copy original airports.txt back from backup
        if os.path.exists('airports.txt.backup'):
            shutil.copy('airports.txt.backup', AIRPORTS_FILE)

            # Restart the METAR service to apply changes immediately
            try:
                subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)
                return jsonify({'success': True})
            except subprocess.CalledProcessError as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to restart METAR service: {str(e)}'
                }), 500
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error resetting kiosk: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/kiosk/condition-airports')
def get_condition_airports():
    try:
        # Read weather data
        weather_data = weather.read_weather_data()
        if not weather_data:
            return jsonify({'error': 'No weather data available'}), 404
            
        # Use existing weather.py functions
        windy_airports = weather.get_windy_airports(weather_data)
        lightning_airports = weather.get_lightning_airports(weather_data)
        snowy_airports = weather.get_snowy_airports(weather_data)
        
        return jsonify({
            'windy': windy_airports,
            'lightning': lightning_airports,
            'snowy': snowy_airports
        })
    except Exception as e:
        logger.error(f"Error getting condition airports: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-weather-data')
def get_weather_data():
    try:
        weather_file_path = '/home/pi/weather.json'
        app.logger.info(f"Reading weather data from: {weather_file_path}")
        with open(weather_file_path, 'r') as f:
            weather_data = json.load(f)
        app.logger.info("Successfully loaded weather data")
        return jsonify(weather_data)
    except FileNotFoundError:
        app.logger.error("Weather data file not found")
        return jsonify({"error": "Weather data not found"}), 404
    except Exception as e:
        app.logger.error(f"Error reading weather data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/test-leds', methods=['POST'])
def test_leds_route():
    data = request.get_json()
    color = data.get('color')
    start_pixel = data.get('start_pixel')
    end_pixel = data.get('end_pixel')
    
    if not color:
        return jsonify({'error': 'No color provided'}), 400
    
    # Convert hex color to RGB tuple
    color = color.lstrip('#')
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    
    # Convert pixel indices to integers if provided
    if start_pixel is not None:
        try:
            start_pixel = int(start_pixel)
        except ValueError:
            return jsonify({'error': 'Invalid start_pixel value'}), 400
            
    if end_pixel is not None:
        try:
            end_pixel = int(end_pixel)
        except ValueError:
            return jsonify({'error': 'Invalid end_pixel value'}), 400
    
    try:
        # Create a simple script that imports and uses the led_test module
        temp_script = '/tmp/led_test_temp.py'
        with open(temp_script, 'w') as f:
            f.write(f'''
import sys
import os
import traceback

try:
    # Add /home/pi to Python path
    sys.path.append('/home/pi')
    
    # Import the led_test module
    from led_test import test_specific_leds
    
    # Test the LEDs with the specified color and pixel range
    print(f"Testing LEDs with color: {rgb}")
    print(f"Pixel range: {start_pixel} to {end_pixel}")
    test_specific_leds({rgb}, {start_pixel}, {end_pixel})
    print("LED test completed successfully")
except Exception as e:
    print(f"Error in LED test: {{str(e)}}")
    traceback.print_exc()
    sys.exit(1)
''')
        
        # Use the correct Python interpreter path
        python_path = '/home/pi/metar/bin/python3'
        
        # Run the script with sudo and capture output
        result = subprocess.run(['sudo', python_path, temp_script], 
                               check=True, 
                               capture_output=True, 
                               text=True)
        
        # Log the output for debugging
        print(f"Script stdout: {result.stdout}")
        print(f"Script stderr: {result.stderr}")
        
        return jsonify({'success': True, 'output': result.stdout})
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if hasattr(e, 'stderr') else "No error output available"
        stdout_output = e.stdout if hasattr(e, 'stdout') else "No stdout output available"
        return jsonify({
            'error': f'Failed to test LEDs: {str(e)}',
            'stdout': stdout_output,
            'stderr': error_output
        }), 500
    except Exception as e:
        return jsonify({'error': f'Failed to test LEDs: {str(e)}'}), 500

@app.route('/turn-off-leds', methods=['POST'])
def turn_off_leds_route():
    try:
        # Create a simple script that imports and uses the led_test module
        temp_script = '/tmp/led_off_temp.py'
        with open(temp_script, 'w') as f:
            f.write('''
import sys
import os
import traceback

try:
    # Add /home/pi to Python path
    sys.path.append('/home/pi')
    
    # Import the led_test module
    from led_test import turn_off_leds
    
    # Turn off all LEDs
    print("Turning off all LEDs")
    turn_off_leds()
    print("LEDs turned off successfully")
except Exception as e:
    print(f"Error turning off LEDs: {str(e)}")
    traceback.print_exc()
    sys.exit(1)
''')
        
        # Use the correct Python interpreter path
        python_path = '/home/pi/metar/bin/python3'
        
        # Run the script with sudo and capture output
        result = subprocess.run(['sudo', python_path, temp_script], 
                               check=True, 
                               capture_output=True, 
                               text=True)
        
        # Log the output for debugging
        print(f"Script stdout: {result.stdout}")
        print(f"Script stderr: {result.stderr}")
        
        return jsonify({'success': True, 'output': result.stdout})
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if hasattr(e, 'stderr') else "No error output available"
        stdout_output = e.stdout if hasattr(e, 'stdout') else "No stdout output available"
        return jsonify({
            'error': f'Failed to turn off LEDs: {str(e)}',
            'stdout': stdout_output,
            'stderr': error_output
        }), 500
    except Exception as e:
        return jsonify({'error': f'Failed to turn off LEDs: {str(e)}'}), 500

@app.route('/update-brightness', methods=['POST'])
def update_brightness_route():
    data = request.get_json()
    brightness = data.get('brightness')
    if not brightness:
        return jsonify({'error': 'No brightness provided'}), 400
    
    try:
        # Create a self-contained script that doesn't rely on importing led_test
        temp_script = '/tmp/led_brightness_temp.py'
        with open(temp_script, 'w') as f:
            f.write(f'''
import sys
import os
import traceback

try:
    # Add /home/pi to Python path
    sys.path.append('/home/pi')
    
    # Import required modules
    import board
    import neopixel
    from config import PIXEL_PIN, NUM_PIXELS, BRIGHTNESS, LED_COLOR_ORDER
    
    # Set up the LED strip
    pixel_pin = f"D{{PIXEL_PIN}}"  # Create "D18"
    pixels = neopixel.NeoPixel(getattr(board, pixel_pin), NUM_PIXELS, 
                              brightness=BRIGHTNESS, auto_write=False, 
                              pixel_order=LED_COLOR_ORDER)
    
    # Update brightness
    print(f"Updating brightness to: {brightness}")
    pixels.brightness = {brightness}
    pixels.show()
    print("Brightness updated successfully")
except Exception as e:
    print(f"Error updating brightness: {{str(e)}}")
    traceback.print_exc()
    sys.exit(1)
''')
        
        # Use the correct Python interpreter path
        python_path = '/home/pi/metar/bin/python3'
        
        # Run the script with sudo and capture output
        result = subprocess.run(['sudo', python_path, temp_script], 
                               check=True, 
                               capture_output=True, 
                               text=True)
        
        # Log the output for debugging
        print(f"Script stdout: {result.stdout}")
        print(f"Script stderr: {result.stderr}")
        
        return jsonify({'success': True, 'output': result.stdout})
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if hasattr(e, 'stderr') else "No error output available"
        stdout_output = e.stdout if hasattr(e, 'stdout') else "No stdout output available"
        return jsonify({
            'error': f'Failed to update brightness: {str(e)}',
            'stdout': stdout_output,
            'stderr': error_output
        }), 500
    except Exception as e:
        return jsonify({'error': f'Failed to update brightness: {str(e)}'}), 500

# LED Test Service Control
@app.route('/led-test-service/start', methods=['POST'])
def start_led_test_service():
    try:
        result = subprocess.run(['sudo', 'systemctl', 'start', 'ledtest.service'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({'success': True})
        else:
            app.logger.error(f"Failed to start LED test service: {result.stderr}")
            return jsonify({'success': False, 'error': result.stderr})
    except Exception as e:
        app.logger.error(f"Error starting LED test service: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/led-test-service/stop', methods=['POST'])
def stop_led_test_service():
    try:
        result = subprocess.run(['sudo', 'systemctl', 'stop', 'ledtest.service'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({'success': True})
        else:
            app.logger.error(f"Failed to stop LED test service: {result.stderr}")
            return jsonify({'success': False, 'error': result.stderr})
    except Exception as e:
        app.logger.error(f"Error stopping LED test service: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/led-test-service/status', methods=['GET'])
def led_test_service_status():
    try:
        result = subprocess.run(['systemctl', 'is-active', 'ledtest.service'], 
                               capture_output=True, text=True)
        is_active = result.stdout.strip() == 'active'
        return jsonify({'success': True, 'active': is_active})
    except Exception as e:
        app.logger.error(f"Error checking LED test service status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/shutdown', methods=['POST'])
def shutdown_system():
    """Stop all services, blank the lights, and shut down the Raspberry Pi."""
    try:
        # First, send a response to the client
        response = jsonify({'success': True, 'message': 'System is shutting down'})
        response.headers['Connection'] = 'close'  # Force the connection to close after sending
        
        # Schedule the shutdown to happen after the response is sent
        def shutdown_after_response():
            try:
                # Stop the METAR service
                subprocess.run(['sudo', 'systemctl', 'stop', 'metar.service'], check=True)
                app.logger.info("METAR service stopped for shutdown")
                
                # Try to run blank.py to turn off all LEDs, but continue even if it fails
                try:
                    # Use the virtual environment Python interpreter
                    subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'], check=True)
                    app.logger.info("LEDs blanked for shutdown")
                except subprocess.CalledProcessError as e:
                    app.logger.warning(f"Failed to blank LEDs: {e}. Continuing with shutdown.")
                
                # Stop the scheduler service
                subprocess.run(['sudo', 'systemctl', 'stop', 'scheduler.service'], check=True)
                app.logger.info("Scheduler service stopped for shutdown")
                
                # Shutdown the Raspberry Pi
                subprocess.run(['sudo', 'shutdown', 'now'], check=True)
                app.logger.info("Shutdown command executed")
            except Exception as e:
                app.logger.error(f"Error during shutdown process: {e}")
        
        # Start the shutdown process in a separate thread
        threading.Thread(target=shutdown_after_response).start()
        
        return response
    except Exception as e:
        app.logger.error(f"Unexpected error during shutdown: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/restart', methods=['POST'])
def restart_system():
    """Restart the Raspberry Pi with a delayed response for countdown."""
    try:
        # First, send a response to the client
        response = jsonify({'success': True, 'message': 'System is restarting'})
        response.headers['Connection'] = 'close'  # Force the connection to close after sending

        # Schedule the restart to happen after the response is sent
        def restart_after_response():
            try:
                # Stop the METAR service
                subprocess.run(['sudo', 'systemctl', 'stop', 'metar.service'], check=True)
                app.logger.info("METAR service stopped for restart")

                # Try to run blank.py to turn off all LEDs, but continue even if it fails
                try:
                    subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'], check=True)
                    app.logger.info("LEDs blanked for restart")
                except subprocess.CalledProcessError as e:
                    app.logger.warning(f"Failed to blank LEDs: {e}. Continuing with restart.")

                # Stop the scheduler service
                subprocess.run(['sudo', 'systemctl', 'stop', 'scheduler.service'], check=True)
                app.logger.info("Scheduler service stopped for restart")

                # Wait for countdown (20 seconds recommended)
                app.logger.info("Waiting 1 second before restarting...")
                time.sleep(1)

                # Restart the Raspberry Pi
                subprocess.run(['sudo', 'reboot'], check=True)
                app.logger.info("Reboot command executed")
            except Exception as e:
                app.logger.error(f"Error during restart process: {e}")

        # Start the restart process in a separate thread
        threading.Thread(target=restart_after_response).start()

        return response
    except Exception as e:
        app.logger.error(f"Unexpected error during restart: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/calculate-sun-times', methods=['POST'])
def calculate_sun_times_endpoint():
    """Calculate sunrise and sunset times for a selected city."""
    try:
        city_name = request.json.get('city')
        if not city_name:
            return jsonify({'error': 'City name is required'}), 400
            
        sunrise, sunset = calculate_sun_times(city_name)
        
        if sunrise and sunset:
            return jsonify({
                'success': True,
                'sunrise': f"{sunrise.hour:02d}:{sunrise.minute:02d}",
                'sunset': f"{sunset.hour:02d}:{sunset.minute:02d}",
                'bright_time_start': f"{sunrise.hour:02d}:{sunrise.minute:02d}",
                'dim_time_start': f"{sunset.hour:02d}:{sunset.minute:02d}"
            })
        else:
            return jsonify({'error': 'Could not calculate sun times for this city'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Error calculating sun times: {str(e)}'}), 500

@app.route('/get-cities', methods=['GET'])
def get_cities():
    """Get the list of available cities."""
    try:
        from config import CITIES
        cities = [city['name'] for city in CITIES]
        return jsonify({'cities': cities})
    except Exception as e:
        return jsonify({'error': f'Error getting cities: {str(e)}'}), 500

@app.route('/validate_config')
def validate_config():
    """Validate the current config.py file and return results."""
    try:
        is_valid, message = validate_config_file('/home/pi/config.py')
        return jsonify({
            'valid': is_valid,
            'message': message,
            'file_size': os.path.getsize('/home/pi/config.py') if os.path.exists('/home/pi/config.py') else 0
        })
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': f"Validation error: {str(e)}",
            'file_size': 0
        })

if __name__ == '__main__':
    if ENABLE_HTTPS:
        app.run(
            host='0.0.0.0',
            port=443,
            ssl_context=(
                '/etc/ssl/certs/flask-selfsigned.crt',
                '/etc/ssl/private/flask-selfsigned.key'
            )
        )
    else:
        app.run(host='0.0.0.0', port=80, debug=False)
