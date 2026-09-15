#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6 import QtCore
from atomize.general_modules.gui_style import REFINED_STYLES
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction, QDropEvent
from PyQt6.QtWidgets import QListView, QDockWidget, QWidget, QAbstractItemView

class QueueList(QDockWidget):
    def __init__(self, window):
        super(QueueList, self).__init__()
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)

        self.setTitleBarWidget(QWidget(self))
        
        self.namelist_model = QStandardItemModel()
        self.namelist_view = CustomListView()

        self.namelist_view.setStyleSheet(REFINED_STYLES['PLOT_LIST_STYLE'] + 'QListView { border: none; }')
        self.namelist_view.setTextElideMode(Qt.TextElideMode.ElideMiddle)

        self.namelist_view.setModel(self.namelist_model)
        self.namelist_model.rowsInserted.connect(self.sync_items)
        self.namelist_model.rowsRemoved.connect(self.sync_items)
        self.namelist_model.rowsMoved.connect(self.sync_items)
        self.namelist_model.dataChanged.connect(self.sync_items)
        self.namelist_model.modelReset.connect(self.sync_items)

        self.setWidget(self.namelist_view)
        self.window = window
        self.plot_dict = {}

        #self.namelist_view.doubleClicked.connect(self.activate_item)
        self.namelist_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        delete_action = QAction("Remove from Queue", self.namelist_view)
        delete_action.triggered.connect(self.delete_item)
        self.namelist_view.addAction(delete_action)
        clear_action = QAction("Remove All", self.namelist_view)
        clear_action.triggered.connect(lambda: self.clear())
        self.namelist_view.addAction(clear_action)

    def sync_items(self, *args):
        self.plot_dict = {
            str(row): self.namelist_model.index(row, 0).data(Qt.ItemDataRole.UserRole)
            for row in range(self.namelist_model.rowCount())
        }

    def mark_running(self, path, queued=False):
        if not queued:
            self.namelist_model.insertRow(0, self.create_item(path))
        item = self.namelist_model.item(0)
        self.namelist_view.running = True
        item.setText(f'Running: {path}')
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self.namelist_view.setCurrentIndex(item.index())

    def finish_running(self):
        if self.namelist_view.running:
            self.namelist_view.running = False
            self.namelist_model.removeRow(0)

    def delete_item(self):
        index = self.namelist_view.currentIndex()
        item = self.namelist_model.itemFromIndex(index)
        if item is None:            # empty queue / nothing selected
            return
        if self.namelist_view.running and index.row() == 0:
            return
        self.namelist_model.removeRow(index.row())

    def __getitem__(self, item):
        return self.plot_dict[item]

    def __setitem__(self, name, plot):
        self.namelist_model.appendRow(self.create_item(plot))

    def create_item(self, plot):
        model = QStandardItem(plot)
        model.setData(plot, Qt.ItemDataRole.UserRole)
        model.setToolTip(plot)
        model.setEditable(False)
        model.setFlags(model.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)
        return model

    def __contains__(self, value):
        return value in self.plot_dict

    def __delitem__(self, name):
        for row, path in enumerate(self.values()):
            if path == name and not (self.namelist_view.running and row == 0):
                self.namelist_model.removeRow(row)
                return

    def keys(self):
        return list(self.plot_dict.keys())

    def values(self):
        return list(self.plot_dict.values())

    def clear(self, force=False):
        if self.namelist_view.running and not force:
            self.namelist_model.removeRows(1, self.namelist_model.rowCount() - 1)
        else:
            self.namelist_view.running = False
            self.namelist_model.clear()


class CustomListView(QListView):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.running = False

    def blocks_running_move(self, event):
        if not self.running:
            return False
        if any(index.row() == 0 for index in self.selectedIndexes()):
            return True
        return (self.indexAt(event.position().toPoint()).row() == 0
                and self.dropIndicatorPosition() != QAbstractItemView.DropIndicatorPosition.BelowItem)

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        if self.blocks_running_move(event):
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if self.blocks_running_move(event):
            event.ignore()
            return
        super().dropEvent(event)
