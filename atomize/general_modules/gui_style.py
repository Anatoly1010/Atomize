# -*- coding: utf-8 -*-
"""
Shared, theme-driven GUI styling for Atomize Qt applications.

Why this module exists
----------------------
Atomize spawns several independent Qt processes (the main window plus, in the
EPR fork, each control-center tool runs in its own ``QProcess`` with its own
``QApplication``). Historically each defined its dark-theme colours and
per-widget stylesheets inline.

On Linux the default Qt style is *Fusion*, which honours the partial,
``color``-only stylesheets and draws clean themed borders, spin ``+/-`` glyphs
and combo arrows. On Windows the default style is *windowsvista*, which draws
``QComboBox`` / ``QSpinBox`` / ``QLineEdit`` frames and sub-controls its own
way: wrong combo colours, inconsistent borders, missing ``+/-`` signs. Because
the inline stylesheets only set the text/selection colour, everything else
falls back to the (divergent) native style.

Design
------
The look is described once by a :class:`Theme` (plain RGB tuples). From a theme
we derive both a ``QPalette`` and a set of per-widget stylesheet strings, so a
single source of truth drives the whole UI and re-skinning means editing one
dataclass. Everything is framework-only (PyQt6) with no Atomize dependencies,
so the file can be dropped into upstream Atomize's ``general_modules`` verbatim.

Typical use, right after creating the ``QApplication``::

    from atomize.general_modules.gui_style import apply_app_style
    app = QApplication(sys.argv)
    apply_app_style(app, app_id='Atomize.MainWindow')   # Fusion + dark palette
    ...

The exported module-level constants (``BG``, ``FG``, ``ACCENT`` and the
``*_STYLE`` sheets) are generated from :data:`DEFAULT_THEME` and kept for the
per-widget ``setStyleSheet(...)`` calls scattered across the tools. To re-skin,
build a custom :class:`Theme`, pass it to :func:`apply_app_style`, and read its
sheets from :func:`build_styles`.
"""

import os
import sys
import ctypes
from string import Template
from dataclasses import dataclass

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QStyleFactory


# --------------------------------------------------------------------------- #
# Theme
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Theme:
    """A colour theme as ``(r, g, b)`` tuples. Subclass / copy to re-skin."""
    bg:     tuple = (42, 42, 64)     # window / central-widget background
    base:   tuple = (63, 63, 97)     # input-field background, buttons, tabs
    border: tuple = (83, 83, 117)    # element borders / separators
    fg:     tuple = (193, 202, 227)  # primary text
    accent: tuple = (211, 194, 78)   # selection / highlight (gold)
    track:  tuple = (43, 43, 77)     # scrollbar track / tab-pane border
    hover:  tuple = (73, 73, 107)    # hover background (tabs, etc.)
    light:  tuple = (103, 103, 137)  # lighter edge for the Fusion 3-D frame
    dark:   tuple = (32, 32, 52)     # darker edge / shadow for the frame


DEFAULT_THEME = Theme()


def _css(rgb):
    """``(r, g, b)`` -> ``'rgb(r, g, b)'`` for use inside a stylesheet."""
    return 'rgb(%d, %d, %d)' % rgb


# Absolute path to the checkmark glyph drawn inside a ticked QCheckBox. Kept
# next to this module and resolved from ``__file__`` so it survives the
# ``os.chdir(libs)`` the main window does at startup and works from any cwd.
# Forward slashes: Qt stylesheet ``url(...)`` wants '/', including on Windows.
_CHECK_ICON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'check.svg').replace('\\', '/')


def _qcolor(rgb):
    """``(r, g, b)`` -> :class:`QColor`."""
    return QColor(*rgb)


