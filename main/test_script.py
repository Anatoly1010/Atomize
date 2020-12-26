import pyqtplotter
import pyqtgraph as pg
from PyQt5 import QtWidgets
import sys
import time

y = [2,4,6,8,10,12,14,16,18,20]
x = range(0,10)

pyqtplotter.plot_1d(x,y)

print(1)
time.sleep(1)

pyqtplotter.plot_1d(x,y, "clear")

y2 = [1,2,3,4,5,6,7,8,9,10]
x2 = range(0,10)

pyqtplotter.plot_1d(x2,y2)