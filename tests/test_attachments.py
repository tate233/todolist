"""Attachment manager: content-addressed storage, dedup, orphan cleanup."""
from attachments import AttachmentManager


def test_add_file_and_dedup(tmp_path):
    src = tmp_path / "img.png"
    src.write_bytes(b"PNGDATA")
    am = AttachmentManager(tmp_path / "att")
    n1 = am.add_file(src, "note1")
    n2 = am.add_file(src, "note2")          # same content
    assert n1 == n2                          # de-duplicated by hash
    assert am.path_for(n1).exists()
    assert set(am.refs[n1]) == {"note1", "note2"}


def test_add_bytes(tmp_path):
    am = AttachmentManager(tmp_path / "att")
    name = am.add_bytes(b"hello", ".txt", "n1")
    assert name.endswith(".txt")
    assert am.path_for(name).read_bytes() == b"hello"


def test_orphan_detection_and_purge(tmp_path):
    am = AttachmentManager(tmp_path / "att")
    keep = am.add_bytes(b"keep", ".bin", "n1")
    orphan = am.add_bytes(b"orphan", ".bin", "n2")
    # only `keep` is still referenced
    assert orphan in am.collect_orphans({keep})
    removed = am.purge_orphans({keep})
    assert removed == 1
    assert not am.path_for(orphan).exists()
    assert am.path_for(keep).exists()


def test_index_persists(tmp_path):
    am = AttachmentManager(tmp_path / "att")
    name = am.add_bytes(b"x", ".bin", "n1")
    am2 = AttachmentManager(tmp_path / "att")
    assert name in am2.refs
