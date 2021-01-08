import sys
import time
import numpy as np
from multiprocessing import Process, Pipe
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSpinBox, QHBoxLayout, QLabel, QPushButton
from liveplot import LivePlotClient

class Worker(QWidget):
	def __init__(self,parent=None):
		super(Worker, self).__init__(parent)
		self.command='start'
	def script(self, conn, param_1, param_2, param_3, param_4):
		plotter = LivePlotClient()
		xs=np.array([]);
		ys=np.array([]);
		i=0;
		#Plot_xy Test
		while i < param_1 and self.command!='exit':
			if conn.poll()==True:
				self.command=conn.recv()

			xs = np.append(xs, i);
			ys = np.append(ys, np.random.randint(0, param_3 + 1));
			plotter.plot_xy('Plot XY Test', xs, ys, label='test data')
			time.sleep(param_2/1000)
			i=i+1

class TestWindow(QWidget):
	def __init__(self):
		super(TestWindow, self).__init__()
		self.setStyleSheet("background-color: rgb(24, 25, 26); color: rgb(255, 170, 0); ")
		self.setWindowTitle("GUI Script")
		self.layout = QVBoxLayout(self)
		layout_fields = QHBoxLayout()
		spinbox_layout = QVBoxLayout()
		text_layout = QVBoxLayout()
		layout_buttons = QVBoxLayout()

		# Create 4 spinboxes
		self.spinbox_1, self.spinbox_2,\
		self.spinbox_3, self.spinbox_4 = (QSpinBox(),QSpinBox(),
			QSpinBox(),QSpinBox())

		# Create 4 labels
		self.label_1, self.label_2,\
		self.label_3, self.label_4 = (QLabel('Points:'), QLabel('Timer (ms):'),
			QLabel('Noise Level:'),QLabel('Blank:'))

		# Create 3 buttons
		self.button_1, self.button_2,self.button_3 = (QPushButton('Start Script'),
			QPushButton('Read Parameters'), QPushButton('Stop Script'))

		# Create several lists for comfortable assignment
		sb_list=(self.spinbox_1,self.spinbox_2,
			self.spinbox_3,self.spinbox_4)
		value_list=(20,1,10,10)
		label_list=(self.label_1,self.label_2,
			self.label_3,self.label_4)
		button_list=(self.button_1, self.button_2, self.button_3)
		function_B_list=(self.funcB1, self.funcB2,
		 self.funcB3) # All the functions should be declared
		function_SB_list=(self.funcSB1, self.funcSB2,
		 self.funcSB3, self.funcSB4) # All the functions should be declared

		# Settings, connection of functions, adding of widgets
		i=0;
		while i < len(sb_list):
			sb_list[i].setRange(0,9000)
			sb_list[i].setSingleStep(10)
			sb_list[i].setValue(value_list[i])
			# Connect functions
			sb_list[i].valueChanged.connect(function_SB_list[i])
			spinbox_layout.addWidget(sb_list[i])
			i=i+1;

		i=0;
		while i < len(button_list):
			button_list[i].clicked.connect(function_B_list[i])
			layout_buttons.addWidget(button_list[i])
			i=i+1;

		for elements in label_list:
			text_layout.addWidget(elements)

		# Create attributes for parameters
		self.param_1=self.spinbox_1.value()
		self.param_2=self.spinbox_2.value()
		self.param_3=self.spinbox_3.value()
		self.param_4=self.spinbox_4.value()

		# layouting GUI elements
		layout_fields.addLayout(text_layout)
		layout_fields.addLayout(spinbox_layout)

		self.layout.addLayout(layout_fields)
		self.layout.addLayout(layout_buttons)

		#Creating a process to speak with script
		self.worker = Worker()

	def funcSB1(self):
		self.param_1 = self.spinbox_1.value()
	def funcSB2(self):
		self.param_2 = self.spinbox_2.value()
	def funcSB3(self):
		self.param_3 = self.spinbox_3.value()
	def funcSB4(self):
		self.param_4 = self.spinbox_4.value()

	def funcB1(self):
		self.parent_conn, child_conn = Pipe()
		self.script_process = Process(target=self.worker.script, args=(child_conn,
			self.param_1,self.param_2,self.param_3,self.param_4))
		self.script_process.start()
		self.parent_conn.send('start')
	def funcB2(self):
		self.param_1 = self.spinbox_1.value()
		self.param_2 = self.spinbox_2.value()
		self.param_3 = self.spinbox_3.value()
		self.param_4 = self.spinbox_4.value()
		print(self.param_1,self.param_2,self.param_3,self.param_4)
	def funcB3(self):
		try:
			self.parent_conn.send('exit')
		except BrokenPipeError:
			print('No script is running')
		self.script_process.join()


if __name__ == "__main__":
    app = QApplication([])
    win = TestWindow()
    win.show()
    app.exec_()
