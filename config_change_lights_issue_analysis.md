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

## Recommended Implementation

The cleanest solution is **Option 1** combined with **Option 2**:

1. Add a config flag to control automatic light management
2. Improve the logic to distinguish between user config changes and automatic system updates
3. Allow users to disable automatic light state management while still getting config reloads

This preserves the existing functionality for users who want it while giving users like you the control to manage lights externally through Home Assistant.