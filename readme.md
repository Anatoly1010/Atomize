# Atomize

To do:

A. Modules/Connection/Config
- Need a good way to load a file from different folder. It was partily done. There is only an issue with folders that are not in the root of the project
- Config files for devices
- Connect messages about errors during executing of experimental script with the bottom QPlainText from MainWindow
- Create special modules for connection using different protocols
- Write a detailed instruction how to install gpib library on Linux. Test gpib library on windows.

B. Liveplot
- An issue with append_y() when run from a test experimental script. The workaround is to add a dummy graph after append_y. Like:
plotter.append_y('test', -val, start_step=(xs[0], xs[1]-xs[0]), label='down')

plotter.plot_xy('test',[0],[0])
- Need a way to stop executing of experimental script from the main window of liveplot without closing it
- Need a way to save data from plots without using an internal pyqtgraph widget or at least check how 2D data looks like
- Need a special widget to grab a curve from plot and move it up/down, right/left
- Run python -m liveplot toghether with the main window of the programm

C. Interactive GUI 
- Create a possiblity of creating an interactive GUI for changing experimental parameters. Check fsc2 for details










