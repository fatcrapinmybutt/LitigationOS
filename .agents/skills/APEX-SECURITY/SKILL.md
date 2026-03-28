---
name: APEX-SECURITY
description: >-
  APEX-SECURITY is the unified security mastery system that fuses offensive
  kill-chain execution, adversarial reasoning, and vulnerability intelligence
  into one autonomous red/blue cognition layer. It maps attack surfaces,
  simulates real adversaries, drives exploitation logic, architects layered
  defenses, governs remediation, and verifies compliance in one closed loop.
  Use it when the mission requires simultaneous attacker thinking and
  defender action instead of isolated security specialties.
category: apex-security
version: "1.0.0"
triggers:
  - autonomous red team
  - blue team fusion
  - attack surface mapping
  - exploit chain simulation
  - threat modeling
  - vulnerability lifecycle
  - purple team exercise
  - MITRE ATT&CK emulation
  - zero trust architecture
  - CVE triage and patching
  - OWASP security program
  - security compliance automation
metadata:
  tier: APEX
  fused_forges: 3
  total_source_skills: ~27
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: "2026-03-27"
  forge_class: APEX-CONVERGENCE
  emergent_capability: "Autonomous red/blue team — offense and defense as unified security cognition"
---

# 🛡️ APEX-SECURITY
> **Autonomous Red/Blue Team Security Consciousness (Ω-Δ99 APEX)**

> | Dimension | Value |
> |---|---|
> | **Tier** | APEX |
> | **Domain** | Offensive Security × Defensive Architecture × Vulnerability Intelligence |
> | **Scope** | Reconnaissance, exploitation, detection engineering, patch orchestration, adversary emulation, compliance evidence |
> | **Emergent Capability** | Autonomous red/blue team — offense and defense as unified security cognition |
> | **Control Philosophy** | Every attack idea must immediately produce a defense, and every defense must survive a realistic attack path |

## Forged from 3 FORGE Skills

| FORGE Skill | Domain Contribution | Core Fusion Result | Distinct Value to APEX |
|---|---|---|---|
| **FORGE-PENTESTING-KILL-CHAIN** | Recon, exploitation, persistence, lateral movement, exfiltration | Turns isolated findings into compound, staged attack paths | Provides kinetic offensive sequencing and post-exploitation realism |
| **FORGE-ADVERSARIAL-INTELLIGENCE** | Threat modeling, counter-strategy, adversary personas, ATT&CK reasoning | Predicts how real operators choose timing, targets, and pivots | Provides intent, motive, and decision logic behind attacks |
| **FORGE-VULNERABILITY-MATRIX** | CVE intelligence, OWASP assessment, remediation, compliance, scanning | Continuously discovers, prioritizes, patches, and verifies weakness closure | Provides durable governance, evidence, and lifecycle discipline |

## APEX Security Thesis

A traditional pentest ends with a report. A traditional blue team ends with detections.
A traditional compliance team ends with evidence folders. **APEX-SECURITY collapses those
three timelines into one living system.** The same graph that models the attack surface also
models the control surface, the patch backlog, the ATT&CK campaign narrative, and the audit
trail proving risk reduction.

This convergence creates behaviors the individual FORGE skills cannot achieve alone:

- The exploit engine can stop itself when a hypothetical chain would violate a production guardrail and immediately emit a defense design instead.
- A high-severity CVE is not just triaged by CVSS; it is replayed through likely adversary objectives, mapped to actual reachable assets, and then converted into compensating controls while patching is pending.
- MITRE ATT&CK coverage is measured against real kill chains, not abstract matrices.
- Compliance gaps are validated by adversarial simulation so the control narrative cannot drift into paperwork theater.
- Remediation order is chosen by blast radius plus adversary value, not by scanner severity alone.

## ASCII Architecture Diagram

```text
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                                  APEX-SECURITY CORE                                  │
│                     Autonomous Red/Blue Team Security Cognition                       │
├───────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   ┌─────────────────┐     ┌──────────────────┐     ┌────────────────────────────┐    │
│   │ AS1             │────▶│ AS2              │────▶│ AS3                        │    │
│   │ Unified Threat  │ map │ Autonomous       │ path│ Defense-in-Depth Architect │    │
│   │ Landscape       │     │ Penetration      │     │                            │    │
│   │                 │     │ Engine           │     │                            │    │
│   └────────┬────────┘     └────────┬─────────┘     └────────────┬───────────────┘    │
│            │                       │                              │                    │
│            │                       ▼                              ▼                    │
│            │             ┌──────────────────┐           ┌──────────────────────┐      │
│            │             │ AS4              │◀─────────▶│ AS5                  │      │
│            └────────────▶│ Vulnerability    │ findings  │ Adversary Simulation │      │
│                          │ Lifecycle Manager│           │ Framework            │      │
│                          └────────┬─────────┘           └──────────┬───────────┘      │
│                                   │                                │                  │
│                                   ▼                                ▼                  │
│                           ┌─────────────────────────────────────────────────────┐      │
│                           │ AS6 Security Compliance Automaton                  │      │
│                           │ SOC2 · ISO 27001 · NIST · OWASP evidence closure  │      │
│                           └─────────────────────────────────────────────────────┘      │
│                                                                                       │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ DATA LAYERS                                                                           │
│ • Assets • Identities • CVEs • Attack Paths • ATT&CK Techniques • Controls • Evidence│
│ • Detection Rules • Patch Waves • Exceptions • Waivers • Audit Artifacts             │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ EMERGENT LOOP                                                                         │
│ attack idea → exploit path → compensating control → patch plan → simulation replay   │
│ → compliance proof → residual risk review → new attack idea                           │
└───────────────────────────────────────────────────────────────────────────────────────┘
```
## AS1: Unified Threat Landscape

### Purpose
AS1 builds the canonical attack-and-defense map of the environment. It does not merely enumerate assets; it correlates services, identities, data sensitivity, trust boundaries, reachable networks, and control ownership so that every later offensive or defensive decision operates from one verified topology.

### Design Pattern
Graph Builder + Exposure Scoring + Identity Correlation. The module fuses attack surface management with adversary-value ranking so the same map can drive recon priorities, zero-trust design, patch urgency, and compliance evidence collection.

### Why This Module Is APEX, Not Merely FORGE
- It sees assets as both targets and defended surfaces, allowing recon output to become control design input without translation loss.
- It correlates business criticality with exploit reachability, which means a low-count exposure on a regulated system can outrank many noisy internet hosts.
- It ties identities to assets early, letting later modules model privilege inheritance, lateral movement risk, and least-privilege redesign from the same dataset.

### Core Responsibilities
1. Ingest asset inventories, service catalogs, cloud topology, identity assignments, and data classifications.
2. Normalize reachable surfaces into a graph that preserves exposure, ownership, and trust boundaries.
3. Calculate attack surface scores that are meaningful to both operators and governance teams.
4. Emit high-confidence target maps for exploitation, detection engineering, and patch sequencing.
5. Continuously detect drift when services or trust paths change.

