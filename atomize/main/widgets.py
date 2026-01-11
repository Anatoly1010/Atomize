import warnings
import os
import configparser
import pyqtgraph as pg
import numpy as np
import math
#from tkinter import filedialog
#import tkinter
from datetime import datetime
from pathlib import Path
from pyqtgraph.dockarea import Dock
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QFileDialog
import atomize.main.local_config as lconf
#import OpenGL

pg.setConfigOption('background', (63,63,97))
pg.setConfigOption('leftButtonPan', False)
pg.setConfigOption('foreground', (192, 202, 227))
#pg.setConfigOptions(imageAxisOrder='row-major')

#pg.setConfigOption('useOpenGL', True)
#pg.setConfigOption('enableExperimental', True)
LastExportDirectory = None

def get_widget(rank, name):
    return {
        1: CrosshairDock,
        2: CrossSectionDock,
        }[rank](name=name)

class CloseableDock(Dock):
    docklist = []
    def __init__(self, *args, **kwargs):
        super(CloseableDock, self).__init__(*args, **kwargs)
        style = QtWidgets.QStyleFactory().create("fusion")
        close_icon = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarCloseButton)
        close_button = QtWidgets.QPushButton(close_icon, "", self)
        close_button.clicked.connect(self.close)
        close_button.setGeometry(0, 0, 15, 15)
        close_button.raise_()
        self.closeClicked = close_button.clicked

        #max_icon = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarMaxButton)
        #max_button = QtWidgets.QPushButton(max_icon, "", self)
        #max_button.clicked.connect(self.maximize)
        #max_button.setGeometry(15, 0, 15, 15)
        #max_button.raise_()

        self.closed = False
        CloseableDock.docklist.append(self)

    def close(self):
        self.setParent(None)
        self.closed = True
        if hasattr(self, '_container'):
            if self._container is not self.area.topContainer:
                self._container.apoptose()

    #def maximize(self):
    #    for d in CloseableDock.docklist:
    #        if d is not self and not d.closed:
    #            d.close()

class CrosshairPlotWidget(pg.PlotWidget):
    def __init__(self, parametric = False, *args, **kwargs):
        super(CrosshairPlotWidget, self).__init__(*args, **kwargs)
        self.scene().sigMouseClicked.connect(self.toggle_search)
        self.scene().sigMouseMoved.connect(self.handle_mouse_move)
        self.cross_section_enabled = False
        self.parametric = parametric
        self.search_mode = True
        self.label = None
        self.label2 = None

    def toggle_search(self, mouse_event):
        if mouse_event.double():
            if self.cross_section_enabled:
                self.hide_cross_hair()
            else:
                item = self.getPlotItem()
                vb = item.getViewBox()
                view_coords = vb.mapSceneToView(mouse_event.scenePos())
                x_log_mode, y_log_mode = vb.state['logMode'][0], vb.state['logMode'][1]
                view_x, view_y = view_coords.x(), view_coords.y()
                self.add_cross_hair(view_x, view_y)
        elif self.cross_section_enabled:
            self.search_mode = not self.search_mode
            if self.search_mode:
                self.handle_mouse_move(mouse_event.scenePos())

    def handle_mouse_move(self, mouse_event):
        if self.cross_section_enabled and self.search_mode:
            item = self.getPlotItem()
            vb = item.getViewBox()
            view_coords = vb.mapSceneToView(mouse_event)
            x_log_mode, y_log_mode = vb.state['logMode'][0], vb.state['logMode'][1]
            view_x, view_y = view_coords.x(), view_coords.y()
            if (x_log_mode == True) and (y_log_mode == False):
                view_x = 10**view_x
            elif (x_log_mode == False) and (y_log_mode == True):
                view_y = 10**view_y
            elif (x_log_mode == True) and (y_log_mode == True):
                view_x = 10**view_x
                view_y = 10**view_y

            best_guesses = []
            for data_item in item.items:
                if isinstance(data_item, pg.PlotDataItem) and (data_item.isVisible()):
                    xdata, ydata = data_item.xData, data_item.yData
                    index_distance = lambda i: ((xdata[i]-view_x))**2 + ((ydata[i] - view_y)/view_y)**2
                    if self.parametric:
                        index = min(list(range(len(xdata))), key=index_distance)
                    else:
                        index = min(np.searchsorted(xdata, view_x), len(xdata)-1)
                        if index and xdata[index] - view_x > view_x - xdata[index - 1]:
                            index -= 1
                    pt_x, pt_y = xdata[index], ydata[index]
                    best_guesses.append(((pt_x, pt_y), index_distance(index)))

            if not best_guesses:
                return

            (pt_x, pt_y), _ = min(best_guesses, key=lambda x: x[1])
            
            if (x_log_mode == True) and (y_log_mode == False):
                self.v_line.setPos(math.log10(pt_x))
                self.h_line.setPos(pt_y)
            elif (x_log_mode == False) and (y_log_mode == True):
                self.v_line.setPos(pt_x)
                self.h_line.setPos(math.log10(pt_y))
            elif (x_log_mode == True) and (y_log_mode == True):
                self.v_line.setPos(math.log10(pt_x))
                self.h_line.setPos(math.log10(pt_y))
            else:
                self.v_line.setPos(pt_x)
                self.h_line.setPos(pt_y)

            self.label.setText("x=%.3e, y=%.3e" % (pt_x, pt_y))
            self.label2.setText("cur_x=%.4e, cur_y=%.4e" % (view_x, view_y))

    def add_cross_hair(self, x, y):
        self.h_line = pg.InfiniteLine(pos=y, angle=0, movable=False)
        self.v_line = pg.InfiniteLine(pos=x, angle=90, movable=False)
        self.addItem(self.h_line, ignoreBounds=False)
        self.addItem(self.v_line, ignoreBounds=False)
        if self.label is None:
            self.label = pg.LabelItem(justify="right")
            self.getPlotItem().layout.addItem(self.label, 4, 1)
        if self.label2 is None:
            self.label2 = pg.LabelItem(justify="left")
            self.getPlotItem().layout.addItem(self.label2, 4, 1)
        self.x_cross_index = 0
        self.y_cross_index = 0
        self.cross_section_enabled = True

    def add_cross_hair_zero(self):
        self.h_line = pg.InfiniteLine(angle=0, movable=False)
        self.v_line = pg.InfiniteLine(angle=90, movable=False)
        self.addItem(self.h_line, ignoreBounds=False)
        self.addItem(self.v_line, ignoreBounds=False)
        if self.label is None:
            self.label = pg.LabelItem(justify="right")
            self.getPlotItem().layout.addItem(self.label, 4, 1)
        if self.label2 is None:
            self.label2 = pg.LabelItem(justify="left")
            self.getPlotItem().layout.addItem(self.label2, 4, 1)
        self.x_cross_index = 0
        self.y_cross_index = 0
        self.cross_section_enabled = True

    def hide_cross_hair(self):
        self.removeItem(self.h_line)
        self.removeItem(self.v_line)
        self.cross_section_enabled = False

