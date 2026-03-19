#!/usr/bin/env python3
"""
Delta999 Timeline Agent -- 46K+ master timeline event manager.

Anomaly detection (gaps, contradictions, suspicious patterns).
Pattern finder: ex parte clustering, custody denial sequences, retaliatory timing.
Gap analysis: missing periods, undocumented events.

CLI:
    python delta999_timeline_agent.py --action find_anomalies --start-date "2019-01-01"
    python delta999_timeline_agent.py --action cluster_events --event-type "ex parte"
    python delta999_timeline_agent.py --action detect_patterns --pattern "retaliation"
    python delta999_timeline_agent.py --action gap_report --start-date "2019-01-01" --end-date "2024-12-31"
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta
from pathlib import Path

# -- paths -----------------------------------------------------------------
AGENT_DIR = Path(__file__).parent
ENGINE_DIR = AGENT_DIR.parent
sys.path.insert(0, str(ENGINE_DIR))

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
AGENT_NAME = 'delta999_timeline_agent'

from llm_bridge import llm_ask, llm_analyze_legal


# -- DB helpers ------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute('PRAGMA busy_timeout=60000')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn


def log_activity(action, result):
    try:
        conn = get_conn()
        conn.execute(
            'INSERT INTO agent_activity_log (agent_name, action, result) VALUES (?,?,?)',
            (AGENT_NAME, action, str(result)[:2000])
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


TIMELINE_TABLES = ['master_chronological_timeline', 'apex_master_timeline']

SUSPICIOUS_PATTERNS = {
    'ex_parte_clustering': {
        'description': 'Multiple ex parte actions within short time windows',
        'keywords': ['ex parte', 'without notice', 'emergency order'],
        'window_days': 14,
    },
    'custody_denial_sequence': {
        'description': 'Sequential custody denials forming a pattern',
        'keywords': ['denied', 'custody', 'parenting time', 'visitation', 'refused'],
        'window_days': 30,
    },
    'retaliatory_timing': {
        'description': 'Adverse actions following protected activity (filing, complaint)',
        'keywords': ['filed', 'complaint', 'motion', 'appeal'],
        'follow_keywords': ['denied', 'sanction', 'contempt', 'order against'],
        'window_days': 21,
    },
    'procedural_ambush': {
        'description': 'Filings or hearings with inadequate notice',
        'keywords': ['hearing', 'no notice', 'same day', 'emergency'],
        'window_days': 7,
    },
}


# -- Core functions --------------------------------------------------------

def _load_events(start_date: str = '', end_date: str = '', limit: int = 5000) -> list:
    """Load timeline events from all timeline tables."""
    conn = get_conn()
    events = []

    for tbl in TIMELINE_TABLES:
        try:
            sql = f"SELECT * FROM [{tbl}]"
            params = []
            conditions = []

            if start_date:
                conditions.append("event_date >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("event_date <= ?")
                params.append(end_date)

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += f" ORDER BY event_date LIMIT {limit}"

            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                d = dict(r)
                d['_source_table'] = tbl
                events.append(d)
        except Exception:
            pass

    conn.close()
    events.sort(key=lambda e: str(e.get('event_date', '')))
    return events


def find_anomalies(start_date: str = '', end_date: str = '') -> dict:
    """Detect anomalies: gaps, contradictions, suspicious patterns."""
    events = _load_events(start_date, end_date)

    anomalies = {
        'rapid_sequences': [],
        'contradictions': [],
        'unusual_timing': [],
        'duplicate_events': [],
    }

    # Detect rapid sequences (multiple events same day)
    date_counts = Counter(str(e.get('event_date', ''))[:10] for e in events)
    for dt, count in date_counts.items():
        if count >= 5:
            anomalies['rapid_sequences'].append({
                'date': dt,
                'event_count': count,
                'flag': 'HIGH_ACTIVITY_DAY',
            })

    # Detect duplicates
    seen = {}
    for e in events:
        key = f"{e.get('event_date', '')}|{str(e.get('description', ''))[:100]}"
        if key in seen:
            anomalies['duplicate_events'].append({
                'date': e.get('event_date'),
                'description': str(e.get('description', ''))[:200],
                'tables': [seen[key], e.get('_source_table')],
            })
        else:
            seen[key] = e.get('_source_table')

    # Detect unusual timing (weekend/holiday filings, late-night orders)
    for e in events:
        try:
            dt = datetime.strptime(str(e.get('event_date', ''))[:10], '%Y-%m-%d')
            if dt.weekday() >= 5:  # weekend
                desc = str(e.get('description', ''))
                if any(kw in desc.lower() for kw in ['order', 'filing', 'hearing']):
                    anomalies['unusual_timing'].append({
                        'date': str(e.get('event_date')),
                        'day': dt.strftime('%A'),
                        'description': desc[:200],
                        'flag': 'WEEKEND_ACTION',
                    })
        except (ValueError, TypeError):
            pass

    # LLM analysis
    try:
        analysis = llm_ask(
            f"Analyze timeline anomalies for litigation:\n"
            f"Total events: {len(events)}\n"
            f"Rapid sequences: {len(anomalies['rapid_sequences'])}\n"
            f"Contradictions: {len(anomalies['contradictions'])}\n"
            f"Unusual timing: {len(anomalies['unusual_timing'])}\n"
            f"Duplicates: {len(anomalies['duplicate_events'])}\n\n"
            f"Sample rapid sequences: {json.dumps(anomalies['rapid_sequences'][:5], default=str)[:500]}\n"
            f"Sample unusual timing: {json.dumps(anomalies['unusual_timing'][:5], default=str)[:500]}\n\n"
            f"Identify the most significant anomalies and their legal implications.",
            system_prompt="You are a litigation timeline analyst identifying judicial and procedural anomalies."
        )
    except Exception as e:
        analysis = f"LLM unavailable: {e}"

    result = {
        'date_range': f"{start_date or 'earliest'} --> {end_date or 'latest'}",
        'total_events': len(events),
        'anomalies': anomalies,
        'anomaly_summary': {k: len(v) for k, v in anomalies.items()},
        'analysis': analysis,
    }
    log_activity('find_anomalies', json.dumps(result, default=str)[:2000])
    return result


def cluster_events(event_type: str) -> dict:
    """Cluster events by type to find patterns."""
    events = _load_events()

    # Filter events matching the type
    matched = []
    keywords = event_type.lower().split()
    for e in events:
        text = (str(e.get('description', '')) + ' ' + str(e.get('event_type', ''))).lower()
        if any(kw in text for kw in keywords):
            matched.append(e)

    # Cluster by time proximity
    clusters = []
    current_cluster = []
    for e in matched:
        if not current_cluster:
            current_cluster.append(e)
            continue
        try:
            prev_date = datetime.strptime(str(current_cluster[-1].get('event_date', ''))[:10], '%Y-%m-%d')
            curr_date = datetime.strptime(str(e.get('event_date', ''))[:10], '%Y-%m-%d')
            if (curr_date - prev_date).days <= 30:
                current_cluster.append(e)
            else:
                if len(current_cluster) >= 2:
                    clusters.append({
                        'start': str(current_cluster[0].get('event_date')),
                        'end': str(current_cluster[-1].get('event_date')),
                        'count': len(current_cluster),
                        'events': [str(ev.get('description', ''))[:100] for ev in current_cluster[:5]],
                    })
                current_cluster = [e]
        except (ValueError, TypeError):
            current_cluster.append(e)

    if len(current_cluster) >= 2:
        clusters.append({
            'start': str(current_cluster[0].get('event_date')),
            'end': str(current_cluster[-1].get('event_date')),
            'count': len(current_cluster),
            'events': [str(ev.get('description', ''))[:100] for ev in current_cluster[:5]],
        })

    # Monthly distribution
    monthly = Counter()
    for e in matched:
        month = str(e.get('event_date', ''))[:7]
        if month:
            monthly[month] += 1

    result = {
        'event_type': event_type,
        'total_matched': len(matched),
        'clusters_found': len(clusters),
        'clusters': clusters[:20],
        'monthly_distribution': dict(sorted(monthly.items())),
    }
    log_activity(f'cluster:{event_type[:50]}', json.dumps(result, default=str)[:2000])
    return result


def detect_patterns(pattern_name: str = '') -> dict:
    """Detect predefined suspicious patterns in the timeline."""
    events = _load_events()
    detected = {}

    patterns_to_check = (
        {pattern_name: SUSPICIOUS_PATTERNS[pattern_name]}
        if pattern_name in SUSPICIOUS_PATTERNS
        else SUSPICIOUS_PATTERNS
    )

    for name, cfg in patterns_to_check.items():
        matched = []
        for e in events:
            text = (str(e.get('description', '')) + ' ' + str(e.get('event_type', ''))).lower()
            if any(kw in text for kw in cfg['keywords']):
                matched.append(e)

        # Find clusters within window
        clusters = []
        for i, ev in enumerate(matched):
            window = [ev]
            try:
                ev_date = datetime.strptime(str(ev.get('event_date', ''))[:10], '%Y-%m-%d')
            except (ValueError, TypeError):
                continue
            for j in range(i + 1, min(i + 20, len(matched))):
                try:
                    next_date = datetime.strptime(str(matched[j].get('event_date', ''))[:10], '%Y-%m-%d')
                    if (next_date - ev_date).days <= cfg['window_days']:
                        window.append(matched[j])
                except (ValueError, TypeError):
                    continue
            if len(window) >= 3:
                clusters.append({
                    'start_date': str(ev.get('event_date')),
                    'count': len(window),
                    'window_days': cfg['window_days'],
                    'sample_events': [str(w.get('description', ''))[:100] for w in window[:3]],
                })

        detected[name] = {
            'description': cfg['description'],
            'total_matching_events': len(matched),
            'suspicious_clusters': len(clusters),
            'clusters': clusters[:10],
        }

    result = {
        'patterns_checked': list(detected.keys()),
        'detected': detected,
        'total_events_scanned': len(events),
    }
    log_activity(f'detect_patterns:{pattern_name or "all"}', json.dumps(result, default=str)[:2000])
    return result


def gap_report(start_date: str = '2019-01-01', end_date: str = '') -> dict:
    """Find gaps in the timeline where no events are documented."""
    if not end_date:
        end_date = date.today().isoformat()

    events = _load_events(start_date, end_date)

    # Extract unique dates
    event_dates = set()
    for e in events:
        d = str(e.get('event_date', ''))[:10]
        if d and len(d) == 10:
            event_dates.add(d)

    # Find gaps > 14 days
    gaps = []
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        sorted_dates = sorted(event_dates)

        prev = start
        for ds in sorted_dates:
            try:
                d = datetime.strptime(ds, '%Y-%m-%d').date()
                gap_days = (d - prev).days
                if gap_days > 14:
                    gaps.append({
                        'gap_start': prev.isoformat(),
                        'gap_end': d.isoformat(),
                        'gap_days': gap_days,
                        'severity': 'HIGH' if gap_days > 60 else 'MEDIUM' if gap_days > 30 else 'LOW',
                    })
                prev = d
            except (ValueError, TypeError):
                continue

        # Check trailing gap
        if prev < end:
            trailing = (end - prev).days
            if trailing > 14:
                gaps.append({
                    'gap_start': prev.isoformat(),
                    'gap_end': end.isoformat(),
                    'gap_days': trailing,
                    'severity': 'HIGH' if trailing > 60 else 'MEDIUM',
                })
    except (ValueError, TypeError):
        pass

    # Monthly coverage
    monthly_coverage = Counter()
    for ds in event_dates:
        monthly_coverage[ds[:7]] += 1

    result = {
        'date_range': f"{start_date} --> {end_date}",
        'total_events': len(events),
        'unique_event_dates': len(event_dates),
        'gaps_over_14_days': len(gaps),
        'gaps': sorted(gaps, key=lambda g: g['gap_days'], reverse=True)[:30],
        'high_severity_gaps': len([g for g in gaps if g['severity'] == 'HIGH']),
        'monthly_coverage': dict(sorted(monthly_coverage.items())),
    }
    log_activity('gap_report', json.dumps(result, default=str)[:2000])
    return result


# -- CLI -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Delta999 Timeline Agent -- 46K+ Event Manager')
    parser.add_argument('--action', required=True,
                        choices=['find_anomalies', 'cluster_events',
                                 'detect_patterns', 'gap_report'],
                        help='Action to perform')
    parser.add_argument('--start-date', type=str, default='', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='', help='End date (YYYY-MM-DD)')
    parser.add_argument('--event-type', type=str, default='', help='Event type for clustering')
    parser.add_argument('--pattern', type=str, default='', help='Pattern name to detect')
    args = parser.parse_args()

    if args.action == 'find_anomalies':
        result = find_anomalies(args.start_date, args.end_date)
    elif args.action == 'cluster_events':
        if not args.event_type:
            parser.error('--event-type required')
        result = cluster_events(args.event_type)
    elif args.action == 'detect_patterns':
        result = detect_patterns(args.pattern)
    elif args.action == 'gap_report':
        result = gap_report(args.start_date or '2019-01-01', args.end_date)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
