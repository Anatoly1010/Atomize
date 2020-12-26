import pyqtgraph as pg
import pyqtgraph.exporters
import numpy as np

def plot():
	# define the data
	theTitle = "pyqtgraph plot"
	y = [2,4,6,8,10,12,14,16,18,20]
	x = range(0,10)

	# create plot
	plt = pg.plot(x, y, title=theTitle, pen='r')
	#plt.showGrid(x=True,y=True)

	## Start Qt event loop.
	if __name__ == '__main__':
	    import sys
	    if sys.flags.interactive != 1 or not hasattr(pg.QtCore, 'PYQT_VERSION'):
	        pg.QtGui.QApplication.exec_()

