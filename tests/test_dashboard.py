"""dashboard_data groups tasks into overdue/today/upcoming without overlap."""
from datetime import date, timedelta

from task_model import TaskManager

TODAY = date(2026, 6, 15)


def test_grouping(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    tm.create_task("overdue", due_date=str(TODAY - timedelta(days=1)))
    tm.create_task("today", due_date=str(TODAY))
    tm.create_task("soon", due_date=str(TODAY + timedelta(days=2)))
    tm.create_task("far", due_date=str(TODAY + timedelta(days=30)))
    tm.create_task("no-date")

    data = tm.dashboard_data(within_days=7, today=TODAY)
    assert {t.title for t in data["overdue"]} == {"overdue"}
    assert {t.title for t in data["today"]} == {"today"}
    assert {t.title for t in data["upcoming"]} == {"soon"}  # far/no-date excluded


def test_today_not_double_counted_in_upcoming(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    tm.create_task("today", due_date=str(TODAY))
    data = tm.dashboard_data(within_days=7, today=TODAY)
    today_ids = {t.id for t in data["today"]}
    upcoming_ids = {t.id for t in data["upcoming"]}
    assert today_ids.isdisjoint(upcoming_ids)
