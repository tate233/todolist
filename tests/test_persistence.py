"""Persistence consistency: JSON authoritative, .md set reconciled; import de-dup."""
from note_model import NoteManager


def test_import_title_from_heading_and_dedup(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    f1 = tmp_path / "doc.md"
    f1.write_text("# My Title\n\nbody", encoding="utf-8")
    f2 = tmp_path / "other.md"
    f2.write_text("# My Title\n\nother body", encoding="utf-8")
    n1 = nm.import_note(f1)
    n2 = nm.import_note(f2)
    assert n1.title == "My Title"
    assert n2.title == "My Title (2)"  # de-duplicated, no collision


def test_orphan_md_files_pruned_on_reconcile(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    nm.create_note("keep", "content")
    orphan = tmp_path / "deadbeef.md"
    orphan.write_text("stale", encoding="utf-8")
    nm.sync_note_files()
    assert not orphan.exists()
    # every surviving note still has its .md
    for note in nm.notes.values():
        assert (tmp_path / f"{note.id}.md").exists()
