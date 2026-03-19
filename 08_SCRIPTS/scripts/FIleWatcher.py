import os
import time

WATCH_PATH = "F:\\"  # Make sure to keep the trailing backslash for Windows
LOG_FILE = "F:\\FRED_file_watch.log"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.ctime()} - {msg}\n")

def watch_directory(path):
    seen = set(os.listdir(path))
    log("File watcher started. Monitoring F:\ drive...")
    while True:
        try:
            current_files = set(os.listdir(path))
            new_files = current_files - seen
            for file in new_files:
                log(f"New file detected: {file}")
            seen = current_files
            time.sleep(5)  # Check every 5 seconds
        except Exception as e:
            log(f"Error: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    watch_directory(WATCH_PATH)
