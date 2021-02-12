import sys
import time
import numpy as np
from multiprocessing import Process, Pipe
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton
# import of required devices and general modules

# it should be included for possibility of a test run
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'

#def work():
#    Worker().temp1

# The class of the main window of GUI
class MainWindow(QWidget):

    def __init__(self):
        if test_flag != 'test': # it should be included in order to have correctly working tests
            super(MainWindow, self).__init__()
            #self.ls335 = ls.Lakeshore_335()
            # background of the main window
            self.setStyleSheet("background-color: rgb(42, 42, 64); color: rgb(211, 194, 78); ")
            self.setWindowTitle("GUI Script")
            # layouts of GUI elements (QSpinBox, QLabel,QPushButton) and general layout of layouts
            self.layout = QVBoxLayout(self)
            layout_fields = QHBoxLayout()
            spinbox_layout = QVBoxLayout()
            text_layout = QVBoxLayout()
            layout_buttons = QVBoxLayout()

            # Create 4 spinboxes (for handling integers; QDoubleSpinBox can be used for floats)
            self.spinbox_1, self.spinbox_2= (QDoubleSpinBox(), QDoubleSpinBox())

            # Create 4 labels for our spin boxes
            self.label_1, self.label_2 = (QLabel('Temperature 1:'), QLabel('Temperature 2:'))

            # Create 3 buttons to interacte with the experimental script
            self.button_1, self.button_2, self.button_3 = (QPushButton('Set Temperature 1'),
                QPushButton('Read Parameters'), QPushButton('Set Temperature 2'))

            # Create several lists for comfortable assignment for our GUI elements
            sb_list = (self.spinbox_1, self.spinbox_2) # spinboxes
            value_list = (25, 5) # initial values for QSpinBoxes
            label_list = (self.label_1, self.label_2) # labels
            button_list = (self.button_1, self.button_2, self.button_3) # buttons
            function_B_list = (self.funcB1, self.funcB2,
             self.funcB3) # All the functions should be declared (at least as passing)
            function_SB_list = (self.funcSB1, self.funcSB2) # All the functions should be declared

            # Settings, connection of functions, adding of widgets to layouts
            i = 0
            while i < len(sb_list):
                sb_list[i].setRange(2, 300) # range of QSpinBox; it is important to set correct range here,
                # since intrnal parameter tests cannot work in scripts with GUI
                sb_list[i].setSingleStep(0.1) # step of QSpinBox
                sb_list[i].setValue(value_list[i]) # set value of QSpinBox
                # Connect functions
                sb_list[i].valueChanged.connect(function_SB_list[i]) 
                # function funcSB1, etc. will be triggered when the QSpinBox_1 value changes
                spinbox_layout.addWidget(sb_list[i])
                # add SpinBoxes to the layout
                i = i + 1

            i = 0
            while i < len(button_list):
                button_list[i].clicked.connect(function_B_list[i])
                # function funcB1, etc. will be triggered when the QPushButton_1 is clicked
                layout_buttons.addWidget(button_list[i])
                # add PushButtons to the layout
                i = i + 1

            for elements in label_list:
                text_layout.addWidget(elements)
                # add Labels to the layout

            # Create attributes for parameters of the experimental script
            self.param_1 = self.spinbox_1.value()
            self.param_2 = self.spinbox_2.value()

            # layouting GUI elements
            layout_fields.addLayout(text_layout)
            layout_fields.addLayout(spinbox_layout)

            self.layout.addLayout(layout_fields)
            self.layout.addLayout(layout_buttons)

            """
            Create a process to interact with an experimental script that will run on a different thread.
            We need a different thread here, since PyQt GUI applications have a main thread of execution 
            that runs the event loop and GUI. If you launch a long-running task in this thread, then your GUI
            will freeze until the task terminates. During that time, the user won’t be able to interact with 
            the application
            """
            self.worker = Worker()

            
        elif test_flag == 'test': # it should be included in order to skip tests
            # we cannot run test in script with GUI because of GUI mainloop
            pass

    # Functions that are connected to the change of QSpinBox value 
    def funcSB1(self):
        # rewritten the experimental script parameter 1
        self.param_1 = self.spinbox_1.value()

    def funcSB2(self):
        self.param_2 = self.spinbox_2.value()

    # Functions that are connected to the QPushButton
    def funcB1(self):
        """
        Button Start; Run function script(pipe_addres, four parameters of the experimental script)
        from Worker class in a different thread
        Create a Pipe for interaction with this thread
        Self.param_i are used as parameters for script function
        """
        # a process for running function script
        self.script_process = Process(target = self.worker.temp1, args = (self.param_1, ))
        self.script_process.start()

    def funcB2(self):
        """
        Button Read changes the experimental script parameters
        """
        self.param_1 = self.spinbox_1.value()
        self.param_2 = self.spinbox_2.value()

    def funcB3(self):
        """
        Button Start; Run function script(pipe_addres, four parameters of the experimental script)
        from Worker class in a different thread
        Create a Pipe for interaction with this thread
        Self.param_i are used as parameters for script function
        """
        # a process for running function script 
        self.script_process = Process(target = self.worker.temp2, args = (self.param_2, ))
        self.script_process.start()


# The worker class that run the experimental script in a different thread
class Worker(QWidget):
    def __init__(self, parent = None):
        super(Worker, self).__init__(parent)

    def temp1(self, param_1):
        """
        function that contains our experimental script

        """
        import atomize.general_modules.general_functions as general
        import atomize.device_modules.Lakeshore_335 as ls
        ls335 = ls.Lakeshore_335()

        ls335.tc_setpoint(float(param_1))
        general.message(f'Temperature {param_1} K has been set')

    def temp2(self, param_2):
        """
        function that contains our experimental script
        """
        import atomize.general_modules.general_functions as general
        import atomize.device_modules.Lakeshore_335 as ls
        ls335 = ls.Lakeshore_335()

        ls335.tc_setpoint(float(param_2))
        general.message(f'Temperature {param_2} K has been set')


# Running GUI mainloop
if __name__ == "__main__":
    if test_flag != 'test': # it should be included in order to skip tests
        app = QApplication([])
        win = MainWindow()
        win.show()
        app.exec_()
    elif test_flag == 'test': # it should be included in order to skip tests
        pass