### Inputs
- CMDB exports, cloud inventory, Kubernetes services, firewall rules, IAM grants, SSO groups
- Passive recon outputs such as DNS, certificate transparency, and service discovery
- Scanner evidence from VM1-style discovery and purple-team exercise artifacts

### Outputs
- Canonical threat graph digest
- Critical asset shortlist ordered by adversary value and control weakness
- Routing hints for AS2, AS3, and AS4

### Code Example — Python
```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from ipaddress import ip_network
from typing import Iterable
import hashlib
import json


class ExposureLevel(str, Enum):
    INTERNET = "internet"
    PARTNER = "partner"
    INTERNAL = "internal"
    RESTRICTED = "restricted"


@dataclass(slots=True)
class Service:
    port: int
    protocol: str
    name: str
    exposure: ExposureLevel
    auth_required: bool
    internet_reachable: bool = False


@dataclass(slots=True)
class Asset:
    asset_id: str
    hostname: str
    cidr: str
    business_owner: str
    data_classification: str
    services: list[Service] = field(default_factory=list)
    identities: list[str] = field(default_factory=list)

    def attack_surface_score(self) -> int:
        score = 0
        for service in self.services:
            score += 20 if service.internet_reachable else 8
            score += 10 if not service.auth_required else 0
            score += 5 if service.protocol.lower() in {"http", "https"} else 2
        if self.data_classification in {"regulated", "secrets", "customer-pii"}:
            score += 25
        return min(score, 100)


@dataclass(slots=True)
class ThreatEdge:
    source: str
    target: str
    relation: str
    confidence: float


class ThreatLandscapeBuilder:
    def __init__(self, assets: Iterable[Asset]) -> None:
        self.assets = list(assets)

    def discover_edges(self) -> list[ThreatEdge]:
        edges: list[ThreatEdge] = []
        for asset in self.assets:
            for service in asset.services:
                relation = f"exposes:{service.name}:{service.port}/{service.protocol}"
                confidence = 0.95 if service.internet_reachable else 0.70
                edges.append(ThreatEdge(asset.asset_id, service.name, relation, confidence))
            for identity in asset.identities:
                edges.append(ThreatEdge(identity, asset.asset_id, "has-access-to", 0.90))
        return edges

    def summarize(self) -> dict[str, object]:
        critical_assets = [a for a in self.assets if a.attack_surface_score() >= 70]
        reachable_networks = sorted({str(ip_network(a.cidr, strict=False)) for a in self.assets})
        edges = self.discover_edges()
        digest = hashlib.sha256(
            json.dumps([edge.__dict__ for edge in edges], sort_keys=True).encode("utf-8")
        ).hexdigest()
        return {
            "asset_count": len(self.assets),
            "critical_assets": [a.hostname for a in critical_assets],
            "reachable_networks": reachable_networks,
            "edge_count": len(edges),
            "graph_digest": digest,
        }


assets = [
    Asset(
        asset_id="svc-payments-prod",
        hostname="payments-prod-01",
        cidr="10.42.10.15/24",
        business_owner="finance-platform",
        data_classification="regulated",
        services=[
            Service(443, "https", "payments-api", ExposureLevel.INTERNET, auth_required=True, internet_reachable=True),
            Service(5432, "tcp", "postgres", ExposureLevel.RESTRICTED, auth_required=True),
        ],
        identities=["svc-payments", "breakglass-admin"],
    ),
    Asset(
        asset_id="svc-identity",
        hostname="identity-01",
        cidr="10.42.20.8/24",
        business_owner="platform-security",
        data_classification="customer-pii",
        services=[
            Service(443, "https", "identity-api", ExposureLevel.PARTNER, auth_required=True, internet_reachable=True),
            Service(389, "tcp", "ldap", ExposureLevel.INTERNAL, auth_required=True),
        ],
        identities=["svc-identity", "iam-admin"],
    ),
]


builder = ThreatLandscapeBuilder(assets)
landscape = builder.summarize()
print(json.dumps(landscape, indent=2))
```

### Operational Telemetry
- Track graph digests over time to detect silent attack surface drift.
- Measure count of unauthenticated services and privileged identities attached to regulated assets.
- Record asset-owner completeness and flag orphaned systems that lack accountable defenders.
- Publish network-reachability deltas to AS5 before purple-team planning starts.

### Analyst Questions
- What assumption inside AS1 would most likely fail if the environment changed today?
- Which asset, identity, or control in AS1 currently has the highest attacker value relative to monitoring depth?
- What evidence would falsify the current confidence level of AS1 outputs?
- Which dependency outside AS1 must remain healthy for this module to stay trustworthy?

### Execution Sequence
1. Validate incoming context for freshness, ownership, and trustworthiness.
2. Run the module-specific reasoning pass with explicit safety and evidence constraints.
3. Emit both technical outputs and operational decisions rather than raw observations alone.
4. Route follow-on work to adjacent modules using structured handoff data, not prose only.
5. Record telemetry, assumptions, and residual uncertainty for later review.
6. Trigger revalidation whenever new attack evidence, control drift, or governance exceptions appear.

### Integration Points
- Feeds AS2 with ranked entry points and likely pivot nodes.
- Feeds AS3 with trust boundaries requiring layered controls and identity restrictions.
- Feeds AS4 with exposure-aware prioritization so patching follows reachable risk, not abstract severity.
- Feeds AS6 with authoritative asset ownership and data classification evidence for audits.

### Red / Blue Artifacts Produced
- AS1 operational summary suitable for incident command, engineering, and governance review.
- Machine-readable outputs that can be consumed by the next module without manual translation.
- Prioritized action items that distinguish urgent operational fixes from structural program improvements.
- Evidence notes explaining what is known, what is inferred, and what still requires validation.

### Review Cadence
- Re-run immediately after material architecture change, acquisition, or internet exposure expansion.
- Re-run after any critical or high exploitability finding is patched or compensated.
- Re-run before major audits, customer attestations, or executive risk reviews.
- Re-run after purple exercises, incidents, or threat-intelligence changes reveal new tradecraft.

### Escalation Criteria
- Escalate when confidence is low but blast radius is high.
- Escalate when multiple modules disagree about whether risk is closed.
- Escalate when technical truth contradicts policy, waiver, or audit narratives.
- Escalate when the same weakness repeatedly reappears after previous closure claims.

### Failure Modes Prevented by Fusion
- Single-tool tunnel vision that optimizes one phase while creating silent exposure in another.
- Defensive fixes that ignore realistic adversary sequencing and therefore collapse under chained exploitation.
- Offensive findings that lack control mapping, ownership, patch sequencing, or measurable verification.
- Compliance artifacts that look complete on paper but fail when attacked by an adversary who understands system drift.

