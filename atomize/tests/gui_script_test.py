import sys
import time
import numpy as np
from multiprocessing import Process, Pipe
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSpinBox, QHBoxLayout, QLabel, QPushButton
from liveplot import LivePlotClient
import atomize.device_modules.config.messenger_socket_client as send
# import of required devices and general modules

# The class of the main window of GUI
class MainWindow(QWidget):
	def __init__(self):
		super(MainWindow, self).__init__()
		# background of the main window
		self.setStyleSheet("background-color: rgb(24, 25, 26); color: rgb(255, 170, 0); ")
		self.setWindowTitle("GUI Script")
		# layouts of GUI elements (QSpinBox, QLabel,QPushButton) and general layout of layouts
		self.layout = QVBoxLayout(self)
		layout_fields = QHBoxLayout()
		spinbox_layout = QVBoxLayout()
		text_layout = QVBoxLayout()
		layout_buttons = QVBoxLayout()

		# Create 4 spinboxes (for handling integers; QDoubleSpinBox can be used for floats)
		self.spinbox_1, self.spinbox_2,\
		self.spinbox_3, self.spinbox_4 = (QSpinBox(),QSpinBox(),
			QSpinBox(),QSpinBox())

		# Create 4 labels for our spin boxes
		self.label_1, self.label_2,\
		self.label_3, self.label_4 = (QLabel('Points:'), QLabel('Timer (ms):'),
			QLabel('Noise Level:'),QLabel('Blank:'))

		# Create 3 buttons to interacte with the experimental script
		self.button_1, self.button_2,self.button_3 = (QPushButton('Start Script'),
			QPushButton('Read Parameters'), QPushButton('Stop Script'))

		# Create several lists for comfortable assignment for our GUI elements
		sb_list=(self.spinbox_1,self.spinbox_2,
			self.spinbox_3,self.spinbox_4) # spinboxes
		value_list=(20,1,10,10) # initial values for QSpinBoxes
		label_list=(self.label_1,self.label_2,
			self.label_3,self.label_4) # labels
		button_list=(self.button_1, self.button_2, self.button_3) # buttons
		function_B_list=(self.funcB1, self.funcB2,
		 self.funcB3) # All the functions should be declared (at least as passing)
		function_SB_list=(self.funcSB1, self.funcSB2,
		 self.funcSB3, self.funcSB4) # All the functions should be declared

		# Settings, connection of functions, adding of widgets to layouts
		i=0;
		while i < len(sb_list):
			sb_list[i].setRange(0,9000) # range of QSpinBox
			sb_list[i].setSingleStep(10) # step of QSpinBox
			sb_list[i].setValue(value_list[i]) # set value of QSpinBox
			# Connect functions
			sb_list[i].valueChanged.connect(function_SB_list[i]) 
			# function funcSB1, etc. will be triggered when the QSpinBox_1 value changes
			spinbox_layout.addWidget(sb_list[i])
			# add SpinBoxes to the layout
			i=i+1;

		i=0;
		while i < len(button_list):
			button_list[i].clicked.connect(function_B_list[i])
			# function funcB1, etc. will be triggered when the QPushButton_1 is clicked
			layout_buttons.addWidget(button_list[i])
			# add PushButtons to the layout
			i=i+1;

		for elements in label_list:
			text_layout.addWidget(elements)
			# add Labels to the layout

		# Create attributes for parameters of the experimental script
		self.param_1=self.spinbox_1.value()
		self.param_2=self.spinbox_2.value()
		self.param_3=self.spinbox_3.value()
		self.param_4=self.spinbox_4.value()

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

	# Functions that are connected to the change of QSpinBox value 
	def funcSB1(self):
		# rewritten the experimental script parameter 1
		self.param_1 = self.spinbox_1.value()
	def funcSB2(self):
		self.param_2 = self.spinbox_2.value()
	def funcSB3(self):
		self.param_3 = self.spinbox_3.value()
	def funcSB4(self):
		self.param_4 = self.spinbox_4.value()
	# Functions that are connected to the QPushButton
	def funcB1(self):
		"""
		Button Start; Run function script(pipe_addres, four parameters of the experimental script)
		from Worker class in a different thread
		Create a Pipe for interaction with this thread
		Self.param_i are used as parameters for script function
		"""
		self.parent_conn, child_conn = Pipe()
		# a process for running function script 
		self.script_process = Process(target=self.worker.script, args=(child_conn,
			self.param_1,self.param_2,self.param_3,self.param_4))
		self.script_process.start()
		# send a command in a different thread about the current state
		self.parent_conn.send('start')
	def funcB2(self):
		"""
		Button Read changes the experimental script parameters
		"""
		self.param_1 = self.spinbox_1.value()
		self.param_2 = self.spinbox_2.value()
		self.param_3 = self.spinbox_3.value()
		self.param_4 = self.spinbox_4.value()
	def funcB3(self):
		"""
		Button Stop stops the script function from Worker class by sending 'exit' command to it
		"""
		try:
			self.parent_conn.send('exit')
		except BrokenPipeError:
			print('No script is running')
		self.script_process.join()

# The worker class that run the experimental script in a different thread
class Worker(QWidget):
	def __init__(self,parent=None):
		super(Worker, self).__init__(parent)
		# initialization of the attribute we use to stop the experimental script
		# when button Stop is pressed
		self.command='start'
	def script(self, conn, param_1, param_2, param_3, param_4):
		"""
		function that contains our experimental script
		We use four parameters to modify the script in GUI
		Param_1 - number of points
		Param_2 - time between consecutive points
		Param_3 - noise level in dummy data
		Param_4 - blank
		"""
		# Plot_xy script, dummy data
		start_time = time.time()

		plotter = LivePlotClient()
		xs=np.array([]);
		ys=np.array([]);
		i=0;
		# always test our self.command attribute for stopping the script when neccessary
		while i < param_1 and self.command!='exit':
			# poll() checks whether there is data in the Pipe to read
			# we use it to stop the script if the exit command was sent from the main window
			# we read data by conn.recv() only when there is the data to read
			if conn.poll()==True:
				self.command=conn.recv()
			# script loop
			xs = np.append(xs, i);
			ys = np.append(ys, np.random.randint(0, param_3 + 1));
			plotter.plot_xy('Plot XY Test', xs, ys, label='test data')
			time.sleep(param_2/1000)
			i=i+1
		send.message(str(time.time() - start_time))

# Running GUI mainloop
if __name__ == "__main__":
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec_()
