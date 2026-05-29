"""make_snippet: context excerpt around the hit with highlight spans."""
from markdown_parser import MarkdownParser


def test_snippet_around_hit():
    mp = MarkdownParser()
    text = "x " * 60 + "TARGET" + " y" * 60
    snippet, spans = mp.make_snippet(text, "TARGET", context=20)
    assert "TARGET" in snippet
    assert snippet.startswith("…") and snippet.endswith("…")
    # the reported span actually points at the hit text
    s, e = spans[0]
    assert snippet[s:e].lower() == "target"


def test_snippet_no_hit_returns_head():
    mp = MarkdownParser()
    snippet, spans = mp.make_snippet("some plain content here", "zzz", context=10)
    assert spans == []
    assert snippet.startswith("some")


def test_snippet_strips_markdown():
    mp = MarkdownParser()
    snippet, _ = mp.make_snippet("# Heading\n\n**bold** keyword here", "keyword")
    assert "#" not in snippet and "**" not in snippet
    assert "keyword" in snippet


def test_snippet_empty_query():
    mp = MarkdownParser()
    snippet, spans = mp.make_snippet("hello world", "")
    assert spans == [] and "hello" in snippet
