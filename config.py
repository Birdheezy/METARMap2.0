import datetime
import pytz
from config_manager import manager

# Load configuration from JSON
# This exposes all keys in config.json as module-level variables
# e.g. config.BRIGHTNESS will be available
for key, value in manager.config.items():
    globals()[key] = value
