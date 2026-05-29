"""Interactive knowledge-graph visualization (networkx + matplotlib).

matplotlib is optional: if it is not installed, ``is_available`` is False and
the GUI falls back to the textual graph summary.
"""
import logging

logger = logging.getLogger(__name__)


def is_available() -> bool:
    try:
        import matplotlib  # noqa: F401,PLC0415
        import networkx  # noqa: F401,PLC0415
    except ImportError:
        return False
    return True


def build_figure(knowledge_graph, on_pick=None):
    """Return a matplotlib Figure rendering the graph, or None if unavailable.

    Nodes are coloured by category and sized by degree centrality. ``on_pick``
    receives a node id when a node is clicked.
    """
    if not is_available():
        return None
    import matplotlib.pyplot as plt  # noqa: PLC0415
    import networkx as nx  # noqa: PLC0415

    g = knowledge_graph.to_networkx()
    fig, ax = plt.subplots(figsize=(7, 5))
    if g.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "暂无笔记节点", ha="center", va="center")
        return fig

    pos = nx.spring_layout(g, seed=42)
    categories = sorted({d.get("category", "") for _n, d in g.nodes(data=True)})
    cmap = {c: plt.cm.tab10(i % 10) for i, c in enumerate(categories)}
    node_colors = [cmap[d.get("category", "")] for _n, d in g.nodes(data=True)]
    sizes = [300 + 2000 * d.get("centrality", 0) for _n, d in g.nodes(data=True)]

    nx.draw_networkx_edges(g, pos, ax=ax, alpha=0.4)
    nodes = nx.draw_networkx_nodes(g, pos, ax=ax, node_color=node_colors, node_size=sizes)
    labels = {n: d.get("title", n)[:10] for n, d in g.nodes(data=True)}
    nx.draw_networkx_labels(g, pos, labels=labels, ax=ax, font_size=8)
    ax.set_axis_off()

    if on_pick is not None and nodes is not None:
        node_ids = list(g.nodes())
        nodes.set_picker(True)

        def _handler(event):
            ind = getattr(event, "ind", None)
            if ind is not None and len(ind):
                on_pick(node_ids[ind[0]])

        fig.canvas.mpl_connect("pick_event", _handler)
    return fig
