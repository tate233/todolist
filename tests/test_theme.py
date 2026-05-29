"""Theme palettes are complete and switchable."""
import theme

REQUIRED_KEYS = {
    'primary', 'primary_dark', 'secondary', 'accent', 'bg_main', 'bg_sidebar',
    'bg_card', 'text_dark', 'text_light', 'text_white', 'border', 'success',
    'warning', 'danger', 'hover',
}


def test_all_themes_have_required_keys():
    for name in theme.available_themes():
        palette = theme.get_theme(name)
        assert REQUIRED_KEYS <= set(palette), f"{name} missing keys"


def test_light_and_dark_differ():
    assert theme.get_theme("light")["bg_main"] != theme.get_theme("dark")["bg_main"]


def test_unknown_theme_falls_back():
    assert theme.get_theme("nonexistent") == theme.get_theme(theme.DEFAULT_THEME)


def test_get_theme_returns_copy():
    p = theme.get_theme("light")
    p["bg_main"] = "#000000"
    assert theme.get_theme("light")["bg_main"] != "#000000"
