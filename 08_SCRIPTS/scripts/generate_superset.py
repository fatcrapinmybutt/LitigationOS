from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE = Path('/mnt/data/litos_dense_build')
EXTRACTED_CSV = BASE / 'out' / 'field_catalog.csv'
OUTROOT = BASE / 'outpack'

# Clean output
if OUTROOT.exists():
    # Only remove generated files; keep dirs if re-run
    for p in OUTROOT.rglob('*'):
        if p.is_file():
            p.unlink()
else:
    OUTROOT.mkdir(parents=True, exist_ok=True)

(OUTROOT/'docs').mkdir(parents=True, exist_ok=True)
(OUTROOT/'model').mkdir(parents=True, exist_ok=True)
(OUTROOT/'diagrams').mkdir(parents=True, exist_ok=True)

@dataclass
class F:
    name: str
    typ: str
    req: bool = False
    notes: str = ''

@dataclass
class Rel:
    frm: str
    frm_field: str
    to: str
    to_field: str
    rel_name: str
    card: str  # 1:1, 1:N, M:N
    origin: str = 'PROPOSED'
    notes: str = ''

@dataclass
class E:
    name: str
    desc: str
    origin: str = 'PROPOSED'
    pk: str = ''
    fields: List[F] = field(default_factory=list)


def common_fields(prefix: str = '') -> List[F]:
    p = prefix
    return [
        F(p+'id', 'ulid', True, 'Primary identifier (ULID recommended).'),
        F(p+'created_utc', 'datetime_rfc3339', True, 'Created timestamp (UTC).'),
        F(p+'updated_utc', 'datetime_rfc3339', False, 'Last updated timestamp (UTC).'),
        F(p+'created_by_agent_id', 'ulid', False, 'Agent/worker that created the record.'),
        F(p+'updated_by_agent_id', 'ulid', False, 'Agent/worker that last updated the record.'),
        F(p+'status', 'enum', False, 'Lifecycle status (e.g., ACTIVE, CLOSED, DEPRECATED, etc.).'),
        F(p+'tags_json', 'json', False, 'Freeform tags / labels.'),
        F(p+'notes', 'text', False, 'Human notes.'),
        F(p+'integrity_key', 'text', False, 'IntegrityKey(BundleUID+EntryPath+CRC32+bytes+mtime) per your spec.'),
        F(p+'source_ref', 'text', False, 'Canonical source pointer (Vault CID / path / locator).'),
    ]


def add_entity(entities: Dict[str, E], e: E):
    if not e.pk:
        e.pk = f"{e.name.lower()}_id"
    # Ensure pk exists as field
    if not any(f.name == e.pk for f in e.fields):
        e.fields = [F(e.pk, 'ulid', True, 'Primary key.')] + e.fields
    entities[e.name] = e


entities: Dict[str, E] = {}
rels: List[Rel] = []

# ---------------------------
# Canonical domain tables (high-density)
# ---------------------------

add_entity(entities, E(
    name='Workspace',
    desc='Top-level container for a LitigationOS universe (drives, cases, authority snapshots, runs).',
    fields=common_fields('workspace_') + [
        F('workspace_name','text',True),
        F('canonical_drive_root','text',False,'Typically F:/ for litigation data; D:/ for revenue.'),
        F('google_drive_roots_json','json',False,'e.g., EDS-USB, Litigation_OS$.'),
        F('vault_base_url','text',False,'e.g., http://localhost:8899'),
        F('neo4j_uri','text',False),
        F('neo4j_db','text',False),
        F('default_timezone','text',False,'IANA tz'),
        F('policy_bundle_ref','text',False,'Active policy-as-code bundle'),
    ]
))

add_entity(entities, E(
    name='Case',
    desc='A legal case or matter (trial/appellate/admin).',
    fields=common_fields('case_') + [
        F('workspace_id','ulid',True),
        F('case_number','text',False),
        F('caption','text',False),
        F('track','enum',False,'MEEK1..MEEK4 etc.'),
        F('court_id','ulid',False),
        F('case_type','enum',False,'Custody, PPO, LT, Appeal, JTC, etc.'),
        F('filed_date','date',False),
        F('closed_date','date',False),
        F('is_active','bool',False),
        F('controlling_order_id','ulid',False,'Order currently controlling core posture.'),
        F('register_of_actions_artifact_id','ulid',False),
        F('case_summary_md_artifact_id','ulid',False),
        F('case_state_json_artifact_id','ulid',False,'Schema-enforced CASE_STATE output.'),
        F('risk_flags_json','json',False,'Bias/retaliation/waiver hazards.'),
    ]
))

add_entity(entities, E(
    name='Court',
    desc='Court or tribunal (trial, appellate, agency, JTC).',
    fields=common_fields('court_') + [
        F('workspace_id','ulid',True),
        F('court_name','text',True),
        F('court_level','enum',False,'Trial / COA / MSC / Agency / JTC / Federal overlay.'),
        F('jurisdiction','text',False,'Michigan, WDMI, etc.'),
        F('county','text',False),
        F('location_address_id','ulid',False),
        F('efile_portal','text',False,'MiFile, etc.'),
        F('local_admin_orders_artifact_id','ulid',False),
    ]
))

add_entity(entities, E(
    name='Person',
    desc='A natural person (party, witness, judge, clerk, etc.).',
    fields=common_fields('person_') + [
        F('workspace_id','ulid',True),
        F('full_name','text',True),
        F('dob','date',False),
        F('role_flags_json','json',False,'party/witness/judge/etc'),
        F('primary_address_id','ulid',False),
        F('primary_phone','text',False),
        F('primary_email','text',False),
        F('bar_number','text',False,'If attorney.'),
        F('notes_sensitive','text',False,'Use redaction policy if exported.'),
    ]
))

add_entity(entities, E(
    name='Organization',
    desc='An organization (landlord entity, agency, law firm, etc.).',
    fields=common_fields('org_') + [
        F('workspace_id','ulid',True),
        F('org_name','text',True),
        F('org_type','enum',False,'LLC, court, agency, etc.'),
        F('registered_agent_person_id','ulid',False),
        F('registered_address_id','ulid',False),
        F('website','text',False),
        F('ein','text',False),
    ]
))

add_entity(entities, E(
    name='Address',
    desc='Postal address normalized.',
    fields=common_fields('addr_') + [
        F('workspace_id','ulid',True),
        F('line1','text',True),
        F('line2','text',False),
        F('city','text',True),
        F('state','text',True),
        F('postal_code','text',True),
        F('country','text',False),
        F('lat','float',False),
        F('lng','float',False),
    ]
))

# Procedural spine
add_entity(entities, E(
    name='DocketEntry',
    desc='Register of actions / docket entry.',
    fields=common_fields('docket_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',True),
        F('docket_seq','int',False),
        F('filed_utc','datetime_rfc3339',False),
        F('entry_text','text',False),
        F('entry_type','enum',False),
        F('document_id','ulid',False),
        F('order_id','ulid',False),
        F('hearing_id','ulid',False),
        F('fee_amount','money',False),
        F('receipt_artifact_id','ulid',False),
        F('mifile_txn_id','text',False),
    ]
))

add_entity(entities, E(
    name='Document',
    desc='A logical document (motion, brief, order, exhibit cover, transcript, etc.) independent of files.',
    fields=common_fields('doc_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('doc_type','enum',True),
        F('title','text',False),
        F('version_label','text',False),
        F('author_person_id','ulid',False),
        F('created_local_date','date',False),
        F('filed_date','date',False),
        F('filed_by_party_link_id','ulid',False),
        F('primary_artifact_id','ulid',False,'Current primary file artifact (PDF/DOCX).'),
        F('text_extract_artifact_id','ulid',False),
        F('ocr_extract_artifact_id','ulid',False),
        F('pii_scan_report_artifact_id','ulid',False),
        F('redaction_plan_artifact_id','ulid',False),
        F('quote_anchor_index_artifact_id','ulid',False),
        F('authority_snapshot_id','ulid',False),
        F('pcw_gate_result_id','ulid',False),
    ]
))

