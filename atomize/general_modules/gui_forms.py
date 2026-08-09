# -*- coding: utf-8 -*-
"""
Shared form-layout primitives for the Atomize control-center tools.

Why this module exists
---------------------
The parameter panels of the analysis tools (``data_treatment``,
``data_treatment_2d``, ``deer_analysis``, ``sequence_calculator``,
``excitation_profile``, ``spin_dynamics_sim``) had each grown their own
near-identical ``_label`` / ``_note`` / ``_heading`` / ``_hline`` helpers, and
each laid its rows out with a private ``QHBoxLayout``. Two consequences: the
label column was ragged (controls started at a different x in every block of
the same panel), and long explanatory paragraphs were parked permanently on the
canvas, so a tab with four knobs could carry thirteen lines of prose and the
panel inherited the height of its wordiest tab.

This module supplies the missing pieces once:

* :class:`FormPanel` — a grid with **one fixed label column**, so every row of
  every tab in a tool aligns on the same vertical rule.
* :func:`help_chip` / :class:`HelpPopup` — a 16 px ``?`` that opens the long
  explanation in a floating card. The text is kept verbatim; it simply stops
  occupying layout space.
* :class:`Collapsible` — a disclosure header for the secondary knobs, so a tab
  shows what is actually turned per run and folds the rest away.
* :func:`hint`, :func:`heading`, :func:`hline`, :func:`scroll_wrap`,
  :func:`live_update_checkbox`, :func:`apply_row_metrics` — the helpers the
  tools were each redefining.

Typography follows ``gui_style``: bold is reserved for section headings and
actions, field labels are normal weight, and secondary text (units, one-line
summaries, status) is dimmed. Framework-only (PyQt6 + ``gui_style``), so it can
travel to upstream Atomize alongside ``gui_style.py``.

Typical use inside a tab builder::

    from atomize.general_modules.gui_forms import FormPanel

    p = FormPanel()
    p.add_title('Straighten a tilted dipolar ridge', help=_SHEAR_HELP)
    p.add_row('Slope k', self.shear_k, self.fit_k_btn)
    p.add_row('Origin t_ref', self.shear_ref, self.auto_btn)
    adv = p.add_advanced()
    adv.add_row('Fit window', self.shear_win)
    p.add_button_row(self.apply_btn)
    p.add_stretch()
    return p
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QLabel, QFrame, QGridLayout, QHBoxLayout,
                             QVBoxLayout, QToolButton, QCheckBox, QScrollArea,
                             QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
                             QLineEdit, QSizePolicy)

from atomize.general_modules.gui_style import (LABEL_STYLE, HEADING_STYLE,
                                               HINT_STYLE, HELP_CHIP_STYLE,
                                               DISCLOSURE_STYLE,
                                               HELP_POPUP_STYLE,
                                               CHECKBOX_STYLE, SCROLL_STYLE)

# Width of the label column. Wide enough for the longest field name the tools
# use once the parenthetical explanations move to tooltips and suffixes.
LABEL_COL_W = 150

# Row heights the tools already standardised on: spinboxes need a fixed height
# for the native +/- frame to render fully; combos and buttons match for
# alignment.
ROW_H = 26
EDIT_H = 21

# Field / button widths. Pinning them keeps a value box from being stretched
# across the panel just because its row has room; every row that uses them ends
# in a stretch so the grid still has something expandable (see FormPanel).
FIELD_W = 150     # spin boxes, combos, line edits
BTN_W = 78        # small trailing button on a field's row (Auto / Max / End)
ACTION_W = 150    # the row of actions at the foot of a tab (Run / Export)

# Air on each side of the plot/panel divider, and the panel's own inner margins.
# The panel's left margin is 0 on purpose: PANEL_GAP alone then sets the gutter,
# so the panel's first control sits as far from the divider as the plot's edge
# does on the other side.
PANEL_GAP = 12
PANEL_MARGINS = (0, 4, 10, 8)

_POPUP_W = 380

# Right inset for the '?' chip, so a tab's scroll bar never sits on top of it.
CHIP_INSET = 14

# Point size for a subscript in a control label (the base font is 9 pt).
# This is the house rule; plot rich text uses a larger base and sets its own.
LABEL_SUB_PT = 10

# Qt's "no maximum" sentinel, used to tell a pinned width from an unset one.
_QT_MAX_W = 16777215


# --------------------------------------------------------------------------- #
# Text primitives
# --------------------------------------------------------------------------- #
def label(text):
    """A normal-weight field label."""
    lab = QLabel(text)
    lab.setStyleSheet(LABEL_STYLE)
    return lab


def heading(text):
    """A bold gold section heading."""
    lab = QLabel(text)
    lab.setStyleSheet(HEADING_STYLE)
    return lab


def hint(text, wrap=True):
    """Dimmed secondary text: a one-line summary, a unit, a status line."""
    lab = QLabel(text)
    lab.setStyleSheet(HINT_STYLE)
    lab.setWordWrap(wrap)
    lab.setTextFormat(Qt.TextFormat.RichText)
    return lab


def sub(base, subscript, pt=LABEL_SUB_PT):
    """
    ``base`` with a subscript, for a rich-text label. Qt's default subscript is
    ~0.7 em and renders too small against the 9 pt control font, so the size is
    set explicitly. Plain-text widgets (a check box) cannot show this — use the
    Unicode subscript characters there instead.
    """
    return '%s<sub><span style="font-size: %dpt">%s</span></sub>' % (
        base, pt, subscript)


def hline():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Plain)
    line.setStyleSheet('color: rgb(83, 83, 117);')
    return line


def vline():
    """
    The rule between a tool's plot area and its parameter panel. Shared so the
    divider — and the air either side of it, see :data:`PANEL_GAP` — is
    identical in every tool.
    """
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Plain)
    line.setStyleSheet('color: rgb(83, 83, 117);')
    return line


# --------------------------------------------------------------------------- #
# Help chip + popup
# --------------------------------------------------------------------------- #
class HelpPopup(QWidget):
    """
    A floating card holding one explanation. Created with the ``Popup`` window
    flag so a click anywhere outside dismisses it, which is what makes it a
    viable home for text that used to live on the layout: no close button, no
    modality, no state to manage.
    """

    def __init__(self, text, anchor):
        super().__init__(anchor.window(), Qt.WindowType.Popup)
        self.setStyleSheet(HELP_POPUP_STYLE)
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        body = QLabel(f'<div style="line-height: 145%;">{text}</div>')
        body.setStyleSheet(HELP_POPUP_STYLE)
        body.setWordWrap(True)
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setFixedWidth(_POPUP_W)
        box.addWidget(body)

    def show_at(self, anchor):
        self.adjustSize()
        pos = anchor.mapToGlobal(anchor.rect().bottomRight())
        x, y = pos.x() - self.width(), pos.y() + 4
        screen = anchor.screen()
        if screen is not None:
            geo = screen.availableGeometry()
            x = max(geo.left() + 4, min(x, geo.right() - self.width() - 4))
            if y + self.height() > geo.bottom():
                y = max(geo.top() + 4, pos.y() - self.height() - anchor.height() - 4)
        self.move(x, y)
        self.show()


def help_chip(text):
    """
    A 16 px ``?`` that opens *text* in a :class:`HelpPopup`. The same text is
    the chip's tooltip, so hovering is enough for a quick read and clicking
    pins it open for a long one.
    """
    btn = QToolButton()
    btn.setText('?')
    btn.setStyleSheet(HELP_CHIP_STYLE)
    btn.setFixedSize(16, 16)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setToolTip(text)
    btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def open_popup():
        popup = getattr(btn, '_popup', None)
        if popup is None:
            popup = HelpPopup(text, btn)
            btn._popup = popup
        popup.show_at(btn)

    btn.clicked.connect(open_popup)
    return btn


# --------------------------------------------------------------------------- #
# Collapsible block
# --------------------------------------------------------------------------- #
class Collapsible(QWidget):
    """
    A disclosure header over a :class:`FormPanel` body, collapsed by default.

    The body is a full FormPanel sharing the parent's label column width, so
    folded rows line up with the visible ones when opened.
    """

    def __init__(self, title='Advanced', label_width=LABEL_COL_W, parent=None):
        super().__init__(parent)
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(2)
        self._title = title
        self.header = QToolButton()
        self.header.setStyleSheet(DISCLOSURE_STYLE)
        self.header.setCheckable(True)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.header.setText(f'▸  {title}')
        self.header.toggled.connect(self._on_toggled)
        box.addWidget(self.header)
        self.body = FormPanel(label_width=label_width)
        self.body.setVisible(False)
        box.addWidget(self.body)

    def _on_toggled(self, on):
        self.header.setText(('▾  ' if on else '▸  ') + self._title)
        self.body.setVisible(on)

    def set_expanded(self, on):
        self.header.setChecked(on)


# --------------------------------------------------------------------------- #
# The form panel
# --------------------------------------------------------------------------- #
class FormPanel(QWidget):
    """
    A parameter block on a two-column grid: fixed-width label column, stretching
    field column. Every ``add_*`` call appends one row, so a tab builder reads as
    the list of rows the user sees.
    """

    def __init__(self, label_width=LABEL_COL_W, margins=(0, 0, 0, 0), spacing=6,
                 field_width=None, button_width=None, parent=None):
        super().__init__(parent)
        self.label_width = label_width
        # Optional fixed field / trailing-button widths. A row that uses them
        # ends in a stretch, so the grid still has something expandable —
        # without it Qt cannot place the slack anywhere and centres the whole
        # form, leaving dead space down both sides of the panel.
        self.field_width = field_width
        self.button_width = button_width
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(*margins)
        self.grid.setVerticalSpacing(spacing)
        self.grid.setHorizontalSpacing(8)
        self.grid.setColumnMinimumWidth(0, label_width)
        self.grid.setColumnStretch(0, 0)
        self.grid.setColumnStretch(1, 1)
        self._row = 0

    # -- rows ------------------------------------------------------------- #
    def add_row(self, text, *widgets, help=None, tooltip=None, stretch=None,
                full=False):
        """
        One labelled row. Several *widgets* share the field column (a spinbox
        plus its ``Auto`` button, say); *stretch* is an optional per-widget
        stretch list. A *help* string adds a ``?`` chip after the label.

        *text* may be a ready-made widget rather than a string — a label whose
        text changes with the mode, or a check box that gates the field beside
        it — in which case it occupies the label column.

        *full* lets this row stretch to the panel width instead of taking the
        common fixed widths. Nothing on the row is pinned, so *stretch* decides
        the split — which is how a button is made to line up with a column of a
        stretched toolbar above it (``stretch=[3, 1]`` puts it under the fourth
        button of a four-button row).
        """
        if text is None:
            cell = self._field_cell(widgets, stretch, full=full)
            self.grid.addLayout(cell, self._row, 0, 1, 2)
        else:
            lab = text if isinstance(text, QWidget) else label(text)
            if tooltip:
                lab.setToolTip(tooltip)
            if help:
                head = QHBoxLayout()
                head.setContentsMargins(0, 0, 0, 0)
                head.setSpacing(4)
                head.addWidget(lab)
                head.addWidget(help_chip(help))
                head.addStretch(1)
                self.grid.addLayout(head, self._row, 0)
            else:
                self.grid.addWidget(lab, self._row, 0)
            if widgets:
                self.grid.addLayout(self._field_cell(widgets, stretch, full=full),
                                    self._row, 1)
        self._row += 1
        return self._row - 1

    _FIELDS = (QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit)

    def _field_cell(self, widgets, stretch=None, full=False):
        cell = QHBoxLayout()
        cell.setContentsMargins(0, 0, 0, 0)
        # same as the grid's horizontal spacing and add_button_row's, so a
        # trailing button lands on the same vertical as one in an action row
        cell.setSpacing(8)
        # only a row that actually pinned something needs the trailing stretch;
        # adding it regardless would absorb the width an unpinned field wants
        fixed = False
        for i, w in enumerate(widgets):
            s = stretch[i] if stretch and i < len(stretch) else 1
            if isinstance(w, QWidget):
                # a width the caller pinned already wins: some fields need more
                # room than the common one (a combo with long item text)
                pinned = w.maximumWidth() < _QT_MAX_W
                if pinned:
                    s = 0
                    fixed = True
                elif self.button_width and isinstance(w, QPushButton) and not full:
                    w.setFixedWidth(self.button_width)
                    s = 0
                    fixed = True
                elif self.field_width and isinstance(w, self._FIELDS) and not full:
                    need = self.field_width
                    if isinstance(w, QComboBox) and w.count():
                        need = max(need, combo_content_width(w))
                    w.setFixedWidth(need)
                    s = 0
                    fixed = True
                elif isinstance(w, self._FIELDS):
                    # spin boxes are Minimum and combos Preferred, so a stretch
                    # factor alone leaves them at their hint width
                    w.setSizePolicy(QSizePolicy.Policy.Expanding,
                                    w.sizePolicy().verticalPolicy())
                cell.addWidget(w, s)
            else:
                cell.addLayout(w, s)
        if fixed:
            cell.addStretch(1)
        return cell

    def add_title(self, summary, help=None):
        """
        A dim one-line summary of what the tab does, with the long explanation
        behind a ``?`` chip. This is the row that replaces a wall of prose.
        """
        row = QHBoxLayout()
        # inset on the right so the chip clears a scroll bar when the tab scrolls
        row.setContentsMargins(0, 0, CHIP_INSET, 0)
        row.setSpacing(6)
        lab = hint(summary)
        row.addWidget(lab, 1)
        if help:
            chip = help_chip(help)
            row.addWidget(chip, 0, Qt.AlignmentFlag.AlignTop)
        self.grid.addLayout(row, self._row, 0, 1, 2)
        self._row += 1
        return lab

    def add_heading(self, text, help=None):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(heading(text))
        if help:
            row.addWidget(help_chip(help))
        row.addStretch(1)
        self.grid.addLayout(row, self._row, 0, 1, 2)
        self._row += 1

    def add_check(self, text, tooltip=None, checked=False, help=None):
        """A checkbox spanning both columns. Explanations go to *tooltip*."""
        box = QCheckBox(text)
        box.setStyleSheet(CHECKBOX_STYLE)
        if tooltip:
            box.setToolTip(tooltip)
        box.setChecked(checked)
        if help:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)
            row.addWidget(box)
            row.addWidget(help_chip(help))
            row.addStretch(1)
            self.grid.addLayout(row, self._row, 0, 1, 2)
        else:
            self.grid.addWidget(box, self._row, 0, 1, 2)
        self._row += 1
        return box

    def add_widget(self, widget, span=2):
        """A widget spanning the full panel width (a plot, a table, a note)."""
        self.grid.addWidget(widget, self._row, 0, 1, span)
        self._row += 1
        return widget

    def add_layout(self, layout, span=2):
        self.grid.addLayout(layout, self._row, 0, 1, span)
        self._row += 1
        return layout

    def add_button_row(self, *buttons, width=None):
        """
        A row of actions spanning the panel. With *width* each button is pinned
        to it and the row ends in a stretch, so the actions stay a readable size
        instead of stretching to whatever the panel happens to be.
        """
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        # the form grid's horizontal spacing, so a pinned first button puts the
        # second one exactly on the field column
        row.setSpacing(8)
        for b in buttons:
            if width:
                b.setFixedWidth(width)
            row.addWidget(b)
        if width:
            row.addStretch(1)
        self.grid.addLayout(row, self._row, 0, 1, 2)
        self._row += 1
        return row

    def add_hint(self, text):
        return self.add_widget(hint(text))

    def add_sep(self):
        return self.add_widget(hline())

    def add_advanced(self, title='Advanced', expanded=False):
        """Append a collapsible block and return its inner FormPanel."""
        block = Collapsible(title, label_width=self.label_width)
        block.set_expanded(expanded)
        self.grid.addWidget(block, self._row, 0, 1, 2)
        self._row += 1
        return block.body

    def add_stretch(self):
        """
        Absorb the leftover height so rows stay top-aligned. Without this a tab
        with few rows spreads them down the panel and the tool looks as though
        its controls float.
        """
        self.grid.setRowStretch(self._row, 1)
        self._row += 1

    def set_row_stretch(self, row, factor):
        self.grid.setRowStretch(row, factor)


# --------------------------------------------------------------------------- #
# Misc shared widgets / passes
# --------------------------------------------------------------------------- #
def live_update_checkbox(tooltip=None):
    """
    The 'recompute on every parameter change' toggle, which the tools had each
    spelled out as a 31-character label.
    """
    box = QCheckBox('Live update')
    box.setStyleSheet(CHECKBOX_STYLE)
    box.setToolTip(tooltip or 'Recompute and redraw the preview on every '
                              'parameter change, without pressing the action '
                              'button.')
    return box


def scroll_wrap(widget):
    """Put *widget* in a themed, borderless vertical scroll area."""
    area = QScrollArea()
    area.setStyleSheet(SCROLL_STYLE)
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setWidget(widget)
    return area


def apply_row_metrics(root, row_h=ROW_H, edit_h=EDIT_H):
    """
    Give every input in *root* the shared row height and the repo-wide ``+/-``
    spinbox buttons, so rows line up across blocks that were built separately.
    """
    for wdg in root.findChildren((QComboBox, QPushButton)):
        wdg.setMinimumHeight(row_h)
    for spin in root.findChildren((QSpinBox, QDoubleSpinBox)):
        spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        spin.setMinimumHeight(row_h)
    for le in root.findChildren(QLineEdit):
        le.setMinimumHeight(edit_h)


def equal_grid(columns, spacing=6):
    """
    A grid whose *columns* are equal width. Rows added to it line up exactly —
    including the gaps, which a stretch factor cannot reproduce: a two-item row
    split 3:1 has one gap where a four-button row has three, so its last item
    comes out wider than the fourth button. Put the toolbar and the rows that
    must align under it in one of these instead.
    """
    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(spacing)
    grid.setVerticalSpacing(spacing)
    for c in range(columns):
        grid.setColumnStretch(c, 1)
    return grid


def combo_content_width(combo):
    """
    Width a combo needs for its longest item. Asking Qt (via AdjustToContents)
    rather than guessing from the text keeps the arrow, frame and padding in the
    sum, so a long item cannot silently clip when the field width is pinned.
    """
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
    return combo.sizeHint().width()


def compact(widget):
    """Stop a field stretching to the full column width (a narrow spinbox)."""
    widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return widget
