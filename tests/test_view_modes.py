"""Editor view-mode state machine cycling and visibility."""
import view_modes


def test_cycle_order():
    assert view_modes.next_mode(view_modes.EDIT) == view_modes.SPLIT
    assert view_modes.next_mode(view_modes.SPLIT) == view_modes.PREVIEW
    assert view_modes.next_mode(view_modes.PREVIEW) == view_modes.EDIT


def test_cycle_unknown_resets_to_edit():
    assert view_modes.next_mode("bogus") == view_modes.EDIT


def test_visibility():
    assert view_modes.visibility(view_modes.EDIT) == (True, False)
    assert view_modes.visibility(view_modes.SPLIT) == (True, True)
    assert view_modes.visibility(view_modes.PREVIEW) == (False, True)
