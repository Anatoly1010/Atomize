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
dataclass. The module is framework-only (PyQt6) with no Atomize imports, so it
can be dropped into upstream Atomize's ``general_modules`` — together with the
``check.svg`` glyph that ``CHECKBOX_STYLE`` renders (it lives next to this file
and is referenced by an absolute ``url(...)`` resolved from ``__file__``).

Typical use, right after creating the ``QApplication``::

    from atomize.general_modules.gui_style import apply_app_style
    app = QApplication(sys.argv)
    apply_app_style(app, app_id='Atomize.MainWindow')   # Fusion + dark palette
    ...

The exported module-level constants (``BG``, ``FG``, ``ACCENT`` and the
``*_STYLE`` sheets) use :data:`REFINED_THEME` and are kept for the
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
    dim:    tuple = (142, 150, 178)  # secondary text (hints, units, help chips)
    accent: tuple = (211, 194, 78)   # selection / highlight (gold)
    track:  tuple = (43, 43, 77)     # scrollbar track / tab-pane border
    hover:  tuple = (73, 73, 107)    # hover background (tabs, etc.)
    light:  tuple = (103, 103, 137)  # lighter edge for the Fusion 3-D frame
    dark:   tuple = (32, 32, 52)     # darker edge / shadow for the frame
    input_bg: tuple = (38, 40, 58)
    input_hover: tuple = (48, 51, 74)
    input_focus: tuple = (44, 47, 68)


DEFAULT_THEME = Theme()

REFINED_THEME = Theme(
    bg=(32, 33, 49), base=(52, 55, 79), border=(73, 77, 104),
    fg=(226, 229, 240), dim=(164, 171, 194), accent=(211, 194, 78),
    track=(41, 43, 64), hover=(64, 68, 94), light=(83, 88, 117),
    dark=(25, 27, 41),
)

TAB_MARGINS = (16, 8, 16, 12)


def _css(rgb):
    """``(r, g, b)`` -> ``'rgb(r, g, b)'`` for use inside a stylesheet."""
    return 'rgb(%d, %d, %d)' % rgb


