"""Wikilink parsing + resolution to bidirectional note links + backlinks."""
from markdown_parser import MarkdownParser
from note_model import NoteManager


def test_extract_wikilinks():
    mp = MarkdownParser()
    links = mp.extract_wikilinks("see [[Alpha]] and [[Beta|the beta note]] end")
    assert links == ["Alpha", "Beta"]


def test_sync_resolves_links_and_backlinks(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    target = nm.create_note("Target Note", "content")
    src = nm.create_note("Source", "refer to [[Target Note]] here")
    unresolved = nm.sync_wikilinks(src.id)
    assert unresolved == []
    assert target.id in nm.get_note(src.id).links
    # backlink visible from the target
    assert src.id in [n.id for n in nm.get_backlinks(target.id)]


def test_unresolved_titles_reported(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    src = nm.create_note("S", "link to [[Nonexistent]]")
    unresolved = nm.sync_wikilinks(src.id)
    assert unresolved == ["Nonexistent"]
    assert nm.get_note(src.id).links == []


def test_no_self_link(tmp_path):
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    s = nm.create_note("Self", "I reference [[Self]]")
    nm.sync_wikilinks(s.id)
    assert s.id not in nm.get_note(s.id).links
