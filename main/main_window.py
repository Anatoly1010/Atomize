import sys
import os
import time
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog #QMessageBox
from PyQt5.QtGui import QColor 

# Some variables
path = ''

# DESCRIPTION OF GUI FUNCTIONS AND WINDOWS
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.destroyed.connect(MainWindow.on_destroyed)         # connect some actions to exit

        # Load the UI Page
        uic.loadUi('gui/main_window.ui', self)        # Design file

        # Connection of different action to different Menus and Buttons
        self.button_open.clicked.connect(self.open_file_dialog)
        self.button_open.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_edit.clicked.connect(self.edit_file)
        self.button_edit.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_test.clicked.connect(self.test)
        self.button_test.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_start.clicked.connect(self.start_experiment)
        self.button_start.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_help.clicked.connect(self.help)
        self.button_help.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.button_quit.clicked.connect(self.quit)
        self.button_quit.setStyleSheet("QPushButton {border-radius: 4px; background-color: rgb(136, 138, 133); border-style: outset; } QPushButton:pressed {background-color: rgb(255, 170, 0); ; border-style: inset}");
        self.textEdit.setStyleSheet("QPlainTextEdit {background-color: rgb(24, 25, 26); color: rgb(255, 172, 0); } QScrollBar:vertical {background-color: rgb(0, 0, 0);}");
        self.text_errors.setStyleSheet("QPlainTextEdit {background-color: rgb(24, 25, 26); color: rgb(255, 170, 0); }")
        
        # for running a test in pylint.exe using QProcess
        self.process = QtCore.QProcess(self)
        self.process_text_editor = QtCore.QProcess(self)
        self.process_python = QtCore.QProcess(self)
        self.process.setProgram('pylint')
        self.process_text_editor.setProgram("subl")
        # we need to know path to text editor
        self.process_python.setProgram('python3')
        # for getting data when the process is finished
        self.process.finished.connect(self.on_finished)
    # function for destroying the main window
    def on_destroyed(self):
        ###er031m.field_controller_command('cf0')
        pass
    # Functions that are connected to Menu
    def start_experiment(self):
        self.process_python.setArguments([script, '-i'])
        self.process_python.start()    # for running a script in another process using python.exe
        #self.dialog = pyqtplotter.MainWindow(self)
        #self.dialog.show()

    # To run syntax check
    def test(self): 
        self.text_errors.appendPlainText("Testing... Please, wait!")
        self.process.setArguments(['--errors-only', script])
        self.process.start()
    # To add error information to QPlainText 
    def on_finished(self):
        text = self.process.readAllStandardOutput().data().decode()
        if text == '':
            self.text_errors.appendPlainText("No errors are found!")
        else:
            self.text_errors.appendPlainText(text)
            self.text_errors.verticalScrollBar().setValue(self.text_errors.verticalScrollBar().maximum())

    def quit(self):
        sys.exit()

    def help(self):
        pass

    def edit_file(self):
        self.process_text_editor.setArguments([script])
        self.process_text_editor.start()
    # Function for Open Script
    def open_file(self, filename):
        global path, script
        text = open(filename).read()
        self.textEdit.setPlainText(text)
        path = os.path.dirname(filename) # for memorizing the path to the last used folder
        script = filename
    def open_file_dialog(self):
        global path

        if path == '':
            path = ""

        filedialog = QFileDialog(self, 'Open File', directory = path, filter ="text (*.py)")
        # use QFileDialog.DontUseNativeDialog to change directory
        filedialog.setStyleSheet("QWidget { background-color : rgb(136, 138, 133) }")
        # change background color of the open file window
        filedialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        filedialog.fileSelected.connect(self.open_file)
        filedialog.show()

    #def save_text(self):
    #    text = self.textedit.toPlainText()
    #    with open('mytextfile.txt', 'w') as f:
    #        f.write(text)

# Running of the main window
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