add_entity(entities, E(
    name='Filing',
    desc='A filing event (submitted to court).',
    fields=common_fields('filing_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',True),
        F('document_id','ulid',True),
        F('filed_utc','datetime_rfc3339',False),
        F('filed_method','enum',False,'MiFile, in-person, mail.'),
        F('fee_paid','money',False),
        F('fee_waiver_requested','bool',False),
        F('fee_receipt_artifact_id','ulid',False),
        F('served','bool',False),
        F('service_batch_id','ulid',False),
        F('docket_entry_id','ulid',False),
        F('resulting_order_id','ulid',False),
    ]
))

add_entity(entities, E(
    name='Order',
    desc='An order issued by the court.',
    fields=common_fields('order_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',True),
        F('document_id','ulid',False),
        F('signed_date','date',False),
        F('entered_date','date',False),
        F('judge_person_id','ulid',False),
        F('order_type','enum',False),
        F('is_interim','bool',False),
        F('supersedes_order_id','ulid',False),
        F('stayed_by_order_id','ulid',False),
        F('effective_date','date',False),
        F('expiration_date','date',False),
        F('findings_required','bool',False),
        F('findings_text_extract','text',False),
        F('relief_summary_json','json',False),
        F('deadline_bundle_id','ulid',False,'Derived deadlines from order.'),
    ]
))

add_entity(entities, E(
    name='Hearing',
    desc='A scheduled court hearing/session.',
    fields=common_fields('hearing_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',True),
        F('court_id','ulid',False),
        F('hearing_type','enum',False),
        F('scheduled_start_utc','datetime_rfc3339',False),
        F('scheduled_end_utc','datetime_rfc3339',False),
        F('actual_start_utc','datetime_rfc3339',False),
        F('actual_end_utc','datetime_rfc3339',False),
        F('judge_person_id','ulid',False),
        F('location','text',False),
        F('is_evidentiary','bool',False),
        F('was_on_record','bool',False),
        F('minutes_artifact_id','ulid',False),
        F('transcript_id','ulid',False),
        F('resulting_order_id','ulid',False),
    ]
))

add_entity(entities, E(
    name='Transcript',
    desc='Hearing transcript (logical).',
    fields=common_fields('tx_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',True),
        F('hearing_id','ulid',True),
        F('requested_date','date',False),
        F('received_date','date',False),
        F('vendor','text',False),
        F('pages','int',False),
        F('cost','money',False),
        F('audio_artifact_id','ulid',False),
        F('pdf_artifact_id','ulid',False),
        F('text_extract_artifact_id','ulid',False),
        F('quote_anchor_index_artifact_id','ulid',False),
        F('objection_offer_proof_matrix_artifact_id','ulid',False),
    ]
))

# Evidence plane
add_entity(entities, E(
    name='EvidenceItem',
    desc='A piece of evidence (file, photo, report, message export, etc.).',
    fields=common_fields('ev_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('evidence_type','enum',True),
        F('title','text',False),
        F('captured_utc','datetime_rfc3339',False),
        F('source_device','text',False),
        F('source_app','text',False),
        F('original_artifact_id','ulid',True),
        F('derived_text_artifact_id','ulid',False),
        F('derived_ocr_artifact_id','ulid',False),
        F('metadata_json','json',False),
        F('authentication_notes','text',False),
        F('mre_foundation_checklist_json','json',False),
        F('sensitivity_level','enum',False),
    ]
))

add_entity(entities, E(
    name='Exhibit',
    desc='An exhibit prepared for filing/hearing, linking EvidenceItems to a packet with cover pages.',
    fields=common_fields('exh_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',True),
        F('exhibit_label','text',True,'Exhibit A, B, ...'),
        F('offering_party','enum',False,'Plaintiff/Defendant'),
        F('cover_document_id','ulid',False),
        F('compiled_pdf_artifact_id','ulid',False),
        F('exhibit_matrix_row_id','ulid',False),
        F('is_filed','bool',False),
        F('filed_filing_id','ulid',False),
    ]
))

add_entity(entities, E(
    name='EvidenceAtom',
    desc='Smallest analyzable unit (fact/quote/metadata fragment) extracted from EvidenceItem.',
    fields=common_fields('atom_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('evidence_item_id','ulid',True),
        F('atom_type','enum',True,'quote|timestamp|field|message|image_region|etc'),
        F('content_text','text',False),
        F('content_json','json',False),
        F('content_hash','text',False),
        F('source_locator','text',False,'Re-open recipe: bundle→entry→page/line/time.'),
        F('start_offset','int',False),
        F('end_offset','int',False),
        F('start_time_ms','int',False),
        F('end_time_ms','int',False),
        F('confidence','float',False),
        F('quote_lock_status','enum',False,'CANDIDATE|VERIFIED'),
        F('verification_artifact_id','ulid',False),
    ]
))

add_entity(entities, E(
    name='Statement',
    desc='A statement (utterance/claim) attributable to a speaker or source; may be true/false/unknown.',
    fields=common_fields('stmt_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('speaker_person_id','ulid',False),
        F('speaker_role','text',False),
        F('statement_text','text',True),
        F('statement_date','date',False),
        F('context','text',False),
        F('source_atom_id','ulid',False),
        F('classification','enum',False,'assertion/denial/accusation'),
    ]
))

add_entity(entities, E(
    name='Fact',
    desc='A normalized fact candidate with provenance to EvidenceAtoms and evaluation state.',
    fields=common_fields('fact_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('fact_text','text',True),
        F('fact_type','enum',False),
        F('truth_status','enum',False,'OPEN|PARTIAL|SATISFIED per PCW-like grading.'),
        F('harm_category','enum',False),
        F('materiality','enum',False),
        F('validation_notes','text',False),
    ]
))

add_entity(entities, E(
    name='Contradiction',
    desc='Explicit contradiction mapping between two statements/facts.',
    fields=common_fields('cx_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('lhs_statement_id','ulid',False),
        F('rhs_statement_id','ulid',False),
        F('lhs_fact_id','ulid',False),
        F('rhs_fact_id','ulid',False),
        F('contradiction_type','enum',False),
        F('analysis','text',False),
    ]
))

# Authority plane
add_entity(entities, E(
    name='AuthoritySource',
    desc='A primary authority source (MCR/MCL/MRE/Benchbook/MSC AO/COA cases/JTC rules, etc.).',
    fields=common_fields('authsrc_') + [
        F('workspace_id','ulid',True),
        F('authority_kind','enum',True),
        F('title','text',True),
        F('publisher','text',False),
        F('effective_date','date',False),
        F('version_label','text',False),
        F('source_artifact_id','ulid',False),
        F('extracted_text_artifact_id','ulid',False),
        F('citation_style','text',False),
    ]
))

add_entity(entities, E(
    name='AuthorityPinpoint',
    desc='Pinpoint locator within an authority source (section, page/line, paragraph, etc.).',
    fields=common_fields('pin_') + [
        F('workspace_id','ulid',True),
        F('authority_source_id','ulid',True),
        F('pin_type','enum',True,'section|page_line|para|holding|rule_part'),
        F('pin_label','text',True,'e.g., MCR 2.003(C)(1) or p.12 l.3-10'),
        F('pin_path','text',False,'machine path'),
        F('page','int',False),
        F('line_start','int',False),
        F('line_end','int',False),
        F('excerpt_verified','bool',False),
        F('excerpt_text','text',False,'Only if QuoteLock verified.'),
        F('verification_artifact_id','ulid',False),
    ]
))

add_entity(entities, E(
    name='Proposition',
    desc='Atomic legal proposition used in drafting; must cite AuthorityPinpoints inside snapshot for PCG outputs.',
    fields=common_fields('prop_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('proposition_text','text',True),
        F('domain','enum',False,'procedure|substantive|evidence|appellate'),
        F('authority_snapshot_id','ulid',False),
        F('confidence','float',False),
        F('status_gate','enum',False,'DRAFT|VERIFIED|RELEASE'),
    ]
))

