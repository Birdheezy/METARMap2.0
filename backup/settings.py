from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
import os

# Load the config module dynamically
def reload_config():
    import config
    import importlib
    importlib.reload(config)
    return config

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

@app.route('/', methods=['GET', 'POST'])
def edit_settings():
    config = reload_config()  # Load the current config at the start

    if request.method == 'POST':
        # Get form values for brightness, time settings, and animation settings
        brightness = request.form.get('brightness')
        dim_brightness = request.form.get('dim_brightness')
        bright_time_start_hour = int(request.form.get('bright_time_start_hour'))
        bright_time_start_minute = int(request.form.get('bright_time_start_minute'))
        dim_time_start_hour = int(request.form.get('dim_time_start_hour'))
        dim_time_start_minute = int(request.form.get('dim_time_start_minute'))

        # Create datetime.time objects
        bright_time_start = datetime.time(bright_time_start_hour, bright_time_start_minute)
        dim_time_start = datetime.time(dim_time_start_hour, dim_time_start_minute)

        # Validate and update config.py
        with open('config.py', 'r') as file:
            lines = file.readlines()

        with open('config.py', 'w') as file:
            for line in lines:
                if line.startswith('BRIGHTNESS'):
                    file.write(f'BRIGHTNESS = {brightness}\n')
                elif line.startswith('DIM_BRIGHTNESS'):
                    file.write(f'DIM_BRIGHTNESS = {dim_brightness}\n')
                elif line.startswith('BRIGHT_TIME_START'):
                    file.write(f'BRIGHT_TIME_START = datetime.time({bright_time_start_hour}, {bright_time_start_minute})\n')
                elif line.startswith('DIM_TIME_START'):
                    file.write(f'DIM_TIME_START = datetime.time({dim_time_start_hour}, {dim_time_start_minute})\n')
                else:
                    file.write(line)

        flash('Configuration updated successfully!', 'success')
        return redirect(url_for('edit_settings'))

    config = reload_config()  # Reload updated config after saving
    with open('airports.txt', 'r') as file:
        airports = file.read()

    return render_template('settings.html', config=config, airports=airports)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
