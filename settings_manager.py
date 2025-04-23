# -*- coding: utf-8 -*-

import json
import os
import logging
import appdirs # Use appdirs to find appropriate user data directory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_NAME = "护目君" # Changed application name back
APP_AUTHOR = "ClineUser" # Or your preferred author name
SETTINGS_FILE = "settings.json"

def get_settings_path():
    """Gets the full path to the settings file in the user's data directory."""
    data_dir = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            logging.info(f"Created application data directory: {data_dir}")
        except OSError as e:
            logging.error(f"Failed to create data directory {data_dir}: {e}")
            # Fallback to current directory if creation fails
            return os.path.join(".", SETTINGS_FILE)
    return os.path.join(data_dir, SETTINGS_FILE)

def get_default_settings():
    """Returns a dictionary containing the default application settings."""
    return {
        "temperature_kelvin": 6500,
        "brightness_percent": 80, # Default brightness target
        "reminder_enabled": False,
        "reminder_work_hours": 1, # Default work time: 1 hour
        "reminder_rest_minutes": 5, # Default rest time: 5 minutes
        "auto_start_enabled": False, # Default: disabled
        # Add more settings later (e.g., saved profiles, hotkeys)
        "profiles": {
             "Default": {"temperature": 6500, "brightness": 80},
             "Night Mode": {"temperature": 3500, "brightness": 40},
             "Reading": {"temperature": 4500, "brightness": 60}
         },
        "hotkeys": {
             "<ctrl>+<alt>+1": "Night Mode", # Ctrl+Alt+1 for Night Mode
             "<ctrl>+<alt>+2": "Reading",    # Ctrl+Alt+2 for Reading Mode
             "<ctrl>+<alt>+0": "Default"     # Ctrl+Alt+0 for Default profile
        }
    }

def load_settings():
    """Loads settings from the JSON file. Returns defaults if file not found or invalid."""
    settings_path = get_settings_path()
    defaults = get_default_settings()
    if not os.path.exists(settings_path):
        logging.info(f"Settings file not found at {settings_path}. Using defaults and creating file.")
        save_settings(defaults) # Save defaults if file doesn't exist
        return defaults

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            logging.info(f"Settings loaded successfully from {settings_path}")
            # Merge loaded settings with defaults to handle missing keys in old files
            settings = defaults.copy()
            settings.update(loaded) # Overwrite defaults with loaded values
            return settings
    except (json.JSONDecodeError, IOError, TypeError) as e:
        logging.error(f"Failed to load or parse settings file {settings_path}: {e}. Using default settings.")
        # Optionally backup the corrupted file here
        return defaults

def save_settings(settings):
    """Saves the provided settings dictionary to the JSON file."""
    settings_path = get_settings_path()
    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        logging.info(f"Settings saved successfully to {settings_path}")
        return True
    except (IOError, TypeError) as e:
        logging.error(f"Failed to save settings to {settings_path}: {e}")
        return False

# Example Usage (for testing)
if __name__ == "__main__":
    print("Testing settings manager...")
    # Install appdirs if not present: pip install appdirs
    try:
        import appdirs
    except ImportError:
        print("Please install 'appdirs': pip install appdirs")
        exit()

    print(f"Settings file path: {get_settings_path()}")

    # Load initial settings (might be defaults or existing)
    current_settings = load_settings()
    print("\nInitial loaded settings:")
    print(json.dumps(current_settings, indent=4, ensure_ascii=False))

    # Modify a setting
    current_settings["temperature_kelvin"] = 4000
    current_settings["reminder_enabled"] = True
    print("\nModified settings (before saving):")
    print(json.dumps(current_settings, indent=4, ensure_ascii=False))

    # Save modified settings
    if save_settings(current_settings):
        print("\nSettings saved.")
    else:
        print("\nFailed to save settings.")

    # Load again to verify
    reloaded_settings = load_settings()
    print("\nReloaded settings:")
    print(json.dumps(reloaded_settings, indent=4, ensure_ascii=False))

    # Verify modification
    if reloaded_settings.get("temperature_kelvin") == 4000:
        print("\nTemperature modification verified.")
    else:
        print("\nTemperature modification FAILED.")

    print("\nTest complete.")
