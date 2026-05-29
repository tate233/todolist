"""SqliteRepository implements the NoteRepository contract correctly."""
from note_model import Note, NoteManager
from storage.base import NoteRepository
from storage.sqlite_repository import SCHEMA_VERSION, SqliteRepository


def test_is_note_repository(tmp_path):
    repo = SqliteRepository(tmp_path / "db.sqlite3", Note)
    assert isinstance(repo, NoteRepository)
    assert repo.schema_version() == SCHEMA_VERSION


def test_crud_roundtrip(tmp_path):
    repo = SqliteRepository(tmp_path / "db.sqlite3", Note)
    nm = NoteManager(tmp_path / "n.db", tmp_path, repository=repo)
    n = nm.create_note("标题", "正文", tags=["a", "b"])
    n.links = ["x"]
    nm.save_notes()

    # fresh manager + fresh repo over the same db reloads everything
    repo2 = SqliteRepository(tmp_path / "db.sqlite3", Note)
    nm2 = NoteManager(tmp_path / "n.db", tmp_path, repository=repo2)
    got = nm2.get_note(n.id)
    assert got is not None
    assert got.title == "标题" and got.tags == ["a", "b"] and got.links == ["x"]

    nm2.purge_note(n.id)  # permanent removal
    assert SqliteRepository(tmp_path / "db.sqlite3", Note).list_ids() == []


def test_env_var_selects_sqlite(tmp_path, monkeypatch):
    monkeypatch.setenv("SMARTNOTES_BACKEND", "sqlite")
    nm = NoteManager(tmp_path / "n.db", tmp_path)
    assert isinstance(nm.repository, SqliteRepository)
