"""
Centralized logging of errors during the intake pipeline.
"""

def log_error(msg):
    with open("F:/FRED-LITIGATION-OS/Exhibit Intake/error.log", "a") as f:
        f.write(msg + "\n")