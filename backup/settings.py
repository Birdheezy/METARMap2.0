from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
import os
from config import *  # Import all variables from config.py
import datetime

app = Flask(__name__)

# Set a secret key for session management (needed for flashing messages)
app.secret_key = os.urandom(24)

# Helper function to reload config values
def reload_config():
    global BRIGHTNESS, DIM_BRIGHTNESS, BRIGHT_TIME_START, DIM_TIME_START
    global WIND_THRESHOLD, WIND_FADE_TIME, WIND_PAUSE, ANIMATION_PAUSE
    global NUM_STEPS, SNOW_BLINK_COUNT, SNOW_BLINK_PAUSE
    global WIND_ANIMATION, LIGHTENING_ANIMATION, SNOWY_ANIMATION
    global VFR_COLOR, MVFR_COLOR, IFR_COLOR, LIFR_COLOR, MISSING_COLOR, LIGHTENING_COLOR

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

reload_config()

@app.route('/', methods=['GET', 'POST'])
def edit_settings():
    if request.method == 'POST':
        try:
            # Get time values from the form input
            bright_hour = int(request.form['bright_time_start_hour'])
            bright_minute = int(request.form['bright_time_start_minute'])
            dim_hour = int(request.form['dim_time_start_hour'])
            dim_minute = int(request.form['dim_time_start_minute'])

            # Convert time inputs to datetime.time format
            bright_time_start = f"datetime.time({bright_hour}, {bright_minute:02d})"
            dim_time_start = f"datetime.time({dim_hour}, {dim_minute:02d})"
            
            # Save the settings, including time settings in the correct format
            config_updates = {
                "BRIGHT_TIME_START": bright_time_start,
                "DIM_TIME_START": dim_time_start,
                "BRIGHTNESS": float(request.form['brightness']),
                "DIM_BRIGHTNESS": float(request.form['dim_brightness']),
                "WIND_THRESHOLD": int(request.form['wind_threshold']),
                "WIND_FADE_TIME": float(request.form['wind_fade_time']),
                "WIND_PAUSE": float(request.form['wind_pause']),
                "ANIMATION_PAUSE": float(request.form['animation_pause']),
                "NUM_STEPS": int(request.form['num_steps']),
                "SNOW_BLINK_COUNT": int(request.form['snow_blink_count']),
                "SNOW_BLINK_PAUSE": float(request.form['snow_blink_pause']),
                "WIND_ANIMATION": 'wind_animation' in request.form,
                "LIGHTENING_ANIMATION": 'lightening_animation' in request.form,
                "SNOWY_ANIMATION": 'snowy_animation' in request.form,
            }

            # Update the config.py file
            with open('/home/pi/config.py', 'r') as f:
                config_lines = f.readlines()

            with open('/home/pi/config.py', 'w') as f:
                for line in config_lines:
                    updated = False
                    for key, value in config_updates.items():
                        if line.startswith(key):
                            f.write(f"{key} = {value}\n")  # Write the formatted time values
                            updated = True
                            break
                    if not updated:
                        f.write(line)

            reload_config()  # Reload the updated values
            flash('Configuration updated successfully!', 'success')
        except Exception as e:
            flash(f'Error updating configuration: {str(e)}', 'danger')

    # Load the airport list from airports.txt
    with open('/home/pi/airports.txt', 'r') as f:
        airports = f.read()

    return render_template('settings.html', config=globals(), airports=airports)

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
        subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'], check=True)  # Assuming 'blank' is the correct alias for blanking LEDs
        flash('METAR service stopped and LEDs blanked!', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Error stopping METAR service or blanking LEDs: {str(e)}', 'danger')

    return redirect(url_for('edit_settings'))

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
