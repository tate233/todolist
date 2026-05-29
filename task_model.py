"""Task data model and persistence for SmartNotes.

Brings the "todo" half back to a repo named `todolist`. Mirrors the
Note/NoteManager uuid + JSON conventions for consistency.
"""
import logging
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from storage.atomic_io import atomic_write_json

logger = logging.getLogger(__name__)

# Priority and status constants (state machine extended in a later PR).
PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"
PRIORITIES = (PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH)

STATUS_TODO = "todo"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"
STATUSES = (STATUS_TODO, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)

_TS = "%Y-%m-%d %H:%M:%S"


class Task:
    def __init__(self, title: str, description: str = "", due_date: str = None,
                 priority: str = PRIORITY_MEDIUM, status: str = STATUS_TODO,
                 task_id: str = None, created_at: str = None, completed_at: str = None,
                 tags: List[str] = None, note_id: str = None):
        self.id = task_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.due_date = due_date            # 'YYYY-MM-DD' or None
        self.priority = priority if priority in PRIORITIES else PRIORITY_MEDIUM
        self.status = status if status in STATUSES else STATUS_TODO
        self.created_at = created_at or datetime.now().strftime(_TS)
        self.completed_at = completed_at
        self.tags = tags or []
        self.note_id = note_id

    def to_dict(self) -> Dict:
        return {
            'id': self.id, 'title': self.title, 'description': self.description,
            'due_date': self.due_date, 'priority': self.priority, 'status': self.status,
            'created_at': self.created_at, 'completed_at': self.completed_at,
            'tags': self.tags, 'note_id': self.note_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        return cls(
            title=data['title'], description=data.get('description', ''),
            due_date=data.get('due_date'), priority=data.get('priority', PRIORITY_MEDIUM),
            status=data.get('status', STATUS_TODO), task_id=data.get('id'),
            created_at=data.get('created_at'), completed_at=data.get('completed_at'),
            tags=data.get('tags', []), note_id=data.get('note_id'),
        )

    def mark_done(self):
        self.status = STATUS_DONE
        self.completed_at = datetime.now().strftime(_TS)

    def _due(self):
        if not self.due_date:
            return None
        try:
            return datetime.strptime(self.due_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def is_overdue(self, today=None) -> bool:
        due = self._due()
        if due is None or self.status in (STATUS_DONE, STATUS_CANCELLED):
            return False
        today = today or date.today()
        return due < today

    def is_due_today(self, today=None) -> bool:
        due = self._due()
        if due is None:
            return False
        return due == (today or date.today())

    def days_until_due(self, today=None):
        due = self._due()
        if due is None:
            return None
        return (due - (today or date.today())).days


# Allowed status transitions (state machine).
_TRANSITIONS = {
    STATUS_TODO: {STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED},
    STATUS_IN_PROGRESS: {STATUS_TODO, STATUS_DONE, STATUS_CANCELLED},
    STATUS_DONE: {STATUS_TODO, STATUS_IN_PROGRESS},
    STATUS_CANCELLED: {STATUS_TODO},
}


def can_transition(from_status: str, to_status: str) -> bool:
    if from_status == to_status:
        return True
    return to_status in _TRANSITIONS.get(from_status, set())


class TaskManager:
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.tasks: Dict[str, Task] = {}
        self.load()

    def load(self):
        if not self.storage_path.exists():
            self.tasks = {}
            return
        try:
            import json  # noqa: PLC0415
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.tasks = {tid: Task.from_dict(td) for tid, td in data.items()}
        except Exception as e:
            logger.exception("加载任务失败: %s", e)
            self.tasks = {}

    def save(self) -> bool:
        try:
            atomic_write_json(self.storage_path, {tid: t.to_dict() for tid, t in self.tasks.items()})
            return True
        except Exception as e:
            logger.exception("保存任务失败: %s", e)
            return False

    def create_task(self, title: str, **kwargs) -> Task:
        if not title or not title.strip():
            raise ValueError("任务标题不能为空")
        task = Task(title=title.strip(), **kwargs)
        self.tasks[task.id] = task
        self.save()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> bool:
        task = self.get_task(task_id)
        if not task:
            return False
        new_status = kwargs.get("status")
        if new_status is not None and not can_transition(task.status, new_status):
            raise ValueError(f"非法状态流转: {task.status} -> {new_status}")
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        if new_status == STATUS_DONE and not task.completed_at:
            task.completed_at = datetime.now().strftime(_TS)
        self.save()
        return True

    def get_overdue(self, today=None) -> List[Task]:
        return [t for t in self.tasks.values() if t.is_overdue(today)]

    def get_due_today(self, today=None) -> List[Task]:
        return [t for t in self.tasks.values() if t.is_due_today(today)]

    def get_upcoming(self, within_days: int = 7, today=None) -> List[Task]:
        out = []
        for t in self.tasks.values():
            d = t.days_until_due(today)
            if d is not None and 0 <= d <= within_days and t.status not in (STATUS_DONE, STATUS_CANCELLED):
                out.append(t)
        return out

    def dashboard_data(self, within_days: int = 7, today=None) -> Dict[str, List[Task]]:
        """Grouped view for the dashboard: overdue / due-today / upcoming.

        'upcoming' excludes items already counted as due-today.
        """
        due_today = self.get_due_today(today)
        today_ids = {t.id for t in due_today}
        upcoming = [t for t in self.get_upcoming(within_days, today) if t.id not in today_ids]
        return {
            "overdue": self.get_overdue(today),
            "today": due_today,
            "upcoming": upcoming,
        }

    def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save()
            return True
        return False

    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    def get_by_status(self, status: str) -> List[Task]:
        return [t for t in self.tasks.values() if t.status == status]

    def get_by_due_date(self, due_date: str) -> List[Task]:
        return [t for t in self.tasks.values() if t.due_date == due_date]
