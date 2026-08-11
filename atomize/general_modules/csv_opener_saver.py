#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import configparser
import numpy as np
from PyQt6.QtWidgets import QFileDialog, QDialog, QApplication, QSizeGrip, QLineEdit, QFileIconProvider, QPushButton, QTreeView, QHeaderView
from PyQt6 import QtCore
from PyQt6.QtCore import QTimer
import atomize.main.local_config as lconf

class Saver_Opener():
    def __init__(self):

        # Test run parameters
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        # for open directory specified in the config file
        #path_to_main = os.path.abspath(os.getcwd())

        path_to_main = os.path.abspath(os.path.join(os.path.dirname(__file__ ), '..'))
        #os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'templates'))
        # configuration data
        #path_config_file = os.path.join(path_to_main,'atomize/config.ini')
        path_config_file, path_config2 = lconf.load_config()
        self.path_to_main = path_config2

        config = configparser.ConfigParser()
        config.read(path_config_file)
        # directories
        self.open_dir = str(config['DEFAULT']['open_dir'])
        if self.open_dir == '':
            self.open_dir = lconf.load_scripts(os.path.join(path_to_main, '..', 'tests'))

        self.script_dir = str(config['DEFAULT']['script_dir'])
        if self.script_dir == '':
            self.script_dir = lconf.load_scripts(os.path.join(path_to_main, '..', 'tests'))
        
        if self.test_flag == 'test':
            self.test_header_array = np.array(['header1', 'header2'])
            self.test_data = np.arange(1000, 2)
            self.test_data_2d = np.meshgrid(self.test_data, self.test_data)
            self.test_file_path = os.path.join(self.path_to_main, 'test')
            self.test_file_param_path = os.path.join(self.path_to_main, 'test.param')
    
    def open_file_dialog(self, directory = '', fmt = '', multiprocessing = False,
                         name_filters = None, multiple = False):
        # multiple = True returns a list of selected paths (possibly empty);
        # the default single-file behaviour is unchanged (returns a path or None).
        if self.test_flag != 'test':
            if not multiprocessing:
                print("open_file_dialog", flush = True)
                file_path = sys.stdin.readline().strip()

                if multiple:
                    return [file_path] if file_path else []
                if file_path:
                    return file_path
                return None

            else:
                result = self.FileDialog(directory = directory, mode = 'Open',
                                         fmt = 'csv', name_filters = name_filters,
                                         multiple = multiple)

                if multiple:
                    return result or []
                if result:
                    return result
                return None

        elif self.test_flag == 'test':
            return [self.test_file_path] if multiple else self.test_file_path

    def create_file_dialog(self, directory = '', multiprocessing = False, fmt = 'csv'):
        if self.test_flag != 'test':
            if not multiprocessing:
                # the suffix tells the parent window which filter to open with
                print(f"create_file_dialog {fmt}", flush = True)
                file_path = sys.stdin.readline().strip()

                if file_path and file_path != "None":
                    open(file_path, "w").close()
                    return file_path
                return "None"

            else:
                file_path = self.FileDialog(directory = directory, mode = 'Save', fmt = fmt)

                if file_path: 
                    open(file_path, "w").close()
                    return file_path
                return "None"
        
        elif self.test_flag == 'test':
            return self.test_file_path
    
    def create_file_parameters(self, add_name, directory = '', multiprocessing = False):
        if self.test_flag != 'test':
            try:
                file_name = self.create_file_dialog(
                    directory = directory, 
                    multiprocessing = multiprocessing 
                    )
                base_name = file_name.rsplit('.', 1)[0]
                file_save_param = f"{base_name}{add_name}.csv"

            except (TypeError, FileNotFoundError):
                file_name = os.path.join(self.path_to_main, 'temp.csv')
                base_name = file_name.rsplit('.', 1)[0]
                file_save_param = f"{base_name}{add_name}.csv"
            
            return file_name, file_save_param

        elif self.test_flag == 'test':
            return self.test_file_path, self.test_file_param_path

    def save_header(self, filename, header = '', mode = 'w'):
        if self.test_flag != 'test':
            if (filename != 'None') and (filename != ''):
                if self._is_h5(filename):
                    h5py = self._h5py()
                    # 'a' keeps whatever data the file already holds
                    with h5py.File(filename, 'a' if mode == 'a' else 'w') as file_for_save:
                        self._write_h5_attrs(file_for_save, header)
                    return

                with open(filename, mode) as file_for_save:
                    np.savetxt(
                        file_for_save, 
                        [], 
                        fmt='%.6e', 
                        delimiter=',', 
                        newline='\n', 
                        header=header, 
                        footer='', 
                        comments='# ', 
                        encoding=None
                    )

        elif self.test_flag == 'test':
            with open(filename, mode) as f:
                pass
            os.remove( filename )

    def save_data(self, filename, data, header = '', mode = 'w', axes = None,
                  fmt = '%.6e', dtype = None):
        if self.test_flag != 'test':
            if (filename != 'None') and (filename != ''):
                if self._is_h5(filename):
                    if mode == 'a':
                        raise ValueError("append mode is not supported for '.h5' files")

                    self._save_h5(filename, data, header = header, axes = axes,
                                  dtype = dtype if dtype is not None else self._dtype_from_fmt(fmt))
                    return

                if len( data.shape ) == 2:
                    with open(filename, mode) as file_for_save:
                        np.savetxt(
                            file_for_save,
                            data,
                            fmt=fmt,
                            delimiter=',',
                            newline='\n',
                            header=header,
                            footer='',
                            comments='# ',
                            encoding=None
                        )

                elif data.ndim == 3:
                    base_name = filename.rsplit('.', 1)[0]
                    ext = ".csv"

                    for i in range(data.shape[0]):
                        current_filename = filename if i == 0 else f"{base_name}_{i}{ext}"

                        with open(current_filename, mode) as f:
                            np.savetxt(
                                f,
                                np.transpose(data[i]),
                                fmt=fmt,
                                delimiter=',',
                                header=header,
                                comments='# '
                            )

        elif self.test_flag == 'test':
            with open(filename, mode) as f:
                pass
            os.remove( filename )

    def _is_h5(self, file_path):
        return str(file_path).lower().endswith('.h5')

    def _h5py(self):
        try:
            import h5py
        except ImportError:
            raise ImportError("h5py is not installed; it is required to read or write '.h5' files")

        return h5py

    def _dtype_from_fmt(self, fmt):
        # '%.6e' is 7 significant digits, the float32 band; anything wider needs float64
        try:
            digits = int(str(fmt).split('.')[1][:-1])
        except (IndexError, ValueError):
            return 'float32'

        return 'float32' if digits <= 6 else 'float64'

    def _write_h5_attrs(self, file_for_save, header):
        file_for_save.attrs['header'] = header
        file_for_save.attrs['format_version'] = 1
        file_for_save.attrs['source'] = 'atomize'

    def _save_h5(self, filename, data, header = '', axes = None, dtype = 'float32'):
        h5py = self._h5py()
        data = np.asarray(data)

        with h5py.File(filename, 'w') as file_for_save:
            self._write_h5_attrs(file_for_save, header)

            # the array is stored exactly as np.savetxt would lay it out
            if data.ndim == 3:
                for i in range(data.shape[0]):
                    name = ('I', 'Q')[i] if i < 2 else f'D{i}'
                    file_for_save.create_dataset(name, data = np.transpose(data[i]).astype(dtype))
            else:
                file_for_save.create_dataset('I', data = data.astype(dtype))

            if axes is not None:
                for name, axis in zip(('t', 'sweep'), axes):
                    if axis is not None:
                        file_for_save.create_dataset(name, data = np.asarray(axis, dtype = 'float64'))

    def _open_h5(self, file_path, header = 0, scans = False):
        h5py = self._h5py()

        with h5py.File(file_path, 'r') as file_to_read:
            # the same list of ':'-split '# ' lines the csv readers return
            header_array = [ ('# ' + line + '\n').split(':') \
                             for line in str(file_to_read.attrs.get('header', '')).splitlines() ]
            if header > 0:
                header_array = header_array[:header]

            if scans and 'scans' in file_to_read:
                data = [ np.asarray(scan) for scan in file_to_read['scans'] ]
            else:
                # every plane the writer laid down, in the order it wrote them
                names = [ name for name in ['I', 'Q'] + [f'D{i}' for i in range(2, 32)] \
                          if name in file_to_read ]
                if not names:
                    # a header-only file, as save_header leaves it
                    data = np.array([])
                elif len(names) == 1:
                    data = np.asarray(file_to_read[names[0]])
                else:
                    data = np.stack( [ np.asarray(file_to_read[name]) for name in names ] )

        return header_array, data

    def open_h5_axes(self, file_path):
        h5py = self._h5py()

        with h5py.File(file_path, 'r') as file_to_read:
            axes = { name: np.asarray(file_to_read[name]) for name in ('t', 'sweep') \
                     if name in file_to_read }

        return axes

    def open_1d(self, file_path, header = 0):
        if self.test_flag != 'test':

            if self._is_h5(file_path):
                header_array, temp = self._open_h5(file_path, header = header)
                return header_array, np.transpose(temp)

            header_array = []
            file_to_read = open(file_path, 'r', errors = 'ignore')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',', encoding = 'latin1')
            data = np.transpose(temp)
            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data

    def open_2d(self, file_path, header = 0):
        if self.test_flag != 'test':

            if self._is_h5(file_path):
                return self._open_h5(file_path, header = header)

            header_array = []
            file_to_read = open(file_path, 'r', errors = 'ignore')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp=line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',', encoding = 'latin1')
            data = temp
            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data_2d

    def open_2d_appended(self, file_path, header = 0, chunk_size = 1):
        if self.test_flag != 'test':

            if self._is_h5(file_path):
                header_array, temp = self._open_h5(file_path, header = header, scans = True)
                return header_array, temp if isinstance(temp, list) else np.array_split(temp, chunk_size)

            header_array = []
            file_to_read = open(file_path, 'r', errors = 'ignore')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp=line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',', encoding = 'latin1')
            data = np.array_split(temp, chunk_size)
            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data_2d

    def FileDialog(self, directory = '', mode = 'Open', fmt = '', name_filters = None,
                   multiple = False):

        self.dialog = QFileDialog( options = QFileDialog.Option.DontUseNativeDialog )
        self.dialog.setIconProvider(QFileIconProvider())

        self.dialog.resize(1100, 450)
        self.dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        # multi-select open: a list of existing files instead of a single one
        if multiple and mode == 'Open':
            self.dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        # both open and save dialog
        self.dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)\
         if mode == 'Open' else self.dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

        tree = self.dialog.findChild(QTreeView)
        header = tree.header()
        for i in range(header.count()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        buttons = self.dialog.findChildren(QPushButton)
        seen_texts = []
        for btn in buttons:
            if btn.text() in seen_texts:
                btn.hide()
            else:
                seen_texts.append(btn.text())
        
        line_edit = self.dialog.findChild(QLineEdit)

        if line_edit:
            line_edit.setCompleter(None)

        size_grip = self.dialog.findChild(QSizeGrip)
        if size_grip:
            size_grip.setVisible(False)

        self.dialog.setStyleSheet("""
            QFileDialog, QDialog { 
                background-color: rgb(42, 42, 64); 
                color: rgb(193, 202, 227);
                font-size: 11px;
            }

            QFileDialog QListView {
                min-width: 150px; 
                background-color: rgb(35, 35, 55);
                border: 1px solid rgb(63, 63, 97);
                color: rgb(193, 202, 227);
            }

            QTreeView {
                min-width: 500px;
                background-color: rgb(35, 35, 55);
                border: 1px solid rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                outline: none;
            }

            QFileDialog QFrame#qt_contents, QFileDialog QWidget {
                background-color: rgb(42, 42, 64);
            }
            
            QFileDialog QToolBar {
                background-color: rgb(42, 42, 64);
                border-bottom: 1px solid rgb(63, 63, 97);
                min-height: 34px; 
                padding: 2px;
            }

            QToolButton {
                background-color: rgb(63, 63, 97);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 4px;
                min-height: 23px; 
                max-height: 23px;
                min-width: 23px;
                qproperty-iconSize: 14px 14px; 
                margin: 0px 2px;
                vertical-align: middle;
            }

            QToolButton:hover {
                border: 1px solid rgb(211, 194, 78);
                background-color: rgb(83, 83, 117);
            }

            QLineEdit, QComboBox {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 3px;
                padding: 2px 5px;
                min-height: 16px; 
            }

            QLineEdit:focus, QFileDialog QComboBox:focus {
                border: 1px solid rgb(211, 194, 78);
                color: rgb(211, 194, 78);
                outline: none;
            }

            QFileDialog QComboBox#lookInCombo {
                background-color: rgb(42, 42, 64);
                color: rgb(193, 202, 227);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 3px;
                padding-left: 5px;
                min-height: 19px;
                max-height: 19px;
                selection-background-color: rgb(48, 48, 75);
                selection-color: rgb(211, 194, 78);
            }

            QFileDialog QComboBox#lookInCombo QAbstractItemView {
                outline: none;
                border: 1px solid rgb(48, 48, 75);
                background-color: rgb(42, 42, 64);
            }

            QFileDialog QDialogButtonBox QPushButton {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 4px;
                font-weight: bold;
                min-height: 23px;
                max-height: 23px;
                min-width: 75px;
                padding: 0px 12px;
            }

            QFileDialog QDialogButtonBox QPushButton:hover {
                background-color: rgb(83, 83, 117);
                border: 1px solid rgb(211, 194, 78);
                color: rgb(211, 194, 78);
            }
            
            QHeaderView::section {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                padding: 4px;
                border: none;
                border-right: 1px solid rgb(83, 83, 117);
                min-height: 20px;
            }

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

            QScrollBar:horizontal {
                border: none; 
                background: rgb(43, 43, 77); 
                height: 10px; 
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgb(193, 202, 227); 
                min-width: 20px; 
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover { 
                background: rgb(211, 194, 78); 
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { 
                width: 0px; 
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { 
                background: none; 
            }

            QFileDialog QDialogButtonBox {
                background-color: rgb(42, 42, 64);
                border-top: 1px solid rgb(63, 63, 97);
                padding: 6px;
            }

            QFileDialog QLabel {
                color: rgb(193, 202, 227);
            }

            QFileDialog QListView::item:hover {
                background-color: rgb(48, 48, 75);
                color: rgb(211, 194, 78);
            }

            QHeaderView {
                background-color: rgb(63, 63, 97);
            }

            QFileDialog QListView#sidebar:inactive, 
            QTreeView:inactive {
                selection-background-color: rgb(35, 35, 55);
                selection-color: rgb(211, 194, 78);
            }

            QTreeView::item:hover { 
                background-color: rgb(48, 48, 75);
                color: rgb(211, 194, 78); 
                } 
            QTreeView::item:selected:inactive, 
            QFileDialog QListView#sidebar::item:selected:inactive {
                selection-background-color: rgb(63, 63, 97);
                selection-color: rgb(211, 194, 78);
            }
            QFileDialog QListView#sidebar::item {
                padding-left: 5px; 
                padding-top: 5px;
            }

            QMenu {
                background-color: rgb(42, 42, 64);
                border: 1px solid rgb(63, 63, 97);
                padding: 3px;
            }
            QMenu::item { color: rgb(211, 194, 78); } 
            QMenu::item:selected { 
                background-color: rgb(48, 48, 75); 
                color: rgb(211, 194, 78);
                }

        """)

        # set format: an explicit filter list wins, else the single-suffix filter
        if name_filters:
            self.dialog.setNameFilters(list(name_filters))
        elif fmt != '':
            self.dialog.setDefaultSuffix(fmt)
            self.dialog.setNameFilters([f'{fmt} (*.{fmt})'])

        # set starting directory
        if directory != '':
            self.dialog.setDirectory(str(directory))
        else:
            self.dialog.setDirectory(str(self.open_dir))

        if self.dialog.exec() == QDialog.DialogCode.Accepted:
            files = self.dialog.selectedFiles()
            if multiple:
                return files
            return files[0]
        else:
            return [] if multiple else ''

if __name__ == '__main__':
    main()