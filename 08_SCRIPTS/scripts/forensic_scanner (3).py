import os
import datetime

LOG_PATH = './output/violation_log.json'
TIMELINE_PATH = './output/timeline.json'

def scan_directory(root):
    events = []
    violations = []
    for dirpath, _, filenames in os.walk(root):
        for file in filenames:
            path = os.path.join(dirpath, file)
            if file.lower().endswith(('.pdf', '.docx', '.txt', '.json')):
                events.append({
                    "event": "Document scanned",
                    "file": file,
                    "path": path,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                if 'show cause' in file.lower() or 'order' in file.lower():
                    violations.append({
                        "type": "ORDER/SHOW CAUSE",
                        "detail": "Review for MCR 3.606(B), MCL 600.1711, and Benchbook §2.4(B)",
                        "file": file,
                        "path": path
                    })
                elif 'motion' in file.lower():
                    violations.append({
                        "type": "Motion Filing",
                        "detail": "Validate MCR 2.119 compliance and form linkage",
                        "file": file,
                        "path": path
                    })
    return events, violations

def write_log(data, path):
    import json
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    base = "F:/"
    print("[SCAN] Running F:/ legal forensic scan...")
    events, violations = scan_directory(base)
    write_log(events, TIMELINE_PATH)
    write_log(violations, LOG_PATH)
    print(f"[DONE] Scan Complete: {len(events)} files scanned. {len(violations)} issues flagged.")