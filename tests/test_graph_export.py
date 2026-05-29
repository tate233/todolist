"""KnowledgeGraph.to_networkx export + graph_view availability fallback."""
import graph_view
from note_model import NoteManager
from search_engine import KnowledgeGraph


def test_to_networkx_nodes_edges(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("A", "x", category="工作")
    b = nm.create_note("B", "y", category="工作")
    a.links = [b.id]
    g = KnowledgeGraph()
    g.build_graph(nm.notes)
    nxg = g.to_networkx()
    assert nxg.number_of_nodes() == 2
    assert nxg.has_edge(a.id, b.id)
    assert nxg.nodes[a.id]["title"] == "A"
    assert "centrality" in nxg.nodes[a.id]


def test_to_networkx_empty():
    g = KnowledgeGraph()
    g.build_graph({})
    assert g.to_networkx().number_of_nodes() == 0


def test_build_figure_returns_none_without_matplotlib():
    # matplotlib is not installed in CI's base env; build_figure must not raise.
    if not graph_view.is_available():
        g = KnowledgeGraph()
        g.build_graph({})
        assert graph_view.build_figure(g) is None
