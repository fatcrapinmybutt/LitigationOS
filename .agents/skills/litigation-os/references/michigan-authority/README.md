# Michigan Authority Atlas & Filing Lanes

## Canonical Sources

| Source | Abbrev | Type | Trust Level |
|--------|--------|------|-------------|
| Michigan Court Rules | MCR | Procedural | Authoritative |
| Michigan Compiled Laws | MCL | Statutory | Authoritative |
| Michigan Rules of Evidence | MRE | Evidentiary | Authoritative |
| MJI Benchbooks | MJI | Advisory | High |
| SCAO Forms + Instructions | SCAO | Administrative | Authoritative |
| Local Administrative Orders | Local AO | Procedural | Authoritative (local) |

## Citation Rules

- Always cite to the most specific subsection: `MCR 3.206(C)(1)(a)` not `MCR 3.206`
- Case law: `Name v Name, xxx Mich App xxx; xxx NW2d xxx (year)` with specific page
- Pin cites include: rule subsections, statute subsections, page/paragraph for PDFs

## No-Hallucination Rule

If a proposition cannot be cited:
1. Mark it `UNKNOWN` (not "probably")
2. Generate a Gap Ticket (EGCP v2) with acquisition plan
3. Proceed only with what is grounded

## Filing Lanes

See [mcr-reference.md](mcr-reference.md) for key rules per lane.
See [vehicle-library.md](vehicle-library.md) for VehicleMap templates.

### Trial Court / Family Court (14th Circuit + 60th District)
Motion to modify custody/PT, contempt, enforce, disqualify, transcripts, proposed orders, POS, PPO

### Court of Appeals (COA)
Application for leave (MCR 7.205), claim of appeal (MCR 7.204), original action (MCR 7.206), stay (MCR 7.209)

### Michigan Supreme Court (MSC)
Application for leave (MCR 7.305), immediate consideration (MCR 7.311), supplemental authority (MCR 7.312)

### Judicial Tenure Commission (JTC)
Verified complaint, exhibit binder, narrative (record-based, not opinion-based)

### Federal (WDMI)
42 USC §1983, §1985, Ex Parte Young, Monell county liability

## Authority Snapshot Schema

```json
{
  "authority_id": "MCR_3.206",
  "section": "3",
  "subsection": "C",
  "pinpoint": "(1)(a)",
  "snapshot_date": "2026-02-16",
  "hash": "sha256:..."
}
```
