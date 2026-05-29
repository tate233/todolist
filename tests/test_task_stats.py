"""Task statistics (completion/overdue rates) and pomodoro counting."""
from datetime import date, timedelta

from task_model import STATUS_DONE, Task, TaskManager

TODAY = date(2026, 6, 15)


def test_statistics(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    tm.create_task("a", status=STATUS_DONE)
    tm.create_task("b", priority="high")
    tm.create_task("overdue", due_date=str(TODAY - timedelta(days=1)))
    stats = tm.get_task_statistics(today=TODAY)
    assert stats['total'] == 3
    assert stats['by_status'][STATUS_DONE] == 1
    assert abs(stats['completion_rate'] - 1 / 3) < 1e-9
    assert abs(stats['overdue_rate'] - 1 / 3) < 1e-9


def test_statistics_empty(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    stats = tm.get_task_statistics()
    assert stats['total'] == 0
    assert stats['completion_rate'] == 0.0


def test_pomodoro_count_persists(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    t = tm.create_task("focus")
    assert tm.add_pomodoro(t.id)
    assert tm.add_pomodoro(t.id)
    assert tm.get_task(t.id).pomodoros == 2
    # persisted across reload
    assert TaskManager(tmp_path / "t.db").get_task(t.id).pomodoros == 2


def test_pomodoros_roundtrip():
    t = Task("x", pomodoros=3)
    assert Task.from_dict(t.to_dict()).pomodoros == 3
