# VALIDATION_SUITE — Lints + Gates (v6)

Hard validators:
- Crosswalk schema validity (vehicle_matrix/lanes/*/schemas/*.json)
- DeadlineContractValidate (deadlines/DEADLINE_CONTRACTS.md)
- PacketTemplateExists + PacketPlanValidate (packets/schemas/*)
- RebuttalInput/Output schema validity (rebuttal_compiler/schemas/*)

Reference tool implements fail-closed behavior and produces blockers for missing pins/authority.
