"""Sync framework: local backend round-trip and last-writer-wins conflicts."""
from sync.base import SyncBackend, sync
from sync.local import LocalSyncBackend


def test_local_backend_is_sync_backend(tmp_path):
    assert isinstance(LocalSyncBackend(tmp_path / "remote"), SyncBackend)


def test_upload_new_local_keys(tmp_path):
    backend = LocalSyncBackend(tmp_path / "remote")
    local = {"a.md": (b"alpha", 100.0)}
    result = sync(local, backend)
    assert result.uploaded == ["a.md"]
    assert backend.download("a.md")[0] == b"alpha"


def test_download_new_remote_keys(tmp_path):
    backend = LocalSyncBackend(tmp_path / "remote")
    backend.upload("b.md", b"beta", 200.0)
    local = {}
    result = sync(local, backend)
    assert result.downloaded == ["b.md"]
    assert local["b.md"][0] == b"beta"


def test_conflict_newer_remote_wins(tmp_path):
    backend = LocalSyncBackend(tmp_path / "remote")
    backend.upload("c.md", b"remote-new", 300.0)
    local = {"c.md": (b"local-old", 100.0)}
    result = sync(local, backend)
    assert "c.md" in result.conflicts
    assert local["c.md"][0] == b"remote-new"  # remote (newer) wins


def test_local_newer_uploads(tmp_path):
    backend = LocalSyncBackend(tmp_path / "remote")
    backend.upload("d.md", b"remote-old", 100.0)
    local = {"d.md": (b"local-new", 300.0)}
    result = sync(local, backend)
    assert "d.md" in result.uploaded
    assert backend.download("d.md")[0] == b"local-new"
