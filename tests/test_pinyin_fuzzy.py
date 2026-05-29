"""Pinyin + fuzzy matching helpers and integration with search_fuzzy."""
import pinyin_index
from note_model import NoteManager
from search_engine import SearchEngine


def test_pinyin_full_and_initials():
    assert pinyin_index.to_pinyin("北京") == "beijing"
    assert pinyin_index.to_initials("北京") == "bj"


def test_matches_pinyin():
    assert pinyin_index.matches_pinyin("beijing", "北京游记")
    assert pinyin_index.matches_pinyin("bj", "北京游记")
    assert not pinyin_index.matches_pinyin("shanghai", "北京游记")


def test_edit_distance_and_fuzzy():
    assert pinyin_index.edit_distance("python", "pythn") == 1
    assert pinyin_index.fuzzy_match("pythn", "python", max_distance=1)
    assert not pinyin_index.fuzzy_match("xyz", "python", max_distance=1)


def test_search_fuzzy_recall_pinyin(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    n = nm.create_note("北京游记", "记录北京的行程")
    se = SearchEngine(tmp_path / "i.json")
    se.build_index(nm.notes)
    hits = [nid for nid, _ in se.search_fuzzy("beijing", nm.notes)]
    assert n.id in hits


def test_search_fuzzy_typo(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    n = nm.create_note("Python notes", "python python python")
    se = SearchEngine(tmp_path / "i.json")
    se.build_index(nm.notes)
    hits = [nid for nid, _ in se.search_fuzzy("pythn", nm.notes)]  # one typo
    assert n.id in hits
