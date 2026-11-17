from .translations import TRANSLATIONS, AVAILABLE_UI_MODES, PDF_LANGUAGES, get_text, get_translations
from .themes import THEMES
from .shell import SHELL

# App-shell labels (navigation, company card, bank application, admin) live in
# their own module; merge them into each mode so callers get one flat dict.
for _mode, _labels in SHELL.items():
    TRANSLATIONS.setdefault(_mode, {}).update(_labels)
del _mode, _labels

__all__ = ["TRANSLATIONS", "AVAILABLE_UI_MODES", "PDF_LANGUAGES", "get_text", "get_translations", "THEMES", "SHELL"]
