"""Data integrity checker / doctor for SmartNotes.

Detects (and optionally repairs) inconsistencies between the notes store, the
search index and inter-note links:
  - notes present in the store but missing from the search index (or vice versa)
  - dangling links pointing at notes that no longer exist

Read-only by default; ``fix=True`` rebuilds the index and prunes dangling links.
"""
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class IntegrityReport:
    index_out_of_sync: bool = False
    dangling_links: List[tuple] = field(default_factory=list)  # (note_id, missing_target)
    repaired: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.index_out_of_sync and not self.dangling_links

    def __str__(self):
        if self.ok and not self.repaired:
            return "integrity: OK"
        parts = []
        if self.index_out_of_sync:
            parts.append("index out of sync")
        if self.dangling_links:
            parts.append(f"{len(self.dangling_links)} dangling link(s)")
        if self.repaired:
            parts.append("repaired: " + ", ".join(self.repaired))
        return "integrity: " + "; ".join(parts)


def check(note_manager, search_engine, fix: bool = False) -> IntegrityReport:
    report = IntegrityReport()
    note_ids = set(note_manager.notes.keys())

    # 1) index vs store
    indexed = set(getattr(search_engine, "doc_ids", set()))
    if indexed != note_ids:
        report.index_out_of_sync = True
        if fix:
            search_engine.build_index(note_manager.notes)
            report.repaired.append("search index rebuilt")

    # 2) dangling links
    for note_id, note in note_manager.notes.items():
        for target in list(note.links):
            if target not in note_ids:
                report.dangling_links.append((note_id, target))
                if fix:
                    note.remove_link(target)
    if fix and any(nid for nid, _ in report.dangling_links):
        note_manager.save_notes()
        if report.dangling_links:
            report.repaired.append(f"pruned {len(report.dangling_links)} dangling link(s)")

    return report