## AS2: Autonomous Penetration Engine

### Purpose
AS2 transforms the mapped landscape into adversary-valid attack paths. It plans full-chain operations from initial access through exfiltration, but it does so with explicit guardrails so production safety, authorization boundaries, and compensating controls remain first-class constraints rather than afterthoughts.

### Design Pattern
Planner + Guardrail Enforcer + Multi-Phase Executor. The engine reasons about prerequisites, blast radius, stealth, privilege inheritance, and control response while constructing a chain that is realistic enough for red teaming and actionable enough for blue-team engineering.

### Why This Module Is APEX, Not Merely FORGE
- It never treats exploitation as isolated proof-of-concept work; every step is evaluated for the next pivot, the next credential opportunity, and the next defender reaction.
- It can stop an offensive sequence and immediately convert that incomplete path into a control-validation scenario instead of discarding partial progress.
- It treats simulation, lab validation, and blocked production execution as first-class operating modes so the same logic scales from tabletop to controlled exercise.

### Core Responsibilities
1. Build chained attack paths from foothold to objective using real prerequisites.
2. Select the smallest set of steps needed to prove reachability without unnecessary blast radius.
3. Attach expected defensive telemetry and control assertions to every offensive step.
4. Differentiate between safe simulation, lab validation, and blocked production execution.
5. Return control-verification tasks even when a chain cannot be completed.

### Inputs
- Threat graphs, exposed services, identity grants, known weaknesses, and campaign objectives
- Adversary personas and ATT&CK tactic preferences from AS5
- Patch and control-state information from AS4 and AS3

### Outputs
- Attack path timeline with explicit prerequisites
- Control verification checklist aligned to the path
- Abort or stop reasons that become defensive work items instead of dead ends

### Code Example — Python
```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
import time


class Mode(str, Enum):
    SIMULATION = "simulation"
    LAB = "lab"
    PRODUCTION_BLOCKED = "production-blocked"


@dataclass(slots=True)
class Capability:
    name: str
    prerequisites: set[str]
    blast_radius: str
    detection_risk: float


@dataclass(slots=True)
class AttackPath:
    objective: str
    steps: list[str]
    controls_to_test: list[str]
    stop_reason: str | None = None


class AutonomousPenetrationEngine:
    def __init__(self, mode: Mode, capabilities: Iterable[Capability]) -> None:
        self.mode = mode
        self.capabilities = {cap.name: cap for cap in capabilities}

    def plan(self, footholds: set[str], objective: str) -> AttackPath:
        steps: list[str] = []
        controls_to_test: list[str] = []
        required = [
            "phishing-resistant-auth-bypass",
            "idor-enumeration",
            "privilege-escalation",
            "secrets-access",
            "exfiltration-channel",
        ]
        available = set(footholds)
        for capability_name in required:
            capability = self.capabilities[capability_name]
            if not capability.prerequisites.issubset(available):
                return AttackPath(
                    objective=objective,
                    steps=steps,
                    controls_to_test=controls_to_test,
                    stop_reason=f"missing prerequisites for {capability_name}",
                )
            steps.append(f"exercise:{capability.name}")
            controls_to_test.append(f"detect:{capability.name}")
            available.add(capability.name)
        return AttackPath(objective=objective, steps=steps, controls_to_test=controls_to_test)

    def execute(self, path: AttackPath) -> dict[str, object]:
        if self.mode == Mode.PRODUCTION_BLOCKED:
            return {
                "status": "blocked",
                "reason": "production execution disabled",
                "recommended_controls": path.controls_to_test,
            }
        timeline: list[dict[str, object]] = []
        for order, step in enumerate(path.steps, start=1):
            timeline.append(
                {
                    "order": order,
                    "step": step,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": "simulated" if self.mode == Mode.SIMULATION else "validated-in-lab",
                }
            )
        return {
            "status": "completed",
            "objective": path.objective,
            "timeline": timeline,
            "controls_to_verify": path.controls_to_test,
            "stop_reason": path.stop_reason,
        }


capabilities = [
    Capability("phishing-resistant-auth-bypass", {"initial-access"}, "user-identity", 0.65),
    Capability("idor-enumeration", {"initial-access", "phishing-resistant-auth-bypass"}, "tenant-data", 0.40),
    Capability("privilege-escalation", {"initial-access", "idor-enumeration"}, "admin-scope", 0.75),
    Capability("secrets-access", {"initial-access", "privilege-escalation"}, "key-material", 0.80),
    Capability("exfiltration-channel", {"initial-access", "secrets-access"}, "data-loss", 0.85),
]


engine = AutonomousPenetrationEngine(Mode.SIMULATION, capabilities)
path = engine.plan({"initial-access"}, "obtain regulated customer dataset")
result = engine.execute(path)
for entry in result.get("timeline", []):
    print(f"{entry['order']}: {entry['step']} -> {entry['status']}")
```

### Operational Telemetry
- Measure path depth, required privileges, stealth cost, and expected detection count per exercise.
- Record which controls should have triggered at each step and whether they did.
- Maintain a count of offensive plans converted into preventive design work without live execution.
- Compare successful paths against previous purple exercises to quantify hardening progress.

### Analyst Questions
- What assumption inside AS2 would most likely fail if the environment changed today?
- Which asset, identity, or control in AS2 currently has the highest attacker value relative to monitoring depth?
- What evidence would falsify the current confidence level of AS2 outputs?
- Which dependency outside AS2 must remain healthy for this module to stay trustworthy?

### Execution Sequence
1. Validate incoming context for freshness, ownership, and trustworthiness.
2. Run the module-specific reasoning pass with explicit safety and evidence constraints.
3. Emit both technical outputs and operational decisions rather than raw observations alone.
4. Route follow-on work to adjacent modules using structured handoff data, not prose only.
5. Record telemetry, assumptions, and residual uncertainty for later review.
6. Trigger revalidation whenever new attack evidence, control drift, or governance exceptions appear.

### Integration Points
- Consumes AS1 graph rankings and returns exploited path candidates to AS5 for replay.
- Triggers AS3 when an exploit path reveals a missing segmentation, identity, or DLP layer.
- Creates AS4 remediation items when a chain proves real exploitability of a scanner finding.
- Supplies AS6 with evidence that control operation was tested adversarially, not just documented.

### Red / Blue Artifacts Produced
- AS2 operational summary suitable for incident command, engineering, and governance review.
- Machine-readable outputs that can be consumed by the next module without manual translation.
- Prioritized action items that distinguish urgent operational fixes from structural program improvements.
- Evidence notes explaining what is known, what is inferred, and what still requires validation.

### Review Cadence
- Re-run immediately after material architecture change, acquisition, or internet exposure expansion.
- Re-run after any critical or high exploitability finding is patched or compensated.
- Re-run before major audits, customer attestations, or executive risk reviews.
- Re-run after purple exercises, incidents, or threat-intelligence changes reveal new tradecraft.

