from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
import os
from config import *  # Import all variables from config.py
import datetime
import config
from flask import jsonify
import shutil
import shutil
import re
import time
import threading
import importlib


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
    subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/weather.py'], check=True)
    return jsonify({"status": "Weather updated successfully"}), 200

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
                config_updates["LEGEND"] = 'legend' in request.form
                config_updates["ENABLE_LIGHTS_OFF"] = 'enable_lights_off' in request.form
                config_updates["DAYTIME_DIMMING"] = 'daytime_dimming' in request.form
                config_updates["WIND_ANIMATION"] = 'wind_animation' in request.form
                config_updates["LIGHTENING_ANIMATION"] = 'lightening_animation' in request.form
                config_updates["SNOWY_ANIMATION"] = 'snowy_animation' in request.form
                config_updates["ENABLE_HTTPS"] = 'enable_https' in request.form
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

                # Time Settings (convert from form input)
                config_updates["BRIGHT_TIME_START"] = f"datetime.time({request.form.get('bright_time_start_hour', 0)}, {request.form.get('bright_time_start_minute', 0)})"
                config_updates["DIM_TIME_START"] = f"datetime.time({request.form.get('dim_time_start_hour', 0)}, {request.form.get('dim_time_start_minute', 0)})"
                config_updates["LIGHTS_OFF_TIME"] = f"datetime.time({request.form.get('lights_off_time_hour', 0)}, {request.form.get('lights_off_time_minute', 0)})"
                config_updates["LIGHTS_ON_TIME"] = f"datetime.time({request.form.get('lights_on_time_hour', 0)}, {request.form.get('lights_on_time_minute', 0)})"

            except ValueError:
                raise ValueError("Could not update time settings: Please enter valid numbers for hours and minutes.")

            # Handle color inputs with GRB adjustment
            color_fields = {
                "VFR_COLOR": "vfr_color",
                "MVFR_COLOR": "mvfr_color",
                "IFR_COLOR": "ifr_color",
                "LIFR_COLOR": "lifr_color",
                "MISSING_COLOR": "missing_color",
                "LIGHTENING_COLOR": "lightening_color"
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

            # Boolean values for checkbox-based settings
            config_updates["WIND_ANIMATION"] = 'wind_animation' in request.form
            config_updates["LIGHTENING_ANIMATION"] = 'lightening_animation' in request.form
            config_updates["SNOWY_ANIMATION"] = 'snowy_animation' in request.form
            config_updates["DAYTIME_DIMMING"] = 'daytime_dimming' in request.form
            config_updates["ENABLE_LIGHTS_OFF"] = 'enable_lights_off' in request.form
            config_updates["LEGEND"] = 'legend' in request.form
            config_updates["ENABLE_HTTPS"] = 'enable_https' in request.form

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
            flash('Configuration updated successfully!', 'success')

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
        enable_https=config.ENABLE_HTTPS
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
        # Start the restart process in a separate thread
        threading.Thread(target=restart_service_thread).start()

        # Immediately return a success response to the client
        return jsonify({"message": "Settings service is restarting."}), 200
    except Exception as e:
        # Handle any exceptions and return a proper error response
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
        subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/weather.py'], check=True)
        flash('Weather Has Been Updated!', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Weather Update Has Failed... {str(e)}', 'danger')
    return redirect(url_for('edit_settings'))

@app.route('/scan-networks', methods=['GET'])
def scan_networks():
    import subprocess
    import logging

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
    import subprocess
    from flask import request, jsonify

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


@app.route('/check_for_updates', methods=['GET'])
def check_for_updates():
    try:
        # Fetch the latest information from the remote repository
        subprocess.run(['git', 'fetch'], cwd='/home/pi', check=True)

        # Check if there are differences between the local and remote branches
        result = subprocess.run(['git', 'status', '-uno'], cwd='/home/pi', capture_output=True, text=True)

        # Check for indicators that the branch is behind
        if ("Your branch is behind" in result.stdout or
                "have diverged" in result.stdout or
                "can be fast-forwarded" in result.stdout):
            return jsonify({"updates_available": True, "message": "Updates are available!"}), 200
        else:
            return jsonify({"updates_available": False, "message": "No updates available."}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to check for updates: {e.stderr}"}), 500

@app.route('/apply_updates', methods=['POST'])
def apply_updates():
    try:
        # Define paths
        project_dir = '/home/pi'
        backup_dir = os.path.join(project_dir, 'BACKUP')
        user_config_path = os.path.join(project_dir, 'config.py')
        repo_config_path = os.path.join(project_dir, 'config.py')

        # Step 1: Create backup
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'backup_{timestamp}')
        os.makedirs(backup_path, exist_ok=True)

        for filename in os.listdir(project_dir):
            if filename != 'airports.txt' and not filename.startswith('.') and filename != 'BACKUP':  
                source_path = os.path.join(project_dir, filename)
                destination_path = os.path.join(backup_path, filename)
                if os.path.isfile(source_path):
                    shutil.copy(source_path, destination_path)
                elif os.path.isdir(source_path):
                    shutil.copytree(source_path, destination_path)
        # Limit backups to 5
        existing_backups = sorted(
            [os.path.join(backup_dir, d) for d in os.listdir(backup_dir)],
            key=os.path.getmtime
        )
        while len(existing_backups) > 5:
            shutil.rmtree(existing_backups[0])
            existing_backups.pop(0)

        # Step 2: Pull updates from the repo
        subprocess.run(['git', 'fetch'], cwd=project_dir, check=True)
        # Get the current branch
        current_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=project_dir, text=True).strip()
        
        # Temporarily move airports.txt out of the way
        airports_path = os.path.join(project_dir, 'airports.txt')
        temp_airports_path = os.path.join(project_dir, 'airports.txt.tmp')
        os.rename(airports_path, temp_airports_path)
        
        # Use the current branch to reset
        subprocess.run(['git', 'reset', '--hard', f'origin/{current_branch}'], cwd=project_dir, check=True)
        
        # Move airports.txt back to its original location
        os.rename(temp_airports_path, airports_path)
        subprocess.run(['sudo', 'chown', '-R', 'pi:pi', '/home/pi'], check=True)
        # Step 3: Update config.py
        update_config(user_config_path, repo_config_path)

        # Step 4: Restart services
        subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)

        return jsonify({"message": "Updates applied successfully!"}), 200

    except FileNotFoundError as e:
        return jsonify({"error": f"Missing file during update: {str(e)}"}), 500
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Command failed: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

def update_config(user_config_path, repo_config_path):
    user_config = {}
    repo_config = {}

    # Load the user's config
    with open(user_config_path, 'r') as user_file:
        exec(user_file.read(), user_config)

    # Load the repo's config
    with open(repo_config_path, 'r') as repo_file:
        exec(repo_file.read(), repo_config)

    # Add any NEW keys from the repo config to the user config
    for key, value in repo_config.items():
        if key.isupper() and key not in user_config:  # Only add if key is missing
            user_config[key] = value

    # Write the updated user config back to the file
    with open(user_config_path, 'w') as user_file:
        user_file.write("import datetime\n\n")  # Add the import statement

        for key, value in user_config.items():
            if key.isupper():  # Write only configuration constants
                user_file.write(f"{key} = {repr(value)}\n")

if __name__ == '__main__':
    if ENABLE_HTTPS:
        app.run(
            host='0.0.0.0',
            port=443,  # Use port 443 for HTTPS
            ssl_context=(
                '/etc/ssl/certs/flask-selfsigned.crt',  # Replace with your certificate paths
                '/etc/ssl/private/flask-selfsigned.key'
            )
        )
    else:
        app.run(host='0.0.0.0', port=80, debug=False)
