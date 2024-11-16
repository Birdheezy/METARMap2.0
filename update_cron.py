import os
import time
import config
import subprocess
import datetime

# Function to update cron jobs with new times from config.py
def update_cron():
    # Extract on and off times from config.py
    lights_on_time = config.LIGHTS_ON_TIME  # e.g., datetime.time(7, 10)
    lights_off_time = config.LIGHTS_OFF_TIME  # e.g., datetime.time(20, 5)

    # Format times for cron (HH:MM)
    on_time_str = f"{lights_on_time.minute} {lights_on_time.hour}"
    off_time_str = f"{lights_off_time.minute} {lights_off_time.hour}"

    # Read existing crontab
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    existing_cron = result.stdout.splitlines()

    # Patterns to identify cron jobs for starting and stopping metar.service
    start_pattern = "/usr/bin/systemctl start metar.service"
    stop_pattern = "/usr/bin/systemctl stop metar.service && /home/pi/metar/bin/python3 /home/pi/blank.py"

    # Updated cron job list
    new_cron = []

    # Update existing cron jobs
    cron_updated = False
    for line in existing_cron:
        if start_pattern in line:
            # Update only the time portion for starting the service
            new_cron.append(f"{on_time_str} * * * * {start_pattern}")
            cron_updated = True
        elif stop_pattern in line:
            # Update only the time portion for stopping the service and running blank.py
            new_cron.append(f"{off_time_str} * * * * {stop_pattern}")
            cron_updated = True
        else:
            new_cron.append(line)

    # If the cron jobs were not found, append them as new jobs
    if not cron_updated:
        new_cron.append(f"{on_time_str} * * * * {start_pattern}")
        new_cron.append(f"{off_time_str} * * * * {stop_pattern}")

    # Apply the updated crontab
    new_cron_str = "\n".join(new_cron) + "\n"
    subprocess.run(["crontab"], input=new_cron_str, text=True)
    print("Cron jobs updated successfully.")

# Monitor the last modified timestamp of config.py
def monitor_config():
    config_path = '/home/pi/config.py'
    last_modified_timestamp = os.path.getmtime(config_path)

    while True:
        try:
            current_timestamp = os.path.getmtime(config_path)
            if current_timestamp != last_modified_timestamp:
                print("config.py modified, updating cron jobs...")
                time.sleep(1)  # Delay to ensure file is fully written
                update_cron()
                # Update the last modified timestamp
                last_modified_timestamp = current_timestamp

        except FileNotFoundError:
            print("config.py not found, waiting for file...")
        
        # Check every second (or adjust based on how often you expect changes)
        time.sleep(1)

if __name__ == "__main__":
    monitor_config()
