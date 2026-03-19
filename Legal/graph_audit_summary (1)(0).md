# Graph Audit — Litigation OS

## Counts

- **Nodes**: 26810
- **Edges**: 57808
- **Invalid Edges**: 0
- **Dup Node Ids**: 0
- **Dup Edges**: 0
- **Orphan Nodes**: 15305
- **Empty Labels**: 0
- **Too Long Labels**: 33
- **Authority Nodes**: 15717
- **Authority Edges**: 31788

## Top Node Types

- node: 26810

## Top Edge Labels

- seeks: 12790
- categorized_as: 11095
- cites: 9280
- part_of: 7263
- member_of: 6646
- through: 6214
- venue: 2675
- belongs_to: 533
- includes: 500
- authority_of: 235
- related_to: 74
- on: 47
- crosswalk: 43
- involves: 40
- implicates: 35
- category_of: 31
- index_of: 28
- guided_by: 27
- references: 27
- case_of: 20
- authorized_by: 17
- next: 17
- interprets: 17
- requires: 15
- controlled_by: 15
- includes_step: 15
- actor_link: 13
- ethics_related: 12
- petal: 11
- trigger: 9
- controls: 9
- chapter_of: 8
- topic_of: 7
- responds_to: 6
- section_of: 6
- supported_by: 6
- instruction_of: 5
- governed_by: 5
- stage_of: 5
- jurisdiction_of: 3
- violation_pathway: 1
- nan: 1
- remedy_against: 1
- manifests: 1

## Top-Degree Nodes (25)

- Authority (`hub::authority`) — deg 7886
- MCR Wheel (`hub_MCR_Wheel`) — deg 5519
- Violation (`hub::violation`) — deg 3006
- MCL Wheel (`hub_MCL_Wheel`) — deg 1781
- MCR 2.119 (`mcr::2.119`) — deg 1163
- sanctions (`remedy::d5301e3e6d`) — deg 1141
- MCL 722.27a(9) (`mcl::722.27a(9)`) — deg 1140
- MCR 3.207(B) (`mcr::3.207(B)`) — deg 1140
- Circuit Court – Family Division (`venue::Circuit Court – Family Division`) — deg 826
- MCR 3.705 (`mcr::3.705`) — deg 819
- MCL 600.2950a (`mcl::600.2950a`) — deg 819
- fees (`remedy::9ca93831c6`) — deg 819
- Motion to Terminate/Modify PPO (`procedure::35aff90572`) — deg 819
- MCL Other (`hub_MCL_Other`) — deg 783
- MCL 600 — Revised Judicature Act (Courts & Procedure) (`hub_MCL_600_Revised_Judicature_Act_Courts_Procedure_`) — deg 736
- MCL 600.2918 (`mcl::600.2918`) — deg 685
- MCL 600.5731 (`mcl::600.5731`) — deg 673
- Injunction (`remedy::Injunction`) — deg 673
- Verified Complaint for Illegal Eviction/Conversion (`procedure::Verified Complaint for Illegal Eviction/Conversion`) — deg 673
- Treble damages (`remedy::Treble damages`) — deg 673
- Return of possession (`remedy::Return of possession`) — deg 673
- District Court (LT) or Circuit Court (damages) (`venue::District Court (LT) or Circuit Court (damages)`) — deg 673
- Immediate TRO restoring access (`relief::Immediate TRO restoring access`) — deg 673
- Emergency TRO (MCR 3.310) (`procedure::Emergency TRO (MCR 3.310)`) — deg 673
- Damages + costs (`relief::Damages + costs`) — deg 673

## Notes

- Orphan nodes = nodes with no incident edges.
- Invalid edges = edges where source or target does not exist in nodes.
- Duplicate edges = exact same (source, target, label) appearing more than once.
- Empty labels = nodes lacking a readable label; consider normalizing.
- Very long labels (>200 chars) may hurt readability; consider shortening display names.
- Authority anchors indicate MCR/MCL/Canon/Benchbook/FRCP/LCivR/SCAO presence in graph.