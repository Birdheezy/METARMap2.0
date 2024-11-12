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


app = Flask(__name__)
app.secret_key = os.urandom(24)

# Helper function to reload config values
def reload_config():
    global BRIGHTNESS, DIM_BRIGHTNESS, BRIGHT_TIME_START, DIM_TIME_START
    global WIND_THRESHOLD, WIND_FADE_TIME, WIND_PAUSE, ANIMATION_PAUSE
    global NUM_STEPS, SNOW_BLINK_COUNT, SNOW_BLINK_PAUSE
    global WIND_ANIMATION, LIGHTENING_ANIMATION, SNOWY_ANIMATION
    global VFR_COLOR, MVFR_COLOR, IFR_COLOR, LIFR_COLOR, MISSING_COLOR, LIGHTENING_COLOR
    global DAYTIME_DIMMING, DAYTIME_DIM_BRIGHTNESS, ENABLE_LIGHTS_OFF
    global LIGHTS_OFF_TIME, LIGHTS_ON_TIME

    # Use exec to load the latest values from config.py
    config_globals = {}
    with open('/home/pi/config.py') as f:
        exec(f.read(), config_globals)

    # Update global values from the loaded config
    BRIGHTNESS = config_globals['BRIGHTNESS']
    DIM_BRIGHTNESS = config_globals['DIM_BRIGHTNESS']
    BRIGHT_TIME_START = config_globals['BRIGHT_TIME_START']
    DIM_TIME_START = config_globals['DIM_TIME_START']
    WIND_THRESHOLD = config_globals['WIND_THRESHOLD']
    WIND_FADE_TIME = config_globals['WIND_FADE_TIME']
    WIND_PAUSE = config_globals['WIND_PAUSE']
    ANIMATION_PAUSE = config_globals['ANIMATION_PAUSE']
    NUM_STEPS = config_globals['NUM_STEPS']
    SNOW_BLINK_COUNT = config_globals['SNOW_BLINK_COUNT']
    SNOW_BLINK_PAUSE = config_globals['SNOW_BLINK_PAUSE']
    WIND_ANIMATION = config_globals['WIND_ANIMATION']
    LIGHTENING_ANIMATION = config_globals['LIGHTENING_ANIMATION']
    SNOWY_ANIMATION = config_globals['SNOWY_ANIMATION']
    VFR_COLOR = config_globals['VFR_COLOR']
    MVFR_COLOR = config_globals['MVFR_COLOR']
    IFR_COLOR = config_globals['IFR_COLOR']
    LIFR_COLOR = config_globals['LIFR_COLOR']
    MISSING_COLOR = config_globals['MISSING_COLOR']
    LIGHTENING_COLOR = config_globals['LIGHTENING_COLOR']
    DAYTIME_DIMMING = config_globals.get('DAYTIME_DIMMING')
    DAYTIME_DIM_BRIGHTNESS = config_globals.get('DAYTIME_DIM_BRIGHTNESS')
    LIGHTS_OFF_TIME = config_globals['LIGHTS_OFF_TIME']
    LIGHTS_ON_TIME = config_globals['LIGHTS_ON_TIME']
    ENABLE_LIGHTS_OFF = config_globals['ENABLE_LIGHTS_OFF']

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
                bright_time_start_hour = int(request.form['bright_time_start_hour'])
                bright_time_start_minute = int(request.form['bright_time_start_minute'])
                dim_time_start_hour = int(request.form['dim_time_start_hour'])
                dim_time_start_minute = int(request.form['dim_time_start_minute'])
                lights_off_time_hour = int(request.form['lights_off_time_hour'])
                lights_off_time_minute = int(request.form['lights_off_time_minute'])
                lights_on_time_hour = int(request.form['lights_on_time_hour'])
                lights_on_time_minute = int(request.form['lights_on_time_minute'])
                
                # Convert the time inputs into datetime.time format
                config_updates["BRIGHT_TIME_START"] = f"datetime.time({bright_time_start_hour}, {bright_time_start_minute})"
                config_updates["DIM_TIME_START"] = f"datetime.time({dim_time_start_hour}, {dim_time_start_minute})"
                config_updates["LIGHTS_OFF_TIME"] = f"datetime.time({lights_off_time_hour}, {lights_off_time_minute})"
                config_updates["LIGHTS_ON_TIME"] = f"datetime.time({lights_on_time_hour}, {lights_on_time_minute})"
            except ValueError:
                raise ValueError("Could not update time settings: Please enter valid numbers for hours and minutes.")

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

            # Boolean values for checkbox-based settings
            config_updates["WIND_ANIMATION"] = 'wind_animation' in request.form
            config_updates["LIGHTENING_ANIMATION"] = 'lightening_animation' in request.form
            config_updates["SNOWY_ANIMATION"] = 'snowy_animation' in request.form
            config_updates["DAYTIME_DIMMING"] = 'daytime_dimming' in request.form
            config_updates["ENABLE_LIGHTS_OFF"] = 'enable_lights_off' in request.form

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

    # Get the last modified date of weather.json
    weather_file_path = '/home/pi/weather.json'  # Adjust this path if necessary
    try:
        last_modified_timestamp = os.path.getmtime(weather_file_path)
        weather_last_modified = datetime.datetime.fromtimestamp(last_modified_timestamp).strftime('%Y-%m-%d %H:%M:%S')
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
        config=globals(),  # Pass the entire config if needed for other settings
        weather_last_modified=weather_last_modified  # Pass the last modified date to the template
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

        if "Your branch is behind" in result.stdout:
            return jsonify({"updates_available": True, "message": "Updates are available!"}), 200
        else:
            return jsonify({"updates_available": False, "message": "No updates available."}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to check for updates: {str(e)}"}), 500


def merge_configs(user_config_path, template_config_path):
    # Load the template config lines to get the correct structure and order
    with open(template_config_path, 'r') as template_file:
        template_lines = template_file.readlines()

    # Load the user's config into a dictionary to preserve their changes
    user_config = {}
    with open(user_config_path, 'r') as user_file:
        for line in user_file:
            line = line.strip()
            if line.startswith("#") or not line or line.startswith("import"):
                continue  # Skip comments, empty lines, and import statements

            # Extract key and value using regex
            match = re.match(r'^(\w+)\s*=\s*(.+)$', line)
            if match:
                key, value = match.groups()
                user_config[key.strip()] = value.strip()

    # Create the updated config content by using the structure of the template
    updated_lines = []
    for line in template_lines:
        stripped_line = line.strip()

        if stripped_line.startswith("#") or not stripped_line or stripped_line.startswith("import"):
            # Preserve comments, empty lines, and import statements from the template
            updated_lines.append(line)
            continue

        # Extract key from the template line
        match = re.match(r'^(\w+)\s*=', stripped_line)
        if match:
            key = match.group(1).strip()
            # Use the user's value if it exists, otherwise keep the template's value
            if key in user_config:
                updated_lines.append(f"{key} = {user_config[key]}\n")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Write the updated configuration back to user config.py
    with open(user_config_path, 'w') as user_file:
        user_file.writelines(updated_lines)


@app.route('/pull_updates', methods=['GET'])
def pull_updates():
    try:
        # Define the project directory and backup directory
        project_dir = '/home/pi'
        backup_dir = os.path.join(project_dir, '*BACKUP*')

        # Set a limit for the number of backups to retain
        MAX_BACKUPS = 5

        # Create a timestamped backup directory to keep multiple backups
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'backup_{timestamp}')
        
        # Create the backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Get the list of files from the GitHub repo
        result = subprocess.run(
            ['git', 'ls-tree', '-r', 'HEAD', '--name-only'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True
        )

        # Split the output into individual file paths
        files_in_repo = result.stdout.strip().split('\n')

        # Create the specific backup folder
        os.makedirs(backup_path, exist_ok=True)

        # Copy each file to the backup folder
        for item in files_in_repo:
            item_path = os.path.join(project_dir, item)
            if os.path.exists(item_path):
                if os.path.isdir(item_path):
                    shutil.copytree(item_path, os.path.join(backup_path, os.path.basename(item)), dirs_exist_ok=True)
                else:
                    shutil.copy2(item_path, backup_path)

        # Delete old backups if they exceed the limit
        existing_backups = sorted(
            [os.path.join(backup_dir, d) for d in os.listdir(backup_dir)],
            key=os.path.getmtime
        )

        while len(existing_backups) > MAX_BACKUPS:
            shutil.rmtree(existing_backups[0])
            existing_backups.pop(0)

        # Pull the latest updates from the remote repository
        subprocess.run(['git', 'pull'], cwd=project_dir, check=True)

        # Merge the configuration files after pulling updates
        user_config_path = os.path.join(project_dir, 'config.py')
        template_config_path = os.path.join(project_dir, 'config_template.py')
        merge_configs(user_config_path, template_config_path)

        return jsonify({"success": True, "message": f"Update successful! Backup created at {backup_path}"}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": f"Failed to pull updates: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": f"An error occurred during backup or update: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=443,  # Use port 443 for HTTPS
        ssl_context=(
            '/etc/ssl/certs/flask-selfsigned.crt',
            '/etc/ssl/private/flask-selfsigned.key'
        )
    )

#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=80, debug=False)