### Escalation Criteria
- Escalate when confidence is low but blast radius is high.
- Escalate when multiple modules disagree about whether risk is closed.
- Escalate when technical truth contradicts policy, waiver, or audit narratives.
- Escalate when the same weakness repeatedly reappears after previous closure claims.

### Failure Modes Prevented by Fusion
- Single-tool tunnel vision that optimizes one phase while creating silent exposure in another.
- Defensive fixes that ignore realistic adversary sequencing and therefore collapse under chained exploitation.
- Offensive findings that lack control mapping, ownership, patch sequencing, or measurable verification.
- Compliance artifacts that look complete on paper but fail when attacked by an adversary who understands system drift.

## AS3: Defense-in-Depth Architect

### Purpose
AS3 designs the layered response to the attack paths found by AS1 and AS2. It translates realistic adversary behavior into preventive, detective, and recovery controls across identity, network, workload, application, and data layers, with zero-trust assumptions enforced by default.

### Design Pattern
Threat-to-Control Mapper + Zero-Trust Policy Builder + Residual Risk Reducer. The module builds layered controls that overlap intentionally so single-control failure does not equal mission failure.

### Why This Module Is APEX, Not Merely FORGE
- It does not design static checklists; it designs layers specifically against real attack paths already proven or strongly modeled by AS2 and AS5.
- It balances prevention and detection by recognizing when stopping an attacker is infeasible but exposing them early is achievable.
- It converts business context into control depth, so regulated assets and crown jewels inherit stronger guardrails automatically.

### Core Responsibilities
1. Map realistic threats to compensating, preventive, detective, and recovery controls.
2. Generate deny-by-default access policies with just-in-time exceptions.
3. Choose control stacks that reduce both exploit success and post-exploit maneuverability.
4. Surface residual risks that remain after the control stack is applied.
5. Emit implementation-ready control plans for platform, identity, and engineering teams.

### Inputs
- Ranked threats, exploit paths, ATT&CK mappings, identity graphs, and asset criticality
- Existing control inventory, control effectiveness ratings, and policy exceptions
- Compliance obligations and compensating-control allowances from AS6

### Outputs
- Control maps aligned to specific threats and assets
- Zero-trust policy fragments and inspection requirements
- Residual risk statements for leadership acceptance or further remediation

### Code Example — Python
```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
import json


@dataclass(slots=True)
class Threat:
    vector: str
    asset: str
    likelihood: int
    impact: int

    @property
    def risk(self) -> int:
        return self.likelihood * self.impact


@dataclass(slots=True)
class Control:
    control_id: str
    family: str
    description: str
    trust_boundary: str
    effectiveness: float


class DefenseInDepthArchitect:
    def __init__(self, controls: Iterable[Control]) -> None:
        self.controls = list(controls)

    def map_controls(self, threats: Iterable[Threat]) -> dict[str, list[Control]]:
        mapped: dict[str, list[Control]] = {}
        for threat in threats:
            selected = [
                control
                for control in self.controls
                if control.family in {
                    "identity",
                    "network",
                    "workload",
                    "data",
                    "detection",
                }
            ]
            selected.sort(key=lambda item: item.effectiveness, reverse=True)
            mapped[f"{threat.asset}:{threat.vector}"] = selected[:3]
        return mapped

    def zero_trust_policy(self, asset: str, identities: list[str]) -> dict[str, object]:
        return {
            "asset": asset,
            "default_action": "deny",
            "required_claims": ["mfa", "managed-device", "just-in-time-approval"],
            "allowed_identities": identities,
            "inspection_layers": ["identity", "network", "runtime", "data-loss-prevention"],
        }


controls = [
    Control("IAM-01", "identity", "Enforce phishing-resistant MFA", "identity", 0.95),
    Control("NET-07", "network", "Mutual TLS between service tiers", "network", 0.88),
    Control("WKL-03", "workload", "Ephemeral workload identity", "runtime", 0.85),
    Control("DAT-09", "data", "Column-level encryption for regulated records", "data", 0.82),
    Control("DET-14", "detection", "High-signal ATT&CK aligned analytics", "siem", 0.90),
]

threats = [
    Threat("credential-theft", "identity-api", 5, 5),
    Threat("ssrf-to-metadata", "payments-api", 4, 5),
    Threat("lateral-movement", "admin-jump-host", 4, 4),
]


architect = DefenseInDepthArchitect(controls)
mapping = architect.map_controls(threats)
policy = architect.zero_trust_policy("payments-api", ["svc-payments", "sre-breakglass"])
print(json.dumps({"mapping": {k: [c.control_id for c in v] for k, v in mapping.items()}, "policy": policy}, indent=2))
```

### Operational Telemetry
- Track mean control depth per critical asset and identify single-point defensive failures.
- Measure control overlap across identity, network, runtime, and data boundaries.
- Compare intended control effectiveness with exercise-derived effectiveness from AS5.
- Count emergency exceptions and force periodic re-validation of each waiver.

### Analyst Questions
- What assumption inside AS3 would most likely fail if the environment changed today?
- Which asset, identity, or control in AS3 currently has the highest attacker value relative to monitoring depth?
- What evidence would falsify the current confidence level of AS3 outputs?
- Which dependency outside AS3 must remain healthy for this module to stay trustworthy?

### Execution Sequence
1. Validate incoming context for freshness, ownership, and trustworthiness.
2. Run the module-specific reasoning pass with explicit safety and evidence constraints.
3. Emit both technical outputs and operational decisions rather than raw observations alone.
4. Route follow-on work to adjacent modules using structured handoff data, not prose only.
5. Record telemetry, assumptions, and residual uncertainty for later review.
6. Trigger revalidation whenever new attack evidence, control drift, or governance exceptions appear.

### Integration Points
- Consumes AS2 exploit results to design controls that actually break proven chains.
- Feeds AS4 when a mitigation should precede or substitute for a delayed patch.
- Feeds AS5 with blocking controls to validate in purple exercises.
- Feeds AS6 with control descriptions, policy references, and implementation evidence requirements.

### Red / Blue Artifacts Produced
- AS3 operational summary suitable for incident command, engineering, and governance review.
- Machine-readable outputs that can be consumed by the next module without manual translation.
- Prioritized action items that distinguish urgent operational fixes from structural program improvements.
- Evidence notes explaining what is known, what is inferred, and what still requires validation.

### Review Cadence
- Re-run immediately after material architecture change, acquisition, or internet exposure expansion.
- Re-run after any critical or high exploitability finding is patched or compensated.
- Re-run before major audits, customer attestations, or executive risk reviews.
- Re-run after purple exercises, incidents, or threat-intelligence changes reveal new tradecraft.

