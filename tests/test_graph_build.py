"""build_graph tag-co-occurrence edges should match a brute-force reference."""
from itertools import combinations

from note_model import NoteManager
from search_engine import KnowledgeGraph


def _ref_tag_edges(notes):
    edges = set()
    items = list(notes.items())
    for (ia, na), (ib, nb) in combinations(items, 2):
        if len(set(na.tags) & set(nb.tags)) >= 2:
            edges.add(frozenset((ia, ib)))
    return edges


def test_tag_edges_match_bruteforce(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    nm.create_note("a", "x", tags=["t1", "t2", "t3"])
    nm.create_note("b", "y", tags=["t1", "t2"])      # shares 2 with a -> edge
    nm.create_note("c", "z", tags=["t1"])             # shares 1 with a/b -> none
    nm.create_note("d", "w", tags=["t9"])             # isolated
    g = KnowledgeGraph()
    g.build_graph(nm.notes)
    got = {frozenset(e) for e in g.edges}
    assert got == _ref_tag_edges(nm.notes)


def test_no_duplicate_unordered_edges(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    for i in range(5):
        nm.create_note(f"n{i}", "c", tags=["shared", "common"])
    g = KnowledgeGraph()
    g.build_graph(nm.notes)
    seen = [frozenset(e) for e in g.edges]
    assert len(seen) == len(set(seen))
