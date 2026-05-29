"""Task date logic: overdue/due-today/upcoming and status transitions."""
from datetime import date, timedelta

import pytest

from task_model import (
    STATUS_CANCELLED,
    STATUS_DONE,
    Task,
    TaskManager,
    can_transition,
)

TODAY = date(2026, 6, 15)


def test_overdue_only_for_unfinished_past_due():
    past = Task("a", due_date="2026-06-10")
    assert past.is_overdue(TODAY) is True
    past.status = STATUS_DONE
    assert past.is_overdue(TODAY) is False
    future = Task("b", due_date="2026-06-20")
    assert future.is_overdue(TODAY) is False


def test_due_today_and_days_until():
    t = Task("a", due_date="2026-06-15")
    assert t.is_due_today(TODAY) is True
    assert t.days_until_due(TODAY) == 0
    assert Task("b", due_date="2026-06-20").days_until_due(TODAY) == 5


def test_no_due_date():
    t = Task("a")
    assert t.is_overdue(TODAY) is False
    assert t.days_until_due(TODAY) is None


def test_manager_queries(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    tm.create_task("overdue", due_date=str(TODAY - timedelta(days=2)))
    tm.create_task("today", due_date=str(TODAY))
    tm.create_task("soon", due_date=str(TODAY + timedelta(days=3)))
    assert len(tm.get_overdue(TODAY)) == 1
    assert len(tm.get_due_today(TODAY)) == 1
    assert len(tm.get_upcoming(7, TODAY)) == 2  # today + soon


def test_transitions():
    assert can_transition("todo", "done")
    assert can_transition("done", "todo")
    assert not can_transition("cancelled", "done")


def test_illegal_transition_rejected(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    t = tm.create_task("x", status=STATUS_CANCELLED)
    with pytest.raises(ValueError):
        tm.update_task(t.id, status=STATUS_DONE)
