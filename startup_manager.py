# -*- coding: utf-8 -*-

import winreg
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Use a consistent name for the registry entry
APP_NAME = "护目君" # Changed application name back for registry key
# Registry path for current user startup programs
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def get_executable_path():
    """
    Determines the path to the executable or the command to run the script.
    This needs refinement for a packaged application.
    """
    # If running as a frozen executable (e.g., PyInstaller)
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        # Running as a script, construct the command to run main.py with pythonw.exe
        # Using pythonw.exe prevents a console window from appearing on startup.
        # Assumes pythonw.exe is in the same directory as python.exe or in PATH.
        pythonw_path = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        if not os.path.exists(pythonw_path):
             pythonw_path = 'pythonw.exe' # Fallback to hoping it's in PATH

        # Get the absolute path to the main script directory
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Go up one level from EyeProtector dir
        main_script_path = os.path.join(script_dir, 'EyeProtector', 'main.py') # Path relative to project root

        # Ensure paths are absolute and quoted if they contain spaces
        # Note: This might still have issues depending on environment setup.
        # A packaged .exe is the most reliable way.
        # For development, this command assumes the venv is NOT needed when run at startup,
        # which might be incorrect. A wrapper script might be better.
        # Let's simplify for now and just use the main.py path with pythonw
        # A better approach for dev might be a .bat file.
        # For now, let's assume a packaged app scenario is the target.
        # If running from source, manual setup might be needed or a different approach.

        # Simplification: Return path to main.py, assuming pythonw handles it.
        # This is NOT robust for running from source without activation.
        # Let's return the command using sys.executable (often python.exe) for now.
        # User might need to adjust this or create a shortcut/wrapper.
        main_script_abs_path = os.path.abspath(main_script_path)
        # Using sys.executable (python.exe) might show a console briefly.
        # return f'"{sys.executable}" "{main_script_abs_path}"'
        # Let's try pythonw path directly
        return f'"{pythonw_path}" "{main_script_abs_path}"'


def is_auto_start_enabled():
    """Checks if the application is configured to run at startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        logging.info(f"'{APP_NAME}' found in startup registry.")
        return True
    except FileNotFoundError:
        logging.info(f"'{APP_NAME}' not found in startup registry.")
        return False
    except Exception as e:
        logging.error(f"Error checking startup registry: {e}")
        return False # Assume disabled on error

def enable_auto_start():
    """Adds the application to the Windows startup registry."""
    executable_path_or_command = get_executable_path()
    if not executable_path_or_command:
        logging.error("Could not determine executable path for auto-start.")
        return False

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, executable_path_or_command)
        winreg.CloseKey(key)
        logging.info(f"Enabled auto-start for '{APP_NAME}' with command: {executable_path_or_command}")
        return True
    except Exception as e:
        logging.error(f"Failed to enable auto-start: {e}")
        return False

def disable_auto_start():
    """Removes the application from the Windows startup registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        logging.info(f"Disabled auto-start for '{APP_NAME}'.")
        return True
    except FileNotFoundError:
        logging.info(f"'{APP_NAME}' was not in startup registry, nothing to disable.")
        return True # Considered success if it's already not there
    except Exception as e:
        logging.error(f"Failed to disable auto-start: {e}")
        return False

# Example Usage (for testing)
if __name__ == "__main__":
    print("Testing Startup Manager...")
    print(f"Executable path/command: {get_executable_path()}")

    print("\nChecking current status...")
    if is_auto_start_enabled():
        print("Auto-start is currently ENABLED.")
        print("Attempting to disable...")
        if disable_auto_start():
            print("Disable successful.")
            if not is_auto_start_enabled():
                print("Verification: Auto-start is now DISABLED.")
            else:
                print("Verification FAILED: Auto-start still seems enabled.")
        else:
            print("Disable failed.")
    else:
        print("Auto-start is currently DISABLED.")
        print("Attempting to enable...")
        if enable_auto_start():
            print("Enable successful.")
            if is_auto_start_enabled():
                print("Verification: Auto-start is now ENABLED.")
            else:
                print("Verification FAILED: Auto-start still seems disabled.")
        else:
            print("Enable failed.")

    # Clean up by disabling at the end of the test
    # print("\nCleaning up: Attempting to disable...")
    # disable_auto_start()
    # print(f"Final status check: {'ENABLED' if is_auto_start_enabled() else 'DISABLED'}")

    print("\nTest complete.")