# Absolute path to the checkmark glyph drawn inside a ticked QCheckBox. Kept
# next to this module and resolved from ``__file__`` so it survives the
# ``os.chdir(libs)`` the main window does at startup and works from any cwd.
# Forward slashes: Qt stylesheet ``url(...)`` wants '/', including on Windows.
_CHECK_ICON = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'check.svg').replace('\\', '/')
_PLUS_ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plus.svg').replace('\\', '/')
_MINUS_ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'minus.svg').replace('\\', '/')
_CHEVRON_ICON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chevron.svg').replace('\\', '/')


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
# Linux desktop identity
# --------------------------------------------------------------------------- #
def set_desktop_identity(app, wm_class='Atomize', desktop_file='atomize'):
    """
    Bind this process to its freedesktop entry so the shell uses the themed icon.

    On X11 Qt fills WM_CLASS with (script name, ``applicationName``), and the
    shell matches a window to a ``.desktop`` file through ``StartupWMClass``;
    setting ``applicationName`` is therefore what makes that match land. On
    Wayland there is no WM_CLASS and no way to push a window icon at all - the
    match is made on the xdg-shell app-id, which Qt takes from
    ``desktopFileName`` - so both are set here.

    Without the match the shell has no themed icon to look up: on X11 it falls
    back to rescaling the raster published over ``_NET_WM_ICON``, and on Wayland
    the window simply has no icon. Install the entries with
    ``icons/install_desktop.py``.

    No-op on Windows and macOS, which identify applications by other means.
    """
    if sys.platform.startswith(('win32', 'darwin')) or app is None:
        return
    try:
        app.setApplicationName(wm_class)
        app.setApplicationDisplayName('Atomize')
        app.setDesktopFileName(desktop_file)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def apply_app_style(app=None, app_id=None, theme=REFINED_THEME, desktop=False):
    """
    Pin the QApplication to the Fusion style with the theme's dark palette.

    Fusion renders identically on Windows and Linux, fixing the windowsvista
    quirks (wrong combo colours, inconsistent borders, missing spin +/- signs).
    Call once right after ``QApplication(sys.argv)``.

    Pass ``app_id`` (e.g. ``'Atomize.MainWindow'``) to give the process its own
    Windows taskbar icon/button via :func:`set_app_user_model_id`. Pass a custom
    ``theme`` to re-skin.

    ``desktop`` claims an installed Linux desktop entry via
    :func:`set_desktop_identity`, so the shell draws the icon from the theme at
    the exact size it needs. Use ``True`` in the main-window process, or the
    tool's icon suffix in a control-centre tool - ``desktop='cw'`` binds to
    ``atomize-cw.desktop`` and the ``atomize-cw`` themed icon, which are what
    ``icons/make_icons.py`` emits for ``icons/svg/icon_cw.svg``.
    """
    set_app_user_model_id(app_id)

    if app is None:
        app = QApplication.instance()
    if app is None:
        return

    if desktop is True:
        set_desktop_identity(app)
    elif desktop:
        name = 'atomize-%s' % desktop
        set_desktop_identity(app, wm_class=name, desktop_file=name)

    # QStyleFactory.create returns None for unknown keys; Fusion ships with Qt
    # on every platform, so this is a safe no-op guard rather than a hard dep.
    style = QStyleFactory.create('Fusion')
    if style is not None:
        app.setStyle(style)
    app.setPalette(build_palette(theme))
    # Theme tooltips app-wide (a QToolTip-only sheet leaves all other widgets,
    # which set their own per-widget stylesheets, untouched).
    styles = build_refined_styles(theme)
    app.setStyleSheet(styles['TOOLTIP_STYLE'] + styles['MENU_STYLE'] + styles['SEPARATOR_STYLE'] + styles['INPUT_STYLE'])


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

    # Field labels are normal weight: bold is reserved for section headings and
    # actions, so a dense parameter panel keeps a readable hierarchy.
    'LABEL_STYLE': Template("QLabel { color: $fg; }"),

    # Gold bold section heading (the one bold level inside a parameter panel).
    'HEADING_STYLE': Template(
        "QLabel { color: $accent; font-weight: bold; font-size: 13px; }"),

    # Dimmed secondary text: units, short hints, status lines.
    'HINT_STYLE': Template("QLabel { color: $dim; }"),

    # Round '?' chip that opens a help popup; quiet until hovered.
    'HELP_CHIP_STYLE': Template("""
    QToolButton {
        color: $dim;
        background-color: transparent;
        border: 1px solid $border;
        border-radius: 8px;
        font-weight: bold;
        padding: 0px;
    }
    QToolButton:hover { color: $accent; border: 1px solid $accent; }
    QToolButton:checked { color: $accent; border: 1px solid $accent; }
"""),

    # Disclosure header for a collapsible 'Advanced' block.
    'DISCLOSURE_STYLE': Template("""
    QToolButton {
        color: $dim;
        background-color: transparent;
        border: none;
        font-weight: bold;
        text-align: left;
        padding: 2px 0px;
    }
    QToolButton:hover { color: $accent; }
"""),

    # Body of a help popup: a bordered card floating over the panel.
    'HELP_POPUP_STYLE': Template("""
    QWidget { background-color: $bg; }
    QLabel {
        color: $fg;
        background-color: $bg;
        border: 1px solid $accent;
        border-radius: 3px;
        padding: 8px;
    }
"""),

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
    QScrollBar:horizontal {
        border: none; background: $track; height: 10px; margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background: $fg; min-width: 20px; border-radius: 5px;
    }
    QScrollBar::handle:horizontal:hover { background: $accent; }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
    QScrollBar::corner { background: $track; }
