"""KnowledgeGraph: connectivity, centrality, isolation, communities, paths."""
from note_model import NoteManager
from search_engine import KnowledgeGraph


def _graph_with_link(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("A", "x")
    b = nm.create_note("B", "y")
    c = nm.create_note("C", "z")  # isolated
    a.links = [b.id]
    g = KnowledgeGraph()
    g.build_graph(nm.notes)
    return g, a, b, c


def test_link_creates_edge_and_connectivity(tmp_path):
    g, a, b, _c = _graph_with_link(tmp_path)
    assert b.id in g.get_connected_notes(a.id)


def test_isolated_notes(tmp_path):
    g, _a, _b, c = _graph_with_link(tmp_path)
    assert c.id in g.get_isolated_notes()


def test_central_notes_ranks_linked(tmp_path):
    g, a, b, _c = _graph_with_link(tmp_path)
    central = dict(g.get_central_notes())
    assert central.get(a.id, 0) >= 1 and central.get(b.id, 0) >= 1


def test_shortest_path(tmp_path):
    g, a, b, _c = _graph_with_link(tmp_path)
    assert g.get_shortest_path(a.id, b.id) == [a.id, b.id]


def test_empty_graph_stats():
    g = KnowledgeGraph()
    g.build_graph({})
    stats = g.get_statistics()
    assert stats['total_nodes'] == 0 and stats['communities'] == 0
