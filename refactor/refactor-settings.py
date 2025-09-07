from flask import Flask, render_template, request, jsonify
import os
import sys
import json
from config import *

# Add the parent directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Handle form submission and save to config.py
        try:
            # Get form data
            brightness = float(request.form.get('brightness', config.BRIGHTNESS))
            daytime_dim_brightness = float(request.form.get('daytime_dim_brightness', config.DAYTIME_DIM_BRIGHTNESS))
            dim_brightness = float(request.form.get('dim_brightness', config.DIM_BRIGHTNESS))
            
            # Update config values
            BRIGHTNESS = brightness
            DAYTIME_DIM_BRIGHTNESS = daytime_dim_brightness
            DIM_BRIGHTNESS = dim_brightness
            
            # Save to config.py file
            save_config_to_file()
            
            return jsonify({'success': True, 'message': 'Settings saved successfully!'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error saving settings: {str(e)}'})
    
    # Convert RGB tuples to hex colors for the template
    def rgb_to_hex(rgb_tuple):
        return f"#{rgb_tuple[0]:02x}{rgb_tuple[1]:02x}{rgb_tuple[2]:02x}"
    
    colors = {
        'vfr_color': rgb_to_hex(VFR_COLOR),
        'mvfr_color': rgb_to_hex(MVFR_COLOR),
        'ifr_color': rgb_to_hex(IFR_COLOR),
        'lifr_color': rgb_to_hex(LIFR_COLOR),
        'lightening_color': rgb_to_hex(LIGHTENING_COLOR),
        'snowy_color': rgb_to_hex(SNOWY_COLOR),
        'missing_color': rgb_to_hex(MISSING_COLOR),
        'stale_data_color': rgb_to_hex(STALE_DATA_COLOR),
        'wifi_disconnected_color': rgb_to_hex(WIFI_DISCONNECTED_COLOR)
    }
    
    # Read airports from airports.txt
    airports_content = ""
    try:
        airports_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), AIRPORTS_FILE)
        with open(airports_path, 'r') as f:
            airports_content = f.read().strip()
    except FileNotFoundError:
        airports_content = "KJFK\nKLAX\nKORD\nKHOU\nKPHX"  # Fallback
    
    # Get local IP address
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "192.168.1.100"  # Fallback
    
    # Get weather last modified (this would need to be implemented based on your weather data)
    weather_last_modified = "2024-01-01 12:00:00"  # Placeholder - needs actual implementation
    
    return render_template('refactor-settings.html',
                         config=locals(),  # Pass all local variables as config
                         cities=CITIES,
                         selected_city=SELECTED_CITY,
                         airports=airports_content,
                         weather_last_modified=weather_last_modified,
                         local_ip=local_ip,
                         **colors)

def save_config_to_file():
    """Save current config values back to config.py file"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')
        
        # Read the current config.py file
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Update the specific values we're changing
        content = update_config_value(content, 'BRIGHTNESS', BRIGHTNESS)
        content = update_config_value(content, 'DAYTIME_DIM_BRIGHTNESS', DAYTIME_DIM_BRIGHTNESS)
        content = update_config_value(content, 'DIM_BRIGHTNESS', DIM_BRIGHTNESS)
        
        # Write back to file
        with open(config_path, 'w') as f:
            f.write(content)
            
        print(f"Config saved to {config_path}")
        
    except Exception as e:
        print(f"Error saving config: {e}")
        raise

def update_config_value(content, key, value):
    """Update a specific config value in the config.py content"""
    import re
    
    # Handle different value types
    if isinstance(value, bool):
        value_str = str(value)
    elif isinstance(value, str):
        value_str = f"'{value}'"
    else:
        value_str = str(value)
    
    # Pattern to match: KEY = value
    pattern = rf"^{key}\s*=\s*.*$"
    replacement = f"{key} = {value_str}"
    
    # Replace the line
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if re.match(pattern, line.strip()):
            lines[i] = replacement
            break
    
    return '\n'.join(lines)

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
