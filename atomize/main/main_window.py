#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import atexit
import os
import sys
import time
import json
import ctypes
import logging
import signal
import socket
import threading
import webbrowser
import subprocess
import configparser
import platform
import numpy as np
from . import widgets
import pyqtgraph as pg
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QSharedMemory, QSize, QEventLoop
from PyQt6.QtGui import QColor, QIcon, QStandardItem, QStandardItemModel, QAction
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QListView, QDockWidget, QVBoxLayout, QWidget, QGridLayout, QTabWidget, QMainWindow, QPlainTextEdit, QHBoxLayout, QApplication, QPushButton, QWidget, QFileDialog, QLabel, QSizePolicy
from PyQt6.QtNetwork import QLocalServer
from PyQt6 import QtCore, QtGui
from pyqtgraph.dockarea import DockArea
import atomize.main.queue as queue
import atomize.main.codeeditor as codeedit
import atomize.main.local_config as lconf
import atomize.main.messenger_socket_server as socket_server
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

class MainWindow(QMainWindow):
    """
    A main window class.
    """
    def __init__(self, *args, **kwargs):
        """
        A function for connecting actions and creating a main window.
        """
        additional_path = kwargs.pop('ptm', '')
        super(MainWindow, self).__init__(*args, **kwargs)

        path_to_main = Path(__file__).parent
        self.destroyed.connect(lambda: self._on_destroyed())

        self.design_setting()

        path_to_main_lib = os.path.join(path_to_main, additional_path)
        os.chdir(path_to_main_lib)

        self.icon_path = os.path.join(path_to_main,'icon.ico')
        self.setWindowIcon(QIcon(self.icon_path))

        # important attribures
        if len(sys.argv) > 1 and sys.argv[1] != '':  # for bash option
            self.script = sys.argv[1]
            self.open_file(self.script)
        elif len(sys.argv) == 1:
            self.script = '' # for not opened script
        self.test_flag = 0 # flag for not running script if test is failed
        self.flag_opened_script_changed = 0 # flag for saving changes in the opened script
        #self.path = os.path.join(path_to_main,'atomize/tests')
        self.path = os.path.join(path_to_main, '..', 'tests')

        self.queue = 0
        self.success = False

        # Liveplot server settings
        self.server = QLocalServer()
        self.server.removeServer('LivePlot')
        self.server.listen('LivePlot')
        self.server.newConnection.connect(self.accept)
        self.bytes = bytearray()
        self.target_size = 0
        self.meta = None
        self.insert_dock_right = True
        self.conns = []
        self.shared_mems = []
        signal.signal(signal.SIGINT, self.close)
        self.system = platform.system()

        # configuration data
        #path_config_file = os.path.join(path_to_main,'atomize/config.ini')
        path_config_file = os.path.join(path_to_main, '..', 'config.ini')
        path_config_file_device = os.path.join(path_to_main, '..', 'device_modules/config')
        path_config_file, self.path_config2 = lconf.copy_config(path_config_file, path_config_file_device)

        config = configparser.ConfigParser()
        config.read(path_config_file)
        # directories
        self.open_dir = str(config['DEFAULT']['open_dir'])
        if self.open_dir == '':
            self.open_dir = lconf.load_scripts(os.path.join(path_to_main, '..', 'tests'))

        self.script_dir = str(config['DEFAULT']['script_dir'])
        if self.script_dir == '':
            self.script_dir = lconf.load_scripts(os.path.join(path_to_main, '..', 'tests'))

        print( f'SYSTEM: {self.system}' )
        print( f'DATA DIRECTORY: {self.open_dir}' )
        print( f'SCRIPTS DIRECTORY: {self.script_dir}' )
        print( f'MAIN CONFIG PATH: {path_config_file}' )
        print( f'DEVICE CONFIG DIRECTORY: {self.path_config2}' )

        self.path = self.script_dir
        self.test_timeout = int(config['DEFAULT']['test_timeout']) * 1000 # in ms

        # for running different processes using QProcess
        self.process_text_editor = QtCore.QProcess(self)
        self.process_python = QtCore.QProcess(self)
        self.pid = 0

        if self.system == 'Windows':
            self.process_text_editor.setProgram(str(config['DEFAULT']['editorW']))
            self.process_python.setProgram('python.exe')
            print('EDITOR: ' + str(config['DEFAULT']['editorW']))
        elif self.system == 'Linux':
            self.editor = str(config['DEFAULT']['editor'])
            if self.editor == 'nano' or self.editor == 'vi':
                self.process_text_editor.setProgram('xterm')
                print(f'EDITOR: nano / vi')
            else:
                self.process_text_editor.setProgram(str(config['DEFAULT']['editor']))
                print('EDITOR: ' + str(config['DEFAULT']['editor']))
            self.process_python.setProgram('python3')

        self.process_python.finished.connect(self.on_finished_script)

    ##### Liveplot Functions

    def close(self, sig = None, frame = None):
        #print('closing')
        for conn in self.conns:
            conn.close()
        for shm in self.shared_mems:
            shm.detach()
        self._on_destroyed()
        #QApplication.instance().exit()

    def accept(self):
        logging.debug('connection accepted')
        conn = self.server.nextPendingConnection()
        conn.waitForReadyRead()
        key = str(conn.read(36).decode())
        memory = QSharedMemory()
        memory.setKey(key)
        memory.attach()
        logging.debug('attached to memory %s with size %s'%(key, memory.size()))
        #11-04-2021; Should be uncommented in case of problems
        #atexit.register(memory.detach)
        self.conns.append(conn)
        self.shared_mems.append(memory)
        conn.readyRead.connect(lambda: self.read_from(conn, memory))
        conn.disconnected.connect(memory.detach)
        conn.write(b'ok')

    def read_from(self, conn, memory):
        logging.debug('reading data')
        try:
            self.meta = json.loads(conn.read(320).decode())
        except json.decoder.JSONDecodeError:
            #print('error')
            pass

        if self.meta['arrsize'] != 0:
            memory.lock()
            try:
                raw_data = memory.data()
                if raw_data is not None:
                    # Slice and create a view directly without copying yet
                    ba = raw_data[:self.meta['arrsize']]
                    # interpreted as the correct dtype
                    arr = np.frombuffer(ba, dtype = self.meta['dtype'])
                    # Reshape first, THEN copy while still LOCKED to ensure data integrity
                    arr = arr.reshape(self.meta['shape']).copy() 
                    conn.write(b'ok')
                else:
                    arr = None
            finally:
                # Using finally ensures the lock is released even if reshape/copy fails
                memory.unlock()
        else:
            arr = None

        self.do_operation(arr)

    def do_operation(self, arr = None):
        def clear(name):
            self.namelist[name].clear()

        def close(name):
            self.namelist[name].close()

        def remove(name):
            del self.namelist[name]

        meta = self.meta
        operation = meta['operation']
        name = meta['name']

        if name in self.namelist:
            pw = self.namelist[name]
            #if pw.closed:
            #    pw.closed = False
            #    self.dockarea.addDock(pw)

        elif name == "*":
            if operation == 'clear':
                list(map(clear, list(self.namelist.keys())))
            elif operation == 'close':
                list(map(close, list(self.namelist.keys())))
            elif operation == 'remove':
                list(map(remove, list(self.namelist.keys())))
            return
        else:
            if operation in ('clear', 'close', 'remove', 'none'):
                return
            pw = self.add_new_plot(meta['rank'], name)

        if operation == 'clear':
            pw.clear()
        elif operation == 'close':
            pw.close()
        elif operation == 'none':
            pass
        elif operation == 'remove':
            del self.namelist[name]


        elif operation == 'plot_y':
            start_step = meta['start_step']
            label = meta['label']
            if start_step is not None:
                x0, dx = start_step
                nx = len(arr)
                xs = np.linspace(x0, x0 + (nx - 1)*dx, nx)
                pw.plot(xs, arr, name=label, scatter='False')
            else:
                pw.plot(arr, name=label, scatter='False')


        elif operation == 'plot_xy':
            label = meta['label']
            xnam = meta['Xname']
            xscal = meta['X']
            ynam = meta['Yname']
            yscal = meta['Y']
            scat = meta['Scatter']
            taxis = meta['TimeAxis']
            verline = meta['Vline']
            tex = meta['value']
            pw.plot(arr[0], arr[1], parametric=True, name=label, xname=xnam, xscale =xscal,\
             yname=ynam, yscale =yscal, scatter=scat, timeaxis=taxis, vline=verline, text=tex)


        elif operation == 'plot_z':
            start_step = meta['start_step']
            xnam = meta['Xname']
            xscal = meta['X']
            ynam = meta['Yname']
            yscal = meta['Y']
            znam = meta['Zname']
            zscal = meta['Z']
            tex = meta['value']
            if start_step is not None:
                (x0, dx), (y0, dy) = start_step
                pw.setAxisLabels(xname=xnam, xscale =xscal, yname=ynam, yscale =yscal,\
                zname=znam, zscale =zscal)
                pw.setImage(arr, pos=(x0, y0), scale=(dx, dy) ) # , axes={'y':0, 'x':1}
                # Graph title
                if tex != '':
                    pw.setTitle(meta['value'])
            else:
                pw.setAxisLabels(xname=xnam, xscale =xscal, yname=ynam, yscale =yscal,\
                 zname=znam, zscale =zscal)
                pw.setImage(arr) #, axes={'y':0, 'x':1}
                # Graph title
                if tex != '':
                    pw.setTitle(meta['value'])


        elif operation == 'append_y':
            label = meta['label']
            xnam = meta['Xname']
            xscal = meta['X']
            ynam = meta['Yname']
            yscal = meta['Y']
            scat = meta['Scatter']
            taxis = meta['TimeAxis']
            verline = meta['Vline']
            
            xs, ys = pw.get_data(label)
            new_ys = list(ys)
            new_ys.append(meta['value'])
            start_step = meta['start_step']
            if start_step is not None:
                x0, dx = start_step
                nx = len(new_ys)
                xs = np.linspace(x0, x0 + (nx - 1)*dx, nx)
                pw.plot(xs, new_ys, name=label, xname=xnam, xscale =xscal, yname=ynam,\
                 yscale =yscal, scatter=scat, timeaxis=taxis, vline=verline)
            else:
                pw.plot(new_ys, name=label, xname=xnam, xscale =xscal, yname=ynam,\
                 yscale =yscal, scatter=scat, timeaxis=taxis, vline=verline)


        elif operation == 'append_xy':
            label = meta['label']
            xs, ys = pw.get_data(label)
            xn, yn = meta['value']
            new_xs = list(xs)
            new_xs.append(xn)
            new_ys = list(ys)
            new_ys.append(yn)
            pw.plot(new_xs, new_ys, parametric=True, name=label, scatter='False')


        elif operation == 'append_z':
            image = pw.get_data()
            if image is None:
                image = np.array([arr])
            else:
                try:
                    image = np.vstack((np.transpose(image), [arr]))
                except ValueError:
                    image = np.array([arr])
            start_step = meta['start_step']
            xnam = meta['Xname']
            xscal = meta['X']
            ynam = meta['Yname']
            yscal = meta['Y']
            znam = meta['Zname']
            zscal = meta['Z']
            if start_step is not None:
                (x0, dx), (y0, dy) = start_step
                pw.setAxisLabels(xname=xnam, xscale =xscal, yname=ynam, yscale =yscal,\
                 zname=znam, zscale =zscal)
                pw.setImage(image, pos=(x0, y0), scale=(dx, dy), axes={'y':0, 'x':1})
            else:
                pw.setAxisLabels(xname=xnam, xscale =xscal, yname=ynam, yscale =yscal)
                pw.setImage(image, axes={'y':0, 'x':1})


        elif operation == 'label':
            pw.setTitle(meta['value'])

    def add_new_plot(self, rank, name):
        pw = widgets.get_widget(rank, name)
        self.add_plot(pw)
        self.namelist[name] = pw
        return pw

    def add_plot(self, pw):
        self.insert_dock_right = not self.insert_dock_right
        self.dockarea.addDock(pw, position=['bottom', 'bottom'][self.insert_dock_right])
        #print(['bottom', 'right'][self.insert_dock_right])
        #self.dockarea.moveDock(pw, 'above', self.dock_list[-1])   ## move d6 to stack on top of d4

    #####################################################

    def design_setting(self):
        
        self.setObjectName("MainWindow")
        self.setWindowTitle("Atomize")

        screen_geometry = QApplication.primaryScreen().geometry()
        width = int(screen_geometry.width() * 0.6)
        height = int(screen_geometry.height() * 0.7)

        #int(screen_geometry.height() * 0.6)
        self.setMinimumSize(int(screen_geometry.width() * 0.6), 650)
        self.resize(width, height)

        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2

        self.move(x, y)
        
        self.setStyleSheet("""
            QMainWindow { background-color: rgb(42, 42, 64); }
            QTabWidget::pane {
            border: 1.5px solid rgb(40, 30, 45 );
            }
            QTabBar::tab { 
                width: 185px;
                height: 25px;
                font-weight: bold; 
                color: rgb(193, 202, 227);
                background: rgb(63, 63, 97);
                border: 1px solid rgb(43, 43, 77);
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                color: rgb(211, 194, 78);
                background: rgb(83, 83, 117); /* Чуть светлее при выборе */
                border-bottom: 2px solid rgb(211, 194, 78);
            }
            QTabBar::tab:hover {
                background: rgb(73, 73, 107);
            }

            QScrollBar:vertical { border: none; background: rgb(43, 43, 77); width: 10px; }
            QScrollBar::handle:vertical { background: rgb(193, 202, 227); border-radius: 5px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: rgb(211, 194, 78); }

        """)

        central_container = QWidget()
        self.setCentralWidget(central_container)
        main_window_layout = QVBoxLayout(central_container)
        main_window_layout.setContentsMargins(0, 0, 0, 0)

        self.tabwidget = QTabWidget()
        self.tab1 = QWidget()
        self.tabwidget.addTab(self.tab1, "Main")
        main_window_layout.addWidget(self.tabwidget)

        self.gridLayout_tab = QGridLayout(self.tab1)
        self.gridLayout_tab.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_tab.setSpacing(5)

        buttons_widget = QWidget()
        buttons_widget.setMinimumHeight(420)
        buttons_v_layout = QVBoxLayout(buttons_widget)
        #buttons_v_layout.setContentsMargins(10, 5, 10, 5)
        buttons_v_layout.setSpacing(5)

        buttons_v_layout.addStretch()

        self.button_open = QPushButton("&Open Script")
        self.button_edit = QPushButton("&Edit Script")
        self.button_test = QPushButton("&Test Script")
        self.button_reload = QPushButton("&Update Script")
        self.button_start = QPushButton("&Start Experiment")
        self.button_stop = QPushButton("Stop Experiment")
        self.button_queue = QPushButton("&Add to Queue")
        self.button_help = QPushButton("&Help")
        self.button_quit = QPushButton("&Quit")

        btn_list = [
            (self.button_open, self.open_file_dialog), (self.button_edit, self.edit_file),
            (self.button_test, lambda: self.test(self.script)), (self.button_reload, self.reload),
            (self.button_start, self.start_experiment), (self.button_stop, self.stop_script),
            (self.button_queue, self.add_to_queue), (self.button_help, self.help),
            (self.button_quit, self.quit)
        ]

        for btn, method in btn_list:
            btn.clicked.connect(method)
            btn.setFixedSize(140, 40)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, 
                              QSizePolicy.Policy.Fixed)
            buttons_v_layout.addWidget(btn)
            btn.setStyleSheet("""
                QPushButton {
                border-radius: 4px; background-color: rgb(63, 63, 97); 
                border-style: outset; color: rgb(193, 202, 227); font-weight: bold;
                padding: 2px 10px;
            }
                QPushButton:pressed { background-color: rgb(211, 194, 78); border-style: inset; }
            """)

        buttons_v_layout.addStretch()
        self.gridLayout_tab.addWidget(buttons_widget, 0, 0, 1, 1)

        self.textEdit = codeedit.CodeEditor(self)
        #self.textEdit.setReadOnly(True)
        self.textEdit.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        option = QtGui.QTextOption()
        self.textEdit.document().setDefaultTextOption(option)
        self.textEdit.setTabStopDistance(
            QtGui.QFontMetricsF(self.textEdit.font()).horizontalAdvance(' ') * 4
        )

        self.textEdit.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgb(42, 42, 64); 
                color: rgb(211, 194, 78); 
                selection-background-color: rgb(211, 197, 78); 
                selection-color: rgb(63, 63, 97);
                border: 1px solid rgb(63, 63, 97);
            }
            QMenu {
                background-color: rgb(42, 42, 64);
                border: 1px solid rgb(63, 63, 97);
            }
            QMenu::item { color: rgb(211, 194, 78); } 
            QMenu::item:selected { background-color: rgb(48, 48, 75); } 
            QScrollBar:vertical {
                border: none; background: rgb(42, 42, 64); 
                width: 10px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgb(193, 202, 227); min-height: 20px; border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover { background: rgb(211, 194, 78); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)

        self.textEdit.textChanged.connect(self.save_edited_text)

        self.text_errors = codeedit.CodeEditor(self)
        self.text_errors.setReadOnly(True)
        self.text_errors.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self.text_errors.setCenterOnScroll(True)
        self.text_errors.ensureCursorVisible()
        self.text_errors.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)

        self.text_errors.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgb(42, 42, 64); 
                color: rgb(211, 194, 78); 
                selection-background-color: rgb(211, 197, 78); 
                selection-color: rgb(63, 63, 97);
                border: 1px solid rgb(63, 63, 97);
            }
            QMenu {
                background-color: rgb(42, 42, 64);
                border: 1px solid rgb(63, 63, 97);
            }
            QMenu::item { color: rgb(211, 194, 78); } 
            QMenu::item:selected { background-color: rgb(48, 48, 75); } 

            QScrollBar:vertical {
                border: none; background: rgb(43, 43, 77); 
                width: 10px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgb(193, 202, 227); min-height: 20px; border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover { background: rgb(211, 194, 78); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)

        self.gridLayout_tab.setColumnStretch(1, 1)
        self.gridLayout_tab.setRowStretch(0, 10)
        self.gridLayout_tab.setRowStretch(1, 3)


        self.dockarea2 = DockArea()
        self.dock_editor = self.dockarea2.addDock(name="Script Editor")
        self.textEdit.textChanged.connect(self.save_edited_text)
        self.dock_editor.addWidget(widget=self.textEdit)
        self.gridLayout_tab.addWidget(self.dockarea2, 0, 1, 1, 1)

        self.dockarea3 = DockArea()
        self.dock_errors = self.dockarea3.addDock(name="Output")
        self.dockarea3.setMinimumHeight(100)
        self.dock_errors.addWidget(widget=self.text_errors)
        self.gridLayout_tab.addWidget(self.dockarea3, 1, 0, 1, 2)

        self.dockarea4 = DockArea()
        self.dockarea4.setMaximumHeight(60)    
        self.dockarea4.setMaximumHeight(80)
        self.script_queue = queue.QueueList(self)
        self.dock_queue = self.dockarea4.addDock(name="Queue")
        self.dock_queue.addWidget(widget=self.script_queue)
        self.gridLayout_tab.addWidget(self.dockarea4, 2, 0, 1, 2)


        self.label_filename = QLabel("No experimental script is opened")
        self.label_filename.setStyleSheet("color: rgb(193, 202, 227); font-weight: bold; padding: 2px;")
        self.gridLayout_tab.addWidget(self.label_filename, 4, 0, 1, 2)

        self.gridLayout_tab.setRowStretch(0, 10)
        self.gridLayout_tab.setRowStretch(4, 0)

        self.tabwidget.tabBar().setTabTextColor(0, QColor(193, 202, 227))
        self.tabwidget.tabBar().setTabTextColor(1, QColor(193, 202, 227))

        actions = [
            ('Clear', self.clear_errors),
            ('Open Config Directory', self.conf_dir_action),
            ('List Resources', self.list_resources_action)
        ]

        for name, method in actions:
            action = QAction(name, self.text_errors)
            action.triggered.connect(method)
            self.text_errors.addAction(action)


        # Liveplot tab setting
        tab3 = QWidget()
        self.gridLayout_tab_liveplot = QGridLayout(tab3)
        self.gridLayout_tab_liveplot.setContentsMargins(5, 5, 5, 5)
        self.tabwidget.addTab(tab3, "Liveplot")
        self.tabwidget.tabBar().setTabTextColor(1, QColor(193, 202, 227))

        # Liveplot tab setting
        self.dockarea = DockArea()
        self.namelist = NameList(self)

        self.gridLayout_tab_liveplot.setColumnMinimumWidth(0, 200)
        self.gridLayout_tab_liveplot.setColumnStretch(1, 2000)
        self.gridLayout_tab_liveplot.addWidget(self.namelist, 0, 0)
        self.gridLayout_tab_liveplot.setAlignment(self.namelist, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.gridLayout_tab_liveplot.addWidget(self.dockarea, 0, 1)
        #self.gridLayout_tab_liveplot.setAlignment(self.dockarea, QtConst.AlignRight)
        self.namelist.setStyleSheet(
            "QListView {background-color: rgb(42, 42, 64); selection-color: rgb(211, 194, 78); color: rgb(211, 194, 78); selection-background-color: rgb(63, 63, 97); border: 1px solid rgb(40, 30, 45);} "
            "QListView::item:hover {background-color: rgb(211, 194, 78); color: rgb(42, 42, 64);} "
            "QMenu {background-color: rgb(42, 42, 64); border: 1px solid rgb(63, 63, 97);} "
            "QMenu::item {color: rgb(211, 194, 78);} "
            "QMenu::item:selected {background-color: rgb(48, 48, 75);}"
        )

    def stop_script(self):
        sock = socket.socket()
        sock.connect(('localhost', 9091))
        sock.send(b'Script stopped')
        sock.close()

    def add_to_queue(self):
        key_number = str( len(self.script_queue.keys()) )
        self.test(self.script)
        exec_code = self.success
        if self.test_flag == 0 and exec_code == True:
            self.script_queue[key_number] = self.script
        else:
            pass

    def _on_destroyed(self):
        """
        A function to do some actions when the main window is closing.
        """
        self.process_python.close()
    
    def clear_errors(self):
        self.text_errors.clear()

    def conf_dir_action(self):
        self.open_directory(self.path_config2)

    def list_resources_action(self):
        import pyvisa

        rm = pyvisa.ResourceManager()
        print(f"AVAILABLE INSTRUMENTS: {rm.list_resources()}")

    def quit(self):
        """
        A function to quit the programm
        """
        self.process_python.terminate()
        sys.exit()

    def start_experiment(self):
        """
        A function to run an experimental script using python.exe.
        """
        if len(self.script_queue.keys()) != 0:
            self.queue = 1
            first_index = self.script_queue.namelist_model.index(0, 0 )
            self.script_queue.namelist_view.setCurrentIndex(first_index)

        else:
            self.queue = 0

        if self.queue == 0:
            name = self.script
        else:
            name = self.script_queue.values()[0]

        if self.script != '':
            stamp = os.stat(name).st_mtime
        else:
            self.text_errors.appendPlainText('No experimental script is opened')
            return

        self.test(name)
        exec_code = self.success

        if self.test_flag == 1:
            self.text_errors.appendPlainText("Experiment cannot be started, since test is not passed. Test execution timeout is " + str( self.test_timeout / 60000 ) + " minutes")
            return

        elif self.test_flag == 0 and exec_code == True:
            self.process_python.setArguments([name])
            self.button_start.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(211, 194, 78); border-style: outset; color: rgb(63, 63, 97); font-weight: bold; } ")
            self.process_python.start()
            self.pid = self.process_python.processId()
            print(f'SCRIPT PROCESS ID: {self.pid}')

    def message_box_clicked(self, btn):
        """
        Message Box fow warning
        """
        if btn.text() == "Discrad and Run Experiment":
            self.start_experiment()
        elif btn.text() == "Update Script":
            self.reload()
            #self.start_experiment()
        else:
            return

    def test(self, name):
        """
        A function to run script check.
        """
        self.button_test.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(193, 202, 227); border-style: outset; color: rgb(63, 63, 97); font-weight: bold; } ")

        QApplication.processEvents()

        self.success = False
        process = QtCore.QProcess()

        if self.system == 'Windows':
            process.setProgram('python.exe')
        elif self.system == 'Linux':
            process.setProgram('python3')

        if name != '':
            stamp = os.stat(name).st_mtime
        else:
            self.text_errors.appendPlainText('No experimental script is opened')
            return

        if stamp != self.cached_stamp and self.flag_opened_script_changed == 1 and self.queue == 0:
            self.cached_stamp = stamp
            message = QMessageBox(self);  # Message Box for warning of updated file
            message.setWindowTitle("Your script has been changed!")
            message.setStyleSheet("QWidget { background-color : rgb(42, 42, 64); color: rgb(211, 194, 78); }")
            message.addButton(QPushButton('Discrad and Run Experiment'), QMessageBox.ButtonRole.YesRole)
            message.addButton(QPushButton('Update Script'), QMessageBox.ButtonRole.NoRole)
            message.setText("Your experimental script has been changed   ");
            message.show();
            message.buttonClicked.connect(self.message_box_clicked)
            return

        loop = QEventLoop()
        process.finished.connect(lambda exit_code, exit_status: self.on_finished_checking(exit_code, exit_status, loop, process))

        #self.text_errors.appendPlainText("Testing... Please, wait!")
        #self.process.setArguments(['--errors-only', self.script])
        process.setArguments([name, 'test'])
        process.start()

        loop.exec()

    def reload(self):
        """
        A function to reload an experimental script.
        """
        try:
            self.cached_stamp = os.stat(self.script).st_mtime
            text = open(self.script).read()
            self.textEdit.setPlainText(text)
        except FileNotFoundError:
            pass

    def on_finished_checking(self, exit_code, exit_status, loop, process):
        """
        A function to add the information about errors found during syntax checking
        to a dedicated text box in the main window of the programm.
        """
        text = process.readAllStandardOutput().data().decode()
        text_errors_script = process.readAllStandardError().data().decode()
        if text_errors_script == '':
            self.text_errors.appendPlainText("No errors are found")
            self.test_flag = 0
        elif text_errors_script != '':
            self.test_flag = 1
            self.text_errors.appendPlainText(text_errors_script)

        self.button_test.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(63, 63, 97); border-style: outset; color: rgb(193, 202, 227); font-weight: bold; } ")

        self.success = (exit_status == QtCore.QProcess.ExitStatus.NormalExit and exit_code == 0)
        loop.quit()
 
    def on_finished_script(self):
        """
        A function to add the information about errors found during syntax checking to a dedicated text box in the main window of the programm.
        """
        if self.queue == 1:
            key_to_del = self.script_queue.values()[0]
            del self.script_queue[key_to_del]
        #except IndexError:
        #    pass

        text = self.process_python.readAllStandardOutput().data().decode()
        text_errors_script = self.process_python.readAllStandardError().data().decode()
        if text_errors_script == '':
            self.text_errors.appendPlainText(f"The script PID {self.pid} was executed normally")
        elif text_errors_script != '':
            self.text_errors.appendPlainText(f"The script PID {self.pid} was executed with errors")
            self.text_errors.appendPlainText(text_errors_script)

        self.button_start.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(63, 63, 97); border-style: outset; color: rgb(193, 202, 227); font-weight: bold; } ")

        if len(self.script_queue.keys()) != 0:
            self.start_experiment()
            self.queue = 1
        else:
            self.queue = 0

    def help(self):
        """
        A function to open a documentation
        """
        webbrowser.open("https://anatoly1010.github.io/atomize_docs/functions/", new = 0, autoraise = True)

    def edit_file(self):
        """
        A function to open an experimental script in a text editor.
        """
        if self.system == 'Linux':
            if self.editor =='nano':
                self.process_text_editor.setArguments(['-e','nano', self.script])
            elif self.editor == 'vi':
                self.process_text_editor.setArguments(['-e','vi', self.script])
            else:
                self.process_text_editor.setArguments([self.script])
        elif self.system == 'Windows':
            self.process_text_editor.setArguments([self.script])
        self.process_text_editor.start()
        
    def open_file(self, filename):
        """
        A function to open an experimental script.
        :param filename: string
        """
        self.cached_stamp = os.stat(filename).st_mtime
        text = open(filename).read()
        self.path = os.path.dirname(filename) # for memorizing the path to the last used folder
        self.script = filename
        self.textEdit.setPlainText(text)

        self.label_filename.setText( str( self.script ) )

    def save_file(self, filename):
        """
        A function to save a new experimental script.
        :param filename: string
        """
        with open(filename, 'w') as file:
            file.write(self.textEdit.toPlainText())

        self.cached_stamp = os.stat(filename).st_mtime
        self.script = filename

    def open_file_dialog(self):
        """
        A function to open a new window for choosing an experimental script.
        """
        filedialog = QFileDialog(self, 'Open File', directory = self.path, filter = "python (*.py)",options = QFileDialog.Option.DontUseNativeDialog)
        # use QFileDialog.Option.DontUseNativeDialog to change directory
        filedialog.setStyleSheet("QWidget { background-color : rgb(42, 42, 64); color: rgb(211, 194, 78);}")
        filedialog.setFileMode(QFileDialog.FileMode.AnyFile)
        filedialog.fileSelected.connect(self.open_file)
        filedialog.show()

    def save_file_dialog(self):
        """
        A function to open a new window for choosing a name for a new experimental script.
        """
        filedialog = QFileDialog(self, 'Save File', directory = self.path, filter = "python (*.py)",options = QFileDialog.Option.DontUseNativeDialog)
        filedialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        # use QFileDialog.Option.DontUseNativeDialog to change directory
        filedialog.setStyleSheet("QWidget { background-color : rgb(42, 42, 64); color: rgb(211, 194, 78);}")
        filedialog.setFileMode(QFileDialog.FileMode.AnyFile)
        filedialog.fileSelected.connect(self.save_file)
        filedialog.show()

    def save_edited_text(self):
        if self.script:
            self.flag_opened_script_changed = 1
            with open(self.script, 'w') as file:
                file.write(self.textEdit.toPlainText())
            
            self.cached_stamp = os.stat(self.script).st_mtime

        else:
            self.flag_opened_script_changed = 1
            if self.textEdit.toPlainText() != '': # save file dialog will be opened after at least one character is added
                self.save_file_dialog()
        
    @QtCore.pyqtSlot(str)
    def add_error_message(self, data):
        """
        A function for adding an error message to a dedicated text box in the main window of the programm;
        This function runs when Helper.changedSignal.emit(str) is emitted.
        :param data: string
        """
        self.text_errors.appendPlainText(str(data))

        if data == 'Script stopped':
            self.script_queue.clear()
            self.queue = 0
            self.process_python.close()

    def open_directory(self, path):
        if os.name == 'nt':
            os.startfile(path)
        elif os.name == 'posix': 
            subprocess.Popen(['open', path]) 
        else:
            print(f"Unsupported operating system: {os.name}")

