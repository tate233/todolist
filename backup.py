"""Backup and full zip export/import for SmartNotes data.

- Rolling snapshots of the data directory (keep N most recent).
- Export everything (database, notes, attachments) to a single zip with a
  manifest; restore from such a zip into a clean data directory.
"""
import json
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

MANIFEST_NAME = "manifest.json"


def create_backup(data_dir: Path, backups_dir: Path, keep: int = 5) -> Path:
    """Snapshot the data dir into backups_dir/backup_<ts>.zip, pruning old ones."""
    data_dir, backups_dir = Path(data_dir), Path(backups_dir)
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = backups_dir / f"backup_{stamp}.zip"
    export_archive(data_dir, dest)
    _prune(backups_dir, keep)
    return dest


def _prune(backups_dir: Path, keep: int):
    backups = sorted(backups_dir.glob("backup_*.zip"))
    for old in backups[:-keep] if keep > 0 else []:
        try:
            old.unlink()
        except OSError:  # noqa: PERF203 - per-file pruning is intentional
            logger.exception("删除旧备份失败: %s", old)


def export_archive(data_dir: Path, zip_path: Path) -> Path:
    """Bundle the data directory into a zip with a manifest."""
    data_dir, zip_path = Path(data_dir), Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    files = [p for p in data_dir.rglob("*")
             if p.is_file() and "backups" not in p.relative_to(data_dir).parts]
    manifest = {
        "version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "file_count": len(files),
    }
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))
        for f in files:
            zf.write(f, f.relative_to(data_dir).as_posix())
    return zip_path


def restore_archive(zip_path: Path, data_dir: Path, overwrite: bool = False) -> dict:
    """Restore a zip produced by export_archive into data_dir."""
    zip_path, data_dir = Path(zip_path), Path(data_dir)
    if data_dir.exists() and any(data_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"{data_dir} 非空；传入 overwrite=True 以覆盖恢复")
    data_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        manifest = json.loads(zf.read(MANIFEST_NAME)) if MANIFEST_NAME in zf.namelist() else {}
        for name in zf.namelist():
            if name == MANIFEST_NAME:
                continue
            zf.extract(name, data_dir)
    return manifest


def list_backups(backups_dir: Path) -> List[Path]:
    return sorted(Path(backups_dir).glob("backup_*.zip"))
