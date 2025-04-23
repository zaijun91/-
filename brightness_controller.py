# -*- coding: utf-8 -*-

import logging
import platform
import time

try:
    import wmi
    import pywintypes # Often needed with wmi/pywin32
except ImportError:
    logging.error("Required library not found: 'wmi' or 'pywin32'. Brightness control unavailable.")
    logging.error("Please install using: pip install wmi pywin32")
    wmi = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BrightnessController:
    """Handles screen brightness adjustments via WMI."""

    def __init__(self):
        self.supported = False
        self.wmi_instance = None
        self.brightness_methods = None
        if platform.system() == "Windows" and wmi:
            try:
                # Connect to WMI namespace for display management
                self.wmi_instance = wmi.WMI(namespace='wmi')
                # Get brightness control methods
                self.brightness_methods = self.wmi_instance.WmiMonitorBrightnessMethods()
                if self.brightness_methods:
                    self.supported = True
                    logging.info("BrightnessController initialized successfully via WMI.")
                else:
                    logging.warning("WMI brightness control methods not found. Brightness control might be unavailable.")
            except wmi.x_wmi as e:
                logging.error(f"WMI Initialization Error: {e}. Brightness control unavailable.")
                # Handle specific errors like access denied if needed
                if "Access is denied" in str(e):
                     logging.error("WMI access denied. Try running as administrator?")
            except Exception as e:
                 logging.error(f"Unexpected error during WMI initialization: {e}. Brightness control unavailable.")
        else:
            logging.warning("Brightness control requires Windows and the 'wmi'/'pywin32' libraries.")

    def is_supported(self):
        """Check if brightness control is supported."""
        return self.supported

    def get_brightness(self):
        """Gets the current screen brightness percentage (0-100)."""
        if not self.supported:
            logging.error("Cannot get brightness: Control not supported or initialized.")
            return -1

        try:
            brightness_info = self.wmi_instance.WmiMonitorBrightness()
            if brightness_info:
                # WmiMonitorBrightness usually returns a list, get the first monitor's info
                current_brightness = brightness_info[0].CurrentBrightness
                logging.debug(f"Current brightness level reported by WMI: {current_brightness}")
                # The value is typically 0-100 already, but double-check documentation if needed
                return int(current_brightness)
            else:
                logging.error("Failed to retrieve brightness info via WMI.")
                return -1
        except Exception as e:
            logging.error(f"Error getting brightness via WMI: {e}")
            return -1

    def set_brightness(self, level, smooth_transition=True, duration_ms=200):
        """Sets the screen brightness percentage (0-100)."""
        if not self.supported:
            logging.error("Cannot set brightness: Control not supported or initialized.")
            return False

        level = int(clamp(level, 0, 100)) # Ensure level is within 0-100

        try:
            current_level = self.get_brightness()
            if current_level == -1:
                # If we can't get current level, just set directly
                smooth_transition = False

            if smooth_transition and current_level != level:
                logging.info(f"Smoothly setting brightness from {current_level}% to {level}% over {duration_ms}ms")
                steps = 10 # Number of steps for transition
                delay = duration_ms / 1000 / steps
                level_step = (level - current_level) / steps

                for i in range(1, steps + 1):
                    target_level = int(current_level + i * level_step)
                    # WmiSetBrightness takes level (0-100) and timeout (0)
                    self.brightness_methods[0].WmiSetBrightness(target_level, 0)
                    time.sleep(delay)
                # Ensure final level is set exactly
                self.brightness_methods[0].WmiSetBrightness(level, 0)

            else:
                logging.info(f"Setting brightness directly to {level}%")
                # WmiSetBrightness takes level (0-100) and timeout (0)
                self.brightness_methods[0].WmiSetBrightness(level, 0)

            logging.debug(f"Successfully set brightness to {level}% via WMI.")
            return True
        except pywintypes.com_error as com_err:
             logging.error(f"COM Error setting brightness via WMI: {com_err}")
             return False
        except Exception as e:
            logging.error(f"Error setting brightness via WMI: {e}")
            return False

# Helper clamp function (duplicate from gamma_controller, consider moving to a utils module later)
def clamp(value, min_val, max_val):
    """Clamps a value between a minimum and maximum."""
    return max(min_val, min(value, max_val))

# Example Usage (for testing)
if __name__ == "__main__":
    if platform.system() != "Windows" or not wmi:
        print("This script requires Windows and the 'wmi'/'pywin32' libraries.")
        sys.exit(1)

    controller = BrightnessController()
    if controller.is_supported():
        print("Brightness control appears to be supported.")
        original_brightness = controller.get_brightness()
        print(f"Original brightness: {original_brightness}%")

        if original_brightness != -1:
            print("Setting brightness to 20% (smoothly)...")
            controller.set_brightness(20)
            time.sleep(3)

            print("Setting brightness to 80% (smoothly)...")
            controller.set_brightness(80)
            time.sleep(3)

            print(f"Restoring original brightness ({original_brightness}%) smoothly...")
            controller.set_brightness(original_brightness)
            print("Test complete.")
        else:
            print("Could not get original brightness to run full test.")
            print("Attempting to set brightness to 50% directly...")
            if controller.set_brightness(50, smooth_transition=False):
                print("Set brightness to 50%. Please check visually.")
            else:
                print("Failed to set brightness.")

    else:
        print("Brightness control not supported or failed to initialize on this system.")