add_entity(entities, E(
    name='AuthoritySnapshot',
    desc='Frozen set of authorities valid for a run/release boundary.',
    fields=common_fields('snap_') + [
        F('workspace_id','ulid',True),
        F('snapshot_label','text',True),
        F('created_for_run_id','ulid',False),
        F('coverage_json','json',False,'Which MCR/MCL/MRE etc included.'),
        F('index_artifact_id','ulid',False,'auth_snapshot_index.json'),
        F('is_locked','bool',False),
    ]
))

# PCW plane
add_entity(entities, E(
    name='Vehicle',
    desc='Procedural vehicle (motion/complaint/appeal form) forms-first.',
    fields=common_fields('veh_') + [
        F('workspace_id','ulid',True),
        F('vehicle_name','text',True),
        F('vehicle_type','enum',False,'Motion, Appeal, JTC complaint, etc.'),
        F('scao_form_id','ulid',False),
        F('trigger_conditions_json','json',False),
        F('elements_grid_artifact_id','ulid',False),
        F('default_deadlines_json','json',False),
    ]
))

add_entity(entities, E(
    name='ProofObligation',
    desc='Proof obligation (PO) required by a vehicle, keyed to authority + evidence requirements.',
    fields=common_fields('po_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('vehicle_id','ulid',True),
        F('po_code','text',True),
        F('po_name','text',True),
        F('po_type','enum',False,'CoreSAT|NonCore'),
        F('authority_snapshot_id','ulid',False),
        F('required_authority_pins_json','json',False),
        F('required_evidence_types_json','json',False),
        F('status','enum',False,'OBLIGATION_OPEN|OBLIGATION_PARTIAL|OBLIGATION_SATISFIED'),
        F('assurance_score','float',False),
        F('validator_version','text',False),
        F('last_evaluated_utc','datetime_rfc3339',False),
    ]
))

add_entity(entities, E(
    name='GateResult',
    desc='A gate evaluation decision for a stage/run artifact.',
    fields=common_fields('gate_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('run_id','ulid',False),
        F('stage','text',True),
        F('status','enum',True,'PASS|FAIL|PARTIAL|DEGRADED'),
        F('unsat_core_artifact_id','ulid',False),
        F('decision_md_artifact_id','ulid',False),
        F('policy_bundle_artifact_id','ulid',False),
        F('metrics_json','json',False),
    ]
))

# Runs + artifacts
add_entity(entities, E(
    name='Run',
    desc='A deterministic run (R##) producing manifests, reports, cyclepacks.',
    fields=common_fields('run_') + [
        F('workspace_id','ulid',True),
        F('series_id','text',False),
        F('run_name','text',True),
        F('started_utc','datetime_rfc3339',True),
        F('ended_utc','datetime_rfc3339',False),
        F('status','enum',True,'INIT|RUNNING|DEGRADED|FAILED|COMPLETED'),
        F('inputs_manifest_artifact_id','ulid',False),
        F('outputs_manifest_artifact_id','ulid',False),
        F('run_ledger_artifact_id','ulid',False),
        F('event_log_artifact_id','ulid',False),
        F('checkpoint_artifact_id','ulid',False),
        F('tool_versions_json','json',False),
        F('idempotency_keys_json','json',False),
    ]
))

add_entity(entities, E(
    name='Artifact',
    desc='A file artifact (original or derived) tracked with lineage.',
    fields=common_fields('art_') + [
        F('workspace_id','ulid',True),
        F('artifact_kind','enum',True),
        F('relative_path','text',True),
        F('filename','text',True),
        F('extension','text',False),
        F('mime_type','text',False),
        F('bytes','int',False),
        F('crc32','text',False),
        F('mtime_utc','datetime_rfc3339',False),
        F('derived_from_artifact_id','ulid',False),
        F('derivation_activity_id','ulid',False),
        F('vault_cid','text',False),
        F('content_preview','text',False),
    ]
))

add_entity(entities, E(
    name='DerivationActivity',
    desc='PROV-style activity node for transformations (extract, OCR, parse, compile, etc.).',
    fields=common_fields('act_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('activity_type','enum',True),
        F('tool_name','text',False),
        F('tool_version','text',False),
        F('started_utc','datetime_rfc3339',False),
        F('ended_utc','datetime_rfc3339',False),
        F('params_json','json',False),
        F('metrics_json','json',False),
        F('logs_artifact_id','ulid',False),
    ]
))

# ---------------------------
# MEGA EXPANSION: additional canonical tables (max-density)
# Goal: "all tables physically possible" while keeping the model normalized.
# Every table uses the same audit fields + explicit *_id foreign keys so relationships can be inferred.
# ---------------------------

def add_many(defs: List[E]):
    for d in defs:
        add_entity(entities, d)


