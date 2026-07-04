import warnings
import os
import colorsys
import configparser
import pyqtgraph as pg
import numpy as np
import math
from datetime import datetime
from pathlib import Path
from pyqtgraph.dockarea import Dock
from PyQt6 import QtWidgets, QtCore, QtGui, sip
import atomize.main.local_config as lconf
import atomize.general_modules.last_dir as ldir

pg.setConfigOption('background', (63,63,97))
pg.setConfigOption('leftButtonPan', False)
pg.setConfigOption('foreground', (192, 202, 227))
#pg.setConfigOptions(imageAxisOrder='row-major')

LastExportDirectory = None

# Bare SI base units pyqtgraph may auto-prefix in a cursor readout. An
# already-prefixed unit ('ns', 'MHz', 'mV') or a non-SI label is shown verbatim,
# so a value of 0.4 with unit 'ns' reads '0.4 ns', not the double-prefixed
# '400 mns' that siFormat() would emit. Mirrors data_treatment_2d.SI_BASE_UNITS.
SI_BASE_UNITS = {'s', 'hz', 'v', 'a', 'g', 't', 'k', 'm', 'ev'}

def si_cursor_label(value, unit, precision=5):
    """Format a cursor-readout value: let pyqtgraph SI-prefix only bare SI-base
    units; for already-prefixed or non-SI units, print the value verbatim with
    the unit appended to avoid a double prefix."""
    u = str(unit).strip()
    if u.lower() in SI_BASE_UNITS:
        return pg.siFormat(value, suffix=u, precision=precision)
    num = f"{value:.{precision}g}"
    return f"{num} {u}" if u else num

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
        # When True, the cross-hair may land between samples (on the nearest
        # point of the drawn polyline). Off by default: the cross-hair jumps
        # to the nearest actual data point (vertex) instead of sliding smoothly
        # along the curve.
        self.snap_to_segments = False
        #self.label = None
        self.label2 = None
        self.image_operation = 0
        self.click_count = 1
        self.click_count_1d = 0
        self.axis = ['', '']
        self.cross_section = 0

        self.plot_item = self.getPlotItem()

        # Render speed: only rasterise points inside the view (clip) and, when a
        # trace has more samples than the view is wide, draw a peak-preserving
        # decimation instead of every point. Display-only — .xData/.yData (raw)
        # are untouched, so the crosshair snap (reads xData/yData), the ruler and
        # every data export (get_raw_data) still see full resolution; append/
        # redraw were switched to get_raw_data so they never bake in the
        # decimation. 'peak' keeps min/max per bin so noise spikes don't vanish.
        # ~5x faster at 100k points, ~9x at 1M; no effect on small traces.
        self.plot_item.setClipToView(True)
        self.plot_item.setDownsampling(auto=True, mode='peak')

        self.plot_item.ctrl.fftCheck.toggled.connect(self.on_fft_toggled)
        self.plot_item.ctrl.logXCheck.toggled.connect( self.hide_cross_hair )
        self.plot_item.ctrl.logYCheck.toggled.connect( self.hide_cross_hair )
        self.plot_item.ctrl.derivativeCheck.toggled.connect( self.hide_cross_hair )
        self.plot_item.ctrl.phasemapCheck.toggled.connect( self.hide_cross_hair )
        try:
            self.plot_item.ctrl.subtractMeanCheck.toggled.connect( self.hide_cross_hair )
        except Exception:
            pass
        
        #self.plot_item.showGrid(x=True, y=True, alpha=0.1)

        self.hide_action = QtGui.QAction('Hide Label', self)
        self.hide_action.setCheckable(True)
        self.hide_action.setChecked(False)
        self.hide_action.triggered.connect(self.update_label_visibility)
        self.plot_item.vb.menu.addAction(self.hide_action)

        #(63,63,97)
        self.cursor_label = pg.TextItem(anchor=(0, 1), color='w', fill=(42, 42, 64, 150))
        self.cursor_label.border = pg.mkPen((255, 255, 255, 255), width=1.5)
        self.cursor_label.hide()
        # top-level
        self.cursor_label.setZValue(100)
        self.addItem(self.cursor_label)

        self.getViewBox().setLimits(maxYRange=1e30, minYRange=1e-30)

        # Ruler (Shift + left-drag) — state, items, and viewbox drag hook
        self._ruler_start_scene = None
        self._ruler_p1 = None
        self._ruler_p2 = None
        self._ruler_line = None
        self._ruler_marks = None
        self._ruler_label = None
        self._ruler_locked_item = None
        self._ruler_locked_color = None

        self.clear_ruler_action = QtGui.QAction('Clear Ruler', self)
        self.clear_ruler_action.triggered.connect(self._clear_ruler)
        self.plot_item.vb.menu.addAction(self.clear_ruler_action)

        self._install_ruler_drag()

    def plot(self, *args, **kwargs):
        """Create a curve and correct its auto-range bounds.

        With auto-downsampling on (above), a PlotDataItem's dataBounds are read
        from the *decimated* curve, so on log-spaced / multi-decade data the
        sparse extreme samples are dropped and the view auto-scales short of the
        true extent. Patch dataBounds to report the RAW data range for a plain
        full-range query (frac == 1, no ortho window), which is what ViewBox
        auto-scaling uses. FFT display (transformed X) falls back to the
        decimated bounds; log axes are handled by log-scaling the raw range."""
        item = self.plot_item.plot(*args, **kwargs)
        try:
            orig = item.dataBounds

            def _raw_bounds(ax, frac=1.0, orthoRange=None, _it=item, _orig=orig):
                if frac == 1.0 and orthoRange is None and not _it.opts.get('fftMode', False):
                    data = _it.xData if ax == 0 else _it.yData
                    if data is not None and len(data):
                        d = np.asarray(data, dtype=float)
                        if _it.opts.get('logMode', [False, False])[ax]:
                            d = d[d > 0]
                            if d.size:
                                d = np.log10(d)
                        else:
                            d = d[np.isfinite(d)]
                        if d.size:
                            return (float(np.min(d)), float(np.max(d)))
                return _orig(ax, frac, orthoRange)

            item.dataBounds = _raw_bounds
        except Exception:
            pass
        return item

    def on_fft_toggled(self, enabled):
        if enabled:
            self.hide_cross_hair()
            self.plot_item.setLabel('bottom', 'Frequency', units = 'Hz')
            self.x_units = 'Hz'
        else:
            try:
                self.hide_cross_hair()
                self.plot_item.setLabel('bottom', self.axis[0], units = self.axis[1])
                self.x_units = self.axis[1]
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
                # Immediately snap to the nearest curve at the double-click
                # position so the cross-hair lands on the data on first show.
                # Reuses the standard snap pipeline → works in FFT / log /
                # derivative / phasemap / subtractMean modes uniformly.
                self.handle_mouse_move(mouse_event.scenePos())

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
        if not (self.cross_section_enabled and self.search_mode):
            return

        res = self._snap_to_nearest_point(mouse_event)
        if res is None:
            self.cursor_label.hide()
            return

        v_pos = res['view_x']
        h_pos = res['view_y']

        self.cursor_label.border = pg.mkPen(res['color'], width=1.5)
        self.cursor_label.setText(f"X: {res['x_text']}\nY: {res['y_text']}")

        vb = self.getPlotItem().getViewBox()
        view_range = vb.viewRange()
        x_min, x_max = view_range[0]
        y_min, y_max = view_range[1]
        anchor_x = 1 if v_pos > (x_max + x_min) / 2 else 0
        anchor_y = 0 if h_pos > (y_max + y_min) / 2 else 1

        self.cursor_label.setAnchor((anchor_x, anchor_y))
        self.cursor_label.setPos(v_pos, h_pos)
        self.update_label_visibility()

        self.v_line.setPos(v_pos)
        self.h_line.setPos(h_pos)
        self.label2.setText("cur_x=%.4e, cur_y=%.4e" % (res['cur_view_x'], res['cur_view_y']))

    def _snap_to_nearest_point(self, scene_pos, restrict_to=None):
        """Find nearest data point across visible curves.

        Returns dict {view_x, view_y, x_text, y_text, color, item, cur_view_x, cur_view_y}
        in display coordinates (with siFormat labels), or None if no eligible curves.
        When `restrict_to` is a PlotDataItem, only that curve is searched (used by
        the ruler after the drag has locked onto a specific curve).
        """
        item = self.getPlotItem()
        vb = item.getViewBox()
        view_coords = vb.mapSceneToView(scene_pos)
        x_log_mode, y_log_mode = vb.state['logMode'][0], vb.state['logMode'][1]

        if not hasattr(self, 'y_units'):
            self.y_units = item.getAxis('left').labelUnits
        if not hasattr(self, 'x_units'):
            self.x_units = item.getAxis('bottom').labelUnits

        v_x, v_y = view_coords.x(), view_coords.y()

        # Size of one screen pixel in view (already-log when an axis is in
        # log mode) coordinates. Using this instead of the view-range span
        # makes the nearest-point search measure true on-screen distance,
        # so it is correct regardless of the widget's width/height aspect.
        px, py = vb.viewPixelSize()
        px = px if px > 0 else 1.0
        py = py if py > 0 else 1.0

        best_guesses = []
        for data_item in item.items:
            if not (isinstance(data_item, pg.PlotDataItem) and data_item.isVisible()):
                continue
            if restrict_to is not None and data_item is not restrict_to:
                continue
            xdata_0, ydata_0 = data_item.xData, data_item.yData
            if xdata_0 is None or len(xdata_0) < 2:
                continue

            offset = data_item.pos()
            scale_y = data_item.transform().m22()
            local_v_x = v_x - offset.x()
            local_v_y = (v_y - offset.y()) / scale_y

            # --- per-curve transformed + search arrays, cached (#5) ---
            # Recomputing the FFT / derivative / mean / log on every mouse
            # move is wasteful. Cache the result on the curve and reuse it
            # until its source data or a relevant mode changes. The cache lives
            # on the PlotDataItem, so it is freed together with the curve and
            # cannot collide across curves. opts.get(...) also removes the old
            # KeyError dance for pyqtgraph builds without 'subtractMeanMode'.
            opts = data_item.opts
            fft_mode = bool(opts.get('fftMode', False))
            submean_mode = bool(opts.get('subtractMeanMode', False))
            deriv_mode = bool(opts.get('derivativeMode', False))
            phasemap_mode = bool(opts.get('phasemapMode', False))
            fft_logx = bool(opts.get('logMode', (False, False))[0])
            flags = (fft_mode, submean_mode, deriv_mode, phasemap_mode,
                     fft_logx, x_log_mode, y_log_mode)

            cache = getattr(data_item, '_snap_cache', None)
            if (cache is not None and cache['x_src'] is xdata_0
                    and cache['y_src'] is ydata_0 and cache['flags'] == flags):
                search_x = cache['search_x']
                search_y = cache['search_y']
            else:
                if fft_mode:
                    xdata, ydata = self._fourierTransform(xdata_0, ydata_0)
                    if fft_logx:
                        xdata, ydata = xdata[1:], ydata[1:]
                elif submean_mode:
                    xdata, ydata = xdata_0, ydata_0 - np.mean(ydata_0)
                elif deriv_mode:
                    xdata, ydata = xdata_0[:-1], np.diff(ydata_0) / np.diff(xdata_0)
                elif phasemap_mode:
                    xdata, ydata = ydata_0[:-1], np.diff(ydata_0) / np.diff(xdata_0)
                else:
                    xdata, ydata = xdata_0, ydata_0

                # Build search arrays in the space the curve is drawn in. On a
                # log axis, non-positive samples are hidden by pyqtgraph, so map
                # them to NaN (excluded below) instead of clamping to a fake
                # floor that used to make the cross-hair snap to ~1e-15 points.
                if x_log_mode:
                    with np.errstate(divide='ignore', invalid='ignore'):
                        search_x = np.log10(xdata)
                    search_x[~(xdata > 0)] = np.nan
                else:
                    search_x = np.asarray(xdata)
                if y_log_mode:
                    with np.errstate(divide='ignore', invalid='ignore'):
                        search_y = np.log10(ydata)
                    search_y[~(ydata > 0)] = np.nan
                else:
                    search_y = np.asarray(ydata)

                data_item._snap_cache = {
                    'x_src': xdata_0, 'y_src': ydata_0, 'flags': flags,
                    'search_x': search_x, 'search_y': search_y,
                }

            dist_sq = ((search_x - local_v_x) / px)**2 + ((search_y - local_v_y) / py)**2
            # NaN (hidden log-axis points) -> +inf so they can never be chosen.
            dist_sq = np.where(np.isfinite(dist_sq), dist_sq, np.inf)

            # Nearest vertex. Full argmin is O(n) and correct for ordered and
            # parametric curves alike (the old ±50-index window assumed sorted
            # x and could miss the true nearest point on steep/sparse data).
            index = int(np.argmin(dist_sq))
            if not np.isfinite(dist_sq[index]):
                continue  # every point on this curve is hidden on the log axis

            best_d = float(dist_sq[index])
            ss_x = float(search_x[index])
            ss_y = float(search_y[index])

            # --- refine onto the nearest point of the drawn polyline (#6) ---
            # Project the cursor onto the two segments adjacent to the nearest
            # vertex (in pixel-normalised space) so the cross-hair can land
            # between samples. Segments touching a hidden log point are skipped.
            if self.snap_to_segments:
                ax, ay = search_x[index], search_y[index]
                for j in (index - 1, index + 1):
                    if not (0 <= j < len(search_x)):
                        continue
                    bx, by = search_x[j], search_y[j]
                    if not (np.isfinite(bx) and np.isfinite(by)):
                        continue
                    dx = (bx - ax) / px
                    dy = (by - ay) / py
                    seg_len_sq = dx * dx + dy * dy
                    if seg_len_sq == 0:
                        continue
                    t = (((local_v_x - ax) / px) * dx +
                         ((local_v_y - ay) / py) * dy) / seg_len_sq
                    if t <= 0.0 or t >= 1.0:
                        continue  # projection lands outside -> vertex already wins
                    projx = ax + t * (bx - ax)
                    projy = ay + t * (by - ay)
                    d = (((local_v_x - projx) / px) ** 2 +
                         ((local_v_y - projy) / py) ** 2)
                    if d < best_d:
                        best_d = float(d)
                        ss_x, ss_y = float(projx), float(projy)

            best_guesses.append({
                'dist': best_d,
                'ss_x': ss_x, 'ss_y': ss_y,
                'offset': offset, 'scale_y': scale_y,
                'item': data_item,
            })

        if not best_guesses:
            return None

        best_res = min(best_guesses, key=lambda g: g['dist'])
        target_item = best_res['item']
        offset = best_res['offset']
        scale_y = best_res['scale_y']
        ss_x, ss_y = best_res['ss_x'], best_res['ss_y']

        raw_pen = target_item.opts.get('pen')
        if isinstance(raw_pen, tuple):
            raw_pen = raw_pen[0]
        if hasattr(raw_pen, 'color'):
            curve_color = raw_pen.color()
        else:
            curve_color = pg.mkColor(raw_pen)

        # ss_x / ss_y are in the curve's local display space (already log when
        # the axis is log). Map back to the view position and to the data value
        # shown in the label. This one path covers both vertex and interpolated
        # (segment) snaps, in linear and log modes alike.
        v_pos = ss_x + offset.x()
        h_pos = ss_y * scale_y + offset.y()
        x_val = 10 ** v_pos if x_log_mode else v_pos
        y_val = 10 ** h_pos if y_log_mode else h_pos
        x_parsed = pg.siFormat(x_val, suffix=self.x_units, precision=5)
        y_parsed = pg.siFormat(y_val, suffix=self.y_units, precision=5)

        return {
            'view_x': v_pos,
            'view_y': h_pos,
            'x_text': x_parsed,
            'y_text': y_parsed,
            'color': curve_color,
            'item': target_item,
            'cur_view_x': v_x,
            'cur_view_y': v_y,
        }

    # ----- Ruler (Shift + left-drag) -----
    def _install_ruler_drag(self):
        vb = self.plot_item.vb
        orig = vb.mouseDragEvent
        widget = self

        def wrapper(ev, axis=None):
            modifiers = QtGui.QGuiApplication.keyboardModifiers()
            is_left = (ev.button() == QtCore.Qt.MouseButton.LeftButton or
                       bool(ev.buttons() & QtCore.Qt.MouseButton.LeftButton))
            if is_left and (modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier):
                ev.accept()
                widget._on_ruler_drag(ev)
                return
            orig(ev, axis=axis)

        vb.mouseDragEvent = wrapper

    def _on_ruler_drag(self, ev):
        modifiers = QtGui.QGuiApplication.keyboardModifiers()
        # Shift alone = snap to data; Shift+Ctrl = free coordinates
        snap = not bool(modifiers & QtCore.Qt.KeyboardModifier.ControlModifier)

        if ev.isStart():
            self._ruler_start_scene = ev.buttonDownScenePos()
            self.cursor_label.hide()
            # Lock to the curve under the press point (if any and snap is on)
            if snap:
                lock_res = self._snap_to_nearest_point(self._ruler_start_scene)
                if lock_res is not None:
                    self._ruler_locked_item = lock_res['item']
                    self._ruler_locked_color = lock_res['color']
                else:
                    self._ruler_locked_item = None
                    self._ruler_locked_color = None
            else:
                self._ruler_locked_item = None
                self._ruler_locked_color = None

        if self._ruler_start_scene is None:
            return

        # Honor the lock only while the locked curve is still alive and visible
        locked = self._ruler_locked_item
        if locked is not None and (
            locked not in self.plot_item.items or not locked.isVisible()
        ):
            locked = None

        p1 = self._ruler_point_at(self._ruler_start_scene, snap, locked_item=locked)
        p2 = self._ruler_point_at(ev.scenePos(), snap, locked_item=locked)
        self._ruler_p1, self._ruler_p2 = p1, p2

        # Color: locked curve color when snap is on and lock is valid; else yellow
        color = self._ruler_locked_color if (snap and locked is not None) else None
        self._update_ruler(p1, p2, color)

    def _ruler_point_at(self, scene_pos, snap, locked_item=None):
        """Return {x, y, x_text, y_text} for a ruler endpoint at `scene_pos`.

        When `snap` is True, snaps to nearest data point on the `locked_item`
        curve if provided (and any curve otherwise). Falls back to raw view
        coordinates with siFormat labels (log-mode aware) if snapping is
        disabled or yields nothing.
        """
        if snap:
            res = self._snap_to_nearest_point(scene_pos, restrict_to=locked_item)
            if res is not None:
                return {
                    'x': res['view_x'],
                    'y': res['view_y'],
                    'x_text': res['x_text'],
                    'y_text': res['y_text'],
                }

        vb = self.plot_item.vb
        view = vb.mapSceneToView(scene_pos)
        vx, vy = view.x(), view.y()

        if not hasattr(self, 'y_units'):
            self.y_units = self.getPlotItem().getAxis('left').labelUnits
        if not hasattr(self, 'x_units'):
            self.x_units = self.getPlotItem().getAxis('bottom').labelUnits

        x_log_mode, y_log_mode = vb.state['logMode'][0], vb.state['logMode'][1]
        x_disp = 10**vx if x_log_mode else vx
        y_disp = 10**vy if y_log_mode else vy
        return {
            'x': vx,
            'y': vy,
            'x_text': pg.siFormat(x_disp, suffix=self.x_units, precision=5),
            'y_text': pg.siFormat(y_disp, suffix=self.y_units, precision=5),
        }

    def _ensure_ruler_items(self):
        # Route through vb.addItem (not self.addItem -> PlotItem.addItem) so the
        # ruler doesn't get registered in PlotItem.curves. Otherwise FFT/log
        # toggles iterate self.curves and call setFftMode on every item, which
        # PlotCurveItem / ScatterPlotItem don't implement.
        vb = self.plot_item.vb
        if self._ruler_line is None:
            self._ruler_line = pg.PlotCurveItem(pen=pg.mkPen((255, 255, 0, 220), width=1.5))
            self._ruler_line.setZValue(95)
            vb.addItem(self._ruler_line, ignoreBounds=True)
        if self._ruler_marks is None:
            self._ruler_marks = pg.ScatterPlotItem(
                size=8, symbol='o',
                pen=pg.mkPen((255, 255, 255, 255), width=1),
                brush=pg.mkBrush(255, 255, 0, 255),
            )
            self._ruler_marks.setZValue(96)
            vb.addItem(self._ruler_marks, ignoreBounds=True)
        if self._ruler_label is None:
            self._ruler_label = pg.TextItem(anchor=(0.5, 1.0), color='w', fill=(42, 42, 64, 150))
            self._ruler_label.border = pg.mkPen((255, 255, 0, 255), width=1.5)
            self._ruler_label.setZValue(100)
            vb.addItem(self._ruler_label, ignoreBounds=True)

    def _update_ruler(self, p1, p2, color=None):
        self._ensure_ruler_items()

        x1, y1 = p1['x'], p1['y']
        x2, y2 = p2['x'], p2['y']

        # Color: when None (no lock / snap off), fall back to yellow
        ruler_color = color if color is not None else pg.mkColor(255, 255, 0)
        self._ruler_line.setPen(pg.mkPen(ruler_color, width=1.5))
        self._ruler_marks.setBrush(pg.mkBrush(ruler_color))
        self._ruler_label.border = pg.mkPen(ruler_color, width=1.5)

        self._ruler_line.setData([x1, x2], [y1, y2])
        self._ruler_marks.setData([x1, x2], [y1, y2])
        self._ruler_line.show()
        self._ruler_marks.show()

        vb = self.plot_item.vb
        x_log_mode, y_log_mode = vb.state['logMode'][0], vb.state['logMode'][1]

        dx_disp = (10**x2 - 10**x1) if x_log_mode else (x2 - x1)
        dy_disp = (10**y2 - 10**y1) if y_log_mode else (y2 - y1)

        if not hasattr(self, 'y_units'):
            self.y_units = self.getPlotItem().getAxis('left').labelUnits
        if not hasattr(self, 'x_units'):
            self.x_units = self.getPlotItem().getAxis('bottom').labelUnits

        dx_text = pg.siFormat(dx_disp, suffix=self.x_units, precision=5)
        dy_text = pg.siFormat(dy_disp, suffix=self.y_units, precision=5)

        self._ruler_label.setText(
            f"ΔX: {dx_text}\n"
            f"ΔY: {dy_text}\n"
            f"P1: ({p1['x_text']}, {p1['y_text']})\n"
            f"P2: ({p2['x_text']}, {p2['y_text']})"
        )

        # Anchor at P1, on the side opposite P2 so the segment doesn't run
        # through the label. Mirror at viewbox edges to keep it inside.
        view_range = vb.viewRange()
        x_min, x_max = view_range[0]
        y_min, y_max = view_range[1]

        dx, dy = x2 - x1, y2 - y1
        anchor_x = 1 if dx >= 0 else 0
        anchor_y = 0 if dy >= 0 else 1

        try:
            pxw, pxh = vb.viewPixelSize()
            rect = self._ruler_label.boundingRect()
            w_view = rect.width() * pxw
            h_view = rect.height() * pxh
        except Exception:
            w_view = h_view = 0

        if w_view > 0:
            if x1 - anchor_x * w_view < x_min:
                anchor_x = 0
            elif x1 + (1 - anchor_x) * w_view > x_max:
                anchor_x = 1
        if h_view > 0:
            if y1 - (1 - anchor_y) * h_view < y_min:
                anchor_y = 1
            elif y1 + anchor_y * h_view > y_max:
                anchor_y = 0

        self._ruler_label.setAnchor((anchor_x, anchor_y))
        self._ruler_label.setPos(x1, y1)
        self._ruler_label.show()

    def _clear_ruler(self):
        for attr in ('_ruler_line', '_ruler_marks', '_ruler_label'):
            item = getattr(self, attr, None)
            if item is not None:
                item.hide()
        self._ruler_start_scene = None
        self._ruler_p1 = None
        self._ruler_p2 = None
        self._ruler_locked_item = None
        self._ruler_locked_color = None

    def add_cross_hair(self, x, y):
        if hasattr(self, 'v_line'):
            # Reset positions to (x, y) — after a mode toggle (FFT/log/...)
            # the axis range may have changed and the stored line positions
            # would otherwise sit far outside the new view.
            self.v_line.setPos(x)
            self.h_line.setPos(y)
            self.h_line.show()
            self.v_line.show()
            #self.cursor_label.show()
            self.update_label_visibility()
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
            #self.cursor_label.show()
            self.update_label_visibility()
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
        self._clear_ruler()

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

    def update_label_visibility(self):
        if self.cross_section_enabled:
            self.cursor_label.setVisible(not self.hide_action.isChecked())

