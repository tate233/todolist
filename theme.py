"""Theme palettes for SmartNotes.

Centralises the colour constants that used to be hardcoded in gui.py so the UI
can switch between light/dark (and future) themes from one place.
"""
from typing import Dict

LIGHT = {
    'primary': '#667eea', 'primary_dark': '#5568d3', 'secondary': '#764ba2',
    'accent': '#f093fb', 'bg_main': '#f7fafc', 'bg_sidebar': '#2d3748',
    'bg_card': '#ffffff', 'text_dark': '#2d3748', 'text_light': '#718096',
    'text_white': '#ffffff', 'border': '#e2e8f0', 'success': '#48bb78',
    'warning': '#ed8936', 'danger': '#f56565', 'hover': '#edf2f7',
}

DARK = {
    'primary': '#7f9cf5', 'primary_dark': '#667eea', 'secondary': '#9f7aea',
    'accent': '#ed64a6', 'bg_main': '#1a202c', 'bg_sidebar': '#171923',
    'bg_card': '#2d3748', 'text_dark': '#e2e8f0', 'text_light': '#a0aec0',
    'text_white': '#ffffff', 'border': '#4a5568', 'success': '#68d391',
    'warning': '#f6ad55', 'danger': '#fc8181', 'hover': '#4a5568',
}

THEMES: Dict[str, Dict[str, str]] = {"light": LIGHT, "dark": DARK}
DEFAULT_THEME = "light"


def get_theme(name: str) -> Dict[str, str]:
    """Return the palette for a theme name, falling back to the default."""
    return dict(THEMES.get(name, THEMES[DEFAULT_THEME]))


def available_themes():
    return list(THEMES.keys())
