# Michigan Court Filing Framework

A **case-agnostic**, reusable framework for managing litigation filings in
Michigan state courts (Circuit, COA, MSC, District) and extensible to
federal courts (WDMI).

## Quick Start

```python
# 1. Initialize a new case database
python init_case_db.py \
    --case-number "2024-001234-DC" \
    --court "14th Circuit" \
    --judge "Hon. Jane Doe" \
    --plaintiff "John Smith" \
    --defendant "Jane Smith" \
    --db "my_case.db"

# 2. Generate a caption
from caption_generator import generate_caption
caption = generate_caption(case_info, "Motion to Compel Discovery", "circuit")

# 3. Calculate a deadline
from deadline_calculator import calculate_deadline
from datetime import date
deadline = calculate_deadline(date(2025, 6, 1), "MOTION_RESPONSE")

# 4. Run pre-filing QA
from filing_checklist import generate_checklist
checklist = generate_checklist("motion", "circuit", case_info)

# 5. Generate Certificate of Service
from cos_generator import generate_cos
cos = generate_cos(parties_served, "electronic", date.today(), case_info)
```

## Files

| File | Purpose |
|------|---------|
| `filing_db_schema.sql` | SQLite schema for any litigation case database |
| `michigan_format_specs.py` | Pre-loaded format specs for MI courts + WDMI federal |
| `filing_checklist.py` | Pre-filing QA checklist generator by filing type |
| `deadline_calculator.py` | MCR deadline calculator with holiday awareness |
| `caption_generator.py` | Court caption/header generator for all MI courts |
| `cos_generator.py` | Certificate of Service generator |
| `signature_block.py` | Signature block generator (pro se and attorney) |
| `exhibit_indexer.py` | Exhibit index/table generator with Bates ranges |
| `init_case_db.py` | Case database initializer script |

## Design Principles

1. **Case-agnostic** — No hardcoded party names, case numbers, or judges.
2. **Authority-backed** — Every format spec and rule cites an MCR/MCL/LCivR.
3. **Extensible** — Add new courts or jurisdictions by extending the spec dicts.
4. **Standalone modules** — Each `.py` file is independently importable.
5. **CLI-ready** — Each module has a `__main__` block for command-line use.
6. **SQLite best practices** — WAL mode, busy_timeout, cache_size, FTS5 indexes.

## Supported Courts

- Michigan Circuit Court (MCR 2.113, 2.119)
- Michigan Court of Appeals (MCR 7.212)
- Michigan Supreme Court (MCR 7.306, 7.312)
- Michigan District Court (MCR 4.002)
- US District Court, Western District of Michigan (LCivR)

## Dependencies

- Python 3.9+
- No external packages required (stdlib only)
