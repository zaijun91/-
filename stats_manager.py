# -*- coding: utf-8 -*-

import csv
import os
import logging
import datetime
import appdirs # Use appdirs again for consistency

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_NAME = "EyeProtector"
APP_AUTHOR = "ClineUser" # Match settings_manager
STATS_FILE = "usage_stats.csv"
CSV_HEADER = ["date", "total_usage_seconds", "rest_periods_taken"] # Simplified header for now

def get_stats_path():
    """Gets the full path to the statistics CSV file."""
    data_dir = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
    # Ensure data directory exists (might have been created by settings_manager)
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            logging.info(f"Created application data directory for stats: {data_dir}")
        except OSError as e:
            logging.error(f"Failed to create data directory {data_dir}: {e}")
            # Fallback to current directory
            return os.path.join(".", STATS_FILE)
    return os.path.join(data_dir, STATS_FILE)

def initialize_stats_file():
    """Creates the CSV file and writes the header if it doesn't exist."""
    stats_path = get_stats_path()
    if not os.path.exists(stats_path):
        try:
            with open(stats_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(CSV_HEADER)
            logging.info(f"Initialized statistics file: {stats_path}")
        except IOError as e:
            logging.error(f"Failed to initialize statistics file {stats_path}: {e}")

def record_daily_summary(usage_seconds, rest_periods):
    """
    Appends or updates the daily summary for today in the CSV file.

    :param usage_seconds: Total seconds the application was used today.
    :param rest_periods: Number of rest periods triggered today.
    """
    stats_path = get_stats_path()
    initialize_stats_file() # Ensure file and header exist

    today_date_str = datetime.date.today().isoformat()
    updated = False
    rows = []

    try:
        # Read existing data
        with open(stats_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader) # Skip header
            rows.append(header)
            for row in reader:
                if row and row[0] == today_date_str:
                    # Update today's entry
                    current_usage = int(row[1])
                    current_rests = int(row[2])
                    row[1] = str(current_usage + usage_seconds) # Accumulate usage
                    row[2] = str(current_rests + rest_periods) # Accumulate rests
                    updated = True
                    logging.info(f"Updating stats for {today_date_str}: usage={row[1]}s, rests={row[2]}")
                rows.append(row)

        # If today's entry wasn't found, append a new one
        if not updated:
            new_row = [today_date_str, str(usage_seconds), str(rest_periods)]
            rows.append(new_row)
            logging.info(f"Appending new stats for {today_date_str}: usage={usage_seconds}s, rests={rest_periods}")

        # Write data back to the file
        with open(stats_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)
        return True

    except (IOError, csv.Error, ValueError, IndexError) as e:
        logging.error(f"Failed to read or write statistics file {stats_path}: {e}")
        return False

# Example Usage (for testing)
if __name__ == "__main__":
    print("Testing stats manager...")
    try:
        import appdirs
    except ImportError:
        print("Please install 'appdirs': pip install appdirs")
        exit()

    print(f"Stats file path: {get_stats_path()}")

    # Simulate recording data
    print("\nRecording summary 1 (Usage: 3600s, Rests: 5)...")
    record_daily_summary(usage_seconds=3600, rest_periods=5)

    print("\nRecording summary 2 (Usage: 1800s, Rests: 2)...")
    record_daily_summary(usage_seconds=1800, rest_periods=2)

    print("\nReading final stats file:")
    try:
        with open(get_stats_path(), 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                print(row)
    except FileNotFoundError:
        print("Stats file not found.")
    except Exception as e:
        print(f"Error reading stats file: {e}")

    print("\nTest complete.")