### Escalation Criteria
- Escalate when confidence is low but blast radius is high.
- Escalate when multiple modules disagree about whether risk is closed.
- Escalate when technical truth contradicts policy, waiver, or audit narratives.
- Escalate when the same weakness repeatedly reappears after previous closure claims.

### Failure Modes Prevented by Fusion
- Single-tool tunnel vision that optimizes one phase while creating silent exposure in another.
- Defensive fixes that ignore realistic adversary sequencing and therefore collapse under chained exploitation.
- Offensive findings that lack control mapping, ownership, patch sequencing, or measurable verification.
- Compliance artifacts that look complete on paper but fail when attacked by an adversary who understands system drift.

## AS4: Vulnerability Lifecycle Manager

### Purpose
AS4 governs the discover → triage → patch → verify cycle for every weakness that matters. It ranks vulnerabilities by exploitability, reachability, business blast radius, and adversary value, then orchestrates patch waves, compensating controls, verification scans, and closure evidence.

### Design Pattern
Closed-Loop Remediation Orchestrator + Exposure-Aware Prioritizer. The module turns scanner noise into operating decisions and refuses to mark work complete until exploit paths, telemetry, and compliance evidence all agree the risk has changed.

### Why This Module Is APEX, Not Merely FORGE
- It understands that a critical CVE on an isolated lab host may matter less than a medium flaw on an internet-facing identity boundary with clear adversary value.
- It does not treat patching as done when the version changes; it requires exploit replay, control validation, and evidence closure.
- It routes unresolved issues into compensating-control design instead of letting them stagnate as accepted risk without defense.

### Core Responsibilities
1. Aggregate scanner output, red-team proof, and business context into one priority queue.
2. Apply SLAs that reflect severity, exploitability, reachability, and crown-jewel proximity.
3. Trigger patch waves or compensating-control work depending on fix availability.
4. Verify closure with rescans, replayed exploit paths, and telemetry review.
5. Preserve an auditable history of risk posture change for each finding.

### Inputs
- CVE feeds, scanner findings, exploit-path confirmation, asset sensitivity, and control exceptions
- Patch advisories, package versions, dependency graphs, and change windows
- Validation results from AS2 and AS5 and control-state data from AS3

### Outputs
- Prioritized remediation backlog with owners and deadlines
- Patch wave plans and compensating-control assignments
- Verification records proving whether risk closed, shrank, or persists

### Code Example — Python
```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable


class Status(str, Enum):
    DISCOVERED = "discovered"
    TRIAGED = "triaged"
    PATCHING = "patching"
    VERIFIED = "verified"
    ACCEPTED = "accepted"


@dataclass(slots=True)
class Finding:
    finding_id: str
    title: str
    asset: str
    cve: str | None
    severity: str
    exploitability: float
    internet_reachable: bool
    patch_available: bool
    owner: str
    status: Status = Status.DISCOVERED
    due_at: datetime | None = None


class VulnerabilityLifecycleManager:
    def prioritize(self, findings: Iterable[Finding]) -> list[Finding]:
        ranked = sorted(
            findings,
            key=lambda item: (
                item.internet_reachable,
                item.patch_available,
                item.exploitability,
                item.severity,
            ),
            reverse=True,
        )
        for finding in ranked:
            finding.status = Status.TRIAGED
            sla_days = 3 if finding.severity == "critical" else 7 if finding.severity == "high" else 30
            finding.due_at = datetime.utcnow() + timedelta(days=sla_days)
        return ranked

    def patch_wave(self, findings: Iterable[Finding]) -> list[dict[str, str]]:
        plans: list[dict[str, str]] = []
        for finding in findings:
            finding.status = Status.PATCHING if finding.patch_available else Status.ACCEPTED
            plans.append(
                {
                    "finding_id": finding.finding_id,
                    "owner": finding.owner,
                    "action": "apply vendor patch" if finding.patch_available else "add compensating controls",
                    "verification": "re-scan + replay exploit chain + validate telemetry",
                }
            )
        return plans

    def verify(self, findings: Iterable[Finding]) -> list[str]:
        verified: list[str] = []
        for finding in findings:
            if finding.patch_available:
                finding.status = Status.VERIFIED
                verified.append(f"{finding.finding_id}:closed")
            else:
                verified.append(f"{finding.finding_id}:control-monitored")
        return verified


findings = [
    Finding("F-1001", "SSRF to cloud metadata", "payments-api", "CVE-2026-1001", "critical", 0.96, True, True, "platform"),
    Finding("F-1002", "Token leak in CI logs", "build-pipeline", None, "high", 0.91, True, False, "devsecops"),
    Finding("F-1003", "Outdated OpenSSL", "edge-proxy", "CVE-2026-2002", "high", 0.75, True, True, "network"),
]


manager = VulnerabilityLifecycleManager()
triaged = manager.prioritize(findings)
wave = manager.patch_wave(triaged)
verification = manager.verify(triaged)

for item in wave:
    print(item["finding_id"], item["action"], item["verification"])
for result in verification:
    print(result)
```

### Operational Telemetry
- Measure exposure-weighted backlog age rather than raw ticket count.
- Track how many findings were confirmed exploitable versus scanner-only.
- Record verification quality: re-scan only, exploit replay, or full purple validation.
- Publish missed SLAs alongside business justification and waiver ownership.

### Analyst Questions
- What assumption inside AS4 would most likely fail if the environment changed today?
- Which asset, identity, or control in AS4 currently has the highest attacker value relative to monitoring depth?
- What evidence would falsify the current confidence level of AS4 outputs?
- Which dependency outside AS4 must remain healthy for this module to stay trustworthy?

### Execution Sequence
1. Validate incoming context for freshness, ownership, and trustworthiness.
2. Run the module-specific reasoning pass with explicit safety and evidence constraints.
3. Emit both technical outputs and operational decisions rather than raw observations alone.
4. Route follow-on work to adjacent modules using structured handoff data, not prose only.
5. Record telemetry, assumptions, and residual uncertainty for later review.
6. Trigger revalidation whenever new attack evidence, control drift, or governance exceptions appear.

### Integration Points
- Consumes AS1 exposure ranking to prioritize reachable assets over theoretical noise.
- Consumes AS2 proof-of-exploit to distinguish exploitable from speculative weaknesses.
- Consumes AS3 mitigation options when no patch exists or maintenance windows are constrained.
- Produces AS6 evidence that remediation is active, measured, and verified.

### Red / Blue Artifacts Produced
- AS4 operational summary suitable for incident command, engineering, and governance review.
- Machine-readable outputs that can be consumed by the next module without manual translation.
- Prioritized action items that distinguish urgent operational fixes from structural program improvements.
- Evidence notes explaining what is known, what is inferred, and what still requires validation.

