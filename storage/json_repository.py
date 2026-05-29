"""JSON-file note repository: notes.db (authoritative) + per-note .md export."""
import json
import logging
from pathlib import Path
from typing import Dict, List

from storage.atomic_io import atomic_write_json, atomic_write_text
from storage.base import NoteRepository

logger = logging.getLogger(__name__)


class JsonFileRepository(NoteRepository):
    def __init__(self, storage_path: Path, notes_dir: Path, note_cls):
        self.storage_path = Path(storage_path)
        self.notes_dir = Path(notes_dir)
        self._note_cls = note_cls

    def load_all(self) -> Dict[str, object]:
        if not self.storage_path.exists():
            return {}
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {nid: self._note_cls.from_dict(nd) for nid, nd in data.items()}
        except Exception as e:
            logger.exception("加载笔记失败: %s", e)
            return {}

    def save_all(self, notes: Dict[str, object]) -> bool:
        try:
            data = {nid: note.to_dict() for nid, note in notes.items()}
            atomic_write_json(self.storage_path, data)
            return True
        except Exception as e:
            logger.exception("保存笔记失败: %s", e)
            return False

    def upsert(self, note) -> None:
        try:
            atomic_write_text(self.notes_dir / f"{note.id}.md", note.content)
        except Exception as e:
            logger.exception("保存笔记文件失败: %s", e)

    def delete(self, note_id: str) -> None:
        try:
            path = self.notes_dir / f"{note_id}.md"
            if path.exists():
                path.unlink()
        except Exception as e:
            logger.exception("删除笔记文件失败: %s", e)

    def list_ids(self) -> List[str]:
        return [p.stem for p in self.notes_dir.glob("*.md")]
