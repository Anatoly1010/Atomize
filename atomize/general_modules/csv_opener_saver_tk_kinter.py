#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import configparser
import numpy as np
from tkinter import filedialog
import tkinter

class Saver_Opener:
    def __init__(self):

        # Test run parameters
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        # for open directory specified in the config file
        #path_to_main = os.path.abspath(os.getcwd())
        self.path_to_main = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..'))
        #os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'templates'))
        # configuration data
        #path_config_file = os.path.join(path_to_main,'atomize/config.ini')
        path_config_file = os.path.join(self.path_to_main,'config.ini')
        config = configparser.ConfigParser()
        config.read(path_config_file)
        # directories
        self.open_dir = str(config['DEFAULT']['open_dir'])
        self.script_dir = str(config['DEFAULT']['script_dir'])

        if self.test_flag == 'test':
            self.test_header_array = np.array(['header1', 'header2'])
            self.test_data = np.arange(1000, 2)
            self.test_data_2d = np.meshgrid(self.test_data, self.test_data)
            self.test_file_path = os.path.join(os.path.abspath(os.getcwd()), 'test')
            self.test_file_param_path = os.path.join(os.path.abspath(os.getcwd()), 'test.param')

    def open_1D(self, path, header = 0):
        if self.test_flag != 'test':
            header_array = []

            file_to_read = open(str(path), 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(str(path), dtype = float, delimiter = ',') 
            data = np.transpose(temp)

            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data

    def open_1D_dialog(self, directory = '', header = 0):
        if self.test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Open')

            header_array = [];
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

    def save_1D_dialog(self, data, directory = '', header = ''):
        if self.test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Save')

            np.savetxt(file_path, np.transpose(data), fmt = '%.6e', delimiter = ',',\
                newline = '\n', header = header, footer = '', comments = '# ', encoding = None)

        elif self.test_flag == 'test':
            pass

    def open_2D(self, path, header = 0):
        if self.test_flag != 'test':
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

        elif self.test_flag == 'test':
            return header_array, self.test_data_2d

    def open_2D_dialog(self, directory = '', header = 0):
        if self.test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Open')

            header_array = []
            file_to_read = open(file_path, 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',') 
            data = temp
            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data_2d

    def open_2D_appended(self, path, header = 0, chunk_size = 1):
        if self.test_flag != 'test':
            header_array = []
            file_to_read = open(str(path), 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(str(path), dtype = float, delimiter = ',') 
            data = np.array_split(temp, chunk_size)
            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data_2d

    def open_2D_appended_dialog(self, directory = '', header = 0, chunk_size = 1):
        if self.test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Open')

            header_array = []
            file_to_read = open(file_path, 'r')
            for i, line in enumerate(file_to_read):
                if i is header: break
                temp = line.split(":")
                header_array.append(temp)
            file_to_read.close()

            temp = np.genfromtxt(file_path, dtype = float, delimiter = ',')
            data = np.array_split(temp, chunk_size)
            return header_array, data

        elif self.test_flag == 'test':
            return self.test_header_array, self.test_data_2d

    def save_2D_dialog(self, data, directory = '', header = ''):
        if self.test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Save')
            np.savetxt(file_path, data, fmt = '%.6e', delimiter = ',', newline = '\n', \
                header = header, footer = '', comments = '#', encoding = None)

        elif self.test_flag == 'test':
            pass

    def create_file_dialog(self,  directory = ''):
        if self.test_flag != 'test':
            file_path = self.file_dialog(directory = directory, mode = 'Save')
            open(file_path, "w").close()
            return file_path
            
        elif self.test_flag == 'test':
            return self.test_file_path

    def create_file_parameters(self, add_name, directory = ''):
        if self.test_flag != 'test':
            try:
                file_name = self.create_file_dialog()
                file_save_param = file_name.split('.csv')[0] + str(add_name)
            # pressed cancel Tk_kinter
            except TypeError:
                file_name = os.path.join(self.path_to_main, 'temp.csv')
                file_save_param = file_name.split('.csv')[0] + str(add_name)
            # pressed cancel PyQt
            except FileNotFoundError:
                file_name = os.path.join(self.path_to_main, 'temp.csv')
                file_save_param = file_name.split('.csv')[0] + str(add_name)

            return file_name, file_save_param

        elif self.test_flag == 'test':
            return self.test_file_path, self.test_file_param_path

    def save_header(self, filename, header = '', mode = 'w'):
        if self.test_flag != 'test':
            file_for_save = open(filename, mode)
            np.savetxt(file_for_save, [], fmt='%.6e', delimiter=',', \
                                        newline='\n', header=header, footer='', comments='# ', encoding=None)
            file_for_save.close()
        elif self.test_flag == 'test':
            file_for_save = open(filename, mode)
            file_for_save.close()

    def save_data(self, filename, data, header = '', mode = 'w'):
        if self.test_flag != 'test':
            if len( data.shape ) == 2:
                file_for_save = open(filename, mode)
                np.savetxt(file_for_save, data, fmt='%.6e', delimiter=',', \
                                            newline='\n', header=header, footer='', comments='# ', encoding=None)
                file_for_save.close()

            elif len( data.shape ) == 3:
                for i in range( 0, int( data.shape[0] ) ):
                    if i == 0:
                        file_for_save_i = filename
                        file_for_save = open(file_for_save_i, mode)
                        np.savetxt(file_for_save, np.transpose( data[i] ), fmt='%.6e', delimiter=',', \
                                                    newline='\n', header=header, footer='', comments='# ', encoding=None)
                        file_for_save.close()
                    else:
                        file_for_save_i = filename.split('.csv')[0] + '_' + str(i)   + '.csv'
                        file_for_save = open(file_for_save_i, mode)
                        np.savetxt(file_for_save, np.transpose( data[i] ), fmt='%.6e', delimiter=',', \
                                                    newline='\n', header=header, footer='', comments='# ', encoding=None)
                        file_for_save.close()

        elif self.test_flag == 'test':
            file_for_save = open(filename, mode)
            file_for_save.close()
            os.remove(filename) 

    def file_dialog(self, directory = '', mode = 'Open'):
        root = tkinter.Tk()
        root.withdraw()

        if mode == 'Open':
            file_path = filedialog.askopenfilename(**dict(
                initialdir = self.open_dir,
                filetypes = [("CSV", "*.csv"), ("TXT", "*.txt"),\
                ("DAT", "*.dat"), ("all", "*.*")],
                title = 'Select file to open')
                )
        elif mode == 'Save':
            file_path = filedialog.asksaveasfilename(**dict(
                initialdir = self.open_dir,
                filetypes = [("CSV", "*.csv"), ("TXT", "*.txt"),\
                ("DAT", "*.dat"), ("all", "*.*")],
                title = 'Select file to save')
                )
        return file_path

def main():
    pass

if __name__ == '__main__':
    main()