# --------------------------------------------------------------------------- #
# Palette
# --------------------------------------------------------------------------- #
def build_palette(theme=DEFAULT_THEME):
    """Return the dark :class:`QPalette` derived from *theme*."""
    pal = QPalette()
    Role = QPalette.ColorRole
    Group = QPalette.ColorGroup

    bg, base, border = _qcolor(theme.bg), _qcolor(theme.base), _qcolor(theme.border)
    fg, accent = _qcolor(theme.fg), _qcolor(theme.accent)

    pal.setColor(Role.Window, bg)
    pal.setColor(Role.WindowText, fg)
    pal.setColor(Role.Base, base)
    pal.setColor(Role.AlternateBase, bg)
    pal.setColor(Role.Text, fg)
    pal.setColor(Role.Button, base)
    pal.setColor(Role.ButtonText, fg)
    pal.setColor(Role.BrightText, accent)
    pal.setColor(Role.Highlight, accent)
    pal.setColor(Role.HighlightedText, base)
    pal.setColor(Role.ToolTipBase, base)
    pal.setColor(Role.ToolTipText, fg)
    pal.setColor(Role.PlaceholderText, border)
    pal.setColor(Role.Link, accent)

    # Frame shading: Fusion derives the 1-px input border from these roles, so
    # pinning them keeps QComboBox / QSpinBox / QLineEdit borders consistent.
    pal.setColor(Role.Light, _qcolor(theme.light))
    pal.setColor(Role.Midlight, border)
    pal.setColor(Role.Mid, border)
    pal.setColor(Role.Dark, _qcolor(theme.dark))
    pal.setColor(Role.Shadow, _qcolor(theme.dark))

    # Disabled widgets: dim the text so they read as inactive.
    for role in (Role.Text, Role.ButtonText, Role.WindowText):
        pal.setColor(Group.Disabled, role, border)

    return pal


# --------------------------------------------------------------------------- #
# Windows taskbar identity
# --------------------------------------------------------------------------- #
def set_app_user_model_id(app_id):
    """
    Give this process its own Windows taskbar identity.

    Each tool is a separate process. Without an explicit AppUserModelID,
    Windows groups its window under the launching python.exe / pythonw.exe and
    shows the generic Python icon on the taskbar instead of the window icon set
    via ``setWindowIcon``. A unique per-tool string makes Windows treat the
    tool as its own application, so its icon shows and it gets its own taskbar
    button. Must run before the window is shown.

    No-op on non-Windows platforms (and harmless if it ever fails).
    """
    if sys.platform != 'win32' or not app_id:
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(str(app_id))
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def apply_app_style(app=None, app_id=None, theme=DEFAULT_THEME):
    """
    Pin the QApplication to the Fusion style with the theme's dark palette.

    Fusion renders identically on Windows and Linux, fixing the windowsvista
    quirks (wrong combo colours, inconsistent borders, missing spin +/- signs).
    Call once right after ``QApplication(sys.argv)``.

    Pass ``app_id`` (e.g. ``'Atomize.MainWindow'``) to give the process its own
    Windows taskbar icon/button via :func:`set_app_user_model_id`. Pass a custom
    ``theme`` to re-skin.
    """
    set_app_user_model_id(app_id)

    if app is None:
        app = QApplication.instance()
    if app is None:
        return

    # QStyleFactory.create returns None for unknown keys; Fusion ships with Qt
    # on every platform, so this is a safe no-op guard rather than a hard dep.
    style = QStyleFactory.create('Fusion')
    if style is not None:
        app.setStyle(style)
    app.setPalette(build_palette(theme))
    # Theme tooltips app-wide (a QToolTip-only sheet leaves all other widgets,
    # which set their own per-widget stylesheets, untouched).
    app.setStyleSheet(build_styles(theme)['TOOLTIP_STYLE'])


