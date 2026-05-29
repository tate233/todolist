"""Calendar view helpers: month matrix, tasks-by-day, month navigation."""
import calendar_view
from task_model import Task


def test_month_matrix_shape():
    weeks = calendar_view.month_matrix(2026, 6)
    assert all(len(w) == 7 for w in weeks)
    # June 2026 starts on a Monday
    assert weeks[0][0] == 1


def test_tasks_by_day_filters_month():
    tasks = [
        Task("a", due_date="2026-06-01"),
        Task("b", due_date="2026-06-01"),
        Task("c", due_date="2026-06-15"),
        Task("d", due_date="2026-07-01"),   # other month
        Task("e"),                           # no date
    ]
    by_day = calendar_view.tasks_by_day(tasks, 2026, 6)
    assert len(by_day[1]) == 2
    assert len(by_day[15]) == 1
    assert 1 in by_day and 31 not in by_day


def test_month_navigation_wraps():
    assert calendar_view.prev_month(2026, 1) == (2025, 12)
    assert calendar_view.next_month(2026, 12) == (2027, 1)
    assert calendar_view.next_month(2026, 6) == (2026, 7)
