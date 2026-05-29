"""Task model + TaskManager CRUD, persistence and round-trip."""
from task_model import (
    STATUS_DONE,
    Task,
    TaskManager,
)


def test_to_from_dict_roundtrip():
    t = Task("write report", description="q3", due_date="2026-06-01",
             priority="high", tags=["work"], note_id="n1")
    again = Task.from_dict(t.to_dict())
    assert again.to_dict() == t.to_dict()


def test_crud_and_persistence(tmp_path):
    tm = TaskManager(tmp_path / "tasks.db")
    t = tm.create_task("buy milk", priority="low")
    assert tm.get_task(t.id).title == "buy milk"
    tm.update_task(t.id, status=STATUS_DONE)
    assert tm.get_task(t.id).completed_at is not None

    # reload from disk
    tm2 = TaskManager(tmp_path / "tasks.db")
    assert tm2.get_task(t.id).status == STATUS_DONE
    assert tm2.delete_task(t.id)
    assert TaskManager(tmp_path / "tasks.db").get_task(t.id) is None


def test_filters(tmp_path):
    tm = TaskManager(tmp_path / "tasks.db")
    tm.create_task("a", status="todo", due_date="2026-06-01")
    tm.create_task("b", status="done", due_date="2026-06-02")
    assert len(tm.get_by_status("todo")) == 1
    assert len(tm.get_by_due_date("2026-06-02")) == 1


def test_empty_title_rejected(tmp_path):
    tm = TaskManager(tmp_path / "tasks.db")
    try:
        tm.create_task("   ")
        assert False, "expected ValueError"
    except ValueError:
        pass
