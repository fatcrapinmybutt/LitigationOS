#!/usr/bin/env python3
"""Build the LitigationOS MEEK2/3/4 ERD pack from source zips."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class TableDef:
    title: str
    fields: Sequence[tuple[str, str, str]]


@dataclass(frozen=True)
class InputDataset:
    name: str
    path: Path
    row_count: int


def log_event(event: str, **payload: object) -> None:
    record = {
        "ts": dt.datetime.utcnow().isoformat() + "Z",
        "event": event,
        **payload,
    }
    print(json.dumps(record, sort_keys=True))


def guess_type(name: str) -> str:
    lowered = name.lower()
    if "benchbook" in lowered or lowered.endswith("bb.pdf") or lowered.endswith("bb mobile.pdf"):
        return "benchbook"
    if "checklist" in lowered or "flowchart" in lowered or "table" in lowered:
        return "checklist_table"
    if (
        "admin-order" in lowered
        or "administrative" in lowered
        or lowered.startswith("ao")
        or "ao-" in lowered
        or "order" in lowered
    ):
        return "order_admin"
    if "code-of-judicial-conduct" in lowered or "judicial conduct" in lowered:
        return "judicial_conduct"
    if "mcr" in lowered or "court rules" in lowered or ("rules" in lowered and "appeals" not in lowered):
        return "court_rules"
    if "appeal" in lowered or "appellate" in lowered:
        return "appellate"
    if "jtc" in lowered:
        return "jtc"
    if lowered.endswith(".pdf"):
        return "pdf_misc"
    return "misc"


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def node_table(name: str, title: str, fields: Sequence[tuple[str, str, str]]) -> str:
    rows: list[str] = []
    rows.append(f'<TR><TD BGCOLOR="#F2F2CC" COLSPAN="3"><B>{html_escape(title)}</B></TD></TR>')
    for field_name, field_type, field_label in fields:
        escaped = html_escape(field_name)
        rows.append(
            f"<TR>"
            f"<TD ALIGN=\"LEFT\" PORT=\"{escaped}\">{escaped}</TD>"
            f"<TD ALIGN=\"LEFT\">{html_escape(field_type)}</TD>"
            f"<TD ALIGN=\"LEFT\">{html_escape(field_label)}</TD>"
            f"</TR>"
        )
    table = (
        '<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="3">'
        + "".join(rows)
        + "</TABLE>>"
    )
    return f"{name} [shape=plaintext label={table}];"


def edge(src: str, src_field: str, dst: str, dst_field: str, label: str = "") -> str:
    label_fragment = f' [label="{label}", fontsize=9]' if label else ""
    return f"  {src}:{html_escape(src_field)} -> {dst}:{html_escape(dst_field)}{label_fragment};"


def dbml_type(field_type: str) -> str:
    return {
        "text": "varchar",
        "int": "int",
        "date": "date",
        "datetime": "datetime",
        "json": "json",
    }.get(field_type, "varchar")


def to_dbml(tables_def: dict[str, TableDef]) -> str:
    lines: list[str] = []
    lines.append("// DBML: LitigationOS MEEK2/3/4 core schema (conceptual)")
    for name, table in tables_def.items():
        lines.append(f"Table {name} {{")
        for field_name, field_type, field_label in table.fields:
            attrs: list[str] = []
            if "PK" in field_label:
                attrs.append("pk")
            if "REQ" in field_label:
                attrs.append("not null")
            if "UNQ" in field_label:
                attrs.append("unique")
            attr_str = " [" + ", ".join(attrs) + "]" if attrs else ""
            lines.append(f"  {field_name} {dbml_type(field_type)}{attr_str}")
        lines.append("}\n")
    for name, table in tables_def.items():
        for field_name, _field_type, field_label in table.fields:
            match = re.search(r"FK->([a-z_]+)\.([a-z_]+)", field_label)
            if match:
                dst_tbl, dst_col = match.group(1), match.group(2)
                lines.append(f"Ref: {name}.{field_name} > {dst_tbl}.{dst_col}")
    return "\n".join(lines)


def load_optional_csv(path: Path, required_columns: Sequence[str], dataset_name: str) -> InputDataset:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{dataset_name} CSV is missing headers: {path}")
        missing = [col for col in required_columns if col not in reader.fieldnames]
        if missing:
            raise ValueError(f"{dataset_name} CSV missing columns: {missing}")
        rows = list(reader)
    return InputDataset(name=dataset_name, path=path, row_count=len(rows))


def build_tables() -> dict[str, TableDef]:
    tables: dict[str, TableDef] = {}
    tables["track"] = TableDef(
        "TRACK",
        [
            ("track_id", "text", "PK"),
            ("code", "text", "UNQ (MEEK2|MEEK3|MEEK4)"),
            ("name", "text", "REQ"),
            ("scope_json", "json", ""),
        ],
    )
    tables["plane"] = TableDef(
        "PLANE",
        [
            ("plane_id", "text", "PK"),
            ("track_id", "text", "FK->track.track_id"),
            ("parent_plane_id", "text", "FK->plane.plane_id"),
            ("code", "text", "UNQ"),
            ("name", "text", "REQ"),
            ("kind", "text", "macro|sub|micro"),
            ("objective", "text", ""),
        ],
    )
    tables["plane_dependency"] = TableDef(
        "PLANE_DEPENDENCY",
        [
            ("dep_id", "text", "PK"),
            ("plane_id", "text", "FK->plane.plane_id"),
            ("depends_on_plane_id", "text", "FK->plane.plane_id"),
            ("reason", "text", ""),
        ],
    )
    tables["court"] = TableDef(
        "COURT",
        [
            ("court_id", "text", "PK"),
            ("name", "text", "REQ"),
            ("jurisdiction", "text", "MI"),
            ("level", "text", "district|circuit|coa|msc"),
            ("county", "text", ""),
        ],
    )
    tables["person"] = TableDef(
        "PERSON",
        [
            ("person_id", "text", "PK"),
            ("full_name", "text", "REQ"),
            ("dob", "date", ""),
            ("notes", "text", ""),
        ],
    )
    tables["organization"] = TableDef(
        "ORGANIZATION",
        [
            ("org_id", "text", "PK"),
            ("name", "text", "REQ"),
            ("type", "text", "court|agency|lawfirm|other"),
        ],
    )
    tables["party"] = TableDef(
        "PARTY",
        [
            ("party_id", "text", "PK"),
            ("party_type", "text", "person|org"),
            ("person_id", "text", "FK->person.person_id"),
            ("org_id", "text", "FK->organization.org_id"),
        ],
    )
    tables["judge"] = TableDef(
        "JUDGE",
        [
            ("judge_id", "text", "PK"),
            ("person_id", "text", "FK->person.person_id"),
            ("court_id", "text", "FK->court.court_id"),
        ],
    )
    tables["case"] = TableDef(
        "CASE",
        [
            ("case_id", "text", "PK"),
            ("case_number", "text", "UNQ"),
            ("court_id", "text", "FK->court.court_id"),
            ("case_type", "text", "custody|ppo|support|other"),
            ("status", "text", "open|closed|post-judgment"),
            ("opened_date", "date", ""),
            ("closed_date", "date", ""),
        ],
    )
    tables["case_party"] = TableDef(
        "CASE_PARTY",
        [
            ("case_party_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id"),
            ("party_id", "text", "FK->party.party_id"),
            ("role", "text", "plaintiff|defendant|petitioner|respondent|other"),
        ],
    )
    tables["file_artifact"] = TableDef(
        "FILE_ARTIFACT",
        [
            ("file_id", "text", "PK"),
            ("storage_root", "text", "F:|gdrive|sandbox"),
            ("path", "text", "REQ"),
            ("bytes", "int", ""),
            ("crc32_hex", "text", ""),
            ("mime", "text", ""),
        ],
    )
    tables["document"] = TableDef(
        "DOCUMENT",
        [
            ("doc_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id NULL"),
            ("doc_type", "text", "motion|order|notice|brief|exhibit|authority|other"),
            ("title", "text", ""),
            ("file_id", "text", "FK->file_artifact.file_id"),
            ("created_date", "date", ""),
            ("served_date", "date", ""),
        ],
    )
    tables["vehicle"] = TableDef(
        "VEHICLE",
        [
            ("vehicle_id", "text", "PK"),
            ("name", "text", "REQ"),
            ("family", "text", "custody|pt|support|ppo|contempt|recusal|jtc|appellate"),
            ("primary_form_id", "text", "FK->form_catalog.form_id NULL"),
        ],
    )
    tables["filing"] = TableDef(
        "FILING",
        [
            ("filing_id", "text", "PK"),
            ("doc_id", "text", "FK->document.doc_id"),
            ("vehicle_id", "text", "FK->vehicle.vehicle_id"),
            ("filed_by_party_id", "text", "FK->party.party_id"),
            ("filed_date", "date", ""),
            ("status", "text", "pending|granted|denied|continued"),
        ],
    )
    tables["service_event"] = TableDef(
        "SERVICE_EVENT",
        [
            ("service_id", "text", "PK"),
            ("doc_id", "text", "FK->document.doc_id"),
            ("served_on_party_id", "text", "FK->party.party_id"),
            ("method", "text", "personal|mail|ecf|email"),
            ("served_date", "date", "REQ"),
            ("proof_doc_id", "text", "FK->document.doc_id"),
            ("defects_json", "json", ""),
        ],
    )
    tables["docket_entry"] = TableDef(
        "DOCKET_ENTRY",
        [
            ("docket_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id"),
            ("filed_date", "date", ""),
            ("title", "text", "REQ"),
            ("doc_id", "text", "FK->document.doc_id"),
            ("resulting_order_id", "text", "FK->order.order_id"),
        ],
    )
    tables["hearing"] = TableDef(
        "HEARING",
        [
            ("hearing_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id"),
            ("scheduled_datetime", "datetime", "REQ"),
            ("hearing_type", "text", "motion|showcause|trial|review"),
            ("judge_id", "text", "FK->judge.judge_id"),
            ("notice_doc_id", "text", "FK->document.doc_id"),
            ("result_order_id", "text", "FK->order.order_id"),
        ],
    )
    tables["order"] = TableDef(
        "ORDER",
        [
            ("order_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id"),
            ("judge_id", "text", "FK->judge.judge_id"),
            ("signed_date", "date", ""),
            ("entered_date", "date", ""),
            ("doc_id", "text", "FK->document.doc_id"),
            ("supersedes_order_id", "text", "FK->order.order_id NULL"),
            ("stay_status", "text", "none|stayed|partial"),
        ],
    )
    tables["authority_source"] = TableDef(
        "AUTHORITY_SOURCE",
        [
            ("source_id", "text", "PK"),
            ("type", "text", "MCR|MCL|MRE|Benchbook|Form|AO|Case|Other"),
            ("title", "text", "REQ"),
            ("file_id", "text", "FK->file_artifact.file_id"),
            ("publisher", "text", "REQ"),
            ("effective_date", "date", ""),
        ],
    )
    tables["authority_anchor"] = TableDef(
        "AUTHORITY_ANCHOR",
        [
            ("anchor_id", "text", "PK"),
            ("source_id", "text", "FK->authority_source.source_id"),
            ("pinpoint", "text", "REQ (rule/§/page/para)"),
            ("excerpt", "text", "<=25w"),
            ("url", "text", ""),
        ],
    )
    tables["authority_triple"] = TableDef(
        "AUTHORITY_TRIPLE",
        [
            ("at_id", "text", "PK"),
            ("proposition", "text", "REQ"),
            ("anchor_id", "text", "FK->authority_anchor.anchor_id"),
            ("status", "text", "controlling|persuasive"),
            ("notes", "text", ""),
        ],
    )
    tables["form_catalog"] = TableDef(
        "FORM_CATALOG",
        [
            ("form_id", "text", "PK"),
            ("code", "text", "REQ"),
            ("name", "text", "REQ"),
            ("court_level", "text", "district|circuit|coa|msc"),
            ("file_id", "text", "FK->file_artifact.file_id"),
        ],
    )
    tables["vehicle_rule_map"] = TableDef(
        "VEHICLE_RULE_MAP",
        [
            ("vrm_id", "text", "PK"),
            ("vehicle_id", "text", "FK->vehicle.vehicle_id"),
            ("anchor_id", "text", "FK->authority_anchor.anchor_id"),
            ("required_findings_json", "json", ""),
        ],
    )
    tables["order_finding"] = TableDef(
        "ORDER_FINDING",
        [
            ("finding_id", "text", "PK"),
            ("order_id", "text", "FK->order.order_id"),
            ("finding_text", "text", "REQ"),
            ("authority_ref_id", "text", "FK->authority_anchor.anchor_id"),
        ],
    )
    tables["order_relief"] = TableDef(
        "ORDER_RELIEF",
        [
            ("relief_id", "text", "PK"),
            ("order_id", "text", "FK->order.order_id"),
            ("relief_text", "text", "REQ"),
            ("requires_findings", "text", ""),
        ],
    )
    tables["obligation"] = TableDef(
        "OBLIGATION",
        [
            ("obligation_id", "text", "PK"),
            ("order_id", "text", "FK->order.order_id"),
            ("obligor_party_id", "text", "FK->party.party_id"),
            ("action", "text", "REQ"),
            ("due_date", "date", ""),
            ("status", "text", "open|partial|satisfied"),
        ],
    )
    tables["deadline"] = TableDef(
        "DEADLINE",
        [
            ("deadline_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id"),
            ("trigger_event", "text", "REQ"),
            ("authority_anchor_id", "text", "FK->authority_anchor.anchor_id"),
            ("due_date", "date", "REQ"),
            ("computed_by_run_id", "text", "FK->run.run_id"),
        ],
    )
    tables["transcript_request"] = TableDef(
        "TRANSCRIPT_REQUEST",
        [
            ("tr_id", "text", "PK"),
            ("hearing_id", "text", "FK->hearing.hearing_id"),
            ("requested_date", "date", "REQ"),
            ("status", "text", "requested|paid|received|delayed"),
            ("request_doc_id", "text", "FK->document.doc_id"),
            ("received_file_id", "text", "FK->file_artifact.file_id"),
        ],
    )
    tables["evidence_atom"] = TableDef(
        "EVIDENCE_ATOM",
        [
            ("ea_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id NULL"),
            ("type", "text", "text|audio|image|pdf|msg|calllog|other"),
            ("file_id", "text", "FK->file_artifact.file_id"),
            ("locator", "text", "page/line/para/timecode"),
            ("event_date", "date", ""),
            ("date_known", "date", ""),
            ("actor_party_id", "text", "FK->party.party_id NULL"),
            ("quote_exact", "text", ""),
        ],
    )
    tables["exhibit"] = TableDef(
        "EXHIBIT",
        [
            ("exhibit_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id"),
            ("offering_party_id", "text", "FK->party.party_id"),
            ("label", "text", "REQ (PltfYellow|DefBlue)"),
            ("cover_doc_id", "text", "FK->document.doc_id"),
            ("primary_file_id", "text", "FK->file_artifact.file_id"),
        ],
    )
    tables["exhibit_evidence"] = TableDef(
        "EXHIBIT_EVIDENCE",
        [
            ("xe_id", "text", "PK"),
            ("exhibit_id", "text", "FK->exhibit.exhibit_id"),
            ("ea_id", "text", "FK->evidence_atom.ea_id"),
        ],
    )
    tables["adverse_language_hit"] = TableDef(
        "ADVERSE_LANGUAGE_HIT",
        [
            ("hit_id", "text", "PK"),
            ("ea_id", "text", "FK->evidence_atom.ea_id"),
            ("term", "text", "REQ"),
            ("context_window", "text", "REQ"),
            ("speaker_party_id", "text", "FK->party.party_id NULL"),
        ],
    )
    tables["claim"] = TableDef(
        "CLAIM",
        [
            ("claim_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id"),
            ("track_id", "text", "FK->track.track_id"),
            ("caption", "text", "REQ"),
            ("elements_json", "json", "REQ"),
            ("burden", "text", "REQ"),
            ("status", "text", "open|partial|satisfied"),
        ],
    )
    tables["claim_evidence"] = TableDef(
        "CLAIM_EVIDENCE",
        [
            ("ce_id", "text", "PK"),
            ("claim_id", "text", "FK->claim.claim_id"),
            ("ea_id", "text", "FK->evidence_atom.ea_id"),
            ("purpose", "text", "supports|contradicts"),
        ],
    )
    tables["contradiction"] = TableDef(
        "CONTRADICTION",
        [
            ("cx_id", "text", "PK"),
            ("case_id", "text", "FK->case.case_id"),
            ("claim_a", "text", "REQ"),
            ("claim_b", "text", "REQ"),
            ("conflict_type", "text", "factual|legal|timeline|order"),
            ("ea_refs_json", "json", "REQ"),
        ],
    )
    tables["jtc_allegation"] = TableDef(
        "JTC_ALLEGATION",
        [
            ("jtc_id", "text", "PK"),
            ("judge_id", "text", "FK->judge.judge_id"),
            ("canon", "text", "REQ"),
            ("event_summary", "text", "REQ"),
            ("ea_refs_json", "json", "REQ"),
            ("authority_anchor_id", "text", "FK->authority_anchor.anchor_id"),
        ],
    )
    tables["run"] = TableDef(
        "RUN",
        [
            ("run_id", "text", "PK"),
            ("started_at", "datetime", "REQ"),
            ("ended_at", "datetime", ""),
            ("mode", "text", "analyze|compile|pcg"),
            ("track_id", "text", "FK->track.track_id"),
            ("case_id", "text", "FK->case.case_id NULL"),
            ("notes", "text", ""),
        ],
    )
    tables["run_output"] = TableDef(
        "RUN_OUTPUT",
        [
            ("ro_id", "text", "PK"),
            ("run_id", "text", "FK->run.run_id"),
            ("output_type", "text", "CASE_STATE|VM|CP|TL|EX|CM|VR|SBNA|DRAFT"),
            ("doc_id", "text", "FK->document.doc_id"),
            ("file_id", "text", "FK->file_artifact.file_id"),
        ],
    )
    tables["validation_result"] = TableDef(
        "VALIDATION_RESULT",
        [
            ("vr_id", "text", "PK"),
            ("run_id", "text", "FK->run.run_id"),
            ("scope", "text", "vehicle|service|deadline|proof|citation"),
            ("status", "text", "PASS|WARN|FAIL"),
            ("detail", "text", "REQ"),
        ],
    )
    return tables


def build_dot(tables_def: dict[str, TableDef]) -> str:
    dot_lines: list[str] = []
    dot_lines.append("digraph ERD {")
    dot_lines.append(
        '  graph [rankdir=LR, bgcolor="white", fontname="Helvetica", splines=ortho, '
        "nodesep=0.35, ranksep=0.6];"
    )
    dot_lines.append('  node [fontname="Helvetica"];')
    dot_lines.append('  edge [color="#4B6FBF", arrowsize=0.7, penwidth=1.0];')

    clusters = {
        "cluster_planes": ("CASCADING_PLANES", ["track", "plane", "plane_dependency"]),
        "cluster_case": (
            "CASE+DOCKET",
            [
                "court",
                "person",
                "organization",
                "party",
                "judge",
                "case",
                "case_party",
                "docket_entry",
                "hearing",
                "order",
                "order_finding",
                "order_relief",
                "obligation",
                "transcript_request",
            ],
        ),
        "cluster_documents": (
            "DOCUMENTS+FILINGS+SERVICE",
            ["file_artifact", "document", "filing", "service_event", "exhibit", "exhibit_evidence"],
        ),
        "cluster_authority": (
            "AUTHORITY+FORMS+VEHICLES",
            ["authority_source", "authority_anchor", "authority_triple", "form_catalog", "vehicle", "vehicle_rule_map"],
        ),
        "cluster_evidence": (
            "EVIDENCE+ANALYTICS",
            [
                "evidence_atom",
                "adverse_language_hit",
                "claim",
                "claim_evidence",
                "contradiction",
                "jtc_allegation",
            ],
        ),
        "cluster_runs": (
            "RUNS+OUTPUTS+VALIDATION",
            ["run", "run_output", "validation_result", "deadline"],
        ),
    }

    for cname, (ctitle, table_names) in clusters.items():
        dot_lines.append(f"  subgraph {cname} {{")
        dot_lines.append(f'    label="{ctitle}"; color="#D0D7E6"; fontsize=12; style="rounded";')
        for table_name in table_names:
            table = tables_def[table_name]
            dot_lines.append("    " + node_table(table_name, table.title, table.fields))
        dot_lines.append("  }")

    edges: list[str] = []
    edges += [
        edge("plane", "track_id", "track", "track_id"),
        edge("plane", "parent_plane_id", "plane", "plane_id", "parent"),
        edge("plane_dependency", "plane_id", "plane", "plane_id"),
        edge("plane_dependency", "depends_on_plane_id", "plane", "plane_id", "depends_on"),
    ]
    edges += [
        edge("judge", "person_id", "person", "person_id"),
        edge("judge", "court_id", "court", "court_id"),
        edge("case", "court_id", "court", "court_id"),
        edge("case_party", "case_id", "case", "case_id"),
        edge("case_party", "party_id", "party", "party_id"),
        edge("party", "person_id", "person", "person_id"),
        edge("party", "org_id", "organization", "org_id"),
        edge("docket_entry", "case_id", "case", "case_id"),
        edge("docket_entry", "doc_id", "document", "doc_id"),
        edge("docket_entry", "resulting_order_id", "order", "order_id"),
        edge("hearing", "case_id", "case", "case_id"),
        edge("hearing", "judge_id", "judge", "judge_id"),
        edge("hearing", "notice_doc_id", "document", "doc_id"),
        edge("hearing", "result_order_id", "order", "order_id"),
        edge("order", "case_id", "case", "case_id"),
        edge("order", "judge_id", "judge", "judge_id"),
        edge("order", "doc_id", "document", "doc_id"),
        edge("order", "supersedes_order_id", "order", "order_id", "supersedes"),
        edge("order_finding", "order_id", "order", "order_id"),
        edge("order_finding", "authority_ref_id", "authority_anchor", "anchor_id"),
        edge("order_relief", "order_id", "order", "order_id"),
        edge("obligation", "order_id", "order", "order_id"),
        edge("obligation", "obligor_party_id", "party", "party_id"),
        edge("transcript_request", "hearing_id", "hearing", "hearing_id"),
        edge("transcript_request", "request_doc_id", "document", "doc_id"),
        edge("transcript_request", "received_file_id", "file_artifact", "file_id"),
    ]
    edges += [
        edge("document", "case_id", "case", "case_id"),
        edge("document", "file_id", "file_artifact", "file_id"),
        edge("filing", "doc_id", "document", "doc_id"),
        edge("filing", "vehicle_id", "vehicle", "vehicle_id"),
        edge("filing", "filed_by_party_id", "party", "party_id"),
        edge("service_event", "doc_id", "document", "doc_id"),
        edge("service_event", "served_on_party_id", "party", "party_id"),
        edge("service_event", "proof_doc_id", "document", "doc_id", "proof"),
        edge("exhibit", "case_id", "case", "case_id"),
        edge("exhibit", "offering_party_id", "party", "party_id"),
        edge("exhibit", "cover_doc_id", "document", "doc_id"),
        edge("exhibit", "primary_file_id", "file_artifact", "file_id"),
        edge("exhibit_evidence", "exhibit_id", "exhibit", "exhibit_id"),
        edge("exhibit_evidence", "ea_id", "evidence_atom", "ea_id"),
    ]
    edges += [
        edge("evidence_atom", "case_id", "case", "case_id"),
        edge("evidence_atom", "file_id", "file_artifact", "file_id"),
        edge("evidence_atom", "actor_party_id", "party", "party_id"),
        edge("adverse_language_hit", "ea_id", "evidence_atom", "ea_id"),
        edge("adverse_language_hit", "speaker_party_id", "party", "party_id"),
        edge("claim", "case_id", "case", "case_id"),
        edge("claim", "track_id", "track", "track_id"),
        edge("claim_evidence", "claim_id", "claim", "claim_id"),
        edge("claim_evidence", "ea_id", "evidence_atom", "ea_id"),
        edge("contradiction", "case_id", "case", "case_id"),
        edge("jtc_allegation", "judge_id", "judge", "judge_id"),
        edge("jtc_allegation", "authority_anchor_id", "authority_anchor", "anchor_id"),
    ]
    edges += [
        edge("authority_source", "file_id", "file_artifact", "file_id"),
        edge("authority_anchor", "source_id", "authority_source", "source_id"),
        edge("authority_triple", "anchor_id", "authority_anchor", "anchor_id"),
        edge("form_catalog", "file_id", "file_artifact", "file_id"),
        edge("vehicle", "primary_form_id", "form_catalog", "form_id"),
        edge("vehicle_rule_map", "vehicle_id", "vehicle", "vehicle_id"),
        edge("vehicle_rule_map", "anchor_id", "authority_anchor", "anchor_id"),
    ]
    edges += [
        edge("run", "track_id", "track", "track_id"),
        edge("run", "case_id", "case", "case_id"),
        edge("run_output", "run_id", "run", "run_id"),
        edge("run_output", "doc_id", "document", "doc_id"),
        edge("run_output", "file_id", "file_artifact", "file_id"),
        edge("validation_result", "run_id", "run", "run_id"),
        edge("deadline", "case_id", "case", "case_id"),
        edge("deadline", "authority_anchor_id", "authority_anchor", "anchor_id"),
        edge("deadline", "computed_by_run_id", "run", "run_id"),
    ]

    dot_lines.extend(edges)
    dot_lines.append("}")
    return "\n".join(dot_lines)


def build_mermaid(tables_def: dict[str, TableDef]) -> str:
    mermaid: list[str] = ["erDiagram"]
    subset = [
        "case",
        "court",
        "judge",
        "party",
        "person",
        "document",
        "filing",
        "order",
        "hearing",
        "evidence_atom",
        "authority_source",
        "authority_anchor",
        "vehicle",
        "run",
        "validation_result",
        "deadline",
        "file_artifact",
    ]
    for table_name in subset:
        table = tables_def[table_name]
        mermaid.append(f"  {table_name.upper()} {{")
        for field_name, field_type, _label in table.fields:
            mermaid_type = "string"
            if field_type == "int":
                mermaid_type = "int"
            elif field_type == "date":
                mermaid_type = "date"
            elif field_type == "datetime":
                mermaid_type = "datetime"
            mermaid.append(f"    {mermaid_type} {field_name}")
        mermaid.append("  }")
    mermaid.extend(
        [
            "  COURT ||--o{ CASE : has",
            "  PERSON ||--o{ JUDGE : is",
            "  COURT ||--o{ JUDGE : assigns",
            "  CASE ||--o{ HEARING : schedules",
            "  CASE ||--o{ ORDER : issues",
            "  FILE_ARTIFACT ||--o{ DOCUMENT : stores",
            "  FILE_ARTIFACT ||--o{ EVIDENCE_ATOM : stores",
            "  DOCUMENT ||--o{ FILING : represented_by",
            "  VEHICLE ||--o{ FILING : uses",
            "  AUTHORITY_SOURCE ||--o{ AUTHORITY_ANCHOR : has",
            "  CASE ||--o{ EVIDENCE_ATOM : contains",
            "  RUN ||--o{ VALIDATION_RESULT : produces",
            "  CASE ||--o{ DEADLINE : has",
        ]
    )
    return "\n".join(mermaid)


def append_fragment(base: str, fragment: str, header: str) -> str:
    lines = [base.rstrip(), "", f"// {header}", fragment.rstrip(), ""]
    return "\n".join(lines)


def build_cycle_ledger(events: Sequence[str]) -> str:
    lines: list[str] = []
    now = dt.datetime.utcnow().isoformat() + "Z"
    for idx, event in enumerate(events, start=1):
        record = {"ts": now, "cycle": idx, "event": event}
        lines.append(json.dumps(record, sort_keys=True))
    return "\n".join(lines) + ("\n" if lines else "")


def build_run_ledger(events: Sequence[str]) -> str:
    lines: list[str] = []
    for event in events:
        record = {"ts": dt.datetime.utcnow().isoformat() + "Z", "event": event}
        lines.append(json.dumps(record, sort_keys=True))
    return "\n".join(lines) + ("\n" if lines else "")


def build_provenance_index(seed_rows: Sequence[dict[str, str | int]]) -> dict[str, object]:
    entries = []
    for row in seed_rows:
        entries.append(
            {
                "artifact_id": row["artifact_id"],
                "zip_file": row["zip_file"],
                "path_in_zip": row["path_in_zip"],
                "bytes": row["bytes"],
                "crc32_hex": row["crc32_hex"],
                "type_guess": row["type_guess"],
            }
        )
    return {"artifacts": entries}


def build_blockers_and_plan(
    missing_inputs: Sequence[str],
    optional_inputs: Sequence[InputDataset],
) -> dict[str, object]:
    return {
        "missing_inputs": list(missing_inputs),
        "available_optional_inputs": [
            {"name": dataset.name, "path": str(dataset.path), "rows": dataset.row_count}
            for dataset in optional_inputs
        ],
        "acquisition_plan": [
            {
                "step": "Provide authoritative mappings (forms, vehicles, authorities) via CSV inputs.",
                "reason": "Source data not available in this run; cannot infer without citations.",
            }
            for _ in missing_inputs
        ],
    }


def build_final_deliverable(out_root: Path) -> dict[str, object]:
    files = []
    for path in out_root.rglob("*"):
        if path.is_file():
            files.append(
                {
                    "path": path.relative_to(out_root).as_posix(),
                    "bytes": path.stat().st_size,
                }
            )
    return {
        "generated_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "out_root": str(out_root),
        "files": sorted(files, key=lambda item: item["path"]),
    }


def self_check_outputs(out_root: Path, required_paths: Sequence[Path]) -> list[str]:
    issues: list[str] = []
    for rel_path in required_paths:
        abs_path = out_root / rel_path
        if not abs_path.exists():
            issues.append(f"missing:{rel_path}")
            continue
        if abs_path.is_file() and abs_path.stat().st_size == 0:
            issues.append(f"empty:{rel_path}")
    return issues


def write_text(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        log_event("dry_run.write_text", path=str(path), bytes=len(content.encode("utf-8")))
        return
    path.write_text(content, encoding="utf-8")


def ensure_dir(path: Path, dry_run: bool) -> None:
    if dry_run:
        log_event("dry_run.mkdir", path=str(path))
        return
    path.mkdir(parents=True, exist_ok=True)


def render_graphviz(dot_path: Path, output_dir: Path, dry_run: bool) -> list[Path]:
    outputs = [
        output_dir / "litigationos_meek234_erd.svg",
        output_dir / "litigationos_meek234_erd.png",
        output_dir / "litigationos_meek234_erd.pdf",
    ]
    if dry_run:
        for path in outputs:
            log_event("dry_run.render", path=str(path))
        return outputs
    for out_path in outputs:
        fmt = out_path.suffix.lstrip(".")
        subprocess.run(["dot", f"-T{fmt}", str(dot_path), "-o", str(out_path)], check=True)
    return outputs


def build_seed_inventory(zip_paths: Iterable[Path]) -> list[dict[str, str | int]]:
    import zipfile

    seed_rows: list[dict[str, str | int]] = []
    artifact_counter = 1
    for zip_path in zip_paths:
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            for info in zip_file.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                seed_rows.append(
                    {
                        "artifact_id": f"AF_{artifact_counter:05d}",
                        "zip_file": zip_path.name,
                        "path_in_zip": name,
                        "bytes": info.file_size,
                        "crc32_hex": f"{info.CRC:08x}",
                        "type_guess": guess_type(name),
                    }
                )
                artifact_counter += 1
    return seed_rows


def build_manifest(out_root: Path, tables: dict[str, TableDef], seed_rows: list[dict[str, str | int]]) -> dict:
    manifest = {
        "pack_id": f"LITIGATIONOS_MEEK234_ERD_PACK_{dt.datetime.utcnow().date().isoformat()}",
        "generated_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "counts": {
            "tables": len(tables),
            "seed_artifacts": len(seed_rows),
        },
        "files": [],
    }
    for path in out_root.rglob("*"):
        if path.is_file():
            manifest["files"].append(
                {
                    "path": path.relative_to(out_root).as_posix(),
                    "bytes": path.stat().st_size,
                }
            )
    manifest["files"] = sorted(manifest["files"], key=lambda item: item["path"])
    return manifest


def write_seed_csv(seed_rows: list[dict[str, str | int]], path: Path, dry_run: bool) -> None:
    if dry_run:
        log_event("dry_run.write_csv", path=str(path), rows=len(seed_rows))
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0].keys()))
        writer.writeheader()
        writer.writerows(seed_rows)


def write_html_wrapper(html_path: Path, svg_path: Path, dry_run: bool) -> None:
    if dry_run:
        log_event("dry_run.write_html", path=str(html_path))
        return
    svg_content = svg_path.read_text(encoding="utf-8")
    html_path.write_text(
        """<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>LitigationOS MEEK2/3/4 ERD</title>
