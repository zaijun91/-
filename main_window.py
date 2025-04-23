# -*- coding: utf-8 -*-

import sys
import os # Import os for path manipulation
import logging
import datetime # Import datetime for usage tracking
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QSystemTrayIcon, QMenu, QSpinBox, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction

# Import our controllers and managers
from gamma_controller import GammaController
from brightness_controller import BrightnessController
from reminder_manager import ReminderManager # Re-enabled import
from hotkey_manager import HotkeyManager # Re-enabled import
import settings_manager as sm # Import settings manager
import stats_manager # Import stats manager
import startup_manager # Re-enabled import

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # Note: Adjust if your main script isn't at the root where PyInstaller runs
        base_path = sys._MEIPASS
    except Exception:
        # Not running as a bundle, use the directory of this script file
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.start_time = datetime.datetime.now() # Record start time for usage stats
        self.setWindowTitle("护目君") # Changed window title back
        icon_path = resource_path("Mind.ico") # Get correct path for icon
        if os.path.exists(icon_path):
             self.setWindowIcon(QIcon(icon_path)) # Set the application icon using resolved path
        else:
             logging.warning(f"Icon file not found at resolved path: {icon_path}")


        # Load settings first
        self.settings = sm.load_settings()
        logging.info(f"Loaded settings: {self.settings}")

        # Initialize controllers
        self.gamma_controller = GammaController()
        self.brightness_controller = BrightnessController()
        self.reminder_manager = ReminderManager(self) # Re-enabled instantiation
        # Apply loaded reminder durations (using new keys/units) # Re-enabled
        self.reminder_manager.set_durations( # Re-enabled
            self.settings.get("reminder_work_hours", 1), # Use hours # Re-enabled
            self.settings.get("reminder_rest_minutes", 5) # Use minutes # Re-enabled
        ) # Re-enabled


        # --- Main Layout ---
        central_widget = QWidget()
        self.main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # --- Temperature Control ---
        temp_layout = QHBoxLayout()
        self.temp_label = QLabel("色温 (Kelvin): 6500K")
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(2500, 6500) # Reverted minimum range to 2500K
        self.temp_slider.setValue(self.settings.get("temperature_kelvin", 6500)) # Use loaded value
        self.temp_slider.setSingleStep(100) # Step size
        self.temp_slider.setTickInterval(500)
        self.temp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.temp_slider.valueChanged.connect(self.on_temperature_change)

        temp_layout.addWidget(self.temp_label)
        temp_layout.addWidget(self.temp_slider)
        self.main_layout.addLayout(temp_layout)

        # --- Brightness Control ---
        brightness_layout = QHBoxLayout()
        self.brightness_label = QLabel("亮度 (%): N/A") # Initial state
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 100)
        # Set initial brightness slider value, but don't trigger API call yet
        self.brightness_slider.setValue(self.settings.get("brightness_percent", 80))
        self.brightness_slider.setSingleStep(5)
        self.brightness_slider.setTickInterval(10)
        self.brightness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.brightness_slider.valueChanged.connect(self.on_brightness_change)
        self.brightness_slider.setEnabled(self.brightness_controller.is_supported()) # Enable only if supported

        brightness_layout.addWidget(self.brightness_label)
        brightness_layout.addWidget(self.brightness_slider)
        self.main_layout.addLayout(brightness_layout)

        # --- Reset Button ---
        self.reset_button = QPushButton("恢复默认设置")
        self.reset_button.clicked.connect(self.reset_settings)
        self.main_layout.addWidget(self.reset_button)

        # --- Reminder Settings --- (Re-enabled)
        reminder_group = QGroupBox("用眼定时提醒 (20-20-20 法则)")
        reminder_layout = QVBoxLayout()
        self.reminder_enabled_checkbox = QCheckBox("启用定时提醒")
        self.reminder_enabled_checkbox.setChecked(self.settings.get("reminder_enabled", False))
        self.reminder_enabled_checkbox.toggled.connect(self.toggle_reminder)

        # Time settings layout
        time_layout = QHBoxLayout()
        self.work_time_label = QLabel("工作时长 (小时):") # Changed label
        self.work_time_spinbox = QSpinBox()
        self.work_time_spinbox.setRange(1, 12) # Sensible range for hours
        self.work_time_spinbox.setValue(self.settings.get("reminder_work_hours", 1)) # Use hours
        self.work_time_spinbox.valueChanged.connect(self.update_reminder_times)

        self.rest_time_label = QLabel("休息时长 (分钟):") # Changed label
        self.rest_time_spinbox = QSpinBox()
        self.rest_time_spinbox.setRange(1, 60) # Sensible range for minutes
        self.rest_time_spinbox.setValue(self.settings.get("reminder_rest_minutes", 5)) # Use minutes
        self.rest_time_spinbox.valueChanged.connect(self.update_reminder_times)

        time_layout.addWidget(self.work_time_label)
        time_layout.addWidget(self.work_time_spinbox)
        time_layout.addStretch() # Add space
        time_layout.addWidget(self.rest_time_label)
        time_layout.addWidget(self.rest_time_spinbox)

        reminder_layout.addWidget(self.reminder_enabled_checkbox)
        reminder_layout.addLayout(time_layout)
        reminder_group.setLayout(reminder_layout)
        self.main_layout.addWidget(reminder_group) # Re-enabled adding widget

        # Enable/disable spinboxes based on checkbox initial state
        self.work_time_spinbox.setEnabled(self.reminder_enabled_checkbox.isChecked())
        self.rest_time_spinbox.setEnabled(self.reminder_enabled_checkbox.isChecked())


        # --- Auto Start Settings --- (Re-enabled)
        auto_start_group = QGroupBox("常规设置")
        auto_start_layout = QVBoxLayout()
        self.auto_start_checkbox = QCheckBox("开机时自动启动 护目君") # Changed checkbox text back
        # Set initial state based on settings AND registry check for consistency
        initial_auto_start_setting = self.settings.get("auto_start_enabled", False)
        actual_auto_start_status = startup_manager.is_auto_start_enabled()
        if initial_auto_start_setting != actual_auto_start_status:
             logging.warning(f"Settings file auto-start ({initial_auto_start_setting}) differs from registry ({actual_auto_start_status}). Using registry status.")
             # Optionally update setting file here to match registry
             # self.settings["auto_start_enabled"] = actual_auto_start_status
             # sm.save_settings(self.settings) # Save the corrected state
             self.auto_start_checkbox.setChecked(actual_auto_start_status)
        else:
             self.auto_start_checkbox.setChecked(initial_auto_start_setting)

        self.auto_start_checkbox.toggled.connect(self.toggle_auto_start)
        auto_start_layout.addWidget(self.auto_start_checkbox)
        auto_start_group.setLayout(auto_start_layout)
        self.main_layout.addWidget(auto_start_group) # Re-enabled adding widget


        # --- Initialize Control States ---
        self.update_brightness_label() # Get initial brightness if possible

        # --- System Tray Icon (Basic Setup) ---
        # self.create_tray_icon() # Implement later

        # --- Initialize Control States ---
        # Apply initial temperature and brightness from loaded settings
        self.apply_initial_settings()
        # Update brightness label based on actual capability/value
        self.update_brightness_label()

        # --- System Tray Icon (Basic Setup) ---
        # self.create_tray_icon() # Implement later

        # --- Hotkey Manager --- (Re-enabled)
        self.hotkey_manager = HotkeyManager(self.settings.get("hotkeys", {}), self)
        self.hotkey_manager.hotkey_pressed.connect(self.handle_hotkey_press)
        logging.info("Attempting to start hotkey listener...") # ADDED LOG
        self.hotkey_manager.start_listening() # Re-enabled listener start
        logging.info("Hotkey listener started (or attempted).") # ADDED LOG

        logging.info("MainWindow initialized.")


    # --- Settings Load/Save ---
    def apply_initial_settings(self):
        """Apply the loaded temperature and brightness settings."""
        logging.info("Applying initial settings from loaded configuration.")
        # Apply temperature
        initial_temp = self.settings.get("temperature_kelvin", 6500)
        self.temp_label.setText(f"色温 (Kelvin): {initial_temp}K") # Update label immediately
        self.gamma_controller.set_temperature(initial_temp)

        # Apply brightness (if supported)
        if self.brightness_controller.is_supported():
            initial_brightness = self.settings.get("brightness_percent", 80)
            self.brightness_label.setText(f"亮度 (%): {initial_brightness}%") # Update label immediately
            self.brightness_controller.set_brightness(initial_brightness, smooth_transition=False)
        else:
            # Ensure slider is disabled if brightness not supported
             self.brightness_slider.setEnabled(False)


    def save_current_settings(self):
        """Gather current UI state and save it to the settings file."""
        self.settings["temperature_kelvin"] = self.temp_slider.value()
        if self.brightness_controller.is_supported():
            # Only save brightness if it's supported and controllable
            # Use slider value as the target, even if get_brightness fails sometimes
            self.settings["brightness_percent"] = self.brightness_slider.value()
        # Re-enabled reminder settings saving
        self.settings["reminder_enabled"] = self.reminder_enabled_checkbox.isChecked()
        self.settings["reminder_work_hours"] = self.work_time_spinbox.value() # Save hours
        self.settings["reminder_rest_minutes"] = self.rest_time_spinbox.value() # Save minutes
        self.settings["auto_start_enabled"] = self.auto_start_checkbox.isChecked() # Re-enabled auto-start state saving

        logging.debug(f"Saving settings: {self.settings}")
        sm.save_settings(self.settings)


    # --- Reminder Control Logic --- (Re-enabled)
    def toggle_reminder(self, checked):
        """Enable or disable the reminder timer based on checkbox state."""
        self.work_time_spinbox.setEnabled(checked)
        self.rest_time_spinbox.setEnabled(checked)
        if checked:
            logging.info("Reminder enabled by user.")
            self.update_reminder_times() # Start timer with current values
        else:
            logging.info("Reminder disabled by user.")
            self.reminder_manager.stop_timer()
        self.save_current_settings() # Save the toggle state

    def update_reminder_times(self):
        """Update reminder durations when spinboxes change and restart timer if enabled."""
        work_hours = self.work_time_spinbox.value()
        rest_minutes = self.rest_time_spinbox.value()
        logging.info(f"Reminder times updated: Work={work_hours}h, Rest={rest_minutes}m")
        self.reminder_manager.set_durations(work_hours, rest_minutes)
        if self.reminder_enabled_checkbox.isChecked():
            self.reminder_manager.start_timer() # Restart timer with new values
        self.save_current_settings() # Save the new time settings


    # --- Slider Callbacks ---
    def on_temperature_change(self, value):
        """Handle temperature slider changes."""
        kelvin = value
        # Ensure value aligns with slider steps if needed (though slider handles range)
        self.temp_label.setText(f"色温 (Kelvin): {kelvin}K")
        logging.debug(f"Slider changed, setting temperature to {kelvin}K")
        if self.gamma_controller.set_temperature(kelvin):
            self.save_current_settings() # Save on successful change

    def on_brightness_change(self, value):
        """Handle brightness slider changes."""
        level = value
        self.brightness_label.setText(f"亮度 (%): {level}%")
        logging.debug(f"Slider changed, setting brightness to {level}%")
        if self.brightness_controller.set_brightness(level, smooth_transition=False): # Direct set for responsiveness
             self.save_current_settings() # Save on successful change

    def update_brightness_label(self):
        """Update brightness label and slider with current value."""
        if self.brightness_controller.is_supported():
            current_brightness = self.brightness_controller.get_brightness()
            if current_brightness != -1:
                self.brightness_label.setText(f"亮度 (%): {current_brightness}%")
                # Update slider without triggering valueChanged signal
                self.brightness_slider.blockSignals(True)
                self.brightness_slider.setValue(current_brightness)
                self.brightness_slider.blockSignals(False)
            else:
                self.brightness_label.setText("亮度 (%): 获取失败")
                self.brightness_slider.setEnabled(False) # Disable if getting failed
        else:
             self.brightness_label.setText("亮度 (%): 不支持")
             self.brightness_slider.setEnabled(False)

    def reset_settings(self):
        """Reset temperature and brightness to defaults."""
        logging.info("Resetting settings to default.")
        # Reset temperature
        default_temp = 6500
        self.temp_slider.setValue(default_temp) # This will trigger on_temperature_change
        # self.gamma_controller.reset_gamma() # Slider change already calls set_temperature

        # Reset brightness (if supported)
        if self.brightness_controller.is_supported():
            # What's the 'default' brightness? Often 100% or last user setting.
            # Let's try setting to 80% as a sensible default reset.
            default_brightness = 80
            # We need to get the *actual* default from the system if possible,
            # but WMI doesn't provide a 'reset' function easily.
            # Setting to a fixed value like 80 or 100 is a common approach.
            self.brightness_slider.setValue(default_brightness) # This triggers on_brightness_change
            # self.brightness_controller.set_brightness(default_brightness)

        logging.info("Settings reset (Temperature to 6500K, Brightness attempt to 80%).")
        # Save the reset state
        self.save_current_settings()


    # --- Hotkey Handling --- (Re-enabled)
    def handle_hotkey_press(self, hotkey_str):
        """Applies the profile associated with the pressed hotkey."""
        logging.info(f"Hotkey pressed: {hotkey_str}")
        profile_name = self.settings.get("hotkeys", {}).get(hotkey_str)

        if not profile_name:
            logging.warning(f"No profile associated with hotkey: {hotkey_str}")
            return

        profile_settings = self.settings.get("profiles", {}).get(profile_name)
        if not profile_settings:
            logging.warning(f"Profile '{profile_name}' not found in settings for hotkey {hotkey_str}")
            return

        logging.info(f"Applying profile '{profile_name}' triggered by hotkey {hotkey_str}")

        # Apply temperature
        temp = profile_settings.get("temperature")
        if temp is not None:
            self.temp_slider.setValue(temp) # This triggers on_temperature_change -> save_current_settings

        # Apply brightness (if supported)
        brightness = profile_settings.get("brightness")
        if brightness is not None and self.brightness_controller.is_supported():
             self.brightness_slider.setValue(brightness) # This triggers on_brightness_change -> save_current_settings

        # Note: We don't save settings here directly, as the slider value changes
        # already trigger the save. If they didn't, we would call self.save_current_settings() here.


    # --- Placeholder for Tray Icon ---
    # def create_tray_icon(self):
    #     pass # Implement later

    # --- Handle Window Closing ---
    def closeEvent(self, event):
        """Stop listener, save settings before closing the window.""" # Re-enabled listener stop
        logging.info("Window close event triggered.")
        logging.info("Stopping hotkey listener...") # Re-enabled log
        self.hotkey_manager.stop_listening() # Stop listener first # Re-enabled call

        # Record usage statistics before saving settings (in case saving fails)
        try:
            end_time = datetime.datetime.now()
            usage_duration = end_time - self.start_time
            usage_seconds = int(usage_duration.total_seconds())
            rests_today = self.reminder_manager.get_rest_periods_today() # Re-enabled reminder dependency
            # rests_today = 0 # Placeholder or remove stats if reminder is gone
            logging.info(f"Recording daily stats: Usage={usage_seconds}s, Rests={rests_today}")
            stats_manager.record_daily_summary(usage_seconds, rests_today)
        except Exception as e:
            logging.error(f"Failed to record usage statistics: {e}")

        logging.info("Saving final settings.")
        self.save_current_settings()

        # Optional: Reset gamma/brightness on close? Usually not desired.
        # self.reset_settings()
        super().closeEvent(event) # Proceed with closing


    # --- Auto Start Toggle --- (Re-enabled)
    def toggle_auto_start(self, checked):
        """Enable or disable auto-start based on checkbox state."""
        success = False
        if checked:
            logging.info("User enabled auto-start.")
            success = startup_manager.enable_auto_start()
            if not success:
                logging.error("Failed to enable auto-start via registry.")
                # Uncheck the box visually if enabling failed
                self.auto_start_checkbox.setChecked(False)
        else:
            logging.info("User disabled auto-start.")
            success = startup_manager.disable_auto_start()
            if not success:
                logging.error("Failed to disable auto-start via registry.")
                # Re-check the box visually if disabling failed
                self.auto_start_checkbox.setChecked(True)

        # Save the setting only if the registry operation was potentially successful
        # or if the user intended to disable it (even if it wasn't there).
        # We update the setting based on the *intended* state unless the operation failed critically.
        if success or not checked: # Save if enable worked, or if user disabled
             self.settings["auto_start_enabled"] = self.auto_start_checkbox.isChecked() # Use current checkbox state after potential revert
             self.save_current_settings()


# Example Usage (for testing this window directly)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
