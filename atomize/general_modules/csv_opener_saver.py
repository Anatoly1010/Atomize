#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import csv
import time
import numpy as np
from PyQt5.QtWidgets import QFileDialog, QDialog
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer

class csv():
	def __init__(self):
		pass

	def open_1D(self, path, header=0):
		header_array=[];

		file_to_read = open(str(path),'r')
		for i, line in enumerate(file_to_read):
		    if i is header: break
		    temp=line.split(":")
		    header_array.append(temp)
		file_to_read.close()

		temp = np.genfromtxt(str(path), dtype=float, delimiter=',') 
		data = np.transpose(temp)

		return header_array, data

	def open_1D_dialog(self, directory='', fmt='', header=0):

		self.app = QtWidgets.QApplication([])
		file_path = self.FileDialog(directory=directory, mode='Open', fmt=fmt)
		QTimer.singleShot(100, self.app.quit)
		self.app.exec_()

		header_array=[];
		file_to_read = open(file_path,'r')
		for i, line in enumerate(file_to_read):
			if i is header: break
			temp=line.split(":")
			header_array.append(temp)
		file_to_read.close()

		temp = np.genfromtxt(file_path, dtype=float, delimiter=',') 
		data = np.transpose(temp)
		return header_array, data

	def save_1D_dialog(self, data, directory='', fmt='', header=''):

		self.app2 = QtWidgets.QApplication(sys.argv)
		file_path = self.FileDialog(directory=directory,mode='Save', fmt=fmt)
		QTimer.singleShot(50, self.app2.quit)
		self.app2.exec_()

		np.savetxt(file_path, np.transpose(data), fmt='%.10f', delimiter=',', newline='\n', header=header, footer='', comments='#', encoding=None)

	def open_2D(self, path, header=0):

		header_array=[];
		file_to_read = open(str(path),'r')
		for i, line in enumerate(file_to_read):
		    if i is header: break
		    temp=line.split(":")
		    header_array.append(temp)
		file_to_read.close()

		temp = np.genfromtxt(str(path), dtype=float, delimiter=',') 
		data = temp

		return header_array, data

	def open_2D_dialog(self, directory='', fmt='', header=0):

		self.app = QtWidgets.QApplication(sys.argv)
		file_path = self.FileDialog(directory=directory, mode='Open', fmt=fmt)
		QTimer.singleShot(50, self.app.quit)
		self.app.exec_()

		header_array=[];
		file_to_read = open(file_path,'r')
		for i, line in enumerate(file_to_read):
		    if i is header: break
		    temp=line.split(":")
		    header_array.append(temp)
		file_to_read.close()

		temp = np.genfromtxt(file_path, dtype=float, delimiter=',') 
		data = temp
		return header_array, data

	def open_2D_appended(self, path, header=0, chunk_size=1):

		header_array=[];
		file_to_read = open(str(path),'r')
		for i, line in enumerate(file_to_read):
		    if i is header: break
		    temp=line.split(":")
		    header_array.append(temp)
		file_to_read.close()

		temp = np.genfromtxt(str(path), dtype=float, delimiter=',') 
		data = np.array_split(temp, chunk_size)
		return header_array, data

	def open_2D_appended_dialog(self, directory='', fmt='', header=0, chunk_size=1):

		self.app = QtWidgets.QApplication(sys.argv)
		file_path = self.FileDialog(directory=directory, mode='Open', fmt=fmt)

		QTimer.singleShot(50, self.app.quit)
		self.app.exec_()

		header_array=[];
		file_to_read = open(file_path,'r')
		for i, line in enumerate(file_to_read):
		    if i is header: break
		    temp=line.split(":")
		    header_array.append(temp)
		file_to_read.close()

		temp = np.genfromtxt(file_path, dtype=float, delimiter=',') 
		data = np.array_split(temp, chunk_size)
		return header_array, data

	def save_2D_dialog(self, data, directory='', fmt='', header=''):

		self.app2 = QtWidgets.QApplication(sys.argv)
		file_path = self.FileDialog(directory=directory,mode='Save', fmt=fmt)
		QTimer.singleShot(50, self.app2.quit)
		self.app2.exec_()

		np.savetxt(file_path, data, fmt='%.10f', delimiter=',', newline='\n', header=header, footer='', comments='#', encoding=None)

	def create_file_dialog(self,  directory='', fmt=''):

		self.app3 = QtWidgets.QApplication(sys.argv)
		file_path = self.FileDialog(directory=directory,mode='Save', fmt=fmt)
		open(file_path, "w").close()
		QTimer.singleShot(50, self.app3.quit)
		self.app3.exec_() # run mainloop which runs all time and makes all job in GUI.
						 # mainloop will close the dialog, but we will have problems closing loop
						 # we use QTimer with app.quit to inform mainloop to execute 
						 # it after it will be started.
		return file_path

	def FileDialog(self, directory='', mode='Open', fmt=''):
	    self.dialog = QFileDialog()
	    self.dialog.setStyleSheet("QWidget { background-color : rgb(136, 138, 133) }")
	    self.dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
	    # both open and save dialog
	    self.dialog.setAcceptMode(QFileDialog.AcceptOpen) if mode=='Open' else self.dialog.setAcceptMode(QFileDialog.AcceptSave)

	    # set format
	    if fmt != '':
	        self.dialog.setDefaultSuffix(fmt)
	        self.dialog.setNameFilters([f'{fmt} (*.{fmt})'])

	    # set starting directory
	    if directory != '':
	        self.dialog.setDirectory(str(directory))
	    else:
	        pass

	    if self.dialog.exec_() == QDialog.Accepted:
	        path = self.dialog.selectedFiles()[0]  # returns a list
	        return path
	    else:
	        return ''

if __name__ == '__main__':
    main()