<style>
body { margin: 0; font-family: Helvetica, Arial, sans-serif; }
.header { padding: 10px 14px; background: #f7f7f7; border-bottom: 1px solid #ddd; }
.frame { width: 100vw; height: calc(100vh - 52px); overflow: auto; }
svg { width: 2600px; height: auto; }
.small { color: #666; font-size: 12px; }
</style>
</head>
<body>
<div class="header">
  <div><b>LitigationOS — MEEK2/MEEK3/MEEK4 ERD</b></div>
  <div class="small">Offline HTML wrapper embedding Graphviz SVG (scroll/pan; browser zoom works).</div>
</div>
<div class="frame">
"""
        + svg_content
        + """
</div>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the LitigationOS MEEK2/3/4 ERD pack.")
    parser.add_argument(
        "--zip",
        dest="zip_paths",
        action="append",
        required=True,
        help="Path to a source ZIP to inventory (repeatable).",
    )
    parser.add_argument(
        "--authorities-csv",
        type=Path,
        help="Optional CSV mapping authorities to sources (columns: source_id,title,type,publisher).",
    )
    parser.add_argument(
        "--forms-csv",
        type=Path,
        help="Optional CSV for court forms (columns: form_id,code,name,court_level).",
    )
    parser.add_argument(
        "--vehicles-csv",
        type=Path,
        help="Optional CSV for vehicles (columns: vehicle_id,name,family).",
    )
    parser.add_argument(
        "--append-dot",
        type=Path,
        action="append",
        help="Append additional DOT fragments to the ERD DOT output (repeatable).",
    )
    parser.add_argument(
        "--append-dbml",
        type=Path,
        action="append",
        help="Append additional DBML fragments to the ERD DBML output (repeatable).",
    )
    parser.add_argument(
        "--append-mmd",
        type=Path,
        action="append",
        help="Append additional Mermaid fragments to the ERD Mermaid output (repeatable).",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("artifacts/meek234_erd_pack"),
        help="Output directory root.",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Render SVG/PNG/PDF with Graphviz dot.",
    )
    parser.add_argument("--zip-out", type=Path, help="Write a zip archive of the pack.")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without writing files.")
    parser.add_argument("--self-check", action="store_true", help="Validate expected outputs after build.")
    args = parser.parse_args()

    zip_paths = [Path(path).expanduser().resolve() for path in args.zip_paths]
    for zip_path in zip_paths:
        if not zip_path.exists():
            log_event("error.missing_zip", path=str(zip_path))
            return 2

    out_root = args.out_root
    erd_dir = out_root / "erd"
    seed_dir = out_root / "seed"
    tools_dir = out_root / "tools"
    ensure_dir(erd_dir, args.dry_run)
    ensure_dir(seed_dir, args.dry_run)
    ensure_dir(tools_dir, args.dry_run)

    tables = build_tables()
    seed_rows = build_seed_inventory(zip_paths)
    if not seed_rows:
        log_event("error.no_seed_rows")
        return 3

    seed_csv = seed_dir / "source_artifacts.csv"
    write_seed_csv(seed_rows, seed_csv, args.dry_run)

    dot_path = erd_dir / "litigationos_meek234_erd.dot"
    dot_output = build_dot(tables)
    if args.append_dot:
        for fragment_path in args.append_dot:
            fragment_text = fragment_path.read_text(encoding="utf-8")
            dot_output = append_fragment(dot_output, fragment_text, f"appended:{fragment_path.name}")
    write_text(dot_path, dot_output, args.dry_run)

    dbml_output = to_dbml(tables)
    if args.append_dbml:
        for fragment_path in args.append_dbml:
            fragment_text = fragment_path.read_text(encoding="utf-8")
            dbml_output = append_fragment(dbml_output, fragment_text, f"appended:{fragment_path.name}")
    write_text(erd_dir / "litigationos_meek234_erd.dbml", dbml_output, args.dry_run)

    mermaid_output = build_mermaid(tables)
    if args.append_mmd:
        for fragment_path in args.append_mmd:
            fragment_text = fragment_path.read_text(encoding="utf-8")
            mermaid_output = append_fragment(mermaid_output, fragment_text, f"appended:{fragment_path.name}")
    write_text(erd_dir / "litigationos_meek234_erd.mmd", mermaid_output, args.dry_run)

    svg_path = erd_dir / "litigationos_meek234_erd.svg"
    if args.render:
        render_graphviz(dot_path, erd_dir, args.dry_run)
        if not args.dry_run:
            write_html_wrapper(erd_dir / "litigationos_meek234_erd.html", svg_path, args.dry_run)
    else:
        log_event("render.skipped", reason="--render not set")

    optional_inputs: list[InputDataset] = []
    missing_inputs: list[str] = []
    if args.authorities_csv:
        optional_inputs.append(
            load_optional_csv(
                args.authorities_csv,
                ["source_id", "title", "type", "publisher"],
                "authorities",
            )
        )
    else:
        missing_inputs.append("authorities_csv")
    if args.forms_csv:
        optional_inputs.append(
            load_optional_csv(
                args.forms_csv,
                ["form_id", "code", "name", "court_level"],
                "forms",
            )
        )
    else:
        missing_inputs.append("forms_csv")
    if args.vehicles_csv:
        optional_inputs.append(
            load_optional_csv(
                args.vehicles_csv,
                ["vehicle_id", "name", "family"],
                "vehicles",
            )
        )
    else:
        missing_inputs.append("vehicles_csv")

    cycle_ledger_path = out_root / "cycle_ledger.jsonl"
    cycle_events = [
        "Harvest/Normalize: seed inventory",
        "Graph/Proof: ERD schema export",
        "Package/Audit: manifest + optional zip",
    ]
    write_text(cycle_ledger_path, build_cycle_ledger(cycle_events), args.dry_run)
    run_ledger_path = out_root / "run_ledger.jsonl"
    run_events = [
        "seed_inventory_written",
        "erd_exports_written",
        "optional_inputs_checked",
        "audit_artifacts_written",
    ]
    write_text(run_ledger_path, build_run_ledger(run_events), args.dry_run)
    provenance_path = out_root / "provenance_index.json"
    if args.dry_run:
        log_event("dry_run.write_json", path=str(provenance_path))
    else:
        provenance_path.write_text(json.dumps(build_provenance_index(seed_rows), indent=2), encoding="utf-8")
    blockers_path = out_root / "blockers_and_acquisition_plan.json"
    if args.dry_run:
        log_event("dry_run.write_json", path=str(blockers_path))
    else:
        blockers = build_blockers_and_plan(missing_inputs, optional_inputs)
        blockers_path.write_text(json.dumps(blockers, indent=2), encoding="utf-8")
    final_deliverable_path = out_root / "final_deliverable.json"
    if args.dry_run:
        log_event("dry_run.write_json", path=str(final_deliverable_path))
    else:
        final_deliverable_path.write_text(
            json.dumps(build_final_deliverable(out_root), indent=2),
            encoding="utf-8",
        )

    builder_script = tools_dir / "build_erd.py"
    builder_script_content = """#!/usr/bin/env python3
# build_erd.py — regenerate ERD outputs locally (requires Graphviz `dot` on PATH)
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dot_path = root / "erd" / "litigationos_meek234_erd.dot"


def main() -> None:
    out_svg = root / "erd" / "litigationos_meek234_erd.svg"
    out_png = root / "erd" / "litigationos_meek234_erd.png"
    out_pdf = root / "erd" / "litigationos_meek234_erd.pdf"
    for fmt, outp in [("svg", out_svg), ("png", out_png), ("pdf", out_pdf)]:
        subprocess.run(["dot", f"-T{fmt}", str(dot_path), "-o", str(outp)], check=True)
    print("OK:", out_svg, out_png, out_pdf)


if __name__ == "__main__":
    main()
"""
    write_text(builder_script, builder_script_content, args.dry_run)
    if not args.dry_run:
        builder_script.chmod(0o755)

    readme_path = out_root / "README.md"
    readme_content = """# LitigationOS — MEEK2/MEEK3/MEEK4 ERD Blueprint Pack

## Purpose
ERD-style **cascading planes blueprint** mapping the LitigationOS MEEK2/3/4 universe into:
- **CASCADING_PLANES** (Track/Plane dependency tree)
- **CASE+DOCKET** (case, parties, docket, hearings, orders, obligations, transcripts)
- **DOCUMENTS+FILINGS+SERVICE** (documents, filings/vehicles, service, exhibits)
- **AUTHORITY+FORMS+VEHICLES** (authority sources/anchors/triples + form/vehicle mapping)
- **EVIDENCE+ANALYTICS** (evidence atoms, adverse language, claims, contradictions, JTC allegations)
- **RUNS+OUTPUTS+VALIDATION** (runs, outputs, validations, deadlines)

## Open
- `erd/litigationos_meek234_erd.html` (best viewer)
- or `erd/litigationos_meek234_erd.pdf` (printable)

## Edit
- edit `erd/litigationos_meek234_erd.dot` then run `python tools/build_erd.py`
- or paste `erd/litigationos_meek234_erd.dbml` into dbdiagram.io (optional)

## Seed
- `seed/source_artifacts.csv` lists the source PDFs found in the uploaded ZIPs (CRC32+size only).

## Output contract
- `cycle_ledger.jsonl` captures the Harvest/Graph/Package phases for audit trails.
- `run_ledger.jsonl` captures per-run operations and timing in JSONL.
- `provenance_index.json` provides source artifact provenance.
- `blockers_and_acquisition_plan.json` lists missing optional inputs and acquisition steps.
- `final_deliverable.json` lists outputs for handoff or packaging.

## Optional inputs
- `--authorities-csv` for authority catalog rows (source_id,title,type,publisher).
- `--forms-csv` for form catalog rows (form_id,code,name,court_level).
- `--vehicles-csv` for vehicle catalog rows (vehicle_id,name,family).
- `--append-dot` to add DOT fragments into the ERD output.
- `--append-dbml` to add DBML fragments into the ERD output.
- `--append-mmd` to add Mermaid fragments into the ERD output.

## Validation
- `--self-check` validates required outputs and sizes after build.
"""
    write_text(readme_path, readme_content, args.dry_run)

    if args.dry_run:
        log_event("dry_run.skip_manifest")
    else:
        manifest = build_manifest(out_root, tables, seed_rows)
        (out_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if args.self_check and not args.dry_run:
        required = [
            Path("seed/source_artifacts.csv"),
            Path("erd/litigationos_meek234_erd.dot"),
            Path("erd/litigationos_meek234_erd.dbml"),
            Path("erd/litigationos_meek234_erd.mmd"),
            Path("cycle_ledger.jsonl"),
            Path("run_ledger.jsonl"),
            Path("provenance_index.json"),
            Path("blockers_and_acquisition_plan.json"),
            Path("final_deliverable.json"),
            Path("manifest.json"),
        ]
        issues = self_check_outputs(out_root, required)
        if issues:
            log_event("self_check.failed", issues=issues)
            return 4
        log_event("self_check.passed", outputs=len(required))

    if args.zip_out:
        if args.dry_run:
            log_event("dry_run.zip", path=str(args.zip_out))
        else:
            import zipfile

            if args.zip_out.exists():
                args.zip_out.unlink()
            with zipfile.ZipFile(args.zip_out, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                for path in out_root.rglob("*"):
                    if path.is_file():
                        zip_file.write(path, arcname=path.relative_to(out_root))
            log_event("zip.written", path=str(args.zip_out), bytes=args.zip_out.stat().st_size)

    log_event("pack.complete", out_root=str(out_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
