"""Migrate legacy JSON (+ per-note .md) storage into SQLite.

The .md files are treated as the authoritative content when they diverge from
the JSON copy (the JSON content could be stale from an interrupted write). The
migration backs up the data directory first and is idempotent: notes already
present in SQLite are upserted, not duplicated.
"""
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List

from note_model import Note
from storage.sqlite_repository import SqliteRepository

logger = logging.getLogger(__name__)


@dataclass
class MigrationReport:
    migrated: int = 0
    content_repaired: int = 0
    failed: List[str] = field(default_factory=list)
    backup_dir: str = ""

    def __str__(self):
        return (f"migrated={self.migrated} content_repaired={self.content_repaired} "
                f"failed={len(self.failed)} backup={self.backup_dir}")


def backup_data_dir(data_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = data_dir.parent / f"{data_dir.name}.backup_{stamp}"
    shutil.copytree(data_dir, dest)
    return dest


def migrate(json_path: Path, notes_dir: Path, sqlite_path: Path,
            data_dir: Path = None, do_backup: bool = True) -> MigrationReport:
    report = MigrationReport()
    json_path, notes_dir, sqlite_path = Path(json_path), Path(notes_dir), Path(sqlite_path)

    if do_backup and data_dir and Path(data_dir).exists():
        report.backup_dir = str(backup_data_dir(Path(data_dir)))

    raw = {}
    if json_path.exists():
        try:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.exception("读取旧 JSON 失败: %s", e)

    repo = SqliteRepository(sqlite_path, Note)
    existing = set(repo.list_ids())

    for note_id, data in raw.items():
        try:
            note = Note.from_dict(data)
            md_file = notes_dir / f"{note_id}.md"
            if md_file.exists():
                md_content = md_file.read_text(encoding="utf-8")
                if md_content != note.content:
                    note.content = md_content
                    report.content_repaired += 1
            repo.upsert(note)
            if note_id not in existing:
                report.migrated += 1
        except Exception as e:  # noqa: PERF203 - per-note isolation is intentional
            logger.exception("迁移笔记 %s 失败: %s", note_id, e)
            report.failed.append(note_id)

    return report
