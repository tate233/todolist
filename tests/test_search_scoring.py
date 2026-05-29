"""Regression tests for search scoring landing on real note ids.

Complements test_search_engine.py: focuses on tag weighting and that no
integer (enumerate-index) keys leak into the result set.
"""
from note_model import NoteManager
from search_engine import SearchEngine


def _setup(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("Roadmap", "planning content", tags=["project", "plan"])
    b = nm.create_note("Notes", "misc content", tags=["misc"])
    se = SearchEngine(tmp_path / "i.json")
    se.build_index(nm.notes)
    return nm, se, a, b


def test_tag_hit_scored_on_real_id(tmp_path):
    nm, se, a, _b = _setup(tmp_path)
    scores = dict(se.search("project", nm.notes))
    assert scores.get(a.id, 0) > 0
    assert all(nid in nm.notes for nid in scores)


def test_results_keys_are_strings(tmp_path):
    nm, se, _a, _b = _setup(tmp_path)
    results = se.search("planning", nm.notes)
    assert results
    assert all(isinstance(nid, str) for nid, _ in results)
