import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from markdown_parser import count_words

logger = logging.getLogger(__name__)


def _default_repository(storage_path: Path, notes_dir: Path):
    """Pick the storage backend from config / SMARTNOTES_BACKEND env var.

    Defaults to the JSON file backend; "sqlite" selects SqliteRepository.
    """
    import os  # noqa: PLC0415
    backend = os.environ.get("SMARTNOTES_BACKEND")
    if backend is None:
        try:
            from config import config  # noqa: PLC0415
            backend = getattr(config, "storage_backend", "json")
        except Exception:
            backend = "json"
    if backend == "sqlite":
        from storage.sqlite_repository import SqliteRepository  # noqa: PLC0415
        db = Path(storage_path).with_suffix(".sqlite3")
        return SqliteRepository(db, Note)
    from storage.json_repository import JsonFileRepository  # noqa: PLC0415
    return JsonFileRepository(storage_path, notes_dir, Note)


class Note:
    def __init__(self, title: str, content: str = "", category: str = "未分类",
                 tags: List[str] = None, note_id: str = None, created_at: str = None,
                 updated_at: str = None, is_favorite: bool = False, deleted_at: str = None):
        self.id = note_id or str(uuid.uuid4())
        self.title = title
        self.content = content
        self.category = category
        self.tags = tags or []
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = updated_at or self.created_at
        self.is_favorite = is_favorite
        self.deleted_at = deleted_at      # None = active; timestamp = in trash
        self.word_count = count_words(content)
        self.links = []

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_favorite': self.is_favorite,
            'deleted_at': self.deleted_at,
            'word_count': self.word_count,
            'links': self.links
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Note':
        note = cls(
            title=data['title'],
            content=data.get('content', ''),
            category=data.get('category', '未分类'),
            tags=data.get('tags', []),
            note_id=data.get('id'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            is_favorite=data.get('is_favorite', False),
            deleted_at=data.get('deleted_at'),
        )
        note.links = data.get('links', [])
        return note

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if 'content' in kwargs:
            self.word_count = count_words(kwargs['content'])

    def add_tag(self, tag: str):
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def remove_tag(self, tag: str):
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add_link(self, note_id: str):
        if note_id and note_id not in self.links and note_id != self.id:
            self.links.append(note_id)
            self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def remove_link(self, note_id: str):
        if note_id in self.links:
            self.links.remove(note_id)
            self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class NoteManager:
    def __init__(self, storage_path: Path, notes_dir: Path, repository=None):
        self.storage_path = storage_path
        self.notes_dir = notes_dir
        # Persistence is delegated to a NoteRepository; default keeps the
        # existing JSON-file + per-note .md behaviour.
        if repository is None:
            repository = _default_repository(storage_path, notes_dir)
        self.repository = repository
        self.notes: Dict[str, Note] = {}
        self.load_notes()
        self.sync_note_files()

    def sync_note_files(self):
        """Reconcile the per-note .md export files with the authoritative JSON.

        The JSON store (notes.db) is the source of truth; the .md files are a
        rebuildable export. This rewrites any missing/stale .md and removes
        orphan .md files left behind by partial failures, keeping the two sets
        consistent.
        """
        valid = set()
        for note in self.notes.values():
            self._save_note_file(note)
            valid.add(f"{note.id}.md")
        try:
            for path in self.notes_dir.glob("*.md"):
                if path.name not in valid:
                    path.unlink()
        except OSError:
            logger.exception("清理孤立 .md 文件失败")

    def load_notes(self):
        self.notes = self.repository.load_all()

    def save_notes(self):
        return self.repository.save_all(self.notes)

    def create_note(self, title: str, content: str = "", category: str = "未分类",
                   tags: List[str] = None) -> Note:
        if not title or not title.strip():
            raise ValueError("笔记标题不能为空")

        note = Note(
            title=title.strip(),
            content=content,
            category=category,
            tags=tags or []
        )
        self.notes[note.id] = note
        self._save_note_file(note)
        self.save_notes()
        return note

    def get_note(self, note_id: str) -> Optional[Note]:
        return self.notes.get(note_id)

    def update_note(self, note_id: str, **kwargs) -> bool:
        note = self.get_note(note_id)
        if note:
            note.update(**kwargs)
            self._save_note_file(note)
            self.save_notes()
            return True
        return False

    def delete_note(self, note_id: str) -> bool:
        """Soft-delete: move the note to the trash (excluded from active lists)."""
        note = self.get_note(note_id)
        if note and note.deleted_at is None:
            note.deleted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_notes()
            return True
        return False

    def restore_note(self, note_id: str) -> bool:
        note = self.notes.get(note_id)
        if note and note.deleted_at is not None:
            note.deleted_at = None
            self.save_notes()
            return True
        return False

    def purge_note(self, note_id: str) -> bool:
        """Permanently remove a note and its backing file."""
        note = self.notes.get(note_id)
        if note:
            self._delete_note_file(note)
            del self.notes[note_id]
            self._remove_links_to_note(note_id)
            self.save_notes()
            return True
        return False

    def get_trash(self) -> List[Note]:
        return [n for n in self.notes.values() if n.deleted_at is not None]

    def empty_trash(self, older_than_days: int = None) -> int:
        """Permanently delete trashed notes; optionally only those older than N days."""
        from datetime import timedelta  # noqa: PLC0415
        cutoff = None
        if older_than_days is not None:
            cutoff = datetime.now() - timedelta(days=older_than_days)
        removed = 0
        for note in self.get_trash():
            if cutoff is not None:
                try:
                    deleted_dt = datetime.strptime(note.deleted_at, "%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    deleted_dt = None
                if deleted_dt and deleted_dt > cutoff:
                    continue
            if self.purge_note(note.id):
                removed += 1
        return removed

    def get_all_notes(self) -> List[Note]:
        return [n for n in self.notes.values() if n.deleted_at is None]

    def get_notes_by_category(self, category: str) -> List[Note]:
        return [n for n in self.get_all_notes() if n.category == category]

    def get_notes_by_tag(self, tag: str) -> List[Note]:
        return [n for n in self.get_all_notes() if tag in n.tags]

    def get_favorite_notes(self) -> List[Note]:
        return [n for n in self.get_all_notes() if n.is_favorite]

    def search_notes(self, keyword: str) -> List[Note]:
        if not keyword:
            return self.get_all_notes()

        keyword = keyword.lower()
        results = []

        for note in self.get_all_notes():
            if not (keyword in note.title.lower() or
                keyword in note.content.lower() or
                any(keyword in tag.lower() for tag in note.tags)):
                continue
            results.append(note)

        return results

    def get_linked_notes(self, note_id: str) -> List[Note]:
        note = self.get_note(note_id)
        if not note:
            return []

        linked_notes = []
        for linked_id in note.links:
            linked_note = self.get_note(linked_id)
            if linked_note:
                linked_notes.append(linked_note)

        return linked_notes

    def get_backlinks(self, note_id: str) -> List[Note]:
        return [note for note in self.notes.values() if note_id in note.links]

    def resolve_title(self, title: str) -> Optional[str]:
        """Return the id of the (first) note with this title, or None."""
        t = title.strip().lower()
        for note in self.notes.values():
            if note.title.lower() == t:
                return note.id
        return None

    def sync_wikilinks(self, note_id: str) -> List[str]:
        """Parse [[title]] wikilinks in a note's content and set note.links to
        the resolved target ids (de-duplicated, excluding self). Returns the
        list of unresolved titles."""
        from markdown_parser import MarkdownParser  # noqa: PLC0415
        note = self.get_note(note_id)
        if not note:
            return []
        parser = MarkdownParser()
        resolved, unresolved = [], []
        for title in parser.extract_wikilinks(note.content):
            target = self.resolve_title(title)
            if target and target != note_id and target not in resolved:
                resolved.append(target)
            elif not target:
                unresolved.append(title)
        note.links = resolved
        self.save_notes()
        return unresolved

    def get_all_tags(self) -> List[str]:
        tags = set()
        for note in self.get_all_notes():
            tags.update(note.tags)
        return sorted(list(tags))

    def get_statistics(self) -> Dict:
        active = self.get_all_notes()
        total_notes = len(active)
        total_words = sum(note.word_count for note in active)

        category_counts = {}
        for note in active:
            category_counts[note.category] = category_counts.get(note.category, 0) + 1

        tag_counts = {}
        for note in active:
            for tag in note.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            'total_notes': total_notes,
            'total_words': total_words,
            'categories': category_counts,
            'tags': tag_counts,
            'favorites': len(self.get_favorite_notes())
        }

    def sort_notes(self, by: str = "updated", reverse: bool = True) -> List[Note]:
        notes = self.get_all_notes()

        if by == "title":
            return sorted(notes, key=lambda n: n.title, reverse=reverse)
        elif by == "created":
            return sorted(notes, key=lambda n: n.created_at, reverse=reverse)
        elif by == "category":
            return sorted(notes, key=lambda n: n.category, reverse=reverse)
        elif by == "words":
            return sorted(notes, key=lambda n: n.word_count, reverse=reverse)
        else:
            return sorted(notes, key=lambda n: n.updated_at, reverse=reverse)

    def export_note(self, note_id: str, filepath: Path, format: str = "md") -> bool:
        note = self.get_note(note_id)
        if not note:
            return False

        try:
            if format == "md":
                content = f"# {note.title}\n\n"
                content += f"**分类**: {note.category}\n"
                content += f"**标签**: {', '.join(note.tags)}\n"
                content += f"**创建时间**: {note.created_at}\n"
                content += f"**更新时间**: {note.updated_at}\n\n"
                content += "---\n\n"
                content += note.content

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            elif format == "txt":
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"{note.title}\n\n{note.content}")

            return True
        except Exception as e:
            logger.exception("导出笔记失败: %s", e)
            return False

    def _unique_title(self, base: str) -> str:
        existing = {note.title for note in self.notes.values()}
        if base not in existing:
            return base
        i = 2
        while f"{base} ({i})" in existing:
            i += 1
        return f"{base} ({i})"

    def import_note(self, filepath: Path, category: str = "未分类") -> Optional[Note]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Prefer the first Markdown heading as the title; fall back to the
            # file stem. De-duplicate so importing two same-named files does not
            # collide on title.
            title = None
            for line in content.splitlines():
                heading = re.match(r'^#{1,6}\s+(.+)', line.strip())
                if heading:
                    title = heading.group(1).strip()
                    break
            title = self._unique_title(title or filepath.stem)
            note = self.create_note(title, content, category)
            return note
        except Exception as e:
            logger.exception("导入笔记失败: %s", e)
            return None

    def _save_note_file(self, note: Note):
        self.repository.upsert(note)

    def _delete_note_file(self, note: Note):
        self.repository.delete(note.id)

    def _remove_links_to_note(self, note_id: str):
        for note in self.notes.values():
            if note_id in note.links:
                note.remove_link(note_id)