### Review Cadence
- Re-run immediately after material architecture change, acquisition, or internet exposure expansion.
- Re-run after any critical or high exploitability finding is patched or compensated.
- Re-run before major audits, customer attestations, or executive risk reviews.
- Re-run after purple exercises, incidents, or threat-intelligence changes reveal new tradecraft.

### Escalation Criteria
- Escalate when confidence is low but blast radius is high.
- Escalate when multiple modules disagree about whether risk is closed.
- Escalate when technical truth contradicts policy, waiver, or audit narratives.
- Escalate when the same weakness repeatedly reappears after previous closure claims.

### Failure Modes Prevented by Fusion
- Single-tool tunnel vision that optimizes one phase while creating silent exposure in another.
- Defensive fixes that ignore realistic adversary sequencing and therefore collapse under chained exploitation.
- Offensive findings that lack control mapping, ownership, patch sequencing, or measurable verification.
- Compliance artifacts that look complete on paper but fail when attacked by an adversary who understands system drift.

## AS5: Adversary Simulation Framework

### Purpose
AS5 operationalizes the purple-team core of the APEX system. It converts adversary objectives, MITRE ATT&CK techniques, known exploits, and defensive hypotheses into replayable exercises that prove whether the organization can see, stop, and recover from realistic campaigns.

### Design Pattern
Scenario Compiler + ATT&CK Sequencer + Purple Exercise Recorder. The module produces repeatable exercises whose output is equally useful to detection engineers, control owners, incident responders, and auditors.

### Why This Module Is APEX, Not Merely FORGE
- It fuses attacker intent with vulnerability and control state, so an exercise is never generic theater.
- It measures defensive quality at the exact step where an operator would act, not only at the final breach outcome.
- It converts each observed gap into immediate tickets for AS3 and AS4 while preserving ATT&CK-linked evidence for AS6.

### Core Responsibilities
1. Build campaign scenarios from objectives, targets, techniques, and control assumptions.
2. Sequence ATT&CK techniques in ways that mirror plausible operator tradecraft and prerequisites.
3. Capture expected telemetry, analyst actions, and blocking controls at each step.
4. Produce replayable exercise packs for tabletop, lab, or controlled purple operations.
5. Quantify detection and response gaps with direct ties to remediation and governance work.

### Inputs
- Adversary persona data, exploit paths, ATT&CK mappings, and control hypotheses
- Detection content, incident response runbooks, and asset-level telemetry contracts
- Patch and policy state so exercises reflect reality rather than stale assumptions

### Outputs
- Replayable purple-team exercise plans
- ATT&CK coverage deltas and telemetry requirements
- Gap records that route directly to AS3, AS4, and AS6

### Code Example — Python
```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
import json


class ATTACK(str, Enum):
    INITIAL_ACCESS = "TA0001"
    PERSISTENCE = "TA0003"
    PRIV_ESC = "TA0004"
    DEFENSE_EVASION = "TA0005"
    CREDENTIAL_ACCESS = "TA0006"
    DISCOVERY = "TA0007"
    LATERAL_MOVEMENT = "TA0008"
    COLLECTION = "TA0009"
    EXFILTRATION = "TA0010"


@dataclass(slots=True)
class SimulationStep:
    technique: str
    tactic: ATTACK
    expectation: str
    telemetry: list[str]
    blocking_control: str


class AdversarySimulationFramework:
    def __init__(self, steps: Iterable[SimulationStep]) -> None:
        self.steps = list(steps)

    def run(self, mode: str = "purple") -> dict[str, object]:
        observations: list[dict[str, object]] = []
        for index, step in enumerate(self.steps, start=1):
            observations.append(
                {
                    "index": index,
                    "technique": step.technique,
                    "tactic": step.tactic.value,
                    "expected_red_goal": step.expectation,
                    "expected_blue_telemetry": step.telemetry,
                    "blocking_control": step.blocking_control,
                    "exercise_mode": mode,
                }
            )
        return {
            "exercise_mode": mode,
            "step_count": len(observations),
            "observations": observations,
            "success_criteria": [
                "all critical telemetry fields present",
                "response playbook invoked within SLA",
                "control gap converted into detection or prevention work item",
            ],
        }


steps = [
    SimulationStep("T1566.002", ATTACK.INITIAL_ACCESS, "credential capture via malicious link", ["proxy", "identity", "mail"], "phishing-resistant MFA"),
    SimulationStep("T1078", ATTACK.PERSISTENCE, "valid account reuse", ["identity", "conditional-access"], "conditional access policy"),
    SimulationStep("T1068", ATTACK.PRIV_ESC, "local privilege escalation", ["edr", "kernel alerts"], "application control"),
    SimulationStep("T1552", ATTACK.CREDENTIAL_ACCESS, "secrets harvested from files", ["file auditing", "edr"], "secret vault isolation"),
    SimulationStep("T1021", ATTACK.LATERAL_MOVEMENT, "remote service pivot", ["network flow", "auth logs"], "admin tier segmentation"),
    SimulationStep("T1041", ATTACK.EXFILTRATION, "exfiltration over existing channel", ["proxy", "dlp", "egress"], "egress filtering"),
]


framework = AdversarySimulationFramework(steps)
exercise = framework.run("purple")
print(json.dumps(exercise, indent=2))
```

### Operational Telemetry
- Track ATT&CK coverage against exercised techniques rather than paper mappings only.
- Measure time-to-detect, time-to-contain, and time-to-evidence for each step.
- Record which detections were high-signal, noisy, or absent.
- Maintain scenario drift metrics so exercises evolve with architecture and threat changes.

### Analyst Questions
- What assumption inside AS5 would most likely fail if the environment changed today?
- Which asset, identity, or control in AS5 currently has the highest attacker value relative to monitoring depth?
- What evidence would falsify the current confidence level of AS5 outputs?
- Which dependency outside AS5 must remain healthy for this module to stay trustworthy?

### Execution Sequence
1. Validate incoming context for freshness, ownership, and trustworthiness.
2. Run the module-specific reasoning pass with explicit safety and evidence constraints.
3. Emit both technical outputs and operational decisions rather than raw observations alone.
4. Route follow-on work to adjacent modules using structured handoff data, not prose only.
5. Record telemetry, assumptions, and residual uncertainty for later review.
6. Trigger revalidation whenever new attack evidence, control drift, or governance exceptions appear.

### Integration Points
- Consumes AS2 attack chains and converts them into controlled purple-team exercises.
- Validates AS3 blocking controls and AS4 compensating controls under realistic sequence pressure.
- Supplies AS6 with adversarially tested control evidence and ATT&CK-linked audit trails.
- Returns new path ideas to AS1 when exercises reveal hidden assets or trust relationships.

### Red / Blue Artifacts Produced
- AS5 operational summary suitable for incident command, engineering, and governance review.
- Machine-readable outputs that can be consumed by the next module without manual translation.
- Prioritized action items that distinguish urgent operational fixes from structural program improvements.
- Evidence notes explaining what is known, what is inferred, and what still requires validation.

