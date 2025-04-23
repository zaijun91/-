# -*- coding: utf-8 -*-

import ctypes
import math
import logging
import platform

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define necessary Windows structures and constants
# Based on wingdi.h
# WORD is c_ushort, DWORD is c_ulong
class RAMP(ctypes.Structure):
    _fields_ = [('red', ctypes.c_ushort * 256),
                ('green', ctypes.c_ushort * 256),
                ('blue', ctypes.c_ushort * 256)]

# Function prototypes from gdi32.dll
try:
    gdi32 = ctypes.windll.gdi32
    # GetDeviceGammaRamp = gdi32.GetDeviceGammaRamp # Optional: if needed to read current ramp
    SetDeviceGammaRamp = gdi32.SetDeviceGammaRamp
    SetDeviceGammaRamp.argtypes = [ctypes.c_void_p, ctypes.c_void_p] # HDC, LPVOID (ramp)
    SetDeviceGammaRamp.restype = ctypes.c_bool
except AttributeError:
    logging.error("Failed to load gdi32.dll or find GammaRamp functions. Gamma control unavailable.")
    SetDeviceGammaRamp = None # Ensure it's defined but unusable

# Get DC for the entire screen
try:
    user32 = ctypes.windll.user32
    hdc = user32.GetDC(None)
    if not hdc:
        logging.error("Failed to get screen device context (HDC). Gamma control unavailable.")
except AttributeError:
     logging.error("Failed to load user32.dll or find GetDC function. Gamma control unavailable.")
     hdc = None


def clamp(value, min_val, max_val):
    """Clamps a value between a minimum and maximum."""
    return max(min_val, min(value, max_val))

class GammaController:
    """Handles screen color temperature adjustments via Gamma Ramp."""

    def __init__(self):
        self.hdc = hdc # Use the globally obtained HDC
        self.supported = self._check_support()
        if not self.supported:
            logging.warning("Gamma control via SetDeviceGammaRamp might not be supported or failed to initialize.")
        else:
            logging.info("GammaController initialized successfully.")
            # Optionally store the original gamma ramp here if needed for perfect reset
            # self.original_ramp = self._get_current_ramp()

    def _check_support(self):
        """Check if necessary functions and handles are available."""
        return platform.system() == "Windows" and self.hdc is not None and SetDeviceGammaRamp is not None

    # def _get_current_ramp(self): # Optional: Implement if needed
    #     if not self.supported: return None
    #     ramp = RAMP()
    #     if gdi32.GetDeviceGammaRamp(self.hdc, ctypes.byref(ramp)):
    #         return ramp
    #     else:
    #         logging.error("Failed to get current gamma ramp.")
    #         return None

    def _calculate_color_gain(self, kelvin):
        """Calculates RGB gains based on Kelvin temperature. Simplified."""
        kelvin = clamp(kelvin, 1000, 10000)

        r_gain, g_gain, b_gain = 1.0, 1.0, 1.0

        if kelvin <= 6500: # Warmer
            r_gain = 1.0
            g_gain = clamp(0.8 + 0.2 * ((kelvin - 1000) / (6500 - 1000)), 0.8, 1.0)
            b_gain = clamp(0.6 + 0.4 * ((kelvin - 1000) / (6500 - 1000)), 0.6, 1.0)
        else: # Colder
            r_gain = clamp(1.0 - 0.2 * ((kelvin - 6500) / (10000 - 6500)), 0.8, 1.0)
            g_gain = clamp(1.0 - 0.1 * ((kelvin - 6500) / (10000 - 6500)), 0.9, 1.0)
            b_gain = 1.0

        logging.debug(f"Calculated gains for {kelvin}K: R={r_gain:.2f}, G={g_gain:.2f}, B={b_gain:.2f}")
        return r_gain, g_gain, b_gain

    def set_temperature(self, kelvin):
        """Sets the display color temperature."""
        if not self.supported:
            logging.error("Cannot set temperature: Gamma control not supported or initialized.")
            return False

        logging.info(f"Setting color temperature to {kelvin}K")
        r_gain, g_gain, b_gain = self._calculate_color_gain(kelvin)

        ramp = RAMP()
        gamma = 2.2 # Standard gamma assumption

        for i in range(256):
            # Normalize, linearize, apply gain, apply inverse gamma, scale to WORD
            norm_intensity = i / 255.0
            linear_intensity = math.pow(norm_intensity, gamma) # Linearize approx.

            r_corrected = linear_intensity * r_gain
            g_corrected = linear_intensity * g_gain
            b_corrected = linear_intensity * b_gain

            # Apply inverse gamma and scale
            ramp.red[i] = int(clamp(math.pow(r_corrected, 1.0/gamma), 0.0, 1.0) * 65535 + 0.5)
            ramp.green[i] = int(clamp(math.pow(g_corrected, 1.0/gamma), 0.0, 1.0) * 65535 + 0.5)
            ramp.blue[i] = int(clamp(math.pow(b_corrected, 1.0/gamma), 0.0, 1.0) * 65535 + 0.5)

        # Apply the new gamma ramp
        success = SetDeviceGammaRamp(self.hdc, ctypes.byref(ramp))
        if not success:
            # Get error code if needed: error_code = ctypes.windll.kernel32.GetLastError()
            logging.error("SetDeviceGammaRamp failed.")
        else:
            logging.debug("Successfully applied new gamma ramp.")
        return success

    def reset_gamma(self):
        """Resets the gamma ramp to a linear default."""
        if not self.supported:
            logging.error("Cannot reset gamma: Gamma control not supported or initialized.")
            return False

        logging.info("Attempting to reset gamma ramp to linear default.")
        ramp = RAMP()
        for i in range(256):
            val = int((i / 255.0) * 65535 + 0.5)
            ramp.red[i] = val
            ramp.green[i] = val
            ramp.blue[i] = val

        # Apply the linear ramp
        success = SetDeviceGammaRamp(self.hdc, ctypes.byref(ramp))
        if not success:
            logging.error("Resetting gamma ramp failed.")
        else:
            logging.info("Gamma ramp reset to linear default.")
        return success

    def __del__(self):
        # Release DC when object is destroyed (or application exits)
        # Note: Releasing the DC obtained with GetDC(None) might not be strictly
        # necessary or could even be problematic if other parts of the app use it.
        # Consider managing the HDC lifecycle carefully, perhaps releasing it
        # only at application exit. For now, we don't release it here.
        # if self.hdc:
        #     user32.ReleaseDC(None, self.hdc)
        #     logging.info("Screen device context released.")
        pass # See note above

# Example Usage (for testing)
if __name__ == "__main__":
    if platform.system() != "Windows":
        print("This script requires Windows for gamma control.")
        sys.exit(1)

    controller = GammaController()
    if controller.supported:
        import time
        print("Setting temperature to 3500K (Warm)")
        controller.set_temperature(3500)
        time.sleep(5)
        print("Setting temperature to 5000K (Less Warm)")
        controller.set_temperature(5000)
        time.sleep(5)
        print("Resetting gamma")
        controller.reset_gamma()
        print("Test complete.")
    else:
        print("Gamma control not supported on this system.")

    # Explicitly release DC at the end of the test script
    if hdc:
        user32.ReleaseDC(None, hdc)
        logging.info("Screen device context released at script exit.")
