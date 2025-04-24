import os
import schedule
import time
import subprocess
from datetime import datetime
import importlib  # For reloading the config module
import config  # Import config for dynamic updates
import logging
import threading
import weather  # Import weather module directly
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Only include the message, let journald handle the timestamp
)

logger = logging.getLogger(__name__)

# Create a lock for weather updates
weather_update_lock = threading.Lock()

def turn_on_lights():
    """Restart the metar.service to turn on the lights."""
    try:
        subprocess.run(['systemctl', 'start', 'metar.service'], check=True)
        logger.info("Lights turned on: METAR service started.")
        # Schedule an immediate weather update when lights turn on
        update_weather()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error turning on lights: {e}")


def turn_off_lights():
    """Stop the metar.service and run blank.py to turn off the lights."""
    try:
        subprocess.run(['systemctl', 'stop', 'metar.service'], check=True)
        time.sleep(2)
        subprocess.run(["sudo", "/home/pi/metar/bin/python3", "/home/pi/blank.py"], check=True)
        logger.info("Lights turned off: METAR service stopped and LEDs blanked.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error turning off lights: {e}")


def is_metar_running():
    """Check if METAR service is running.
    Returns:
        bool: True if service is running, False otherwise
    """
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'metar.service'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == "active"
    except subprocess.CalledProcessError:
        return False

def update_weather(force=False):
    """Update weather data directly using the weather module."""
    global weather_update_lock
    
    if not weather_update_lock.acquire(blocking=False):
        logger.info("Weather update already in progress, skipping...")
        return
        
    try:
        if not force and not is_metar_running():
            logger.info("Skipping weather update - METAR service is not running.")
            return
        
        logger.info("Fetching new weather data...")
        # Call weather module functions directly instead of running as a subprocess
        metar_data = weather.fetch_metar()
        if metar_data:
            parsed_data = weather.parse_weather(metar_data)
            if parsed_data:
                # Save the weather data
                with open('/home/pi/weather.json', 'w') as json_file:
                    json.dump(parsed_data, json_file, indent=4)
                logger.info("Weather data updated successfully")
            else:
                logger.error("Failed to parse weather data")
        else:
            logger.error("Failed to fetch weather data")
    finally:
        weather_update_lock.release()

def schedule_lights():
    """Schedule lights on/off and weather updates based on the current configuration."""
    # Clear all existing schedules
    schedule.clear()

    # Only schedule weather updates if enabled in config
    if config.UPDATE_WEATHER:
        # Schedule regular weather updates
        schedule.every(config.WEATHER_UPDATE_INTERVAL).seconds.do(update_weather)
        logger.info(f"Scheduled weather updates every {config.WEATHER_UPDATE_INTERVAL} seconds")
        # Run an immediate update when scheduling is set up
        update_weather()
    else:
        logger.info("Weather updates are disabled in settings")

    # Schedule lights on/off if enabled
    if config.ENABLE_LIGHTS_OFF:
        on_time = f"{config.LIGHTS_ON_TIME.hour:02}:{config.LIGHTS_ON_TIME.minute:02}"
        schedule.every().day.at(on_time).do(turn_on_lights)
        logger.info(f"Scheduled lights on at {on_time}")

        off_time = f"{config.LIGHTS_OFF_TIME.hour:02}:{config.LIGHTS_OFF_TIME.minute:02}"
        schedule.every().day.at(off_time).do(turn_off_lights)
        logger.info(f"Scheduled lights off at {off_time}")
    else:
        logger.info("Lights scheduling is disabled")


def monitor_config_changes(config_file):
    """Monitor config.py for changes and reload schedules dynamically."""
    last_modified = os.path.getmtime(config_file)
    last_check = time.time()  # Initialize with timestamp
    last_service_status = is_metar_running()  # Initial service status

    while True:
        current_time = time.time()  # Get current timestamp
        
        # Run scheduled tasks every second
        schedule.run_pending()
        
        # Check METAR service status
        current_status = is_metar_running()
        if current_status != last_service_status:
            last_service_status = current_status
            if current_status:
                logger.info("METAR service is now running, rescheduling updates...")
                schedule_lights()  # This will schedule weather updates if enabled
            else:
                logger.info("METAR service has stopped, weather updates will be skipped.")
        
        # Check for config changes every few seconds
        if current_time - last_check >= 5:
            current_modified = os.path.getmtime(config_file)
            if current_modified != last_modified:
                logger.info("Detected config.py changes. Reloading schedules and restarting METAR service...")
                last_modified = current_modified
                
                # Reload the config module to get updated values
                importlib.reload(config)
                
                # Restart the METAR service to apply all config changes
                try:
                    subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)
                    logger.info("METAR service restarted successfully")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error restarting METAR service: {e}")
                
                # Reschedule with the updated values
                schedule_lights()

                # Handle lights state after config change
                if config.ENABLE_LIGHTS_OFF:
                    now = datetime.now().time()  # Get current time for comparison
                    lights_off = (
                        (config.LIGHTS_OFF_TIME > config.LIGHTS_ON_TIME and (now >= config.LIGHTS_OFF_TIME or now < config.LIGHTS_ON_TIME)) or
                        (config.LIGHTS_OFF_TIME <= config.LIGHTS_ON_TIME and config.LIGHTS_OFF_TIME <= now < config.LIGHTS_ON_TIME)
                    )
                    if lights_off:
                        turn_off_lights()
                    else:
                        turn_on_lights()
            
            last_check = current_time  # Update last check timestamp
        
        time.sleep(1)  # Sleep for 1 second between checks


if __name__ == "__main__":
    # Monitor config changes and run scheduler
    config_file = "/home/pi/config.py"
    schedule_lights()  # Initial scheduling
    monitor_config_changes(config_file)
