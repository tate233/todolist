"""Unit tests for MarkdownParser extraction and statistics."""
from markdown_parser import MarkdownParser, count_words


def test_extract_headings_and_links():
    mp = MarkdownParser()
    text = "# H1\n## H2\n[label](http://x)"
    assert mp.extract_headings(text) == [(1, "H1"), (2, "H2")]
    assert mp.extract_links(text) == [("label", "http://x")]


def test_extract_tasks():
    mp = MarkdownParser()
    tasks = mp.extract_tasks("- [ ] todo\n- [x] done")
    assert tasks == [(False, "todo"), (True, "done")]


def test_count_words_ignores_code_and_markup():
    # inline code `x` is dropped; bold text "y" still counts as a word
    assert count_words("# Title\n\nhello world `x` **y**") == 4
    assert count_words("   --- ** ** ") == 0


def test_statistics_shape():
    mp = MarkdownParser()
    stats = mp.get_statistics("# T\n\nbody [a](b)\n- [ ] task")
    assert stats["heading_count"] == 1
    assert stats["task_count"] == 1
    assert stats["word_count"] >= 1
    assert "reading_time" in stats


def test_plain_text_strips_markup():
    mp = MarkdownParser()
    plain = mp.convert_to_plain_text("# Title\n\n**bold** [x](y)")
    assert "#" not in plain and "**" not in plain
    assert "Title" in plain and "bold" in plain
