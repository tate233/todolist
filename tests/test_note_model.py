"""Unit tests for Note serialization and NoteManager behaviour."""
import pytest

from note_model import Note, NoteManager


def test_note_to_from_dict_roundtrip():
    n = Note("Title", "body", category="工作", tags=["a", "b"])
    n.links = ["other"]
    again = Note.from_dict(n.to_dict())
    assert again.to_dict() == n.to_dict()


def test_create_requires_title(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    with pytest.raises(ValueError):
        nm.create_note("   ")


def test_crud_and_reload(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    n = nm.create_note("A", "x", tags=["t"])
    nm.update_note(n.id, content="y")
    assert nm.get_note(n.id).content == "y"
    nm2 = NoteManager(tmp_path / "n.db", tmp_path)
    assert nm2.get_note(n.id).content == "y"
    nm2.delete_note(n.id)
    assert NoteManager(tmp_path / "n.db", tmp_path).get_note(n.id) is None


def test_links_cleaned_on_delete(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    a = nm.create_note("A", "x")
    b = nm.create_note("B", "y")
    a.add_link(b.id)
    nm.save_notes()
    nm.delete_note(b.id)
    assert b.id not in nm.get_note(a.id).links


def test_filters_and_tags(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    nm.create_note("A", "x", category="工作", tags=["p"])
    nm.create_note("B", "y", category="学习", tags=["q"])
    assert len(nm.get_notes_by_category("工作")) == 1
    assert len(nm.get_notes_by_tag("q")) == 1
    assert nm.get_all_tags() == ["p", "q"]
