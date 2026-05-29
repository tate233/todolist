"""update_document yields the same index as a full rebuild; flush is deferred."""
from note_model import NoteManager
from search_engine import SearchEngine


def test_update_matches_full_rebuild(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("A", "alpha beta", tags=["x"])
    nm.create_note("B", "gamma", tags=["y"])
    se = SearchEngine(tmp_path / "i.json")
    se.build_index(nm.notes)

    # edit A and incrementally update
    a.title = "A edited"
    a.content = "delta epsilon"
    se.update_document(a.id, a, flush=True)

    # compare against a full rebuild into a separate engine
    ref = SearchEngine(tmp_path / "ref.json")
    ref.build_index(nm.notes)
    assert se.inverted_index == ref.inverted_index
    assert se.total_docs == ref.total_docs


def test_deferred_flush_writes_only_on_flush(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("A", "alpha")
    se = SearchEngine(tmp_path / "i.json")
    se.build_index(nm.notes)
    idx = tmp_path / "i.json"
    before = idx.read_text(encoding="utf-8")
    a.content = "changed"
    se.update_document(a.id, a)              # deferred, no write
    assert idx.read_text(encoding="utf-8") == before
    se.flush()                                # now it writes
    assert idx.read_text(encoding="utf-8") != before
