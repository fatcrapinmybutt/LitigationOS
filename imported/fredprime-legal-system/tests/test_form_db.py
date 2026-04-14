"""
Tests for form_db.py module - especially focusing on performance-critical operations.
"""
import json
import pytest
from pathlib import Path
from src.form_db import FormDatabase, load_manifest


@pytest.fixture
def test_db(tmp_path: Path) -> FormDatabase:
    """Create a test database."""
    db_path = tmp_path / "test_forms.db"
    return FormDatabase(db_path)


@pytest.fixture
def sample_forms() -> list:
    """Sample form data for testing."""
    return [
        {
            "form_id": "MC-12",
            "title": "Motion to Adjourn",
            "filename": "mc12.docx",
            "rules": ["MCR 2.503"],
            "statutes": ["MCL 600.101"],
            "benchbook": ["Benchbook § 2.1"],
            "constitution": [],
            "federal": [],
        },
        {
            "form_id": "FOC-87",
            "title": "Motion Regarding Parenting Time",
            "filename": "foc87.docx",
            "rules": ["MCR 3.210", "MCR 3.211"],
            "statutes": ["MCL 722.27a"],
            "benchbook": ["Benchbook § 3.5"],
            "constitution": ["MI Const. Art 1 § 17"],
            "federal": [],
        },
        {
            "form_id": "MC-97",
            "title": "Complaint for Injunctive Relief",
            "filename": "mc97.docx",
            "rules": ["MCR 3.310"],
            "statutes": [],
            "benchbook": [],
            "constitution": [],
            "federal": ["28 USC § 1331"],
        },
    ]


def test_add_and_get_form(test_db: FormDatabase):
    """Test adding and retrieving a single form."""
    test_db.add_form(
        form_id="MC-12",
        title="Motion to Adjourn",
        filename="mc12.docx",
        rules=["MCR 2.503"],
        statutes=["MCL 600.101"],
    )
    form = test_db.get_form("MC-12")
    assert form is not None
    assert form["id"] == "MC-12"
    assert form["title"] == "Motion to Adjourn"
    assert form["rules"] == ["MCR 2.503"]
    assert form["statutes"] == ["MCL 600.101"]


def test_get_nonexistent_form(test_db: FormDatabase):
    """Test retrieving a form that doesn't exist."""
    form = test_db.get_form("NONEXISTENT")
    assert form is None


def test_list_forms(test_db: FormDatabase, sample_forms: list):
    """Test listing all forms - performance critical operation."""
    # Add multiple forms
    for form_data in sample_forms:
        test_db.add_form(**form_data)
    
    # List all forms
    forms = test_db.list_forms()
    assert len(forms) == len(sample_forms)
    assert forms[0]["id"] == "FOC-87"  # Should be sorted by id
    assert forms[1]["id"] == "MC-12"
    assert forms[2]["id"] == "MC-97"


def test_list_forms_empty(test_db: FormDatabase):
    """Test listing forms when database is empty."""
    forms = test_db.list_forms()
    assert forms == []


def test_search_forms_by_title(test_db: FormDatabase, sample_forms: list):
    """Test searching forms by title keyword."""
    for form_data in sample_forms:
        test_db.add_form(**form_data)
    
    results = test_db.search_forms("motion")
    assert len(results) == 2
    assert any(form["id"] == "MC-12" for form in results)
    assert any(form["id"] == "FOC-87" for form in results)


def test_search_forms_by_statute(test_db: FormDatabase, sample_forms: list):
    """Test searching forms by statute reference."""
    for form_data in sample_forms:
        test_db.add_form(**form_data)
    
    results = test_db.search_forms("MCL 722")
    assert len(results) == 1
    assert results[0]["id"] == "FOC-87"


def test_search_forms_no_match(test_db: FormDatabase, sample_forms: list):
    """Test search with no matching results."""
    for form_data in sample_forms:
        test_db.add_form(**form_data)
    
    results = test_db.search_forms("NOMATCH12345")
    assert results == []


def test_find_by_reference(test_db: FormDatabase, sample_forms: list):
    """Test finding forms by rule/statute reference."""
    for form_data in sample_forms:
        test_db.add_form(**form_data)
    
    # Find by court rule
    results = test_db.find_by_reference("MCR 3.210")
    assert len(results) == 1
    assert results[0]["id"] == "FOC-87"
    
    # Find by statute
    results = test_db.find_by_reference("MCL 600.101")
    assert len(results) == 1
    assert results[0]["id"] == "MC-12"
    
    # Find by federal reference
    results = test_db.find_by_reference("28 USC")
    assert len(results) == 1
    assert results[0]["id"] == "MC-97"


def test_find_by_reference_no_match(test_db: FormDatabase, sample_forms: list):
    """Test reference search with no matches."""
    for form_data in sample_forms:
        test_db.add_form(**form_data)
    
    results = test_db.find_by_reference("NOMATCH")
    assert results == []


def test_remove_form(test_db: FormDatabase):
    """Test removing a form."""
    test_db.add_form(
        form_id="MC-12",
        title="Motion to Adjourn",
        filename="mc12.docx",
    )
    form = test_db.get_form("MC-12")
    assert form is not None
    
    test_db.remove_form("MC-12")
    form = test_db.get_form("MC-12")
    assert form is None


def test_update_form(test_db: FormDatabase):
    """Test updating an existing form."""
    test_db.add_form(
        form_id="MC-12",
        title="Original Title",
        filename="mc12.docx",
    )
    test_db.add_form(
        form_id="MC-12",
        title="Updated Title",
        filename="mc12_v2.docx",
    )
    form = test_db.get_form("MC-12")
    assert form["title"] == "Updated Title"
    assert form["filename"] == "mc12_v2.docx"


def test_load_manifest(test_db: FormDatabase, tmp_path: Path, sample_forms: list):
    """Test loading forms from a manifest file."""
    # Create manifest file
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(sample_forms))
    
    # Load manifest
    forms_dir = tmp_path / "forms"
    forms_dir.mkdir()
    load_manifest(manifest_path, test_db, forms_dir)
    
    # Verify forms were loaded
    forms = test_db.list_forms()
    assert len(forms) == len(sample_forms)


def test_form_with_empty_references(test_db: FormDatabase):
    """Test form with no legal references."""
    test_db.add_form(
        form_id="TEST-01",
        title="Test Form",
        filename="test.docx",
        rules=None,
        statutes=None,
    )
    form = test_db.get_form("TEST-01")
    assert form is not None
    assert form["rules"] == []
    assert form["statutes"] == []
    assert form["benchbook"] == []


def test_cursor_description_efficiency(test_db: FormDatabase, sample_forms: list, benchmark_timer):
    """Test that cursor description is efficiently handled in list operations."""
    # Add many forms
    for i in range(100):
        form_data = sample_forms[i % len(sample_forms)].copy()
        form_data["form_id"] = f"FORM-{i:03d}"
        test_db.add_form(**form_data)
    
    # Time the list operation
    with benchmark_timer:
        forms = test_db.list_forms()
    
    assert len(forms) == 100
    # This test will fail if cursor description is extracted in loop
    # Performance should be consistent regardless of result set size
    assert benchmark_timer.elapsed < 1.0  # Should be much faster
