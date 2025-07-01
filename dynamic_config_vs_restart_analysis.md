# Dynamic Config Loading vs Service Restart Analysis

## Current Approach: Service Restart
**How it works:** When config.py changes, scheduler.py restarts the entire METAR service.

### Pros:
- **Simple and reliable** - guaranteed fresh start with new config
- **No memory leaks** - process restart clears any accumulated state
- **Handles all config changes** - works for any type of configuration change
- **No code complexity** - existing approach, well-tested

### Cons:
- **Causes unwanted light management** - triggers automatic on/off logic
- **Brief service interruption** - LEDs go dark momentarily during restart
- **Resource overhead** - full process restart is heavier than needed
- **Timing issues** - creates race conditions with config monitoring

## Alternative Approach: Dynamic Config Loading
**How it would work:** Modify metar.py to monitor config.py and reload it without restarting.

### Pros:
- **No service interruption** - LEDs stay on, no flicker
- **No unwanted light management** - avoids the scheduler's restart logic
- **Better performance** - just reload config, don't restart process
- **Cleaner separation** - config changes don't trigger light scheduling

### Cons:
- **Code complexity** - need to add file monitoring to metar.py
- **Partial reload risks** - some config changes might not take effect properly
- **Memory considerations** - repeated imports without restart
- **Error handling** - what if config reload fails?

## Technical Implementation Comparison

### Current (Restart):
```python
# In scheduler.py
subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)
# Side effect: triggers light management logic
```

### Dynamic Loading:
```python
# In metar.py - would need to add:
import importlib
import os

def monitor_config_changes():
    last_modified = os.path.getmtime('/home/pi/config.py')
    while True:
        current_modified = os.path.getmtime('/home/pi/config.py')
        if current_modified != last_modified:
            importlib.reload(config)
            # Update any config-dependent variables
            update_config_dependent_vars()
            last_modified = current_modified
        time.sleep(5)
```

## Recommendation: Dynamic Loading is Better

**For your use case, dynamic config loading would be superior because:**

1. **Solves your core problem** - eliminates the unwanted light management completely
2. **Better user experience** - no LED interruptions during config updates
3. **Cleaner architecture** - separates config management from light scheduling
4. **More responsive** - config changes take effect immediately without restart delay

## Implementation Strategy

The best approach would be:

1. **Add config monitoring to metar.py** 
2. **Remove config restart logic from scheduler.py**
3. **Keep scheduler.py for time-based scheduling only**
4. **Handle config-dependent reinitialization** (like LED brightness, colors)

This way:
- Config changes in metar.py → dynamic reload, no restart
- Time-based scheduling in scheduler.py → no config restart logic
- Your Home Assistant integration → unaffected by config updates
- Sunset/sunrise updates → no unwanted light activation

## Potential Challenges

1. **Variable scope** - some config vars imported with `from config import *` need special handling
2. **Timing updates** - brightness/dimming schedules need to be recalculated
3. **LED reinitialization** - might need to rebuild NeoPixel object for pin/count changes
4. **Graceful degradation** - handle config reload failures

The benefits strongly outweigh the implementation complexity for your use case.