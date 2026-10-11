"""Remember each workspace window's normal size."""

from pathlib import Path

from PyQt6 import QtCore

from atomize.main import local_config

# How long after a restore a size change is treated as the compositor's, not the user's.
SETTLE_MS = 1000


class WindowSize(QtCore.QObject):
    def __init__(self, window, key='window/size', settings=None):
        super().__init__(window)
        self.window = window
        self.key = key
        if settings is None:
            config_dir = Path(local_config.load_config()[0]).parent
            settings = QtCore.QSettings(str(config_dir / 'workspace.ini'), QtCore.QSettings.Format.IniFormat)
        self.settings = settings
        size = self.settings.value(key)
        self._size_to_restore = size if isinstance(size, QtCore.QSize) and not size.isEmpty() else None
        self._settle_size = None
        window.installEventFilter(self)

    def _restore(self):
        """Restore after the first paint to avoid GNOME's initial auto-maximize."""
        size = self._size_to_restore
        if size is None:
            return
        if self.window.isMaximized():
            self.window.showNormal()
            return
        available = self.window.screen().availableGeometry()
        self.window.resize(size.boundedTo(available.size()))
        self.window.move(available.center() - self.window.rect().center())
        self._size_to_restore = None
        # A GNOME dock launch reverts the restore once; hold the size until it settles.
        self._settle_size = self.window.size()
        QtCore.QTimer.singleShot(SETTLE_MS, self._end_settle)

    def _end_settle(self):
        self._settle_size = None

    def eventFilter(self, watched, event):
        if event.type() == QtCore.QEvent.Type.Paint and self._size_to_restore is not None:
            QtCore.QTimer.singleShot(0, self._restore)
        elif event.type() == QtCore.QEvent.Type.Resize and self._settle_size is not None:
            if self.window.size() != self._settle_size and not (
                    self.window.isMaximized() or self.window.isMinimized() or self.window.isFullScreen()):
                QtCore.QTimer.singleShot(0, lambda: self._settle_size is not None
                                         and self.window.resize(self._settle_size))
        elif (event.type() == QtCore.QEvent.Type.Resize and self._size_to_restore is None
              and self.window.isVisible() and not (self.window.isMaximized()
                                                  or self.window.isMinimized() or self.window.isFullScreen())):
            self.settings.setValue(self.key, self.window.size())
            self.settings.sync()
        elif event.type() == QtCore.QEvent.Type.Close:
            self.settings.sync()
        return super().eventFilter(watched, event)
