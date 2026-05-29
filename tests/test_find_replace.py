"""Find / replace pure helpers (offsets, case sensitivity, count)."""
import md_actions


def test_find_all_case_insensitive():
    m = md_actions.find_all_matches("Foo foo FOO", "foo")
    assert m == [(0, 3), (4, 7), (8, 11)]


def test_find_all_case_sensitive():
    m = md_actions.find_all_matches("Foo foo FOO", "foo", case_sensitive=True)
    assert m == [(4, 7)]


def test_find_empty_needle():
    assert md_actions.find_all_matches("abc", "") == []


def test_replace_all_count():
    new, n = md_actions.replace_all("a-a-a", "a", "X")
    assert new == "X-X-X" and n == 3


def test_replace_all_case_sensitive():
    new, n = md_actions.replace_all("Aa", "a", "Z", case_sensitive=True)
    assert new == "AZ" and n == 1


def test_replace_no_match():
    new, n = md_actions.replace_all("abc", "z", "Y")
    assert new == "abc" and n == 0
