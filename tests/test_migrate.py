"""Migration: JSON+md -> SQLite, .md wins on divergence, idempotent, backup made."""
from note_model import Note, NoteManager
from storage.migrator import migrate
from storage.sqlite_repository import SqliteRepository


def _make_legacy(tmp_path):
    data_dir = tmp_path / ".smart_notes"
    notes_dir = data_dir / "notes"
    notes_dir.mkdir(parents=True)
    json_path = data_dir / "notes.db"
    nm = NoteManager(json_path, notes_dir)
    n = nm.create_note("Legacy", "json content", tags=["t"])
    # diverge the .md from the json copy
    (notes_dir / f"{n.id}.md").write_text("authoritative md content", encoding="utf-8")
    return data_dir, notes_dir, json_path, n


def test_migration_prefers_md_and_backs_up(tmp_path):
    data_dir, notes_dir, json_path, n = _make_legacy(tmp_path)
    sqlite_path = data_dir / "notes.sqlite3"
    report = migrate(json_path, notes_dir, sqlite_path, data_dir=data_dir)
    assert report.migrated == 1
    assert report.content_repaired == 1
    assert report.backup_dir and (tmp_path / "").exists()
    got = SqliteRepository(sqlite_path, Note).load_all()[n.id]
    assert got.content == "authoritative md content"


def test_migration_idempotent(tmp_path):
    data_dir, notes_dir, json_path, _n = _make_legacy(tmp_path)
    sqlite_path = data_dir / "notes.sqlite3"
    migrate(json_path, notes_dir, sqlite_path, do_backup=False)
    second = migrate(json_path, notes_dir, sqlite_path, do_backup=False)
    assert second.migrated == 0  # already present
    assert len(SqliteRepository(sqlite_path, Note).list_ids()) == 1


def test_migration_handles_empty(tmp_path):
    sqlite_path = tmp_path / "empty.sqlite3"
    report = migrate(tmp_path / "missing.db", tmp_path, sqlite_path, do_backup=False)
    assert report.migrated == 0 and not report.failed
