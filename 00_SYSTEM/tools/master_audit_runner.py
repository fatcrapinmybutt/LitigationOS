#!/usr/bin/env python3
"""
LitigationOS Master Audit Runner — All-in-One Filing Quality Suite
===================================================================
Runs all 6 novel litigation tools in sequence and generates a
unified report card for all 10 filings.

Tools in this suite:
  1. Filing Readiness Scorecard    — Section/authority/fabrication check
  2. Timeline Integrity Validator  — Cross-filing date conflict detection
  3. Cross-Filing Consistency      — Assertion consistency across F1-F10
  4. Contradiction Detector        — Emily/McNeill contradiction mining
  5. Evidence Chain Mapper         — Claim-to-evidence traceability
  6. Judicial Pattern Analyzer     — Statistical bias metrics

Usage:
  python master_audit_runner.py [--quick] [--full] [--json]
    --quick: Scorecard + Consistency + Timeline only (~30s)
    --full:  All 6 tools (~2-5 min depending on DB size)
    --json:  Save JSON reports from each tool
"""

import sys, os, importlib, time, argparse
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(TOOLS_DIR, '..', 'reports')

# Add tools dir to path for imports
sys.path.insert(0, TOOLS_DIR)


def run_tool(name, func, *args, **kwargs):
    """Run a tool with timing and error handling."""
    print(f"\n{'▓' * 70}")
    print(f"  Running: {name}")
    print(f"{'▓' * 70}\n")
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"\n  ✅ {name} completed in {elapsed:.1f}s")
        return result
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n  ❌ {name} failed after {elapsed:.1f}s: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Master Audit Runner')
    parser.add_argument('--quick', action='store_true', help='Quick mode: 3 tools')
    parser.add_argument('--full', action='store_true', help='Full mode: all 6 tools')
    parser.add_argument('--json', '-j', action='store_true', help='Save JSON reports')
    args = parser.parse_args()

    if not args.quick and not args.full:
        args.full = True  # Default to full

    print("═" * 70)
    print("  LITIGATIONOS MASTER AUDIT RUNNER")
    print(f"  Mode: {'QUICK (3 tools)' if args.quick else 'FULL (6 tools)'}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 70)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    total_start = time.time()
    results = {}

    # Tool 1: Filing Readiness Scorecard
    try:
        from filing_readiness_scorecard import run_scorecard
        results['scorecard'] = run_tool("Filing Readiness Scorecard", run_scorecard)
    except ImportError:
        print("  ⚠ filing_readiness_scorecard not importable — run standalone")
    except Exception as e:
        print(f"  ⚠ Scorecard error: {e}")

    # Tool 2: Timeline Integrity Validator
    try:
        from timeline_integrity_validator import run_validation
        results['timeline'] = run_tool("Timeline Integrity Validator",
                                        run_validation, verbose=False, output_json=args.json)
    except ImportError:
        print("  ⚠ timeline_integrity_validator not importable — run standalone")
    except Exception as e:
        print(f"  ⚠ Timeline error: {e}")

    # Tool 3: Cross-Filing Consistency
    try:
        from cross_filing_consistency_checker import run_check
        results['consistency'] = run_tool("Cross-Filing Consistency Checker",
                                          run_check, verbose=False, output_json=args.json)
    except ImportError:
        print("  ⚠ cross_filing_consistency_checker not importable — run standalone")
    except Exception as e:
        print(f"  ⚠ Consistency error: {e}")

    if args.full:
        # Tool 4: Contradiction Detector
        try:
            from contradiction_detector import main as contra_main
            results['contradictions'] = run_tool("Contradiction Detector", contra_main)
        except ImportError:
            print("  ⚠ contradiction_detector not importable — run standalone")
        except Exception as e:
            print(f"  ⚠ Contradiction error: {e}")

        # Tool 5: Evidence Chain Mapper
        try:
            from evidence_chain_mapper import run_mapping
            results['evidence'] = run_tool("Evidence Chain Mapper",
                                           run_mapping, verbose=False, output_json=args.json)
        except ImportError:
            print("  ⚠ evidence_chain_mapper not importable — run standalone")
        except Exception as e:
            print(f"  ⚠ Evidence mapper error: {e}")

        # Tool 6: Judicial Pattern Analyzer
        try:
            from judicial_pattern_analyzer import generate_report, get_db, discover_schema
            conn = get_db()
            tables = discover_schema(conn)
            results['judicial'] = run_tool("Judicial Pattern Analyzer",
                                           generate_report, conn, tables,
                                           verbose=False, output_json=args.json, save_report=True)
            conn.close()
        except ImportError:
            print("  ⚠ judicial_pattern_analyzer not importable — run standalone")
        except Exception as e:
            print(f"  ⚠ Judicial analyzer error: {e}")

    # Final summary
    total_elapsed = time.time() - total_start
    print()
    print("═" * 70)
    print("  MASTER AUDIT COMPLETE")
    print(f"  Total time: {total_elapsed:.1f}s")
    print(f"  Tools run: {len(results)}")
    print("═" * 70)
    print()
    print("  Reports generated in: 00_SYSTEM/reports/")
    print("    • filing_readiness_scorecard (stdout)")
    print("    • timeline_validation.json")
    print("    • consistency_check.json")
    print("    • CONTRADICTION_REPORT.md")
    print("    • evidence_chain_map.json")
    print("    • judicial_pattern_analysis.json + .md")
    print()

    return results


if __name__ == '__main__':
    main()
