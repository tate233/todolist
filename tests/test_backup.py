"""Backup/export/restore round-trip and rolling-snapshot pruning."""
import backup


def _make_data(tmp_path):
    data = tmp_path / "data"
    (data / "notes").mkdir(parents=True)
    (data / "notes.db").write_text('{"x": 1}', encoding="utf-8")
    (data / "notes" / "a.md").write_text("hello", encoding="utf-8")
    return data


def test_export_restore_roundtrip(tmp_path):
    data = _make_data(tmp_path)
    zip_path = tmp_path / "out.zip"
    backup.export_archive(data, zip_path)
    assert zip_path.exists()

    restored = tmp_path / "restored"
    manifest = backup.restore_archive(zip_path, restored)
    assert manifest["file_count"] == 2
    assert (restored / "notes.db").read_text(encoding="utf-8") == '{"x": 1}'
    assert (restored / "notes" / "a.md").read_text(encoding="utf-8") == "hello"


def test_restore_refuses_nonempty_without_overwrite(tmp_path):
    data = _make_data(tmp_path)
    zip_path = tmp_path / "out.zip"
    backup.export_archive(data, zip_path)
    try:
        backup.restore_archive(zip_path, data)  # data is non-empty
        assert False, "expected FileExistsError"
    except FileExistsError:
        pass


def test_rolling_backups_pruned(tmp_path):
    data = _make_data(tmp_path)
    backups = tmp_path / "backups"
    for _ in range(4):
        # vary names by forcing distinct timestamps is hard; call keep=2 at end
        backup.export_archive(data, backups / f"backup_{_:02d}0000_000000.zip")
    backup.create_backup(data, backups, keep=2)
    assert len(backup.list_backups(backups)) == 2
