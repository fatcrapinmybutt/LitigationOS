"""
Scans exhibits for common errors and format issues before manifest logging.
"""

import os

def perform_quality_check(filepath):
    filename = os.path.basename(filepath)
    if " " in filename or any(c in filename for c in ['[', ']', '(', ')']):
        raise ValueError(f"Invalid characters in filename: {filename}")
    if not os.path.getsize(filepath):
        raise ValueError(f"File is empty: {filename}")