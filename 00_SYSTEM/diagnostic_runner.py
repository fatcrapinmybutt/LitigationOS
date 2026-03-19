#!/usr/bin/env python3
"""
Comprehensive diagnostic queries for LitigationOS databases.
Executes with proper CWD and environment setup.
"""
import os
import sys
import json
import sqlite3
from pathlib import Path
from collections import defaultdict

# Set working directory explicitly
os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

def get_db_schema(db_path):
    """Get table names and their column info from a database."""
    if not Path(db_path).exists():
        return {"error": f"Database not found: {db_path}"}
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA busy_timeout=60000")
        if db_path.endswith("master_index.db"):
            conn.execute("PRAGMA journal_mode=WAL")
        
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        schema = {}
        for table in tables:
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            schema[table] = {"columns": columns, "row_count": count}
        
        conn.close()
        return schema
    except Exception as e:
        return {"error": str(e)}

def query_master_index():
    """Query master_index.db for detailed analytics."""
    db_path = "pipeline/agents/master_index.db"
    if not Path(db_path).exists():
        return {"error": f"Database not found: {db_path}"}
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        
        results = {}
        
        # List all tables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        results["tables"] = [row[0] for row in cursor.fetchall()]
        
        # Agent log analytics
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM agent_log")
            results["agent_log_total_rows"] = cursor.fetchone()[0]
            
            cursor = conn.execute(
                "SELECT level, COUNT(*) as count FROM agent_log GROUP BY level ORDER BY level"
            )
            results["agent_log_by_level"] = dict(cursor.fetchall())
            
            cursor = conn.execute(
                "SELECT action, COUNT(*) as count FROM agent_log GROUP BY action ORDER BY count DESC LIMIT 20"
            )
            results["agent_log_top_actions"] = dict(cursor.fetchall())
            
            cursor = conn.execute(
                "SELECT agent_id, COUNT(*) as count FROM agent_log GROUP BY agent_id ORDER BY count DESC LIMIT 15"
            )
            results["agent_log_by_agent"] = dict(cursor.fetchall())
            
            cursor = conn.execute(
                "SELECT * FROM agent_log WHERE level IN ('FATAL', 'CRASH', 'ERROR') ORDER BY timestamp DESC LIMIT 10"
            )
            cols = [description[0] for description in cursor.description]
            results["top_errors"] = [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            results["agent_log_error"] = str(e)
        
        # Ready queue analytics
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM ready_queue")
            results["ready_queue_total"] = cursor.fetchone()[0]
            
            cursor = conn.execute(
                "SELECT status, COUNT(*) as count FROM ready_queue GROUP BY status"
            )
            results["ready_queue_by_status"] = dict(cursor.fetchall())
        except Exception as e:
            results["ready_queue_error"] = str(e)
        
        # Files table analytics
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM files")
            results["files_total"] = cursor.fetchone()[0]
            
            cursor = conn.execute(
                "SELECT category, COUNT(*) as count FROM files GROUP BY category ORDER BY count DESC"
            )
            results["files_by_category"] = dict(cursor.fetchall())
        except Exception as e:
            results["files_error"] = str(e)
        
        conn.close()
        return results
    except Exception as e:
        return {"error": str(e)}

def query_litigation_context():
    """Query litigation_context.db for analytics."""
    db_path = "../litigation_context.db"
    if not Path(db_path).exists():
        return {"error": f"Database not found: {db_path}"}
    
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA busy_timeout=60000")
        
        results = {}
        
        # List all tables
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        results["tables"] = [row[0] for row in cursor.fetchall()]
        
        # Memory store analytics
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM memory_store")
            results["memory_store_total"] = cursor.fetchone()[0]
            
            cursor = conn.execute(
                "SELECT memory_type, COUNT(*) as count FROM memory_store GROUP BY memory_type"
            )
            results["memory_store_by_type"] = dict(cursor.fetchall())
        except Exception as e:
            results["memory_store_error"] = str(e)
        
        # Engine metrics analytics
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM engine_metrics")
            results["engine_metrics_total"] = cursor.fetchone()[0]
            
            cursor = conn.execute(
                "SELECT * FROM engine_metrics ORDER BY timestamp DESC LIMIT 5"
            )
            cols = [description[0] for description in cursor.description]
            results["recent_metrics"] = [dict(zip(cols, row)) for row in cursor.fetchall()]
        except Exception as e:
            results["engine_metrics_error"] = str(e)
        
        conn.close()
        return results
    except Exception as e:
        return {"error": str(e)}

def parse_evolution_log():
    """Parse evolution_log.json for cycle analytics."""
    log_path = "local_model/evolution_log.json"
    if not Path(log_path).exists():
        return {"error": f"File not found: {log_path}"}
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            return {"error": "evolution_log.json is not a JSON array"}
        
        results = {
            "total_cycles": len(data),
            "first_cycle": data[0] if data else None,
            "last_cycle": data[-1] if data else None,
        }
        
        if len(data) > 0:
            results["cycle_range"] = f"Cycle {data[0].get('cycle')} to {data[-1].get('cycle')}"
            
            # Aggregate phase metrics
            phase_stats = defaultdict(lambda: {"count": 0, "total_time": 0})
            total_elapsed = 0
            
            for entry in data:
                total_elapsed += entry.get("elapsed_s", 0)
                if "phases" in entry:
                    for phase_name, phase_data in entry["phases"].items():
                        if isinstance(phase_data, dict) and "elapsed_s" in phase_data:
                            phase_stats[phase_name]["count"] += 1
                            phase_stats[phase_name]["total_time"] += phase_data["elapsed_s"]
            
            results["total_elapsed_seconds"] = total_elapsed
            results["average_cycle_time"] = total_elapsed / len(data) if data else 0
            results["phase_averages"] = {
                phase: {
                    "avg_time": stats["total_time"] / stats["count"],
                    "total_time": stats["total_time"],
                    "cycles": stats["count"]
                }
                for phase, stats in phase_stats.items()
            }
        
        return results
    except json.JSONDecodeError as e:
        return {"error": f"JSON parsing error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    """Run all diagnostics and output results."""
    print("=" * 80)
    print("LITIGATIONOS DATABASE DIAGNOSTICS")
    print("=" * 80)
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Master Index Database
    print("-" * 80)
    print("MASTER_INDEX.DB SCHEMA")
    print("-" * 80)
    schema = get_db_schema("pipeline/agents/master_index.db")
    print(json.dumps(schema, indent=2))
    print()
    
    print("-" * 80)
    print("MASTER_INDEX.DB ANALYTICS")
    print("-" * 80)
    analytics = query_master_index()
    print(json.dumps(analytics, indent=2, default=str))
    print()
    
    # Litigation Context Database
    print("-" * 80)
    print("LITIGATION_CONTEXT.DB SCHEMA")
    print("-" * 80)
    schema = get_db_schema("../litigation_context.db")
    print(json.dumps(schema, indent=2))
    print()
    
    print("-" * 80)
    print("LITIGATION_CONTEXT.DB ANALYTICS")
    print("-" * 80)
    analytics = query_litigation_context()
    print(json.dumps(analytics, indent=2, default=str))
    print()
    
    # Evolution Log
    print("-" * 80)
    print("EVOLUTION_LOG.JSON ANALYSIS")
    print("-" * 80)
    log_analysis = parse_evolution_log()
    print(json.dumps(log_analysis, indent=2, default=str))
    print()
    
    print("=" * 80)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
