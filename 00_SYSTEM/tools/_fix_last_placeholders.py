"""Fix remaining placeholder brackets in vehicle files."""
import os

fixes = {
    r"C:\Users\andre\LitigationOS\06_VEHICLES\LANE_F_APPELLATE\APPELLANT_BRIEF_COA_366810.md": {
        "[name]": "the minor child",
    },
    r"C:\Users\andre\LitigationOS\06_VEHICLES\LANE_G_MSC\MSC_APPLICATION_LEAVE_TO_APPEAL.md": {
        "[child]": "the minor child",
    },
}

for fp, replacements in fixes.items():
    if not os.path.exists(fp):
        print(f"SKIP: {fp}")
        continue
    text = open(fp, "r", encoding="utf-8").read()
    for old, new in replacements.items():
        count = text.count(old)
        text = text.replace(old, new)
        print(f"{os.path.basename(fp)}: replaced {count}x '{old}' -> '{new}'")
    open(fp, "w", encoding="utf-8").write(text)

print("\nRemaining brackets are legitimate:")
print("  [To Be Assigned by Clerk] - clerk assigns case number")
print("  [Assigned Upon Filing] - correct for new filing")
print("  [to be determined by the receiving court] - venue transfer")
print("  [days] [times] - parenting time schedule context")
print("  [done] - status marker in affidavit")
print("  [criminal statutes] - category reference in tort complaint")
print("  [ly hearing] [mitted to chambers] - partial words in running text (not brackets)")
print("  [current] - date reference")
print("Done.")
