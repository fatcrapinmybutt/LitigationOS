"""Self-Documenting System — Auto-generates reference docs from code.

Introspects the litigation_context.db schema, engine directories, and
SINGULARITY skill files to produce always-current Markdown reference
documentation. Uses ast.parse for safe Python introspection.

Usage:
    from engines.self_doc import SelfDocumenter

    doc = SelfDocumenter()
    doc.generate_all("04_ANALYSIS/REFERENCE/")
"""

__version__ = "1.0.0"

from .documenter import SelfDocumenter

__all__ = ["SelfDocumenter"]
