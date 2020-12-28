#need a better way here. To load a file from different folder
import sys
sys.path.append("/home/anatoly/atomize/plot_modules/")

from pyqtgraph.Qt import QtCore, QtGui
import threading
import numpy as np
import time
import pyqtplotter as plotter

xdata = []
xdata2 = []
ydata = []
ydata2 = []


def create_data1(helper, name):
    for x in np.arange(0,20,0.5):
        xdata.append(x)
        ydata.append(np.exp(-x**2)+10*np.exp(-(x-7)**2))
        time.sleep(1)
        #print(xdata)
        helper.changedSignal.emit(name, (xdata, ydata))
        #helper.changedSignal.emit(name, (xdata, ydata2))


plotter.plot_1d(create_data1, "1")
#add.plot_1d(create_data2, "2")