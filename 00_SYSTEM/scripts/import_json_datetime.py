import json, datetime
from pathlib import Path

try:
    from graphviz import Digraph  # type: ignore
    graphviz_ok = True
except Exception:
    graphviz_ok = False

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
root = Path("/mnt/data") / f"{ts}_EVENT_HORIZON_DFA_AND_AUTHORITY_VERIFIER_PACKS"
pack1 = root / "Michigan_Vehicle_DFA_Pack"
pack2 = root / "Authority_Snapshot_Verifier_Pack"

for p in [pack1, pack2]:
    (p / "schemas").mkdir(parents=True, exist_ok=True)
    (p / "examples").mkdir(parents=True, exist_ok=True)
    (p / "diagrams").mkdir(parents=True, exist_ok=True)
    (p / "docs").mkdir(parents=True, exist_ok=True)

(pack2 / "scripts").mkdir(parents=True, exist_ok=True)
(pack2 / "rules").mkdir(parents=True, exist_ok=True)

# ---------------------------
# Pack 1: Michigan Vehicle DFA Pack
# ---------------------------
from typing import Any, Dict

dfa_schemas: Dict[str, Any] = {
    "DFAState.schema.json": {
        "$schema":"https://json-schema.org/draft/2020-12/schema",
        "$id":"litigationos://schemas/DFAState",
        "title":"DFAState",
        "type":"object",
        "required":["state_id","label","category"],
        "properties":{
            "state_id":{"type":"string","pattern":"^[A-Z0-9_]+$"},
            "label":{"type":"string"},
            "category":{"type":"string","enum":["POSTURE","GATE","READY","FILED","HEARING","ORDER","APPEAL","OVERSIGHT","FAILSOFT","TERMINAL"]},
            "lane_scope":{"type":["string","null"],"enum":["MEEK2","MEEK3","MEEK4",None]},
            "description":{"type":["string","null"]},
            "entry_actions":{"type":"array","items":{"type":"string"}},
            "exit_actions":{"type":"array","items":{"type":"string"}}
        },
        "additionalProperties": False
    },
    "DFATransition.schema.json": {
        "$schema":"https://json-schema.org/draft/2020-12/schema",
        "$id":"litigationos://schemas/DFATransition",
        "title":"DFATransition",
        "type":"object",
        "required":["transition_id","from_state","to_state","trigger_filing_or_event"],
        "properties":{
            "transition_id":{"type":"string","pattern":"^[A-Z0-9_]+$"},
            "from_state":{"type":"string"},
            "to_state":{"type":"string"},
            "trigger_filing_or_event":{"type":"string"},
            "authority_candidates":{"type":"array","items":{"type":"string"}},
            "preconditions":{"type":"array","items":{"type":"string"}},
            "deadline_clock_ids":{"type":"array","items":{"type":"string"}},
            "service_gate_ids":{"type":"array","items":{"type":"string"}},
            "proof_obligations":{"type":"array","items":{"type":"string"}},
            "fail_soft_on_missing":{"type":"boolean"},
            "acquisition_tasks":{"type":"array","items":{"type":"string"}}
        },
        "additionalProperties": False
    },
    "DeadlineClock.schema.json": {
        "$schema":"https://json-schema.org/draft/2020-12/schema",
        "$id":"litigationos://schemas/DeadlineClock",
        "title":"DeadlineClock",
        "type":"object",
        "required":["clock_id","label","start_trigger","time_basis","status"],
        "properties":{
            "clock_id":{"type":"string","pattern":"^[A-Z0-9_]+$"},
            "label":{"type":"string"},
            "start_trigger":{"type":"string"},
            "time_basis":{"type":"string","enum":["ENTRY_DATE","SERVICE_DATE","HEARING_DATE","SIGNED_DATE","STATUTE_EVENT","UNKNOWN_PENDING_PIN"]},
            "duration_expression":{"type":"string"},
            "authority_candidates":{"type":"array","items":{"type":"string"}},
            "status":{"type":"string","enum":["ACTIVE","SATISFIED","MISSED","UNKNOWN_PENDING_PIN"]},
            "notes":{"type":["string","null"]}
        },
        "additionalProperties": False
    },
    "ServiceGate.schema.json": {
        "$schema":"https://json-schema.org/draft/2020-12/schema",
        "$id":"litigationos://schemas/ServiceGate",
        "title":"ServiceGate",
        "type":"object",
        "required":["service_gate_id","label","required_before","status"],
        "properties":{
            "service_gate_id":{"type":"string","pattern":"^[A-Z0-9_]+$"},
            "label":{"type":"string"},
            "required_before":{"type":"string"},
            "methods_allowed":{"type":"array","items":{"type":"string"}},
            "proof_required":{"type":"array","items":{"type":"string"}},
            "status":{"type":"string","enum":["PASS","FAIL_SOFT","FAIL_HARD","UNKNOWN"]},
            "authority_candidates":{"type":"array","items":{"type":"string"}}
        },
        "additionalProperties": False
    },
    "EscalationRoute.schema.json": {
        "$schema":"https://json-schema.org/draft/2020-12/schema",
        "$id":"litigationos://schemas/EscalationRoute",
        "title":"EscalationRoute",
        "type":"object",
        "required":["route_id","route_type","from_court","to_court","trigger_state"],
        "properties":{
            "route_id":{"type":"string","pattern":"^[A-Z0-9_]+$"},
            "route_type":{"type":"string","enum":["TRIAL_TO_COA","COA_TO_MSC","TRIAL_TO_JTC","TRIAL_TO_INTERNAL_OVERSIGHT"]},
            "from_court":{"type":"string"},
            "to_court":{"type":"string"},
            "trigger_state":{"type":"string"},
            "vehicle_candidates":{"type":"array","items":{"type":"string"}},
            "authority_candidates":{"type":"array","items":{"type":"string"}},
            "prerequisites":{"type":"array","items":{"type":"string"}},
            "deadline_clock_ids":{"type":"array","items":{"type":"string"}},
            "service_gate_ids":{"type":"array","items":{"type":"string"}}
        },
        "additionalProperties": False
    },
    "VehicleDFA.schema.json": {
        "$schema":"https://json-schema.org/draft/2020-12/schema",
        "$id":"litigationos://schemas/VehicleDFA",
        "title":"VehicleDFA",
        "type":"object",
        "required":["dfa_id","lane","version","states","transitions","deadline_clocks","service_gates","escalation_routes"],
        "properties":{
            "dfa_id":{"type":"string"},
            "lane":{"type":"string","enum":["MEEK2","MEEK3","MEEK4"]},
            "version":{"type":"string"},
            "core_invariants":{"type":"array","items":{"type":"string"}},
            "states":{"type":"array","items":{"$ref":"litigationos://schemas/DFAState"}},
            "transitions":{"type":"array","items":{"$ref":"litigationos://schemas/DFATransition"}},
            "deadline_clocks":{"type":"array","items":{"$ref":"litigationos://schemas/DeadlineClock"}},
            "service_gates":{"type":"array","items":{"$ref":"litigationos://schemas/ServiceGate"}},
            "escalation_routes":{"type":"array","items":{"$ref":"litigationos://schemas/EscalationRoute"}}
        },
        "additionalProperties": False
    }
}
for name, schema in dfa_schemas.items():
    (pack1 / "schemas" / name).write_text(json.dumps(schema, indent=2), encoding="utf-8")