class CrosshairDock(CloseableDock):
    # Distinct, background-legible curve colours (see self.avail_colors). Same
    # aesthetic as data_treatment's BATCH_COLORS: mid-to-high luminance and
    # saturated so each reads clearly on the dark (63,63,97) plot background.
    # Order = draw order (white, yellow pinned first). Chosen by a farthest-point
    # search in CIELAB with saturation capped soft (<=0.78) and every colour kept
    # above a 3:1 WCAG contrast on the (63,63,97) background: the closest pair sits
    # at CIEDE2000 ~17 (vs ~10 for the old set), so overlapping traces stay easy to
    # tell apart without going neon.
    CURVE_PALETTE = [
        (255, 255, 255),   # white
        (255, 255,   0),   # yellow
        (228,  56, 255),   # magenta
        (255,  83,  56),   # red-orange
        ( 50, 146, 230),   # blue
        ( 50, 230, 146),   # green
        (230, 158,  50),   # amber
        ( 50, 218, 230),   # cyan
        (255, 153, 187),   # pink
        (167, 153, 255),   # violet
        (255, 180, 153),   # peach
        (153, 207, 255),   # sky
        (255, 221, 153),   # sand
    ]

    @staticmethod
    def _overflow_color(n):
        """A distinct bright colour for the n-th curve past the palette.

        Golden-angle hue spacing keeps successive colours far apart, at a fixed
        high value/saturation so they stay legible on the dark background — far
        better than the old behaviour of collapsing every extra curve to white.
        """
        h = (0.618033988749895 * n + 0.12) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.62, 1.0)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _take_color(self):
        """Next curve pen: a recycled/palette colour while any remain, else a
        freshly generated distinct hue. Never exhausts, never collapses to a
        single indistinguishable pen."""
        if self.avail_colors:
            return self.avail_colors.pop()
        pen = pg.mkPen(color=self._overflow_color(self._overflow_index), width=1)
        self._overflow_index += 1
        return pen

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

        plot_item = self.plot_widget.getPlotItem()
        open_action = QtGui.QAction('Open 1D Data', self)
        open_action.triggered.connect(self.file_dialog)
        plot_item.vb.menu.addAction(open_action)

        # Curve palette tuned for the dark (63,63,97) plot background: bright,
        # saturated hues that all stay legible. The old list held near-black
        # (0,0,0) / pure-blue (0,0,255) / dark-slate (47,79,79) colours that
        # vanish on the indigo background. Stored as a stack popped from the end
        # (so CURVE_PALETTE[0] is the first curve) and refilled by del_item.
        self.avail_colors = [pg.mkPen(color=c, width=1)
                             for c in reversed(self.CURVE_PALETTE)]
        # cursor for the golden-angle overflow generator (>len(palette) curves)
        self._overflow_index = 0
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
        # Fresh plot (no existing curves) → drop any stale ruler from a prior dataset
        if not self.curves:
            self.plot_widget._clear_ruler()

        if not hasattr(self.plot_widget, 'y_units'):
            self.plot_widget.y_units = kwargs.get('yscale', '')
        if not hasattr(self.plot_widget, 'x_units'):
            self.plot_widget.x_units = kwargs.get('xscale', '')

        self.plot_widget.parametric = kwargs.pop('parametric', False)
        vline_arg = kwargs.get('vline', '')

        # setLabel / setAxisItems each trigger a layout pass. They used to run on
        # every call, including every live-plot update and every append; cache the
        # last-applied values and only re-apply when they actually change.
        xnm, xsc = kwargs.get('xname', ''), kwargs.get('xscale', '')
        ynm, ysc = kwargs.get('yname', ''), kwargs.get('yscale', '')
        if kwargs.get('timeaxis', '') == 'True':
            # strange scaling when zoom
            if getattr(self, '_bottom_axis_key', None) != ('time', xnm):
                axis = pg.DateAxisItem()
                self.plot_widget.setAxisItems({'bottom': axis})
                self.plot_widget.setLabel("bottom", text=xnm)
                self._bottom_axis_key = ('time', xnm)
        else:
            if getattr(self, '_bottom_axis_key', None) != ('lin', xnm, xsc):
                self.plot_widget.setLabel("bottom", text=xnm, units=xsc)
                self._bottom_axis_key = ('lin', xnm, xsc)

        if getattr(self, '_left_axis_key', None) != (ynm, ysc):
            self.plot_widget.setLabel("left", text=ynm, units=ysc)
            self._left_axis_key = (ynm, ysc)
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
                                kwargs['pen'] = self.used_colors[name] = self._take_color()
                                args_mod = (args[0][i], args[1][i])

                                curve = self.plot_widget.plot(*args_mod, **kwargs)

                                legend = self.plot_widget.getPlotItem().legend
                                if legend is not None:
                                    last_sample, last_label = legend.items[-1]
                                    
                                    last_label.setAcceptHoverEvents(True)

                                    last_label.mouseClickEvent = lambda ev, c=curve: self.activate_by_legend(c, ev)
                                    last_label.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

                                curve_item = curve.curve 
                                curve_item.setClickable(True)#, width=10)
                                
                                curve_item.mouseDragEvent = lambda ev, c=curve: self.handle_drag(c, ev)
                                curve_item.mousePressEvent = lambda ev, c=curve: self.handle_press(c, ev)
                                self.curves[name] = curve

                                # Text label above the graph
                                temp = kwargs.get('text', '')
                                if temp != '':
                                    self.setTitle( temp )

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
                            self.vl1 = self.plot_widget.addLine( x = self.ver_line_1, pen='g' )
                        if self.ver_line_2 != float(vline_arg[1]):
                            self.plot_widget.removeItem(self.vl2)
                            self.ver_line_2 = float(vline_arg[1])
                            self.vl2 = self.plot_widget.addLine( x = self.ver_line_2, pen='g' )
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
                            kwargs['pen'] = self.used_colors[name] = self._take_color()
                            args_mod = (args[0][i], args[1][i])
                            curve = self.plot_widget.plot(*args_mod, **kwargs)

                            legend = self.plot_widget.getPlotItem().legend
                            if legend is not None:
                                last_sample, last_label = legend.items[-1]
                                
                                last_label.setAcceptHoverEvents(True)

                                last_label.mouseClickEvent = lambda ev, c=curve: self.activate_by_legend(c, ev)
                                last_label.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

                            curve_item = curve.curve 
                            curve_item.setClickable(True)#, width=10)
                            
                            curve_item.mouseDragEvent = lambda ev, c=curve: self.handle_drag(c, ev)
                            curve_item.mousePressEvent = lambda ev, c=curve: self.handle_press(c, ev)
                            self.curves[name] = curve

                        else:
                            kwargs['pen'] = self.used_colors[name]
                            args_mod = (args[0][0], args[1][0])

                            # the first curve is already plotted
                            self.curves[name].setData(*args_mod, **kwargs)

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
                                kwargs['pen'] = self.used_colors[name] = self._take_color()
                                args_mod = (args[0][i], args[1][i])
                                # the second curve is a new one
                                #self.curves[name] = self.plot_widget.plot(*args_mod, **kwargs)
                                curve = self.plot_widget.plot(*args_mod, **kwargs)

                                legend = self.plot_widget.getPlotItem().legend
                                if legend is not None:
                                    last_sample, last_label = legend.items[-1]
                                    
                                    last_label.setAcceptHoverEvents(True)

                                    last_label.mouseClickEvent = lambda ev, c=curve: self.activate_by_legend(c, ev)
                                    last_label.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

                                curve_item = curve.curve 
                                curve_item.setClickable(True)#, width=10)
                                curve_item.mouseDragEvent = lambda ev, c=curve: self.handle_drag(c, ev)
                                curve_item.mousePressEvent = lambda ev, c=curve: self.handle_press(c, ev)
                                self.curves[name] = curve

                                # Text label above the graph
                                temp = kwargs.get('text', '')
                                if temp != '':
                                    self.setTitle( temp )

                else:
                    kwargs['pen'] = self.used_colors[name] = self._take_color()

                    curve = self.plot_widget.plot(*args, **kwargs)

                    legend = self.plot_widget.getPlotItem().legend
                    if legend is not None:
                        last_sample, last_label = legend.items[-1]
                        
                        last_label.setAcceptHoverEvents(True)

                        last_label.mouseClickEvent = lambda ev, c=curve: self.activate_by_legend(c, ev)
                        last_label.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

                    curve_item = curve.curve 
                    curve_item.setClickable(True)#, width=10)
                    curve_item.mouseDragEvent = lambda ev, c=curve: self.handle_drag(c, ev)
                    curve_item.mousePressEvent = lambda ev, c=curve: self.handle_press(c, ev)
                    self.curves[name] = curve

                    # Text label above the graph
                    temp = kwargs.get('text', '')
                    if temp != '':
                        self.setTitle( temp )
                    
                # vertical lines
                if vline_arg != 'False':
                    try:
                        self.vl1 = self.plot_widget.addLine( x = float(vline_arg[0]), pen='g' )
                        self.vl2 = self.plot_widget.addLine( x = float(vline_arg[1]), pen='g' )
                    except IndexError:
                        pass

        item = self.plot_widget.getPlotItem()
        plot_data_item = next((i for i in item.items if isinstance(i, pg.PlotDataItem)), None)
        fft_state = plot_data_item.opts.get('fftMode', False)
        #fft_state = item.items[0].opts['fftMode']
        self.on_fft_toggled( fft_state )

        if not fft_state:
            self.bottom_axis_text = self.plot_widget.getAxis('bottom').labelText
            self.bottom_axis_units = self.plot_widget.getAxis('bottom').labelUnits

    def activate_by_legend(self, curve, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            
            for c in self.curves.values():
                c.setZValue(0)

            curve.setZValue(1000)
            curve.setOpacity(1.0)

            self.flash_curve(curve)

        elif ev.button() == QtCore.Qt.MouseButton.MiddleButton:
            ev.accept()
            self.del_item(curve)

    def handle_press(self, curve, ev):
        modifiers = QtGui.QGuiApplication.keyboardModifiers()
        
        if (ev.button() == QtCore.Qt.MouseButton.LeftButton and 
            modifiers == QtCore.Qt.KeyboardModifier.AltModifier):
            ev.accept()
            
            curve.setTransform(QtGui.QTransform()) 
            curve.setPos(0, 0)

            self.flash_curve(curve)

        else:
            ev.ignore()

    def flash_curve(self, curve, duration=100, width=2):
        if sip.isdeleted(curve):
            return
                
        p = pg.mkPen(curve.opts['pen'])
        old_w = p.width()
        
        p.setWidth(width)
        curve.setPen(p)
        
        def safe_restore():
            if not sip.isdeleted(curve):
                p.setWidth(old_w)
                curve.setPen(p)
                
        QtCore.QTimer.singleShot(duration, safe_restore)

    def handle_drag(self, curve, ev):
        is_left_click = ev.button() == QtCore.Qt.MouseButton.LeftButton or (ev.buttons() & QtCore.Qt.MouseButton.LeftButton)

        if is_left_click:
            modifiers = QtGui.QGuiApplication.keyboardModifiers()
            if modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier:
                ev.accept()
                self.plot_widget._on_ruler_drag(ev)
                return

            ev.accept()

            if ev.isStart():
                self.flash_curve(curve)

            if not ev.isFinish():
                delta_scene = ev.scenePos() - ev.lastScenePos()
                
                if modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
                    x_data, y_data = curve.getData()
                    if y_data is not None and len(y_data) > 0:
                        # Vertical scaling pivots about the point grabbed at the
                        # start of the drag, so whatever the user puts the cursor
                        # on (typically the baseline) stays fixed while the curve
                        # scales. Capture, once per drag, the data value sitting
                        # under the cursor and the view-y it occupies. Both are
                        # in the curve's display space, so this is correct in log
                        # mode as well (view_y = data_y * m22 + curve.y()).
                        vb = curve.getViewBox()
                        if vb is not None and (ev.isStart() or
                                               not hasattr(curve, '_scale_pivot_view_y')):
                            pivot_view_y = vb.mapSceneToView(ev.buttonDownScenePos()).y()
                            m22_0 = curve.transform().m22() or 1.0
                            curve._scale_pivot_view_y = pivot_view_y
                            curve._scale_pivot_data_y = (pivot_view_y - curve.y()) / m22_0

                        sensitivity = 0.005
                        factor = 1.0 - (delta_scene.y() * sensitivity)
                        factor = max(0.1, min(factor, 10.0))

                        new_sy = curve.transform().m22() * factor
                        curve.setTransform(QtGui.QTransform().scale(1.0, new_sy))

                        # Re-translate so the grabbed point keeps its screen y.
                        if hasattr(curve, '_scale_pivot_view_y'):
                            curve.setY(curve._scale_pivot_view_y
                                       - curve._scale_pivot_data_y * new_sy)

                elif modifiers == QtCore.Qt.KeyboardModifier.NoModifier:
                    p1 = curve.mapToParent(ev.pos())
                    p2 = curve.mapToParent(ev.lastPos())
                    diff = p1 - p2
                    
                    new_pos = curve.pos() + diff
                    curve.setPos(new_pos.x(), new_pos.y())

            if ev.isFinish():
                p = pg.mkPen(curve.opts['pen'])
                p.setWidth(1)
                curve.setPen(p)
                curve.setZValue(0)
                # forget the per-drag pivot so the next Ctrl-drag re-grabs
                if hasattr(curve, '_scale_pivot_view_y'):
                    del curve._scale_pivot_view_y
                    del curve._scale_pivot_data_y

        else:
            ev.ignore()

    def del_item(self, item):
        self.plot_widget.removeItem(item)
        key_name = list(self.curves.keys())[list(self.curves.values()).index(item)]
        self.curves.pop(key_name, None)
        self.avail_colors.append(self.used_colors[key_name])
        #TO DO the same for scatter plot

    def open_file(self, filename):
        """
        A function to open 1d data.
        :param filename: string
        """
        file_path = filename
        self.open_dir = os.path.dirname(filename)
        ldir.save('data', self.open_dir)      # remember the data folder

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
        name_plot = os.path.splitext(os.path.basename(file_path))[0]

        if len(data) == 2:
            self.plot(data[0], data[1], parametric = True, name = name_plot, xname = 'X', xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
        elif len(data) == 3 and np.isnan(data[2][0]) != True:
            self.plot(data[0], data[1], parametric = True, name = name_plot + '_1', xname = 'X', xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
            self.plot(data[0], data[2], parametric = True, name = name_plot + '_2', xname = 'X', xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', label = 'Data_2', scatter = 'False')
        elif len(data) == 3 and np.isnan(data[2][0]) == True:
            self.plot(data[0], data[1], parametric = True, name = name_plot, xname = 'X', xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
        elif len(data) == 4 and np.isnan(data[3][0]) == True:
            self.plot(data[0], data[1], parametric = True, name = name_plot + '_1', xname = 'X', xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
            self.plot(data[0], data[2], parametric = True, name = name_plot + '_2', xname = 'X', xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', label = 'Data_2', scatter = 'False')
        elif len(data) == 5 and np.isnan(data[4][0]) == True:
            self.plot(data[0], data[1], parametric = True, name = name_plot + '_1', xname = 'X', xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', label = 'Data_1', scatter = 'False')
            self.plot(data[0], data[3], parametric = True, name = name_plot + '_2', xname = 'X', xscale = 'Arb. U.', yname = 'Y', yscale = 'Arb. U.', label = 'Data_2', scatter = 'False')

    def file_dialog(self, directory = ''):
        """
        A function to open a new window for choosing 1d data
        """
        filedialog = QtWidgets.QFileDialog(self, 'Open File', directory = ldir.load('data', self.open_dir), filter = "CSV (*.csv)",  options = QtWidgets.QFileDialog.Option.DontUseNativeDialog )
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
        self.plot_widget._clear_ruler()
        self.plot_widget.clear()

    def get_data(self, label):
        if label in self.curves:
            return self.curves[label].getData()
        else:
            return [], []

    def get_raw_data(self, label):
        # Original, untransformed samples (.xData/.yData) rather than getData(),
        # which returns the DISPLAY data — log10-mapped on a log axis, or
        # FFT/derivative-transformed in those modes. Used when exporting the
        # underlying data (e.g. "Send to Data Treatment"), so a log-scaled plot
        # doesn't ship log-space x values that break the axis and the fit.
        if label in self.curves:
            x = self.curves[label].xData
            y = self.curves[label].yData
            if x is None or y is None:
                return [], []
            return x, y
        else:
            return [], []

    def redraw(self):
        xs_ys = []
        for name in self.curves:
            # raw, not get_data(): rebuilding from the decimated display series
            # would bake the downsampling permanently into the stored curve.
            xs_ys.append((name,) + self.get_raw_data(name))
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

        #self.plot_item.showGrid(x=True, y=True, alpha=0.1)

        time_plot = self.img_view.ui.roiPlot
        self.vb_time = time_plot.getViewBox()
        time_plot.hideButtons()
        self.vb_time.mouseClickEvent = self.on_time_click

        axis = time_plot.getAxis('bottom')
        axis.setTickSpacing(major=1, minor=1)

        self.line = self.img_view.timeLine
        self.line.setPen(pg.mkPen('y', width=3))
        self.line.setHoverPen(pg.mkPen('w', width=3))

        # Two colormaps, picked per-signal (see _auto_levels_cmap):
        #  * bipolar blue-white-red for two-sided signals, WHITE centred on the
        #    baseline so a non-zero offset reads neutral;
        #  * sequential viridis for one-sided signals, so an all-positive (or
        #    all-negative) map never shows a spurious opposite-sign colour.
        self.cmap_bipolar = pg.ColorMap(
            np.array([0.0, 0.5, 1.0]),
            np.array([[0, 0, 255, 255], [255, 255, 255, 255], [255, 0, 0, 255]],
                     dtype=np.ubyte))
        self.cmap_sequential = pg.ColorMap(
            np.array([0.0, 0.25, 0.5, 0.75, 1.0]),
            np.array([[68, 1, 84, 255], [59, 82, 139, 255], [33, 145, 140, 255],
                      [94, 201, 98, 255], [253, 231, 37, 255]], dtype=np.ubyte))
        cmap = self.cmap_bipolar
        self._active_cmap = cmap
        # Colour mode. 'default' reproduces the original build exactly (pyqtgraph
        # autoLevels + the fixed bipolar map, zero extra cost) and is the default;
        # the smart modes 'auto' | 'bipolar' | 'sequential' are opt-in from the
        # menu. center_baseline pins the bipolar white to the estimated baseline.
        self.color_mode = 'default'
        self.center_baseline = True
        # Auto mode locks its first non-trivial polarity decision here so a
        # dynamically re-pushed plot can't flip sequential<->bipolar mid-run.
        # Reset on a new dataset (geometry change) or when Auto is re-selected.
        self._auto_locked = None
        # subsample size for the baseline (median) estimate: the full-array median
        # is the costly part, so a representative sample keeps a smart mode's
        # per-push cost close to the default build's subsampled autoLevels.
        self._stat_sample = 100000
        # For a multi-frame stack, level+colormap each frame on its own stats
        # (so a raw non-zero-baseline frame and a baseline-subtracted frame in
        # the same stack each display correctly). Off = one fixed scaling from
        # the whole stack, keeping frames directly comparable.
        self.per_frame_levels = True

        # plot options menu
        #self.plot_item.getViewBox().menu.setStyleSheet("QMenu::item:selected {background-color: rgb(40, 40, 40); } QMenu::item { color: rgb(211, 194, 78); } QMenu {background-color: rgb(42, 42, 64); }")
        #self.plot_item.ctrlMenu.setStyleSheet("QMenu::item:selected {background-color: rgb(40, 40, 40); } QMenu::item { color: rgb(211, 194, 78); } QMenu {background-color: rgb(42, 42, 64); }")
        self.auto_levels = 0
        self.set_image = 0
        self.click_count = 1
        view.setAspectLocked(lock=False)
        self.ui = self.img_view.ui
        self.imageItem = self.img_view.imageItem
        # Decimate the image to ~display resolution before the makeARGB/LUT pass
        # when it has more pixels than the view. Display-only: imageItem.image
        # (read by get_data/append_z map-building and the cross-section slices)
        # stays full resolution. Modest (~1.3x at the 4M-cell cap), free below.
        self.imageItem.setAutoDownsample(True)
        super(CrossSectionDock, self).__init__(**kwargs)
        self.closeClicked.connect(self.hide_cross_section)
        self.cross_section_enabled = False
        self.search_mode = False
        self.signals_connected = False
        self.set_histogram(False)

        self.hide_action = QtGui.QAction('Hide Label', self)
        self.hide_action.setCheckable(True)
        self.hide_action.setChecked(False)
        self.hide_action.triggered.connect(self.update_label_visibility)
        self.plot_item.vb.menu.addAction(self.hide_action)

        histogram_action = QtGui.QAction('Histogram', self)
        histogram_action.setCheckable(True)
        histogram_action.triggered.connect(self.set_histogram)
        self.plot_item.vb.menu.addAction(histogram_action)

        save_action = QtGui.QAction('Save Data', self)
        save_action.triggered.connect(self.fileSaveDialog)
        self.plot_item.vb.menu.addAction(save_action)

        # Colormap control: auto-pick per signal, or force bipolar/sequential,
        # plus a toggle for baseline-centred bipolar levels.
        cmap_menu = self.plot_item.vb.menu.addMenu('Colormap')
        grp = QtGui.QActionGroup(self)
        grp.setExclusive(True)
        for label, key in (('Default (build autoLevels)', 'default'),
                           ('Auto', 'auto'),
                           ('Bipolar (blue-white-red)', 'bipolar'),
                           ('Sequential (viridis)', 'sequential')):
            act = QtGui.QAction(label, self, checkable=True)
            act.setChecked(key == self.color_mode)
            act.triggered.connect(lambda _checked, k=key: self._set_color_mode(k))
            grp.addAction(act)
            cmap_menu.addAction(act)
        cmap_menu.addSeparator()
        self.center_action = QtGui.QAction('Center bipolar on baseline', self,
                                           checkable=True)
        self.center_action.setChecked(self.center_baseline)
        self.center_action.triggered.connect(self._set_center_baseline)
        cmap_menu.addAction(self.center_action)
        self.per_frame_action = QtGui.QAction('Per-frame auto-levels (stacks)',
                                              self, checkable=True)
        self.per_frame_action.setChecked(self.per_frame_levels)
        self.per_frame_action.triggered.connect(self._set_per_frame)
        cmap_menu.addAction(self.per_frame_action)

        #self.autolevels_action = QtGui.QAction('Autoscale Levels', self)
        #self.autolevels_action.setCheckable(True)
        #self.autolevels_action.setChecked(True)
        #self.autolevels_action.triggered.connect(self.redraw)

        #self.ui.histogram.item.sigLevelChangeFinished.connect(lambda: self.autolevels_action.setChecked(False))
        #self.img_view.scene.contextMenu.append(self.autolevels_action)
        #self.clear_action = QtGui.QAction('Clear Contents', self)
        #self.clear_action.triggered.connect(self.clear)
        #self.img_view.scene.contextMenu.append(self.clear_action)
        self.ui.histogram.gradient.setColorMap(cmap)
        self._active_cmap = cmap
        # re-level per frame when scrolling a stack (see per_frame_levels)
        self.img_view.sigTimeChanged.connect(self._on_frame_changed)

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

        # Ruler (Shift + left-drag) — state, items, and viewbox drag hook
        self._ruler_start_scene = None
        self._ruler_p1 = None
        self._ruler_p2 = None
        self._ruler_line = None
        self._ruler_marks = None
        self._ruler_label = None

        self.clear_ruler_action = QtGui.QAction('Clear Ruler', self)
        self.clear_ruler_action.triggered.connect(self._clear_ruler)
        self.plot_item.vb.menu.addAction(self.clear_ruler_action)

        self._install_ruler_drag()

        # Refresh ruler Z when the time line moves (dragging the yellow line
        # changes the displayed frame; make_line_discrete handles the click
        # path, this handles the drag path).
        self.line.sigPositionChanged.connect(self._refresh_ruler_z)

        self.first_render = True

    def on_time_click(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            pos = self.vb_time.mapSceneToView(ev.scenePos())
            new_x = pos.x()
            
            self.img_view.timeLine.setValue(new_x)
            self.make_line_discrete() 
            
            ev.accept()
        else:
            ev.ignore()

    def make_line_discrete(self):
        current_val = self.line.value()
        t_data = self.time_array

        idx = (np.abs(t_data - current_val)).argmin()
        snap_val = t_data[idx]

        self.line.blockSignals(True)
        self.line.setValue(snap_val)
        self.line.blockSignals(False)
        self.img_view.setCurrentIndex(idx)
        self._refresh_ruler_z()

    def update_label_visibility(self):
        if self.cross_section_enabled:
            self.cursor_label.setVisible(not self.hide_action.isChecked())

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
        # honour the unit passed on each push (so re-labelling from a treatment
        # tool updates the SI suffix), but keep the previous value when a push
        # omits the key (e.g. append_z without zscale).
        if 'zscale' in kwargs:
            self.label_z = kwargs.get('zscale', '')
        elif not hasattr(self, 'label_z'):
            self.label_z = ''
        if 'yscale' in kwargs:
            self.label_y = kwargs.get('yscale', '')
        elif not hasattr(self, 'label_y'):
            self.label_y = ''
        if 'xscale' in kwargs:
            self.label_x = kwargs.get('xscale', '')
        elif not hasattr(self, 'label_x'):
            self.label_x = ''

        self.plot_item.setLabel(axis='bottom', text=kwargs.get('xname', ''), units=self.label_x)
        self.plot_item.setLabel(axis='left', text=kwargs.get('yname', ''), units=self.label_y)
        self.v_cross_section_widget.plotItem.setLabel(axis='left', text=kwargs.get('zname', ''), units=self.label_z)
        self.h_cross_section_widget.plotItem.setLabel(axis='bottom', text=kwargs.get('xname', ''), units=self.label_x)
        self.v_cross_section_widget.plotItem.setLabel(axis='bottom', text=kwargs.get('yname', ''), units=self.label_y)
        self.h_cross_section_widget.plotItem.setLabel(axis='left', text=kwargs.get('zname', ''), units=self.label_z)

        self.h_cross_section_widget.axis = [kwargs.get('xname', ''), kwargs.get('xscale', '')] 
        self.v_cross_section_widget.axis = [kwargs.get('yname', ''), kwargs.get('yscale', '')] 

    def _auto_levels_cmap(self, img):
        """Choose (levels, colormap) for a 2D map, centred on its baseline.

        Baseline = median (robust to sparse signal on a flat background). We
        measure the swing below/above it: a two-sided (bimodal) signal gets the
        blue-white-red map with WHITE pinned to the baseline and symmetric
        levels, so a non-zero offset reads neutral and +/- lobes are comparable;
        a one-sided signal gets sequential viridis over min..max, so it never
        shows a spurious opposite-sign colour. Returns (None, None) to fall back
        to plain autoLevels (degenerate / non-numeric data).
        """
        try:
            arr = np.asarray(img)
        except Exception:
            return None, None
        if arr.size < 2:
            return None, None
        # baseline from a strided subsample (median's full-array partition is the
        # costly part); levels from nan-safe full min/max so a real peak/dip in a
        # sparse map is never clipped by subsampling
        flat = arr.ravel()
        step = max(1, flat.size // self._stat_sample)
        base = float(np.nanmedian(flat[::step]))
        lo, hi = float(np.nanmin(arr)), float(np.nanmax(arr))
        if not (np.isfinite(base) and np.isfinite(lo) and np.isfinite(hi)):
            return None, None
        neg, pos = base - lo, hi - base            # both >= 0
        span = max(neg, pos)
        if span <= 0:
            return None, None
        mode = self.color_mode
        if mode == 'auto':
            if self._auto_locked is not None:
                mode = self._auto_locked            # frozen for the rest of the run
            else:
                # two-sided when the smaller excursion is a real fraction of the
                # larger; freeze this first non-trivial (span>0) decision so a
                # live re-push can't recolour mid-acquisition
                mode = 'bipolar' if (min(neg, pos) / span) > 0.15 else 'sequential'
                self._auto_locked = mode
        if mode == 'bipolar':
            if self.center_baseline:
                return (base - span, base + span), self.cmap_bipolar
            return (lo, hi), self.cmap_bipolar
        return (lo, hi), self.cmap_sequential

    def _apply_cmap(self, cmap):
        """Swap the histogram gradient only when it actually changes, so a user's
        manual gradient/level edits aren't reset on every live re-push."""
        if cmap is not None and cmap is not self._active_cmap:
            self.ui.histogram.gradient.setColorMap(cmap)
            self._active_cmap = cmap

    def _auto_apply(self, arr):
        """Compute + apply levels and colormap from a single array."""
        if arr is None:
            return
        levels, cmap = self._auto_levels_cmap(np.asarray(arr))
        self._apply_cmap(cmap)
        if levels is not None:
            self.img_view.setLevels(*levels)

    def _level_source(self):
        """The array the levels/colormap are computed from: the current frame
        when per_frame_levels is on, else the whole (possibly 3D) stack."""
        if self.per_frame_levels:
            return self.img_view.imageItem.image        # current 2D frame
        return self.img_view.image                       # whole stack

    def _reapply_colormap(self):
        """Recompute levels + colormap for what's on screen (menu toggles,
        frame scroll)."""
        if self.img_view.image is None:
            return
        self._auto_apply(self._level_source())

    def _on_frame_changed(self, *args):
        # scrolling to another frame of a stack: re-level it on its own stats
        # (only in the opt-in smart modes)
        if self.color_mode != 'default' and self.per_frame_levels:
            self._auto_apply(self.img_view.imageItem.image)

    def _set_color_mode(self, mode):
        self.color_mode = mode
        if mode == 'auto':
            self._auto_locked = None            # (re)selecting Auto re-decides
        if mode == 'default':
            # restore the original build's look: fixed bipolar map + plain
            # (nan-safe) min/max levels on the current frame
            self._apply_cmap(self.cmap_bipolar)
            img = self.img_view.imageItem.image
            if img is not None:
                lo, hi = float(np.nanmin(img)), float(np.nanmax(img))
                if np.isfinite(lo) and np.isfinite(hi):
                    self.img_view.setLevels(lo, hi)
        else:
            self._reapply_colormap()

    def _set_center_baseline(self, enabled):
        self.center_baseline = bool(enabled)
        self._reapply_colormap()

    def _set_per_frame(self, enabled):
        self.per_frame_levels = bool(enabled)
        self._reapply_colormap()

    def setImage(self, *args, **kwargs):
        item = self.plot_item.getViewBox()

        if self.first_render:
            kwargs['autoRange'] = True
            self.first_render = False
        else:
            kwargs['autoRange'] = False
            item.disableAutoRange(pg.ViewBox.XYAxes)

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
                self._clear_ruler()
                # geometry changed (e.g. reset-to-raw, FFT axis swap): the old
                # view range is meaningless, so refit the data this push.
                kwargs['autoRange'] = True
                item.enableAutoRange(pg.ViewBox.XYAxes)
                # a new dataset starts a fresh run: let Auto re-decide polarity
                self._auto_locked = None

        self._x0_prev = self._x0
        self._y0_prev = self._y0
        self._xscale_prev = self._xscale
        self._yscale_prev = self._yscale

        #autorange = self.img_view.getView().vb.autoRangeEnabled()[0]
        #kwargs['autoRange'] = autorange

        # do_auto=False means the caller pinned manual levels. In 'default' mode
        # we defer entirely to pyqtgraph's autoLevels (original build, zero extra
        # cost); in a smart mode we set levels ourselves after the image is in.
        do_auto = (self.auto_levels == 0)
        self.auto_levels = 0
        if self.color_mode == 'default':
            kwargs['autoLevels'] = do_auto
        else:
            kwargs['autoLevels'] = False

        # remember which frame of a multi-frame stack (e.g. real/imag) the user
        # is viewing; ImageView.setImage resets it to 0 on every call, which
        # would snap live re-pushes back to the first frame.
        prev_index = getattr(self.img_view, 'currentIndex', 0) or 0

        self.img_view.setImage(*args, **kwargs )

        if self.set_image != 0 and prev_index > 0:
            img = self.img_view.image
            nframes = img.shape[0] if (img is not None and img.ndim == 3) else 1
            if prev_index < nframes:
                self.img_view.setCurrentIndex(prev_index)

        # smart modes only: baseline-centred levels + polarity-appropriate
        # colormap on the frame now shown (or whole stack when per-frame is off);
        # skipped in 'default' mode and when the caller pinned manual levels
        if do_auto and self.color_mode != 'default':
            self._reapply_colormap()

        if self.set_image == 0:
            item.autoRange(padding = 0.05 )
            if hasattr(self.img_view, 'tVals') and self.img_view.tVals is not None and len(self.img_view.tVals) > 0:
                self.time_array = self.img_view.tVals
                t_min, t_max = self.time_array[0], self.time_array[-1]
                self.line.setBounds([t_min, t_max])

        ##full_stack = self.img_view.image 

        #self.img_view.getView().vb.enableAutoRange(enable = autorange)
        self.update_cross_section_set_data()
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
        current_header = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))

        base_name, ext = os.path.splitext(fileName)
        ext = '.csv'

        if data.ndim <= 2:
            full_path = f"{base_name}{ext}"
            np.savetxt(full_path, data, fmt='%.4e', delimiter=',', newline='\n',
                       header=current_header, footer='', comments='#', encoding=None)
        else:
            for i in range(len(data)):
                full_path = f"{base_name}_{i}{ext}"
                np.savetxt(full_path, data[i], fmt='%.4e', delimiter=',', newline='\n',
                           header=current_header, footer='', comments='#', encoding=None)

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
        self.cursor_label.setVisible(not self.hide_action.isChecked())
        #self.cursor_label.show()

        mid_y_parsed = si_cursor_label(mid_y, self.label_y)
        mid_x_parsed = si_cursor_label(mid_x, self.label_x)
        mid_z_parsed = si_cursor_label(0, self.label_z)

        self.cursor_label.border = pg.mkPen((255, 255, 0, 255), width=1.5)
        label_text = f"X: {mid_x_parsed}\nY: {mid_y_parsed}\nZ: {mid_z_parsed}"
        self.cursor_label.setText(label_text)

        self.v_cross_section_widget.image_operation = 1
        self.v_cross_section_widget.click_count_1d = 0
        self.v_cross_section_widget.search_mode = False

        self.h_cross_section_widget.image_operation = 1
        self.h_cross_section_widget.click_count_1d = 0
        self.h_cross_section_widget.search_mode = False

    def hide_cross_section(self):
        if self.cross_section_enabled:
            self.plot_item.removeItem(self.h_line)
            self.plot_item.removeItem(self.v_line)
            #self.img_view.ui.graphicsView.removeItem(self.text_item)
            self.cross_section_enabled = False
            self.h_cross_dock.close()
            self.v_cross_dock.close()

            self.cursor_label.hide()
            self._clear_ruler()

    def connect_signal(self):
        """This can only be run after the item has been embedded in a scene"""
        if self.signals_connected:
            warnings.warn("")
        if self.imageItem.scene() is None:
            raise RuntimeError('Signal can only be connected after it has been embedded in a scene.')
        self.imageItem.scene().sigMouseClicked.connect(self.toggle_search)
        self.imageItem.scene().sigMouseMoved.connect(self.handle_mouse_move)
        #self.img_view.timeLine.sigPositionChanged.connect(self.update_cross_section)
        # refresh the section curves when the frame slider moves (e.g. toggling
        # the real/imag frame of a complex stack), not just on a fresh setImage.
        self.img_view.timeLine.sigPositionChanged.connect(self.update_cross_section_set_data)
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
            self.cursor_label.setVisible(not self.hide_action.isChecked())

            #self.cursor_label.show()

            y_parsed = si_cursor_label(view_y, self.label_y)
            x_parsed = si_cursor_label(view_x, self.label_x)
            z_parsed = si_cursor_label(z_val, self.label_z)

            label_text = f"X: {x_parsed} ({(self.y_cross_index+1):.0f})\nY: {y_parsed} ({(self.x_cross_index+1):.0f})\nZ: {z_parsed}"
            self.cursor_label.setText(label_text)

    def update_cross_section_set_data(self):
        img = self.imageItem.image
        if img is None or img.ndim != 2:
            return
        nx, ny = img.shape
        # clamp stale crosshair indices after a shape change (e.g. FFT zero fill
        # alters the point count) so the section refresh stays in range instead
        # of raising and silently aborting the update.
        self.x_cross_index = min(max(self.x_cross_index, 0), nx - 1)
        self.y_cross_index = min(max(self.y_cross_index, 0), ny - 1)
        x0, y0, xscale, yscale = self._x0, self._y0, self._xscale, self._yscale
        xdata = np.linspace(x0, x0+(xscale*(nx-1)), nx)
        ydata = np.linspace(y0, y0+(yscale*(ny-1)), ny)
        v_xdata = img[:, self.y_cross_index]
        v_ydata = img[self.x_cross_index, :]

        self.h_cross_section_widget_data.setData(xdata, v_xdata)
        self.v_cross_section_widget_data.setData(ydata, v_ydata)

        # the curves now reflect new data / a new frame; resync the readout
        # labels too (Z at the crosshair, and X/Y if the axes changed) so they
        # don't keep showing the coordinates from the previous push.
        if self.cross_section_enabled:
            zval = img[self.x_cross_index, self.y_cross_index]
            x_parsed = si_cursor_label(xdata[self.x_cross_index], self.label_x)
            y_parsed = si_cursor_label(ydata[self.y_cross_index], self.label_y)
            z_parsed = si_cursor_label(zval, self.label_z)
            self.cursor_label.setText(
                f"X: {x_parsed} ({(self.y_cross_index+1):.0f})\n"
                f"Y: {y_parsed} ({(self.x_cross_index+1):.0f})\nZ: {z_parsed}")
            # section-plot crosshair labels + marker lines
            self.update_cross_section()

    def update_cross_section(self):
        nx, ny = self.imageItem.image.shape
        x0, y0, xscale, yscale = self._x0, self._y0, self._xscale, self._yscale
        xdata = np.linspace(x0, x0+(xscale*(nx-1)), nx)
        ydata = np.linspace(y0, y0+(yscale*(ny-1)), ny)
        zval = self.imageItem.image[self.x_cross_index, self.y_cross_index]
        v_xdata = self.imageItem.image[:, self.y_cross_index]
        v_ydata = self.imageItem.image[self.x_cross_index, :]

        self.h_cross_section_widget_data.setData(xdata, v_xdata)
        self.v_cross_section_widget_data.setData(ydata, v_ydata)

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
                #self.v_cross_section_widget.cursor_label.show()
                self.v_cross_section_widget.update_label_visibility()

            y_parsed = si_cursor_label(ydata[self.y_cross_index], self.label_y)
            x_parsed = si_cursor_label(xdata[self.x_cross_index], self.label_x)
            z_parsed = si_cursor_label(zval, self.label_z)

            label_text = f"X: {x_parsed} ({(self.y_cross_index+1):.0f})\nY: {y_parsed} ({(self.x_cross_index+1):.0f})\nZ: {z_parsed}"
            #label_text = f"Y: {ydata[self.y_cross_index]:.4g}\nZ: {zval:.4g}\nPoint: {(self.x_cross_index+1):.0f}"
            
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
                #self.h_cross_section_widget.cursor_label.show()
                self.h_cross_section_widget.update_label_visibility()

            y_parsed = si_cursor_label(ydata[self.y_cross_index], self.label_y)
            x_parsed = si_cursor_label(xdata[self.x_cross_index], self.label_x)
            z_parsed = si_cursor_label(zval, self.label_z)

            label_text = f"X: {x_parsed} ({(self.y_cross_index+1):.0f})\nY: {y_parsed} ({(self.x_cross_index+1):.0f})\nZ: {z_parsed}"
            #f"X: {xdata[self.x_cross_index]:.4g}\nZ: {zval:.4g}\nPoint: {(self.y_cross_index+1):.0f}"

            self.h_cross_section_widget.cursor_label.setText(label_text)

    # ----- Ruler (Shift + left-drag) -----
    def _install_ruler_drag(self):
        vb = self.plot_item.vb
        orig = vb.mouseDragEvent
        dock = self

        def wrapper(ev, axis=None):
            modifiers = QtGui.QGuiApplication.keyboardModifiers()
            is_left = (ev.button() == QtCore.Qt.MouseButton.LeftButton or
                       bool(ev.buttons() & QtCore.Qt.MouseButton.LeftButton))
            if is_left and (modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier):
                ev.accept()
                dock._on_ruler_drag(ev)
                return
            orig(ev, axis=axis)

        vb.mouseDragEvent = wrapper

    def _on_ruler_drag(self, ev):
        modifiers = QtGui.QGuiApplication.keyboardModifiers()
        # Shift alone = snap to pixel; Shift+Ctrl = free coordinates
        snap = not bool(modifiers & QtCore.Qt.KeyboardModifier.ControlModifier)

        if ev.isStart():
            self._ruler_start_scene = ev.buttonDownScenePos()

        if self._ruler_start_scene is None:
            return

        p1 = self._ruler_point_at(self._ruler_start_scene, snap)
        p2 = self._ruler_point_at(ev.scenePos(), snap)
        self._ruler_p1, self._ruler_p2 = p1, p2

        self._update_ruler(p1, p2)

    def _ruler_point_at(self, scene_pos, snap):
        """Return {x, y, z, x_text, y_text, z_text} for a ruler endpoint at `scene_pos`.

        When `snap` is True, snaps to the nearest pixel center (xdata[ix]=x0+ix*xs,
        ydata[iy]=y0+iy*ys) and reads z from `imageItem.image[ix, iy]`. Otherwise
        keeps the raw view coordinates and looks up z at the underlying pixel if
        the point is inside the image.
        """
        vb = self.plot_item.vb
        view = vb.mapSceneToView(scene_pos)
        vx, vy = view.x(), view.y()

        label_x = getattr(self, 'label_x', '')
        label_y = getattr(self, 'label_y', '')
        label_z = getattr(self, 'label_z', '')

        image = self.imageItem.image
        z = None
        x_text = pg.siFormat(vx, suffix=label_x, precision=5)
        y_text = pg.siFormat(vy, suffix=label_y, precision=5)
        z_text = ''

        if (image is not None and image.shape != (1, 1)
                and hasattr(self, '_x0') and hasattr(self, '_xscale')
                and self._xscale != 0 and self._yscale != 0):
            nx, ny = image.shape
            x0, y0, xs, ys = self._x0, self._y0, self._xscale, self._yscale

            if snap:
                ix = int(round((vx - x0) / xs))
                iy = int(round((vy - y0) / ys))
            else:
                ix = int((vx - x0) / xs)
                iy = int((vy - y0) / ys)

            ix_c = max(0, min(ix, nx - 1))
            iy_c = max(0, min(iy, ny - 1))

            if snap:
                vx = x0 + ix_c * xs
                vy = y0 + iy_c * ys
                z = float(image[ix_c, iy_c])
                x_text = pg.siFormat(vx, suffix=label_x, precision=5) + f" ({iy_c + 1})"
                y_text = pg.siFormat(vy, suffix=label_y, precision=5) + f" ({ix_c + 1})"
                z_text = pg.siFormat(z, suffix=label_z, precision=5)
            elif 0 <= ix < nx and 0 <= iy < ny:
                z = float(image[ix, iy])
                z_text = pg.siFormat(z, suffix=label_z, precision=5)

        return {
            'x': vx,
            'y': vy,
            'z': z,
            'x_text': x_text,
            'y_text': y_text,
            'z_text': z_text,
        }

    def _ensure_ruler_items(self):
        vb = self.plot_item.vb
        if self._ruler_line is None:
            self._ruler_line = pg.PlotCurveItem(pen=pg.mkPen((255, 255, 0, 220), width=1.5))
            self._ruler_line.setZValue(95)
            vb.addItem(self._ruler_line, ignoreBounds=True)
        if self._ruler_marks is None:
            self._ruler_marks = pg.ScatterPlotItem(
                size=8, symbol='o',
                pen=pg.mkPen((255, 255, 255, 255), width=1),
                brush=pg.mkBrush(255, 255, 0, 255),
            )
            self._ruler_marks.setZValue(96)
            vb.addItem(self._ruler_marks, ignoreBounds=True)
        if self._ruler_label is None:
            self._ruler_label = pg.TextItem(anchor=(0.5, 1.0), color='w', fill=(42, 42, 64, 150))
            self._ruler_label.border = pg.mkPen((255, 255, 0, 255), width=1.5)
            self._ruler_label.setZValue(100)
            vb.addItem(self._ruler_label, ignoreBounds=True)

    def _update_ruler(self, p1, p2):
        self._ensure_ruler_items()

        x1, y1 = p1['x'], p1['y']
        x2, y2 = p2['x'], p2['y']

        self._ruler_line.setData([x1, x2], [y1, y2])
        self._ruler_marks.setData([x1, x2], [y1, y2])
        self._ruler_line.show()
        self._ruler_marks.show()

        self._ruler_label.setText(self._ruler_label_text(p1, p2))

        # Anchor at P1, on the side opposite P2 so the segment doesn't run
        # through the label. Mirror at viewbox edges to keep it inside.
        vb = self.plot_item.vb
        view_range = vb.viewRange()
        x_min, x_max = view_range[0]
        y_min, y_max = view_range[1]

        dx, dy = x2 - x1, y2 - y1
        anchor_x = 1 if dx >= 0 else 0
        anchor_y = 0 if dy >= 0 else 1

        try:
            pxw, pxh = vb.viewPixelSize()
            rect = self._ruler_label.boundingRect()
            w_view = rect.width() * pxw
            h_view = rect.height() * pxh
        except Exception:
            w_view = h_view = 0

        if w_view > 0:
            if x1 - anchor_x * w_view < x_min:
                anchor_x = 0
            elif x1 + (1 - anchor_x) * w_view > x_max:
                anchor_x = 1
        if h_view > 0:
            if y1 - (1 - anchor_y) * h_view < y_min:
                anchor_y = 1
            elif y1 + anchor_y * h_view > y_max:
                anchor_y = 0

        self._ruler_label.setAnchor((anchor_x, anchor_y))
        self._ruler_label.setPos(x1, y1)
        self._ruler_label.show()

    def _clear_ruler(self):
        for attr in ('_ruler_line', '_ruler_marks', '_ruler_label'):
            item = getattr(self, attr, None)
            if item is not None:
                item.hide()
        self._ruler_start_scene = None
        self._ruler_p1 = None
        self._ruler_p2 = None

    def _refresh_ruler_z(self):
        """Re-read Z at both ruler endpoints from the currently displayed frame.

        Used after the time slider snaps to a new index in a 2D-stack plot:
        X/Y stay fixed, but the underlying image changes, so the ruler's
        ΔZ / P1.Z / P2.Z need to be recomputed from imageItem.image.
        """
        if self._ruler_p1 is None or self._ruler_p2 is None:
            return
        if self._ruler_line is None or not self._ruler_line.isVisible():
            return
        image = self.imageItem.image
        if image is None or image.shape == (1, 1):
            return
        if not (hasattr(self, '_x0') and hasattr(self, '_xscale')):
            return
        if self._xscale == 0 or self._yscale == 0:
            return

        nx, ny = image.shape
        x0, y0, xs, ys = self._x0, self._y0, self._xscale, self._yscale
        label_z = getattr(self, 'label_z', '')

        for p in (self._ruler_p1, self._ruler_p2):
            ix = int(round((p['x'] - x0) / xs))
            iy = int(round((p['y'] - y0) / ys))
            if 0 <= ix < nx and 0 <= iy < ny:
                p['z'] = float(image[ix, iy])
                p['z_text'] = pg.siFormat(p['z'], suffix=label_z, precision=5)
            else:
                p['z'] = None
                p['z_text'] = ''

        # Only refresh the text — keep the anchor/position locked from the
        # original drag so the label doesn't jump when ΔZ width changes.
        if self._ruler_label is not None:
            self._ruler_label.setText(
                self._ruler_label_text(self._ruler_p1, self._ruler_p2)
            )

    def _ruler_label_text(self, p1, p2):
        label_x = getattr(self, 'label_x', '')
        label_y = getattr(self, 'label_y', '')
        label_z = getattr(self, 'label_z', '')

        dx_text = pg.siFormat(p2['x'] - p1['x'], suffix=label_x, precision=5)
        dy_text = pg.siFormat(p2['y'] - p1['y'], suffix=label_y, precision=5)

        lines = [f"ΔX: {dx_text}", f"ΔY: {dy_text}"]
        if p1['z'] is not None and p2['z'] is not None:
            dz_text = pg.siFormat(p2['z'] - p1['z'], suffix=label_z, precision=5)
            lines.append(f"ΔZ: {dz_text}")

        p1_z = f", Z: {p1['z_text']}" if p1['z_text'] else ''
        p2_z = f", Z: {p2['z_text']}" if p2['z_text'] else ''
        lines.append(f"P1: ({p1['x_text']}, {p1['y_text']}{p1_z})")
        lines.append(f"P2: ({p2['x_text']}, {p2['y_text']}{p2_z})")
        return "\n".join(lines)
