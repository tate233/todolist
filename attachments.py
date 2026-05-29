"""Attachment management: content-addressed storage for images/files.

Files are stored under attachments/ keyed by a SHA-256 of their content, so
identical files are de-duplicated. A small JSON index records which note(s)
reference each attachment, enabling orphan cleanup when notes are removed.
"""
import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List

from storage.atomic_io import atomic_write_json

logger = logging.getLogger(__name__)


class AttachmentManager:
    def __init__(self, attachments_dir: Path, index_file: Path = None):
        self.dir = Path(attachments_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.index_file = Path(index_file) if index_file else self.dir / "index.json"
        self.refs: Dict[str, List[str]] = {}   # filename -> [note_id,...]
        self._load()

    def _load(self):
        if self.index_file.exists():
            try:
                self.refs = json.loads(self.index_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.exception("加载附件索引失败: %s", e)
                self.refs = {}

    def _save(self):
        try:
            atomic_write_json(self.index_file, self.refs)
        except Exception as e:
            logger.exception("保存附件索引失败: %s", e)

    @staticmethod
    def _hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()[:16]

    def add_file(self, src_path: Path, note_id: str = None) -> str:
        """Store a file by content hash; returns the stored filename."""
        src_path = Path(src_path)
        data = src_path.read_bytes()
        name = f"{self._hash_bytes(data)}{src_path.suffix.lower()}"
        dest = self.dir / name
        if not dest.exists():
            shutil.copyfile(src_path, dest)
        self._add_ref(name, note_id)
        return name

    def add_bytes(self, data: bytes, suffix: str, note_id: str = None) -> str:
        name = f"{self._hash_bytes(data)}{suffix}"
        dest = self.dir / name
        if not dest.exists():
            dest.write_bytes(data)
        self._add_ref(name, note_id)
        return name

    def _add_ref(self, name: str, note_id):
        refs = self.refs.setdefault(name, [])
        if note_id and note_id not in refs:
            refs.append(note_id)
        self._save()

    def path_for(self, name: str) -> Path:
        return self.dir / name

    def collect_orphans(self, referenced_names: set) -> List[str]:
        """Return stored files no longer referenced by any live note."""
        orphans = []
        for f in self.dir.iterdir():
            if f.name == self.index_file.name or not f.is_file():
                continue
            if f.name not in referenced_names:
                orphans.append(f.name)
        return orphans

    def purge_orphans(self, referenced_names: set) -> int:
        removed = 0
        for name in self.collect_orphans(referenced_names):
            try:
                (self.dir / name).unlink()
                self.refs.pop(name, None)
                removed += 1
            except OSError:  # noqa: PERF203 - per-file cleanup is intentional
                logger.exception("删除孤儿附件失败: %s", name)
        self._save()
        return removed
