"""PASS 8: Filing Readiness Dashboard (HTML)."""
import os, json
from datetime import datetime, date

DELTA99 = r"I:\LitigationOS_Delta99"
DASHBOARD = os.path.join(DELTA99, "DASHBOARD.html")
LOG = r"I:\DRIVE_ORG\operations.log"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

PKG_NAMES = {
    "PKG01": "Emergency Parenting Time",
    "PKG02": "Vacate/Terminate PPO",
    "PKG03": "Disqualify Judge McNeill",
    "PKG04": "Void Ex Parte Orders",
    "PKG05": "COA Appellant Brief",
    "PKG06": "JTC Request for Investigation",
    "PKG07": "MSC Application for Leave",
    "PKG08": "Contempt Motion (PT)",
    "PKG09": "Housing Complaint",
    "PKG10": "Federal 42 USC 1983",
    "PKG11": "Spoliation Notice",
    "PKG12": "FOC Objection"
}

def run():
    log("PASS 8: FILING READINESS DASHBOARD")
    
    # Load evidence map
    emap_path = os.path.join(DELTA99, "EVIDENCE_MAP.json")
    emap = {}
    if os.path.exists(emap_path):
        with open(emap_path, "r") as f:
            emap = json.load(f)
    
    # Scan packages
    packages = sorted([d for d in os.listdir(DELTA99) if d.startswith("PKG") and os.path.isdir(os.path.join(DELTA99, d))])
    
    pkg_data = []
    for pkg in packages:
        pkg_dir = os.path.join(DELTA99, pkg)
        files = [f for f in os.listdir(pkg_dir) if os.path.isfile(os.path.join(pkg_dir, f))]
        
        has_proof = any("PROOFREAD" in f.upper() for f in files)
        has_manifest = any("MANIFEST" in f.upper() for f in files)
        has_exhibits = any("EXHIBIT" in f.upper() for f in files)
        has_motion = any(f.endswith(".md") and ("MOTION" in f.upper() or "BRIEF" in f.upper() or "COMPLAINT" in f.upper() or "APPLICATION" in f.upper() or "NOTICE" in f.upper() or "OBJECTION" in f.upper()) for f in files)
        
        proof_status = "PASS"
        proof_file = [f for f in files if "PROOFREAD" in f.upper()]
        if proof_file:
            try:
                with open(os.path.join(pkg_dir, proof_file[0]), "r", encoding="utf-8", errors="ignore") as pf:
                    content = pf.read()
                    if "FAIL" in content.upper() and "PASS" not in content.upper().split("FAIL")[0][-20:]:
                        proof_status = "FAIL"
            except:
                proof_status = "UNKNOWN"
        else:
            proof_status = "MISSING"
        
        ev_info = emap.get("packages", {}).get(pkg, {})
        gaps = len(ev_info.get("gaps", []))
        
        total_size = sum(os.path.getsize(os.path.join(pkg_dir, f)) for f in files)
        
        pkg_data.append({
            "id": pkg,
            "name": PKG_NAMES.get(pkg.split("_")[0] + "_" + "_".join(pkg.split("_")[1:3]) if len(pkg.split("_")) > 2 else pkg[:5], pkg),
            "files": len(files),
            "size_kb": round(total_size / 1024),
            "has_motion": has_motion,
            "has_proof": has_proof,
            "has_manifest": has_manifest,
            "has_exhibits": has_exhibits,
            "proof_status": proof_status,
            "evidence_gaps": gaps
        })
    
    # COA deadline countdown
    coa_deadline = date(2026, 4, 15)
    days_left = (coa_deadline - date.today()).days
    
    # Drive space
    drive_info = []
    for letter in ["C", "D", "F", "G", "H", "I"]:
        try:
            import shutil
            usage = shutil.disk_usage(f"{letter}:\\")
            drive_info.append({"drive": letter, "free_gb": round(usage.free / 1024**3, 1), "total_gb": round(usage.total / 1024**3, 1)})
        except:
            pass
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>LitigationOS Delta99 - Filing Readiness Dashboard</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0a; color: #e0e0e0; padding: 20px; }}
h1 {{ color: #00ff88; font-size: 28px; margin-bottom: 5px; }}
h2 {{ color: #00ccff; font-size: 20px; margin: 20px 0 10px; }}
.subtitle {{ color: #888; font-size: 14px; margin-bottom: 20px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 15px; }}
.card {{ background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 15px; }}
.card.pass {{ border-left: 4px solid #00ff88; }}
.card.fail {{ border-left: 4px solid #ff4444; }}
.card.warn {{ border-left: 4px solid #ffaa00; }}
.card-title {{ font-size: 16px; font-weight: bold; margin-bottom: 8px; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
.badge-pass {{ background: #00ff88; color: #000; }}
.badge-fail {{ background: #ff4444; color: #fff; }}
.badge-warn {{ background: #ffaa00; color: #000; }}
.badge-info {{ background: #00ccff; color: #000; }}
.stat {{ display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #222; font-size: 13px; }}
.stat:last-child {{ border-bottom: none; }}
.countdown {{ text-align: center; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 2px solid #00ccff; border-radius: 12px; margin-bottom: 20px; }}
.countdown .days {{ font-size: 72px; font-weight: bold; color: {'#ff4444' if days_left < 30 else '#ffaa00' if days_left < 90 else '#00ff88'}; }}
.countdown .label {{ font-size: 14px; color: #888; }}
.drives {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0; }}
.drive {{ background: #1a1a2e; padding: 8px 12px; border-radius: 6px; font-size: 12px; }}
.bar {{ height: 6px; background: #333; border-radius: 3px; margin-top: 4px; }}
.bar-fill {{ height: 100%; border-radius: 3px; }}
.summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0; }}
.summary-item {{ text-align: center; padding: 15px; background: #1a1a2e; border-radius: 8px; }}
.summary-num {{ font-size: 32px; font-weight: bold; }}
.summary-label {{ font-size: 12px; color: #888; }}
table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #222; font-size: 13px; }}
th {{ color: #00ccff; font-size: 12px; text-transform: uppercase; }}
</style>
</head>
<body>
<h1>LITIGATIONOS DELTA99</h1>
<div class="subtitle">Pigors v. Watson | Case 2024-001507-DC | 14th Circuit, Muskegon County | Generated {datetime.now().strftime('%B %d, %Y %H:%M')}</div>

<div class="countdown">
<div class="days">{days_left}</div>
<div class="label">DAYS TO COA DEADLINE (April 15, 2026) | Case 366810</div>
</div>

<div class="summary">
<div class="summary-item"><div class="summary-num" style="color:#00ff88">{len(packages)}</div><div class="summary-label">FILING PACKAGES</div></div>
<div class="summary-item"><div class="summary-num" style="color:#00ccff">{sum(p['files'] for p in pkg_data)}</div><div class="summary-label">TOTAL FILES</div></div>
<div class="summary-item"><div class="summary-num" style="color:{'#00ff88' if sum(1 for p in pkg_data if p['proof_status']=='PASS') == len(packages) else '#ffaa00'}">{sum(1 for p in pkg_data if p['proof_status']=='PASS')}/{len(packages)}</div><div class="summary-label">PROOFREAD PASS</div></div>
<div class="summary-item"><div class="summary-num" style="color:{'#ff4444' if sum(p['evidence_gaps'] for p in pkg_data) > 0 else '#00ff88'}">{sum(p['evidence_gaps'] for p in pkg_data)}</div><div class="summary-label">EVIDENCE GAPS</div></div>
</div>

<h2>PACKAGE STATUS</h2>
<div class="grid">
"""
    
    for p in pkg_data:
        status_class = "pass" if p["proof_status"] == "PASS" and p["evidence_gaps"] == 0 else "fail" if p["proof_status"] == "FAIL" else "warn"
        proof_badge = f'<span class="badge badge-pass">PROOF PASS</span>' if p["proof_status"] == "PASS" else f'<span class="badge badge-fail">PROOF FAIL</span>'
        gap_badge = f'<span class="badge badge-pass">EVIDENCE OK</span>' if p["evidence_gaps"] == 0 else f'<span class="badge badge-warn">{p["evidence_gaps"]} GAPS</span>'
        
        name = PKG_NAMES.get(p["id"][:5], p["id"])
        
        html += f"""<div class="card {status_class}">
<div class="card-title">{p['id'][:5]}: {name}</div>
{proof_badge} {gap_badge}
<div style="margin-top:8px">
<div class="stat"><span>Files</span><span>{p['files']}</span></div>
<div class="stat"><span>Size</span><span>{p['size_kb']} KB</span></div>
<div class="stat"><span>Motion/Brief</span><span>{'YES' if p['has_motion'] else 'NO'}</span></div>
<div class="stat"><span>Manifest</span><span>{'YES' if p['has_manifest'] else 'NO'}</span></div>
<div class="stat"><span>Exhibits</span><span>{'YES' if p['has_exhibits'] else 'NO'}</span></div>
</div>
</div>
"""
    
    html += "</div>\n\n<h2>DRIVE STATUS</h2>\n<div class='drives'>\n"
    for d in drive_info:
        pct = round((d["total_gb"] - d["free_gb"]) / d["total_gb"] * 100) if d["total_gb"] > 0 else 0
        color = "#ff4444" if d["free_gb"] < 2 else "#ffaa00" if d["free_gb"] < 10 else "#00ff88"
        html += f"""<div class="drive">
<strong>{d['drive']}:</strong> {d['free_gb']}GB free / {d['total_gb']}GB
<div class="bar"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div>
</div>\n"""
    
    html += f"""</div>
<h2>CASE FACTS</h2>
<table>
<tr><th>Item</th><th>Detail</th></tr>
<tr><td>Plaintiff</td><td>Andrew J. Pigors, pro se</td></tr>
<tr><td>Defendant</td><td>Tiffany Emily Watson (fka Pigors), counsel: Jennifer L. Barnes</td></tr>
<tr><td>Minor Child</td><td>Lincoln Watson, DOB Nov 9, 2022</td></tr>
<tr><td>Judge</td><td>Hon. Jenny L. McNeill</td></tr>
<tr><td>Court</td><td>14th Judicial Circuit, Muskegon County</td></tr>
<tr><td>Case No.</td><td>2024-001507-DC</td></tr>
<tr><td>COA Case</td><td>366810 (Deadline: April 15, 2026)</td></tr>
<tr><td>Separation</td><td>571+ days (since July 29, 2025)</td></tr>
<tr><td>Drug Screen</td><td>NEGATIVE</td></tr>
</table>

<div style="margin-top:30px;padding:15px;background:#1a1a2e;border-radius:8px;font-size:12px;color:#666">
LitigationOS Delta99 | Operation Total Convergence | {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
Passes Complete: 1(Scan) 2(Purge:134GB) 3(DB Cascade) 5(Evidence) 7(Timeline) 8(Dashboard)
</div>
</body>
</html>"""
    
    with open(DASHBOARD, "w", encoding="utf-8") as f:
        f.write(html)
    
    log(f"PASS 8 COMPLETE — {DASHBOARD}")

if __name__ == "__main__":
    run()
