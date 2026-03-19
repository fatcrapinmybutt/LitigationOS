# Authority Lane — 7 Agents

## AGENT:AUTH_HARVESTER
- **Role**: Pull official sources (MCR/MCL/MRE, benchbooks, SCAO forms, local AO)
- **Outputs**: Snapshot files + SHA-256 hashes

## AGENT:AUTH_NORMALIZER
- **Role**: Normalize citations, split into shards, build inverted index
- **Outputs**: Normalized citation shards + inverted index

## AGENT:PINPOINT_ENGINE
- **Role**: Produce pinpoints (rule subsections, statute subsections, page/paragraph for PDFs)
- **Outputs**: Pin cite records: `{authority_id, section, subsection, pinpoint}`

## AGENT:VEHICLE_SELECTOR
- **Role**: Map relief to vehicle candidates across trial/COA/MSC/JTC
- **Outputs**: VehicleMap entries with all mandatory fields

## AGENT:FORM_FINDER
- **Role**: Map vehicle to required SCAO/MC/FOC forms
- **Outputs**: Form list with download links and instructions

## AGENT:LOCAL_RULES_SCOUT
- **Role**: Fetch Muskegon local AO / filing procedures & constraints
- **Outputs**: Local rules digest with e-filing requirements

## AGENT:STANDARDS_ENGINE
- **Role**: Generate standards of review / burdens / elements grids
- **Outputs**: Standards grid: `{standard, burden, elements, citations}`
