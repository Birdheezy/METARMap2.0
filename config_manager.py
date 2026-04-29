import json
import os
import datetime
import logging
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

class ConfigManager:
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = {}
        self.load_config()

    def load_config(self):
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_file):
            logger.warning(f"Config file {self.config_file} not found. Using defaults.")
            return

        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            
            # Convert types
            self._convert_types_after_load()
            logger.info("Configuration loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def _convert_types_after_load(self):
        """Convert specific fields from strings/lists to Python objects."""
        time_fields = ['LIGHTS_ON_TIME', 'LIGHTS_OFF_TIME', 'BRIGHT_TIME_START', 'DIM_TIME_START']
        for field in time_fields:
            if field in self.config and isinstance(self.config[field], str):
                try:
                    hour, minute = map(int, self.config[field].split(':'))
                    self.config[field] = datetime.time(hour, minute)
                except ValueError:
                    logger.error(f"Invalid time format for {field}: {self.config[field]}")

        color_fields = [
            'VFR_COLOR', 'MVFR_COLOR', 'IFR_COLOR', 'LIFR_COLOR', 'MISSING_COLOR',
            'LIGHTENING_COLOR', 'SNOWY_COLOR', 'STALE_DATA_COLOR', 'WIFI_DISCONNECTED_COLOR'
        ]
        for field in color_fields:
            if field in self.config and isinstance(self.config[field], list):
                self.config[field] = tuple(self.config[field])

    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a configuration value."""
        self.config[key] = value

    def save_config(self):
        """Save configuration to JSON file."""
        try:
            # Create a copy to convert types for serialization
            config_to_save = self.config.copy()
            
            time_fields = ['LIGHTS_ON_TIME', 'LIGHTS_OFF_TIME', 'BRIGHT_TIME_START', 'DIM_TIME_START']
            for field in time_fields:
                if field in config_to_save and isinstance(config_to_save[field], datetime.time):
                    config_to_save[field] = f"{config_to_save[field].hour:02d}:{config_to_save[field].minute:02d}"

            # Write to temp file first
            temp_file = self.config_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            
            # Atomic move
            shutil.move(temp_file, self.config_file)
            logger.info("Configuration saved successfully.")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

# Global instance
manager = ConfigManager()

def get_config():
    return manager.config
