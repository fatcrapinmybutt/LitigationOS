"""Final quality audit of all vehicle filings."""
import os, re

vehicles = r"C:\Users\andre\LitigationOS\06_VEHICLES"
total_mcr = 0
total_mcl = 0
total_chess = 0
total_size = 0
file_count = 0

for root, dirs, files in os.walk(vehicles):
    for f in files:
        if not f.endswith(".md"):
            continue
        fp = os.path.join(root, f)
        try:
            content = open(fp, "r", encoding="utf-8", errors="ignore").read()
        except:
            continue
        
        mcr = len(re.findall(r"MCR \d", content))
        mcl = len(re.findall(r"MCL \d", content))
        chess = len(re.findall(r"(?i)(Anticipated Defense|Pre-Rebuttal|Watson.*?may argue|Barnes.*?may argue|defense.*?fails)", content))
        evidence = len(re.findall(r"(?i)(Exhibit [A-Z]|LC Record|Tr\. |hearing.*?\d{4})", content))
        size = os.path.getsize(fp)
        
        total_mcr += mcr
        total_mcl += mcl
        total_chess += chess
        total_size += size
        file_count += 1
        
        lane = os.path.basename(root)
        print(f"  {lane:40s} {f:50s} {size//1024:>4}KB  MCR:{mcr:>3}  MCL:{mcl:>3}  Chess:{chess:>3}  Evidence:{evidence:>3}")

print()
print("=" * 70)
print("FINAL QUALITY AUDIT")
print("=" * 70)
print(f"Total filings: {file_count}")
print(f"Total size: {total_size // 1024}KB")
print(f"Total MCR citations: {total_mcr}")
print(f"Total MCL citations: {total_mcl}")
print(f"Total chess-mode markers: {total_chess}")
if file_count > 0:
    print(f"Avg citations per file: {(total_mcr + total_mcl) / file_count:.1f}")
print("=" * 70)