"""),

    'TAB_STYLE': Template("""
    /* awg_phasing_insys' tab colours on the strip, but no pane fill and no
       frame: the pages inherit the window background, so a filled pane would
       show only as a thick band of $base framing the content. */
    QTabWidget::pane {
        border: none;
        top: -1px;
        background: transparent;
        padding: 10px 0px 0px 0px;
    }
    QTabBar {
        background: transparent;
        qproperty-drawBase: 0;
    }
    QTabBar::tab {
        height: 22px;
        font-weight: bold;
        color: $fg;
        background: $base;
        border: none;
        border-bottom: 2px solid $track;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        padding: 3px 12px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        color: $accent;
        background: $border;
        border-bottom: 2px solid $accent;
    }
    QTabBar::tab:hover:!selected {
        background: $hover;
        border-bottom: 2px solid $border;
    }
"""),
}


def build_styles(theme=DEFAULT_THEME):
    """
    Return a dict of per-widget stylesheet strings rendered from *theme*.

    Keys: ``BUTTON_STYLE``, ``LABEL_STYLE``, ``HEADING_STYLE``, ``HINT_STYLE``,
    ``HELP_CHIP_STYLE``, ``DISCLOSURE_STYLE``, ``HELP_POPUP_STYLE``,
    ``TOOLTIP_STYLE``, ``DSPIN_STYLE``, ``SPIN_STYLE``, ``COMBO_STYLE``,
    ``LINEEDIT_STYLE``, ``CHECKBOX_STYLE``, ``SCROLL_STYLE``, ``TAB_STYLE``.
    """
    subs = {
        'bg':     _css(theme.bg),
        'base':   _css(theme.base),
        'border': _css(theme.border),
        'fg':     _css(theme.fg),
        'dim':    _css(theme.dim),
        'accent': _css(theme.accent),
        'track':  _css(theme.track),
        'hover':  _css(theme.hover),
        'check':  _CHECK_ICON,
    }
    return {name: tmpl.substitute(subs) for name, tmpl in _TEMPLATES.items()}


def build_refined_styles(theme=REFINED_THEME):
    """Styles for the main workspace and the first refreshed instrument panel."""
    styles = build_styles(theme)
    bg, base, border, fg, dim, accent, panel, hover, dark = (
        _css(getattr(theme, name)) for name in
        ('bg', 'base', 'border', 'fg', 'dim', 'accent', 'track', 'hover', 'dark')
    )
    def input_surface(selectors):
        normal = ', '.join(selectors)
        hovered = ', '.join(selector + ':hover:enabled' for selector in selectors)
        focused = ', '.join(selector + ':focus:enabled' for selector in selectors)
        return f"""
            {normal} {{ background: {_css(theme.input_bg)}; border: 1px solid {panel}; border-radius: 2px; }}
            {hovered} {{ background: {_css(theme.input_hover)}; }}
            {focused} {{ background: {_css(theme.input_focus)}; border-color: {accent}; }}
        """

    styles['SCROLL_STYLE'] += f"""
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{ background: {border}; }}
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{ background: {dim}; }}
    """
    styles['TAB_STYLE'] += f"""
        QTabWidget::pane {{ padding: 0px; top: 0px; border: 1px solid {panel}; }}
        QTabBar::tab {{ border: 1px solid {panel}; border-bottom: 2px solid {panel};
            outline: none; }}
        QTabBar::tab:selected {{ background: {panel}; border-bottom-color: {accent}; }}
        QTabBar::tab:focus {{ border-color: {accent}; }}
    """
    styles['ANALYSIS_TAB_STYLE'] = styles['TAB_STYLE'] + "QTabWidget::pane { padding: 10px 8px 8px 8px; }"
    styles['CHECKBOX_STYLE'] += f"""
        QCheckBox::indicator:unchecked {{ background: {base}; border-color: {border}; }}
        QCheckBox::indicator:unchecked:hover {{ border-color: {accent}; }}
        QCheckBox::indicator:unchecked:disabled {{ background: {panel}; border-color: {base}; }}
    """
    styles['SEPARATOR_STYLE'] = f"""
        QFrame[frameShape="4"] {{ border: none; background: {base}; min-height: 1px; max-height: 1px; }}
        QFrame[frameShape="5"] {{ border: none; background: {base}; min-width: 1px; max-width: 1px; }}
    """
    styles['RADIO_STYLE'] = f"""
        QRadioButton {{ color: {fg}; background: transparent; spacing: 6px; }}
        QRadioButton::indicator {{ width: 13px; height: 13px; border-radius: 7px;
            background: {base}; border: 1px solid {border}; }}
        QRadioButton::indicator:checked {{ background: {accent}; border-color: {accent}; }}
        QRadioButton::indicator:hover {{ border-color: {accent}; }}
        QRadioButton::indicator:disabled {{ background: {panel}; border-color: {base}; }}
    """
    styles['WINDOW_STYLE'] = f"""
        QMainWindow {{ background: {bg}; color: {fg}; }}
        QLabel {{ color: {fg}; font-weight: normal; }}
        QWidget#launcherPanel {{ background: {bg}; border: 1px solid {panel}; border-radius: 4px; }}
        QWidget#workspaceActions {{ border-right: 1px solid {panel}; }}
    """ + styles['TAB_STYLE'] + styles['SCROLL_STYLE'] + styles['SEPARATOR_STYLE']
    styles['BUTTON_STYLE'] = f"""
        QPushButton {{ background: {base}; color: {fg}; border: 1px solid {panel};
            border-radius: 4px; padding: 6px 12px; font-weight: 500; outline: none; }}
        QPushButton:hover {{ background: {hover}; border-color: {border}; }}
        QPushButton:focus {{ border: 1px solid {accent}; }}
        QPushButton:pressed {{ background: {accent}; color: {dark}; }}
        QPushButton:disabled {{ background: {panel}; color: {dim}; border-color: {panel}; }}
        QPushButton[text="Stop"]:hover:enabled {{ background: #49303d; border-color: #eda6aa; }}
        QPushButton[text="Stop"]:focus:enabled {{ border-color: #eda6aa; }}
        QPushButton[text="Start"]:hover:enabled, QPushButton[text="Start Experiment"]:hover:enabled,
        QPushButton[text="Run Pulses"]:hover:enabled {{ background: #3b382b; border-color: {accent}; }}
    """
    styles['PRIMARY_BUTTON_STYLE'] = styles['BUTTON_STYLE'] + f"""
        QPushButton:enabled {{ background: {accent}; color: {dark}; border-color: {accent}; }}
        QPushButton:hover:enabled, QPushButton[text="Start"]:hover:enabled,
        QPushButton[text="Start Experiment"]:hover:enabled,
        QPushButton[text="Run Pulses"]:hover:enabled {{ background: #e2d477; border-color: #e2d477; }}
        QPushButton:focus:enabled {{ border: 2px solid {fg}; }}
        QPushButton:pressed:enabled, QPushButton[text="Start"]:pressed:enabled,
        QPushButton[text="Start Experiment"]:pressed:enabled,
        QPushButton[text="Run Pulses"]:pressed:enabled {{ background: #b9a93e; border-color: #b9a93e; }}
    """
    styles['START_BUTTON_STYLE'] = styles['BUTTON_STYLE'] + f"""
        QPushButton:hover:enabled {{ background: #3b382b; border-color: {accent}; }}
        QPushButton:focus:enabled {{ border-color: {accent}; }}
    """
    styles['STOP_BUTTON_STYLE'] = styles['BUTTON_STYLE'] + f"""
        QPushButton:hover:enabled {{ background: #49303d; border-color: #eda6aa; }}
        QPushButton:focus:enabled {{ border-color: #eda6aa; }}
        QPushButton:pressed:enabled {{ background: #eda6aa; color: {dark}; }}
    """
    styles['WORKSPACE_ACTION_STYLE'] = styles['BUTTON_STYLE'] + f"""
        QPushButton {{ background: {base}; border-color: {panel};
            border-radius: 4px; text-align: left; padding: 4px 10px; }}
        QPushButton:hover {{ background: {base}; border-color: {accent}; color: {accent}; }}
        QPushButton:focus {{ border-color: {accent}; }}
        QPushButton:pressed {{ background: {accent}; color: {dark}; border-color: {accent}; }}
    """
    styles['WORKSPACE_ACTIVE_STYLE'] = styles['WORKSPACE_ACTION_STYLE'] + f"""
        QPushButton:enabled {{ color: {accent}; border-color: {accent}; }}
    """
    styles['ACTION_HEADING_STYLE'] = f"""
        QLabel {{ color: {dim}; font-size: 12px; font-weight: 500; padding-left: 10px; }}
    """
    styles['SECTION_HEADING_STYLE'] = f"QLabel {{ color: {dim}; font-size: 12px; font-weight: 500; }}"
    styles['ACTIVE_BUTTON_STYLE'] = styles['BUTTON_STYLE'] + f"""
        QPushButton:enabled {{ background: {panel}; color: {accent}; border-color: {accent}; }}
    """
    styles['EDITOR_STYLE'] = f"""
        QPlainTextEdit {{ background: {dark}; color: {fg}; border: none;
            selection-background-color: {accent}; selection-color: {dark}; padding: 8px; }}
        QMenu {{ background: {panel}; color: {fg}; border: 1px solid {border}; }}
        QMenu::item:selected {{ background: {hover}; }}
    """ + styles['SCROLL_STYLE']
    styles['LIST_STYLE'] = f"""
        QListView {{ background: {dark}; color: {fg}; border: 1px solid {panel};
            outline: none; font-weight: normal; }}
        QListView::item {{ padding: 8px; border: none; }}
        QListView::item:selected {{ background: {base}; color: {accent}; }}
        QListView::item:hover {{ background: {hover}; }}
        QMenu {{ background: {panel}; color: {fg}; border: 1px solid {border}; }}
        QMenu::item:selected {{ background: {hover}; }}
    """ + styles['SCROLL_STYLE']
    styles['DOCK_LABEL_STYLE'] = f"""
        DockLabel {{ background: {bg}; color: {dim}; padding: 0px 24px 0px 8px;
            border: 1px solid {panel};
            font-size: 12px; font-weight: 500; }}
    """
    styles['DOCK_CONTENT_STYLE'] = f"""
        QWidget#dockContent {{ background: {dark}; border: 1px solid {panel}; border-top: none; }}
    """
    styles['DOCK_STYLE'] = f"background-color: {bg};"
    styles['DOCK_CLOSE_STYLE'] = f"""
        QPushButton {{ background: transparent; color: {dim}; border: 1px solid {panel};
            border-radius: 3px; padding: 0px; outline: none; }}
        QPushButton:hover {{ background: {hover}; color: {fg}; border-color: {dim}; }}
        QPushButton:focus {{ border: 1px solid {accent}; }}
    """
    styles['PLOT_LIST_STYLE'] = styles['LIST_STYLE'] + f"""
        QListView {{ border-top: none; padding: 1px; }}
        QListView::item {{ padding: 3px 5px; margin: 0px;
            border: none; border-left: 2px solid transparent; border-radius: 3px; }}
        QListView::item:selected {{ background: {panel}; color: {accent}; border-left-color: {accent}; }}
        QListView::item:selected:!active {{ background: {panel}; color: {accent}; border-left-color: {accent}; }}
        QListView::item:hover:!selected {{ background: {base}; }}
    """
    styles['FIELD_STYLE'] = f"""
        QDoubleSpinBox, QSpinBox {{ color: {fg}; selection-background-color: {accent};
            selection-color: {dark}; background: {base}; border: 1px solid {panel}; padding: 4px; }}
        QDoubleSpinBox:focus, QSpinBox:focus {{ border-color: {accent}; }}
        QDoubleSpinBox:disabled, QSpinBox:disabled {{ color: {dim}; }}
        QDoubleSpinBox::up-button, QSpinBox::up-button {{ subcontrol-origin: border;
            subcontrol-position: top right; width: 16px; border: none; margin: 1px; }}
        QDoubleSpinBox::down-button, QSpinBox::down-button {{ subcontrol-origin: border;
            subcontrol-position: bottom right; width: 16px; border: none; margin: 1px; }}
        QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {{ image: url({_PLUS_ICON}); width: 9px; height: 9px; }}
        QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {{ image: url({_MINUS_ICON}); width: 9px; height: 9px; }}
    """
    styles['COMPACT_FIELD_STYLE'] = styles['FIELD_STYLE'] + "QDoubleSpinBox, QSpinBox { padding: 0px 3px; }"
    styles['DSPIN_STYLE'] = styles['SPIN_STYLE'] = styles['COMPACT_FIELD_STYLE']
    styles['COMPACT_TEXT_STYLE'] = f"""
        QTextEdit, QPlainTextEdit {{ background: {base}; color: {fg}; border: 1px solid {panel};
            selection-background-color: {accent}; selection-color: {dark}; padding: 1px 3px; }}
    """
    styles['COMBO_STYLE'] = f"""
        QComboBox {{ background: {base}; color: {fg}; border: 1px solid {panel};
            padding: 0px 3px; selection-background-color: {panel}; selection-color: {accent}; }}
        QComboBox:focus {{ border-color: {accent}; }}
        QComboBox::drop-down {{ width: 18px; border: none; }}
        QComboBox::down-arrow {{ image: url({_CHEVRON_ICON}); width: 9px; height: 9px; }}
        QComboBox QAbstractItemView {{ background: {base}; color: {fg}; border: 1px solid {panel};
            selection-background-color: {panel}; selection-color: {accent}; outline: none; }}
    """
    styles['LINEEDIT_STYLE'] = f"""
        QLineEdit {{ background: {base}; color: {fg}; border: 1px solid {panel};
            selection-background-color: {accent}; selection-color: {dark}; padding: 1px 3px; }}
        QLineEdit:focus {{ border-color: {accent}; }}
    """
    styles['PROGRESS_STYLE'] = f"""
        QProgressBar {{ background: {panel}; color: {accent}; border: 1px solid {panel};
            border-radius: 4px; font-weight: bold; text-align: right; margin-right: 40px; height: 20px; }}
        QProgressBar::chunk {{ background: #c1cae3; border-radius: 2px; }}
    """
    styles['MENU_STYLE'] = f"""
        QMenu, QMenu QWidget {{ background: {bg}; color: {fg}; }}
        QMenu {{ border: 1px solid {panel}; padding: 4px; }}
        QMenu::item {{ padding: 4px 24px 4px 8px; }}
        QMenu::item:selected {{ background: {panel}; color: {accent}; }}
        QMenu::item:disabled {{ color: {dim}; }}
        QMenu::separator {{ height: 1px; background: {panel}; margin: 4px; }}
        QMenuBar {{ color: {fg}; font-weight: bold; font-size: 14px;
            border-bottom: 2px solid {border}; margin-bottom: 1px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0.95 {bg}, stop:1.0 {dim}); padding-top: 2px; padding-bottom: 1px; }}
        QMenuBar::item:selected {{ background: {panel}; color: {accent}; }}
        QMenu QLineEdit, QMenu QAbstractSpinBox, QMenu QComboBox {{ background: {base};
            color: {fg}; border: 1px solid {panel}; }}
    """
    styles['FILE_DIALOG_STYLE'] = f"""
        QDialog {{ background: {bg}; color: {fg}; }}
        QLabel {{ color: {fg}; }}
        QListView, QTreeView {{ background: {dark}; color: {fg}; border: 1px solid {panel};
            selection-background-color: {panel}; selection-color: {accent}; outline: none; }}
        QListView::item, QTreeView::item {{ padding: 3px 5px; }}
        QListView::item:selected, QTreeView::item:selected {{ background: {panel}; color: {accent}; }}
        QListView::item:hover:!selected, QTreeView::item:hover:!selected {{ background: {base}; }}
        QLineEdit, QComboBox {{ background: {bg}; color: {fg}; border: 1px solid {panel};
            padding: 3px 5px; selection-background-color: {accent}; selection-color: {dark}; }}
        QLineEdit:focus, QComboBox:focus {{ border-color: {accent}; }}
        QComboBox QAbstractItemView {{ background: {dark}; color: {fg}; border: 1px solid {panel};
            selection-background-color: {panel}; selection-color: {accent}; outline: none; }}
        QHeaderView::section {{ background: {bg}; color: {dim}; border: none;
            border-bottom: 1px solid {panel}; padding: 4px; }}
        QToolButton {{ background: {bg}; color: {fg}; border: 1px solid {panel};
            border-radius: 3px; padding: 3px; outline: none; }}
        QToolButton:hover, QToolButton:focus {{ border-color: {accent}; }}
    """ + styles['BUTTON_STYLE'] + styles['SCROLL_STYLE']
    styles['INPUT_STYLE'] = input_surface(('QDoubleSpinBox', 'QSpinBox', 'QComboBox', 'QTextEdit', 'QPlainTextEdit'))
    for key, selectors in (
        ('FIELD_STYLE', ('QDoubleSpinBox', 'QSpinBox')),
        ('COMPACT_FIELD_STYLE', ('QDoubleSpinBox', 'QSpinBox')),
        ('COMPACT_TEXT_STYLE', ('QTextEdit', 'QPlainTextEdit')),
        ('EDITOR_STYLE', ('QPlainTextEdit',)),
        ('LINEEDIT_STYLE', ('QLineEdit',)),
        ('COMBO_STYLE', ('QComboBox',)),
        ('FILE_DIALOG_STYLE', ('QLineEdit', 'QComboBox')),
        ('MENU_STYLE', ('QMenu QLineEdit', 'QMenu QAbstractSpinBox', 'QMenu QComboBox')),
    ):
        styles[key] += input_surface(selectors)
    styles['DSPIN_STYLE'] = styles['SPIN_STYLE'] = styles['COMPACT_FIELD_STYLE']
    return styles


REFINED_STYLES = build_refined_styles()


def style_file_dialog(dialog):
    """Match file pickers to the workspace palette and selection treatment."""
    palette = build_palette(REFINED_THEME)
    palette.setColor(QPalette.ColorRole.Highlight, _qcolor(REFINED_THEME.track))
    palette.setColor(QPalette.ColorRole.HighlightedText, _qcolor(REFINED_THEME.accent))
    dialog.setPalette(palette)
    dialog.setStyleSheet(REFINED_STYLES['FILE_DIALOG_STYLE'])


# --------------------------------------------------------------------------- #
# Default-theme convenience constants (backwards-compatible exports)
# --------------------------------------------------------------------------- #
BG     = _css(REFINED_THEME.bg)
BASE   = _css(REFINED_THEME.base)
BORDER = _css(REFINED_THEME.track)
FG     = _css(REFINED_THEME.fg)
DIM    = _css(REFINED_THEME.dim)
ACCENT = _css(REFINED_THEME.accent)

_STYLES = REFINED_STYLES
BUTTON_STYLE   = _STYLES['BUTTON_STYLE']
LABEL_STYLE    = _STYLES['LABEL_STYLE']
HEADING_STYLE  = _STYLES['HEADING_STYLE']
HINT_STYLE     = _STYLES['HINT_STYLE']
HELP_CHIP_STYLE   = _STYLES['HELP_CHIP_STYLE']
DISCLOSURE_STYLE  = _STYLES['DISCLOSURE_STYLE']
HELP_POPUP_STYLE  = _STYLES['HELP_POPUP_STYLE']
TOOLTIP_STYLE  = _STYLES['TOOLTIP_STYLE']
DSPIN_STYLE    = _STYLES['DSPIN_STYLE']
SPIN_STYLE     = _STYLES['SPIN_STYLE']
COMBO_STYLE    = _STYLES['COMBO_STYLE']
LINEEDIT_STYLE = _STYLES['LINEEDIT_STYLE']
CHECKBOX_STYLE = _STYLES['CHECKBOX_STYLE']
SCROLL_STYLE   = _STYLES['SCROLL_STYLE']
TAB_STYLE      = _STYLES['TAB_STYLE']
ANALYSIS_TAB_STYLE = _STYLES['ANALYSIS_TAB_STYLE']
SEPARATOR_STYLE = _STYLES['SEPARATOR_STYLE']
RADIO_STYLE = _STYLES['RADIO_STYLE']