add_many([
    # --- Automation / observability / agents ---
    E('Agent', 'Executable actor (human or automation worker).', fields=common_fields('agent_') + [
        F('workspace_id','ulid',True),
        F('agent_name','text',True),
        F('agent_type','enum',False,'human|script|service|llm|scheduler'),
        F('host_fingerprint','text',False),
        F('runtime','text',False,'python/node/powershell/etc'),
        F('runtime_version','text',False),
        F('capabilities_json','json',False),
        F('default_workdir','text',False),
        F('default_output_root','text',False),
        F('security_profile','enum',False),
    ]),
    E('RunStep', 'A step within a Run (pipeline stage execution).', fields=common_fields('step_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',True),
        F('step_name','text',True),
        F('step_seq','int',False),
        F('stage','enum',False,'Atoms|Deltas|Signals|Scores|Gates|Actions|Vehicles|Graph|Packaging'),
        F('started_utc','datetime_rfc3339',False),
        F('ended_utc','datetime_rfc3339',False),
        F('status','enum',False,'OK|WARN|FAIL|SKIP'),
        F('input_artifacts_json','json',False),
        F('output_artifacts_json','json',False),
        F('metrics_json','json',False),
        F('error_artifact_id','ulid',False),
    ]),
    E('RunEvent', 'Event log row for runs/steps (audit).', fields=common_fields('evt_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('step_id','ulid',False),
        F('agent_id','ulid',False),
        F('event_time_utc','datetime_rfc3339',True),
        F('event_type','enum',True),
        F('severity','enum',False,'DEBUG|INFO|WARN|ERROR|FATAL'),
        F('message','text',False),
        F('context_json','json',False),
        F('related_artifact_id','ulid',False),
    ]),
    E('RunMetric', 'Key/value metrics (for dashboards and ADD scoring).', fields=common_fields('metric_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('step_id','ulid',False),
        F('metric_name','text',True),
        F('metric_value','float',False),
        F('metric_value_text','text',False),
        F('unit','text',False),
        F('dimensions_json','json',False),
        F('observed_utc','datetime_rfc3339',False),
    ]),
    E('Schedule', 'Recurring schedule definition (e.g., 4x/day harvest).', fields=common_fields('sched_') + [
        F('workspace_id','ulid',True),
        F('schedule_name','text',True),
        F('cron','text',False),
        F('timezone','text',False),
        F('is_enabled','bool',False),
        F('target_pipeline','text',False),
        F('params_json','json',False),
        F('last_run_id','ulid',False),
        F('next_due_utc','datetime_rfc3339',False),
    ]),

    # --- Storage / bundles / manifests / provenance ---
    E('Bundle', 'A packaged deliverable (ZIP folder, MiFile packet, authority pack, etc.).', fields=common_fields('bundle_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('bundle_type','enum',True,'zip|packet|authority_pack|context_pack'),
        F('bundle_version','text',False),
        F('root_path','text',False),
        F('primary_artifact_id','ulid',False),
        F('manifest_artifact_id','ulid',False),
        F('integrity_check_id','ulid',False),
        F('signature_id','ulid',False),
        F('readme_artifact_id','ulid',False),
        F('release_notes_artifact_id','ulid',False),
    ]),
    E('BundleEntry', 'A file/member row within a Bundle.', fields=common_fields('be_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',True),
        F('artifact_id','ulid',False),
        F('relative_path','text',True),
        F('bytes','int',False),
        F('crc32','text',False),
        F('mtime_utc','datetime_rfc3339',False),
        F('role','enum',False,'source|output|log|manifest|index|diagram'),
        F('content_type','text',False),
    ]),
    E('IntegrityCheck', 'Integrity verification run (zip test, CRC scan, duplicates, etc.).', fields=common_fields('ic_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('artifact_id','ulid',False),
        F('check_type','enum',True,'zip_test|crc_scan|schema_validate|pii_scan|quote_lock'),
        F('status','enum',False,'PASS|WARN|FAIL'),
        F('started_utc','datetime_rfc3339',False),
        F('ended_utc','datetime_rfc3339',False),
        F('findings_artifact_id','ulid',False),
        F('metrics_json','json',False),
    ]),
    E('Signature', 'Signature / attestation for a bundle (optional, free tooling only).', fields=common_fields('sig_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('artifact_id','ulid',False),
        F('sig_type','enum',False,'minisign|cosign|pgp'),
        F('public_key_ref','text',False),
        F('signature_artifact_id','ulid',False),
        F('attestation_artifact_id','ulid',False),
        F('signed_utc','datetime_rfc3339',False),
    ]),
    E('ProvenanceEntity', 'W3C PROV Entity mirror row (interop).', fields=common_fields('prov_e_') + [
        F('workspace_id','ulid',True),
        F('external_id','text',False),
        F('label','text',False),
        F('type','text',False),
        F('value_json','json',False),
        F('generated_at_utc','datetime_rfc3339',False),
        F('location','text',False),
    ]),
    E('ProvenanceActivity', 'W3C PROV Activity mirror row (interop).', fields=common_fields('prov_a_') + [
        F('workspace_id','ulid',True),
        F('external_id','text',False),
        F('label','text',False),
        F('type','text',False),
        F('started_at_utc','datetime_rfc3339',False),
        F('ended_at_utc','datetime_rfc3339',False),
        F('location','text',False),
    ]),
    E('ProvenanceAgent', 'W3C PROV Agent mirror row (interop).', fields=common_fields('prov_g_') + [
        F('workspace_id','ulid',True),
        F('external_id','text',False),
        F('label','text',False),
        F('type','text',False),
        F('location','text',False),
    ]),
    E('ProvenanceRelation', 'W3C PROV relations (wasGeneratedBy/used/wasDerivedFrom/etc.).', fields=common_fields('prov_r_') + [
        F('workspace_id','ulid',True),
        F('rel_type','enum',True),
        F('from_external_id','text',False),
        F('to_external_id','text',False),
        F('attrs_json','json',False),
    ]),

    # --- Evidence / foundation / redaction ---
    E('PIIItem', 'PII/PHI finding (for redaction workflows).', fields=common_fields('pii_') + [
        F('workspace_id','ulid',True),
        F('artifact_id','ulid',True),
        F('document_id','ulid',False),
        F('pii_type','enum',True),
        F('confidence','float',False),
        F('locator_json','json',False,'page/line/bbox/timecode'),
        F('text_snippet','text',False),
        F('recommended_action','enum',False,'redact|mask|review'),
    ]),
    E('RedactionAction', 'Planned or executed redaction step.', fields=common_fields('red_') + [
        F('workspace_id','ulid',True),
        F('artifact_id','ulid',True),
        F('pii_item_id','ulid',False),
        F('action_type','enum',True,'box|text_replace|remove_page|metadata_strip'),
        F('action_params_json','json',False),
        F('status','enum',False,'PLANNED|DONE|SKIPPED'),
        F('output_artifact_id','ulid',False),
    ]),
    E('EvidenceFoundationCheck', 'MRE-based admissibility checklist row per exhibit/artifact.', fields=common_fields('mre_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('evidence_item_id','ulid',False),
        F('artifact_id','ulid',False),
        F('exhibit_id','ulid',False),
        F('rule','text',False,'MRE citation string'),
        F('issue','text',False,'authentication|hearsay|best_evidence|relevance|403|etc'),
        F('status','enum',False,'OPEN|PARTIAL|SATISFIED|BLOCKED'),
        F('supporting_atom_ids_json','json',False),
        F('notes','text',False),
    ]),

    # --- Service chain ---
    E('ServicePlan', 'Planned service chain for a filing (methods, addresses, deadlines).', fields=common_fields('svc_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('filing_id','ulid',False),
        F('served_party_link_id','ulid',False),
        F('method','enum',False,'mail|personal|email|mifile|publication'),
        F('address_id','ulid',False),
        F('deadline_utc','datetime_rfc3339',False),
        F('status','enum',False,'PLANNED|IN_PROGRESS|COMPLETE|FAILED'),
        F('notes','text',False),
    ]),
    E('ServiceAttempt', 'A concrete attempt instance (date, carrier, tracking).', fields=common_fields('svca_') + [
        F('workspace_id','ulid',True),
        F('service_plan_id','ulid',True),
        F('attempted_utc','datetime_rfc3339',False),
        F('carrier','text',False),
        F('tracking_number','text',False),
        F('result','enum',False,'SENT|DELIVERED|RETURNED|REFUSED|UNKNOWN'),
        F('proof_artifact_id','ulid',False),
    ]),
    E('ServiceProof', 'Service proof object (receipt, affidavit of service).', fields=common_fields('svcp_') + [
        F('workspace_id','ulid',True),
        F('service_attempt_id','ulid',True),
        F('proof_type','enum',False,'receipt|affidavit|mifile_confirmation'),
        F('artifact_id','ulid',False),
        F('verified','bool',False),
        F('verified_by_agent_id','ulid',False),
        F('verified_utc','datetime_rfc3339',False),
    ]),

    # --- Record survival / transcripts / objections ---
    E('TranscriptRequest', 'Request for transcript (tracking).', fields=common_fields('trq_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',True),
        F('hearing_id','ulid',False),
        F('requested_from_person_id','ulid',False,'court reporter/clerk'),
        F('requested_utc','datetime_rfc3339',False),
        F('due_utc','datetime_rfc3339',False),
        F('status','enum',False,'REQUESTED|PAID|RECEIVED|OVERDUE'),
        F('receipt_artifact_id','ulid',False),
        F('transcript_id','ulid',False),
    ]),
    E('TranscriptSegment', 'Timestamped / page-line segment inside a transcript.',
      fields=common_fields('trs_') + [
        F('workspace_id','ulid',True),
        F('transcript_id','ulid',True),
        F('page_start','int',False),
        F('line_start','int',False),
        F('page_end','int',False),
        F('line_end','int',False),
        F('time_start','text',False),
        F('time_end','text',False),
        F('speaker_person_id','ulid',False),
        F('text','text',False),
        F('quote_anchor_id','ulid',False),
      ]),
    E('Objection', 'On-record objection (for appeal preservation).', fields=common_fields('obj_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',True),
        F('hearing_id','ulid',False),
        F('transcript_segment_id','ulid',False),
        F('objecting_party_link_id','ulid',False),
        F('basis','text',False,'rule|relevance|hearsay|foundation|etc'),
        F('ruling','enum',False,'SUSTAINED|OVERRULED|RESERVED'),
        F('notes','text',False),
    ]),
    E('OfferOfProof', 'Offer of proof payload (what was excluded).', fields=common_fields('oop_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',True),
        F('hearing_id','ulid',False),
        F('document_id','ulid',False),
        F('artifact_id','ulid',False),
        F('related_exhibit_id','ulid',False),
        F('excluded_evidence_item_id','ulid',False),
        F('notes','text',False),
    ]),

    # --- Graph contracts / import / bloom ---
    E('GraphContract', 'JSON Schema contract for node/edge CSVs.', fields=common_fields('gc_') + [
        F('workspace_id','ulid',True),
        F('contract_name','text',True),
        F('version','text',False),
        F('schema_artifact_id','ulid',False),
        F('validator_command','text',False),
        F('notes','text',False),
    ]),
    E('NodeTable', 'Node CSV logical table (for Neo4j import).', fields=common_fields('nt_') + [
        F('workspace_id','ulid',True),
        F('contract_id','ulid',False),
        F('table_name','text',True),
        F('label','text',False),
        F('csv_artifact_id','ulid',False),
        F('primary_key_field','text',False),
        F('indexes_json','json',False),
        F('constraints_json','json',False),
    ]),
    E('EdgeTable', 'Edge CSV logical table (for Neo4j import).', fields=common_fields('et_') + [
        F('workspace_id','ulid',True),
        F('contract_id','ulid',False),
        F('table_name','text',True),
        F('type','text',False),
        F('csv_artifact_id','ulid',False),
        F('from_label','text',False),
        F('to_label','text',False),
        F('from_field','text',False),
        F('to_field','text',False),
        F('indexes_json','json',False),
    ]),
    E('Neo4jImportJob', 'Neo4j admin import job record.', fields=common_fields('nj_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('db_name','text',False),
        F('nodes_dir','text',False),
        F('rels_dir','text',False),
        F('command_line','text',False),
        F('status','enum',False,'PLANNED|RUNNING|DONE|FAIL'),
        F('logs_artifact_id','ulid',False),
    ]),
    E('BloomPerspective', 'Neo4j Bloom perspective pack metadata.', fields=common_fields('bp_') + [
        F('workspace_id','ulid',True),
        F('perspective_name','text',True),
        F('json_artifact_id','ulid',False),
        F('import_checklist_artifact_id','ulid',False),
        F('style_notes','text',False),
    ]),

    # --- Preservation / interoperability standards (BagIt, RO-Crate, OCFL, WARC, events/telemetry, supply-chain) ---
    E('BagItBag', 'BagIt package root metadata (bagit.txt, bag-info, tag files).', fields=common_fields('bb_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('bag_version','text',False),
        F('encoding','text',False),
        F('bag_dir','text',False),
        F('bagit_txt_artifact_id','ulid',False),
        F('bag_info_artifact_id','ulid',False),
    ]),
    E('BagItManifest', 'BagIt payload manifest lines (checksum -> relative path).', fields=common_fields('bm_') + [
        F('bag_id','ulid',True),
        F('algorithm','text',True),
        F('payload_path','text',True),
        F('checksum','text',True),
        F('bytes','bigint',False),
    ]),
    E('BagItTagManifest', 'BagIt tagmanifest lines (checksum -> tag file path).', fields=common_fields('btm_') + [
        F('bag_id','ulid',True),
        F('algorithm','text',True),
        F('tag_path','text',True),
        F('checksum','text',True),
        F('bytes','bigint',False),
    ]),

    E('ROCrateEntity', 'RO-Crate entity (JSON-LD node).', fields=common_fields('rce_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('crate_id','text',True),
        F('type','text',False),
        F('name','text',False),
        F('description','text',False),
        F('jsonld_fragment','json',False),
        F('artifact_id','ulid',False),
    ]),
    E('ROCrateContext', 'RO-Crate root context (ro-crate-metadata.json).', fields=common_fields('rcc_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('metadata_artifact_id','ulid',False),
        F('root_dataset_entity_id','ulid',False),
        F('profile','text',False),
    ]),

    E('OCFLObject', 'OCFL logical object.', fields=common_fields('oc_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('object_id','text',True),
        F('object_root','text',False),
        F('inventory_artifact_id','ulid',False),
        F('digest_algorithm','text',False),
    ]),
    E('OCFLInventory', 'OCFL inventory.json normalized view.', fields=common_fields('oci_') + [
        F('ocfl_object_id','ulid',True),
        F('head','text',False),
        F('type','text',False),
        F('digest_algorithm','text',False),
        F('manifest_json','json',False),
        F('versions_json','json',False),
        F('fixity_json','json',False),
    ]),

    E('WARCRecord', 'WARC record (capture unit) normalized header set.', fields=common_fields('wr_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('warc_file_artifact_id','ulid',False),
        F('warc_record_id','text',False),
        F('warc_type','text',False),
        F('warc_date','datetime_rfc3339',False),
        F('content_type','text',False),
        F('target_uri','text',False),
        F('payload_digest','text',False),
        F('block_digest','text',False),
        F('content_length','bigint',False),
        F('headers_json','json',False),
    ]),

    E('CloudEvent', 'CloudEvents 1.0 event (for stage + artifact lifecycle).', fields=common_fields('ce_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('id','text',True),
        F('source','text',True),
        F('specversion','text',True),
        F('type','text',True),
        F('subject','text',False),
        F('time','datetime_rfc3339',False),
        F('datacontenttype','text',False),
        F('dataschema','text',False),
        F('data','json',False),
        F('extensions_json','json',False),
    ]),

    E('OtelSpan', 'OpenTelemetry trace span (normalized).', fields=common_fields('os_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('trace_id','text',True),
        F('span_id','text',True),
        F('parent_span_id','text',False),
        F('name','text',False),
        F('kind','text',False),
        F('start_time','datetime_rfc3339',False),
        F('end_time','datetime_rfc3339',False),
        F('status_code','text',False),
        F('status_message','text',False),
        F('attributes_json','json',False),
        F('events_json','json',False),
    ]),
    E('OtelLogRecord', 'OpenTelemetry log record (normalized).', fields=common_fields('olr_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('timestamp','datetime_rfc3339',False),
        F('severity_text','text',False),
        F('body','text',False),
        F('attributes_json','json',False),
        F('trace_id','text',False),
        F('span_id','text',False),
    ]),
    E('OtelMetricPoint', 'OpenTelemetry metric point (normalized).', fields=common_fields('omp_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('metric_name','text',True),
        F('unit','text',False),
        F('type','text',False),
        F('value','float',False),
        F('attributes_json','json',False),
        F('timestamp','datetime_rfc3339',False),
    ]),

    E('OpenLineageRun', 'OpenLineage run entity.', fields=common_fields('olr2_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('namespace','text',False),
        F('name','text',False),
        F('run_uuid','text',False),
        F('event_time','datetime_rfc3339',False),
        F('inputs_json','json',False),
        F('outputs_json','json',False),
        F('facets_json','json',False),
    ]),

    E('DSSEEnvelope', 'DSSE envelope for signed attestations.', fields=common_fields('dsse_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('payload_type','text',False),
        F('payload_b64','text',False),
        F('signatures_json','json',False),
    ]),
    E('InTotoLink', 'in-toto link metadata (step material/products).', fields=common_fields('it_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('step_name','text',False),
        F('materials_json','json',False),
        F('products_json','json',False),
        F('byproducts_json','json',False),
        F('command_json','json',False),
        F('environment_json','json',False),
        F('signatures_json','json',False),
    ]),
    E('SLSAProvenance', 'SLSA provenance statement (normalized).', fields=common_fields('slsa_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('predicate_type','text',False),
        F('subject_json','json',False),
        F('builder_json','json',False),
        F('build_type','text',False),
        F('invocation_json','json',False),
        F('metadata_json','json',False),
        F('materials_json','json',False),
    ]),

    E('SBOMSPDXPackage', 'SPDX package node (SBOM).', fields=common_fields('spdxp_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('spdx_id','text',True),
        F('name','text',False),
        F('version_info','text',False),
        F('download_location','text',False),
        F('license_concluded','text',False),
        F('license_declared','text',False),
        F('checksums_json','json',False),
        F('external_refs_json','json',False),
    ]),
    E('SBOMCycloneDXComponent', 'CycloneDX component node (SBOM).', fields=common_fields('cdx_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('bom_ref','text',True),
        F('type','text',False),
        F('name','text',False),
        F('version','text',False),
        F('purl','text',False),
        F('cpe','text',False),
        F('hashes_json','json',False),
        F('licenses_json','json',False),
    ]),
    E('VEXStatement', 'Vulnerability Exploitability eXchange statement (generic).', fields=common_fields('vex_') + [
        F('workspace_id','ulid',True),
        F('bundle_id','ulid',False),
        F('vuln_id','text',True),
        F('product_id','text',False),
        F('status','text',False),
        F('justification','text',False),
        F('action_statement','text',False),
        F('impact_statement','text',False),
        F('timestamp','datetime_rfc3339',False),
    ]),

    # --- Retrieval / GraphRAG artifacts ---
    E('ContextPack', 'Packaged retrieval context for a drafting task.', fields=common_fields('cp_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('task_id','ulid',False),
        F('query','text',False),
        F('filters_json','json',False),
        F('retrieval_artifact_id','ulid',False),
        F('rerank_artifact_id','ulid',False),
        F('selected_evidence_atom_ids_json','json',False),
        F('selected_authority_pin_ids_json','json',False),
    ]),
    E('RetrievalEvent', 'Audit of a retrieval run (vector + graph + rerank).', fields=common_fields('re_') + [
        F('workspace_id','ulid',True),
        F('run_id','ulid',False),
        F('context_pack_id','ulid',False),
        F('query','text',False),
        F('results_artifact_id','ulid',False),
        F('metrics_json','json',False),
    ]),

    # --- Tasks / drafts / vehicles ---
    E('Task', 'A human-facing work item (draft motion, build pack, ingest authority).', fields=common_fields('task_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('task_type','enum',True),
        F('title','text',False),
        F('description','text',False),
        F('status','enum',False,'OPEN|IN_PROGRESS|DONE|BLOCKED'),
        F('priority','int',False),
        F('due_utc','datetime_rfc3339',False),
        F('assigned_person_id','ulid',False),
        F('context_pack_id','ulid',False),
    ]),
    E('Draft', 'A draft artifact with versioning (md/docx/pdf).', fields=common_fields('dr_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('task_id','ulid',False),
        F('document_id','ulid',False),
        F('draft_type','enum',False,'md|docx|pdf'),
        F('version','text',False),
        F('artifact_id','ulid',False),
        F('notes','text',False),
    ]),
    E('VehicleMap', 'Mapping of relief → form/vehicle → authority → proof obligations.', fields=common_fields('vm_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('vehicle_id','ulid',False),
        F('relief_sought','text',False),
        F('form_code','text',False),
        F('mcr_gate_json','json',False),
        F('elements_json','json',False),
        F('po_ids_json','json',False),
        F('service_plan_id','ulid',False),
        F('deadline_trigger_id','ulid',False),
    ]),
    E('ActionPlan', 'Selected actions post-gate (file/service/notice/appeal).', fields=common_fields('ap_') + [
        F('workspace_id','ulid',True),
        F('case_id','ulid',False),
        F('run_id','ulid',False),
        F('gate_result_id','ulid',False),
        F('actions_json','json',False),
        F('bundle_id','ulid',False),
        F('execution_notes','text',False),
    ]),
])

