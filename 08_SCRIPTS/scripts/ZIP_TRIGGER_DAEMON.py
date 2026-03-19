
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from CI_AUTOMATION_LAYER import trigger_pipeline

WATCH_PATHS = ["F:/", "Z:/", "E:/"]  # Paths to monitor
TRIGGER_EXTENSIONS = [".zip"]

class ZipHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and any(event.src_path.lower().endswith(ext) for ext in TRIGGER_EXTENSIONS):
            file_path = event.src_path
            case_number = os.path.basename(file_path).split('.')[0]  # crude parse
            print(f"[+] Detected ZIP: {file_path} → Triggering pipeline...")
            try:
                trigger_pipeline(case_number, "MiFile")
                print(f"[✓] Triggered for case: {case_number}")
            except Exception as e:
                print(f"[✗] Error triggering pipeline for {file_path}: {e}")

if __name__ == "__main__":
    observers = []
    for path in WATCH_PATHS:
        if os.path.exists(path):
            print(f"[*] Watching {path} for new ZIPs...")
            event_handler = ZipHandler()
            observer = Observer()
            observer.schedule(event_handler, path, recursive=True)
            observer.start()
            observers.append(observer)
        else:
            print(f"[!] Path not found: {path}")

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        for o in observers:
            o.stop()
        for o in observers:
            o.join()
