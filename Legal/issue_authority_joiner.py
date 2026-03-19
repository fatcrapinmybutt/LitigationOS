#!/usr/bin/env python3
"""
issue_authority_joiner.py

Purpose
=======
Join higher-court issues (from higher_court_issues_report.json) with an
authorities table (authorities_master_table_*.csv produced by
authority_table_builder.py) to build a per-issue authority matrix.

The join is intentionally conservative and string-based. For each authority row,
we try to attach it to any issue whose summary or harms text appears to match
the authority's violation_label.

Inputs
------
  --issues-json        Path to higher_court_issues_report.json
  --authorities-csv    Path to authorities_master_table_*.csv
  --output-dir         Directory for outputs

Outputs
-------
  * issue_authority_matrix.json
      [
        {
          "issue_id": "...",
          "track_guess": "...",
          "source_file": "...",
          "harms_count": N,
          "issue_summary": "...",
          "matched_authorities": [
            {
              "violation_key": "...",
              "violation_label": "...",
              "authority_type": "...",
              "authority_citation": "...",
              "authority_pinpoint": "...",
              "authority_short_name": "...",
              "authority_notes": "...",
              "best_courts_joined": "...",
              "preferred_forums_joined": "...",
              "evidence_count": 0
            },
            ...
          ]
        },
        ...
      ]

  * issue_authority_matrix.csv
      One row per (issue_id, authority_citation) with basic metadata.
"""

import os
import sys
import json
import argparse
from typing import List, Dict

import pandas as pd


def load_issues(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit(f"Expected list in {path}, got {type(data)}")
    return data


def load_authorities(path: str) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", dtype=str)


def issue_matches_authority(issue: Dict, auth_row: Dict) -> bool:
    """
    Conservative heuristic:
      - Take authority violation_label and citation.
      - See if violation_label (lowercased) appears in issue_summary OR in any harm text.
      - Also check if short_name appears.

    This is approximate, not a legal decision engine.
    """
    v_label = str(auth_row.get("violation_label", "") or "").strip().lower()
    short_name = str(auth_row.get("authority_short_name", "") or "").strip().lower()
    citation = str(auth_row.get("authority_citation", "") or "").strip().lower()

    if not v_label and not short_name and not citation:
        return False

    summary = str(issue.get("issue_summary", "") or "").lower()
    harms = issue.get("harms", []) or []

    haystack = [summary]
    for h in harms:
        txt = str(h.get("text", "") or "")
        haystack.append(txt.lower())

    def any_contains(needle: str) -> bool:
        if not needle:
            return False
        return any(needle in chunk for chunk in haystack)

    if v_label and any_contains(v_label):
        return True
    if short_name and any_contains(short_name):
        return True
    # As a last resort, sometimes authorities are referenced by citation text in the harms
    if citation and any_contains(citation):
        return True

    return False


def build_issue_authority_matrix(issues, auth_df: pd.DataFrame):
    # Normalize auth_df columns
    needed_cols = [
        "violation_key",
        "violation_label",
        "authority_type",
        "authority_citation",
        "authority_pinpoint",
        "authority_short_name",
        "authority_notes",
        "best_courts_joined",
        "preferred_forums_joined",
        "evidence_count",
    ]
    for col in needed_cols:
        if col not in auth_df.columns:
            auth_df[col] = ""

    records = auth_df.to_dict(orient="records")
    issue_matrix = []
    csv_rows = []

    for issue in issues:
        iid = issue.get("issue_id", "")
        track = issue.get("track_guess", "")
        src = issue.get("source_file", "")
        harms_count = int(issue.get("harms_count", len(issue.get("harms", []) or [])))
        summary = issue.get("issue_summary", "")

        matched_auths = []
        for ar in records:
            if issue_matches_authority(issue, ar):
                matched_auths.append(ar)

        issue_entry = {
            "issue_id": iid,
            "track_guess": track,
            "source_file": src,
            "harms_count": harms_count,
            "issue_summary": summary,
            "matched_authorities": matched_auths,
        }
        issue_matrix.append(issue_entry)

        for ar in matched_auths:
            csv_rows.append({
                "issue_id": iid,
                "track_guess": track,
                "source_file": src,
                "harms_count": harms_count,
                "issue_summary": summary,
                "violation_key": ar.get("violation_key", ""),
                "violation_label": ar.get("violation_label", ""),
                "authority_type": ar.get("authority_type", ""),
                "authority_citation": ar.get("authority_citation", ""),
                "authority_pinpoint": ar.get("authority_pinpoint", ""),
                "authority_short_name": ar.get("authority_short_name", ""),
                "authority_notes": ar.get("authority_notes", ""),
                "best_courts_joined": ar.get("best_courts_joined", ""),
                "preferred_forums_joined": ar.get("preferred_forums_joined", ""),
                "evidence_count": ar.get("evidence_count", ""),
            })

    csv_df = pd.DataFrame(csv_rows)
    return issue_matrix, csv_df


def main():
    ap = argparse.ArgumentParser(description="Join higher court issues with authorities table.")
    ap.add_argument("--issues-json", required=True, help="Path to higher_court_issues_report.json")
    ap.add_argument("--authorities-csv", required=True, help="Path to authorities_master_table_*.csv")
    ap.add_argument("--output-dir", default=".", help="Output directory")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    issues = load_issues(args.issues_json)
    auth_df = load_authorities(args.authorities_csv)

    issue_matrix, csv_df = build_issue_authority_matrix(issues, auth_df)

    json_path = os.path.join(args.output_dir, "issue_authority_matrix.json")
    csv_path = os.path.join(args.output_dir, "issue_authority_matrix.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(issue_matrix, f, indent=2)

    csv_df.to_csv(csv_path, index=False, encoding="utf-8")

    print(f"[OK] Issues: {len(issues)}")
    print(f"[OK] Authority rows: {len(auth_df)}")
    print(f"[OK] Matched rows in CSV: {len(csv_df)}")
    print(f"[OK] JSON -> {json_path}")
    print(f"[OK] CSV  -> {csv_path}")


if __name__ == "__main__":
    main()
