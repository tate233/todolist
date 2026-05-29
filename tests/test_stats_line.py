"""Live stats line formatting."""
from markdown_parser import MarkdownParser


def test_stats_line_contains_metrics():
    mp = MarkdownParser()
    line = mp.format_stats_line("hello world foo")
    assert "3 词" in line
    assert "字符" in line
    assert "分钟" in line


def test_stats_line_empty():
    mp = MarkdownParser()
    line = mp.format_stats_line("")
    assert "0 词" in line
    assert "0 字符" in line


def test_reading_time_scales():
    mp = MarkdownParser()
    short = mp.get_reading_time("word " * 10)
    long = mp.get_reading_time("word " * 1000)
    assert long > short
