#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import configparser
import time
import numpy as np
from PyQt5.QtWidgets import QFileDialog, QDialog
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer

# Test run parameters
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_header_array = np.array(['header1', 'header2'])
test_data = np.arange(1000, 2)
test_data_2d = np.meshgrid(test_data, test_data)
test_file_path = os.path.abspath(os.getcwd())

class Saver_Opener():
    def __init__(self):
        # for open directory specified in the config file
        path_to_main = os.path.abspath(os.getcwd())
        #os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'templates'))
        # configuration data
        path_config_file = os.path.join(path_to_main,'atomize/config.ini')
        config = configparser.ConfigParser()
        config.read(path_config_file)
        # directories
        self.open_dir = str(config['DEFAULT']['open_dir'])
        self.script_dir = str(config['DEFAULT']['script_dir'])

    def open_1D(self, path, header = 0):
        if test_flag != 'test':
            header_array = []

            file_to_read = open(str(path), 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp=line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(str(path), dtype = float, delimiter = ',') 
            data = np.transpose(temp)

            return header_array, data

        elif test_flag == 'test':
            return test_header_array, test_data

    def open_1D_dialog(self, directory = '', fmt = '', header = 0):
        if test_flag != 'test':
            self.app = QtWidgets.QApplication([])
            file_path = self.FileDialog(directory = directory, mode = 'Open', fmt = 'csv')
            QTimer.singleShot(100, self.app.quit)
            self.app.exec_()

            header_array = []
            file_to_read = open(file_path, 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp=line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',') 
            data = np.transpose(temp)
            return header_array, data

        elif test_flag == 'test':
            return test_header_array, test_data

    def save_1D_dialog(self, data, directory = '', fmt = '', header = ''):
        if test_flag != 'test':
            self.app = QtWidgets.QApplication(sys.argv)
            file_path = self.FileDialog(directory = directory, mode = 'Save', fmt = 'csv')
            QTimer.singleShot(50, self.app.quit)
            self.app.exec_()

            np.savetxt(file_path, np.transpose(data), fmt = '%.4e', delimiter = ',', newline = '\n', header = header, footer = '', comments = '#', encoding = None)
        
        elif test_flag == 'test':
            pass

    def open_2D(self, path, header = 0):
        if test_flag != 'test':
            header_array = []
            file_to_read = open(str(path), 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp=line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(str(path), dtype = float, delimiter = ',') 
            data = temp

            return header_array, data

        elif test_flag == 'test':
            return header_array, test_data_2d

    def open_2D_dialog(self, directory = '', fmt = '', header = 0):
        if test_flag != 'test':
            self.app = QtWidgets.QApplication(sys.argv)
            file_path = self.FileDialog(directory = directory, mode = 'Open', fmt = 'csv')
            QTimer.singleShot(50, self.app.quit)
            self.app.exec_()

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

        elif test_flag == 'test':
            return test_header_array, test_data_2d

    def open_2D_appended(self, path, header = 0, chunk_size = 1):
        if test_flag != 'test':
            header_array = []
            file_to_read = open(str(path), 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp=line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(str(path), dtype = float, delimiter = ',') 
            data = np.array_split(temp, chunk_size)
            return header_array, data

        elif test_flag == 'test':
            return test_header_array, test_data_2d

    def open_2D_appended_dialog(self, directory = '', header = 0, chunk_size = 1):
        if test_flag != 'test':
            self.app = QtWidgets.QApplication(sys.argv)
            file_path = self.FileDialog(directory = directory, mode = 'Open', fmt = 'csv')

            QTimer.singleShot(50, self.app.quit)
            self.app.exec_()

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

        elif test_flag == 'test':
            return test_header_array, test_data_2d

    def save_2D_dialog(self, data, directory = '', header = ''):
        if test_flag != 'test':
            self.app = QtWidgets.QApplication(sys.argv)
            file_path = self.FileDialog(directory = directory, mode = 'Save', fmt = 'csv')
            QTimer.singleShot(50, self.app.quit)
            self.app.exec_()

            np.savetxt(file_path, data, fmt = '%.4e', delimiter = ',', newline = '\n', header = header, footer = '', comments = '#', encoding = None)
        
        elif test_flag == 'test':
            pass

    def create_file_dialog(self,  directory = ''):
        if test_flag != 'test':
            self.app = QtWidgets.QApplication(sys.argv)
            file_path = self.FileDialog(directory = directory, mode = 'Save', fmt = 'csv')
            open(file_path, "w").close()
            QTimer.singleShot(50, self.app.quit)
            self.app.exec_() # run mainloop which runs all time and makes all job in GUI.
                             # mainloop will close the dialog, but we will have problems closing loop
                             # we use QTimer with app.quit to inform mainloop to execute 
                             # it after it will be started.
            return file_path

        elif test_flag == 'test':
            return test_file_path

    def FileDialog(self, directory = '', mode = 'Open', fmt = ''):

        self.dialog = QFileDialog( options = QtWidgets.QFileDialog.DontUseNativeDialog ) # options = QtWidgets.QFileDialog.DontUseNativeDialog
        self.dialog.setStyleSheet("QWidget { background-color : rgb(42, 42, 64); color: rgb(211, 194, 78);}")
        self.dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        # both open and save dialog
        self.dialog.setAcceptMode(QFileDialog.AcceptOpen)\
         if mode == 'Open' else self.dialog.setAcceptMode(QFileDialog.AcceptSave)

        # set format
        if fmt != '':
            self.dialog.setDefaultSuffix(fmt)
            self.dialog.setNameFilters([f'{fmt} (*.{fmt})'])

        # set starting directory
        if directory != '':
            self.dialog.setDirectory(str(directory))
        else:
            self.dialog.setDirectory(str(self.open_dir))

        if self.dialog.exec_() == QDialog.Accepted:
            path = self.dialog.selectedFiles()[0]  # returns a list
            return path
        else:
            return ''

if __name__ == '__main__':
    main()