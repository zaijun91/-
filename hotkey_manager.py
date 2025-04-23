# -*- coding: utf-8 -*-

import logging
import threading
import time # Import the time module
from pynput import keyboard
from PySide6.QtCore import QObject, Signal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HotkeyManager(QObject):
    """Listens for global hotkeys in a separate thread and emits signals."""

    # Signal emitted when a registered hotkey is pressed.
    # The argument will be the string representation of the hotkey (e.g., '<ctrl>+<alt>+1')
    hotkey_pressed = Signal(str)

    def __init__(self, hotkey_map=None, parent=None):
        """
        Initializes the HotkeyManager.
        :param hotkey_map: Dictionary mapping hotkey strings (e.g., '<ctrl>+<alt>+1')
                           to identifiers or actions. Currently, we only need the keys.
        :param parent: Parent QObject.
        """
        super().__init__(parent)
        self.hotkey_map = hotkey_map if hotkey_map is not None else {}
        self._listener_thread = None
        self._listener = None
        self._stop_event = threading.Event()
        logging.info("HotkeyManager initialized.")

    def _parse_hotkey(self, hotkey_string):
        """Parses a pynput-style hotkey string into a set of keys."""
        # Basic parsing, might need refinement for complex keys
        keys = set()
        parts = hotkey_string.lower().split('+')
        for part in parts:
            part = part.strip()
            if part.startswith('<') and part.endswith('>'):
                 # Special key like <ctrl>, <alt>, <f1> etc.
                 key_name = part[1:-1]
                 try:
                     # Map common names to pynput Key objects
                     key = getattr(keyboard.Key, key_name, None)
                     if key is None and key_name.startswith('cmd'): # Mac command key alias
                         key = keyboard.Key.cmd
                     if key:
                         keys.add(key)
                     else:
                          logging.warning(f"Unknown special key name: {key_name} in hotkey '{hotkey_string}'")
                 except AttributeError:
                     logging.warning(f"Invalid special key: {key_name} in hotkey '{hotkey_string}'")
            elif len(part) == 1:
                 # Regular character key
                 try:
                     keys.add(keyboard.KeyCode.from_char(part))
                 except ValueError:
                      logging.warning(f"Invalid character key: {part} in hotkey '{hotkey_string}'")
            else:
                logging.warning(f"Unsupported part in hotkey string: {part}")
        return keys


    def start_listening(self):
        """Starts the keyboard listener in a separate thread."""
        if self._listener_thread is not None and self._listener_thread.is_alive():
            logging.warning("Hotkey listener thread already running.")
            return

        if not self.hotkey_map:
            logging.info("No hotkeys defined to listen for.")
            return

        logging.info(f"Starting hotkey listener for: {list(self.hotkey_map.keys())}")
        self._stop_event.clear()
        self._listener_thread = threading.Thread(target=self._run_listener, daemon=True)
        self._listener_thread.start()

    def stop_listening(self):
        """Stops the keyboard listener thread."""
        if self._listener_thread is None or not self._listener_thread.is_alive():
            logging.info("Hotkey listener thread is not running.")
            return

        logging.info("Stopping hotkey listener...")
        self._stop_event.set() # Signal the thread to stop
        if self._listener:
            # Stop the pynput listener itself
            # Note: This might need to be called from within the listener thread
            # or use keyboard.Listener.stop() if running directly
             try:
                 # This might raise exceptions if called from wrong thread, hence try-except
                 keyboard.Listener.stop(self._listener)
             except Exception as e:
                 logging.debug(f"Exception stopping listener (expected if called from main thread): {e}")

        self._listener_thread.join(timeout=1.0) # Wait for thread to finish
        if self._listener_thread.is_alive():
             logging.warning("Hotkey listener thread did not stop gracefully.")
        else:
             logging.info("Hotkey listener stopped.")
        self._listener_thread = None
        self._listener = None


    def _run_listener(self):
        """The function that runs in the listener thread."""
        pressed_keys = set()
        hotkeys_to_check = {hk: self._parse_hotkey(hk) for hk in self.hotkey_map.keys()}

        def on_press(key):
            pressed_keys.add(key)
            # logging.debug(f"Pressed: {key}, Current set: {pressed_keys}")
            for hotkey_str, required_keys in hotkeys_to_check.items():
                if required_keys.issubset(pressed_keys):
                    logging.info(f"Hotkey detected: {hotkey_str}")
                    self.hotkey_pressed.emit(hotkey_str) # Emit signal
                    # Optional: Consume the key press? Requires more complex listener setup.

            if self._stop_event.is_set():
                logging.debug("Stop event detected in on_press, stopping listener.")
                return False # Stop the listener

        def on_release(key):
            # logging.debug(f"Released: {key}")
            if key in pressed_keys:
                pressed_keys.remove(key)

            if self._stop_event.is_set():
                 logging.debug("Stop event detected in on_release, stopping listener.")
                 return False # Stop the listener

        # Create and run the listener
        try:
            with keyboard.Listener(on_press=on_press, on_release=on_release) as self._listener:
                logging.info("pynput listener started.")
                # Keep the thread alive while listener is running and stop event is not set
                while self._listener.running and not self._stop_event.is_set():
                    time.sleep(0.1) # Prevent busy-waiting
            logging.info("pynput listener finished.")
        except Exception as e:
             logging.error(f"Error running keyboard listener: {e}")
        finally:
             self._listener = None # Clear listener reference


# Example Usage (for testing without GUI integration)
if __name__ == "__main__":
    import time
    print("Hotkey Manager Test")

    # Define some hotkeys to listen for
    test_hotkeys = {
        '<ctrl>+<alt>+1': 'profile_night',
        '<ctrl>+<alt>+2': 'profile_reading',
        '<ctrl>+<alt>+p': 'toggle_pause', # Example
        'h': 'print_hello' # Simple key test
    }

    manager = HotkeyManager(test_hotkeys)

    def handle_hotkey(hotkey_str):
        print(f"--- Hotkey Signal Received: {hotkey_str} (Action: {manager.hotkey_map.get(hotkey_str)}) ---")

    manager.hotkey_pressed.connect(handle_hotkey)

    print("Starting listener... Press Ctrl+Alt+1, Ctrl+Alt+2, Ctrl+Alt+P, or 'h'. Press Ctrl+C in console to stop.")
    manager.start_listening()

    try:
        # Keep the main thread alive to allow the listener thread to run
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Stopping listener...")
        manager.stop_listening()
        print("Test finished.")
