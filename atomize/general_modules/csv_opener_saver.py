#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import configparser
import numpy as np
from PyQt6.QtWidgets import QFileDialog, QDialog, QApplication, QSizeGrip, QLineEdit, QFileIconProvider, QPushButton
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
    
    def open_file_dialog(self, directory = '', fmt = '', multiprocessing = False):
        if self.test_flag != 'test':
            if not multiprocessing:
                print("open_file_dialog", flush = True)
                file_path = sys.stdin.readline().strip()

                if file_path:
                    return file_path
                return None

            else:
                file_path = self.FileDialog(directory = directory, mode = 'Open', fmt = 'csv')
                
                if file_path:
                    return file_path
                return None
        
        elif self.test_flag == 'test':
            return self.test_file_path

    def create_file_dialog(self, directory = '', multiprocessing = False):
        if self.test_flag != 'test':
            if not multiprocessing:
                print("create_file_dialog", flush = True)
                file_path = sys.stdin.readline().strip()

                if file_path and file_path != "None":
                    open(file_path, "w").close()
                    return file_path
                return "None"

            else:
                file_path = self.FileDialog(directory = directory, mode = 'Save', fmt = 'csv')

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

    def save_data(self, filename, data, header = '', mode = 'w'):
        if self.test_flag != 'test':
            if (filename != 'None') and (filename != ''):
                if len( data.shape ) == 2:
                    with open(filename, mode) as file_for_save:
                        np.savetxt(
                            file_for_save, 
                            data, 
                            fmt='%.6e', 
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
                                fmt='%.6e', 
                                delimiter=',', 
                                header=header, 
                                comments='# '
                            )
        
        elif self.test_flag == 'test':
            with open(filename, mode) as f:
                pass
            os.remove( filename )

    def open_1d(self, file_path, header = 0):
        if self.test_flag != 'test':

            header_array = []
            file_to_read = open(file_path, 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',') 
            data = np.transpose(temp)
            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data

    def open_2d(self, file_path, header = 0):
        if self.test_flag != 'test':

            header_array = []
            file_to_read = open(file_path, 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp=line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',') 
            data = temp
            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data_2d

    def open_2d_appended(self, file_path, header = 0, chunk_size = 1):
        if self.test_flag != 'test':

            header_array = []
            file_to_read = open(file_path, 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp=line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',') 
            data = np.array_split(temp, chunk_size)
            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data_2d

    def FileDialog(self, directory = '', mode = 'Open', fmt = ''):

        self.dialog = QFileDialog( options = QFileDialog.Option.DontUseNativeDialog )
        self.dialog.setIconProvider(QFileIconProvider())
        
        self.dialog.resize(800, 450) 
        self.dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        # both open and save dialog
        self.dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)\
         if mode == 'Open' else self.dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

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

            QFileDialog QListView#sidebar {
                min-width: 150px; 
                max-width: 200px;
                background-color: rgb(35, 35, 55);
                border-right: 1px solid rgb(63, 63, 97);
                color: rgb(193, 202, 227);
            }

            QTreeView {
                min-width: 450px; 
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

            QFileDialog QComboBox#lookInCombo {
                min-height: 23px;
                max-height: 23px;
                margin: 0px;
                padding: 0px 4px;
                vertical-align: middle;
            }

            QLineEdit, QComboBox {
                background-color: rgb(63, 63, 97);
                color: rgb(211, 194, 78);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 3px;
                padding: 2px 5px;
                min-height: 16px; 
            }
            
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid rgb(211, 194, 78);
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

            QTreeView {
                background-color: rgb(35, 35, 55);
                border: 1px solid rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                outline: none;
            }
            
            QHeaderView::section {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                padding: 4px;
                border: none;
                border-right: 1px solid rgb(83, 83, 117);
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

            QFileDialog QAbstractItemView {
                color: rgb(193, 202, 227);
            }

            QFileDialog QListView {
                color: rgb(193, 202, 227);
            }

            QHeaderView {
                background-color: rgb(63, 63, 97);
            }

            QFileDialog QListView#sidebar:inactive, 
            QTreeView:inactive {
                selection-background-color: rgb(35, 35, 55);
                selection-color: rgb(211, 194, 78);
            }

            QTreeView::item:selected:inactive, 
            QFileDialog QListView#sidebar::item:selected:inactive {
                selection-background-color: rgb(63, 63, 97);
                selection-color: rgb(211, 194, 78);
            }
        """)
        # set format
        if fmt != '':
            self.dialog.setDefaultSuffix(fmt)
            self.dialog.setNameFilters([f'{fmt} (*.{fmt})'])

        # set starting directory
        if directory != '':
            self.dialog.setDirectory(str(directory))
        else:
            self.dialog.setDirectory(str(self.open_dir))

        if self.dialog.exec() == QDialog.DialogCode.Accepted:
            path = self.dialog.selectedFiles()[0]
            return path 
        else:
            return ''

if __name__ == '__main__':
    main()