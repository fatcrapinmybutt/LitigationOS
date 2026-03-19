# Path Stability (Autonomous)

Recommended:
1) Choose a stable root: D:\LitigationOS
2) Run: `py scripts\litigationos.py init-config --home D:\LitigationOS`
3) Set env var: `setx LITIGATIONOS_HOME "D:\LitigationOS"`

Optional: CURRENT pointer to most recent cyclepack
- Create directory junction:
  `mklink /J D:\LitigationOS\cyclepacks\CURRENT D:\LITIGATIONOS_HARVEST_CYCLEPACK_YYYYMMDD_HHMMSS`
