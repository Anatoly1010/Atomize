#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np
from tkinter import filedialog
import tkinter

# Test run parameters
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

test_header_array = np.array(['header1', 'header2'])
test_data = np.arange(1000, 2)
test_data_2d = np.meshgrid(test_data, test_data)
test_file_path = os.path.abspath(os.getcwd())

class Saver_Opener:
    def __init__(self):
        pass

    def open_1D(self, path, header = 0):
        if test_flag != 'test':
            header_array = []

            file_to_read = open(str(path),'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(str(path), dtype = float, delimiter = ',') 
            data = np.transpose(temp)

            return header_array, data

        elif test_flag == 'test':
            return test_header_array, test_data

    def open_1D_dialog(self, directory = '', header = 0):
        if test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Open')

            header_array = [];
            file_to_read = open(file_path,'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype=float, delimiter=',') 
            data = np.transpose(temp)
            return header_array, data

        elif test_flag == 'test':
            return test_header_array, test_data

    def save_1D_dialog(self, data, directory = '',header = ''):
        if test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Save')

            np.savetxt(file_path, np.transpose(data), fmt='%.10f', delimiter=',',\
             newline='\n', header=header, footer='', comments='#', encoding=None)

        elif test_flag == 'test':
            pass

    def open_2D(self, path, header = 0):
        if test_flag != 'test':
            header_array = []
            file_to_read = open(str(path), 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(str(path), dtype = float, delimiter = ',') 
            data = temp

            return header_array, data

        elif test_flag == 'test':
            return header_array, test_data_2d

    def open_2D_dialog(self, directory = '', header = 0):
        if test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Open')

            header_array = [];
            file_to_read = open(file_path,'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
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
            file_to_read = open(str(path),'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(str(path), dtype = float, delimiter = ',') 
            data = np.array_split(temp, chunk_size)
            return header_array, data

        elif test_flag == 'test':
            return test_header_array, test_data_2d

    def open_2D_appended_dialog(self, directory = '', header = 0, chunk_size = 1):
        if test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Open')

            header_array = []
            file_to_read = open(file_path,'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',')
            data = np.array_split(temp, chunk_size)
            return header_array, data

        elif test_flag == 'test':
            return test_header_array, test_data_2d

    def save_2D_dialog(self, data, directory = '', header = ''):
        if test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Save')
            np.savetxt(file_path, data, fmt = '%.10f', delimiter = ',', newline = '\n', \
                header = header, footer = '', comments = '#', encoding = None)

        elif test_flag == 'test':
            pass

    def create_file_dialog(self,  directory = ''):
        if test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Save')
            open(file_path, "w").close()
            return file_path
        elif test_flag == 'test':
            return test_file_path

    def file_dialog(self, directory = '', mode = 'Open'):
        root = tkinter.Tk()
        root.withdraw()

        if mode == 'Open':
            file_path = filedialog.askopenfilename(**dict(
                initialdir = directory,
                filetypes = [("CSV", "*.csv"), ("TXT", "*.txt"),\
                ("DAT", "*.dat"), ("all", "*.*")],
                title = 'Select file to open')
                )
        elif mode == 'Save':
            file_path = filedialog.asksaveasfilename(**dict(
                initialdir = directory,
                filetypes = [("CSV", "*.csv"), ("TXT", "*.txt"),\
                ("DAT", "*.dat"), ("all", "*.*")],
                title = 'Select file to save')
                )
        return file_path

def main():
    pass

if __name__ == '__main__':
    main()