# ---------------------------
# Relationship link tables (M:N expansions)
# ---------------------------

link_pairs = [
    ('Case','Person','CasePersonLink','case_id','person_id','role','text','Role in case (plaintiff/defendant/judge/witness/etc).'),
    ('Case','Organization','CaseOrgLink','case_id','org_id','role','text','Role in case.'),
    ('EvidenceItem','Exhibit','EvidenceItemExhibitLink','evidence_item_id','exhibit_id','purpose','text','Why included in exhibit.'),
    ('EvidenceAtom','Statement','AtomStatementLink','atom_id','stmt_id','basis','text','Extraction rationale.'),
    ('Statement','Fact','StatementFactLink','stmt_id','fact_id','relation','enum','supports|contradicts|duplicates'),
    ('Fact','EvidenceAtom','FactAtomLink','fact_id','atom_id','weight','float','Support weight.'),
    ('Proposition','AuthorityPinpoint','PropositionPinLink','prop_id','pin_id','pin_role','enum','holding|rule|commentary'),
    ('Proposition','Fact','PropositionFactLink','prop_id','fact_id','fit','enum','element|context|harm'),
    ('Vehicle','Proposition','VehiclePropositionLink','vehicle_id','prop_id','use_type','enum','elements|standard|procedure'),
    ('ProofObligation','EvidenceAtom','POAtomLink','po_id','atom_id','satisfies','enum','direct|partial'),
    ('ProofObligation','AuthorityPinpoint','POPinLink','po_id','pin_id','satisfies','enum','required_basis'),
    ('GateResult','ProofObligation','GatePOLink','gate_id','po_id','status','enum','sat|unsat|waived'),
    ('Run','Artifact','RunArtifactLink','run_id','artifact_id','role','enum','input|output|report|checkpoint'),
]