### Review Cadence
- Re-run immediately after material architecture change, acquisition, or internet exposure expansion.
- Re-run after any critical or high exploitability finding is patched or compensated.
- Re-run before major audits, customer attestations, or executive risk reviews.
- Re-run after purple exercises, incidents, or threat-intelligence changes reveal new tradecraft.

### Escalation Criteria
- Escalate when confidence is low but blast radius is high.
- Escalate when multiple modules disagree about whether risk is closed.
- Escalate when technical truth contradicts policy, waiver, or audit narratives.
- Escalate when the same weakness repeatedly reappears after previous closure claims.

### Failure Modes Prevented by Fusion
- Single-tool tunnel vision that optimizes one phase while creating silent exposure in another.
- Defensive fixes that ignore realistic adversary sequencing and therefore collapse under chained exploitation.
- Offensive findings that lack control mapping, ownership, patch sequencing, or measurable verification.
- Compliance artifacts that look complete on paper but fail when attacked by an adversary who understands system drift.

## AS6: Security Compliance Automaton

### Purpose
AS6 turns the living security program into verifiable evidence across SOC 2, ISO 27001, NIST, and OWASP expectations. It does not merely collect documents; it evaluates whether implemented controls, exercise results, remediation records, and policy artifacts together prove the control actually operates.

### Design Pattern
Evidence Graph + Control Gating + Cross-Framework Mapper. The automaton links the same technical facts to multiple frameworks so the organization can defend itself to auditors without duplicating truth across disconnected spreadsheets.

### Why This Module Is APEX, Not Merely FORGE
- It refuses to accept documentary evidence that is contradicted by adversarial testing or remediation history.
- It maps one control state to many frameworks, eliminating compliance duplication while preserving framework-specific nuance.
- It measures coverage continuously so governance is driven by live security posture, not point-in-time audits.

### Core Responsibilities
1. Normalize control statements, technical evidence, and validation outputs across major frameworks.
2. Calculate coverage and gate decisions for each framework and control family.
3. Flag documentary claims unsupported by exploit replay, telemetry proof, or remediation evidence.
4. Emit auditor-ready summaries while preserving deep links to the technical truth.
5. Drive corrective action when compliance claims drift from operational reality.

### Inputs
- Policies, standards, risk register entries, evidence files, exercise reports, and remediation histories
- Control descriptions from AS3 and verification artifacts from AS4 and AS5
- Framework mappings for SOC2, ISO 27001, NIST CSF, and OWASP-aligned application controls

### Outputs
- Coverage dashboards and framework pass/remediate decisions
- Evidence requirements for missing or contradicted controls
- Unified proof packs backed by technical execution records

### Code Example — Python
```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
import json


@dataclass(slots=True)
class ControlEvidence:
    control_id: str
    framework: str
    statement: str
    evidence_paths: list[str]
    verified: bool


class SecurityComplianceAutomaton:
    def __init__(self, evidence: Iterable[ControlEvidence]) -> None:
        self.evidence = list(evidence)

    def summarize(self) -> dict[str, object]:
        frameworks: dict[str, dict[str, object]] = {}
        for item in self.evidence:
            frame = frameworks.setdefault(
                item.framework,
                {"total_controls": 0, "verified_controls": 0, "missing_evidence": []},
            )
            frame["total_controls"] += 1
            if item.verified:
                frame["verified_controls"] += 1
            else:
                frame["missing_evidence"].append(item.control_id)
        for frame in frameworks.values():
            total = frame["total_controls"] or 1
            frame["coverage"] = round(frame["verified_controls"] / total, 2)
        return frameworks

    def gate(self, minimum_coverage: float = 0.85) -> dict[str, str]:
        summary = self.summarize()
        decisions: dict[str, str] = {}
        for framework, data in summary.items():
            decisions[framework] = "pass" if data["coverage"] >= minimum_coverage else "remediate"
        return decisions


evidence = [
    ControlEvidence("CC6.1", "SOC2", "Logical access is restricted by role", ["evidence/iam-review.pdf"], True),
    ControlEvidence("CC7.2", "SOC2", "Changes are monitored and anomalies investigated", ["evidence/siem-runbook.pdf"], True),
    ControlEvidence("A.5.15", "ISO27001", "Access control policy exists and is enforced", ["evidence/access-policy.docx"], True),
    ControlEvidence("A.8.16", "ISO27001", "Monitoring activities are defined", ["evidence/monitoring-standard.docx"], False),
    ControlEvidence("DE.CM-01", "NIST-CSF", "Networks are monitored for anomalies", ["evidence/network-detection.yaml"], True),
    ControlEvidence("OWASP-A05", "OWASP-ASVS", "Security misconfiguration controls are validated", ["evidence/hardening-audit.json"], True),
]


automaton = SecurityComplianceAutomaton(evidence)
print(json.dumps({"summary": automaton.summarize(), "gate": automaton.gate()}, indent=2))
```

### Operational Telemetry
- Track coverage by framework, control family, and technical validation depth.
- Measure the percentage of controls supported by adversarial testing rather than documentation only.
- Record stale evidence age and force refresh before audit or customer attestation deadlines.
- Quantify control contradictions where policy states pass but exercises or scans prove failure.

### Analyst Questions
- What assumption inside AS6 would most likely fail if the environment changed today?
- Which asset, identity, or control in AS6 currently has the highest attacker value relative to monitoring depth?
- What evidence would falsify the current confidence level of AS6 outputs?
- Which dependency outside AS6 must remain healthy for this module to stay trustworthy?

### Execution Sequence
1. Validate incoming context for freshness, ownership, and trustworthiness.
2. Run the module-specific reasoning pass with explicit safety and evidence constraints.
3. Emit both technical outputs and operational decisions rather than raw observations alone.
4. Route follow-on work to adjacent modules using structured handoff data, not prose only.
5. Record telemetry, assumptions, and residual uncertainty for later review.
6. Trigger revalidation whenever new attack evidence, control drift, or governance exceptions appear.

### Integration Points
- Consumes AS3 control plans, AS4 remediation verification, and AS5 purple-team evidence.
- Feeds leadership with residual-risk and compliance-readiness status grounded in technical truth.
- Feeds AS1 and AS4 when evidence reveals unknown assets or untracked remediation obligations.
- Completes the loop by turning governance gaps into new technical objectives for the whole APEX system.

### Red / Blue Artifacts Produced
- AS6 operational summary suitable for incident command, engineering, and governance review.
- Machine-readable outputs that can be consumed by the next module without manual translation.
- Prioritized action items that distinguish urgent operational fixes from structural program improvements.
- Evidence notes explaining what is known, what is inferred, and what still requires validation.

