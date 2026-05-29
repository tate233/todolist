"""Tag cloud frequency scaling and ordering."""
from note_model import NoteManager


def test_frequencies(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    nm.create_note("a", "x", tags=["py", "web"])
    nm.create_note("b", "y", tags=["py"])
    nm.create_note("c", "z", tags=["py", "web"])
    freq = nm.tag_frequencies()
    assert freq == {"py": 3, "web": 2}


def test_tag_cloud_sorted_and_scaled(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    for _ in range(4):
        nm.create_note("p" + _.__repr__(), "x", tags=["hot"])
    nm.create_note("q", "y", tags=["cold"])
    cloud = nm.tag_cloud(buckets=5)
    # most frequent first
    assert cloud[0][0] == "hot"
    # sizes within range and hot >= cold
    sizes = {tag: size for tag, _c, size in cloud}
    assert 1 <= sizes["cold"] <= 5 and sizes["hot"] >= sizes["cold"]


def test_empty(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    assert nm.tag_cloud() == []
