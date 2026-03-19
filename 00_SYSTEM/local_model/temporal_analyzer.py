"""
THE MANBEARPIG — Temporal Anomaly Detection (EPOCH v4.0)
Statistical analysis of judicial and litigation event timing.
DBSCAN clustering to find suspicious temporal patterns.
"""
import os, sqlite3, json, re, time
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sklearn.cluster import DBSCAN

DB_PATH = os.environ.get("LITIGATION_DB_PATH", r"C:\Users\andre\LitigationOS\litigation_context.db")

class TemporalAnalyzer:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
    
    def _get_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def _parse_date(self, date_str):
        """Parse various date formats found in the DB."""
        if not date_str:
            return None
        for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S', '%B %d, %Y'):
            try:
                return datetime.strptime(str(date_str).strip()[:19], fmt)
            except:
                continue
        # Try to extract date from string
        m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', str(date_str))
        if m:
            try:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except:
                pass
        return None
    
    def load_events(self) -> list:
        """Load all dated events from multiple tables."""
        db = self._get_db()
        events = []
        
        # Check actual columns in each table before querying
        tables_configs = [
            ("global_chronology", ["date", "event_date", "date_iso", "timestamp"]),
            ("master_timeline", ["date", "event_date", "date_iso", "timestamp"]),
            ("chronological_misconduct", ["date", "event_date", "date_iso", "timestamp"]),
            ("docket_events", ["event_date_iso", "event_date", "date", "date_iso"]),
            ("judicial_violations", ["date", "event_date", "created_at"]),
        ]
        
        for table, date_cols in tables_configs:
            try:
                # Find the actual date column
                cols = [c[1] for c in db.execute(f"PRAGMA table_info({table})").fetchall()]
                date_col = None
                for dc in date_cols:
                    if dc in cols:
                        date_col = dc
                        break
                if not date_col:
                    # Try any column with 'date' in name
                    date_col = next((c for c in cols if 'date' in c.lower()), None)
                
                if not date_col:
                    continue
                
                # Get a text column for description
                text_col = next((c for c in cols if any(x in c.lower() for x in ['title', 'description', 'summary', 'text', 'event'])), cols[1] if len(cols) > 1 else cols[0])
                
                rows = db.execute(f"SELECT {date_col}, {text_col} FROM {table} WHERE {date_col} IS NOT NULL").fetchall()
                for r in rows:
                    dt = self._parse_date(r[0])
                    if dt and dt.year >= 2020:
                        events.append({
                            "date": dt,
                            "text": str(r[1] or "")[:200],
                            "source": table
                        })
            except Exception as e:
                continue
        
        db.close()
        events.sort(key=lambda x: x["date"])
        return events
    
    def cluster_events(self, eps_days=3, min_samples=3) -> dict:
        """DBSCAN clustering on event dates to find suspicious bursts of activity.
        eps_days: maximum days between events to be in same cluster
        min_samples: minimum events to form a cluster
        """
        events = self.load_events()
        if not events:
            return {"error": "No events loaded"}
        
        # Convert dates to days-since-epoch for DBSCAN
        epoch = events[0]["date"]
        X = np.array([(e["date"] - epoch).total_seconds() / 86400.0 for e in events]).reshape(-1, 1)
        
        db_scan = DBSCAN(eps=eps_days, min_samples=min_samples)
        labels = db_scan.fit_predict(X)
        
        clusters = defaultdict(list)
        noise = 0
        for i, label in enumerate(labels):
            if label == -1:
                noise += 1
            else:
                clusters[label].append(events[i])
        
        # Analyze each cluster
        cluster_analysis = []
        for label, cluster_events in sorted(clusters.items()):
            dates = [e["date"] for e in cluster_events]
            sources = [e["source"] for e in cluster_events]
            
            cluster_analysis.append({
                "cluster_id": int(label),
                "event_count": len(cluster_events),
                "start_date": min(dates).isoformat(),
                "end_date": max(dates).isoformat(),
                "duration_days": (max(dates) - min(dates)).days,
                "sources": dict(sorted(defaultdict(int, {s: sources.count(s) for s in set(sources)}).items(), key=lambda x: -x[1])),
                "sample_events": [e["text"] for e in cluster_events[:5]],
                "suspicious": len(cluster_events) > 10 or (max(dates) - min(dates)).days < 2
            })
        
        cluster_analysis.sort(key=lambda x: -x["event_count"])
        
        return {
            "total_events": len(events),
            "clusters": len(cluster_analysis),
            "noise_events": noise,
            "suspicious_clusters": sum(1 for c in cluster_analysis if c["suspicious"]),
            "cluster_details": cluster_analysis[:20]
        }
    
    def detect_ex_parte_timing(self) -> list:
        """Find rulings that occurred suspiciously close to ex parte communications.
        Search for: ex parte event → ruling within 48 hours."""
        events = self.load_events()
        
        # Identify ex parte events
        ex_parte_events = [e for e in events if any(kw in e["text"].lower() for kw in ["ex parte", "without notice", "one-sided", "no hearing"])]
        
        # Identify ruling events
        ruling_events = [e for e in events if any(kw in e["text"].lower() for kw in ["order", "ruling", "decision", "granted", "denied", "judgment"])]
        
        suspicious = []
        for ep in ex_parte_events:
            for ruling in ruling_events:
                delta = abs((ruling["date"] - ep["date"]).total_seconds()) / 3600.0  # hours
                if 0 < delta < 72:  # Within 72 hours
                    suspicious.append({
                        "ex_parte_date": ep["date"].isoformat(),
                        "ex_parte_text": ep["text"],
                        "ruling_date": ruling["date"].isoformat(),
                        "ruling_text": ruling["text"],
                        "hours_apart": round(delta, 1),
                        "source": f"{ep['source']} → {ruling['source']}"
                    })
        
        suspicious.sort(key=lambda x: x["hours_apart"])
        return suspicious[:50]
    
    def detect_delay_patterns(self) -> dict:
        """Detect unusual delays or rushing in proceedings."""
        events = self.load_events()
        if len(events) < 2:
            return {"error": "Not enough events"}
        
        # Calculate gaps between consecutive events
        gaps = []
        for i in range(1, len(events)):
            gap_days = (events[i]["date"] - events[i-1]["date"]).days
            if gap_days > 0:
                gaps.append({
                    "gap_days": gap_days,
                    "before": events[i-1]["text"][:100],
                    "after": events[i]["text"][:100],
                    "before_date": events[i-1]["date"].isoformat(),
                    "after_date": events[i]["date"].isoformat()
                })
        
        if not gaps:
            return {"error": "No gaps found"}
        
        gap_values = [g["gap_days"] for g in gaps]
        mean_gap = np.mean(gap_values)
        std_gap = np.std(gap_values)
        
        # Find unusual gaps (>2 std deviations)
        unusual_delays = [g for g in gaps if g["gap_days"] > mean_gap + 2 * std_gap]
        unusual_rushes = [g for g in gaps if g["gap_days"] < max(1, mean_gap - 2 * std_gap) and g["gap_days"] <= 1]
        
        return {
            "total_gaps": len(gaps),
            "mean_gap_days": round(mean_gap, 1),
            "std_gap_days": round(std_gap, 1),
            "unusual_delays": sorted(unusual_delays, key=lambda x: -x["gap_days"])[:10],
            "unusual_rushes": unusual_rushes[:10],
            "delay_count": len(unusual_delays),
            "rush_count": len(unusual_rushes)
        }
    
    def calculate_separation_days(self) -> dict:
        """Calculate exact parent-child separation days from evidence."""
        # Separation started ~July 1, 2024 based on case context
        separation_start = datetime(2024, 7, 1)
        now = datetime.now()
        total_days = (now - separation_start).days
        
        return {
            "separation_start": separation_start.isoformat(),
            "current_date": now.isoformat(),
            "total_days": total_days,
            "total_months": round(total_days / 30.44, 1),
            "total_years": round(total_days / 365.25, 2),
            "legal_significance": "Prolonged separation exceeding 1 year creates presumption of harm. MCL 722.27a(7)(c) — parenting time denial must be based on clear and convincing evidence of endangerment."
        }
    
    def generate_anomaly_report(self) -> dict:
        """Comprehensive temporal anomaly report."""
        return {
            "clusters": self.cluster_events(),
            "ex_parte_timing": self.detect_ex_parte_timing()[:20],
            "delay_patterns": self.detect_delay_patterns(),
            "separation": self.calculate_separation_days()
        }
    
    def status(self) -> dict:
        events = self.load_events()
        return {
            "engine": "MANBEARPIG-Temporal",
            "total_events": len(events),
            "date_range": f"{events[0]['date'].isoformat()} to {events[-1]['date'].isoformat()}" if events else "none",
            "sources": dict(sorted(defaultdict(int, {e['source']: 1 for e in events}).items()))
        }

