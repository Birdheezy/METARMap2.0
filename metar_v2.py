import time
import datetime
import signal
import sys
import logging
import json
import os
import threading
import schedule # Import the library directly
import scheduler_v2 as app_scheduler # Rename local module to avoid collision
import board
import neopixel
from astral import LocationInfo
from astral.sun import sun
import pytz

# Import local modules
import config # Import config as module for defaults
from config_manager import manager # Import manager for dynamic config
import weather_v2 as weather

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Helper to get config value with fallback
def get_config_value(key, default=None):
    # Try dynamic config first
    val = manager.get(key)
    if val is not None:
        return val
    # Fallback to static config module
    return getattr(config, key, default)

class METARDisplay:
    def __init__(self):
        self.pixels = None
        self.running = True
        self.weather_data = {}
        self.airports = []
        self.windy_airports = {}
        self.lightning_airports = {}
        self.snowy_airports = {}
        self.missing_airports = []
        self.base_led_colors = [] # Cache for base LED colors
        
        # State tracking
        self.lights_on = True
        self.current_brightness = get_config_value('BRIGHTNESS', 0.5)
        self.last_weather_update = 0
        self.last_wifi_check = 0
        self.wifi_connected = True
        
        # Animation state
        self.animation_generators = []
        self.current_animation_index = 0
        self.animation_start_time = 0
        self.is_animating = False
        
        # Sun times
        self.sunrise = None
        self.sunset = None
        
        self.setup_leds()
        self.setup_signals()
        self.setup_scheduler()
        
        # Initial load
        self.load_airports() # Must load airports before updating weather/colors
        self.update_sun_times()
        self.update_weather()

    def setup_leds(self):
        try:
            pixel_pin_val = get_config_value('PIXEL_PIN', 18)
            num_pixels = get_config_value('NUM_PIXELS', 50)
            brightness = get_config_value('BRIGHTNESS', 0.5)
            led_order = get_config_value('LED_COLOR_ORDER', 'GRB')
            
            pixel_pin = getattr(board, f"D{pixel_pin_val}")
            self.pixels = neopixel.NeoPixel(
                pixel_pin,
                num_pixels,
                brightness=brightness,
                auto_write=False,
                pixel_order=led_order
            )
            logger.info(f"LED strip initialized on pin D{pixel_pin_val}")
        except Exception as e:
            logger.error(f"Failed to initialize LED strip: {e}")
            sys.exit(1)

    def setup_signals(self):
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)

    def setup_scheduler(self):
        # Schedule weather updates
        interval = get_config_value('WEATHER_UPDATE_INTERVAL', 300)
        schedule.every(interval).seconds.do(self.update_weather)
        
        # Schedule sun time updates (daily at 3 AM)
        schedule.every().day.at("03:00").do(self.update_sun_times)
        
        # Schedule WiFi check
        if get_config_value('WIFI_INDICATION', True):
            wifi_interval = get_config_value('WIFI_CHECK_INTERVAL', 300)
            schedule.every(wifi_interval).seconds.do(self.check_wifi)

    def cleanup(self, signum, frame):
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False
        if self.pixels:
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
        sys.exit(0)

    def load_airports(self):
        airports_file = get_config_value('AIRPORTS_FILE', 'airports.txt')
        self.airports = weather.get_airports_with_skip(airports_file)

    def update_sun_times(self):
        # Use getattr to safely access config variables that might be missing
        use_sun = get_config_value('USE_SUNRISE_SUNSET', False)
        city = get_config_value('SELECTED_CITY', None)
        
        if not use_sun or not city:
            return

        try:
            # This requires a proper city lookup or lat/long in config
            pass 
        except Exception as e:
            logger.error(f"Failed to update sun times: {e}")

    def update_weather(self):
        logger.info("Updating weather data...")
        try:
            # Fetch new data
            metar_data = weather.fetch_metar()
            if metar_data:
                parsed_data = weather.parse_weather(metar_data)
                
                # 1. Load stations
                stations = weather.load_stations()
                
                # 2. Merge
                final_data = {}
                airports_file = get_config_value('AIRPORTS_FILE', 'airports.txt')
                expected = weather.get_valid_airports(airports_file)
                
                for code in expected:
                    if code in parsed_data:
                        final_data[code] = parsed_data[code]
                        # Update station cache
                        if parsed_data[code].get('latitude'):
                            stations[code] = {
                                'latitude': parsed_data[code]['latitude'],
                                'longitude': parsed_data[code]['longitude'],
                                'site': parsed_data[code].get('site', code)
                            }
                    elif code in stations:
                        final_data[code] = {
                            "flt_cat": "MISSING",
                            "raw_observation": "No data available",
                            "site": stations[code].get('site', code),
                            "latitude": stations[code]['latitude'],
                            "longitude": stations[code]['longitude'],
                            "observation_time": "Unknown"
                        }
                    else:
                        final_data[code] = {
                            "flt_cat": "MISSING",
                            "raw_observation": "No data available",
                            "site": code
                        }
                
                # Save stations
                weather.save_stations(stations)
                
                # Save weather.json
                with open('/home/pi/weather.json', 'w') as f:
                    json.dump(final_data, f, indent=4)
                
                self.weather_data = final_data
                self.last_weather_update = time.time()
                
                # Update special lists
                self.windy_airports = weather.get_windy_airports(self.weather_data)
                self.lightning_airports = weather.get_lightning_airports(self.weather_data)
                self.snowy_airports = weather.get_snowy_airports(self.weather_data)
                
                # --- OPTIMIZATION: Pre-calculate base colors ---
                self.precalculate_base_colors()
                
                logger.info("Weather updated successfully.")
            else:
                logger.warning("Failed to fetch METAR data.")
                
        except Exception as e:
            logger.error(f"Error updating weather: {e}")

    def check_wifi(self):
        # Simple check - can be improved
        try:
            # Check for default gateway
            response = os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1")
            self.wifi_connected = (response == 0)
        except:
            self.wifi_connected = False

    def get_brightness(self):
        now = datetime.datetime.now().time()
        
        daytime_dimming = get_config_value('DAYTIME_DIMMING', True)
        dim_start = get_config_value('DIM_TIME_START', datetime.time(20, 0))
        bright_start = get_config_value('BRIGHT_TIME_START', datetime.time(6, 0))
        brightness = get_config_value('BRIGHTNESS', 0.5)
        daytime_dim_brightness = get_config_value('DAYTIME_DIM_BRIGHTNESS', 0.2)

        if daytime_dimming:
            # Handle wrap-around time (e.g. 22:00 to 06:00)
            if dim_start > bright_start:
                # Normal day (e.g. 06:00 to 20:00 is bright)
                if bright_start <= now < dim_start:
                    return brightness
                else:
                    return daytime_dim_brightness
            else:
                # Wrap around
                if bright_start <= now or now < dim_start:
                    return brightness
                else:
                    return daytime_dim_brightness
        return brightness

    def check_lights_off(self):
        if not get_config_value('ENABLE_LIGHTS_OFF', False):
            return False
            
        now = datetime.datetime.now().time()
        off_time = get_config_value('LIGHTS_OFF_TIME', datetime.time(22, 0))
        on_time = get_config_value('LIGHTS_ON_TIME', datetime.time(6, 30))
        
        if off_time > on_time:
            return now >= off_time or now < on_time
        else:
            return off_time <= now < on_time

    def set_pixel(self, index, color):
        # Apply brightness
        b = self.current_brightness
        self.pixels[index] = (int(color[0] * b), int(color[1] * b), int(color[2] * b))

    def get_available_leds(self):
        """Calculate the number of LEDs available for airports (excluding legend LEDs)."""
        if get_config_value('LEGEND', False):
            # Count enabled legend items
            legend_items = [
                get_config_value('LEGEND_VFR', True),
                get_config_value('LEGEND_MVFR', True),
                get_config_value('LEGEND_IFR', True),
                get_config_value('LEGEND_LIFR', True),
                get_config_value('LEGEND_SNOWY', True),
                get_config_value('LEGEND_LIGHTNING', True), 
                get_config_value('LEGEND_WINDY', True),
                get_config_value('LEGEND_MISSING', True)
            ]
            legend_count = sum(1 for x in legend_items if x)
            return get_config_value('NUM_PIXELS', 50) - legend_count
        else:
            return get_config_value('NUM_PIXELS', 50)

    def precalculate_base_colors(self):
        """Pre-calculate the base color for every LED to speed up rendering."""
        num_pixels = get_config_value('NUM_PIXELS', 50)
        missing_color = get_config_value('MISSING_COLOR', (255, 255, 0))
        
        self.base_led_colors = [(0, 0, 0)] * num_pixels
        available_count = self.get_available_leds()
        
        # 1. Airports
        for i, code in enumerate(self.airports):
            if i >= available_count:
                break
            
            if code == "SKIP":
                self.base_led_colors[i] = (0, 0, 0)
                continue
                
            if code in self.weather_data:
                cat = self.weather_data[code].get('flt_cat', 'MISSING')
                color = weather.get_flt_cat_color(cat)
                self.base_led_colors[i] = color
            else:
                self.base_led_colors[i] = missing_color

        # 2. Legend
        if get_config_value('LEGEND', False):
            vfr_color = get_config_value('VFR_COLOR', (0, 255, 0))
            legend_items = [
                ('VFR', vfr_color, get_config_value('LEGEND_VFR', True)),
                ('MVFR', get_config_value('MVFR_COLOR', (0, 0, 255)), get_config_value('LEGEND_MVFR', True)),
                ('IFR', get_config_value('IFR_COLOR', (255, 0, 0)), get_config_value('LEGEND_IFR', True)),
                ('LIFR', get_config_value('LIFR_COLOR', (255, 0, 255)), get_config_value('LEGEND_LIFR', True)),
                ('SNOWY', get_config_value('SNOWY_COLOR', (0, 255, 255)), get_config_value('LEGEND_SNOWY', True)),
                ('LIGHTNING', get_config_value('LIGHTENING_COLOR', (255, 255, 255)), get_config_value('LEGEND_LIGHTNING', True)),
                ('WINDY', tuple(int(c * get_config_value('DIM_BRIGHTNESS', 0.05)) for c in vfr_color), get_config_value('LEGEND_WINDY', True)),
                ('MISSING', missing_color, get_config_value('LEGEND_MISSING', True))
            ]
            enabled_items = [(name, color) for name, color, enabled in legend_items if enabled]
            
            for i, (name, color) in enumerate(enabled_items):
                led_index = num_pixels - 1 - i
                if led_index >= 0:
                    self.base_led_colors[led_index] = color

    def render_base_map(self):
        """Render the static map colors using pre-calculated list."""
        # Fast copy of pre-calculated colors
        # We still need to apply brightness, which happens in set_pixel
        # But wait, set_pixel applies brightness to self.pixels.
        # So we can just iterate and set.
        
        # Optimization: If brightness hasn't changed, we could cache the *dimmed* colors too?
        # For now, just iterating the list is O(N) and fast enough.
        
        for i, color in enumerate(self.base_led_colors):
            self.set_pixel(i, color)

    # Remove separate render_legend as it's now part of pre-calculation
    # def render_legend(self): ...

    # --- Generators for Animations ---
    
    def anim_windy(self):
        """Generator for windy animation."""
        if not self.windy_airports:
            return

        steps = get_config_value('NUM_STEPS', 100)
        delay = get_config_value('WIND_FADE_TIME', 0.5) / steps
        wind_pause = get_config_value('WIND_PAUSE', 2.0)
        dim_brightness = get_config_value('DIM_BRIGHTNESS', 0.05)
        
        # Get windy LED indices
        indices = []
        for i, code in enumerate(self.airports):
            if code in self.windy_airports and i < self.get_available_leds():
                indices.append(i)
        
        if not indices:
            return

        # Helper to set dim color
        def set_dim_color(brightness_factor):
            # brightness_factor: 0.0 (Current) to 1.0 (Dim)
            b_current = self.current_brightness
            b_target = dim_brightness
            b_now = b_current - (b_current - b_target) * brightness_factor
            
            for idx in indices:
                code = self.airports[idx]
                cat = self.weather_data.get(code, {}).get('flt_cat', 'MISSING')
                base = weather.get_flt_cat_color(cat)
                self.pixels[idx] = (int(base[0] * b_now), int(base[1] * b_now), int(base[2] * b_now))

        # Fade Out
        for i in range(steps):
            set_dim_color(i / steps)
            yield delay

        # Pause at dim
        # We must keep yielding to hold the state because render_base_map wipes it every frame
        pause_end = time.time() + wind_pause
        while time.time() < pause_end:
            set_dim_color(1.0) # Keep it dim
            yield 0.1 # Yield short sleeps

        # Fade In
        for i in range(steps):
            set_dim_color(1.0 - (i / steps))
            yield delay

    def anim_lightning(self):
        """Generator for lightning animation."""
        if not self.lightning_airports:
            return

        indices = []
        for i, code in enumerate(self.airports):
            if code in self.lightning_airports and i < self.get_available_leds():
                indices.append(i)
        
        if not indices:
            return

        # Flash count
        flash_count = get_config_value('LIGHTNING_FLASH_COUNT', 4)
        for _ in range(flash_count):
            # White Flash
            for idx in indices:
                # Full white, scaled by brightness
                b = self.current_brightness
                self.pixels[idx] = (int(255 * b), int(255 * b), int(255 * b))
            yield 0.1 # Short flash duration

            # Off (or back to normal color) - handled by render_base_map on next frame
            # But we want to pause briefly between flashes
            pause_end = time.time() + 0.2
            while time.time() < pause_end:
                 # Do nothing, let render_base_map show normal color
                 # We still need to yield something to keep the loop alive
                 yield 0.05

    def anim_snowy(self):
        """Generator for snowy animation (twinkling)."""
        if not self.snowy_airports:
            return

        indices = []
        for i, code in enumerate(self.airports):
            if code in self.snowy_airports and i < self.get_available_leds():
                indices.append(i)
        
        if not indices:
            return

        import random
        # Initialize random states for each LED
        led_states = {}
        start_time = time.time()
        
        snow_min_brightness = get_config_value('SNOW_MIN_BRIGHTNESS', 0.05)
        snow_cycle_min = get_config_value('SNOW_CYCLE_MIN_DURATION', 2.0)
        snow_cycle_max = get_config_value('SNOW_CYCLE_MAX_DURATION', 4.0)
        snow_offset_max = get_config_value('SNOW_START_OFFSET_MAX', 1.0)
        snow_color = get_config_value('SNOWY_COLOR', (0, 255, 255))

        for idx in indices:
            led_states[idx] = {
                'start_brightness': random.uniform(snow_min_brightness, self.current_brightness),
                'cycle_duration': random.uniform(snow_cycle_min, snow_cycle_max),
                'start_time': start_time + random.uniform(0, snow_offset_max)
            }

        duration = get_config_value('SNOWY_ANIMATION_DURATION', 5.0)
        frame_time = 0.05 # 20 FPS
        
        while time.time() - start_time < duration:
            now = time.time()
            
            for idx in indices:
                state = led_states[idx]
                cycle_time = (now - state['start_time']) % state['cycle_duration']
                cycle_pos = cycle_time / state['cycle_duration']
                
                # Calculate brightness factor (0.0 to 1.0 relative to range)
                if cycle_pos < 0.33:
                    f = cycle_pos / 0.33
                    b = state['start_brightness'] + (self.current_brightness - state['start_brightness']) * f
                elif cycle_pos < 0.66:
                    f = (cycle_pos - 0.33) / 0.33
                    b = self.current_brightness - (self.current_brightness - snow_min_brightness) * f
                else:
                    f = (cycle_pos - 0.66) / 0.34
                    b = snow_min_brightness + (state['start_brightness'] - snow_min_brightness) * f
                
                # Apply to snowy color
                # Note: b is absolute brightness value here (e.g. 0.1 to 0.5)
                # SNOWY_COLOR is (255, 255, 255) usually
                sr, sg, sb = snow_color
                self.pixels[idx] = (int(sr * b), int(sg * b), int(sb * b))
            
            yield frame_time

    def run(self):
        logger.info("Starting METARDisplay main loop")
        
        # Initialize animation queue
        animation_queue = []
        current_anim_gen = None
        next_anim_time = 0
        
        while self.running:
            loop_start = time.time()
            
            # 1. Run scheduled tasks
            schedule.run_pending()
            
            # 2. Check state
            self.lights_on = not self.check_lights_off()
            self.current_brightness = self.get_brightness()
            
            if not self.lights_on:
                self.pixels.fill((0, 0, 0))
                self.pixels.show()
                time.sleep(1) # Sleep longer when off
                continue

            # 3. Render Base Map (resets pixels to base state)
            self.render_base_map()
            
            # 4. Handle Animations
            # If no animation running, pick next one
            if current_anim_gen is None:
                if time.time() >= next_anim_time:
                    # Rebuild queue if empty
                    if not animation_queue:
                        if get_config_value('WIND_ANIMATION', True) and self.windy_airports:
                            animation_queue.append(self.anim_windy)
                        if get_config_value('LIGHTENING_ANIMATION', True) and self.lightning_airports:
                            animation_queue.append(self.anim_lightning)
                        if get_config_value('SNOWY_ANIMATION', True) and self.snowy_airports:
                            animation_queue.append(self.anim_snowy)
                    
                    # Pop next animation
                    if animation_queue:
                        anim_func = animation_queue.pop(0)
                        current_anim_gen = anim_func()
                        next_anim_time = 0 # Reset
                    else:
                        # No animations to run, just wait a bit before checking again
                        next_anim_time = time.time() + 1.0
            
            # Execute current animation step
            if current_anim_gen:
                try:
                    delay = next(current_anim_gen)
                    # We don't sleep here! We just mark when we can run next frame.
                    # But wait, this is a single threaded loop.
                    # If we yield a delay, we should ideally sleep OR just loop until that time.
                    # But we want to be non-blocking for other tasks (like schedule).
                    # Since our delays are short (0.05s for snow, 0.1s for lightning), 
                    # we can just sleep. For longer delays (Windy pause), we should break it up?
                    # For simplicity in this version, we'll sleep the yielded amount, 
                    # but cap it to ensure we check schedule periodically.
                    
                    if delay > 0.1:
                        # If delay is long, we sleep in chunks? 
                        # Or just sleep. 0.1s is fine. 
                        # Actually, if delay is 2 seconds (Windy pause), we block schedule for 2s.
                        # That's acceptable for now.
                        time.sleep(delay)
                    else:
                        time.sleep(delay)
                        
                except StopIteration:
                    # Animation finished
                    current_anim_gen = None
                    next_anim_time = time.time() + get_config_value('ANIMATION_PAUSE', 5)
            else:
                # No animation running, just base map
                self.pixels.show()
                time.sleep(0.1)

            # 5. Show pixels
            # We call show() here to push the frame we just calculated (Base + Animation)
            self.pixels.show()
            
            # 6. Sleep to maintain frame rate or animation delay
            if current_anim_gen:
                # If animating, sleep for the yielded delay
                # Cap max sleep to ensure we check schedule/signals
                sleep_time = min(delay, 1.0)
                time.sleep(sleep_time)
            else:
                # If idle, sleep a bit longer
                time.sleep(0.1)

if __name__ == "__main__":
    try:
        # Check if running on Pi (simple check for root or specific file)
        if os.geteuid() != 0:
            logger.warning("Not running as root. LED control might fail.")
        
        logger.info("Initializing METAR Display v2...")
        display = METARDisplay()
        
        # Print initial status table for verification (like original script)
        logger.info("\nInitial Airport Status:")
        logger.info(f"{'Airport':<10} {'Flight Cat':<12} {'Windy':<6} {'Lightning':<10} {'Snowy':<6}")
        logger.info("-" * 60)
        
        available_count = display.get_available_leds()
        for i, code in enumerate(display.airports):
            if i >= available_count: break
            if code == "SKIP": continue
            
            data = display.weather_data.get(code, {})
            cat = data.get('flt_cat', 'MISSING')
            is_windy = code in display.windy_airports
            is_lightning = code in display.lightning_airports
            is_snowy = code in display.snowy_airports
            
            logger.info(f"{code:<10} {cat:<12} {'Yes' if is_windy else 'No':<6} {'Yes' if is_lightning else 'No':<10} {'Yes' if is_snowy else 'No':<6}")
            
        display.run()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