def build_lane_dfa(lane: str):
    # Shared skeleton but lane-specific triggers/routes/authority candidates
    if lane == "MEEK2":
        lane_label = "Custody/PT/Support/FOC"
        triggers = {
            "init":"Parenting-time/custody issue identified",
            "trial_vehicle":"Motion regarding custody/parenting time/support/FOC enforcement",
            "appeal_trigger":"Final/order affecting custody or PT posture entered",
            "oversight_trigger":"Bias/disqual issue embedded in family proceeding"
        }
        auth = {
            "lane":["MCL 722.* (candidate)","MCR 3.201..3.219 (candidate)","MCR 2.119 (candidate)"],
            "appeal":["MCR 7.203 (candidate)","MCR 7.205 (candidate)","MCR 7.211/7.212 (candidate)","MCR 7.305 (candidate)"],
            "oversight":["MCR 2.003 (candidate)","MCJC Canons (candidate)","MCR 9.200 et seq (candidate)"]
        }
    elif lane == "MEEK3":
        lane_label = "PPO/Contempt/Enforcement"
        triggers = {
            "init":"PPO/contempt/enforcement issue identified",
            "trial_vehicle":"PPO modify/terminate/respond or contempt/show-cause related filing",
            "appeal_trigger":"PPO/contempt order entered",
            "oversight_trigger":"Bias/disqual issue embedded in PPO/contempt proceeding"
        }
        auth = {
            "lane":["MCL 600.2950 / 600.2950a (candidate)","MCR 3.705..3.708 (candidate)","MCR 2.119 (candidate)"],
            "appeal":["MCR 7.203 (candidate)","MCR 7.205 (candidate)","MCR 7.211/7.212 (candidate)","MCR 7.305 (candidate)"],
            "oversight":["MCR 2.003 (candidate)","MCJC Canons (candidate)","MCR 9.200 et seq (candidate)"]
        }
    else:
        lane_label = "Bias/Disqual/JTC"
        triggers = {
            "init":"Judicial bias/disqualification oversight issue identified",
            "trial_vehicle":"Motion to disqualify or record-preservation filing",
            "appeal_trigger":"Disqualification ruling/order or underlying order impacting neutrality claim entered",
            "oversight_trigger":"JTC complaint readiness threshold reached"
        }
        auth = {
            "lane":["MCR 2.003 (candidate)","MCJC Canons (candidate)","MCR 2.119 (candidate)"],
            "appeal":["MCR 7.203/7.205 (candidate)","MCR 7.211/7.212 (candidate)","MCR 7.305 (candidate)"],
            "oversight":["MCR 9.200 et seq (candidate)","MCJC Canons (candidate)"]
        }

    states: list[dict[str, Any]] = [  # type: ignore
        {"state_id":"ISSUE_INTAKE","label":"Issue Intake", "category":"POSTURE","lane_scope":lane,
         "description":f"{lane_label} issue detected and classified", "entry_actions":["Create CASE_STATE delta"],"exit_actions":[]},
        {"state_id":"ORDER_PIN_REQUIRED","label":"OperatingOrderPin Required","category":"GATE","lane_scope":lane,
         "description":"No vehicle valid until controlling order pin is identified", "entry_actions":["Create acquisition task if missing order pin"],"exit_actions":[]},
        {"state_id":"ORDER_PINNED","label":"Order Pinned","category":"READY","lane_scope":lane,
         "description":"Controlling order identified with entry/service/status/supersession", "entry_actions":["Initialize deadline clocks"],"exit_actions":[]},
        {"state_id":"VEHICLE_CANDIDATES","label":"Vehicle Candidates","category":"POSTURE","lane_scope":lane,
         "description":"Enumerate lane-appropriate candidate vehicles", "entry_actions":["Build VehicleMap candidates"],"exit_actions":[]},
        {"state_id":"SERVICE_GATES_PENDING","label":"Service Gates Pending","category":"GATE","lane_scope":lane,
         "description":"Service method/proof gates evaluated", "entry_actions":["Assess service proofs"],"exit_actions":[]},
        {"state_id":"TRIAL_ROUTE_READY","label":"Trial Route Ready","category":"READY","lane_scope":lane,
         "description":"Trial-level filing packet can be assembled", "entry_actions":["Assemble exhibits + authority triples"],"exit_actions":[]},
        {"state_id":"TRIAL_FILED","label":"Trial Filing Submitted","category":"FILED","lane_scope":lane,
         "description":"Trial vehicle filed in trial court", "entry_actions":["Log file-stamp"],"exit_actions":[]},
        {"state_id":"HEARING_OR_RESPONSE_PENDING","label":"Hearing/Response Pending","category":"HEARING","lane_scope":lane,
         "description":"Await hearing, response, or scheduling event", "entry_actions":["Track hearing dates"],"exit_actions":[]},
        {"state_id":"ORDER_ENTERED","label":"Order Entered","category":"ORDER","lane_scope":lane,
         "description":"Post-filing order entered; may trigger escalation clocks", "entry_actions":["Re-pin OperatingOrderPin"],"exit_actions":[]},
        {"state_id":"APPEAL_EVAL","label":"Appeal Evaluation","category":"APPEAL","lane_scope":lane,
         "description":"Evaluate COA/MSC route and prerequisites", "entry_actions":["Compute appellate route candidates"],"exit_actions":[]},
        {"state_id":"COA_ROUTE_READY","label":"COA Route Ready","category":"APPEAL","lane_scope":lane,
         "description":"COA filing route ready (claim/leave/original action as applicable)", "entry_actions":["Build COA packet"],"exit_actions":[]},
        {"state_id":"MSC_ROUTE_READY","label":"MSC Route Ready","category":"APPEAL","lane_scope":lane,
         "description":"MSC route ready (application or further review path)", "entry_actions":["Build MSC signal packet"],"exit_actions":[]},
        {"state_id":"JTC_ROUTE_READY","label":"JTC Route Ready","category":"OVERSIGHT","lane_scope":lane,
         "description":"JTC complaint packet can be assembled where applicable", "entry_actions":["Build JTC packet"],"exit_actions":[]},
        {"state_id":"FAILSOFT_GAPLOG","label":"Fail-Soft Gap Log","category":"FAILSOFT","lane_scope":lane,
         "description":"Missing record/service/authority converted to acquisition tasks", "entry_actions":["Emit acquisition tasks"],"exit_actions":[]}
    ]

    deadline_clocks: list[dict[str, Any]] = [  # type: ignore
        {"clock_id":"CLK_TRIAL_RESPONSE","label":"Trial response/hearing clock","start_trigger":"TRIAL_FILED","time_basis":"ENTRY_DATE",
         "duration_expression":"Rule-dependent; compute from selected vehicle (candidate)", "authority_candidates":auth["lane"], "status":"UNKNOWN_PENDING_PIN", "notes":"Exact clock depends on selected vehicle and served entry date"},
        {"clock_id":"CLK_APPEAL_WINDOW","label":"Appellate window clock","start_trigger":"ORDER_ENTERED","time_basis":"ENTRY_DATE",
         "duration_expression":"MCR 7.* route-specific window (candidate verification required)", "authority_candidates":auth["appeal"], "status":"UNKNOWN_PENDING_PIN", "notes":"Use verified route-specific clock after authority verification"},
        {"clock_id":"CLK_SERVICE_PROOF","label":"Service proof filing clock","start_trigger":"TRIAL_FILED","time_basis":"SERVICE_DATE",
         "duration_expression":"Immediate/vehicle-dependent", "authority_candidates":["MCR 2.107 / MCR 2.105 (candidate)"], "status":"UNKNOWN_PENDING_PIN", "notes":"Track proof timing and defects"}
    ]

    service_gates = [
        {"service_gate_id":"SG_TRIAL_FILE","label":"Service required for trial filing", "required_before":"TRIAL_ROUTE_READY",
         "methods_allowed":["MiFILE e-service (where active)","mail","personal service","as-rule-permitted method"],
         "proof_required":["Proof of Service form/statement","Service metadata"],
         "status":"UNKNOWN","authority_candidates":["MCR 2.105 (candidate)","MCR 2.107 (candidate)"]},
        {"service_gate_id":"SG_APPEAL_PACKET","label":"Service required for appellate/oversight packet", "required_before":"COA_ROUTE_READY",
         "methods_allowed":["Rule-authorized appellate service"], "proof_required":["Proof of service"],
         "status":"UNKNOWN","authority_candidates":auth["appeal"] + ["MCR 2.107 (candidate)"]}
    ]

    escalations = [
        {"route_id":"RT_TRIAL_TO_COA","route_type":"TRIAL_TO_COA","from_court":"Trial Court","to_court":"Michigan Court of Appeals",
         "trigger_state":"ORDER_ENTERED","vehicle_candidates":["Claim of Appeal (if applicable)","Application for Leave","Original Action / Superintending (candidate)"],
         "authority_candidates":auth["appeal"], "prerequisites":["OperatingOrderPin current","Deadline clock computed","Service gates satisfied or gap-logged","Record spine mapped"],
         "deadline_clock_ids":["CLK_APPEAL_WINDOW"], "service_gate_ids":["SG_APPEAL_PACKET"]},
        {"route_id":"RT_COA_TO_MSC","route_type":"COA_TO_MSC","from_court":"Michigan Court of Appeals","to_court":"Michigan Supreme Court",
         "trigger_state":"COA_ROUTE_READY","vehicle_candidates":["Application for Leave to Appeal","Emergency/special relief (candidate)"],
         "authority_candidates":["MCR 7.305 (candidate)","MCR 7.311 (candidate)"], "prerequisites":["COA posture identified","COA order/opinion pinned","Deadline clock computed"],
         "deadline_clock_ids":["CLK_APPEAL_WINDOW"], "service_gate_ids":["SG_APPEAL_PACKET"]},
        {"route_id":"RT_TRIAL_TO_JTC","route_type":"TRIAL_TO_JTC","from_court":"Trial Court","to_court":"Judicial Tenure Commission",
         "trigger_state":"APPEAL_EVAL","vehicle_candidates":["JTC Complaint Packet"], "authority_candidates":auth["oversight"],
         "prerequisites":["Bias/conduct allegations tied to record pointers","No invented facts","Chronology + exhibits mapped"],
         "deadline_clock_ids":[], "service_gate_ids":[]}
    ]

    transitions = [
        {"transition_id":"T_ISSUE_TO_ORDERPIN","from_state":"ISSUE_INTAKE","to_state":"ORDER_PIN_REQUIRED","trigger_filing_or_event":triggers["init"],
         "authority_candidates":auth["lane"], "preconditions":["Lane classified"], "deadline_clock_ids":[], "service_gate_ids":[],
         "proof_obligations":["Issue statement"], "fail_soft_on_missing":True,
         "acquisition_tasks":["Identify controlling order, docket entry, or hearing event"]},
        {"transition_id":"T_ORDERPIN_REQUIRED_TO_PINNED","from_state":"ORDER_PIN_REQUIRED","to_state":"ORDER_PINNED","trigger_filing_or_event":"OperatingOrderPin created",
         "authority_candidates":["OperatingOrderPin doctrine"], "preconditions":["Order pin has entry/service/status fields"], "deadline_clock_ids":["CLK_TRIAL_RESPONSE","CLK_APPEAL_WINDOW"], "service_gate_ids":[],
         "proof_obligations":["ROA/order pointer"], "fail_soft_on_missing":False, "acquisition_tasks":[]},
        {"transition_id":"T_ORDERPIN_REQUIRED_TO_FAILSOFT","from_state":"ORDER_PIN_REQUIRED","to_state":"FAILSOFT_GAPLOG","trigger_filing_or_event":"Order pin missing or nonservice ambiguity",
         "authority_candidates":["TruthLock / Fail-soft"], "preconditions":[], "deadline_clock_ids":[], "service_gate_ids":[],
         "proof_obligations":["Gap log"], "fail_soft_on_missing":True,
         "acquisition_tasks":["FOIA/ROA request","Get stamped order copy","Confirm service proof"]},
        {"transition_id":"T_PINNED_TO_VEHICLES","from_state":"ORDER_PINNED","to_state":"VEHICLE_CANDIDATES","trigger_filing_or_event":"Vehicle routing requested",
         "authority_candidates":auth["lane"], "preconditions":["Order pin current"], "deadline_clock_ids":["CLK_TRIAL_RESPONSE"], "service_gate_ids":["SG_TRIAL_FILE"],
         "proof_obligations":["Authority candidate list"], "fail_soft_on_missing":False, "acquisition_tasks":[]},
        {"transition_id":"T_VEHICLES_TO_SERVICE","from_state":"VEHICLE_CANDIDATES","to_state":"SERVICE_GATES_PENDING","trigger_filing_or_event":triggers["trial_vehicle"],
         "authority_candidates":auth["lane"], "preconditions":["Selected vehicle candidate"], "deadline_clock_ids":["CLK_TRIAL_RESPONSE"], "service_gate_ids":["SG_TRIAL_FILE"],
         "proof_obligations":["Draft packet + service plan"], "fail_soft_on_missing":True,
         "acquisition_tasks":["Confirm service method availability", "Collect addresses/party service targets"]},
        {"transition_id":"T_SERVICE_TO_TRIAL_READY","from_state":"SERVICE_GATES_PENDING","to_state":"TRIAL_ROUTE_READY","trigger_filing_or_event":"Service gate pass or fail-soft accepted",
         "authority_candidates":["MCR 2.105/2.107 (candidate)"], "preconditions":["Proof obligations mapped"], "deadline_clock_ids":["CLK_TRIAL_RESPONSE"], "service_gate_ids":["SG_TRIAL_FILE"],
         "proof_obligations":["Proof of service template"], "fail_soft_on_missing":True,
         "acquisition_tasks":["If no proof, create explicit nonservice defect ledger"]},
        {"transition_id":"T_TRIAL_READY_TO_FILED","from_state":"TRIAL_ROUTE_READY","to_state":"TRIAL_FILED","trigger_filing_or_event":"Packet filed",
         "authority_candidates":auth["lane"], "preconditions":["Validation ledger not BLOCKED"], "deadline_clock_ids":["CLK_TRIAL_RESPONSE"], "service_gate_ids":["SG_TRIAL_FILE"],
         "proof_obligations":["File stamp"], "fail_soft_on_missing":False, "acquisition_tasks":[]},
        {"transition_id":"T_FILED_TO_HEARING","from_state":"TRIAL_FILED","to_state":"HEARING_OR_RESPONSE_PENDING","trigger_filing_or_event":"Hearing set or response awaited",
         "authority_candidates":auth["lane"], "preconditions":["ROA updated"], "deadline_clock_ids":["CLK_TRIAL_RESPONSE"], "service_gate_ids