for left, right, lname, lf, rf, extra_name, extra_typ, extra_note in link_pairs:
    add_entity(entities, E(
        name=lname,
        desc=f'Link table: {left} ↔ {right}.',
        fields=common_fields(lname.lower()+'_') + [
            F(lf,'ulid',True),
            F(rf,'ulid',True),
            F(extra_name, extra_typ, False, extra_note),
        ]
    ))

# Relational edges
rels.extend([
    Rel('Case','workspace_id','Workspace','workspace_id','CASE_IN_WORKSPACE','1:N','PROPOSED'),
    Rel('Court','workspace_id','Workspace','workspace_id','COURT_IN_WORKSPACE','1:N','PROPOSED'),
    Rel('Person','workspace_id','Workspace','workspace_id','PERSON_IN_WORKSPACE','1:N','PROPOSED'),
    Rel('Organization','workspace_id','Workspace','workspace_id','ORG_IN_WORKSPACE','1:N','PROPOSED'),
    Rel('Address','workspace_id','Workspace','workspace_id','ADDR_IN_WORKSPACE','1:N','PROPOSED'),
    Rel('Case','court_id','Court','court_id','CASE_IN_COURT','N:1','PROPOSED'),
    Rel('DocketEntry','case_id','Case','case_id','DOCKET_OF_CASE','N:1','PROPOSED'),
    Rel('Document','case_id','Case','case_id','DOC_OF_CASE','N:1','PROPOSED'),
    Rel('Filing','case_id','Case','case_id','FILING_OF_CASE','N:1','PROPOSED'),
    Rel('Filing','document_id','Document','doc_id','FILING_DOC','N:1','PROPOSED'),
    Rel('Order','case_id','Case','case_id','ORDER_OF_CASE','N:1','PROPOSED'),
    Rel('Order','document_id','Document','doc_id','ORDER_DOC','1:1','PROPOSED'),
    Rel('Hearing','case_id','Case','case_id','HEARING_OF_CASE','N:1','PROPOSED'),
    Rel('Transcript','hearing_id','Hearing','hearing_id','TRANSCRIPT_OF_HEARING','1:1','PROPOSED'),
    Rel('EvidenceItem','original_artifact_id','Artifact','art_id','EVIDENCE_ORIGINAL_ARTIFACT','N:1','PROPOSED'),
    Rel('EvidenceAtom','evidence_item_id','EvidenceItem','ev_id','ATOM_OF_EVIDENCE','N:1','PROPOSED'),
    Rel('AuthorityPinpoint','authority_source_id','AuthoritySource','authsrc_id','PINPOINT_IN_SOURCE','N:1','PROPOSED'),
    Rel('Proposition','authority_snapshot_id','AuthoritySnapshot','snap_id','PROP_IN_SNAPSHOT','N:1','PROPOSED'),
    Rel('ProofObligation','vehicle_id','Vehicle','veh_id','PO_OF_VEHICLE','N:1','PROPOSED'),
    Rel('Run','workspace_id','Workspace','workspace_id','RUN_IN_WORKSPACE','N:1','PROPOSED'),
    Rel('Artifact','workspace_id','Workspace','workspace_id','ARTIFACT_IN_WORKSPACE','N:1','PROPOSED'),
    Rel('Artifact','derived_from_artifact_id','Artifact','art_id','DERIVED_FROM','N:1','PROPOSED'),
    Rel('DerivationActivity','run_id','Run','run_id','ACTIVITY_IN_RUN','N:1','PROPOSED'),
])

