import sqlite3, json, os, re
from collections import Counter, defaultdict

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.row_factory = sqlite3.Row

# Schema check
cols = [r[1] for r in conn.execute("PRAGMA table_info(timeline_events)")]
print("timeline_events columns:", cols)

total = conn.execute("SELECT COUNT(*) FROM timeline_events").fetchone()[0]
print(f"Total timeline events: {total}")

# Get events with adversary mentions
adversaries = {
    "Emily Watson": ["emily","watson","defendant","mother"],
    "Albert Watson": ["albert watson","albert"],
    "Lori Watson": ["lori watson","lori"],
    "Judge McNeill": ["mcneill","judge","court"],
    "Ronald Berry": ["ronald berry","ron berry"],
    "Cavan Berry": ["cavan berry","cavan","magistrate"],
    "Pamela Rusco": ["rusco","pamela","foc","friend of court"],
    "Jennifer Barnes": ["barnes","jennifer","attorney","counsel"],
    "Rachel Baxter": ["rachel","baxter","wren"],
    "Hon. Kenneth Hoopes": ["hoopes","chief judge"],
    "Hon. Maria Ladas-Hoopes": ["ladas","maria"],
}

# Categorize events by adversary and type
adv_events = defaultdict(list)
weaponizable = []

# Process in batches
batch_size = 5000
offset = 0
while offset < total:
    rows = conn.execute(f"SELECT * FROM timeline_events LIMIT {batch_size} OFFSET {offset}").fetchall()
    if not rows:
        break
    for r in rows:
        text = " ".join(str(r[c] or "") for c in cols).lower()
        matched_advs = []
        for adv, kws in adversaries.items():
            if any(kw in text for kw in kws):
                matched_advs.append(adv)
        
        if matched_advs:
            evt = {c: r[c] for c in cols}
            evt["adversaries"] = matched_advs
            
            # Detect weaponizable patterns
            weapons = []
            wtext = text
            if any(w in wtext for w in ["false","fabricat","lie","untrue","misrepresent","perjur"]):
                weapons.append("FALSE_ALLEGATION")
            if any(w in wtext for w in ["ex parte","without notice","no notice","unilateral"]):
                weapons.append("EX_PARTE")
            if any(w in wtext for w in ["withhold","deny","refus","block","prevent","restrict"]):
                weapons.append("PARENTING_TIME_DENIAL")
            if any(w in wtext for w in ["contempt","jail","incarcerat","arrest","detain"]):
                weapons.append("CONTEMPT_ABUSE")
            if any(w in wtext for w in ["ppo","protection order","stalking","harass"]):
                weapons.append("PPO_WEAPONIZATION")
            if any(w in wtext for w in ["bias","prejudic","unfair","one-sided","partial"]):
                weapons.append("JUDICIAL_BIAS")
            if any(w in wtext for w in ["alienat","interfere","obstruct","manipulat","undermine"]):
                weapons.append("PARENTAL_ALIENATION")
            if any(w in wtext for w in ["evidence","exclud","suppress","ignor","disregard"]):
                weapons.append("EVIDENCE_SUPPRESSION")
            if any(w in wtext for w in ["due process","rights","constitutional","violat"]):
                weapons.append("DUE_PROCESS_VIOLATION")
            
            if weapons:
                evt["weapon_types"] = weapons
                weaponizable.append(evt)
            
            for adv in matched_advs:
                adv_events[adv].append(evt)
    
    offset += batch_size
    print(f"  Processed {min(offset, total)}/{total}...")

# Summary
print(f"\nTotal adversary-linked events: {sum(len(v) for v in adv_events.values())}")
print(f"Weaponizable events: {len(weaponizable)}")

print("\nEvents per adversary:")
for adv in sorted(adv_events.keys(), key=lambda a: -len(adv_events[a])):
    print(f"  {adv}: {len(adv_events[adv])}")

# Weapon type distribution
weapon_counts = Counter()
for evt in weaponizable:
    for w in evt.get("weapon_types", []):
        weapon_counts[w] += 1

print("\nWeapon type distribution:")
for w, c in weapon_counts.most_common():
    print(f"  {w}: {c}")

# Adversary × Weapon matrix
print("\nAdversary × Weapon Matrix:")
adv_weapon = defaultdict(lambda: Counter())
for evt in weaponizable:
    for adv in evt["adversaries"]:
        for w in evt["weapon_types"]:
            adv_weapon[adv][w] += 1

for adv in sorted(adv_weapon.keys(), key=lambda a: -sum(adv_weapon[a].values())):
    top3 = adv_weapon[adv].most_common(3)
    top_str = ", ".join(f"{w}={c}" for w,c in top3)
    print(f"  {adv}: {sum(adv_weapon[adv].values())} total — {top_str}")

# Save weaponizable events
out = r"D:\LitigationOS_tmp\weaponizable_timeline.json"
clean = []
for evt in weaponizable[:5000]:
    d = {}
    for k,v in evt.items():
        if isinstance(v, list):
            d[k] = v
        else:
            d[k] = str(v) if v is not None else None
    clean.append(d)
with open(out, "w") as f:
    json.dump(clean, f, indent=2)
print(f"\nSaved: {out} ({len(clean)} events)")

conn.close()
