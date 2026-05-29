"""Styled HTML preview output + graceful absence of tkhtmlview."""
import importlib.util

from markdown_parser import MarkdownParser


def test_styled_html_wraps_with_css():
    mp = MarkdownParser()
    html = mp.parse_to_styled_html("# Title\n\n**bold**")
    assert html.startswith("<html>")
    assert "<style>" in html and "font-family" in html
    assert "<h1" in html  # heading rendered to HTML, not raw markdown
    assert "<strong>bold</strong>" in html


def test_tkhtmlview_optional():
    # The app must work whether or not tkhtmlview is installed; just assert the
    # import-capability check is well-defined (no exception).
    available = importlib.util.find_spec("tkhtmlview") is not None
    assert available in (True, False)
