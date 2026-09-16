"""Optional shared Output panel for the Atomize workspace."""

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from atomize.general_modules.gui_style import REFINED_STYLES
from atomize.main import local_config


class OutputScroll(QtCore.QObject):
    """Follow new messages or preserve the visible text across layout changes."""

    def __init__(self, editor, button):
        super().__init__(editor)
        self.editor = editor
        self.scrollbar = editor.verticalScrollBar()
        self.button = button
        self.restoring = False
        self.anchor = QtGui.QTextCursor(editor.document())
        self.anchor.setKeepPositionOnInsert(True)
        self.horizontal = 0
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._restore)
        self.input_timer = QtCore.QTimer(self)
        self.input_timer.setSingleShot(True)
        self.input_timer.timeout.connect(self._input_finished)
        editor.setCenterOnScroll(False)
        editor.installEventFilter(self)
        editor.viewport().installEventFilter(self)
        editor.verticalScrollBar().installEventFilter(self)
        editor.verticalScrollBar().valueChanged.connect(self._scrolled)
        editor.horizontalScrollBar().valueChanged.connect(self._horizontal_scrolled)
        editor.document().contentsChange.connect(self.schedule)
        editor.textChanged.connect(self.schedule)
        button.toggled.connect(self._toggled)

    def schedule(self, *args):
        if not self.restoring and not self.input_timer.isActive():
            self.timer.start(0)

    def _remember(self):
        self.anchor = self.editor.cursorForPosition(QtCore.QPoint(0, 0))
        self.anchor.setKeepPositionOnInsert(True)
        self.horizontal = self.editor.horizontalScrollBar().value()

    def _scrolled(self, value):
        if self.restoring or self.timer.isActive() or self.input_timer.isActive():
            return
        self.input_timer.start(0)

    def _input_finished(self):
        self.restoring = True
        try:
            scrollbar = self.editor.verticalScrollBar()
            following = scrollbar.value() >= scrollbar.maximum()
            blocker = QtCore.QSignalBlocker(self.button)
            self.button.setChecked(following)
            self._remember()
        finally:
            self.restoring = False

    def _horizontal_scrolled(self, value):
        if not self.restoring and not self.timer.isActive():
            self.horizontal = value

    def _toggled(self, following):
        if not following:
            self._remember()
        self.schedule()

    def _restore(self):
        self.restoring = True
        try:
            scrollbar = self.editor.verticalScrollBar()
            if self.button.isChecked():
                scrollbar.setValue(scrollbar.maximum())
            else:
                block = self.anchor.block()
                self.editor.blockBoundingRect(block)
                line = block.layout().lineForTextPosition(self.anchor.positionInBlock())
                offset = line.lineNumber() if line.isValid() else 0
                scrollbar.setValue(block.firstLineNumber() + offset)
                self.editor.horizontalScrollBar().setValue(self.horizontal)
        finally:
            self.restoring = False

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Type.KeyPress and event.matches(QtGui.QKeySequence.StandardKey.MoveToEndOfDocument):
            self.input_timer.stop()
            self.button.setChecked(True)
            self.schedule()
        elif (event.type() == QtCore.QEvent.Type.Wheel
              or event.type() == QtCore.QEvent.Type.KeyPress and event.key() in (
                  QtCore.Qt.Key.Key_Up, QtCore.Qt.Key.Key_Down, QtCore.Qt.Key.Key_PageUp,
                  QtCore.Qt.Key.Key_PageDown, QtCore.Qt.Key.Key_Home, QtCore.Qt.Key.Key_End)
              or watched is self.scrollbar and (
                  event.type() == QtCore.QEvent.Type.MouseButtonPress
                  or event.type() == QtCore.QEvent.Type.MouseMove and event.buttons())):
            self.timer.stop()
            self.input_timer.start(0)
        elif event.type() in (QtCore.QEvent.Type.Resize, QtCore.QEvent.Type.Show):
            self.schedule()
        return super().eventFilter(watched, event)


