"""Storage abstraction for notes.

NoteRepository decouples NoteManager's business logic from how notes are
persisted, so JSON files, SQLite, encrypted or remote backends can be swapped
in without touching the manager or the GUI.
"""
from abc import ABC, abstractmethod
from typing import Dict, List


class NoteRepository(ABC):
    @abstractmethod
    def load_all(self) -> Dict[str, "object"]:
        """Return all notes as {note_id: Note}."""

    @abstractmethod
    def save_all(self, notes: Dict[str, "object"]) -> bool:
        """Persist the full set of notes."""

    @abstractmethod
    def upsert(self, note) -> None:
        """Create or update a single note."""

    @abstractmethod
    def delete(self, note_id: str) -> None:
        """Remove a single note's backing storage."""

    @abstractmethod
    def list_ids(self) -> List[str]:
        """Return the ids currently persisted."""