# Link relationships for link tables
# (Only the structural ones; extra fields described in table cards.)
for left, right, lname, lf, rf, *_ in link_pairs:
    rels.append(Rel(lname, lf, left, f"{left.lower()}_id" if left not in ('Document','Person','Case','Court','Workspace','Run','Artifact','Vehicle','EvidenceItem','EvidenceAtom','Statement','Fact','Proposition','AuthorityPinpoint','ProofObligation','GateResult','Organization','Exhibit') else {
        'Document':'doc_id','Person':'person_id','Case':'case_id','Court':'court_id','Workspace':'workspace_id','Run':'run_id','Artifact':'art_id','Vehicle':'veh_id','EvidenceItem':'ev_id','EvidenceAtom':'atom_id','Statement':'stmt_id','Fact':'fact_id','Proposition':'prop_id','AuthorityPinpoint':'pin_id','ProofObligation':'po_id','GateResult':'gate_id','Organization':'org_id','Exhibit':'exhibit_id'}[left],
        f"{lname.upper()}_{left.upper()}", 'N:1','PROPOSED'))
    rels.append(Rel(lname, rf, right, f"{right.lower()}_id" if right not in ('Document','Person','Case','Court','Workspace','Run','Artifact','Vehicle','EvidenceItem','EvidenceAtom','Statement','Fact','Proposition','AuthorityPinpoint','ProofObligation','GateResult','Organization','Exhibit') else {
        'Document':'doc_id','Person':'person_id','Case':'case_id','Court':'court_id','Workspace':'workspace_id','Run':'run_id','Artifact':'art_id','Vehicle':'veh_id','EvidenceItem':'ev_id','EvidenceAtom':'atom_id','Statement':'stmt_id','Fact':'fact_id','Proposition':'prop_id','AuthorityPinpoint':'pin_id','ProofObligation':'po_id','GateResult':'gate_id','Organization':'org_id','Exhibit':'exhibit_id'}[right],
        f"{lname.upper()}_{right.upper()}", 'N:1','PROPOSED'))

# ---------------------------
# Ingest extracted artifacts (table-like) as EXTRACTED_* entities
# ---------------------------
extracted_entities: Dict[str, List[Tuple[str,str,str]]] = {}
if EXTRACTED_CSV.exists():
    with EXTRACTED_CSV.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            ent = row['entity']
            extracted_entities.setdefault(ent, []).append((row['field'], row.get('type',''), row.get('source','')))

for ent, fields in extracted_entities.items():
    # sanitize into a unique-ish name
    name = 'EXTRACTED_' + ent.replace('/', '_').replace('.', '_').replace('-', '_')
    ef = []
    for fname, ftype, src in fields:
        if not fname:
            continue
        ef.append(F(fname, ftype or 'text', False, f"From: {src}"))
    add_entity(entities, E(
        name=name,
        desc=f'Extracted table-like structure from artifacts: {ent}',
        origin='EXTRACTED',
        fields=ef
    ))

# ---------------------------
# Relationship inference (MAX) — generate FK relationships from *_id patterns.
# This is intentionally aggressive to maximize relationship coverage across the superset.
# ---------------------------

_abbr = {
    'org': 'Organization',
    'doc': 'Document',
    'docs': 'Document',
    'auth': 'AuthoritySource',
    'authsrc': 'AuthoritySource',
    'snap': 'AuthoritySnapshot',
    'pin': 'AuthorityPinpoint',
    'prop': 'Proposition',
    'po': 'ProofObligation',
    'ev': 'EvidenceItem',
    'atom': 'EvidenceAtom',
    'stmt': 'Statement',
    'fact': 'Fact',
    'veh': 'Vehicle',
    'svc': 'ServicePlan',
    'svca': 'ServiceAttempt',
    'svcp': 'ServiceProof',
    'trq': 'TranscriptRequest',
    'trs': 'TranscriptSegment',
    'oop': 'OfferOfProof',
    'obj': 'ObjectionEvent',
    'appeal': 'Appeal',
    'coa': 'Appeal',
    'msc': 'Appeal',
    'jtc': 'JTCComplaint',
    'mifile': 'FilingReceipt',
    'bundle': 'Bundle',
    'be': 'BundleEntry',
    'ic': 'IntegrityCheck',
    'sig': 'Signature',
}

def _titlecase(s: str) -> str:
    return ''.join(part[:1].upper()+part[1:] for part in s.split('_') if part)

_names = {e.name for e in entities.values()}
_names_lower = {e.lower(): e for e in _names}

def _resolve_target(base: str) -> Optional[str]:
    if not base:
        return None
    b = base.lower()
    # strong heuristics by contained tokens
    if 'artifact' in b:
        return 'Artifact' if 'Artifact' in _names else None
    if 'workspace' in b:
        return 'Workspace' if 'Workspace' in _names else None
    if 'case' in b:
        return 'Case' if 'Case' in _names else None
    if 'court' in b:
        return 'Court' if 'Court' in _names else None
    if 'person' in b:
        return 'Person' if 'Person' in _names else None
    if 'org' == b or b.endswith('_org') or b.endswith('org'):
        return 'Organization' if 'Organization' in _names else None
    if b in _abbr:
        t = _abbr[b]
        return t if t in _names else None
    # direct lower match
    if b in _names_lower:
        return _names_lower[b]
    # titlecase match
    tc = _titlecase(b)
    if tc in _names:
        return tc
    # extracted entities: allow matching against EXTRACTED_<base>
    ex = 'EXTRACTED_' + base.replace('/', '_').replace('.', '_').replace('-', '_')
    if ex in _names:
        return ex
    ex2 = 'EXTRACTED_' + tc
    if ex2 in _names:
        return ex2
    return None

_seen_rel = set((r.frm, r.frm_field, r.to, r.to_field, r.rel_name) for r in rels)

for e in list(entities.values()):
    for fld in e.fields:
        fn = fld.name
        if not fn or not fn.endswith('_id'):
            continue
        if fn == e.pk:
            continue
        base = fn[:-3]
        target = _resolve_target(base)
        if not target or target not in entities:
            continue
        to_field = entities[target].pk
        rel_name = f"FK_{e.name}_{fn}_TO_{target}"
        key = (e.name, fn, target, to_field, rel_name)
        if key in _seen_rel:
            continue
        rels.append(Rel(e.name, fn, target, to_field, rel_name, 'N:1', 'INFERRED', 'Inferred from *_id naming.'))
        _seen_rel.add(key)
        # also add explicit reverse edge for traversal convenience
        rev_name = f"HAS_{e.name}_BY_{fn}"
        rev_key = (target, to_field, e.name, fn, rev_name)
        if rev_key not in _seen_rel:
            rels.append(Rel(target, to_field, e.name, fn, rev_name, '1:N', 'INFERRED', f'Reverse of {rel_name}.'))
            _seen_rel.add(rev_key)

# If a table has >=2 *_id fields, treat it as an association table and emit all pairwise links (max).
for e in list(entities.values()):
    id_fields = [fld.name for fld in e.fields if fld.name and fld.name.endswith('_id') and fld.name != e.pk]
    if len(id_fields) < 2:
        continue
    targets = []
    for fn in id_fields:
        t = _resolve_target(fn[:-3])
        if t and t in entities:
            targets.append((fn, t))
    if len(targets) < 2:
        continue
    # association edges already created above; add explicit association semantics for every pair
    for i in range(len(targets)):
        for j in range(i+1, len(targets)):
            fn1, t1 = targets[i]
            fn2, t2 = targets[j]
            rel_name = f"ASSOC_{e.name}_{t1}_{t2}"
            key = (t1, entities[t1].pk, t2, entities[t2].pk, rel_name)
            if key in _seen_rel:
                continue
            rels.append(Rel(t1, entities[t1].pk, t2, entities[t2].pk, rel_name, 'M:N', 'INFERRED', f'Association via {e.name} ({fn1},{fn2}).'))
            _seen_rel.add(key)