class CrosshairDock(CloseableDock):
    def __init__(self, **kwargs):
        # open directory
        #path_to_main = os.path.abspath(os.getcwd())
        path_to_main = Path(__file__).parent
        # configuration data
        path_config_file = os.path.join(path_to_main, '..', 'config.ini')
        path_config_file_device = os.path.join(path_to_main, '..', 'device_modules/config')
        path_config_file, path_config2 = lconf.load_config()
        
        config = configparser.ConfigParser()
        config.read(path_config_file)
        # directories
        self.open_dir = str(config['DEFAULT']['open_dir'])
        if self.open_dir == '':
            self.open_dir = lconf.load_scripts(os.path.join(path_to_main, '..', 'tests'))
        
        # for not removing vertical line if the position is the same
        self.ver_line_1 = 0
        self.ver_line_2 = 0
        self.plot_widget = CrosshairPlotWidget()

        # Disabling AutoRange:
        #item = self.plot_widget.getPlotItem()
        #vb = item.getViewBox()
        #vb.disableAutoRange( axis = vb.YAxis )

        self.legend = self.plot_widget.addLegend(offset = (-20, 20), horSpacing = 25, verSpacing = 0)
        #self.plot_widget.setBackground(None)
        kwargs['widget'] = self.plot_widget
        super(CrosshairDock, self).__init__(**kwargs)

        self.menu = self.plot_widget.getMenu()
        self.menu.addSeparator()
        #self.del_menu = QtGui.QMenu()
        self.del_menu = QtWidgets.QMenu()
        self.del_menu.setTitle('Delete Plot')
        self.menu.addMenu(self.del_menu)

        self.shift_menu = QtWidgets.QMenu()
        self.shift_menu.setTitle('Shift Plot')
        self.menu.addMenu(self.shift_menu)

        open_action = QtGui.QAction('Open 1D Data', self)
        open_action.triggered.connect(self.file_dialog) # self.open_file_dialog
        self.menu.addAction(open_action)

        self.avail_colors = [pg.mkPen(color=(47,79,79),width=1), pg.mkPen(color=(255,153,0),width=1), pg.mkPen(color=(255,0,255),width=1), \
        pg.mkPen(color=(0,0,255),width=1), \
        pg.mkPen(color=(0,0,0),width=1), pg.mkPen(color=(255,0,0),width=1), \
        pg.mkPen(color=(95,158,160),width=1), pg.mkPen(color=(0,128,0),width=1), pg.mkPen(color=(255,255,0),width=1), \
        pg.mkPen(color=(255,255,255),width=1)]
        self.avail_symbols= ['x','p','star','s','o','+']
        self.avail_sym_pens = [ pg.mkPen(color=(0, 0, 0), width=0), pg.mkPen(color=(255, 255, 255), width=0),pg.mkPen(color=(0, 255, 0), width=0),
        pg.mkPen(color=(0, 0, 255), width=0),pg.mkPen(color=(255, 0, 0), width=0),pg.mkPen(color=(255, 0, 255), width=0)]
        self.avail_sym_brush = [pg.mkBrush(0, 0, 0, 255), pg.mkBrush(255, 255, 255, 255),pg.mkBrush(0, 255, 0, 255),pg.mkBrush(0, 0, 255, 255),
        pg.mkBrush(255, 0, 0, 255),pg.mkBrush(255, 0, 255, 255)]
        self.used_colors = {}
        self.used_pens = {}
        self.used_symbols = {}
        self.used_brush = {}
        self.curves = {}
        self.del_dict = {}
        self.name_dict = {}
        self.shifter_dict = {}
        self.shifter_action_dict = {}
        self.index_shift = 0
        self.adaptive_scale = 1
        self.value_prev = 0
        # for delete and shift q_action
        self.qaction_added = 0

    def plot(self, *args, **kwargs):
        self.plot_widget.parametric = kwargs.pop('parametric', False)
        vline_arg = kwargs.get('vline', '')
        if kwargs.get('timeaxis', '') == 'True':
            # strange scaling when zoom
            axis = pg.DateAxisItem()
            self.plot_widget.setAxisItems({'bottom': axis})
            self.plot_widget.setLabel("bottom", text=kwargs.get('xname', ''))
        else:
            self.plot_widget.setLabel("bottom", text=kwargs.get('xname', ''), units=kwargs.get('xscale', ''))
        
        self.plot_widget.setLabel("left", text=kwargs.get('yname', ''), units=kwargs.get('yscale', ''))
        name = kwargs.get('name', '')

        if name in self.curves:
            if kwargs.get('scatter', '') == 'True':
                kwargs['pen'] = None;
                kwargs['symbol'] = self.used_symbols[name]
                kwargs['symbolPen'] = self.used_pens[name]
                kwargs['symbolBrush'] = self.used_brush[name]
                kwargs['symbolSize'] = 7
                self.curves[name].setData(*args, **kwargs)
            elif kwargs.get('scatter', '') == 'False':
                if len( np.shape(args[0]) ) > 1:
                    # simultaneous plot of two curves
                    for i in range( len( args[0]) ):
                        if i == 0:
                            kwargs['pen'] = self.used_colors[name]
                            args_mod = (args[0][i], args[1][i])
                            self.curves[name].setData(*args_mod, **kwargs)
                        else:
                            kwargs['pen'] = self.used_colors[name]
                            args_mod = (args[0][0], args[1][0])
                            self.curves[name].setData(*args_mod, **kwargs)
                            # the second curve
                            name = name + '_' + str(i)
                            if name in self.curves:
                                kwargs['name'] = name
                                kwargs['pen'] = self.used_colors[name]
                                args_mod = (args[0][i], args[1][i])
                                self.curves[name].setData(*args_mod, **kwargs)
                                # Text label above the graph
                                temp = kwargs.get('text', '')
                                if temp != '':
                                    self.setTitle( temp )
                            else:
                                kwargs['name'] = name
                                kwargs['pen'] = self.used_colors[name] = self.avail_colors.pop()
                                args_mod = (args[0][i], args[1][i])
                                self.curves[name] = self.plot_widget.plot(*args_mod, **kwargs)
                                # Text label above the graph
                                temp = kwargs.get('text', '')
                                if temp != '':
                                    self.setTitle( temp )

                                # 05-01-2022; shift and delete graphs
                                del_action = QtGui.QAction(str(name), self)
                                shifter = QtWidgets.QDoubleSpinBox()
                                shiftAction = QtWidgets.QWidgetAction(self)
                                self.add_del_shift_actions(name, del_action, shifter, shiftAction)


                else:
                    kwargs['pen'] = self.used_colors[name]
                    self.curves[name].setData(*args, **kwargs)
                    # Text label above the graph
                    temp = kwargs.get('text', '')
                    if temp != '':
                        self.setTitle( temp )

                # vertical lines
                if vline_arg != 'False':
                    try:
                        if self.ver_line_1 != float(vline_arg[0]):
                            self.plot_widget.removeItem(self.vl1)
                            self.ver_line_1 = float(vline_arg[0])
                            self.vl1 = self.plot_widget.addLine( x = self.ver_line_1 )
                        if self.ver_line_2 != float(vline_arg[1]):
                            self.plot_widget.removeItem(self.vl2)
                            self.ver_line_2 = float(vline_arg[1])
                            self.vl2 = self.plot_widget.addLine( x = self.ver_line_2 )
                    except IndexError:
                        pass
        else:
            if kwargs.get('scatter', '') == 'True':
                kwargs['pen'] = None;
                kwargs['symbol'] = self.used_symbols[name] = self.avail_symbols.pop()
                kwargs['symbolPen'] = self.used_pens[name] = self.avail_sym_pens.pop()
                kwargs['symbolBrush'] = self.used_brush[name] = self.avail_sym_brush.pop()
                kwargs['symbolSize'] = 7
                self.curves[name] = self.plot_widget.plot(*args, **kwargs)
            elif kwargs.get('scatter', '') == 'False':
                if len( np.shape(args[0]) ) > 1:
                    # simultaneous plot of two curves
                    for i in range( len( args[0] )):
                        if i == 0:
                            kwargs['pen'] = self.used_colors[name] = self.avail_colors.pop()
                            args_mod = (args[0][i], args[1][i])
                            self.curves[name] = self.plot_widget.plot(*args_mod, **kwargs)
                        else:
                            kwargs['pen'] = self.used_colors[name]
                            args_mod = (args[0][0], args[1][0])
                            # the first curve is already plotted
                            self.curves[name].setData(*args_mod, **kwargs)

                            # 05-01-2022; shift and delete graphs
                            del_action = QtGui.QAction(str(name), self)
                            shifter = QtWidgets.QDoubleSpinBox()
                            shiftAction = QtWidgets.QWidgetAction(self)
                            self.add_del_shift_actions(name, del_action, shifter, shiftAction)

                            name = name + '_' + str(i)
                            
                            if name in self.curves:
                                kwargs['name'] = name
                                args_mod = (args[0][i], args[1][i])
                                # the second curve is a new one
                                self.curves[name].setData(*args_mod, **kwargs)
                                # Text label above the graph
                                temp = kwargs.get('text', '')
                                if temp != '':
                                    self.setTitle( temp )

                                # a little correction for delete and shift q_action
                                self.qaction_added = 1
                            else:
                                kwargs['name'] = name
                                kwargs['pen'] = self.used_colors[name] = self.avail_colors.pop()
                                args_mod = (args[0][i], args[1][i])
                                # the second curve is a new one
                                self.curves[name] = self.plot_widget.plot(*args_mod, **kwargs)
                                # Text label above the graph
                                temp = kwargs.get('text', '')
                                if temp != '':
                                    self.setTitle( temp )

                else:
                    kwargs['pen'] = self.used_colors[name] = self.avail_colors.pop()
                    self.curves[name] = self.plot_widget.plot(*args, **kwargs)
                    # Text label above the graph
                    temp = kwargs.get('text', '')
                    if temp != '':
                        self.setTitle( temp )
                    
                # vertical lines
                if vline_arg != 'False':
                    try:
                        # , pen = pg.mkPen(color=(230, 0, 126), width = 1)
                        self.vl1 = self.plot_widget.addLine( x = float(vline_arg[0]) )
                        self.vl2 = self.plot_widget.addLine( x = float(vline_arg[1]) )
                    except IndexError:
                        pass
            
            if self.qaction_added == 0:
                del_action_2 = QtGui.QAction(str(name), self)
                shifter_2 = QtWidgets.QDoubleSpinBox()
                shiftAction_2 = QtWidgets.QWidgetAction(self)
                self.add_del_shift_actions(name, del_action_2, shifter_2, shiftAction_2)
    
    def add_del_shift_actions(self, gr_name, del_act, shiftspinbox, shift_act):
        """
        05-01-2021
        Auxiliary function for Delete and Shift QActions
        """
        self.del_dict[del_act] = self.plot_widget.listDataItems()[-1]
        self.name_dict[del_act] = gr_name
        del_act.triggered.connect(lambda: self.del_item(self.del_dict[del_act]))
        self.del_menu.addAction(del_act)

        shiftspinbox.setDecimals(3)
        shiftspinbox.setRange(-10, 10)
        shiftspinbox.setSingleStep(0.001)
        shiftspinbox.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        shiftspinbox.setPrefix( f"{gr_name}: " )
        shiftspinbox.setKeyboardTracking(0)
        self.shifter_dict[shiftspinbox] = self.plot_widget.listDataItems()[-1]
        #shifter.valueChanged.connect( self.shift_curve )
        shiftspinbox.valueChanged.connect( lambda: self.shift_curve(self.shifter_dict[shiftspinbox]) )
        shift_act.setDefaultWidget(shiftspinbox)
        self.shift_menu.addAction(shift_act)
        self.shifter_action_dict[shift_act] = self.plot_widget.listDataItems()[-1]
        self.index_shift = 0

    def shift_curve(self, item):

        qboxname = list(self.shifter_dict.keys())[list(self.shifter_dict.values()).index(item)]
        key_name = list(self.curves.keys())[list(self.curves.values()).index(item)]

        value = float( qboxname.value() )
        data = self.get_data( key_name )

        # percentage shifting:
        if self.index_shift == 0:
            self.adaptive_scale = np.sum( data[1][0:4] ) / 5
            self.index_shift = 1
            self.plot( data[0], data[1] + abs( value ) * self.adaptive_scale, \
                name = str( key_name ), scatter = 'False', xname = 'X', xscale = 'arb. u.', yname = 'Y', yscale = 'arb. u.' )
        else:
            if value > self.value_prev:
                if value > 0:
                    self.plot( data[0], data[1] + abs( value ) * self.adaptive_scale, \
                        name = str( key_name ), scatter = 'False', xname = 'X', xscale = 'arb. u.', yname = 'Y', yscale = 'arb. u.' )
                else:
                    self.plot( data[0], data[1] + abs( value - 0.001 ) * self.adaptive_scale, \
                        name = str( key_name ), scatter = 'False', xname = 'X', xscale = 'arb. u.', yname = 'Y', yscale = 'arb. u.' )
            else:
                if value < 0:
                    self.plot( data[0], data[1] - abs( value ) * self.adaptive_scale, \
                        name = str( key_name ), scatter = 'False', xname = 'X', xscale = 'arb. u.', yname = 'Y', yscale = 'arb. u.' )
                else:
                    self.plot( data[0], data[1] - ( abs( value ) + 0.001 ) * self.adaptive_scale, \
                        name = str( key_name ), scatter = 'False', xname = 'X', xscale = 'arb. u.', yname = 'Y', yscale = 'arb. u.' )

        self.value_prev = value

    def del_item(self, item):
        self.plot_widget.removeItem(item)
        key_action = list(self.del_dict.keys())[list(self.del_dict.values()).index(item)]
        key_name = list(self.curves.keys())[list(self.curves.values()).index(item)]
        qbox_action_name = list(self.shifter_action_dict.keys())[list(self.shifter_action_dict.values()).index(item)]
        self.del_dict.pop(key_action, None)
        self.del_menu.removeAction(key_action)
        self.curves.pop(key_name, None)
        self.shifter_dict.pop(key_name, None)
        self.shift_menu.removeAction(qbox_action_name)
        self.avail_colors.append(self.used_colors[self.name_dict[key_action]])
        #TO DO the same for scatter plot

    def open_file(self, filename):
        """
        A function to open 1d data.
        :param filename: string
        """
        file_path = filename

        header_array = []
        header = 0

        file_to_read = open(filename, 'r')
        for i, line in enumerate(file_to_read):
            if i is header: break
            temp = line.split("#")
            header_array.append(temp)
        file_to_read.close()

        temp = np.genfromtxt(file_path, dtype = float, delimiter = ',', skip_header = 1, comments = '#') 
        data = np.transpose(temp)

        if len(data) == 2:
            self.plot(data[0], data[1], parametric = True, name = file_path, xname = 'X', xscale = 'Arb. U.',\
                yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
        elif len(data) == 3 and np.isnan(data[2][0]) != True:
            self.plot(data[0], data[1], parametric = True, name = file_path + '_1', xname = 'X', xscale = 'Arb. U.',\
                yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
            self.plot(data[0], data[2], parametric = True, name = file_path + '_2', xname = 'X', xscale = 'Arb. U.',\
                yname = 'Y', yscale = 'Arb. U.', label = 'Data_2', scatter = 'False')
        elif len(data) == 3 and np.isnan(data[2][0]) == True:
            self.plot(data[0], data[1], parametric = True, name = file_path, xname = 'X', xscale = 'Arb. U.',\
                yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
        elif len(data) == 4 and np.isnan(data[3][0]) == True:
            self.plot(data[0], data[1], parametric = True, name = file_path + '_1', xname = 'X', xscale = 'Arb. U.',\
                yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
            self.plot(data[0], data[2], parametric = True, name = file_path + '_2', xname = 'X', xscale = 'Arb. U.',\
                yname = 'Y', yscale = 'Arb. U.', label = 'Data_2', scatter = 'False')
        elif len(data) == 5 and np.isnan(data[4][0]) == True:
            self.plot(data[0], data[1], parametric = True, name = file_path + '_1', xname = 'X', xscale = 'Arb. U.',\
                yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
            self.plot(data[0], data[3], parametric = True, name = file_path + '_2', xname = 'X', xscale = 'Arb. U.',\
                yname = 'Y', yscale = 'Arb. U.', label = 'Data_2', scatter = 'False')

    # unused
    def open_file_dialog(self, directory = '', header = 0):
        pass
        #file_path = self.file_dialog(directory = directory)

        #header_array = []
        #file_to_read = open(file_path,'r')
        #for i, line in enumerate(file_to_read):
        #    if i is header: break
        #    temp = line.split("#")
        #    header_array.append(temp)
        #file_to_read.close()

        #temp = np.genfromtxt(file_path, dtype = float, delimiter = ',', skip_header = 0) 
        #data = np.transpose(temp)
        #if len(data) == 2:
        #    self.plot(data[0], data[1], parametric = True, name = file_path, xname = 'X', xscale = 'Arb. U.',\
        #    yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
        #elif len(data) == 3:
        #    self.plot(data[0], data[1], parametric = True, name = file_path + '_1', xname = 'X', xscale = 'Arb. U.',\
        #    yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
        #    self.plot(data[0], data[2], parametric = True, name = file_path + '_2', xname = 'X', xscale = 'Arb. U.',\
        #    yname = 'Y', yscale = 'Arb. U.', label = 'Data_2', scatter = 'False')

    def file_dialog(self, directory = ''):
        """
        A function to open a new window for choosing 1d data
        """
        filedialog = QFileDialog(self, 'Open File', directory = self.open_dir, filter = "CSV (*.csv)", \
                                    options = QtWidgets.QFileDialog.Option.DontUseNativeDialog ) 
        # options = QtWidgets.QFileDialog.Option.DontUseNativeDialog
        # use QFileDialog.Option.DontUseNativeDialog to change directory
        filedialog.setStyleSheet("QWidget { background-color : rgb(42, 42, 64); color: rgb(211, 194, 78);}")
        filedialog.setFileMode(QtWidgets.QFileDialog.FileMode.AnyFile)
        filedialog.fileSelected.connect(self.open_file)
        filedialog.show()

        # Tkinter Open 1D data
        #root = tkinter.Tk()
        #root.withdraw()

        #file_path = filedialog.askopenfilename(**dict(
        #    initialdir = self.open_dir,
        #    filetypes = [("CSV", "*.csv"), ("TXT", "*.txt"),\
        #    ("DAT", "*.dat"), ("all", "*.*")],
        #    title = 'Select file to open')
        #    )
        #return file_path

    def clear(self):
        self.plot_widget.clear()

    def get_data(self, label):
        if label in self.curves:
            return self.curves[label].getData()
        else:
            return [], []

    def redraw(self):
        xs_ys = []
        for name in self.curves:
            xs_ys.append((name,) + self.get_data(name))
        self.clear()
        for name, xs, ys in xs_ys:
            self.plot(xs, ys, name=name)

    def setTitle(self, text):
        self.plot_widget.setTitle(text)

class CrossSectionDock(CloseableDock):
    def __init__(self, trace_size = 80, **kwargs):
        self.plot_item = view = pg.PlotItem(labels = kwargs.pop('labels', None))
        self.img_view = kwargs['widget'] = pg.ImageView(view = view)
        # plot options menu
        #view.ctrlMenu.setStyleSheet("QMenu::item:selected {background-color: rgb(40, 40, 40); }")
        view.setAspectLocked(lock=False)
        self.ui = self.img_view.ui
        self.imageItem = self.img_view.imageItem
        super(CrossSectionDock, self).__init__(**kwargs)
        self.closeClicked.connect(self.hide_cross_section)
        self.cross_section_enabled = False
        self.search_mode = False
        self.signals_connected = False
        self.set_histogram(False)

        save_action = QtGui.QAction('Save Data', self)
        save_action.triggered.connect(self.fileSaveDialog)
        self.img_view.scene.contextMenu.append(save_action)

        histogram_action = QtGui.QAction('Histogram', self)
        histogram_action.setCheckable(True)
        histogram_action.triggered.connect(self.set_histogram)
        self.img_view.scene.contextMenu.append(histogram_action)
        
        self.autolevels_action = QtGui.QAction('Autoscale Levels', self)
        self.autolevels_action.setCheckable(True)
        self.autolevels_action.setChecked(True)
        self.autolevels_action.triggered.connect(self.redraw)
        self.ui.histogram.item.sigLevelChangeFinished.connect(lambda: self.autolevels_action.setChecked(False))
        self.img_view.scene.contextMenu.append(self.autolevels_action)
        self.clear_action = QtGui.QAction('Clear Contents', self)
        self.clear_action.triggered.connect(self.clear)
        self.img_view.scene.contextMenu.append(self.clear_action)

        self.ui.histogram.gradient.loadPreset('bipolar')
        try:
            self.connect_signal()
        except RuntimeError:
            warnings.warn('Scene not set up, cross section signals not connected')

        self.y_cross_index = 0
        self.h_cross_section_widget = CrosshairPlotWidget()
        self.h_cross_dock = CloseableDock(name='X trace', widget=self.h_cross_section_widget, area=self.area)
        self.h_cross_section_widget.add_cross_hair_zero()
        self.h_cross_section_widget.search_mode = False
        self.h_cross_section_widget_data = self.h_cross_section_widget.plot([0,0])

        self.x_cross_index = 0
        self.v_cross_section_widget = CrosshairPlotWidget()
        self.v_cross_dock = CloseableDock(name='Y trace', widget=self.v_cross_section_widget, area=self.area)
        self.v_cross_section_widget.add_cross_hair_zero()
        self.v_cross_section_widget.search_mode = False
        self.v_cross_section_widget_data = self.v_cross_section_widget.plot([0,0])

    def setLabels(self, xlabel = "X", ylabel = "Y", zlabel = "Z"):
        print(self.h_cross_dock.label)
        self.plot_item.setLabels(bottom=(xlabel,), left=(ylabel,))
        self.h_cross_section_widget.plotItem.setLabels(bottom=xlabel, left=zlabel)
        self.v_cross_section_widget.plotItem.setLabels(bottom=ylabel, left=zlabel)
        self.ui.histogram.item.axis.setLabel(text=zlabel)

    def setAxisLabels(self, *args, **kwargs):
        self.plot_item.setLabel(axis='bottom', text=kwargs.get('xname', ''), units=kwargs.get('xscale', ''))
        self.plot_item.setLabel(axis='left', text=kwargs.get('yname', ''), units=kwargs.get('yscale', ''))
        self.v_cross_section_widget.plotItem.setLabel(axis='left', text=kwargs.get('zname', ''), units=kwargs.get('zscale', ''))
        self.h_cross_section_widget.plotItem.setLabel(axis='bottom', text=kwargs.get('xname', ''), units=kwargs.get('xscale', ''))
        self.v_cross_section_widget.plotItem.setLabel(axis='bottom', text=kwargs.get('yname', ''), units=kwargs.get('yscale', ''))
        self.h_cross_section_widget.plotItem.setLabel(axis='left', text=kwargs.get('zname', ''), units=kwargs.get('zscale', ''))

    def setImage(self, *args, **kwargs):
        item = self.plot_item.getViewBox()
        item.invertY(False)        
        if 'pos' in kwargs:
            self._x0, self._y0 = kwargs['pos']
        else:
            self._x0, self._y0 = 0, 0
        if 'scale' in kwargs:
            self._xscale, self._yscale = kwargs['scale']
        else:
            self._xscale, self._yscale = 1, 1

        autorange = self.img_view.getView().vb.autoRangeEnabled()[0]
        kwargs['autoRange'] = autorange
        self.img_view.setImage(*args, **kwargs )
        self.img_view.getView().vb.enableAutoRange(enable = autorange)
        self.update_cross_section()

    def setTitle(self, text):
        self.plot_item.setTitle(text)

    def redraw(self):
        self.setImage(self.img_view.imageItem.image)

    def get_data(self):
        img = self.img_view.imageItem.image
        if img is not None and img.shape != (1, 1):
            return img
        else:
            return None

    def clear(self):
        self.plot_item.enableAutoRange()

    def toggle_cross_section(self):
        if self.cross_section_enabled:
            self.hide_cross_section()
        else:
            self.add_cross_section()

    def set_histogram(self, visible):
        # ROI, histogram settings when QAction is triggered
        self.ui.histogram.setVisible(visible)
        self.ui.roiBtn.setVisible(False)
        self.ui.normGroup.setVisible(False)
        self.ui.menuBtn.setVisible(visible)

    def save_image_data(self, fileName):
        global LastExportDirectory
        LastExportDirectory = os.path.split(fileName)[0]

        data = self.img_view.getProcessedImage()
        try:
            np.savetxt(fileName,\
             data, fmt = '%.4e', delimiter = ',', newline = '\n',\
             header = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S")),\
              footer = '', comments = '#', encoding = None)
        except ValueError:
            for i in range( len(data) ):
                np.savetxt(fileName + str(i),\
                 data[i], fmt = '%.4e', delimiter = ',', newline = '\n',\
                 header = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S")),\
                  footer = '', comments = '#', encoding = None)

    def fileSaveDialog(self):
        self.fileDialog = QFileDialog()
        #self.fileDialog.setOption(QtGui.QFileDialog.Option.DontUseNativeDialog)
        self.fileDialog.setNameFilters(['*.csv','*.txt','*.dat'])
        self.fileDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        global LastExportDirectory
        exportDir = LastExportDirectory
        if exportDir is not None:
            self.fileDialog.setDirectory(exportDir)

        self.fileDialog.show()
        self.fileDialog.fileSelected.connect(self.save_image_data)
        return

    def add_cross_section(self):
        if self.imageItem.image is not None:
            (min_x, max_x), (min_y, max_y) = self.imageItem.getViewBox().viewRange()
            mid_x, mid_y = (max_x + min_x)/2., (max_y + min_y)/2.
        else:
            mid_x, mid_y = 0, 0
        self.h_line = pg.InfiniteLine(pos=mid_y, angle=0, movable=False)
        self.v_line = pg.InfiniteLine(pos=mid_x, angle=90, movable=False)
        self.plot_item.addItem(self.h_line, ignoreBounds=False)
        self.plot_item.addItem(self.v_line, ignoreBounds=False)
        self.x_cross_index = 0
        self.y_cross_index = 0
        self.cross_section_enabled = True
        self.text_item = pg.LabelItem(justify="right")
        #self.img_view.ui.gridLayout.addWidget(self.text_item, 2, 1, 1, 2)
        #self.img_view.ui.graphicsView.addItem(self.text_item)#, 2, 1)
        self.plot_item.layout.addItem(self.text_item, 4, 1)
        #self.cs_layout.addItem(self.label, 2, 1) #TODO: Find a way of displaying this label
        self.search_mode = True

        self.area.addDock(self.h_cross_dock)
        self.area.addDock(self.v_cross_dock, position='right', relativeTo=self.h_cross_dock)
        self.cross_section_enabled = True

    def hide_cross_section(self):
        if self.cross_section_enabled:
            self.plot_item.removeItem(self.h_line)
            self.plot_item.removeItem(self.v_line)
            self.img_view.ui.graphicsView.removeItem(self.text_item)
            self.cross_section_enabled = False

            self.h_cross_dock.close()
            self.v_cross_dock.close()

    def connect_signal(self):
        """This can only be run after the item has been embedded in a scene"""
        if self.signals_connected:
            warnings.warn("")
        if self.imageItem.scene() is None:
            raise RuntimeError('Signal can only be connected after it has been embedded in a scene.')
        self.imageItem.scene().sigMouseClicked.connect(self.toggle_search)
        self.imageItem.scene().sigMouseMoved.connect(self.handle_mouse_move)
        self.img_view.timeLine.sigPositionChanged.connect(self.update_cross_section)
        self.signals_connected = True

    def toggle_search(self, mouse_event):
        if mouse_event.double():
            self.toggle_cross_section()
        elif self.cross_section_enabled:
            self.search_mode = not self.search_mode
            if self.search_mode:
                self.handle_mouse_move(mouse_event.scenePos())

    def handle_mouse_move(self, mouse_event):
        if self.cross_section_enabled and self.search_mode:
            view_coords = self.imageItem.getViewBox().mapSceneToView(mouse_event)
            view_x, view_y = view_coords.x(), view_coords.y()
            item_coords = self.imageItem.mapFromScene(mouse_event)
            item_x, item_y = item_coords.x(), item_coords.y()
            max_x, max_y = self.imageItem.image.shape
            if item_x < 0 or item_x > max_x or item_y < 0 or item_y > max_y:
                return
            self.v_line.setPos(view_x)
            self.h_line.setPos(view_y)
            #(min_view_x, max_view_x), (min_view_y, max_view_y) = self.imageItem.getViewBox().viewRange()
            self.x_cross_index = max(min(int(item_x), max_x-1), 0)
            self.y_cross_index = max(min(int(item_y), max_y-1), 0)
            z_val = self.imageItem.image[self.x_cross_index, self.y_cross_index]
            self.update_cross_section()
            self.text_item.setText("x=%.3e, y=%.3e, z=%.3e" % (view_x, view_y, z_val))

    def update_cross_section(self):
        nx, ny = self.imageItem.image.shape
        x0, y0, xscale, yscale = self._x0, self._y0, self._xscale, self._yscale
        xdata = np.linspace(x0, x0+(xscale*(nx-1)), nx)
        ydata = np.linspace(y0, y0+(yscale*(ny-1)), ny)
        zval = self.imageItem.image[self.x_cross_index, self.y_cross_index]
        self.h_cross_section_widget_data.setData(xdata, self.imageItem.image[:, self.y_cross_index])
        self.h_cross_section_widget.v_line.setPos(xdata[self.x_cross_index])
        self.h_cross_section_widget.h_line.setPos(zval)
        self.v_cross_section_widget_data.setData(ydata, self.imageItem.image[self.x_cross_index, :])
        self.v_cross_section_widget.v_line.setPos(ydata[self.y_cross_index])
        self.v_cross_section_widget.h_line.setPos(zval)

class MoviePlotDock(CrossSectionDock):
    def __init__(self, array, *args, **kwargs):
        super(MoviePlotDock, self).__init__(*args, **kwargs)
        self.setImage(array)
        self.tpts = len(array)
        play_button = QtWidgets.QPushButton("Play")
        stop_button = QtWidgets.QPushButton("Stop")
        stop_button.hide()
        self.addWidget(play_button)
        self.addWidget(stop_button)
        self.play_timer = QtCore.QTimer()
        self.play_timer.setInterval(50)
        self.play_timer.timeout.connect(self.increment)
        play_button.clicked.connect(self.play_timer.start)
        play_button.clicked.connect(play_button.hide)
        play_button.clicked.connect(stop_button.show)
        stop_button.clicked.connect(self.play_timer.stop)
        stop_button.clicked.connect(play_button.show)
        stop_button.clicked.connect(stop_button.hide)

    def increment(self):
        self.img_view.setCurrentIndex((self.img_view.currentIndex + 1) % self.tpts)

