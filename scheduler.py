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
import pytz
from astral import LocationInfo
from astral.sun import sun

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Only include the message, let journald handle the timestamp
)

logger = logging.getLogger(__name__)

# Create a lock for weather updates
weather_update_lock = threading.Lock()

# Add a flag to prevent infinite loops during sun time updates
sun_time_update_in_progress = False

def calculate_sun_times(city_name, date=None):
    """Calculate sunrise and sunset times for a given city and date"""
    if date is None:
        import datetime as dt
        date = dt.date.today()
    
    # Find the city in our database
    city_data = None
    for city in config.CITIES:
        if city["name"] == city_name:
            city_data = city
            break
    
    if not city_data:
        return None, None
    
    try:
        # Create location info for astral calculations
        location = LocationInfo(
            name=city_data["name"],
            region="USA",
            latitude=city_data["lat"],
            longitude=city_data["lon"],
            timezone=city_data["timezone"]
        )
        
        # Calculate sun times
        s = sun(location.observer, date=date, tzinfo=pytz.timezone(city_data["timezone"]))
        
        # Extract sunrise and sunset times
        sunrise = s["sunrise"].time()
        sunset = s["sunset"].time()
        
        return sunrise, sunset
        
    except Exception as e:
        logger.error(f"Error calculating sun times for {city_name}: {e}")
        return None, None

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

def update_sun_times():
    """Calculate and update sunrise/sunset times for the selected city."""
    global sun_time_update_in_progress
    
    # Check if an update is already in progress to avoid re-entry
    if sun_time_update_in_progress:
        logger.debug("Sun time update already in progress, skipping this call.")
        return

    sun_time_update_in_progress = True # Set flag at the very beginning
    try:
        # Only update if sunrise/sunset is enabled and a city is selected
        if not getattr(config, 'USE_SUNRISE_SUNSET', False) or not getattr(config, 'SELECTED_CITY', None):
            return
            
        city_name = config.SELECTED_CITY
        
        # Calculate times for today
        sunrise, sunset = calculate_sun_times(city_name)
        
        if sunrise and sunset:
            with open('/home/pi/config.py', 'r') as f:
                config_lines = f.readlines()
                        
            # Use a temporary file for atomic write to prevent corruption
            temp_config_path = '/home/pi/config.py.tmp'
            with open(temp_config_path, 'w') as f:
                for line in config_lines:
                    if line.startswith('BRIGHT_TIME_START'):
                        f.write(f"BRIGHT_TIME_START = datetime.time({sunrise.hour}, {sunrise.minute})\n")
                    elif line.startswith('DIM_TIME_START'):
                        f.write(f"DIM_TIME_START = datetime.time({sunset.hour}, {sunset.minute})\n")
                    else:
                        f.write(line)
            
            # Atomically replace the old config file with the new one
            os.replace(temp_config_path, '/home/pi/config.py')
            logger.info("config.py updated with new sun times.")

            # Reload the config module
            importlib.reload(config)
            logger.info(f"Updated sun times for {city_name}: Bright at {sunrise.hour:02d}:{sunrise.minute:02d}, Dim at {sunset.hour:02d}:{sunset.minute:02d}")
            
        else:
            logger.error(f"Failed to calculate sun times for {city_name}")
            
    except Exception as e:
        logger.error(f"Error updating sun times: {e}")
    finally:
        # Add a small delay to ensure file system settles and monitor has a chance to see the change
        # while the flag is still True.
        time.sleep(2)
        # Clear flag in finally block to ensure it's always reset
        sun_time_update_in_progress = False

def schedule_lights(initial_run=False):
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

    # Schedule daily sun time updates if enabled
    if getattr(config, 'USE_SUNRISE_SUNSET', False) and getattr(config, 'SELECTED_CITY', None):
        schedule.every().day.at("00:01").do(update_sun_times)  # Update at 12:01 AM daily
        logger.info("Scheduled daily sun time updates")
        # Run an immediate update only on the very first startup
        if initial_run:
            update_sun_times()

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
                schedule_lights(initial_run=False)  # This will schedule weather updates if enabled
            else:
                logger.info("METAR service has stopped, weather updates will be skipped.")
        
        # Check for config changes every few seconds
        if current_time - last_check >= 5:
            current_modified = os.path.getmtime(config_file)
            if current_modified != last_modified and not sun_time_update_in_progress:
                logger.info("Detected config.py changes. Reloading schedules...")
                last_modified = current_modified
                
                # Check if METAR service was running before config change
                was_running = is_metar_running()
                
                # Reload the config module to get updated values
                importlib.reload(config)
                
                # Only restart the METAR service if it was already running
                if was_running:
                    try:
                        subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)
                        logger.info("METAR service restarted successfully")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Error restarting METAR service: {e}")
                else:
                    logger.info("METAR service was not running, skipping restart")
                
                # Reschedule with the updated values
                schedule_lights(initial_run=False)

                # Only handle lights state if the service was running AND lights scheduling is enabled
                if was_running and config.ENABLE_LIGHTS_OFF:
                    now = datetime.now().time()  # Get current time for comparison
                    lights_off = (
                        (config.LIGHTS_OFF_TIME > config.LIGHTS_ON_TIME and (now >= config.LIGHTS_OFF_TIME or now < config.LIGHTS_ON_TIME)) or
                        (config.LIGHTS_OFF_TIME <= config.LIGHTS_ON_TIME and config.LIGHTS_OFF_TIME <= now < config.LIGHTS_ON_TIME)
                    )
                    if lights_off:
                        turn_off_lights()
                    else:
                        turn_on_lights()

            elif current_modified != last_modified and sun_time_update_in_progress:
               logger.debug("Config file changed, but sun time update in progress. Skipping reload.")
            
            last_check = current_time  # Update last check timestamp
        
        time.sleep(5)  # Sleep for 5 seconds between checks


if __name__ == "__main__":
    # Monitor config changes and run scheduler
    config_file = "/home/pi/config.py"
    schedule_lights(initial_run=True)  # Initial scheduling, run all initial tasks
    monitor_config_changes(config_file)
