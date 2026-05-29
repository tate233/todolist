"""Version history: record bounded snapshots, diff and rollback."""
from history import VersionHistory


def test_record_and_get(tmp_path):
    h = VersionHistory(tmp_path / "h.json")
    h.record("n1", "T", "v1")
    h.record("n1", "T", "v2")
    versions = h.get_versions("n1")
    assert [v["content"] for v in versions] == ["v1", "v2"]


def test_record_skips_unchanged(tmp_path):
    h = VersionHistory(tmp_path / "h.json")
    h.record("n1", "T", "same")
    h.record("n1", "T", "same")
    assert len(h.get_versions("n1")) == 1


def test_bounded_to_max(tmp_path):
    h = VersionHistory(tmp_path / "h.json", max_versions=3)
    for i in range(6):
        h.record("n1", "T", f"v{i}")
    versions = h.get_versions("n1")
    assert len(versions) == 3
    assert versions[-1]["content"] == "v5"


def test_diff_and_rollback(tmp_path):
    h = VersionHistory(tmp_path / "h.json")
    h.record("n1", "T", "line one\nline two")
    diff = h.diff("n1", 0, "line one\nline CHANGED")
    assert "line two" in diff and "line CHANGED" in diff
    snap = h.rollback("n1", 0)
    assert snap["content"] == "line one\nline two"


def test_persistence(tmp_path):
    p = tmp_path / "h.json"
    VersionHistory(p).record("n1", "T", "persisted")
    assert VersionHistory(p).get_versions("n1")[0]["content"] == "persisted"
