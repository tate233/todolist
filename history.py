"""Note version history with diff and rollback.

Each save archives the previous content+title under the note id (bounded to the
most recent N versions). Diffs use difflib; rollback returns an older snapshot
so the caller can re-save it (which itself becomes a new version).
"""
import difflib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from storage.atomic_io import atomic_write_json

logger = logging.getLogger(__name__)

MAX_VERSIONS = 20


class VersionHistory:
    def __init__(self, storage_path: Path, max_versions: int = MAX_VERSIONS):
        self.storage_path = Path(storage_path)
        self.max_versions = max_versions
        self.versions: Dict[str, List[dict]] = {}
        self._load()

    def _load(self):
        if not self.storage_path.exists():
            self.versions = {}
            return
        try:
            self.versions = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.exception("加载版本历史失败: %s", e)
            self.versions = {}

    def _save(self):
        try:
            atomic_write_json(self.storage_path, self.versions)
        except Exception as e:
            logger.exception("保存版本历史失败: %s", e)

    def record(self, note_id: str, title: str, content: str):
        entry = {
            "title": title,
            "content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        history = self.versions.setdefault(note_id, [])
        # skip if unchanged from the latest snapshot
        if history and history[-1]["content"] == content and history[-1]["title"] == title:
            return
        history.append(entry)
        if len(history) > self.max_versions:
            del history[: len(history) - self.max_versions]
        self._save()

    def get_versions(self, note_id: str) -> List[dict]:
        return list(self.versions.get(note_id, []))

    def diff(self, note_id: str, index: int, current_content: str) -> str:
        versions = self.versions.get(note_id, [])
        if not (0 <= index < len(versions)):
            return ""
        old = versions[index]["content"].splitlines()
        new = current_content.splitlines()
        return "\n".join(difflib.unified_diff(old, new, "历史版本", "当前", lineterm=""))

    def rollback(self, note_id: str, index: int) -> dict:
        versions = self.versions.get(note_id, [])
        if not (0 <= index < len(versions)):
            raise IndexError("无效的版本序号")
        return dict(versions[index])
