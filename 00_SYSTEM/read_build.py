"""Read build script key sections."""
lines = open(r"C:\Users\andre\LitigationOS\scripts\mbp_build.py", encoding="utf-8").readlines()
for i, line in enumerate(lines[20:85], start=21):
    print(f"{i}: {line}", end="")
