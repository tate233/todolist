"""BM25 ranking: real ids, title weighting, stable relative order."""
from note_model import NoteManager
from search_engine import SearchEngine


def _engine(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("Python 教程", "学习 python 编程基础", tags=["dev"])
    b = nm.create_note("随笔", "今天提到 python 一次而已", tags=["life"])
    nm.create_note("无关", "completely unrelated content", tags=["x"])
    se = SearchEngine(tmp_path / "i.json")
    se.build_index(nm.notes)
    return nm, se, a, b


def test_bm25_returns_real_ids(tmp_path):
    nm, se, _a, _b = _engine(tmp_path)
    results = se.search_bm25("python", nm.notes)
    assert results
    assert all(nm.get_note(nid) is not None for nid, _ in results)


def test_title_field_weight_boosts(tmp_path):
    nm, se, a, b = _engine(tmp_path)
    scores = dict(se.search_bm25("python", nm.notes))
    assert scores[a.id] > scores[b.id]  # title hit weighted above body-only


def test_bm25_score_positive_for_match(tmp_path):
    nm, se, a, _b = _engine(tmp_path)
    assert se.calculate_bm25("python", a.id) > 0


def test_empty_query(tmp_path):
    nm, se, _a, _b = _engine(tmp_path)
    assert se.search_bm25("", nm.notes) == []
