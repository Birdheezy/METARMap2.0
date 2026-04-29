from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import subprocess
import os
import datetime
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
from scheduler_v2 import weather_update_lock, update_weather as scheduler_update_weather, calculate_sun_times
from led_test import test_leds, turn_off_leds, update_brightness
from config_manager import manager

# Import the update manager
from update_manager import (
    check_for_updates, 
    perform_update, 
    get_config_validation_status,
    validate_config_file,
    parse_config_file,
    write_config_file
)

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

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

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
        scheduler_update_weather()
        flash('Weather Has Been Updated!', 'success')
    except Exception as e:
        flash(f'Weather Update Has Failed... {str(e)}', 'danger')
    return redirect(url_for('edit_settings'))

@app.route('/update-weather', methods=['POST'])
def refresh_weather():
    try:
        scheduler_update_weather(force=True)
        return jsonify({'status': 'success', 'message': 'Weather update requested'})
    except Exception as e:
        app.logger.error(f"Error requesting weather update: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/leds/status', methods=['GET'])
def get_led_status():
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'metar.service'],
            capture_output=True, text=True
        )
        led_status = "on" if result.stdout.strip() == "active" else "off"
        return jsonify({"status": led_status}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "off", "error": str(e)}), 500

@app.route('/', methods=['GET', 'POST'])
def edit_settings():
    if request.method == 'POST':
        try:
            # Reload config to ensure we have latest before updating
            manager.load_config()
            
            # Extract and validate settings
            try:
                manager.set("PIXEL_PIN", int(request.form.get('pixel_pin', '')))
                manager.set("LEGEND", 'legend' in request.form)
                manager.set("ENABLE_LIGHTS_OFF", 'enable_lights_off' in request.form)
                manager.set("DAYTIME_DIMMING", 'daytime_dimming' in request.form)
                manager.set("WIND_ANIMATION", 'wind_animation' in request.form)
                manager.set("LIGHTENING_ANIMATION", 'lightening_animation' in request.form)
                manager.set("SNOWY_ANIMATION", 'snowy_animation' in request.form)
                manager.set("ENABLE_HTTPS", 'enable_https' in request.form)
                manager.set("UPDATE_WEATHER", 'update_weather' in request.form)
                manager.set("STALE_INDICATION", 'stale_indication' in request.form)
                manager.set("WIFI_INDICATION", 'wifi_indication' in request.form)
                
                # Legend item visibility settings
                manager.set("LEGEND_VFR", 'legend_vfr' in request.form)
                manager.set("LEGEND_MVFR", 'legend_mvfr' in request.form)
                manager.set("LEGEND_IFR", 'legend_ifr' in request.form)
                manager.set("LEGEND_LIFR", 'legend_lifr' in request.form)
                manager.set("LEGEND_SNOWY", 'legend_snowy' in request.form)
                manager.set("LEGEND_LIGHTNING", 'legend_lightning' in request.form)
                manager.set("LEGEND_WINDY", 'legend_windy' in request.form)
                manager.set("LEGEND_MISSING", 'legend_missing' in request.form)

                # Float or Integer Settings
                manager.set("BRIGHTNESS", float(request.form.get('brightness', 0)))
                manager.set("DIM_BRIGHTNESS", float(request.form.get('dim_brightness', 0)))
                manager.set("DAYTIME_DIM_BRIGHTNESS", float(request.form.get('daytime_dim_brightness', 0)))
                manager.set("WIND_THRESHOLD", int(request.form.get('wind_threshold', 0)))
                manager.set("WIND_FADE_TIME", float(request.form.get('wind_fade_time', 0)))
                manager.set("WIND_PAUSE", float(request.form.get('wind_pause', 0)))
                manager.set("ANIMATION_PAUSE", int(request.form.get('animation_pause', 0)))
                manager.set("LIGHTNING_FLASH_COUNT", int(request.form.get('lightning_flash_count', 0)))
                manager.set("SNOW_BLINK_COUNT", int(request.form.get('snow_blink_count', 0)))
                manager.set("SNOW_BLINK_PAUSE", float(request.form.get('snow_blink_pause', 0)))
                
                # Validation for Snow settings
                snowy_duration = float(request.form.get('snowy_animation_duration', 5.0))
                if not (1.0 <= snowy_duration <= 30.0): raise ValueError("Snowy Animation Duration must be between 1.0 and 30.0 seconds.")
                manager.set("SNOWY_ANIMATION_DURATION", snowy_duration)

                snow_cycle_min = float(request.form.get('snow_cycle_min_duration', 2.0))
                if not (0.5 <= snow_cycle_min <= 10.0): raise ValueError("Snow Cycle Min Duration must be between 0.5 and 10.0 seconds.")
                manager.set("SNOW_CYCLE_MIN_DURATION", snow_cycle_min)

                snow_cycle_max = float(request.form.get('snow_cycle_max_duration', 4.0))
                if not (1.0 <= snow_cycle_max <= 15.0): raise ValueError("Snow Cycle Max Duration must be between 1.0 and 15.0 seconds.")
                manager.set("SNOW_CYCLE_MAX_DURATION", snow_cycle_max)

                snow_offset = float(request.form.get('snow_start_offset_max', 1.0))
                if not (0.1 <= snow_offset <= 5.0): raise ValueError("Snow Start Offset Max must be between 0.1 and 5.0 seconds.")
                manager.set("SNOW_START_OFFSET_MAX", snow_offset)

                snow_min_bright = float(request.form.get('snow_min_brightness', 0.05))
                if not (0.01 <= snow_min_bright <= 0.5): raise ValueError("Snow Min Brightness must be between 0.01 and 0.5.")
                manager.set("SNOW_MIN_BRIGHTNESS", snow_min_bright)

                if snow_cycle_min >= snow_cycle_max:
                    raise ValueError("Snow Cycle Min Duration must be less than Snow Cycle Max Duration.")

                manager.set("NUM_STEPS", int(request.form.get('num_steps', 0)))
                manager.set("NUM_PIXELS", int(request.form.get('num_pixels', 0)))
                
                # Time Settings
                manager.set("BRIGHT_TIME_START", datetime.time(int(request.form.get('bright_time_start_hour', 0)), int(request.form.get('bright_time_start_minute', 0))))
                manager.set("DIM_TIME_START", datetime.time(int(request.form.get('dim_time_start_hour', 0)), int(request.form.get('dim_time_start_minute', 0))))
                manager.set("LIGHTS_OFF_TIME", datetime.time(int(request.form.get('lights_off_time_hour', 0)), int(request.form.get('lights_off_time_minute', 0))))
                manager.set("LIGHTS_ON_TIME", datetime.time(int(request.form.get('lights_on_time_hour', 0)), int(request.form.get('lights_on_time_minute', 0))))

                # Weather Update Interval
                minutes = float(request.form.get('weather_update_interval', 5))
                manager.set("WEATHER_UPDATE_INTERVAL", int(minutes * 60))

                manager.set("LED_COLOR_ORDER", request.form.get('led_color_order', 'GRB'))

            except ValueError as e:
                raise ValueError(f"Invalid input: {str(e)}")

            # Color fields
            color_fields = {
                'vfr_color': 'VFR_COLOR',
                'mvfr_color': 'MVFR_COLOR',
                'ifr_color': 'IFR_COLOR',
                'lifr_color': 'LIFR_COLOR',
                'missing_color': 'MISSING_COLOR',
                'lightening_color': 'LIGHTENING_COLOR',
                'snowy_color': 'SNOWY_COLOR',
                'stale_data_color': 'STALE_DATA_COLOR',
                'wifi_disconnected_color': 'WIFI_DISCONNECTED_COLOR'
            }

            for form_key, config_key in color_fields.items():
                if form_key in request.form:
                    rgb_color = request.form[form_key].lstrip('#')
                    r, g, b = int(rgb_color[0:2], 16), int(rgb_color[2:4], 16), int(rgb_color[4:6], 16)
                    manager.set(config_key, (r, g, b))

            # Animation sequence
            if 'animation_sequence' in request.form and request.form['animation_sequence']:
                sequence_list = request.form['animation_sequence'].split(',')
                manager.set("ANIMATION_ORDER", sequence_list)

            # Sunrise/sunset
            manager.set("USE_SUNRISE_SUNSET", 'use_sunrise_sunset' in request.form)
            if 'selected_city' in request.form and request.form['selected_city']:
                manager.set("SELECTED_CITY", request.form['selected_city'])
                
                if manager.get("USE_SUNRISE_SUNSET"):
                    try:
                        sunrise, sunset = calculate_sun_times(request.form['selected_city'])
                        if sunrise and sunset:
                            manager.set("BRIGHT_TIME_START", sunrise)
                            manager.set("DIM_TIME_START", sunset)
                    except Exception as e:
                        flash(f'Error calculating sun times: {str(e)}', 'warning')

            # Save configuration
            if manager.save_config():
                flash('Configuration updated successfully!', 'success')
            else:
                flash('Failed to save configuration.', 'danger')

            # Update airports.txt
            updated_airports = request.form.get("airports")
            if updated_airports is not None:
                with open('/home/pi/airports.txt', 'w') as f:
                    f.write(updated_airports)

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'An unexpected error occurred: {str(e)}', 'danger')

        return redirect(url_for('edit_settings'))

    # GET request - Prepare data for template
    config = manager.config
    
    # Helper for color display
    def led_to_hex(color_tuple):
        if config.get('LED_COLOR_ORDER') == 'GRB':
            g, r, b = color_tuple
            return '#{:02x}{:02x}{:02x}'.format(r, g, b)
        else:
            r, g, b = color_tuple
            return '#{:02x}{:02x}{:02x}'.format(r, g, b)

    # Prepare context
    context = {
        'config': config,
        'local_ip': get_local_ip(),
        'weather_last_modified': "Weather data not available",
        'weather_update_threshold': (config.get('WEATHER_UPDATE_INTERVAL', 300) / 60) * 2,
        'map_styles': {}
    }

    # Colors
    for key in ['VFR_COLOR', 'MVFR_COLOR', 'IFR_COLOR', 'LIFR_COLOR', 'MISSING_COLOR', 
                'LIGHTENING_COLOR', 'SNOWY_COLOR', 'STALE_DATA_COLOR', 'WIFI_DISCONNECTED_COLOR']:
        hex_color = led_to_hex(config.get(key, (0,0,0)))
        context[key.lower()] = hex_color
        if key != 'STALE_DATA_COLOR' and key != 'WIFI_DISCONNECTED_COLOR':
             context['map_styles'][key.lower()] = hex_color

    # Weather file time
    try:
        weather_file_path = '/home/pi/weather.json'
        if os.path.exists(weather_file_path):
            mtime = os.path.getmtime(weather_file_path)
            context['weather_last_modified'] = datetime.datetime.fromtimestamp(mtime).strftime('%m-%d-%Y %H:%M:%S')
    except Exception:
        pass

    # Airports
    try:
        with open('/home/pi/airports.txt', 'r') as f:
            context['airports'] = f.read()
    except:
        context['airports'] = ""

    # Pass individual config values that template expects directly
    # (Though we passed 'config' object, some might be accessed directly if template uses them)
    # The template uses {{ config.KEY }} mostly, but also some direct variables like {{ vfr_color }}
    
    # Add other specific variables used in template
    context.update({
        'bright_time_start_hour': config.get('BRIGHT_TIME_START').hour,
        'bright_time_start_minute': config.get('BRIGHT_TIME_START').minute,
        'dim_time_start_hour': config.get('DIM_TIME_START').hour,
        'dim_time_start_minute': config.get('DIM_TIME_START').minute,
        'lights_off_time_hour': config.get('LIGHTS_OFF_TIME').hour,
        'lights_off_time_minute': config.get('LIGHTS_OFF_TIME').minute,
        'lights_on_time_hour': config.get('LIGHTS_ON_TIME').hour,
        'lights_on_time_minute': config.get('LIGHTS_ON_TIME').minute,
        'enable_lights_off': config.get('ENABLE_LIGHTS_OFF'),
        'legend': config.get('LEGEND'),
        'enable_https': config.get('ENABLE_HTTPS'),
        'snowy_animation_duration': config.get('SNOWY_ANIMATION_DURATION'),
        'snow_cycle_min_duration': config.get('SNOW_CYCLE_MIN_DURATION'),
        'snow_cycle_max_duration': config.get('SNOW_CYCLE_MAX_DURATION'),
        'snow_start_offset_max': config.get('SNOW_START_OFFSET_MAX'),
        'snow_min_brightness': config.get('SNOW_MIN_BRIGHTNESS'),
        'use_sunrise_sunset': config.get('USE_SUNRISE_SUNSET'),
        'selected_city': config.get('SELECTED_CITY'),
        'cities': config.get('CITIES', []),
        'animation_order': config.get('ANIMATION_ORDER', ['WINDY', 'LIGHTNING', 'SNOWY']),
        'show_save_button': True,
        'now': datetime.datetime.now(),
        'weather_last_modified_dt': datetime.datetime.fromtimestamp(os.path.getmtime('/home/pi/weather.json')) if os.path.exists('/home/pi/weather.json') else None
    })

    return render_template('settings_v2.html', **context)

