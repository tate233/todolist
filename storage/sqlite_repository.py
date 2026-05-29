"""SQLite-backed NoteRepository.

A single transactional database replaces the JSON file as the store, providing
atomic writes and WAL concurrency. Implements the same NoteRepository contract
so it is a drop-in alternative to JsonFileRepository.
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List

from storage.base import NoteRepository

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS notes (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    content     TEXT,
    category    TEXT,
    created_at  TEXT,
    updated_at  TEXT,
    is_favorite INTEGER DEFAULT 0,
    word_count  INTEGER DEFAULT 0,
    tags        TEXT DEFAULT '[]',
    links       TEXT DEFAULT '[]'
);
"""


class SqliteRepository(NoteRepository):
    def __init__(self, db_path: Path, note_cls):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._note_cls = note_cls
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            row = conn.execute("SELECT version FROM schema_version").fetchone()
            if row is None:
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))

    def _row_to_note(self, row):
        return self._note_cls.from_dict({
            'id': row['id'],
            'title': row['title'],
            'content': row['content'] or '',
            'category': row['category'] or '未分类',
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'is_favorite': bool(row['is_favorite']),
            'word_count': row['word_count'],
            'tags': json.loads(row['tags'] or '[]'),
            'links': json.loads(row['links'] or '[]'),
        })

    def load_all(self) -> Dict[str, object]:
        try:
            with self._connect() as conn:
                rows = conn.execute("SELECT * FROM notes").fetchall()
            return {r['id']: self._row_to_note(r) for r in rows}
        except Exception as e:
            logger.exception("加载笔记失败(SQLite): %s", e)
            return {}

    def upsert(self, note) -> None:
        with self._connect() as conn:
            self._upsert_conn(conn, note)

    def save_all(self, notes: Dict[str, object]) -> bool:
        try:
            with self._connect() as conn:
                conn.execute("BEGIN")
                for note in notes.values():
                    self._upsert_conn(conn, note)
            return True
        except Exception as e:
            logger.exception("保存笔记失败(SQLite): %s", e)
            return False

    def _upsert_conn(self, conn, note):
        conn.execute(
            """INSERT INTO notes
               (id, title, content, category, created_at, updated_at,
                is_favorite, word_count, tags, links)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 title=excluded.title, content=excluded.content,
                 category=excluded.category, updated_at=excluded.updated_at,
                 is_favorite=excluded.is_favorite, word_count=excluded.word_count,
                 tags=excluded.tags, links=excluded.links""",
            (note.id, note.title, note.content, note.category,
             note.created_at, note.updated_at, int(note.is_favorite),
             note.word_count, json.dumps(note.tags, ensure_ascii=False),
             json.dumps(note.links, ensure_ascii=False)),
        )

    def delete(self, note_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def list_ids(self) -> List[str]:
        with self._connect() as conn:
            return [r['id'] for r in conn.execute("SELECT id FROM notes").fetchall()]

    def schema_version(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT version FROM schema_version").fetchone()
            return row['version'] if row else 0
