# Simple Service Status Check Solution

## Current Problem
When config.py changes, scheduler.py:
1. **Always restarts METAR service** (turns lights on)
2. **Then checks if lights should be on/off** (might turn them back off)

This means lights flash on momentarily even when they should stay off.

## Your Simple Solution
Check METAR service status **before** restarting it. Only restart if it was already running.

## Code Change Needed

In `scheduler.py`, lines 248-275, change this:

```python
if current_modified != last_modified and not sun_time_update_in_progress:
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
    schedule_lights(initial_run=False)

    # Handle lights state after config change
    if config.ENABLE_LIGHTS_OFF:
        now = datetime.now().time()
        lights_off = (
            (config.LIGHTS_OFF_TIME > config.LIGHTS_ON_TIME and (now >= config.LIGHTS_OFF_TIME or now < config.LIGHTS_ON_TIME)) or
            (config.LIGHTS_OFF_TIME <= config.LIGHTS_ON_TIME and config.LIGHTS_OFF_TIME <= now < config.LIGHTS_ON_TIME)
        )
        if lights_off:
            turn_off_lights()
        else:
            turn_on_lights()
```

To this:

```python
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
        now = datetime.now().time()
        lights_off = (
            (config.LIGHTS_OFF_TIME > config.LIGHTS_ON_TIME and (now >= config.LIGHTS_OFF_TIME or now < config.LIGHTS_ON_TIME)) or
            (config.LIGHTS_OFF_TIME <= config.LIGHTS_ON_TIME and config.LIGHTS_OFF_TIME <= now < config.LIGHTS_ON_TIME)
        )
        if lights_off:
            turn_off_lights()
        else:
            turn_on_lights()
```

## Why This Works Perfectly

1. **If lights are ON** (service running):
   - Config changes → service restarts → lights stay on with new config
   - Time-based logic still works if needed

2. **If lights are OFF** (service stopped by Home Assistant):
   - Config changes → no service restart → lights stay off
   - Your Home Assistant control is preserved

3. **Sunset/sunrise updates at midnight**:
   - If lights are off → no restart → lights stay off ✅
   - If lights are on → restart with new brightness schedule → lights stay on ✅

This is brilliant because it respects the current light state while still allowing config updates to take effect when appropriate!