# ---------------------------
# Write outputs
# ---------------------------

# Field catalog CSV
field_csv = OUTROOT / 'model' / 'field_catalog_superset.csv'
with field_csv.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['entity','field','type','required','origin','notes'])
    for e in sorted(entities.values(), key=lambda x: x.name):
        for fld in e.fields:
            w.writerow([e.name, fld.name, fld.typ, 'Y' if fld.req else 'N', e.origin, fld.notes])

# Relationships CSV
rel_csv = OUTROOT / 'model' / 'relationship_catalog_superset.csv'
with rel_csv.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['from_entity','from_field','to_entity','to_field','rel_name','cardinality','origin','notes'])
    for r in rels:
        w.writerow([r.frm, r.frm_field, r.to, r.to_field, r.rel_name, r.card, r.origin, r.notes])

# Dense markdown dictionary
md = OUTROOT / 'docs' / 'ERD_SUPERSET_FIELD_DICTIONARY_v2026-01-19.2.md'
with md.open('w', encoding='utf-8') as f:
    f.write('# LitigationOS — ERD Superset Field Dictionary (v2026-01-19.2)\n\n')
    f.write('This file is **append-only** and contains two populations:\n\n')
    f.write('- **PROPOSED**: canonical normalized ERD superset (intended target model).\n')
    f.write('- **EXTRACTED**: table-like structures discovered in your uploaded artifacts (CSV headers / JSON schemas).\n\n')
    f.write('## Entity Index\n\n')
    for e in sorted(entities.values(), key=lambda x: x.name):
        f.write(f"- [{e.name}](#{e.name.lower()}) — {e.origin}\n")
    f.write('\n---\n\n')
    for e in sorted(entities.values(), key=lambda x: x.name):
        f.write(f"## {e.name}\n\n")
        f.write(f"**Origin:** {e.origin}  \n")
        f.write(f"**Description:** {e.desc}  \n")
        f.write(f"**Primary Key:** {e.pk}  \n\n")
        f.write('| Field | Type | Req | Notes |\n|---|---|---:|---|\n')
        for fld in e.fields:
            # NOTE: avoid backslashes inside f-string expression parts (Python syntax restriction).
            _req = 'Y' if fld.req else 'N'
            _notes = (fld.notes or '').replace('|', r'\\|')
            f.write(f"| {fld.name} | {fld.typ} | {_req} | {_notes} |\n")
        f.write('\n')

# Diagram DOT (overview)
# Keep it readable: show only entity name + PK, but preserve relationships.

dot = OUTROOT / 'diagrams' / 'erd_superset_overview.dot'
with dot.open('w', encoding='utf-8') as f:
    f.write('digraph ERD {\n')
    f.write('  graph [rankdir=LR, splines=true, overlap=false, fontname="Helvetica"];\n')
    f.write('  node [shape=record, fontsize=10, fontname="Helvetica"];\n')
    f.write('  edge [fontsize=8, fontname="Helvetica"];\n\n')
    # Only include PROPOSED canonical nodes in overview (omit extracted noise)
    for e in sorted([e for e in entities.values() if e.origin=='PROPOSED'], key=lambda x: x.name):
        f.write(f'  "{e.name}" [label="{{{e.name}|PK: {e.pk}}}"];\n')
    f.write('\n')
    for r in rels:
        if r.frm not in entities or r.to not in entities:
            continue
        if entities[r.frm].origin != 'PROPOSED' or entities[r.to].origin != 'PROPOSED':
            continue
        f.write(f'  "{r.frm}" -> "{r.to}" [label="{r.rel_name} ({r.card})"];\n')
    f.write('}\n')

# Diagram DOT (dense cards) — clustered, with full field lists.
def _dot_esc(s: str) -> str:
    return (s or '').replace('\\', r'\\\\').replace('{', r'\\{').replace('}', r'\\}').replace('|', r'\\|').replace('"', r'\\"')

def _cluster_for(name: str) -> str:
    n = name.lower()
    if n.startswith('authority') or n in {'proposition','caselaw','holding','benchbooktopic','formtemplate','formfieldmapping','vehiclerule','vehicle','vehiclepropositionlink','authorityxref'}:
        return 'Authority'
    if n.startswith('evidence') or n in {'exhibit','evidenceitem','evidenceatom','statement','fact','contradiction','evidencefoundationcheck','piiitem','redactionaction','quoteanchor','quotesegment'}:
        return 'Evidence'
    if n in {'case','court','docketentry','filing','order','hearing','transcript','transcriptrequest','transcriptsegment','offerofproof','objectionevent','appeal','jtccomplaint','filingreceipt','deadlineevent','deadlinetrigger','judgeassignment','party','partyrolelink'}:
        return 'Procedure'
    if n.startswith('service') or n in {'serviceplan','serviceattempt','serviceproof'}:
        return 'Service'
    if n in {'run','agent','runstep','runevent','runmetric','schedule','task','taskstep','actionplan'}:
        return 'Automation'
    if n in {'bundle','bundleentry','integritycheck','signature','manifest','manifestentry','sbomspdxpackage','sbomcyclonedxcomponent','ocflobject','ocflinventory','bagitbag','bagitmanifest','warcrecord','rocrateentity','rocratecontext'}:
        return 'Packaging'
    if n.startswith('prov') or n.startswith('provenance') or 'otel' in n or 'openlineage' in n or 'cloudevent' in n or 'slsa' in n or 'intoto' in n or 'spdx' in n or 'cyclonedx' in n or 'rocrate' in n or 'ocfl' in n or 'warc' in n or 'bagit' in n:
        return 'Interop'
    return 'Other'

clusters: Dict[str, List[E]] = {}
for e in entities.values():
    if e.origin != 'PROPOSED':
        continue
    clusters.setdefault(_cluster_for(e.name), []).append(e)

for cname, ents in sorted(clusters.items(), key=lambda kv: kv[0]):
    outdot = OUTROOT / 'diagrams' / f'erd_superset_cards_{cname.lower()}.dot'
    with outdot.open('w', encoding='utf-8') as f:
        f.write('digraph ERD_CARDS {\n')
        f.write('  graph [rankdir=LR, splines=true, overlap=false, fontname="Helvetica", fontsize=10];\n')
        f.write('  node [shape=record, fontsize=8, fontname="Helvetica"];\n')
        f.write('  edge [fontsize=7, fontname="Helvetica"];\n\n')
        f.write(f'  subgraph "cluster_{cname}" {{\n')
        f.write(f'    label="{cname}";\n')
        for e in sorted(ents, key=lambda x: x.name):
            lines = [f"PK: {e.pk}\\l"]
            for fld in e.fields:
                lines.append(f"{_dot_esc(fld.name)}: {_dot_esc(fld.typ)}\\l")
            label = '{' + _dot_esc(e.name) + '|' + ''.join(lines) + '}'
            f.write(f'    "{e.name}" [label="{label}"];\n')
        f.write('  }\n\n')
        # edges within cluster only
        ent_set = {e.name for e in ents}
        for r in rels:
            if r.frm in ent_set and r.to in ent_set:
                f.write(f'  "{r.frm}" -> "{r.to}" [label="{_dot_esc(r.rel_name)} ({_dot_esc(r.card)})"];\n')
        f.write('}\n')

print('WROTE:', OUTROOT)
print('Entities:', len(entities), 'Relationships:', len(rels))
print('Field rows:', sum(len(e.fields) for e in entities.values()))
