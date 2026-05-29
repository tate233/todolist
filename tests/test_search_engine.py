"""Regression tests for SearchEngine.search().

Guards the fix where search() iterated enumerate(notes) (integer indices /
dict keys) instead of notes.items(), which raised AttributeError and returned
bogus integer ids.
"""
import pytest

from note_model import NoteManager
from search_engine import SearchEngine


@pytest.fixture
def engine(tmp_path):
    nm = NoteManager(tmp_path / "notes.db", tmp_path)
    a = nm.create_note("Python 教程", "学习 python 编程", tags=["dev"])
    b = nm.create_note("烹饪", "python is also mentioned here", tags=["food"])
    se = SearchEngine(tmp_path / "index.json")
    se.build_index(nm.notes)
    return nm, se, a, b


def test_search_returns_real_note_ids(engine):
    nm, se, _a, _b = engine
    results = se.search("python", nm.notes)
    ids = [nid for nid, _ in results]
    assert ids
    for nid in ids:
        assert nm.get_note(nid) is not None


def test_title_hit_outranks_content_hit(engine):
    nm, se, a, b = engine
    scores = dict(se.search("python", nm.notes))
    assert scores[a.id] > scores[b.id]


def test_cjk_query_does_not_raise(engine):
    nm, se, _a, _b = engine
    assert isinstance(se.search("教程", nm.notes), list)


def test_empty_query_and_empty_notes(engine):
    nm, se, _a, _b = engine
    assert se.search("", nm.notes) == []
    assert se.search("python", {}) == []
