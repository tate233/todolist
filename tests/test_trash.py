"""Soft-delete trash: excluded from active lists, restorable, purgeable."""
from note_model import NoteManager


def test_soft_delete_excludes_from_active(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("A", "x", category="工作", tags=["t"])
    assert nm.delete_note(a.id)
    assert a.id not in [n.id for n in nm.get_all_notes()]
    assert nm.get_notes_by_category("工作") == []
    assert nm.search_notes("A") == []
    assert a.id in [n.id for n in nm.get_trash()]


def test_restore(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("A", "x")
    nm.delete_note(a.id)
    assert nm.restore_note(a.id)
    assert a.id in [n.id for n in nm.get_all_notes()]
    assert nm.get_trash() == []


def test_purge_is_permanent(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("A", "x")
    nm.delete_note(a.id)
    assert nm.purge_note(a.id)
    assert nm.get_note(a.id) is None
    assert a.id not in nm.notes


def test_soft_delete_persists(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("A", "x")
    nm.delete_note(a.id)
    nm2 = NoteManager(tmp_path / "n.db", tmp_path)
    assert a.id in [n.id for n in nm2.get_trash()]
    assert nm2.get_all_notes() == []
