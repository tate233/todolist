"""Pure helpers for Markdown editor toolbar actions.

Kept free of Tk so the wrap/insert logic is unit-testable. Each function takes
the current text, a selection range (start, end) and returns the new text plus
the caret position to place afterwards.
"""
from typing import Tuple

# marker presets: name -> (prefix, suffix, placeholder)
WRAPS = {
    "bold": ("**", "**", "bold text"),
    "italic": ("*", "*", "italic text"),
    "inline_code": ("`", "`", "code"),
    "strikethrough": ("~~", "~~", "text"),
}

LINE_PREFIXES = {
    "h1": "# ",
    "h2": "## ",
    "h3": "### ",
    "quote": "> ",
    "ul": "- ",
    "ol": "1. ",
}


def apply_wrap(text: str, start: int, end: int, kind: str) -> Tuple[str, int]:
    """Wrap the selection (or insert a placeholder) with the given markers."""
    prefix, suffix, placeholder = WRAPS[kind]
    selected = text[start:end]
    inner = selected or placeholder
    new = text[:start] + prefix + inner + suffix + text[end:]
    if selected:
        caret = start + len(prefix) + len(inner) + len(suffix)
    else:
        caret = start + len(prefix)  # caret at start of placeholder
    return new, caret


def apply_line_prefix(text: str, start: int, kind: str) -> Tuple[str, int]:
    """Insert a line-level marker at the start of the line containing `start`."""
    prefix = LINE_PREFIXES[kind]
    line_start = text.rfind("\n", 0, start) + 1
    new = text[:line_start] + prefix + text[line_start:]
    return new, start + len(prefix)


def insert_snippet(text: str, pos: int, snippet: str) -> Tuple[str, int]:
    new = text[:pos] + snippet + text[pos:]
    return new, pos + len(snippet)
