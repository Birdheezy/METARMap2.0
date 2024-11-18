import os
import schedule
import time
import subprocess
from datetime import datetime  # Fix for the error
from config import ENABLE_LIGHTS_OFF, LIGHTS_ON_TIME, LIGHTS_OFF_TIME


def turn_on_lights():
    """Restart the metar.service to turn on the lights."""
    try:
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


def schedule_lights():
    """Schedule lights on/off based on the current configuration."""
    schedule.clear()

    if ENABLE_LIGHTS_OFF:
        # Schedule lights on
        on_time = f"{LIGHTS_ON_TIME.hour:02}:{LIGHTS_ON_TIME.minute:02}"
        schedule.every().day.at(on_time).do(turn_on_lights)
        print(f"Scheduled lights on at {on_time}.")

        # Schedule lights off
        off_time = f"{LIGHTS_OFF_TIME.hour:02}:{LIGHTS_OFF_TIME.minute:02}"
        schedule.every().day.at(off_time).do(turn_off_lights)
        print(f"Scheduled lights off at {off_time}.")
    else:
        print("Lights scheduling is disabled.")


def monitor_config_changes(config_file):
    """Monitor config.py for changes and reload schedules dynamically."""
    last_modified = os.path.getmtime(config_file)

    while True:
        current_modified = os.path.getmtime(config_file)
        if current_modified != last_modified:
            print("Detected config.py changes. Reloading schedules...")
            last_modified = current_modified
            from config import ENABLE_LIGHTS_OFF, LIGHTS_ON_TIME, LIGHTS_OFF_TIME
            schedule_lights()

            # If the current time falls in the lights-off period, turn off lights immediately
            current_time = datetime.now().time()  # Fixed the error here
            if ENABLE_LIGHTS_OFF and (
                (LIGHTS_OFF_TIME > LIGHTS_ON_TIME and (current_time >= LIGHTS_OFF_TIME or current_time < LIGHTS_ON_TIME)) or
                (LIGHTS_OFF_TIME <= LIGHTS_ON_TIME and LIGHTS_OFF_TIME <= current_time < LIGHTS_ON_TIME)
            ):
                turn_off_lights()

        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    # Monitor config changes and run scheduler
    config_file = "/home/pi/config.py"
    schedule_lights()
    monitor_config_changes(config_file)
