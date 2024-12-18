import os
import schedule
import time
import subprocess
from datetime import datetime
import importlib  # For reloading the config module
import config  # Import config for dynamic updates

def turn_on_lights():
    """Restart the metar.service to turn on the lights."""
    try:
        subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/weather.py'], check=True)
        time.sleep(2)
        subprocess.run(['systemctl', 'start', 'metar.service'], check=True)
        print("Lights turned on: METAR service started.")
    except subprocess.CalledProcessError as e:
        print(f"Error turning on lights: {e}")


def turn_off_lights():
    """Stop the metar.service and run blank.py to turn off the lights."""
    try:
        subprocess.run(['systemctl', 'stop', 'metar.service'], check=True)
        time.sleep(2)
        subprocess.run(["sudo", "/home/pi/metar/bin/python3", "/home/pi/blank.py"], check=True)
        print("Lights turned off: METAR service stopped and LEDs blanked.")
    except subprocess.CalledProcessError as e:
        print(f"Error turning off lights: {e}")


def update_weather():
    """Run the weather update script."""
    try:
        subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/weather.py'], check=True)
        print("Weather data updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error updating weather data: {e}")

def schedule_weather_updates():
    """Schedule weather updates based on the configured interval."""
    schedule.every(config.WEATHER_UPDATE_INTERVAL).seconds.do(update_weather)
    print(f"Scheduled weather updates every {config.WEATHER_UPDATE_INTERVAL} seconds.")

def schedule_lights():
    """Schedule lights on/off based on the current configuration."""
    schedule.clear()  # Clear existing schedules

    # Only schedule weather updates if enabled in config
    if config.UPDATE_WEATHER:
        schedule_weather_updates()
        print("Weather updates are enabled.")
    else:
        print("Weather updates are disabled in settings.")

    # Dynamically fetch updated values from the config module
    if config.ENABLE_LIGHTS_OFF:
        # Schedule lights on
        on_time = f"{config.LIGHTS_ON_TIME.hour:02}:{config.LIGHTS_ON_TIME.minute:02}"
        schedule.every().day.at(on_time).do(turn_on_lights)
        print(f"Scheduled lights on at {on_time}.")

        # Schedule lights off
        off_time = f"{config.LIGHTS_OFF_TIME.hour:02}:{config.LIGHTS_OFF_TIME.minute:02}"
        schedule.every().day.at(off_time).do(turn_off_lights)
        print(f"Scheduled lights off at {off_time}.")
    else:
        print("Lights scheduling is disabled.")


def monitor_config_changes(config_file):
    """Monitor config.py for changes and reload schedules dynamically."""
    last_modified = os.path.getmtime(config_file)
    last_check = time.time()

    while True:
        current_time = time.time()
        
        # Run scheduled tasks every second
        schedule.run_pending()
        
        # Check for config changes every few seconds
        if current_time - last_check >= 5:  # Check config file every 5 seconds
            current_modified = os.path.getmtime(config_file)
            if current_modified != last_modified:
                print("Detected config.py changes. Reloading schedules...")
                last_modified = current_modified
                
                # Reload the config module to get updated values
                importlib.reload(config)
                
                # Reschedule with the updated values
                schedule_lights()

                # Handle lights state after config change
                if config.ENABLE_LIGHTS_OFF:
                    current_time = datetime.now().time()
                    lights_off = (
                        (config.LIGHTS_OFF_TIME > config.LIGHTS_ON_TIME and (current_time >= config.LIGHTS_OFF_TIME or current_time < config.LIGHTS_ON_TIME)) or
                        (config.LIGHTS_OFF_TIME <= config.LIGHTS_ON_TIME and config.LIGHTS_OFF_TIME <= current_time < config.LIGHTS_ON_TIME)
                    )
                    if lights_off:
                        turn_off_lights()
                    else:
                        turn_on_lights()
            
            last_check = current_time
        
        time.sleep(1)  # Sleep for 1 second between checks


if __name__ == "__main__":
    # Monitor config changes and run scheduler
    config_file = "/home/pi/config.py"
    schedule_lights()
    monitor_config_changes(config_file)
