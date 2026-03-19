#!/usr/bin/env python3
"""Disk Space Guard — abort operations if space is too low."""
import ctypes, sys

MIN_FREE_BYTES = 2 * 1024**3  # 2GB

def check_drive(drive_letter):
    free = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(f"{drive_letter}:\\", None, None, ctypes.byref(free))
    return free.value

def guard(drive_letter):
    free = check_drive(drive_letter)
    free_gb = free / (1024**3)
    if free < MIN_FREE_BYTES:
        print(f"ABORT: {drive_letter}: only {free_gb:.2f}GB free (min {MIN_FREE_BYTES/(1024**3):.0f}GB)")
        return False
    return True

if __name__ == "__main__":
    drive = sys.argv[1] if len(sys.argv) > 1 else "C"
    if guard(drive):
        print(f"OK: {drive}: has sufficient space")
        sys.exit(0)
    sys.exit(1)