class NameList(QDockWidget):
    def __init__(self, window):
        super(NameList, self).__init__('Current Plots:')
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setTitleBarWidget(QWidget(self))

        #directories
        path_to_main = os.path.abspath(os.getcwd())
        # configuration data
        path_config_file = os.path.join(path_to_main, '..', 'config.ini')
        path_config_file_device = os.path.join(path_to_main, '..', 'device_modules/config')
        path_config_file, path_config2 = lconf.copy_config(path_config_file, path_config_file_device)

        config = configparser.ConfigParser()
        config.read(path_config_file)
        # directories
        self.open_dir = str(config['DEFAULT']['open_dir'])
        if self.open_dir == '':
            self.open_dir = lconf.load_scripts(os.path.join(path_to_main, '..', 'tests'))
        
        self.namelist_model = QStandardItemModel()
        self.namelist_view = QListView()
        self.namelist_view.setStyleSheet("""
            QListView {
                background-color: rgb(42, 42, 64); 
                color: rgb(211, 194, 78); 
                selection-color: rgb(211, 194, 78); 
                selection-background-color: rgb(63, 63, 97); 
                border: 1px solid rgb(63, 63, 97); 
                outline: none;
                font-size: 12px;
                font-weight: bold;

            }

            QListView::item {
                padding: 5px; 
                border-bottom: 1px solid rgb(53, 53, 84); 
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
        self.setWidget(self.namelist_view)
        self.window = window
        self.plot_dict = {}

        self.namelist_view.doubleClicked.connect(self.activate_item)
        self.namelist_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        delete_action = QAction("Delete Selected", self.namelist_view)
        ###
        pause_action = QAction("Stop Experiment", self.namelist_view)
        delete_action.triggered.connect(self.delete_item)
        pause_action.triggered.connect(self.pause)
        self.namelist_view.addAction(delete_action)
        self.namelist_view.addAction(pause_action)

        open_action = QAction('Open 1D Data', self)
        open_action.triggered.connect(self.file_dialog) #self.open_file_dialog_1
        self.namelist_view.addAction(open_action)

        open_action_2 = QAction('Open 2D Data', self)
        open_action_2.triggered.connect(self.file_dialog_2d) #self.open_file_dialog_2
        self.namelist_view.addAction(open_action_2)

    def open_file(self, filename):
        """
        A function to open existing 1d data.
        :param filename: string
        """
        file_path = filename

        header_array = []
        header = 0

        # detecting the file header for further skipping
        file_to_read = open(filename, 'r')
        for i, line in enumerate(file_to_read):
            if i is header: break
            temp = line.split("#")
            header_array.append(temp)
        file_to_read.close()

        # read data
        temp = np.genfromtxt(file_path, dtype = float, delimiter = ',', skip_header = 1, comments = '#') 
        data = np.transpose(temp)

        # universal name
        name_plot = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        pw = self.window.add_new_plot(1, name_plot)
        # opening of a simple CSV file with a maximum of 4 columns. 
        # this is usually related to internal pyqtgraph export.
        # in this case, there is an extra comma that creates an empty column, which should be taken into account
        # the data may have a different number of columns.
        if len(data) == 2:
            pw.plot(data[0], data[1], parametric = True, name = file_path, xname = 'X', 
                xscale = 'Arb. U.',yname = 'Y', yscale = 'Arb. U.', 
                label = 'Data_1', scatter = 'False')
        elif len(data) == 3 and np.isnan(data[2][0]) != True:
            pw.plot(data[0], data[1], parametric = True, name = file_path + '_1', xname = 'X',
                xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', 
                label = 'Data_1', scatter = 'False')
            pw.plot(data[0], data[2], parametric = True, name = file_path + '_2', xname = 'X', 
                xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', 
                label = 'Data_2', scatter = 'False')
        elif len(data) == 3 and np.isnan(data[2][0]) == True:
            pw.plot(data[0], data[1], parametric = True, name = file_path, xname = 'X', 
                xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', 
                label = 'Data_1', scatter = 'False')
        elif len(data) == 4 and np.isnan(data[3][0]) == True:
            pw.plot(data[0], data[1], parametric = True, name = file_path + '_1', xname = 'X', 
                xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', 
                label = 'Data_1', scatter = 'False')
            pw.plot(data[0], data[2], parametric = True, name = file_path + '_2', xname = 'X', 
                xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', 
                label = 'Data_2', scatter = 'False')
        elif len(data) == 5 and np.isnan(data[4][0]) == True:
            pw.plot(data[0], data[1], parametric = True, name = file_path + '_1', xname = 'X', 
                xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', 
                label = 'Data_1', scatter = 'False')
            pw.plot(data[0], data[3], parametric = True, name = file_path + '_2', xname = 'X', 
                xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', 
                label = 'Data_2', scatter = 'False')

    def open_file_2d(self, filename):
        """
        A function to open 2d data
        :param filename: string
        """
        file_path = filename

        header_array = []
        header = 0

        header_array = []
        file_to_read = open(file_path, 'r')
        for i, line in enumerate(file_to_read):
            if i is header: break
            temp = line.split("#")
            header_array.append(temp)
        file_to_read.close()

        temp = np.genfromtxt(file_path, dtype = float, delimiter = ',', skip_header = 0) 
        data = temp

        name_plot = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        pw = self.window.add_new_plot(2, name_plot)
        pw.setAxisLabels(xname = 'X', xscale = 'Arb. U.',yname = 'X', yscale = 'Arb. U.',\
            zname = 'X', zscale = 'Arb. U.')
        pw.setImage(data, axes = {'y': 0, 'x': 1})

    def file_dialog(self, directory = ''):
        """
        A function to open a new window for choosing 1d data
        """
        filedialog = QFileDialog(self, 'Open File', directory = self.open_dir, filter = "CSV (*.csv)", options = QFileDialog.Option.DontUseNativeDialog )
        # options = QFileDialog.Option.DontUseNativeDialog
        # use QFileDialog.Option.DontUseNativeDialog to change directory
        filedialog.setStyleSheet("QWidget { background-color : rgb(42, 42, 64); color: rgb(211, 194, 78);}")
        filedialog.setFileMode(QFileDialog.FileMode.AnyFile)
        filedialog.fileSelected.connect(self.open_file)
        filedialog.show()

        # Tkinter Open 1D data
        #root = tkinter.Tk()
        #s = ttk.Style().theme_use('alt')
        #root.withdraw()

        #file_path = filedialog.askopenfilename(**dict(
        #    initialdir = self.open_dir,
        #    filetypes = [("CSV", "*.csv"), ("TXT", "*.txt"),\
        #    ("DAT", "*.dat"), ("all", "*.*")],
        #    title = 'Select file to open')
        #    )
        #return file_path

    def file_dialog_2d(self, directory = ''):
        """
        A function to open a new window for choosing 2D data
        """
        filedialog = QFileDialog(self, 'Open File', directory = self.open_dir, filter = "CSV (*.csv)", options = QFileDialog.Option.DontUseNativeDialog )
        #options = QtWidgets.QFileDialog.Option.DontUseNativeDialog
        # use QFileDialog.Option.DontUseNativeDialog to change directory
        filedialog.setStyleSheet("QWidget { background-color : rgb(42, 42, 64); color: rgb(211, 194, 78);}")
        filedialog.setFileMode(QFileDialog.FileMode.AnyFile)
        filedialog.fileSelected.connect(self.open_file_2d)
        filedialog.show()

    def activate_item(self, index):
        item = self.namelist_model.itemFromIndex(index)
        plot = self.plot_dict[str(item.text())]
        if plot.closed:
            plot.closed = False
            self.window.add_plot(plot)

    def delete_item(self):
        index = self.namelist_view.currentIndex()
        item = self.namelist_model.itemFromIndex(index)
        del self[str(item.text())]

    def pause(self):
        sock = socket.socket()
        sock.connect(('localhost', 9091))
        sock.send(b'Script stopped')
        sock.close()

    def __getitem__(self, item):
        return self.plot_dict[item]

    def __setitem__(self, name, plot):
        model = QStandardItem(name)
        model.setEditable(False)
        self.namelist_model.appendRow(model)
        self.plot_dict[name] = plot

    def __contains__(self, value):
        return value in self.plot_dict

    def __delitem__(self, name):
        self.namelist_model.removeRow(self.namelist_model.findItems(name)[0].index().row())
        self.plot_dict[name].close()
        try:
            self.plot_dict[name].h_cross_dock.close()
            self.plot_dict[name].v_cross_dock.close()
        except AttributeError:
            pass        
        del self.plot_dict[name]

    def keys(self):
        return list(self.plot_dict.keys())


def main():
    """
    A function to run the main window of the programm.
    """
    # Windows taskbar
    try:
        myappid = 'atomize' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    main = MainWindow()
    helper = socket_server.Helper()
    server = socket_server.Socket_server()
    # to connect a function add_error_message when the signal from the helper will be emitted.
    helper.changedSignal.connect(main.add_error_message, QtCore.Qt.ConnectionType.QueuedConnection)
    threading.Thread(target = server.start_messenger_server, args = (helper, ), daemon = True).start()
    main.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