# --------------------------------------------------------------------------- #
# Per-widget stylesheets (templates -> generated strings)
# --------------------------------------------------------------------------- #
# ``$name`` placeholders (string.Template) so the literal CSS braces stay
# untouched. Filled from a theme by build_styles().
_TEMPLATES = {
    'BUTTON_STYLE': Template(
        "QPushButton { border-radius: 4px; background-color: $base; "
        "border-style: outset; color: $fg; font-weight: bold; padding: 4px; } "
        "QPushButton:pressed { background-color: $accent; border-style: inset; "
        "font-weight: bold; }"),

    'LABEL_STYLE': Template("QLabel { color: $fg; font-weight: bold; }"),

    # Tooltips: Fusion otherwise falls back to the OS default (light box), which
    # clashes with the dark UI. Applied app-wide by apply_app_style().
    'TOOLTIP_STYLE': Template(
        "QToolTip { color: $fg; background-color: $bg; "
        "border: 1px solid $accent; padding: 4px; border-radius: 3px; }"),

    # Spinboxes: colour text + selection only; Fusion draws the dark field,
    # themed border and the native +/- glyphs from the palette.
    'DSPIN_STYLE': Template(
        "QDoubleSpinBox { color: $fg; selection-background-color: $accent; "
        "selection-color: $base; }"),
    'SPIN_STYLE': Template(
        "QSpinBox { color: $fg; selection-background-color: $accent; "
        "selection-color: $base; }"),

    'COMBO_STYLE': Template(
        # No explicit background-color on the closed box: let Fusion paint it from
        # the palette (Button = base), so it matches the spin/line-edit fields and
        # the control-center tools that keep their own colour-only combo sheets.
        # A flat background-color here made this combo look different from all the
        # others.
        "QComboBox { color: $fg; "
        "selection-color: $base; selection-background-color: $accent; "
        "outline: none; } "
        # Once a QComboBox carries any stylesheet, Qt stops applying the palette
        # to its popup view, so the dropdown items fall back to a default (light)
        # background — the "strange" colour behind the selected label. Style the
        # view explicitly to keep the dark theme on the open list too.
        "QComboBox QAbstractItemView { background-color: $base; color: $fg; "
        "selection-background-color: $accent; selection-color: $base; "
        "outline: none; }"),

    'LINEEDIT_STYLE': Template(
        "QLineEdit { color: $accent; selection-background-color: $accent; "
        "selection-color: $base; }"),

    # Flat, unbulky tick: a hollow rounded outline when off, an accent fill with
    # a drawn checkmark ($check SVG) when on. One source of truth for every
    # control-center tool's checkboxes.
    'CHECKBOX_STYLE': Template("""
    QCheckBox {
        color: $fg;
        background-color: transparent;
        font-weight: bold;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 15px;
        height: 15px;
        background-color: transparent;
        border: 1px solid $border;
        border-radius: 4px;
    }
    QCheckBox::indicator:hover {
        border: 1px solid $accent;
    }
    QCheckBox::indicator:pressed {
        background-color: $hover;
    }
    QCheckBox::indicator:checked {
        background-color: $accent;
        border: 1px solid $accent;
        image: url($check);
    }
    QCheckBox::indicator:checked:hover {
        border: 1px solid $fg;
    }
    QCheckBox::indicator:disabled {
        border: 1px solid $base;
    }
"""),

    'SCROLL_STYLE': Template("""
    QScrollArea { border: none; background: transparent; }
    QScrollBar:vertical {
        border: none; background: $track; width: 10px; margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: $fg; min-height: 20px; border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover { background: $accent; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
"""),

    'TAB_STYLE': Template("""
    QTabWidget::pane {
        border: 1px solid $track;
        top: -1px;
        background: $base;
    }
    QTabBar::tab {
        height: 22px;
        font-weight: bold;
        color: $fg;
        background: $base;
        border: 1px solid $track;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 2px 10px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        color: $accent;
        background: $border;
        border-bottom: 2px solid $accent;
    }
    QTabBar::tab:hover {
        background: $hover;
    }
"""),
}


def build_styles(theme=DEFAULT_THEME):
    """
    Return a dict of per-widget stylesheet strings rendered from *theme*.

    Keys: ``BUTTON_STYLE``, ``LABEL_STYLE``, ``TOOLTIP_STYLE``, ``DSPIN_STYLE``,
    ``SPIN_STYLE``, ``COMBO_STYLE``, ``LINEEDIT_STYLE``, ``CHECKBOX_STYLE``,
    ``SCROLL_STYLE``, ``TAB_STYLE``.
    """
    subs = {
        'bg':     _css(theme.bg),
        'base':   _css(theme.base),
        'border': _css(theme.border),
        'fg':     _css(theme.fg),
        'accent': _css(theme.accent),
        'track':  _css(theme.track),
        'hover':  _css(theme.hover),
        'check':  _CHECK_ICON,
    }
    return {name: tmpl.substitute(subs) for name, tmpl in _TEMPLATES.items()}


# --------------------------------------------------------------------------- #
# Default-theme convenience constants (backwards-compatible exports)
# --------------------------------------------------------------------------- #
BG     = _css(DEFAULT_THEME.bg)
BASE   = _css(DEFAULT_THEME.base)
BORDER = _css(DEFAULT_THEME.border)
FG     = _css(DEFAULT_THEME.fg)
ACCENT = _css(DEFAULT_THEME.accent)

_STYLES = build_styles(DEFAULT_THEME)
BUTTON_STYLE   = _STYLES['BUTTON_STYLE']
LABEL_STYLE    = _STYLES['LABEL_STYLE']
TOOLTIP_STYLE  = _STYLES['TOOLTIP_STYLE']
DSPIN_STYLE    = _STYLES['DSPIN_STYLE']
SPIN_STYLE     = _STYLES['SPIN_STYLE']
COMBO_STYLE    = _STYLES['COMBO_STYLE']
LINEEDIT_STYLE = _STYLES['LINEEDIT_STYLE']
CHECKBOX_STYLE = _STYLES['CHECKBOX_STYLE']
SCROLL_STYLE   = _STYLES['SCROLL_STYLE']
TAB_STYLE      = _STYLES['TAB_STYLE']
