#!/usr/bin/env python3
"""
FRED PRIME Skill Registry & Capability Inventory
Lists all available skills, modules, and capabilities in the litigation system.
"""

import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse


class SkillDiscovery:
    """Discovers and catalogs all available skills in the FRED PRIME system."""

    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self.skills: Dict[str, Dict[str, Any]] = {}

    def extract_docstring(self, file_path: Path) -> Optional[str]:
        """Extract module docstring from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                docstring = ast.get_docstring(tree)
                return docstring.strip() if docstring else None
        except Exception:
            return None

    def extract_classes_and_functions(self, file_path: Path) -> Dict[str, List[str]]:
        """Extract class and function names from a Python file."""
        classes = []
        functions = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        classes.append(node.name)
                    elif isinstance(node, ast.FunctionDef):
                        if not node.name.startswith('_'):  # Skip private functions
                            functions.append(node.name)
        except Exception:
            pass
        return {"classes": classes, "functions": functions}

    def categorize_module(self, file_path: Path) -> str:
        """Categorize module based on directory structure."""
        parts = file_path.relative_to(self.root_path).parts
        if len(parts) > 1:
            return parts[0]
        return "root"

    def get_module_purpose(self, file_path: Path, category: str) -> str:
        """Determine module purpose based on name and category."""
        name = file_path.stem.lower()

        purpose_map = {
            # Core functionality
            "build_system": "Build system definition and manifest generation",
            "codex_brain": "Core codex intelligence and coordination",
            "codex_patch_manager": "System update and patch management",
            "codex_manifest": "Module manifest generation and validation",
            "codex_guardian": "System integrity and validation",
            "codex_supreme": "Supreme codex controller",

            # Evidence and document handling
            "organize_drive": "Evidence intake, sorting, and organization",
            "epoch_unpacker_engine_v1": "OCR, exhibit tagging, and audit trail",
            "zip_validator": "ZIP file validation and integrity checking",
            "binder_builder": "Legal binder assembly and generation",
            "tab_forger": "Binder tab generation",

            # Engines
            "litigation_core_engine_v_9999_full": "Full litigation core engine",
            "litigation_core_engine_v9999": "Litigation core processing",
            "mbp_omnia_engine": "Omnia engine for comprehensive processing",
            "document_needs_engine_v9999": "Document needs analysis and generation",
            "scan_engine": "Document scanning and intake",
            "press_draft_engine": "Press release and media draft generation",
            "fusion_engine": "Timeline fusion and synchronization",
            "warboard_engine": "Litigation warboard visualization",
            "custody_interference_engine": "Custody interference tracking",

            # FOIA and discovery
            "autopacker": "FOIA request autopacking",
            "video_request_builder": "Video evidence FOIA request builder",

            # Motion and filing generation
            "emergency_injunction": "Emergency injunction motion generation",
            "protective_order": "Protective order motion generation",
            "complaint_generator": "Federal complaint generation",
            "notice_of_claim": "Notice of claim generation",

            # Analysis tools
            "contradiction_matrix": "Contradiction detection and analysis",
            "ai_entity_review": "AI-powered entity relationship analysis",
            "benchbook_loader": "Michigan benchbook text extraction",

            # Timeline and scheduling
            "builder": "Timeline building and management",
            "scheduler": "Court date and deadline scheduling",

            # Warboard and visualization
            "svg_builder": "SVG visualization builder",
            "svg_motion_binder": "SVG motion binder generation",
            "ppo_warboard": "PPO case warboard",
            "warboard_matrix_export": "Warboard matrix export",

            # Utilities
            "fts_cli": "Full-text search CLI",
            "gdrive_sync": "Google Drive synchronization",
            "tarball": "Archive creation and management",
            "stack_dispatcher": "Form stack dispatch management",
            "misconduct_letter": "Judicial misconduct letter generation",
            "entity_suppression_feed": "Entity suppression tracking",
            "judge_sim_ladas_hoopes_v1": "Judge behavior simulation",

            # GUI
            "frontend": "GUI frontend interface",

            # Data models
            "models": "Data models and schema definitions",
        }

        return purpose_map.get(name, f"Module in {category} subsystem")

    def scan_repository(self) -> None:
        """Scan the repository for all Python modules and catalog them."""
        python_files = list(self.root_path.rglob("*.py"))

        for file_path in python_files:
            # Skip test files, __pycache__, venv, etc.
            if any(skip in str(file_path) for skip in ['__pycache__', '.git', 'venv', 'test_']):
                continue

            # Skip __init__.py files
            if file_path.name == '__init__.py':
                continue

            relative_path = str(file_path.relative_to(self.root_path))
            category = self.categorize_module(file_path)

            skill_info = {
                "name": file_path.stem,
                "path": relative_path,
                "category": category,
                "purpose": self.get_module_purpose(file_path, category),
                "docstring": self.extract_docstring(file_path),
            }

            # Extract code structure
            structure = self.extract_classes_and_functions(file_path)
            if structure["classes"] or structure["functions"]:
                skill_info["structure"] = structure

            self.skills[relative_path] = skill_info

    def get_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group skills by category."""
        categories: Dict[str, List[Dict[str, Any]]] = {}
        for skill in self.skills.values():
            cat = skill["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(skill)
        return categories

    def print_skills(self, format: str = "text") -> None:
        """Print all skills in the specified format."""
        if format == "json":
            print(json.dumps(self.skills, indent=2))
        elif format == "summary":
            self._print_summary()
        else:
            self._print_detailed()

    def _print_summary(self) -> None:
        """Print a summary view of all skills."""
        categories = self.get_categories()

        print("=" * 80)
        print("FRED PRIME LITIGATION OS - SKILLS REGISTRY")
        print("=" * 80)
        print(f"\nTotal Skills: {len(self.skills)}")
        print(f"Total Categories: {len(categories)}\n")

        # Category overview
        for category, skills in sorted(categories.items()):
            print(f"\n{category.upper()} ({len(skills)} modules)")
            print("-" * 60)
            for skill in sorted(skills, key=lambda x: x["name"]):
                print(f"  • {skill['name']:<35} - {skill['purpose']}")

    def _print_detailed(self) -> None:
        """Print detailed view of all skills."""
        categories = self.get_categories()

        print("=" * 80)
        print("FRED PRIME LITIGATION OS - DETAILED SKILLS INVENTORY")
        print("=" * 80)
        print(f"\nTotal Skills Discovered: {len(self.skills)}")
        print(f"Categories: {len(categories)}\n")

        for category, skills in sorted(categories.items()):
            print(f"\n{'=' * 80}")
            print(f"CATEGORY: {category.upper()}")
            print(f"{'=' * 80}\n")

            for skill in sorted(skills, key=lambda x: x["name"]):
                print(f"Module: {skill['name']}")
                print(f"Path: {skill['path']}")
                print(f"Purpose: {skill['purpose']}")

                if skill.get("docstring"):
                    print(f"Description: {skill['docstring'][:150]}...")

                if skill.get("structure"):
                    structure = skill["structure"]
                    if structure["classes"]:
                        print(f"Classes: {', '.join(structure['classes'][:5])}")
                    if structure["functions"]:
                        print(f"Functions: {', '.join(structure['functions'][:5])}")

                print("-" * 80)

    def save_registry(self, output_path: Path) -> None:
        """Save the skills registry to a JSON file."""
        registry = {
            "system": "FRED PRIME Litigation OS",
            "total_skills": len(self.skills),
            "categories": list(self.get_categories().keys()),
            "skills": self.skills,
            "generated_at": str(Path.cwd()),
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)

        print(f"\nSkills registry saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="List all available skills in FRED PRIME Litigation OS"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "summary"],
        default="summary",
        help="Output format (default: summary)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save skills registry to JSON file"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).parent,
        help="Root path to scan (default: current directory)"
    )

    args = parser.parse_args()

    # Discover skills
    discovery = SkillDiscovery(args.path)
    discovery.scan_repository()

    # Print skills
    discovery.print_skills(format=args.format)

    # Save to file if requested
    if args.output:
        discovery.save_registry(args.output)


if __name__ == "__main__":
    main()
