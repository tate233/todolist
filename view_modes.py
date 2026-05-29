"""Editor view-mode state machine (pure, Tk-free for testability)."""

EDIT = "edit"
SPLIT = "split"
PREVIEW = "preview"
ORDER = (EDIT, SPLIT, PREVIEW)


def next_mode(current: str) -> str:
    """Cycle edit -> split -> preview -> edit."""
    try:
        i = ORDER.index(current)
    except ValueError:
        return EDIT
    return ORDER[(i + 1) % len(ORDER)]


def visibility(mode: str):
    """Return (editor_visible, preview_visible) for a view mode."""
    return {
        EDIT: (True, False),
        SPLIT: (True, True),
        PREVIEW: (False, True),
    }.get(mode, (True, False))
