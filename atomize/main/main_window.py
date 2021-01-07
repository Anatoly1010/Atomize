#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5 import QtWidgets, uic, QtCore, QtGui
import atomize.main.messenger_socket_server as socket_server

class MainWindow(QtWidgets.QMainWindow):
    """
    A main window class.
    """
    def __init__(self, *args, **kwargs):
        """
        A function for connecting actions and creating a main window.
        """
        super(MainWindow, self).__init__(*args, **kwargs)
        # absolute path to icon:
        self.icon_path = os.path.join(os.path.abspath(os.getcwd()),'atomize/main','icon.ico')
        self.setWindowIcon(QIcon(self.icon_path))

        self.destroyed.connect(MainWindow.on_destroyed)         # connect some actions to exit
        # Load the UI Page
        uic.loadUi('atomize/main/gui/main_window.ui', self)        # Design file

        # important attribures
        if len(sys.argv)> 1 and sys.argv[1]!='':  # for bash option
            self.script = sys.argv[1]
            self.open_file(self.script)
        elif len(sys.argv) == 1:
            self.script='' # for not opened script
        self.flag=1 # for not open two liveplot windows
        self.path=os.path.abspath(os.getcwd());
        # Connection of different action to different Menus and Buttons
        self.button_open.clicked.connect(self.open_file_dialog)
        self.button_open.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_edit.clicked.connect(self.edit_file)
        self.button_edit.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_test.clicked.connect(self.test)
        self.button_test.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_reload.clicked.connect(self.reload)
        self.button_reload.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_start.clicked.connect(self.start_experiment)
        self.button_start.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_liveplot.clicked.connect(self.start_liveplot)
        self.button_liveplot.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_quit.clicked.connect(self.quit)
        self.button_quit.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.textEdit.setStyleSheet("QPlainTextEdit {background-color: rgb(24, 25, 26); color: rgb(255, 172, 0); } QScrollBar:vertical {background-color: rgb(0, 0, 0);}");
        self.text_errors.setStyleSheet("QPlainTextEdit {background-color: rgb(24, 25, 26); color: rgb(255, 170, 0); }")
        
        # for running different processes using QProcess
        self.process = QtCore.QProcess(self)
        self.process_text_editor = QtCore.QProcess(self)
        self.process_python = QtCore.QProcess(self)
        self.process_liveplot = QtCore.QProcess(self)
        self.process.setProgram('pylint')
        self.process_text_editor.setProgram("subl") # we need to know path to text editor
        self.process_python.setProgram('python3')
        self.process_liveplot.setProgram('python3')
        self.process_liveplot.setArguments(['-m', 'liveplot'])
        self.process_liveplot.start()
        self.process_liveplot.finished.connect(self.helper_liveplot)
        self.process.finished.connect(self.on_finished_checking)
        self.process_python.finished.connect(self.on_finished_script)
    def on_destroyed(self):
        """
        A function to do some actions when the main window is closing.
        """
        self.process_python.terminate()
    def start_experiment(self):
        """
        A function to run an experimental script using python.exe.
        """
        if self.script != '':
            stamp = os.stat(self.script).st_mtime
        else:
            self.text_errors.appendPlainText('No experimental script is opened')
            return

        if stamp != self.cached_stamp:
            self.cached_stamp = stamp
            message = QMessageBox(self);  # Message Box for warning of updated file
            message.setWindowTitle("Your script has been changed!")
            message.setStyleSheet("QWidget { background-color : rgb(24, 25, 26); color: rgb(255, 170, 0); }")
            message.addButton(QtWidgets.QPushButton('Discrad and Run'), QtWidgets.QMessageBox.YesRole)
            message.addButton(QtWidgets.QPushButton('Update'), QtWidgets.QMessageBox.NoRole)
            message.setText("Your experimental script has been changed   ");
            message.show();
            message.buttonClicked.connect(self.message_box_clicked)   # connect function clicked to button; get the button name
            return        # stop current function

        self.process_python.setArguments([self.script])
        self.process_python.start()
    def message_box_clicked(self, btn):             # Message Box fow warning
        if btn.text() == "Discrad and Run":
            self.start_experiment()
        elif btn.text() == "Update":
            self.reload()
        else:
            return
    def test(self):
        """
        A function to run a syntax check using pylint.
        """
        self.text_errors.appendPlainText("Testing... Please, wait!")
        self.process.setArguments(['--errors-only', self.script])
        self.process.start()
    def reload(self):
        """
        A function to reload an experimental script.
        """
        self.cached_stamp = os.stat(self.script).st_mtime
        text = open(self.script).read()
        self.textEdit.setPlainText(text)
    def on_finished_checking(self):
        """
        A function to add the information about errors found during syntax checking to a dedicated text box in the main window of the programm.
        """
        text = self.process.readAllStandardOutput().data().decode()
        if text == '':
            self.text_errors.appendPlainText("No errors are found!")
        else:
            self.text_errors.appendPlainText(text)
            self.text_errors.verticalScrollBar().setValue(self.text_errors.verticalScrollBar().maximum())
    def on_finished_script(self):
        """
        A function to add the information about errors found during syntax checking to a dedicated text box in the main window of the programm.
        """
        text = self.process_python.readAllStandardOutput().data().decode()
        text_errors_script = self.process_python.readAllStandardError().data().decode()
        if text == '' and text_errors_script == '':
            self.text_errors.appendPlainText("Script done!")
        elif text == '' and text_errors_script != '':
            self.text_errors.appendPlainText(text_errors_script)
            self.text_errors.verticalScrollBar().setValue(self.text_errors.verticalScrollBar().maximum())
    def quit(self):
        """
        A function to quit the programm
        """
        sys.exit()
    def start_liveplot(self):
        """
        A function to open a new liveplot window
        """
        if self.flag == 0:
            self.process_liveplot.setArguments(['-m', 'liveplot'])
            self.process_liveplot.start()
            self.flag = 1
        else:
            self.text_errors.appendPlainText('Liveplot already opened')
    def helper_liveplot(self):
        """
        A function to check whether there is an open liveplot window
        """
        self.flag = 0;
    def edit_file(self):
        """
        A function to open an experimental script in a text editor.
        """
        self.process_text_editor.setArguments([self.script])
        self.process_text_editor.start()
    def open_file(self, filename):
        """
        A function to open an experimental script.
        :param filename: string
        """
        self.cached_stamp = os.stat(filename).st_mtime
        text = open(filename).read()
        self.textEdit.setPlainText(text)
        self.path = os.path.dirname(filename) # for memorizing the path to the last used folder
        self.script = filename
    def open_file_dialog(self):
        """
        A function to open a new window for choosing an experimental script.
        """
        filedialog = QFileDialog(self, 'Open File', directory = self.path, filter ="text (*.py)")
        # use QFileDialog.DontUseNativeDialog to change directory
        filedialog.setStyleSheet("QWidget { background-color : rgb(136, 138, 133) }")
        filedialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        filedialog.fileSelected.connect(self.open_file)
        filedialog.show()

    #def save_text(self):
    #    text = self.textedit.toPlainText()
    #    with open('mytextfile.txt', 'w') as f:
    #        f.write(text)

    @QtCore.pyqtSlot(str) 
    def add_error_message(self, data):
        """
        A function for adding an error message to a dedicated text box in the main window of the programm;
        This function runs when Helper.changedSignal.emit(str) is emitted.
        :param data: string
        """
        self.text_errors.appendPlainText(str(data))
        if data=='Script stopped':
            self.process_python.terminate()

def main():
    """
    A function to run the main window of the programm.
    """
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    helper = socket_server.Helper()
    server = socket_server.Socket_server()
    # to connect a function add_error_message when the signal from the helper will be emitted.
    helper.changedSignal.connect(main.add_error_message, QtCore.Qt.QueuedConnection)
    threading.Thread(target = server.start_messenger_server, args=(helper,), daemon = True).start()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
