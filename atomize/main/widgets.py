import warnings
import os
import configparser
import pyqtgraph as pg
import numpy as np
import math
from datetime import datetime
from pathlib import Path
from pyqtgraph.dockarea import Dock
from PyQt6 import QtWidgets, QtCore, QtGui
import atomize.main.local_config as lconf

pg.setConfigOption('background', (63,63,97))
pg.setConfigOption('leftButtonPan', False)
pg.setConfigOption('foreground', (192, 202, 227))
#pg.setConfigOptions(imageAxisOrder='row-major')

LastExportDirectory = None

def get_widget(rank, name):
    return {
        1: CrosshairDock,
        2: CrossSectionDock,
        }[rank](name=name)

class CloseableDock(Dock):
    docklist = []
    def __init__(self, *args, **kwargs):
        # Default 'closable' to False to prevent pyqtgraph's native button from interfering
        kwargs.setdefault('closable', False)
        super(CloseableDock, self).__init__(*args, **kwargs)
        
        self.setStyleSheet("background: rgba(42, 42, 64, 255);")
        style = QtWidgets.QStyleFactory().create("fusion")
        close_icon = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TitleBarCloseButton)
        
        self.close_button = QtWidgets.QPushButton(close_icon, "", self)
        self.close_button.setGeometry(0, 0, 13, 13)
        self.close_button.setStyleSheet("border: rgba(0, 0, 0, 255); background: rgba(211, 194, 78, 255);")
        self.close_button.raise_()
        self.close_button.clicked.connect(self.close)
        
        self.closeClicked = self.close_button.clicked
        self.closed = False
        CloseableDock.docklist.append(self)

    def containerChanged(self, container):
        """Triggered by pyqtgraph when the dock moves (including floating)."""
        super().containerChanged(container)
        container.setStyleSheet(f"background-color: rgba(42, 42, 64, 255);")
        # Ensure button is on top when it moves to a new floating window
        self.update_button_layout()

    def resizeEvent(self, event):
        """Keeps the button in the top-right corner during any resize."""
        super().resizeEvent(event)
        self.update_button_layout()

    def update_button_layout(self):
        """Positions the button relative to the current dock size."""
        margin = 0
        # Position at top-right
        self.close_button.move(margin, margin)
        self.close_button.raise_()

    def close(self):
        self.setParent(None)
        self.closed = True
        if hasattr(self, '_container'):
            if self._container is not self.area.topContainer:
                self._container.apoptose()

