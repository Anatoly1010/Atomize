#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6 import QtCore
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

        self.namelist_view.setStyleSheet("""
            QListView {
                background-color: rgb(42, 42, 64); 
                color: rgb(211, 194, 78); 
                selection-color: rgb(211, 194, 78); 
                selection-background-color: rgb(63, 63, 97); 
                border: 1px solid rgb(63, 63, 97);
                outline: none;
            }
            QListView::item:hover { 
                background-color: rgb(211, 194, 78); 
                color: rgb(42, 42, 64);
            }

            QScrollBar:vertical {
                border: none;
                background: rgb(43, 43, 77); 
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgb(193, 202, 227); 
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgb(211, 194, 78); 
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        self.namelist_view.setModel(self.namelist_model)
        self.namelist_view.selectionModel().currentChanged.connect(self.list_elements)

        self.setWidget(self.namelist_view)
        self.window = window
        self.plot_dict = {}

        #self.namelist_view.doubleClicked.connect(self.activate_item)
        self.namelist_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        delete_action = QAction("Remove from Queue", self.namelist_view)
        delete_action.triggered.connect(self.delete_item)
        self.namelist_view.addAction(delete_action)
        clear_action = QAction("Remove All", self.namelist_view)
        clear_action.triggered.connect(self.clear)
        self.namelist_view.addAction(clear_action)

    def list_elements(self, previous_index, current_index):
        self.get_items_to_dict(self.namelist_view, previous_index.row(), current_index.row())

    def get_items_to_dict(self, list_view, pr, cur):
        """
        # Function to get items from QListView to a dictionary
        """
        items_dict = {}
        model = list_view.model()
        for row in range(model.rowCount()):
            # Create a model index for the specific row (column 0 for lists)
            index = model.index(row, 0)
            # Retrieve data using the DisplayRole (the visible text)
            item_text = model.data(index, Qt.ItemDataRole.DisplayRole)
            items_dict[row] = item_text
        
        if self.namelist_view.drop == 1:
            self.namelist_view.drop = 0
            b = items_dict.pop(pr)
            items_dict[cur] = b
            keys_list = list(items_dict.keys())

            for i in range( len(keys_list) ):
                items_dict[i] = items_dict.pop(keys_list[i])

        self.plot_dict = items_dict.copy()
        return items_dict

    def delete_item(self):
        index = self.namelist_view.currentIndex()
        item = self.namelist_model.itemFromIndex(index)
        del self[str(item.text())]

    def __getitem__(self, item):
        return self.plot_dict[item]

    def __setitem__(self, name, plot):
        #if name not in self.keys():
        model = QStandardItem(plot)
        model.setEditable(False)
        model.setFlags(model.flags() & ~Qt.ItemFlag.ItemIsDropEnabled)
        self.namelist_model.appendRow(model)
        self.plot_dict[name] = plot

    def __contains__(self, value):
        return value in self.plot_dict

    def __delitem__(self, name):
        for key, value in self.plot_dict.items():
            if value == name:
                key_to_del = key
                break

        index_of_key = list(self.plot_dict.keys()).index(key_to_del)
        self.namelist_model.removeRow(self.namelist_model.findItems(name)[0].index().row())
        del self.plot_dict[ list(self.plot_dict.keys())[index_of_key] ]

    def keys(self):
        return list(self.plot_dict.keys())

    def values(self):
        return list(self.plot_dict.values())

    def clear(self):
        self.namelist_model.clear()
        self.plot_dict = {}


class CustomListView(QListView):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.drop = 0
        self.setStyleSheet("QListView::item:selected:active {background-color: rgb(63, 63, 97); color: rgb(211, 194, 78); } QListView::item:hover {background-color: rgb(48, 48, 75); }")
        self.setStyleSheet("QMenu::item:selected {background-color: rgb(48, 48, 75);  } QMenu::item:selected:active {background-color: rgb(63, 63, 97); }")

    def dropEvent(self, event: QDropEvent):
        self.drop = 1
        super().dropEvent(event)