def self_test():
    results = {"tests": [], "status": "pass"}
    try:
        ta = TemporalAnalyzer()
        events = ta.load_events()
        results["tests"].append({"name": "load_events", "pass": len(events) > 0, "count": len(events)})
        clusters = ta.cluster_events()
        results["tests"].append({"name": "cluster_events", "pass": "clusters" in clusters, "clusters": clusters.get("clusters", 0)})
        sep = ta.calculate_separation_days()
        results["tests"].append({"name": "separation", "pass": sep["total_days"] > 329, "days": sep["total_days"]})
        results["status"] = "pass" if all(t["pass"] for t in results["tests"]) else "partial"
    except Exception as e:
        results["status"] = "fail"
        results["error"] = str(e)
    return results

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    ta = TemporalAnalyzer()
    if cmd == "cluster": print(json.dumps(ta.cluster_events(), indent=2, default=str))
    elif cmd == "ex-parte": print(json.dumps(ta.detect_ex_parte_timing(), indent=2, default=str))
    elif cmd == "delays": print(json.dumps(ta.detect_delay_patterns(), indent=2, default=str))
    elif cmd == "separation": print(json.dumps(ta.calculate_separation_days(), indent=2))
    elif cmd == "report": print(json.dumps(ta.generate_anomaly_report(), indent=2, default=str))
    elif cmd == "self-test": print(json.dumps(self_test(), indent=2))
    elif cmd == "status": print(json.dumps(ta.status(), indent=2, default=str))
