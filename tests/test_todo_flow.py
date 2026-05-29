"""Integration of the todo-view operations through TaskManager."""
from task_model import STATUS_DONE, STATUS_TODO, TaskManager


def test_create_edit_toggle_delete(tmp_path):
    tm = TaskManager(tmp_path / "tasks.db")
    t = tm.create_task("ship feature", priority="high", status=STATUS_TODO,
                       due_date="2026-07-01")
    assert t.id in [x.id for x in tm.get_all_tasks()]

    tm.update_task(t.id, title="ship feature v2", priority="medium")
    assert tm.get_task(t.id).title == "ship feature v2"

    # toggle done <-> todo (what the view's button does)
    tm.update_task(t.id, status=STATUS_DONE)
    assert tm.get_task(t.id).status == STATUS_DONE
    assert tm.get_task(t.id).completed_at is not None
    tm.update_task(t.id, status=STATUS_TODO)
    assert tm.get_task(t.id).status == STATUS_TODO

    assert tm.delete_task(t.id)
    assert tm.get_task(t.id) is None


def test_view_listing_reflects_persistence(tmp_path):
    db = tmp_path / "tasks.db"
    TaskManager(db).create_task("persisted task")
    assert [t.title for t in TaskManager(db).get_all_tasks()] == ["persisted task"]
