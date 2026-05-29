"""Tests for CJK tokenization and length-normalised TF-IDF scoring."""
from note_model import NoteManager
from search_engine import SearchEngine


def test_single_cjk_char_and_bigram_kept(tmp_path):
    se = SearchEngine(tmp_path / "i.json")
    toks = se.tokenize("北京欢迎")
    assert "北" in toks and "京" in toks      # single CJK chars retained
    assert "北京" in toks                       # bigram fallback


def test_latin_single_letters_retained(tmp_path):
    se = SearchEngine(tmp_path / "i.json")
    toks = se.tokenize("a quick brown fox")
    assert "a" in toks and "quick" in toks


def test_single_cjk_query_matches(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    n = nm.create_note("城市", "北京是中国的首都")
    se = SearchEngine(tmp_path / "i.json")
    se.build_index(nm.notes)
    hits = [nid for nid, _ in se.search("京", nm.notes)]
    assert n.id in hits


def test_length_normalisation_favours_short_doc(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    short = nm.create_note("short", "alpha beta")
    long = nm.create_note("long", "alpha " + "filler " * 60)
    nm.create_note("other", "gamma delta")  # lacks 'alpha' so its idf > 0
    se = SearchEngine(tmp_path / "i.json")
    se.build_index(nm.notes)
    assert se.calculate_tf_idf("alpha", short.id) > se.calculate_tf_idf("alpha", long.id)
