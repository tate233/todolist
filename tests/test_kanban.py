"""Kanban columns grouping and adjacent-column moves."""
from task_model import STATUS_DONE, STATUS_IN_PROGRESS, STATUS_TODO, TaskManager


def test_columns_in_order(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    tm.create_task("a", status=STATUS_TODO)
    tm.create_task("b", status=STATUS_IN_PROGRESS)
    tm.create_task("c", status=STATUS_DONE)
    cols = tm.kanban_columns()
    assert list(cols.keys()) == [STATUS_TODO, STATUS_IN_PROGRESS, STATUS_DONE]
    assert [t.title for t in cols[STATUS_TODO]] == ["a"]


def test_move_forward_and_back(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    t = tm.create_task("x", status=STATUS_TODO)
    assert tm.move_status(t.id, 1)
    assert tm.get_task(t.id).status == STATUS_IN_PROGRESS
    assert tm.move_status(t.id, 1)
    assert tm.get_task(t.id).status == STATUS_DONE
    assert tm.move_status(t.id, -1)
    assert tm.get_task(t.id).status == STATUS_IN_PROGRESS


def test_move_past_edges_is_noop(tmp_path):
    tm = TaskManager(tmp_path / "t.db")
    t = tm.create_task("x", status=STATUS_TODO)
    assert tm.move_status(t.id, -1) is False  # already first column
    tm.update_task(t.id, status=STATUS_DONE)
    assert tm.move_status(t.id, 1) is False   # already last column
