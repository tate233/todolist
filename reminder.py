"""Task reminder scanning and desktop notification.

Pure scan logic (which tasks need reminding now) is separated from the GUI/OS
notification so it is testable. A task is due for reminding when it is unfinished
and within `lead_days` of its due date (or overdue), and hasn't been reminded yet.
"""
import logging
from datetime import date

logger = logging.getLogger(__name__)


def due_for_reminder(tasks, already_reminded, lead_days: int = 1, today=None):
    """Return tasks (not in already_reminded) that should be reminded now."""
    today = today or date.today()
    out = []
    for t in tasks:
        if t.id in already_reminded:
            continue
        if t.status in ("done", "cancelled"):
            continue
        days = t.days_until_due(today)
        if days is not None and days <= lead_days:
            out.append(t)
    return out


def notify(title: str, message: str) -> bool:
    """Best-effort desktop notification; returns True if a backend handled it."""
    try:
        from plyer import notification  # noqa: PLC0415
        notification.notify(title=title, message=message, timeout=10)
        return True
    except Exception:
        logger.debug("desktop notification unavailable; falling back")
        return False


class ReminderService:
    """Tracks which tasks have already been reminded this session."""

    def __init__(self, lead_days: int = 1):
        self.lead_days = lead_days
        self.reminded = set()

    def scan(self, tasks, today=None):
        due = due_for_reminder(tasks, self.reminded, self.lead_days, today)
        for t in due:
            self.reminded.add(t.id)
        return due

    def reset(self):
        self.reminded.clear()
