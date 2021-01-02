import os
import sys
import threading
import messenger_socket_server as socket_server
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFileDialog  # QMessageBox
from PyQt5 import QtWidgets, uic, QtCore, QtGui

# Some variables
path = ''

class MainWindow(QtWidgets.QMainWindow):
    """
    A main window class.
    """
    def __init__(self, *args, **kwargs):
        """
        A function for connecting actions and creating a main window.
        """
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
        
        # for running different processes using QProcess
        self.process = QtCore.QProcess(self)
        self.process_text_editor = QtCore.QProcess(self)
        self.process_python = QtCore.QProcess(self)
        self.process.setProgram('pylint')
        self.process_text_editor.setProgram("subl") # we need to know path to text editor
        self.process_python.setProgram('python3')
        self.process.finished.connect(self.on_finished)
    def on_destroyed(self):
        """
        A function to do some actions when the main window is closing.
        """
        pass
    def start_experiment(self):
        """
        A function to run an experimental script using python.exe.
        """
        self.process_python.setArguments([script, '-i'])
        self.process_python.start()
        #self.dialog = pyqtplotter.MainWindow(self)
        #self.dialog.show()
    def test(self):
        """
        A function to run a syntax check using pylint.
        """
        self.text_errors.appendPlainText("Testing... Please, wait!")
        self.process.setArguments(['--errors-only', script])
        self.process.start()
    def on_finished(self):
        """
        A function to add the information about errors found during syntax checking to a dedicated text box in the main window of the programm.
        """
        text = self.process.readAllStandardOutput().data().decode()
        if text == '':
            self.text_errors.appendPlainText("No errors are found!")
        else:
            self.text_errors.appendPlainText(text)
            self.text_errors.verticalScrollBar().setValue(self.text_errors.verticalScrollBar().maximum())
    def quit(self):
        """
        A function to quit the programm
        """
        sys.exit()
    def help(self):
        """
        A function to open a documentation window. Should be done.
        """
        pass
    def edit_file(self):
        """
        A function to open an experimental script in a text editor.
        """
        self.process_text_editor.setArguments(['-i',script])
        self.process_text_editor.start()
    def open_file(self, filename):
        """
        A function to open an experimental script.
        :param filename: string
        """
        global path, script
        text = open(filename).read()
        self.textEdit.setPlainText(text)
        path = os.path.dirname(filename) # for memorizing the path to the last used folder
        script = filename
    def open_file_dialog(self):
        """
        A function to open a new window for choosing an experimental script.
        """
        global path

        if path == '':
            path = ""

        filedialog = QFileDialog(self, 'Open File', directory = path, filter ="text (*.py)")
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
