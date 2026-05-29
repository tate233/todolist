"""Pure Markdown toolbar action helpers."""
import md_actions


def test_wrap_selection():
    new, caret = md_actions.apply_wrap("hello world", 0, 5, "bold")
    assert new == "**hello** world"
    assert caret == len("**hello**")


def test_wrap_empty_inserts_placeholder():
    new, caret = md_actions.apply_wrap("", 0, 0, "italic")
    assert new == "*italic text*"
    assert caret == 1  # caret right after the opening marker


def test_line_prefix():
    new, caret = md_actions.apply_line_prefix("title\nbody", 7, "h2")
    assert new == "title\n## body"
    assert caret == 7 + len("## ")


def test_line_prefix_first_line():
    new, _ = md_actions.apply_line_prefix("body", 2, "quote")
    assert new == "> body"


def test_insert_snippet():
    new, caret = md_actions.insert_snippet("ab", 1, "X")
    assert new == "aXb" and caret == 2
