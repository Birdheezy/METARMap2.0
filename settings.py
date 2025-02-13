from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import subprocess
import os
from config import *
import datetime
import config
import shutil
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


app = Flask(__name__)
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
    PIXEL_PIN = globals().get('PIXEL_PIN', None),
    WEATHER_UPDATE_INTERVAL = globals().get('WEATHER_UPDATE_INTERVAL', None)
    UPDATE_WEATHER = globals().get('UPDATE_WEATHER', None)
    STALE_INDICATION = globals().get('STALE_INDICATION', None)
    STALE_DATA_COLOR = globals().get('STALE_DATA_COLOR', None)
    WIFI_DISCONNECTED_COLOR = globals().get('WIFI_DISCONNECTED_COLOR', None)
    WIFI_INDICATION = globals().get('WIFI_INDICATION', True)


@app.route('/leds/on', methods=['POST'])
def turn_on_leds():
    subprocess.run(['sudo', 'systemctl', 'start', 'metar.service'])
    return jsonify({"status": "LEDs turned on"}), 200

@app.route('/leds/off', methods=['POST'])
def turn_off_leds():
    subprocess.run(['sudo', 'systemctl', 'stop', 'metar.service'])
    subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'])
    return jsonify({"status": "LEDs turned off"}), 200

@app.route('/update-weather', methods=['POST'])
def refresh_weather():
    try:
        # Call weather module functions directly
        metar_data = weather.fetch_metar()
        if metar_data:
            parsed_data = weather.parse_weather(metar_data)
            if parsed_data:
                # Save the weather data
                weather_file = os.path.join(os.getcwd(), 'weather.json')
                with open(weather_file, 'w') as json_file:
                    json.dump(parsed_data, json_file, indent=4)
                return jsonify({"status": "Weather updated successfully"}), 200
            else:
                return jsonify({"status": "Failed to parse weather data"}), 500
        else:
            return jsonify({"status": "Failed to fetch weather data"}), 500
    except Exception as e:
        return jsonify({"status": f"Error updating weather: {str(e)}"}), 500

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
            # Create a dictionary for updates
            config_updates = {}

            # Extract and validate time settings
            try:
                config_updates["PIXEL_PIN"] = request.form.get('PIXEL_PIN', '').strip()
                config_updates["LEGEND"] = 'legend' in request.form
                config_updates["ENABLE_LIGHTS_OFF"] = 'enable_lights_off' in request.form
                config_updates["DAYTIME_DIMMING"] = 'daytime_dimming' in request.form
                config_updates["WIND_ANIMATION"] = 'wind_animation' in request.form
                config_updates["LIGHTENING_ANIMATION"] = 'lightening_animation' in request.form
                config_updates["SNOWY_ANIMATION"] = 'snowy_animation' in request.form
                config_updates["ENABLE_HTTPS"] = 'enable_https' in request.form
                config_updates["UPDATE_WEATHER"] = 'update_weather' in request.form
                config_updates["STALE_INDICATION"] = 'stale_indication' in request.form
            # Float or Integer Settings
                config_updates["BRIGHTNESS"] = float(request.form.get('brightness', 0))
                config_updates["DIM_BRIGHTNESS"] = float(request.form.get('dim_brightness', 0))
                config_updates["DAYTIME_DIM_BRIGHTNESS"] = float(request.form.get('daytime_dim_brightness', 0))
                config_updates["WIND_THRESHOLD"] = int(request.form.get('wind_threshold', 0))
                config_updates["WIND_FADE_TIME"] = float(request.form.get('wind_fade_time', 0))
                config_updates["WIND_PAUSE"] = float(request.form.get('wind_pause', 0))
                config_updates["ANIMATION_PAUSE"] = int(request.form.get('animation_pause', 0))
                config_updates["LIGHTNING_FLASH_COUNT"] = int(request.form.get('lightning_flash_count', 0))
                config_updates["SNOW_BLINK_COUNT"] = int(request.form.get('snow_blink_count', 0))
                config_updates["SNOW_BLINK_PAUSE"] = float(request.form.get('snow_blink_pause', 0))
                config_updates["NUM_STEPS"] = int(request.form.get('num_steps', 0))
                config_updates["NUM_PIXELS"] = int(request.form.get('num_pixels', 0))
                config_updates["WEATHER_UPDATE_INTERVAL"] = int(request.form.get('weather_update_interval', 5))

                # Time Settings (convert from form input)
                config_updates["BRIGHT_TIME_START"] = f"datetime.time({request.form.get('bright_time_start_hour', 0)}, {request.form.get('bright_time_start_minute', 0)})"
                config_updates["DIM_TIME_START"] = f"datetime.time({request.form.get('dim_time_start_hour', 0)}, {request.form.get('dim_time_start_minute', 0)})"
                config_updates["LIGHTS_OFF_TIME"] = f"datetime.time({request.form.get('lights_off_time_hour', 0)}, {request.form.get('lights_off_time_minute', 0)})"
                config_updates["LIGHTS_ON_TIME"] = f"datetime.time({request.form.get('lights_on_time_hour', 0)}, {request.form.get('lights_on_time_minute', 0)})"

                # Convert minutes to seconds for storage
                minutes = float(request.form.get('weather_update_interval', 5))
                config_updates["WEATHER_UPDATE_INTERVAL"] = int(minutes * 60)

            except ValueError:
                raise ValueError("Could not update time settings: Please enter valid numbers for hours and minutes.")

            # Handle color inputs with GRB adjustment
            color_fields = {
                "VFR_COLOR": "vfr_color",
                "MVFR_COLOR": "mvfr_color",
                "IFR_COLOR": "ifr_color",
                "LIFR_COLOR": "lifr_color",
                "MISSING_COLOR": "missing_color",
                "LIGHTENING_COLOR": "lightening_color",
                "SNOWY_COLOR": "snowy_color"
            }

            for key, field_name in color_fields.items():
                hex_value = request.form.get(field_name)
                if hex_value:
                    # Convert HEX to RGB tuple
                    r, g, b = (int(hex_value[i:i+2], 16) for i in (1, 3, 5))

                    # Rearrange to GRB for your LEDs
                    grb_value = (g, r, b)

                    # Save the GRB value
                    config_updates[key] = grb_value

            # Process color values
            stale_data_color = request.form.get('stale_data_color')
            if stale_data_color.startswith('#'):
                stale_data_color = stale_data_color[1:]  # Remove the '#' prefix
            r = int(stale_data_color[:2], 16)
            g = int(stale_data_color[2:4], 16)
            b = int(stale_data_color[4:], 16)
            config_updates["STALE_DATA_COLOR"] = (g, r, b)  # Store in GRB format

            # Define individual settings updates and catch specific errors
            try:
                config_updates["LIGHTNING_FLASH_COUNT"] = float(request.form['lightning_flash_count'])
            except ValueError:
                raise ValueError("Could not update Lightning Flash Count: Please enter a valid number.")
            try:
                config_updates["BRIGHTNESS"] = float(request.form['brightness'])
            except ValueError:
                raise ValueError("Could not update Brightness: Please enter a valid number.")
            try:
                config_updates["DIM_BRIGHTNESS"] = float(request.form['dim_brightness'])
            except ValueError:
                raise ValueError("Could not update Dim Brightness: Please enter a valid number.")
            try:
                config_updates["WIND_THRESHOLD"] = int(request.form['wind_threshold'])
            except ValueError:
                raise ValueError("Could not update Wind Threshold: Please enter a valid integer.")
            try:
                config_updates["WIND_FADE_TIME"] = float(request.form['wind_fade_time'])
            except ValueError:
                raise ValueError("Could not update Wind Fade Time: Please enter a valid number.")
            try:
                config_updates["WIND_PAUSE"] = float(request.form['wind_pause'])
            except ValueError:
                raise ValueError("Could not update Wind Pause: Please enter a valid number.")
            try:
                config_updates["ANIMATION_PAUSE"] = int(request.form['animation_pause'])
            except ValueError:
                raise ValueError("Could not update Animation Pause: Please enter a valid integer.")
            try:
                config_updates["NUM_STEPS"] = int(request.form['num_steps'])
            except ValueError:
                raise ValueError("Could not update Number of Steps: Please enter a valid integer.")
            try:
                config_updates["SNOW_BLINK_COUNT"] = int(request.form['snow_blink_count'])
            except ValueError:
                raise ValueError("Could not update Snow Blink Count: Please enter a valid integer.")
            try:
                config_updates["SNOW_BLINK_PAUSE"] = float(request.form['snow_blink_pause'])
            except ValueError:
                raise ValueError("Could not update Snow Blink Pause: Please enter a valid number.")
            try:
                config_updates["DAYTIME_DIM_BRIGHTNESS"] = float(request.form['daytime_dim_brightness'])
            except ValueError:
                raise ValueError("Could not update Daytime Dim Brightness: Please enter a valid number.")
            try:
                config_updates["NUM_PIXELS"] = float(request.form['num_pixels'])
            except ValueError:
                raise ValueError("Could not update Pixel Count: Please enter a valid number.")
            try:
                config_updates["PIXEL_PIN"] = int(request.form['PIXEL_PIN'])
            except ValueError:
                raise ValueError("Could not update PIXEL_PIN: Please enter a valid integer.")
            try:
                # Convert minutes to seconds for storage
                minutes = float(request.form.get('weather_update_interval', 5))
                config_updates["WEATHER_UPDATE_INTERVAL"] = int(minutes * 60)  # Store as seconds in config
            except ValueError:
                raise ValueError("Could not update Weather Update Interval: Please enter a valid number.")


            # Boolean values for checkbox-based settings
            config_updates["WIND_ANIMATION"] = 'wind_animation' in request.form
            config_updates["LIGHTENING_ANIMATION"] = 'lightening_animation' in request.form
            config_updates["SNOWY_ANIMATION"] = 'snowy_animation' in request.form
            config_updates["DAYTIME_DIMMING"] = 'daytime_dimming' in request.form
            config_updates["ENABLE_LIGHTS_OFF"] = 'enable_lights_off' in request.form
            config_updates["LEGEND"] = 'legend' in request.form
            config_updates["ENABLE_HTTPS"] = 'enable_https' in request.form
            config_updates["UPDATE_WEATHER"] = 'update_weather' in request.form
            config_updates["STALE_INDICATION"] = 'stale_indication' in request.form

            # Update the config.py file
            with open('/home/pi/config.py', 'r') as f:
                config_lines = f.readlines()

            with open('/home/pi/config.py', 'w') as f:
                for line in config_lines:
                    updated = False
                    for key, value in config_updates.items():
                        if line.startswith(key):
                            if isinstance(value, float) and value.is_integer():
                                value = int(value)
                            f.write(f"{key} = {value}\n")
                            updated = True
                            break
                    if not updated:
                        f.write(line)

            # Reload the configuration to reflect the changes
            reload_config()
            updated_airports = request.form.get("airports")

            # Write the updated list to airports.txt
            if updated_airports is not None:
                with open('/home/pi/airports.txt', 'w') as f:  # Replace with actual path to airports.txt
                    f.write(updated_airports)
            flash('Configuration updated and METAR service restarted!', 'success')

        except ValueError as e:
            flash(str(e), 'danger')  # Show specific error messages
        except Exception as e:
            flash(f'An unexpected error occurred: {str(e)}', 'danger')  # Catch all other errors

        # Redirect to refresh the form with updated values
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

    vfr_color = '#{:02x}{:02x}{:02x}'.format(config.VFR_COLOR[1], config.VFR_COLOR[0], config.VFR_COLOR[2])  # GRB -> RGB
    mvfr_color = '#{:02x}{:02x}{:02x}'.format(config.MVFR_COLOR[1], config.MVFR_COLOR[0], config.MVFR_COLOR[2])  # GRB -> RGB
    ifr_color = '#{:02x}{:02x}{:02x}'.format(config.IFR_COLOR[1], config.IFR_COLOR[0], config.IFR_COLOR[2])  # GRB -> RGB
    lifr_color = '#{:02x}{:02x}{:02x}'.format(config.LIFR_COLOR[1], config.LIFR_COLOR[0], config.LIFR_COLOR[2])  # GRB -> RGB
    missing_color = '#{:02x}{:02x}{:02x}'.format(config.MISSING_COLOR[1], config.MISSING_COLOR[0], config.MISSING_COLOR[2])  # GRB -> RGB
    lightening_color = '#{:02x}{:02x}{:02x}'.format(config.LIGHTENING_COLOR[1], config.LIGHTENING_COLOR[0], config.LIGHTENING_COLOR[2])  # GRB -> RGB
    snowy_color = '#{:02x}{:02x}{:02x}'.format(config.SNOWY_COLOR[1], config.SNOWY_COLOR[0], config.SNOWY_COLOR[2])  # GRB -> RGB
    stale_data_color = '#{:02x}{:02x}{:02x}'.format(config.STALE_DATA_COLOR[1], config.STALE_DATA_COLOR[0], config.STALE_DATA_COLOR[2])  # GRB -> RGB
    wifi_disconnected_color = '#{:02x}{:02x}{:02x}'.format(config.WIFI_DISCONNECTED_COLOR[1], config.WIFI_DISCONNECTED_COLOR[0], config.WIFI_DISCONNECTED_COLOR[2])

    # Get the last modified date of weather.json
    weather_file_path = '/home/pi/weather.json'  # Adjust this path if necessary
    try:
        last_modified_timestamp = os.path.getmtime(weather_file_path)
        weather_last_modified = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%m-%d-%Y %H:%M:%S')
    except FileNotFoundError:
        weather_last_modified = "Weather data not available"

    # Load the airport list from airports.txt
    with open('/home/pi/airports.txt', 'r') as f:
        airports = f.read()

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
        wind_animation=config.WIND_ANIMATION,
        lightening_animation=config.LIGHTENING_ANIMATION,
        snowy_animation=config.SNOWY_ANIMATION,
        daytime_dimming=config.DAYTIME_DIMMING,
        enable_https=config.ENABLE_HTTPS,
        pixel_pin=config.PIXEL_PIN,
        weather_update_interval=config.WEATHER_UPDATE_INTERVAL,
        stale_indication=config.STALE_INDICATION,
        wifi_disconnected_color=wifi_disconnected_color
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

