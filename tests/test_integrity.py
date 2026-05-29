"""Integrity doctor detects and repairs index drift and dangling links."""
import integrity
from note_model import NoteManager
from search_engine import SearchEngine


def _setup(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    se = SearchEngine(tmp_path / "i.json")
    a = nm.create_note("A", "alpha")
    b = nm.create_note("B", "beta")
    se.build_index(nm.notes)
    return nm, se, a, b


def test_clean_store_reports_ok(tmp_path):
    nm, se, _a, _b = _setup(tmp_path)
    assert integrity.check(nm, se).ok


def test_detects_and_fixes_index_drift(tmp_path):
    nm, se, _a, _b = _setup(tmp_path)
    nm.create_note("C", "gamma")  # added without indexing -> drift
    report = integrity.check(nm, se, fix=False)
    assert report.index_out_of_sync
    fixed = integrity.check(nm, se, fix=True)
    assert fixed.repaired
    assert integrity.check(nm, se).ok


def test_detects_and_prunes_dangling_links(tmp_path):
    nm, se, a, _b = _setup(tmp_path)
    a.links = ["nonexistent-id"]
    report = integrity.check(nm, se, fix=False)
    assert report.dangling_links
    integrity.check(nm, se, fix=True)
    assert "nonexistent-id" not in nm.get_note(a.id).links
