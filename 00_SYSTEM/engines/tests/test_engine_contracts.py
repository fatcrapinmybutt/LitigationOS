"""
Contract tests for engine public APIs.

These tests verify that engine classes can be imported and instantiated
through the public __init__.py interface. They do NOT test engine
internals — only the module boundary contract.
"""

import sys
from pathlib import Path

import pytest

# Add 00_SYSTEM to path for import resolution
_system_dir = str(Path(__file__).resolve().parent.parent.parent)
if _system_dir not in sys.path:
    sys.path.insert(0, _system_dir)


class TestEngineImports:
    """Contract: all engines importable from the package __init__.py."""

    def test_import_nexus(self):
        from engines.nexus import NexusEngine
        assert NexusEngine is not None

    def test_import_chimera(self):
        from engines.chimera import ChimeraEngine
        assert ChimeraEngine is not None

    def test_import_chronos(self):
        from engines.chronos import ChronosEngine
        assert ChronosEngine is not None

    def test_import_cerberus(self):
        from engines.cerberus import CerberusEngine
        assert CerberusEngine is not None

    def test_import_from_top_level(self):
        """All 4 engines importable from engines package directly."""
        from engines import NexusEngine, ChimeraEngine, ChronosEngine, CerberusEngine
        assert all([NexusEngine, ChimeraEngine, ChronosEngine, CerberusEngine])


class TestGetEngine:
    """Contract: get_engine() factory returns correct engine instances."""

    def test_get_nexus(self):
        from engines import get_engine
        engine = get_engine("nexus")
        from engines.nexus import NexusEngine
        assert isinstance(engine, NexusEngine)

    def test_get_chimera(self):
        from engines import get_engine
        engine = get_engine("chimera")
        from engines.chimera import ChimeraEngine
        assert isinstance(engine, ChimeraEngine)

    def test_get_chronos(self):
        from engines import get_engine
        engine = get_engine("chronos")
        from engines.chronos import ChronosEngine
        assert isinstance(engine, ChronosEngine)

    def test_get_cerberus(self):
        from engines import get_engine
        engine = get_engine("cerberus")
        from engines.cerberus import CerberusEngine
        assert isinstance(engine, CerberusEngine)

    def test_case_insensitive(self):
        from engines import get_engine
        engine = get_engine("NEXUS")
        from engines.nexus import NexusEngine
        assert isinstance(engine, NexusEngine)

    def test_unknown_engine_raises(self):
        from engines import get_engine
        with pytest.raises(KeyError, match="Unknown engine"):
            get_engine("nonexistent_engine")


class TestEngineAll:
    """Contract: __all__ is defined and complete."""

    def test_engines_has_all(self):
        import engines
        assert hasattr(engines, "__all__")
        assert "NexusEngine" in engines.__all__
        assert "get_engine" in engines.__all__

    def test_nexus_has_all(self):
        import engines.nexus as m
        assert hasattr(m, "__all__")
        assert "NexusEngine" in m.__all__

    def test_chimera_has_all(self):
        import engines.chimera as m
        assert hasattr(m, "__all__")
        assert "ChimeraEngine" in m.__all__

    def test_chronos_has_all(self):
        import engines.chronos as m
        assert hasattr(m, "__all__")
        assert "ChronosEngine" in m.__all__

    def test_cerberus_has_all(self):
        import engines.cerberus as m
        assert hasattr(m, "__all__")
        assert "CerberusEngine" in m.__all__