@app.route('/update-weather')
def update_weather():
    try:
        # Call weather module functions directly
        metar_data = weather.fetch_metar()
        if metar_data:
            parsed_data = weather.parse_weather(metar_data)
            if parsed_data:
                # Save the weather data
                with open('/home/pi/weather.json', 'w') as json_file:
                    json.dump(parsed_data, json_file, indent=4)
                flash('Weather Has Been Updated!', 'success')
            else:
                flash('Failed to parse weather data', 'danger')
        else:
            flash('Failed to fetch weather data', 'danger')
    except Exception as e:
        flash(f'Weather Update Has Failed... {str(e)}', 'danger')
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
        # Get logs for any service with consistent formatting, limited to last 100 lines
        result = subprocess.run(
            ['sudo', 'journalctl', '-u', f'{service_name}.service', '-n', '100',
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


@app.route('/weather-status', methods=['GET'])
def get_weather_status():
    weather_file_path = '/home/pi/weather.json'
    try:
        last_modified_timestamp = os.path.getmtime(weather_file_path)
        last_updated = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({
            "last_updated": last_updated,
            "success": True
        }), 200
    except FileNotFoundError:
        return jsonify({
            "last_updated": "Weather data not available",
            "success": False,
            "error": "Weather file not found"
        }), 404
    except Exception as e:
        return jsonify({
            "last_updated": "Weather data not available",
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
def check_for_updates():
    try:
        # Get current branch
        branch_cmd = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                  capture_output=True, text=True, check=True,
                                  cwd='/home/pi')
        current_branch = branch_cmd.stdout.strip()

        # Fetch updates from remote
        fetch_cmd = subprocess.run(['git', 'fetch', 'origin', current_branch],
                                 capture_output=True, text=True, check=True,
                                 cwd='/home/pi')

        # Compare local HEAD with remote HEAD
        diff_cmd = subprocess.run(['git', 'rev-list', 'HEAD...origin/' + current_branch, '--count'],
                                capture_output=True, text=True, check=True,
                                cwd='/home/pi')
        commits_behind = int(diff_cmd.stdout.strip())

        if commits_behind > 0:
            # Get the list of files that would be updated
            files_cmd = subprocess.run(['git', 'diff', '--name-only', 'HEAD...origin/' + current_branch],
                                     capture_output=True, text=True, check=True,
                                     cwd='/home/pi')
            changed_files = files_cmd.stdout.strip().split('\n')

            return jsonify({
                'has_updates': True,
                'branch': current_branch,
                'commits_behind': commits_behind,
                'files': changed_files
            })
        else:
            return jsonify({
                'has_updates': False,
                'branch': current_branch,
                'message': 'Your system is up to date!'
            })

    except subprocess.CalledProcessError as e:
        error_msg = f"Git command failed: {e.stderr.strip() if e.stderr else 'No error output'}"
        app.logger.error(error_msg)
        return jsonify({
            'error': error_msg
        }), 500
    except Exception as e:
        error_msg = f"Error checking for updates: {str(e)}"
        app.logger.error(error_msg)
        return jsonify({
            'error': error_msg
        }), 500

@app.route('/apply_update', methods=['POST'])
def apply_update():
    try:
        # Get current branch
        branch_cmd = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                  capture_output=True, text=True, check=True)
        current_branch = branch_cmd.stdout.strip()

        # Create backup directory with timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_dir = f'/home/pi/BACKUP/{timestamp}'
        os.makedirs(backup_dir, exist_ok=True)

        # Get list of tracked files
        tracked_files_cmd = subprocess.run(['git', 'ls-files'],
                                         capture_output=True, text=True, check=True)
        tracked_files = tracked_files_cmd.stdout.strip().split('\n')

        # Backup tracked files
        for file in tracked_files:
            if os.path.exists(file):
                # Create subdirectories in backup if needed
                backup_file = os.path.join(backup_dir, file)
                os.makedirs(os.path.dirname(backup_file), exist_ok=True)
                shutil.copy2(file, backup_file)

        # Save temporary copies of config.py and airports.txt
        if os.path.exists('config.py'):
            shutil.copy2('config.py', '/tmp/config.py.tmp')
        if os.path.exists('airports.txt'):
            shutil.copy2('airports.txt', '/tmp/airports.txt.tmp')

        # Force pull from remote
        subprocess.run(['git', 'fetch', 'origin', current_branch], check=True)
        subprocess.run(['git', 'reset', '--hard', f'origin/{current_branch}'], check=True)

        # Restore airports.txt if it existed
        if os.path.exists('/tmp/airports.txt.tmp'):
            shutil.copy2('/tmp/airports.txt.tmp', 'airports.txt')
            os.remove('/tmp/airports.txt.tmp')

        # Smart merge of config.py
        if os.path.exists('/tmp/config.py.tmp'):
            # Read both config files
            with open('/tmp/config.py.tmp', 'r') as f:
                old_config = f.read()
            with open('config.py', 'r') as f:
                new_config = f.read()

            # Extract settings from both configs
            old_settings = {}
            new_settings = {}
            exec(old_config, {}, old_settings)
            exec(new_config, {}, new_settings)

            # Remove Python internals
            old_settings = {k: v for k, v in old_settings.items() if not k.startswith('__')}
            new_settings = {k: v for k, v in new_settings.items() if not k.startswith('__')}

            # Merge settings (prefer old values for existing settings)
            merged_settings = new_settings.copy()
            for key, value in old_settings.items():
                if key in merged_settings:
                    merged_settings[key] = value

            # Read the new config file line by line to preserve structure and comments
            with open('config.py', 'r') as f:
                config_lines = f.readlines()

            # Process each line, replacing values while preserving structure
            new_config_lines = []
            for line in config_lines:
                line = line.rstrip()
                if '=' in line and not line.strip().startswith('#'):
                    # Extract the variable name
                    var_name = line.split('=')[0].strip()
                    if var_name in merged_settings:
                        # Format the value based on its type
                        value = merged_settings[var_name]
                        if isinstance(value, str):
                            new_line = f"{var_name} = '{value}'"
                        elif isinstance(value, datetime.time):
                            new_line = f"{var_name} = datetime.time({value.hour}, {value.minute})"
                        elif isinstance(value, (tuple, list)):
                            new_line = f"{var_name} = {value}"
                        else:
                            new_line = f"{var_name} = {value}"
                        new_config_lines.append(new_line)
                    else:
                        new_config_lines.append(line)
                else:
                    new_config_lines.append(line)

            # Write the merged config
            with open('config.py', 'w') as f:
                f.write('\n'.join(new_config_lines))

            os.remove('/tmp/config.py.tmp')

        # Clean up old backups (keep only last 5)
        backup_root = '/home/pi/BACKUP'
        if os.path.exists(backup_root):
            backups = sorted([d for d in os.listdir(backup_root)
                            if os.path.isdir(os.path.join(backup_root, d))])
            while len(backups) > 5:
                oldest = backups.pop(0)
                shutil.rmtree(os.path.join(backup_root, oldest))

        # Set ownership to pi user
        subprocess.run(['sudo', 'chown', '-R', 'pi:pi', '/home/pi'], check=True)

        # Restart all services to apply changes
        try:
            # First restart settings service (which will trigger the page refresh)
            subprocess.run(['sudo', 'systemctl', 'restart', 'settings.service'], check=True)
            # Brief delay to allow settings service to restart
            time.sleep(2)
            # Then restart scheduler (which handles weather updates)
            subprocess.run(['sudo', 'systemctl', 'restart', 'scheduler.service'], check=True)
            # Finally restart metar service (which handles LED display)
            subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)
            restart_message = "Update applied successfully. All services have been restarted."
        except subprocess.CalledProcessError as e:
            restart_message = f"Update applied but service restart failed: {str(e)}"

        return jsonify({
            'success': True,
            'message': restart_message
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
#test
