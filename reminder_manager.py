# -*- coding: utf-8 -*-

import logging
from PySide6.QtCore import QObject, QTimer, Signal
from plyer import notification
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReminderManager(QObject):
    """Manages the work/rest reminder timer and notifications."""

    # Signals to update the GUI status label
    status_updated = Signal(str)
    # Signal to indicate a rest period should start (e.g., for full-screen overlay)
    rest_period_started = Signal(int) # Sends rest duration in seconds
    # Signal to indicate a rest period has ended
    rest_period_ended = Signal()

    STATE_IDLE = "idle" # Timer stopped or not started
    STATE_WORKING = "working"
    STATE_RESTING = "resting"

    def __init__(self, parent=None):
        super().__init__(parent)
        # Store durations in the units received (hours, minutes)
        self.work_hours = 1
        self.rest_minutes = 5
        self.state = self.STATE_IDLE
        self.remaining_seconds = 0 # Internal timer always uses seconds
        self.rest_periods_today = 0 # Counter for stats

        self.timer = QTimer(self)
        self.timer.setInterval(1000) # Tick every second
        self.timer.timeout.connect(self.tick)

        logging.info("ReminderManager initialized.")

    def set_durations(self, work_hours, rest_minutes):
        """Update the work (hours) and rest (minutes) durations."""
        self.work_hours = work_hours
        self.rest_minutes = rest_minutes
        logging.info(f"Durations updated: Work={self.work_hours}h, Rest={self.rest_minutes}m")
        # If timer is running, restart with new durations for the next cycle
        if self.timer.isActive():
            self.start_timer() # Restart will reset to working state

    def start_timer(self):
        """Starts or restarts the work timer (using hours)."""
        if self.work_hours <= 0:
            logging.warning("Cannot start timer with zero or negative work hours.")
            self.status_updated.emit("错误: 工作时长无效")
            return

        logging.info("Starting reminder timer.")
        self.state = self.STATE_WORKING
        # Convert work hours to seconds for the internal timer
        self.remaining_seconds = self.work_hours * 3600
        self.update_status_display()
        self.timer.start()

    def stop_timer(self):
        """Stops the timer."""
        if self.timer.isActive():
            logging.info("Stopping reminder timer.")
            self.timer.stop()
        self.state = self.STATE_IDLE
        self.remaining_seconds = 0
        self.status_updated.emit("状态: 已禁用")


    def tick(self):
        """Called every second by the QTimer."""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_status_display()
        else:
            # Time's up, switch state
            if self.state == self.STATE_WORKING:
                self.start_rest_period()
            elif self.state == self.STATE_RESTING:
                self.end_rest_period()

    def start_rest_period(self):
        """Initiate the rest period (using minutes)."""
        logging.info("Work time finished. Starting rest period.")
        self.state = self.STATE_RESTING
        # Convert rest minutes to seconds for the internal timer
        self.remaining_seconds = self.rest_minutes * 60
        self.rest_periods_today += 1 # Increment rest counter
        logging.info(f"Rest periods today: {self.rest_periods_today}")
        self.update_status_display()
        self.rest_period_started.emit(self.remaining_seconds) # Send rest duration in seconds
        self.send_notification("休息时间到了！", f"请休息 {self.rest_minutes} 分钟。") # Update notification text

    def end_rest_period(self):
        """End the rest period and start the next work cycle."""
        logging.info("Rest time finished. Starting next work period.")
        self.rest_period_ended.emit() # Notify GUI/overlay
        # Restart the work timer immediately
        self.start_timer()

    def update_status_display(self):
        """Update the status string based on current state and time."""
        if self.state == self.STATE_WORKING:
            total_seconds = self.remaining_seconds
            hours = total_seconds // 3600
            mins = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            status_text = f"状态: 工作中... 剩余 {hours:02d}:{mins:02d}:{secs:02d}" # Show H:M:S
        elif self.state == self.STATE_RESTING:
             total_seconds = self.remaining_seconds
             mins = total_seconds // 60
             secs = total_seconds % 60
             status_text = f"状态: 休息中... 剩余 {mins:02d}:{secs:02d}" # Show M:S
        else: # STATE_IDLE
            status_text = "状态: 已停止" # Or "已禁用" if stopped via checkbox

        self.status_updated.emit(status_text)


    def send_notification(self, title, message):
        """Sends a desktop notification using plyer."""
        logging.info(f"Sending notification: Title='{title}', Message='{message}'")
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Eye Protector",
                timeout=10 # Notification disappears after 10 seconds
                # app_icon='path/to/icon.ico' # Add icon later
            )
        except Exception as e:
            logging.error(f"Failed to send notification using plyer: {e}")
            # Fallback or alternative notification method could be added here

    def get_rest_periods_today(self):
        """Returns the number of rest periods triggered today."""
        return self.rest_periods_today
