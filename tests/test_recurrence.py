"""Recurrence, subtasks and task dependencies."""
import pytest

from task_model import STATUS_DONE, Task, TaskManager


def test_fields_roundtrip():
    t = Task("x", recurrence="weekly",
             subtasks=[{"title": "a", "done": True}, {"title": "b", "done": False}],
             depends_on=["d1"])
    again = Task.from_dict(t.to_dict())
    assert again.recurrence == "weekly"
    assert again.subtasks == t.subtasks
    assert again.depends_on == ["d1"]


def test_subtask_progress():
    t = Task("x", subtasks=[{"title": "a", "done": True},
                            {"title": "b", "done": True},
                            {"title": "c", "done": False}])
    assert t.subtask_progress() == (2, 3)


def test_next_occurrence():
    assert Task("x", due_date="2026-06-15", recurrence="daily").next_occurrence_due() == "2026-06-16"
    assert Task("x", due_date="2026-06-15", recurrence="weekly").next_occurrence_due() == "2026-06-22"
    assert Task("x", due_date="2026-06-15", recurrence="monthly").next_occurrence_due() == "2026-07-15"


def test_complete_recurring_spawns_next(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    t = tm.create_task("weekly report", due_date="2026-06-15", recurrence="weekly")
    nxt = tm.complete_task(t.id)
    assert tm.get_task(t.id).status == STATUS_DONE
    assert nxt is not None and nxt.due_date == "2026-06-22"
    assert nxt.status != STATUS_DONE


def test_dependency_blocks_completion(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    pre = tm.create_task("prerequisite")
    main = tm.create_task("dependent", depends_on=[pre.id])
    with pytest.raises(ValueError):
        tm.update_task(main.id, status=STATUS_DONE)
    tm.update_task(pre.id, status=STATUS_DONE)   # satisfy prerequisite
    assert tm.update_task(main.id, status=STATUS_DONE)