### Review Cadence
- Re-run immediately after material architecture change, acquisition, or internet exposure expansion.
- Re-run after any critical or high exploitability finding is patched or compensated.
- Re-run before major audits, customer attestations, or executive risk reviews.
- Re-run after purple exercises, incidents, or threat-intelligence changes reveal new tradecraft.

### Escalation Criteria
- Escalate when confidence is low but blast radius is high.
- Escalate when multiple modules disagree about whether risk is closed.
- Escalate when technical truth contradicts policy, waiver, or audit narratives.
- Escalate when the same weakness repeatedly reappears after previous closure claims.

### Failure Modes Prevented by Fusion
- Single-tool tunnel vision that optimizes one phase while creating silent exposure in another.
- Defensive fixes that ignore realistic adversary sequencing and therefore collapse under chained exploitation.
- Offensive findings that lack control mapping, ownership, patch sequencing, or measurable verification.
- Compliance artifacts that look complete on paper but fail when attacked by an adversary who understands system drift.

## Cross-Module Integration

### Cascade 1 — Recon to Resilience
- AS1 detects that an internet-facing identity API shares a trust path with a regulated payments service.
- AS2 proves a plausible path: initial foothold, IDOR expansion, privilege escalation, secrets access, exfiltration.
- AS3 redesigns the path with phishing-resistant MFA, service identity isolation, segmentation, and DLP checkpoints.
- AS4 accelerates patching for the weak links and records verification requirements that include exploit replay.
- AS5 reruns the sequence as a purple exercise to verify the chain is now broken earlier and louder.
- AS6 updates SOC2, ISO, NIST, and OWASP evidence using the same technical artifacts that proved closure.

### Cascade 2 — CVE to Control Waiver to Proof
- AS4 receives a critical CVE with no immediate vendor patch for an internet-facing edge component.
- AS1 confirms the component sits on a high-value ingress path and touches regulated traffic.
- AS2 models how the CVE could be weaponized alongside existing credentials and lateral movement opportunities.
- AS3 designs a temporary control stack: WAF rule, segmentation, egress filter, workload identity restriction, and higher-sensitivity analytics.
- AS5 validates whether those temporary controls detect and block the modeled campaign until patching is possible.
- AS6 records the exception, the compensating controls, the purple-team proof, and the eventual patch verification trail.

### Cascade 3 — Compliance Claim to Adversarial Truth
- AS6 encounters a control statement claiming privileged access is tightly restricted and monitored.
- AS1 reveals orphaned privileged identities and an undocumented admin jump path.
- AS2 converts that drift into a likely privilege abuse chain and shows how an adversary could capitalize on the mismatch.
- AS5 runs the ATT&CK sequence and demonstrates that monitoring only catches the final action, not the escalation steps.
- AS3 redesigns the admin tier and AS4 creates remediation work for identity cleanup and host hardening.
- AS6 downgrades the compliance claim from pass to remediate until technical evidence and re-simulation prove the gap closed.

### Cascade 4 — Attack Surface Drift to Continuous Assurance
- AS1 notices a new service and network exposure that bypassed standard onboarding.
- AS4 automatically adds discovery scans and configuration review to the backlog.
- AS2 models whether the new service can serve as a shortcut into existing crown-jewel assets.
- AS3 injects provisional zero-trust controls so the surface is denied-by-default while ownership and design catch up.
- AS5 schedules a targeted exercise focusing on the new trust boundary and adjacent identities.
- AS6 links the drift event to change-management and access-control evidence, ensuring the governance record reflects reality.

## Decision Tree

```text
START
  │
  ├── Is the mission about understanding what exists, what is exposed, or where trust boundaries leak?
  │      └── YES → AS1 Unified Threat Landscape
  │
  ├── Is the mission about proving reachability, chaining weaknesses, or validating adversary success paths?
  │      └── YES → AS2 Autonomous Penetration Engine
  │
  ├── Is the mission about designing controls, segmentation, identity boundaries, or defense layers?
  │      └── YES → AS3 Defense-in-Depth Architect
  │
  ├── Is the mission about scanner findings, CVEs, patching, verification, or backlog prioritization?
  │      └── YES → AS4 Vulnerability Lifecycle Manager
  │
  ├── Is the mission about purple-team exercises, ATT&CK simulation, telemetry validation, or adversary emulation?
  │      └── YES → AS5 Adversary Simulation Framework
  │
  ├── Is the mission about SOC2, ISO 27001, NIST, OWASP, audit evidence, or control gating?
  │      └── YES → AS6 Security Compliance Automaton
  │
  └── If the mission spans offense and defense simultaneously:
         1. Start with AS1 if topology confidence is weak
         2. Continue with AS2 to prove or refute exploitability
         3. Feed the result into AS3 for layered control design
         4. Route all findings to AS4 for remediation governance
         5. Validate with AS5 under ATT&CK-aligned exercise conditions
         6. Close the loop in AS6 with live evidence and residual-risk status
```
## Operating Doctrine

- Never separate offensive proof from defensive consequence. If an exploit is discovered, a control decision must follow immediately.
- Never accept scanner severity without reachability, adversary value, and blast radius context.
- Never accept compliance evidence that has not survived adversarial scrutiny or technical validation.
- Prefer smallest-safe proof over maximal impact. Security maturity comes from truth, not spectacle.
- Use ATT&CK as a grammar, not a vanity matrix. Coverage means the organization can detect or stop the technique, not merely name it.
- Measure closure only when technical, operational, and governance signals all agree the risk changed.

## Quick Reference Card

```text
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                 APEX-SECURITY CARD                                 ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║ AS1  Unified Threat Landscape      → Build asset, identity, and exposure truth     ║
║ AS2  Autonomous Penetration Engine → Prove real attack paths with guardrails       ║
║ AS3  Defense-in-Depth Architect    → Design layered controls and zero-trust policy ║
║ AS4  Vulnerability Lifecycle       → Triage, patch, compensate, verify             ║
║ AS5  Adversary Simulation          → Purple-team realistic ATT&CK exercises        ║
║ AS6  Compliance Automaton          → Map live evidence to SOC2/ISO/NIST/OWASP     ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║ Default Loop: AS1 → AS2 → AS3 → AS4 → AS5 → AS6 → back to AS1                      ║
║ Prime Metric: residual risk after adversarial validation                            ║
║ Kill Switch: production execution blocked unless explicitly authorized              ║
║ Success Condition: attack path broken, telemetry validated, evidence updated        ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```
## Output Expectations

- Every offensive conclusion must name the affected asset, required foothold, likely adversary objective, and defensive implication.
- Every defensive recommendation must specify whether it is preventive, detective, responsive, or compensating.
- Every remediation item must include owner, due date logic, verification method, and evidence target.
- Every compliance statement must link to live technical proof rather than stand alone as narrative.
- Every exercise plan must identify ATT&CK techniques, expected telemetry, blocking controls, and closure criteria.

