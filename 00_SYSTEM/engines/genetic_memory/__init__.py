"""Genetic Memory — CORAL-inspired cross-session learning system.

Stores knowledge as evolving 'genes' with confidence scores that grow
through validation and decay through disuse. Supports lineage tracking,
FTS5 search, and automated evolution cycles.

Usage:
    from engines.genetic_memory import GeneticMemory, seed_initial_genes

    mem = GeneticMemory()
    mem.store_gene("fact", "Albert Watson admitted premeditation NS2505044", 0.95)
    genes = mem.recall_genes(gene_type="fact", min_confidence=0.5)
"""

__version__ = "1.0.0"

from .memory import GeneticMemory
from .genes import seed_initial_genes

__all__ = ["GeneticMemory", "seed_initial_genes"]