class CrosshairPlotWidget(pg.PlotWidget):
    def __init__(self, parametric = False, *args, **kwargs):
        super(CrosshairPlotWidget, self).__init__(*args, **kwargs)
        self.scene().sigMouseClicked.connect(self.toggle_search)
        self.scene().sigMouseMoved.connect(self.handle_mouse_move)
        self.cross_section_enabled = False
        self.parametric = parametric
        self.search_mode = True
        #self.label = None
        self.label2 = None
        self.image_operation = 0
        self.click_count = 1
        self.click_count_1d = 0
        self.axis = ['', '']
        self.cross_section = 0

        self.plot_item = self.getPlotItem()
        self.plot_item.ctrl.fftCheck.toggled.connect(self.on_fft_toggled)
        self.plot_item.ctrl.logXCheck.toggled.connect( self.hide_cross_hair )
        self.plot_item.ctrl.logYCheck.toggled.connect( self.hide_cross_hair )
        self.plot_item.ctrl.derivativeCheck.toggled.connect( self.hide_cross_hair )
        self.plot_item.ctrl.phasemapCheck.toggled.connect( self.hide_cross_hair )
        try:
            self.plot_item.ctrl.subtractMeanCheck.toggled.connect( self.hide_cross_hair )
        except Exception:
            pass

        #(63,63,97)
        self.cursor_label = pg.TextItem(anchor=(0, 1), color='w', fill=(42, 42, 64, 150))
        self.cursor_label.border = pg.mkPen((255, 255, 255, 255), width=1.5)
        self.cursor_label.hide()
        # top-level
        self.cursor_label.setZValue(100)
        self.addItem(self.cursor_label)

    def on_fft_toggled(self, enabled):
        if enabled:
            self.hide_cross_hair()
            self.plot_item.setLabel('bottom', 'Frequency', units = 'Hz')
        else:
            try:
                self.hide_cross_hair()
                self.plot_item.setLabel('bottom', self.axis[0], units = self.axis[1])
            except AttributeError:
                pass

    def toggle_search(self, mouse_event):
        if mouse_event.double():
            if self.cross_section_enabled:
                self.hide_cross_hair()
            else:
                #if memorize the last mode; please comment
                self.image_operation = 0
                item = self.getPlotItem()
                vb = item.getViewBox()
                view_coords = vb.mapSceneToView(mouse_event.scenePos())
                view_x, view_y = view_coords.x(), view_coords.y()
                self.add_cross_hair(view_x, view_y)

                #label
                label_text = f"X: {view_x:.4g}\nY: {view_x:.4g}"
                self.cursor_label.border = pg.mkPen((255, 255, 255, 255), width=1.5)
                self.cursor_label.setText(label_text)
                self.cursor_label.setPos(view_x, view_y)
                self.cursor_label.show()

        elif mouse_event.button() == QtCore.Qt.MouseButton.MiddleButton:
            if self.cross_section_enabled:
                self.click_count_1d = (self.click_count_1d + 1 ) % 2
                self.search_mode = not self.search_mode
                if self.click_count_1d == 1:
                    self.cursor_label.border = pg.mkPen((128, 128, 128, 255), width=1.5)
                else:
                    pass
                self.cursor_label.update()

                if self.click_count_1d == 0:
                    self.image_operation = 0
                elif self.click_count_1d == 1:
                    self.image_operation = 1

                mouse_event.accept()
                return 

        elif self.cross_section_enabled:
            ## See mousePressEvent
            #self.click_count = (self.click_count + 1 ) % 2
            #if self.click_count == 0:
            #    self.image_operation = 0
            #elif self.click_count == 1:
            #    self.image_operation = 1
            #if mouse_event.button() == QtCore.Qt.MouseButton.MiddleButton:
            #    self.search_mode = not self.search_mode
            #    self.cursor_label.border = pg.mkPen((255, 255, 255, 255), width=1.5)
            #    self.cursor_label.update()
            if self.search_mode:
                self.handle_mouse_move(mouse_event.scenePos())

    def handle_mouse_move(self, mouse_event):
        if self.cross_section_enabled and self.search_mode:
            item = self.getPlotItem()
            vb = item.getViewBox()
            view_coords = vb.mapSceneToView(mouse_event)
            x_log_mode, y_log_mode = vb.state['logMode'][0], vb.state['logMode'][1]

            # mouse coordinates; log-mode - already log values
            v_x, v_y = view_coords.x(), view_coords.y()

            best_guesses = []
            for data_item in item.items:
                if isinstance(data_item, pg.PlotDataItem) and data_item.isVisible():
                    xdata_0, ydata_0 = data_item.xData, data_item.yData
                    if xdata_0 is None or len(xdata_0) < 2: continue

                    try:
                        if data_item.opts['fftMode'] == True:
                            xdata, ydata = self._fourierTransform(xdata_0, ydata_0)
                            if data_item.opts['logMode'][0]:
                                xdata = xdata[1:]
                                ydata = ydata[1:]
                        elif data_item.opts['subtractMeanMode'] == True:
                            xdata, ydata = xdata_0, ydata_0 - np.mean(ydata_0)
                        elif data_item.opts['derivativeMode'] == True:
                            xdata, ydata = xdata_0[:-1], np.diff(ydata_0) / np.diff(xdata_0)
                        elif data_item.opts['phasemapMode'] == True:
                            xdata, ydata = ydata_0[:-1], np.diff(ydata_0) / np.diff(xdata_0)
                        else:
                            xdata, ydata = xdata_0, ydata_0
                    except KeyError:
                        if data_item.opts['fftMode'] == True:
                            xdata, ydata = self._fourierTransform(xdata_0, ydata_0)
                            if data_item.opts['logMode'][0]:
                                xdata = xdata[1:]
                                ydata = ydata[1:]
                        elif data_item.opts['derivativeMode'] == True:
                            xdata, ydata = xdata_0[:-1], np.diff(ydata_0) / np.diff(xdata_0)
                        elif data_item.opts['phasemapMode'] == True:
                            xdata, ydata = ydata_0[:-1], np.diff(ydata_0) / np.diff(xdata_0)
                        else:
                            xdata, ydata = xdata_0, ydata_0

                    # screen coordinates
                    search_x = np.log10(np.maximum(xdata, 1e-15)) if x_log_mode else xdata
                    search_y = np.log10(np.maximum(ydata, 1e-15)) if y_log_mode else ydata

                    # normalization
                    view_range = vb.viewRange() # [[xmin, xmax], [ymin, ymax]]
                    sx = view_range[0][1] - view_range[0][0]
                    sy = view_range[1][1] - view_range[1][0]
                    sx = sx if sx > 0 else 1
                    sy = sy if sy > 0 else 1

                    dist_sq = ((search_x - v_x) / sx)**2 + ((search_y - v_y) / sy)**2
                    
                    if not self.parametric:
                        real_view_x = 10**v_x if x_log_mode else v_x
                        idx_near = np.searchsorted(xdata, real_view_x)
                        idx_near = np.clip(idx_near, 0, len(xdata)-1)
                        
                        # only closest 100 points
                        i_start = max(0, idx_near - 50)
                        i_end = min(len(xdata), idx_near + 50)
                        
                        sub_dist = dist_sq[i_start:i_end]
                        local_idx = np.argmin(sub_dist)
                        index = i_start + local_idx
                    else:
                        index = np.argmin(dist_sq)

                    best_guesses.append({
                        'point': (xdata[index], ydata[index]),
                        'dist': dist_sq[index],
                        'item': data_item  # plot
                    })

            if not best_guesses:
                self.cursor_label.hide()
                return

            # best point            
            best_res = min(best_guesses, key=lambda x: x['dist'])
            (pt_x, pt_y) = best_res['point']
            target_item = best_res['item']

            #border color
            raw_pen = target_item.opts.get('pen')

            if isinstance(raw_pen, tuple):
                raw_pen = raw_pen[0]

            if hasattr(raw_pen, 'color'):
                curve_color = raw_pen.color()
            else:
                curve_color = pg.mkColor(raw_pen)

            self.cursor_label.border = pg.mkPen(curve_color, width=1.5)
            #border color

            label_text = f"X: {pt_x:.4g}\nY: {pt_y:.4g}"
            self.cursor_label.setText(label_text)
            
            # log_mode - log coordinates
            v_pos = math.log10(max(pt_x, 1e-15)) if x_log_mode else pt_x
            h_pos = math.log10(max(pt_y, 1e-15)) if y_log_mode else pt_y
            
            #label
            view_range = vb.viewRange()
            x_min, x_max = view_range[0]
            y_min, y_max = view_range[1]

            anchor_x = 1 if v_pos > (x_max + x_min) / 2 else 0
            anchor_y = 0 if h_pos > (y_max + y_min) / 2 else 1

            self.cursor_label.setAnchor((anchor_x, anchor_y))
            self.cursor_label.setPos(v_pos, h_pos)
            self.cursor_label.show()

            self.v_line.setPos(v_pos)
            self.h_line.setPos(h_pos)

            #self.label.setText("x=%.3e, y=%.3e" % (pt_x, pt_y))
            self.label2.setText("cur_x=%.4e, cur_y=%.4e" % (v_x, v_y))

    def add_cross_hair(self, x, y):
        if hasattr(self, 'v_line'):
            self.h_line.show()
            self.v_line.show()
            self.cursor_label.show()
        else:
            self.h_line = pg.InfiniteLine(pos=y,angle=0, movable=False)
            self.v_line = pg.InfiniteLine(pos=x, angle=90, movable=False)
            self.addItem(self.h_line, ignoreBounds=False)
            self.addItem(self.v_line, ignoreBounds=False)

        #if self.label is None:
        #    self.label = pg.LabelItem(justify="right")
        #    self.getPlotItem().layout.addItem(self.label, 4, 1)
        if self.label2 is None:
            self.label2 = pg.LabelItem(justify="left")
            self.getPlotItem().layout.addItem(self.label2, 4, 1)
        self.x_cross_index = 0
        self.y_cross_index = 0
        self.cross_section_enabled = True

        self.search_mode = True
        self.click_count_1d = 0
        
        # if cross-hair removing / adding again when from cross-section
        if self.cross_section == 1:
            self.image_operation = 0
            self.click_count_1d = 0
            self.click_count = 1
            # keep type:
            #if self.image_operation == 1:
            #    self.search_mode = False
            #    self.click_count_1d = 1
            #    self.click_count = 1
            #else:
            #    self.click_count_1d = 0
            #    self.click_count = 1

    def add_cross_hair_zero(self):
        if hasattr(self, 'v_line'):
            self.h_line.show()
            self.v_line.show()
            self.cursor_label.show()
        else:
            self.h_line = pg.InfiniteLine(angle=0, movable=False)
            self.v_line = pg.InfiniteLine(angle=90, movable=False)
            self.addItem(self.h_line, ignoreBounds=False)
            self.addItem(self.v_line, ignoreBounds=False)
        #if self.label is None:
        #    self.label = pg.LabelItem(justify="right")
        #    self.getPlotItem().layout.addItem(self.label, 4, 1)
        if self.label2 is None:
            self.label2 = pg.LabelItem(justify="left")
            self.getPlotItem().layout.addItem(self.label2, 4, 1)
        self.x_cross_index = 0
        self.y_cross_index = 0
        self.cross_section_enabled = True

    def hide_cross_hair(self, *enabled):
        try:
            self.cursor_label.hide()
            self.h_line.hide()
            self.v_line.hide()
            #self.removeItem(self.h_line)
            #self.removeItem(self.v_line)
        except AttributeError:
            pass
        self.cross_section_enabled = False
        if self.cross_section == 1 and self.search_mode == True:
            self.click_count = (self.click_count + 1 ) % 2
        if len(enabled) != 0:
            self.click_count_1d ^= 1

    def _fourierTransform(self, x, y):
        # Perform Fourier transform. If x values are not sampled uniformly,
        # then use np.interp to resample before taking fft.
        if len(x) == 1: 
            return np.array([0]), abs(y)
        dx = np.diff(x)
        uniform = not np.any(np.abs(dx - dx[0]) > (abs(dx[0]) / 1000.))
        if not uniform:
            x2 = np.linspace(x[0], x[-1], len(x))
            y = np.interp(x2, x, y)
            x = x2
        n = y.size
        f = np.fft.rfft(y) / n
        d = float(x[-1] - x[0]) / (len(x) - 1)
        x = np.fft.rfftfreq(n, d)
        y = np.abs(f)
        return x, y

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
        #plot_item.scene().contextMenu = None 

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

        #remove cross-hair
        self.closeClicked.connect(self.hide_cross_hair)

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
        open_action.triggered.connect(self.file_dialog)
        self.menu.addAction(open_action)

        self.avail_colors = [pg.mkPen(color=(47,79,79),width=1), pg.mkPen(color=(255,153,0),width=1), pg.mkPen(color=(255,0,255),width=1), pg.mkPen(color=(0,0,255),width=1), pg.mkPen(color=(0,0,0),width=1), pg.mkPen(color=(255,0,0),width=1), pg.mkPen(color=(95,158,160),width=1), pg.mkPen(color=(0,128,0),width=1), pg.mkPen(color=(255,255,0),width=1), pg.mkPen(color=(255,255,255),width=1)]
        self.avail_symbols= ['x','p','star','s','o','+']
        self.avail_sym_pens = [ pg.mkPen(color=(0, 0, 0), width=0), pg.mkPen(color=(255, 255, 255), width=0), pg.mkPen(color=(0, 255, 0), width=0), pg.mkPen(color=(0, 0, 255), width=0),pg.mkPen(color=(255, 0, 0), width=0),pg.mkPen(color=(255, 0, 255), width=0)]
        self.avail_sym_brush = [pg.mkBrush(0, 0, 0, 255), pg.mkBrush(255, 255, 255, 255),pg.mkBrush(0, 255, 0, 255),pg.mkBrush(0, 0, 255, 255), pg.mkBrush(255, 0, 0, 255),pg.mkBrush(255, 0, 255, 255)]

        self.white_pen = pg.mkPen(color=(255, 255, 255), width=1)
        self.yellow_pen = pg.mkPen(color=(255, 255, 0), width=1)

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

        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.ctrl.fftCheck.toggled.connect(self.on_fft_toggled)

    def hide_cross_hair(self):
        self.plot_widget.hide_cross_hair()

    def on_fft_toggled(self, enabled):
        if enabled:
            self.plot_item.setLabel('bottom', 'Frequency', units = 'Hz')
        else:
            try:
                self.plot_item.setLabel('bottom', self.bottom_axis_text, units = self.bottom_axis_units)
            except AttributeError:
                pass

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
                kwargs['pen'] = None        
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
                                try:
                                    kwargs['pen'] = self.used_colors[name] = self.avail_colors.pop()
                                except IndexError:
                                    kwargs['pen'] = self.used_colors[name] = self.white_pen
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
                kwargs['pen'] = None
                try:
                    kwargs['symbol'] = self.used_symbols[name] = self.avail_symbols.pop()
                    kwargs['symbolPen'] = self.used_pens[name] = self.avail_sym_pens.pop()
                    kwargs['symbolBrush'] = self.used_brush[name] = self.avail_sym_brush.pop()
                except IndexError:
                    kwargs['symbol'] = self.used_symbols[name] = '+'
                    kwargs['symbolPen'] = self.used_pens[name] = pg.mkPen(color=(255, 255, 255), width=0)
                    kwargs['symbolBrush'] = self.used_brush[name] = pg.mkBrush(255, 255, 255, 255)                    
                kwargs['symbolSize'] = 7
                self.curves[name] = self.plot_widget.plot(*args, **kwargs)
            elif kwargs.get('scatter', '') == 'False':
                if len( np.shape(args[0]) ) > 1:
                    # simultaneous plot of two curves
                    for i in range( len( args[0] )):
                        if i == 0:
                            try:
                                kwargs['pen'] = self.used_colors[name] = self.avail_colors.pop()
                            except IndexError:
                                kwargs['pen'] = self.used_colors[name] = self.white_pen
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
                                try:
                                    kwargs['pen'] = self.used_colors[name] = self.avail_colors.pop()
                                except IndexError:
                                    kwargs['pen'] = self.used_colors[name] = self.yellow_pen
                                args_mod = (args[0][i], args[1][i])
                                # the second curve is a new one
                                self.curves[name] = self.plot_widget.plot(*args_mod, **kwargs)
                                # Text label above the graph
                                temp = kwargs.get('text', '')
                                if temp != '':
                                    self.setTitle( temp )

                else:
                    try:
                        kwargs['pen'] = self.used_colors[name] = self.avail_colors.pop()
                    except IndexError:
                        kwargs['pen'] = self.used_colors[name] = self.white_pen
                    self.curves[name] = self.plot_widget.plot(*args, **kwargs)
                    # Text label above the graph
                    temp = kwargs.get('text', '')
                    if temp != '':
                        self.setTitle( temp )
                    
                # vertical lines
                if vline_arg != 'False':
                    try:
                        self.vl1 = self.plot_widget.addLine( x = float(vline_arg[0]) )
                        self.vl2 = self.plot_widget.addLine( x = float(vline_arg[1]) )
                    except IndexError:
                        pass
            
            if self.qaction_added == 0:
                del_action_2 = QtGui.QAction(str(name), self)
                shifter_2 = QtWidgets.QDoubleSpinBox()
                shiftAction_2 = QtWidgets.QWidgetAction(self)
                self.add_del_shift_actions(name, del_action_2, shifter_2, shiftAction_2)

        item = self.plot_widget.getPlotItem()
        plot_data_item = next((i for i in item.items if isinstance(i, pg.PlotDataItem)), None)
        fft_state = plot_data_item.opts.get('fftMode', False)
        #fft_state = item.items[0].opts['fftMode']
        self.on_fft_toggled( fft_state )

        if not fft_state:
            self.bottom_axis_text = self.plot_widget.getAxis('bottom').labelText
            self.bottom_axis_units = self.plot_widget.getAxis('bottom').labelUnits

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

    def file_dialog(self, directory = ''):
        """
        A function to open a new window for choosing 1d data
        """
        filedialog = QtWidgets.QFileDialog(self, 'Open File', directory = self.open_dir, filter = "CSV (*.csv)",  options = QtWidgets.QFileDialog.Option.DontUseNativeDialog ) 
        filedialog.resize(800, 450) 
        # use QFileDialog.Option.DontUseNativeDialog to change directory
        filedialog.setIconProvider(QtWidgets.QFileIconProvider())
        line_edit = filedialog.findChild(QtWidgets.QLineEdit)

        tree = filedialog.findChild(QtWidgets.QTreeView)
        header = tree.header()
        for i in range(header.count()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)

        buttons = filedialog.findChildren(QtWidgets.QPushButton)
        seen_texts = []
        for btn in buttons:
            if btn.text() in seen_texts:
                btn.hide()
            else:
                seen_texts.append(btn.text())
    
        if line_edit:
            line_edit.setCompleter(None)

        size_grip = filedialog.findChild(QtWidgets.QSizeGrip)
        if size_grip:
            size_grip.setVisible(False)

        filedialog.setStyleSheet("""
            QFileDialog, QDialog { 
                background-color: rgb(42, 42, 64); 
                color: rgb(193, 202, 227);
                font-size: 11px;
            }

            QFileDialog QListView {
                min-width: 150px; 
                background-color: rgb(35, 35, 55);
                border: 1px solid rgb(63, 63, 97);
                color: rgb(193, 202, 227);
            }

            QTreeView {
                min-width: 500px;
                background-color: rgb(35, 35, 55);
                border: 1px solid rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                outline: none;
            }

            QFileDialog QFrame#qt_contents, QFileDialog QWidget {
                background-color: rgb(42, 42, 64);
            }
            
            QFileDialog QToolBar {
                background-color: rgb(42, 42, 64);
                border-bottom: 1px solid rgb(63, 63, 97);
                min-height: 34px; 
                padding: 2px;
            }

            QToolButton {
                background-color: rgb(63, 63, 97);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 4px;
                min-height: 23px; 
                max-height: 23px;
                min-width: 23px;
                qproperty-iconSize: 14px 14px; 
                margin: 0px 2px;
                vertical-align: middle;
            }

            QToolButton:hover {
                border: 1px solid rgb(211, 194, 78);
                background-color: rgb(83, 83, 117);
            }

            QLineEdit, QComboBox {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 3px;
                padding: 2px 5px;
                min-height: 16px; 
            }

            QLineEdit:focus, QFileDialog QComboBox:focus {
                border: 1px solid rgb(211, 194, 78);
                color: rgb(211, 194, 78);
                outline: none;
            }

            QFileDialog QComboBox#lookInCombo {
                background-color: rgb(42, 42, 64);
                color: rgb(193, 202, 227);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 3px;
                padding-left: 5px;
                min-height: 19px;
                max-height: 19px;
                selection-background-color: rgb(48, 48, 75);
                selection-color: rgb(211, 194, 78);
            }

            QFileDialog QComboBox#lookInCombo QAbstractItemView {
                outline: none;
                border: 1px solid rgb(48, 48, 75);
                background-color: rgb(42, 42, 64);
            }

            QFileDialog QDialogButtonBox QPushButton {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 4px;
                font-weight: bold;
                min-height: 23px;
                max-height: 23px;
                min-width: 75px;
                padding: 0px 12px;
            }

            QFileDialog QDialogButtonBox QPushButton:hover {
                background-color: rgb(83, 83, 117);
                border: 1px solid rgb(211, 194, 78);
                color: rgb(211, 194, 78);
            }
            
            QHeaderView::section {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                padding: 4px;
                border: none;
                border-right: 1px solid rgb(83, 83, 117);
                min-height: 20px;
            }

            QScrollBar:vertical {
                border: none; background: rgb(43, 43, 77); 
                width: 10px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgb(193, 202, 227); min-height: 20px; border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover { background: rgb(211, 194, 78); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

            QScrollBar:horizontal {
                border: none; 
                background: rgb(43, 43, 77); 
                height: 10px; 
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgb(193, 202, 227); 
                min-width: 20px; 
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover { 
                background: rgb(211, 194, 78); 
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { 
                width: 0px; 
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { 
                background: none; 
            }

            QFileDialog QDialogButtonBox {
                background-color: rgb(42, 42, 64);
                border-top: 1px solid rgb(63, 63, 97);
                padding: 6px;
            }

            QFileDialog QLabel {
                color: rgb(193, 202, 227);
            }

            QFileDialog QListView::item:hover {
                background-color: rgb(48, 48, 75);
                color: rgb(211, 194, 78);
            }

            QHeaderView {
                background-color: rgb(63, 63, 97);
            }

            QFileDialog QListView#sidebar:inactive, 
            QTreeView:inactive {
                selection-background-color: rgb(35, 35, 55);
                selection-color: rgb(211, 194, 78);
            }

            QTreeView::item:hover { 
                background-color: rgb(48, 48, 75);
                color: rgb(211, 194, 78); 
                } 
            QTreeView::item:selected:inactive, 
            QFileDialog QListView#sidebar::item:selected:inactive {
                selection-background-color: rgb(63, 63, 97);
                selection-color: rgb(211, 194, 78);
            }
            QFileDialog QListView#sidebar::item {
                padding-left: 5px; 
                padding-top: 5px;
            }

            QMenu {
                background-color: rgb(42, 42, 64);
                border: 1px solid rgb(63, 63, 97);
                padding: 3px;
            }
            QMenu::item { color: rgb(211, 194, 78); } 
            QMenu::item:selected { 
                background-color: rgb(48, 48, 75); 
                color: rgb(211, 194, 78);
                }

        """)


        filedialog.setFileMode(QtWidgets.QFileDialog.FileMode.AnyFile)
        filedialog.fileSelected.connect(self.open_file)
        filedialog.show()

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
        self.img_view.scene.sigMouseClicked.connect(self.on_scene_clicked)

        # Define positions and corresponding colors
        pos = np.array([0.0, 0.5, 1.0])
        color = np.array([
            [0, 0, 255, 255],       # Blue
            [255, 255, 255, 255],   # White
            [255, 0, 0, 255]        # Red
        ], dtype = np.ubyte)
        cmap = pg.ColorMap(pos, color)

        # plot options menu
        #self.plot_item.getViewBox().menu.setStyleSheet("QMenu::item:selected {background-color: rgb(40, 40, 40); } QMenu::item { color: rgb(211, 194, 78); } QMenu {background-color: rgb(42, 42, 64); }")
        #self.plot_item.ctrlMenu.setStyleSheet("QMenu::item:selected {background-color: rgb(40, 40, 40); } QMenu::item { color: rgb(211, 194, 78); } QMenu {background-color: rgb(42, 42, 64); }")
        self.auto_levels = 0
        self.set_image = 0
        self.click_count = 1
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
        self.ui.histogram.gradient.setColorMap(cmap) #loadPreset('bipolar')

        try:
            self.connect_signal()
        except RuntimeError:
            warnings.warn('Scene not set up, cross section signals not connected')

        self.y_cross_index = 0
        self.h_cross_section_widget = CrosshairPlotWidget()
        self.h_cross_section_widget.cross_section = 1
        self.h_cross_section_widget.image_operation = 1
        self.h_cross_dock = CloseableDock(name='X trace', widget=self.h_cross_section_widget, area=self.area)
        # for removing / adding cross-hair again
        self.h_cross_dock.closeClicked.connect(self.hide_cross_hair_h)

        #self.h_cross_section_widget.add_cross_hair_zero()
        self.h_cross_section_widget.search_mode = False
        self.h_cross_section_widget_data = self.h_cross_section_widget.plot([0,0])

        self.x_cross_index = 0
        self.v_cross_section_widget = CrosshairPlotWidget()
        self.v_cross_section_widget.cross_section = 1
        self.v_cross_section_widget.image_operation = 1
        self.v_cross_dock = CloseableDock(name='Y trace', widget=self.v_cross_section_widget, area=self.area)
        self.v_cross_dock.closeClicked.connect(self.hide_cross_hair_v)

        #self.v_cross_section_widget.add_cross_hair_zero()
        self.v_cross_section_widget.search_mode = False
        self.v_cross_section_widget_data = self.v_cross_section_widget.plot([0,0])

        # label
        self.cursor_label = pg.TextItem(anchor=(0, 1), color='w', fill=(42, 42, 64, 150))
        self.cursor_label.hide()
        # top-level
        self.cursor_label.setZValue(100)
        self.plot_item.addItem(self.cursor_label)

    def hide_cross_hair_v(self):
        self.v_cross_section_widget.cross_section = 1
        self.v_cross_section_widget.image_operation = 1
        self.v_cross_section_widget.click_count_1d = 0

    def hide_cross_hair_h(self):
        self.h_cross_section_widget.cross_section = 1
        self.h_cross_section_widget.image_operation = 1
        self.h_cross_section_widget.click_count_1d = 0

    def close(self):
        self.setParent(None)
        self.closed = True
        if hasattr(self, '_container'):
            if self._container is not self.area.topContainer:
                self._container.apoptose()

        self.h_cross_section_widget.image_operation = 1
        self.v_cross_section_widget.image_operation = 1
        self.v_cross_section_widget.click_count_1d = 0
        self.h_cross_section_widget.click_count_1d = 0
        self.click_count = 1
        super().close()

    def setLabels(self, xlabel = "X", ylabel = "Y", zlabel = "Z"):
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

        self.h_cross_section_widget.axis = [kwargs.get('xname', ''), kwargs.get('xscale', '')] 
        self.v_cross_section_widget.axis = [kwargs.get('yname', ''), kwargs.get('yscale', '')] 

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

        if self.set_image != 0:
            if self._x0_prev != self._x0 or self._y0_prev != self._y0 or self._xscale_prev != self._xscale or self._yscale_prev != self._yscale:
                self.hide_cross_section()

        self._x0_prev = self._x0
        self._y0_prev = self._y0
        self._xscale_prev = self._xscale
        self._yscale_prev = self._yscale

        autorange = self.img_view.getView().vb.autoRangeEnabled()[0]
        kwargs['autoRange'] = autorange

        if self.auto_levels == 0:
            kwargs['autoLevels'] = True
        else:
            kwargs['autoLevels'] = False
        self.auto_levels = 0

        self.img_view.setImage(*args, **kwargs )
        self.img_view.getView().vb.enableAutoRange(enable = autorange)
        #self.update_cross_section()
        self.set_image = 1

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
        self.fileDialog = QtWidgets.QFileDialog(self, 'Save File', options = QtWidgets.QFileDialog.Option.DontUseNativeDialog)
        self.fileDialog.resize(800, 450) 
        # use QFileDialog.Option.DontUseNativeDialog to change directory
        self.fileDialog.setIconProvider(QtWidgets.QFileIconProvider())
        line_edit = self.fileDialog.findChild(QtWidgets.QLineEdit)

        tree = self.fileDialog.findChild(QtWidgets.QTreeView)
        header = tree.header()
        for i in range(header.count()):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        
        buttons = self.fileDialog.findChildren(QtWidgets.QPushButton)
        seen_texts = []
        for btn in buttons:
            if btn.text() in seen_texts:
                btn.hide()
            else:
                seen_texts.append(btn.text())
    
        if line_edit:
            line_edit.setCompleter(None)
        
        size_grip = self.fileDialog.findChild(QtWidgets.QSizeGrip)
        if size_grip:
            size_grip.setVisible(False)

        self.fileDialog.setStyleSheet("""
            QFileDialog, QDialog { 
                background-color: rgb(42, 42, 64); 
                color: rgb(193, 202, 227);
                font-size: 11px;
            }

            QFileDialog QListView {
                min-width: 150px; 
                background-color: rgb(35, 35, 55);
                border: 1px solid rgb(63, 63, 97);
                color: rgb(193, 202, 227);
            }

            QTreeView {
                min-width: 500px;
                background-color: rgb(35, 35, 55);
                border: 1px solid rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                outline: none;
            }

            QFileDialog QFrame#qt_contents, QFileDialog QWidget {
                background-color: rgb(42, 42, 64);
            }
            
            QFileDialog QToolBar {
                background-color: rgb(42, 42, 64);
                border-bottom: 1px solid rgb(63, 63, 97);
                min-height: 34px; 
                padding: 2px;
            }

            QToolButton {
                background-color: rgb(63, 63, 97);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 4px;
                min-height: 23px; 
                max-height: 23px;
                min-width: 23px;
                qproperty-iconSize: 14px 14px; 
                margin: 0px 2px;
                vertical-align: middle;
            }

            QToolButton:hover {
                border: 1px solid rgb(211, 194, 78);
                background-color: rgb(83, 83, 117);
            }

            QLineEdit, QComboBox {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 3px;
                padding: 2px 5px;
                min-height: 16px; 
            }

            QLineEdit:focus, QFileDialog QComboBox:focus {
                border: 1px solid rgb(211, 194, 78);
                color: rgb(211, 194, 78);
                outline: none;
            }

            QFileDialog QComboBox#lookInCombo {
                background-color: rgb(42, 42, 64);
                color: rgb(193, 202, 227);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 3px;
                padding-left: 5px;
                min-height: 19px;
                max-height: 19px;
                selection-background-color: rgb(48, 48, 75);
                selection-color: rgb(211, 194, 78);
            }

            QFileDialog QComboBox#lookInCombo QAbstractItemView {
                outline: none;
                border: 1px solid rgb(48, 48, 75);
                background-color: rgb(42, 42, 64);
            }

            QFileDialog QDialogButtonBox QPushButton {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                border: 1px solid rgb(83, 83, 117);
                border-radius: 4px;
                font-weight: bold;
                min-height: 23px;
                max-height: 23px;
                min-width: 75px;
                padding: 0px 12px;
            }

            QFileDialog QDialogButtonBox QPushButton:hover {
                background-color: rgb(83, 83, 117);
                border: 1px solid rgb(211, 194, 78);
                color: rgb(211, 194, 78);
            }
            
            QHeaderView::section {
                background-color: rgb(63, 63, 97);
                color: rgb(193, 202, 227);
                padding: 4px;
                border: none;
                border-right: 1px solid rgb(83, 83, 117);
                min-height: 20px;
            }

            QScrollBar:vertical {
                border: none; background: rgb(43, 43, 77); 
                width: 10px; margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgb(193, 202, 227); min-height: 20px; border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover { background: rgb(211, 194, 78); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

            QScrollBar:horizontal {
                border: none; 
                background: rgb(43, 43, 77); 
                height: 10px; 
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: rgb(193, 202, 227); 
                min-width: 20px; 
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover { 
                background: rgb(211, 194, 78); 
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { 
                width: 0px; 
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { 
                background: none; 
            }

            QFileDialog QDialogButtonBox {
                background-color: rgb(42, 42, 64);
                border-top: 1px solid rgb(63, 63, 97);
                padding: 6px;
            }

            QFileDialog QLabel {
                color: rgb(193, 202, 227);
            }

            QFileDialog QListView::item:hover {
                background-color: rgb(48, 48, 75);
                color: rgb(211, 194, 78);
            }

            QHeaderView {
                background-color: rgb(63, 63, 97);
            }

            QFileDialog QListView#sidebar:inactive, 
            QTreeView:inactive {
                selection-background-color: rgb(35, 35, 55);
                selection-color: rgb(211, 194, 78);
            }

            QTreeView::item:hover { 
                background-color: rgb(48, 48, 75);
                color: rgb(211, 194, 78); 
                } 
            QTreeView::item:selected:inactive, 
            QFileDialog QListView#sidebar::item:selected:inactive {
                selection-background-color: rgb(63, 63, 97);
                selection-color: rgb(211, 194, 78);
            }
            QFileDialog QListView#sidebar::item {
                padding-left: 5px; 
                padding-top: 5px;
            }

            QMenu {
                background-color: rgb(42, 42, 64);
                border: 1px solid rgb(63, 63, 97);
                padding: 3px;
            }
            QMenu::item { color: rgb(211, 194, 78); } 
            QMenu::item:selected { 
                background-color: rgb(48, 48, 75); 
                color: rgb(211, 194, 78);
                }

        """)


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

        self.h_cross_section_widget.add_cross_hair_zero()
        self.v_cross_section_widget.add_cross_hair_zero()
        #self.text_item = pg.LabelItem(justify="right")
        #self.img_view.ui.gridLayout.addWidget(self.text_item, 2, 1, 1, 2)
        #self.img_view.ui.graphicsView.addItem(self.text_item)#, 2, 1)
        #self.plot_item.layout.addItem(self.text_item, 4, 1)
        #self.cs_layout.addItem(self.label, 2, 1) #TODO: Find a way of displaying this label
        self.search_mode = True
        self.click_count = 1

        self.area.addDock(self.h_cross_dock)
        self.area.addDock(self.v_cross_dock, position='right', relativeTo=self.h_cross_dock)
        self.cross_section_enabled = True

        self.cursor_label.setPos(mid_x, mid_y)
        self.cursor_label.show()

        self.cursor_label.border = pg.mkPen((255, 255, 0, 255), width=1.5)
        label_text = f"X: {mid_x:.4g}\nY: {mid_y:.4g}\nZ: {0}"
        self.cursor_label.setText(label_text)

    def hide_cross_section(self):
        if self.cross_section_enabled:
            self.plot_item.removeItem(self.h_line)
            self.plot_item.removeItem(self.v_line)
            #self.img_view.ui.graphicsView.removeItem(self.text_item)
            self.cross_section_enabled = False
            self.h_cross_dock.close()
            self.v_cross_dock.close()
            self.cursor_label.hide()

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

    def on_scene_clicked(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.MiddleButton:
            if self.cross_section_enabled:
                self.v_cross_section_widget.click_count_1d ^= 1
                self.h_cross_section_widget.click_count_1d ^= 1
                self.click_count = (self.click_count + 1) % 2
                self.search_mode = not self.search_mode
                
                color = (255, 255, 0, 255) if self.click_count != 0 else (128, 128, 128, 255)
                self.cursor_label.border = pg.mkPen(color, width=1.5)
                self.cursor_label.update()
                
                pos = ev.scenePos()
                self.handle_mouse_move(pos)
                
                ev.accept()

        #super().mousePressEvent(ev)

    def toggle_search(self, mouse_event):
        if mouse_event.double():
            self.toggle_cross_section()
        elif self.cross_section_enabled:
            # See mousePressEvent
            #if mouse_event.button() == QtCore.Qt.MouseButton.MiddleButton:
            #    self.click_count = (self.click_count + 1 ) % 2
            #    self.search_mode = not self.search_mode
            #    if self.click_count == 0:
            #        self.cursor_label.border = pg.mkPen((128,128,128,255), width=1.5)
            #    else:
            #        self.cursor_label.border = pg.mkPen((255,255,0,255), width=1.5)
            #    self.cursor_label.update()
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
            #self.text_item.setText("x=%.3e, y=%.3e, z=%.3e" % (view_x, view_y, z_val))

            #label
            view_range = self.imageItem.getViewBox().viewRange()
            x_min, x_max = view_range[0]
            y_min, y_max = view_range[1]

            anchor_x = 1 if view_x > (x_max + x_min) / 2 else 0
            anchor_y = 0 if view_y > (y_max + y_min) / 2 else 1

            self.cursor_label.setAnchor((anchor_x, anchor_y))            
            self.cursor_label.setPos(view_x, view_y)
            self.cursor_label.show()

            label_text = f"X: {view_x:.4g}\nY: {view_y:.4g}\nZ: {z_val:.4g}"
            self.cursor_label.setText(label_text)

    def update_cross_section(self):
        nx, ny = self.imageItem.image.shape
        x0, y0, xscale, yscale = self._x0, self._y0, self._xscale, self._yscale
        xdata = np.linspace(x0, x0+(xscale*(nx-1)), nx)
        ydata = np.linspace(y0, y0+(yscale*(ny-1)), ny)
        zval = self.imageItem.image[self.x_cross_index, self.y_cross_index]
        self.h_cross_section_widget_data.setData(xdata, self.imageItem.image[:, self.y_cross_index])
        self.v_cross_section_widget_data.setData(ydata, self.imageItem.image[self.x_cross_index, :])

        if self.v_cross_section_widget.image_operation == 1:
            item = self.v_cross_section_widget.getPlotItem()
            plot_data_item = next((i for i in item.items if isinstance(i, pg.PlotDataItem)), None)
            vb = item.getViewBox()

            self.v_cross_section_widget.cursor_label.border = pg.mkPen((128, 128, 128, 255), width=1.5)

            try:
                if plot_data_item.opts['logMode'][0] == True:
                    y = np.log10( ydata[self.y_cross_index] )
                    z = zval
                elif plot_data_item.opts['logMode'][1] == True:
                    y = ydata[self.y_cross_index]
                    z = np.log10( zval )
                elif (plot_data_item.opts['logMode'][0]) == True and (plot_data_item.opts['logMode'][1]) == True:
                    y = ydata[self.y_cross_index]
                    z = np.log10( zval )
                elif (plot_data_item.opts['fftMode'] == True) or (plot_data_item.opts['derivativeMode'] == True) or (plot_data_item.opts['phasemapMode'] == True) or (plot_data_item.opts['subtractMeanMode'] == True):
                    self.v_cross_section_widget.image_operation = 0
                    y = ydata[self.y_cross_index]
                    z = zval
                    self.v_cross_section_widget.cursor_label.border = pg.mkPen((255, 255, 0, 255), width=1.5)
                else:
                    y = ydata[self.y_cross_index]
                    z = zval
            except KeyError:
                if plot_data_item.opts['logMode'][0] == True:
                    y = np.log10( ydata[self.y_cross_index] )
                    z = zval
                elif plot_data_item.opts['logMode'][1] == True:
                    y = ydata[self.y_cross_index]
                    z = np.log10( zval )
                elif (plot_data_item.opts['logMode'][0]) == True and (plot_data_item.opts['logMode'][1]) == True:
                    y = ydata[self.y_cross_index]
                    z = np.log10( zval )
                elif (plot_data_item.opts['fftMode'] == True) or (plot_data_item.opts['derivativeMode'] == True) or (plot_data_item.opts['phasemapMode'] == True):
                    self.v_cross_section_widget.image_operation = 0
                    y = ydata[self.y_cross_index]
                    z = zval
                    self.v_cross_section_widget.cursor_label.border = pg.mkPen((255, 255, 0, 255), width=1.5)
                else:
                    y = ydata[self.y_cross_index]
                    z = zval

            view_range = vb.viewRange()
            x_min, x_max = view_range[0]
            y_min, y_max = view_range[1]

            anchor_x = 1 if y > (x_max + x_min) / 2 else 0
            anchor_y = 0 if z > (y_max + y_min) / 2 else 1

            self.v_cross_section_widget.cursor_label.setAnchor((anchor_x, anchor_y))

            self.v_cross_section_widget.v_line.setPos(y)
            self.v_cross_section_widget.h_line.setPos(z)

            self.v_cross_section_widget.cursor_label.setPos(y, z)

            if (self.v_cross_section_widget.v_line.isVisible() == False) or (self.v_cross_section_widget.h_line.isVisible() == False):
                pass
            else:
                self.v_cross_section_widget.cursor_label.show()

            label_text = f"Y: {ydata[self.y_cross_index]:.4g}\nZ: {zval:.4g}"
            self.v_cross_section_widget.cursor_label.setText(label_text)

        if self.h_cross_section_widget.image_operation == 1:
            item = self.h_cross_section_widget.getPlotItem()
            plot_data_item = next((i for i in item.items if isinstance(i, pg.PlotDataItem)), None)
            vb = item.getViewBox()

            self.h_cross_section_widget.cursor_label.border = pg.mkPen((128, 128, 128, 255), width=1.5)

            try:
                if plot_data_item.opts['logMode'][0] == True:
                    x = np.log10( xdata[self.x_cross_index] )
                    z = zval
                elif plot_data_item.opts['logMode'][1] == True:
                    x = xdata[self.x_cross_index]
                    z = np.log10( zval )
                elif (plot_data_item.opts['logMode'][0]) == True and (plot_data_item.opts['logMode'][1]) == True:
                    x = xdata[self.x_cross_index]
                    z = np.log10( zval )
                elif (plot_data_item.opts['fftMode'] == True) or (plot_data_item.opts['derivativeMode'] == True) or (plot_data_item.opts['phasemapMode'] == True) or (plot_data_item.opts['subtractMeanMode'] == True):
                    self.h_cross_section_widget.image_operation = 0
                    x = xdata[self.x_cross_index]
                    z = zval
                    self.h_cross_section_widget.cursor_label.border = pg.mkPen((255, 255, 0, 255), width=1.5)
                else:
                    x = xdata[self.x_cross_index]
                    z = zval
            except KeyError:
                if plot_data_item.opts['logMode'][0] == True:
                    x = np.log10( xdata[self.x_cross_index] )
                    z = zval
                elif plot_data_item.opts['logMode'][1] == True:
                    x = xdata[self.x_cross_index]
                    z = np.log10( zval )
                elif (plot_data_item.opts['logMode'][0]) == True and (plot_data_item.opts['logMode'][1]) == True:
                    x = xdata[self.x_cross_index]
                    z = np.log10( zval )
                elif (plot_data_item.opts['fftMode'] == True) or (plot_data_item.opts['derivativeMode'] == True) or (plot_data_item.opts['phasemapMode'] == True):
                    self.h_cross_section_widget.image_operation = 0
                    x = xdata[self.x_cross_index]
                    z = zval
                    self.h_cross_section_widget.cursor_label.border = pg.mkPen((255, 255, 0, 255), width=1.5)
                else:
                    x = xdata[self.x_cross_index]
                    z = zval

            view_range = vb.viewRange()
            x_min, x_max = view_range[0]
            y_min, y_max = view_range[1]

            anchor_x = 1 if x > (x_max + x_min) / 2 else 0
            anchor_y = 0 if z > (y_max + y_min) / 2 else 1

            self.h_cross_section_widget.cursor_label.setAnchor((anchor_x, anchor_y))
            
            self.h_cross_section_widget.v_line.setPos(x)
            self.h_cross_section_widget.h_line.setPos(z)

            self.h_cross_section_widget.cursor_label.setPos(x, z)

            if (self.h_cross_section_widget.v_line.isVisible() == False) or (self.h_cross_section_widget.h_line.isVisible() == False):
                pass
            else:
                self.h_cross_section_widget.cursor_label.show()

            label_text = f"X: {xdata[self.x_cross_index]:.4g}\nZ: {zval:.4g}"
            self.h_cross_section_widget.cursor_label.setText(label_text)
