# Config.py Change Causing Lights to Turn On - Issue Analysis

## Problem Description
Any time `config.py` is modified, the lights automatically turn on because the system restarts the METAR service. This is particularly problematic when:
- Sunset/sunrise times are automatically calculated and updated at midnight (00:01)
- User has disabled lights on/off scheduling and uses Home Assistant integration instead
- Any other config changes trigger unwanted light activation

## Root Cause Analysis

### Location: `scheduler.py` lines 248-275

The `monitor_config_changes()` function:

1. **Detects any config.py file modification** (line 248-249)
2. **Always restarts METAR service** (line 257-261) 
3. **Automatically manages light state** (line 265-275) based on `ENABLE_LIGHTS_OFF` and time calculations

### Specific Problem Areas:

1. **Line 257-261**: Unconditional METAR service restart
```python
# Restart the METAR service to apply all config changes
try:
    subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)
    logger.info("METAR service restarted successfully")
```

2. **Lines 265-275**: Automatic light state management
```python
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

## Proposed Solutions

### Option 1: Add Configuration Flag (Recommended)
Add a new config variable `AUTO_MANAGE_LIGHTS_ON_CONFIG_CHANGE = False` to disable automatic light management when config changes are detected.

### Option 2: Skip Light Management for Sunset/Sunrise Updates
Modify the logic to not manage lights when the config change was triggered by an automatic sunset/sunrise time update.

### Option 3: Selective Service Restart
Only restart the METAR service when necessary config changes occur (not for all changes).

### Option 4: User Control Override
When `ENABLE_LIGHTS_OFF = True` but user wants external control (like Home Assistant), provide a way to disable the automatic light state management.

## Key Discovery: METAR Service Restart is Actually Necessary

After examining `metar.py`, it **does NOT** monitor config changes:
- Imports config once at startup: `from config import *`
- No file watching or config reloading logic
- No dynamic config updates during runtime
- The systemd service (`services/metar.service`) is a simple service with no file watching

**Therefore, restarting the METAR service IS necessary for config changes to take effect.**

## Recommended Implementation

The cleanest solution is **Option 1** - Add a configuration flag:

1. **Add new config variable**: `AUTO_MANAGE_LIGHTS_ON_CONFIG_CHANGE = False`
2. **Modify scheduler.py** to respect this flag when handling config changes
3. **Keep the service restart** (necessary for config to take effect)
4. **Skip the automatic light management** when flag is disabled

This allows:
- Config changes to still take effect (via service restart)
- Users to disable automatic light state management
- External control via Home Assistant
- Existing functionality preserved for users who want it