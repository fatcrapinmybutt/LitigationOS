# FRED PRIME Skills Inventory

## Overview

This document provides a comprehensive inventory of all available skills, modules, and capabilities in the FRED PRIME Litigation OS system.

## Total System Capabilities

- **Total Skills**: 56 modules
- **Total Categories**: 20 functional areas
- **System**: FRED PRIME Litigation OS

## Using the Skills Registry

### List All Skills (Summary View)

```bash
python list_skills.py --format summary
```

### Detailed Skills Information

```bash
python list_skills.py --format text
```

### Export Skills to JSON

```bash
python list_skills.py --format json --output skills_registry.json
```

## Skills by Category

### 1. BINDER (1 module)
- **tab_forger** - Binder tab generation

### 2. CLI (1 module)
- **generate_manifest** - CLI manifest generation

### 3. CONTRADICTIONS (1 module)
- **contradiction_matrix** - Contradiction detection and analysis

### 4. ENTITY_TRACE (1 module)
- **ai_entity_review** - AI-powered entity relationship analysis

### 5. FEDERAL (1 module)
- **complaint_generator** - Federal complaint generation

### 6. FOIA (2 modules)
- **autopacker** - FOIA request autopacking
- **video_request_builder** - Video evidence FOIA request builder

### 7. GUI (2 modules)
- **entity_suppression_feed** - Entity suppression tracking
- **frontend** - GUI frontend interface

### 8. MIFILE (1 module)
- **stack_dispatcher** - Form stack dispatch management

### 9. MODULES (4 modules)
- **benchbook_loader** - Michigan benchbook text extraction
- **codex_guardian** - System integrity and validation
- **codex_manifest** - Module manifest generation and validation
- **codex_supreme** - Supreme codex controller

### 10. MOTIONS (2 modules)
- **emergency_injunction** - Emergency injunction motion generation
- **protective_order** - Protective order motion generation

### 11. NOTICES (1 module)
- **notice_of_claim** - Notice of claim generation

### 12. PRESS (1 module)
- **press_draft_engine** - Press release and media draft generation

### 13. ROOT (22 modules)

Core system modules:

- **BINDER_BUILDER** - Legal binder assembly and generation
- **Build_And_Upload_Master_Litigation_Pack_Z** - Master litigation pack builder
- **DOCUMENT_NEEDS_ENGINE_v9999** - Document needs analysis and generation
- **EPOCH_UNPACKER_ENGINE_v1** - OCR, exhibit tagging, and audit trail
- **FRED_Codex_Bootstrap** - System bootstrap and initialization
- **LITIGATION_CORE_ENGINE_v9999** - Litigation core processing
- **MBP_Omnia_Engine** - Omnia engine for comprehensive processing
- **ZIP_VALIDATOR** - ZIP file validation and integrity checking
- **build_system** - Build system definition and manifest generation
- **codex_brain** - Core codex intelligence and coordination
- **codex_patch_manager** - System update and patch management
- **firstimport** - Initial system import utilities
- **fts_cli** - Full-text search CLI
- **gdrive_sync** - Google Drive synchronization
- **judge_sim_ladas_hoopes_v1** - Judge behavior simulation
- **list_skills** - Skills inventory and discovery tool
- **litigation_core_engine_v_9999_full** - Full litigation core engine
- **organize_drive** - Evidence intake, sorting, and organization
- **tarball** - Archive creation and management

### 14. SCANNER (1 module)
- **scan_engine** - Document scanning and intake

### 15. SCHEDULING (1 module)
- **scheduler** - Court date and deadline scheduling

### 16. SCRIPTS (1 module)
- **generate_manifest** - Script-based manifest generation

### 17. SRC (4 modules)
- **env** - Environment configuration
- **models** - Data models and schema definitions (forms and knowledge)
- **b978fb447583_initial** - Initial database migration

### 18. TIMELINE (2 modules)
- **builder** - Timeline building and management
- **fusion_engine** - Timeline fusion and synchronization

### 19. VIOLATIONS (1 module)
- **misconduct_letter** - Judicial misconduct letter generation

### 20. WARBOARD (6 modules)
- **custody_interference_engine** - Custody interference tracking
- **ppo_warboard** - PPO case warboard
- **svg_builder** - SVG visualization builder
- **svg_motion_binder** - SVG motion binder generation
- **warboard_engine** - Litigation warboard visualization
- **warboard_matrix_export** - Warboard matrix export

## Key Capabilities by Function

### Evidence Management
- organize_drive - Evidence intake and organization
- EPOCH_UNPACKER_ENGINE_v1 - OCR and exhibit tagging
- scan_engine - Document scanning
- ZIP_VALIDATOR - Archive validation

### Document Generation
- BINDER_BUILDER - Binder assembly
- tab_forger - Tab generation
- emergency_injunction - Motion generation
- protective_order - Motion generation
- complaint_generator - Federal complaints
- notice_of_claim - Notice generation
- press_draft_engine - Press releases

### Analysis & Intelligence
- contradiction_matrix - Contradiction detection
- ai_entity_review - Entity analysis
- benchbook_loader - Legal research
- judge_sim_ladas_hoopes_v1 - Judge simulation

### FOIA & Discovery
- autopacker - FOIA request automation
- video_request_builder - Video evidence requests

### Visualization & Reporting
- warboard_engine - Case visualization
- svg_builder - SVG graphics
- ppo_warboard - PPO tracking
- custody_interference_engine - Custody tracking

### System Management
- codex_brain - Core intelligence
- codex_guardian - System integrity
- codex_supreme - Supreme controller
- build_system - Build management
- codex_patch_manager - Update management

### Timeline & Scheduling
- builder - Timeline construction
- fusion_engine - Timeline synchronization
- scheduler - Court scheduling

## File Locations

All skills are Python modules located throughout the repository:

```
/home/runner/work/the_manbearpig/the_manbearpig/
├── list_skills.py (this tool)
├── skills_registry.json (generated registry)
├── [module_name].py (root modules)
└── [category]/[module_name].py (categorized modules)
```

## API Usage

### Programmatic Access

```python
from list_skills import SkillDiscovery
from pathlib import Path

# Initialize discovery
discovery = SkillDiscovery(Path.cwd())

# Scan repository
discovery.scan_repository()

# Access skills
all_skills = discovery.skills
categories = discovery.get_categories()

# Print or process
for skill_path, skill_info in all_skills.items():
    print(f"{skill_info['name']}: {skill_info['purpose']}")
```

## Registry File Format

The generated `skills_registry.json` contains:

```json
{
  "system": "FRED PRIME Litigation OS",
  "total_skills": 56,
  "categories": [...],
  "skills": {
    "path/to/module.py": {
      "name": "module_name",
      "path": "relative/path",
      "category": "category_name",
      "purpose": "Module purpose",
      "docstring": "Module documentation",
      "structure": {
        "classes": ["ClassName", ...],
        "functions": ["function_name", ...]
      }
    }
  }
}
```

## Maintenance

To update the skills registry after adding new modules:

```bash
python list_skills.py --format json --output skills_registry.json
```

The system automatically discovers all Python modules in the repository and categorizes them based on directory structure and naming conventions.

## Integration

The skills registry can be integrated into:

- CI/CD pipelines for validation
- Documentation generation
- Module discovery systems
- GUI interfaces
- API endpoints
- Automated testing frameworks

## Notes

- The skill discovery system ignores test files, `__init__.py` files, and virtual environments
- Skills are automatically categorized based on their directory location
- Module purposes are determined through a combination of naming patterns and docstring analysis
- The system extracts class and function names for detailed capability mapping