class OutputPanel(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.area = window.dockarea3
        config_dir = Path(local_config.load_config()[0]).parent
        self.settings = QtCore.QSettings(str(config_dir / 'workspace.ini'), QtCore.QSettings.Format.IniFormat)
        self.shared = self.settings.value('output/shared', False, type=bool)
        self.right = self.settings.value('output/right', False, type=bool)
        self.settings.remove('output/visible')

        grid = window.gridLayout_tab
        buttons = grid.itemAtPosition(0, 0).widget()
        grid.removeWidget(buttons)
        grid.removeWidget(window.dockarea2)
        grid.removeWidget(self.area)
        self.container = QtWidgets.QWidget()
        self.panel_layout = QtWidgets.QVBoxLayout(self.container)
        self.panel_layout.addWidget(self.area)
        main_content = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout(main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(grid.spacing())
        content_layout.addWidget(buttons)
        content_layout.addWidget(window.dockarea2, 1)
        self.local_splitter = self._splitter()
        self.local_splitter.addWidget(main_content)
        grid.addWidget(self.local_splitter, 0, 0, 1, 2)
        grid.setRowStretch(1, 0)

        central_layout = window.centralWidget().layout()
        central_layout.removeWidget(window.tabwidget)
        self.shared_splitter = self._splitter()
        self.shared_splitter.addWidget(window.tabwidget)
        central_layout.addWidget(self.shared_splitter)

        self.header = QtWidgets.QWidget(window.dock_errors.label)
        header_layout = QtWidgets.QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 4, 0)
        header_layout.setSpacing(4)
        self.shared_button = QtWidgets.QCheckBox('Shared')
        self.shared_button.setStyleSheet(REFINED_STYLES['CHECKBOX_STYLE'])
        self.shared_button.setToolTip('Show Output on every tab')
        self.shared_button.setChecked(self.shared)
        self.shared_button.toggled.connect(self._toggle_shared)
        header_layout.addWidget(self.shared_button)
        header_layout.addSpacing(8)
        self.scroll_button = QtWidgets.QCheckBox('Auto-scroll')
        self.scroll_button.setStyleSheet(REFINED_STYLES['CHECKBOX_STYLE'])
        self.scroll_button.setToolTip('Follow new messages; scrolling up pauses, scrolling to the bottom resumes')
        self.scroll_button.setChecked(True)
        header_layout.addWidget(self.scroll_button)
        self.scrolling = OutputScroll(window.text_errors, self.scroll_button)
        self.position_button = self._button(self._toggle_position)
        header_layout.addWidget(self.position_button)
        self.area.setMinimumWidth(self.header.sizeHint().width() + 70)
        window.dock_errors.label.installEventFilter(self)
        window.installEventFilter(self)
        self._apply_layout()

    def _splitter(self):
        splitter = QtWidgets.QSplitter()
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        splitter.splitterMoved.connect(self._save_sizes)
        return splitter

    def _button(self, callback):
        button = QtWidgets.QPushButton()
        button.setFixedSize(18, 18)
        button.setStyleSheet(REFINED_STYLES['DOCK_CLOSE_STYLE'])
        button.clicked.connect(callback)
        return button

    def _size_key(self):
        scope = 'shared' if self.shared else 'main'
        position = 'right' if self.right else 'bottom'
        return f'output/sizes/{scope}/{position}'

    def _save_sizes(self, *args):
        if self.area.isVisible():
            sizes = self.splitter.sizes()
            if len(sizes) == 2 and all(size > 0 for size in sizes):
                self.settings.setValue(self._size_key(), sizes)
                self.settings.sync()

    def _apply_layout(self):
        self.scrolling.schedule()
        margin = 8 if self.shared else 0
        self.panel_layout.setContentsMargins(0 if self.right else margin, margin if self.right else 0, margin, margin)
        self.splitter = self.shared_splitter if self.shared else self.local_splitter
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal if self.right else QtCore.Qt.Orientation.Vertical)
        self.splitter.addWidget(self.container)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        self.container.show()
        self.area.show()
        sizes = self.settings.value(self._size_key(), [700, 300] if self.right else [700, 210])
        try:
            sizes = [int(size) for size in sizes]
            if len(sizes) != 2 or any(size <= 0 for size in sizes):
                raise ValueError
        except (TypeError, ValueError):
            sizes = [700, 300] if self.right else [700, 210]
        self.splitter.setSizes(sizes)
        self.position_button.setText('↓' if self.right else '→')
        self.position_button.setToolTip('Move Output below' if self.right else 'Move Output to the right')
        self.settings.setValue('output/shared', self.shared)
        self.settings.setValue('output/right', self.right)
        self.settings.sync()
        self._position_header()

    def _position_header(self):
        label = self.window.dock_errors.label
        width = self.header.sizeHint().width()
        label.setContentsMargins(0, 0, width, 0)
        self.header.setGeometry(max(0, label.width() - width), 0, width, label.height())
        self.header.raise_()

    def _toggle_shared(self, shared):
        self._save_sizes()
        self.shared = shared
        if not shared:
            self.window.tabwidget.setCurrentWidget(self.window.tab1)
        self._apply_layout()

    def _toggle_position(self):
        self._save_sizes()
        self.right = not self.right
        self._apply_layout()

    def eventFilter(self, watched, event):
        if watched is self.window.dock_errors.label and event.type() == QtCore.QEvent.Type.Resize:
            self._position_header()
        elif watched is self.window and event.type() == QtCore.QEvent.Type.Close:
            self._save_sizes()
            self.settings.sync()
        return super().eventFilter(watched, event)