# ... (Include other routes like restart_metar, scan_networks, etc. - copying them as is)
# For brevity, I'll assume I need to copy the rest of the functions too.
# I will add them in a second pass or just include them here if I can fit them.

@app.route('/restart_metar')
def restart_metar():
    try:
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
    try:
        time.sleep(2)
        subprocess.run(['sudo', 'systemctl', 'restart', 'settings.service'], check=True)
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
        <style>body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }</style>
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
        subprocess.run(['sudo', 'systemctl', 'stop', 'metar.service'], check=True)
        subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'], check=True)
        flash('METAR service stopped and LEDs blanked!', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Error stopping METAR service or blanking LEDs: {str(e)}', 'danger')
    return redirect(url_for('edit_settings'))

@app.route('/scan-networks', methods=['GET'])
def scan_networks():
    try:
        result = subprocess.run(
            ['nmcli', '-t', '-f', 'SSID,SIGNAL', 'dev', 'wifi', 'list'],
            capture_output=True, text=True, check=True
        )
        networks = {}
        for line in result.stdout.splitlines():
            parts = line.split(':')
            if len(parts) >= 2 and parts[0].strip():
                ssid, signal = parts[0], parts[1]
                signal = int(signal)
                if ssid not in networks or networks[ssid] < signal:
                    networks[ssid] = signal
        sorted_networks = sorted(
            [{'ssid': ssid, 'signal': str(signal)} for ssid, signal in networks.items()],
            key=lambda x: int(x['signal']), reverse=True
        )
        return {'networks': sorted_networks}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/connect-to-network', methods=['POST'])
def connect_to_network():
    data = request.get_json()
    ssid = data.get('ssid')
    password = data.get('password')
    if not ssid: return jsonify({'success': False, 'error': 'SSID is required.'}), 400
    try:
        command = ['nmcli', 'dev', 'wifi', 'connect', ssid]
        if password: command.extend(['password', password])
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0: return jsonify({'success': True})
        else: return jsonify({'success': False, 'error': result.stderr.strip()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/service/status/<service_name>', methods=['GET'])
def get_service_status(service_name):
    try:
        result = subprocess.run(['systemctl', 'is-active', f'{service_name}.service'], capture_output=True, text=True)
        status = result.stdout.strip()
        return jsonify({"status": "running" if status == "active" else "stopped", "message": f"Service is {status}"})
    except Exception as e:
        return jsonify({"status": "unknown", "message": str(e)}), 500

@app.route('/service/control/<service_name>/<action>', methods=['POST'])
def control_service(service_name, action):
    if action not in ['start', 'stop', 'restart']: return jsonify({"error": "Invalid action"}), 400
    try:
        if service_name == 'settings' and action == 'restart':
            response = jsonify({"message": "Settings service restart initiated", "status": "restarting", "special_case": "settings_restart"})
            response.headers['Connection'] = 'close'
            threading.Thread(target=lambda: (time.sleep(1), subprocess.run(['sudo', 'systemctl', 'restart', 'settings.service'], check=True))).start()
            return response
        elif service_name == 'metar' and action == 'stop':
            subprocess.run(['sudo', 'systemctl', 'stop', 'metar.service'], check=True)
            subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'], check=True)
        else:
            subprocess.run(['sudo', 'systemctl', action, f'{service_name}.service'], check=True)
        return jsonify({"message": f"Service {action} successful", "status": "running" if action in ['start', 'restart'] else "stopped"})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to {action} service: {str(e)}"}), 500

@app.route('/service/logs/<service_name>', methods=['GET'])
def get_service_logs(service_name):
    try:
        result = subprocess.run(['sudo', 'journalctl', '-u', f'{service_name}.service', '-n', '200', '-o', 'short', '--no-pager', '--no-hostname'], capture_output=True, text=True, check=True)
        return jsonify({"logs": result.stdout if result.stdout else "No logs available", "success": True})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/weather-status')
def weather_status():
    try:
        weather_file = '/home/pi/weather.json'
        if os.path.exists(weather_file):
            last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(weather_file))
            formatted_date = last_modified.strftime('%m-%d-%Y %H:%M:%S')
            is_stale = (datetime.datetime.now() - last_modified).total_seconds() > (manager.get('WEATHER_UPDATE_INTERVAL', 300) * 2)
            return jsonify({'last_updated': formatted_date, 'is_stale': is_stale})
        return jsonify({'last_updated': 'Never', 'is_stale': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update-weather', methods=['POST'])
def update_weather_manual():
    try:
        # Run the weather update script
        # Using the same python interpreter as the system
        subprocess.run(['/usr/bin/python3', '/home/pi/weather_v2.py'], check=True)
        return jsonify({"success": True, "message": "Weather update triggered successfully!"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": f"Failed to update weather: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

@app.route('/shutdown', methods=['POST'])
def shutdown_system():
    try:
        subprocess.run(['sudo', 'shutdown', 'now'], check=True)
        return jsonify({"success": True, "message": "System is shutting down..."})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/restart', methods=['POST'])
def restart_system():
    try:
        subprocess.run(['sudo', 'reboot'], check=True)
        return jsonify({"success": True, "message": "System is rebooting..."})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    ssl_context = None
    if manager.get('ENABLE_HTTPS'):
        try:
            import OpenSSL
            ssl_context = 'adhoc'
            print("HTTPS Enabled (adhoc)")
        except ImportError:
            print("pyOpenSSL not installed, falling back to HTTP despite ENABLE_HTTPS=True")
            ssl_context = None

    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=ssl_context)
