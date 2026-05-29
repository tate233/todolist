"""Reminder scanning: lead window, status filtering and dedup."""
from datetime import date, timedelta

from reminder import ReminderService, due_for_reminder
from task_model import TaskManager

TODAY = date(2026, 6, 15)


def _tasks(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    tm.create_task("due tomorrow", due_date=str(TODAY + timedelta(days=1)))
    tm.create_task("due next week", due_date=str(TODAY + timedelta(days=7)))
    tm.create_task("overdue", due_date=str(TODAY - timedelta(days=1)))
    tm.create_task("done soon", due_date=str(TODAY), status="done")
    tm.create_task("no date")
    return tm


def test_due_within_lead(tmp_path):
    tm = _tasks(tmp_path)
    due = due_for_reminder(tm.get_all_tasks(), set(), lead_days=1, today=TODAY)
    titles = {t.title for t in due}
    assert titles == {"due tomorrow", "overdue"}  # next-week/done/no-date excluded


def test_service_dedups(tmp_path):
    tm = _tasks(tmp_path)
    svc = ReminderService(lead_days=1)
    first = svc.scan(tm.get_all_tasks(), today=TODAY)
    assert first
    second = svc.scan(tm.get_all_tasks(), today=TODAY)
    assert second == []  # already reminded this session
    svc.reset()
    assert svc.scan(tm.get_all_tasks(), today=TODAY)  # after reset, reminds again
