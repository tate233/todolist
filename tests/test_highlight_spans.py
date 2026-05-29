"""Editor highlight spans cover headings, emphasis, code and links."""
from markdown_parser import MarkdownParser


def _tags(line):
    mp = MarkdownParser()
    return {t for t, _s, _e in mp.highlight_spans(line)}


def test_heading_span():
    mp = MarkdownParser()
    spans = mp.highlight_spans("## Title")
    assert ("md_heading", 0, len("## Title")) in spans


def test_inline_markers():
    assert "md_bold" in _tags("a **bold** b")
    assert "md_code" in _tags("use `code` here")
    assert "md_link" in _tags("see [x](http://y)")


def test_list_marker():
    assert "md_list" in _tags("- item")


def test_plain_line_has_no_spans():
    assert _tags("just plain text") == set()
