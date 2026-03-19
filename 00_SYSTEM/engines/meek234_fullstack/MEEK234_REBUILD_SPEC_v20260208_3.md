# MEEK2+MEEK3+MEEK4 Full-Stack Rebuild Pack (v20260208_3)

This pack is an **expanded, crosswired** foundation for MEEK2/MEEK3/MEEK4, including:
- **Schema CSVs** (node/edge/property/enum specs)
- **Catalogs**:
  - `risk_event_types.json` (unified COA/MSC/JTC + trial risks; includes **fastest-cure** fields)
  - `vehicle_types.json` (cross-forum vehicles for MEEK2/3/4)
  - `forum_gate_profiles.json` (presentation gate profiles)
  - `glossary_terms_core.jsonl` (~293 glossary entries)

## Delta from v20260208_2
- Schema expanded with **Court**, **Forum**, **Transcript**, **Recording**, **CurePacket**, **PresentationGateProfile**
- Risk taxonomy expanded to include:
  - COA dismissal-risk engine primitives (docketing statement, deficiency letters, transcript/record gaps)
  - MSC return-without-docketing + strict timeliness primitives
  - JTC milestone + 28-day letter response primitives (Chapter 9)
- Added forum gate profiles for **trial/COA/MSC/JTC**

## Primary build script
`MEEK234_FULLSTACK_REBUILD_v20260208_3.py` (in this ZIP)

> Note: The catalog authority refs are pointers; in LitigationOS, bind them to your local **AuthoritySnapshot** and attach pinpoints.

Generated at: 20260208T000000Z
