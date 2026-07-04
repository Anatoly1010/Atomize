#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import atexit
import threading
from threading import Thread
import configparser
import numpy as np
import atomize.main.local_config as lconf
from atomize.main.client import LivePlotClient

# Test run parameters
test_flag = sys.argv[1] if len(sys.argv) > 1 else 'None'

_plotter_instance = None

# When True, plot_1d / plot_2d default to the non-blocking coalescing worker even
# without an explicit `pr=` handle (see set_plotting_async). Per-process: a
# control-center acquisition worker flips it on at entry so its whole plot path
# is the "thread version"; experimental scripts leave it off and opt in per call.
_async_default = False

def _plotter():
    """Lazy LivePlotClient singleton. Connects on first call, not at import."""
    global _plotter_instance
    if _plotter_instance is None:
        _plotter_instance = LivePlotClient()
    return _plotter_instance

def set_plotting_async(enabled=True):
    """Make plot_1d / plot_2d default to the non-blocking coalescing worker for
    THIS process, so callers don't have to thread a `pr=` handle through every
    call. Frames coalesce per plot name (only the freshest is drawn) and the
    measurement loop is no longer paced by the GUI. Call once at the start of an
    acquisition worker. append_1d stays synchronous regardless — it is
    incremental, so a dropped frame would drop points. Explicit `pr=` still wins."""
    global _async_default
    _async_default = bool(enabled)

def _in_test():
    return test_flag == 'test'

_MESSAGE_ARRAY_THRESHOLD = 1000
_MESSAGE_MAX_CHARS = 8000

def _format_message(text):
    if len(text) == 1:
        if isinstance(text[0], np.ndarray):
            content = np.array2string(
                text[0],
                separator=',',
                threshold=_MESSAGE_ARRAY_THRESHOLD,
                max_line_width=np.inf,
            )
            content = content.replace('\n', '')
        else:
            content = str(text[0]).replace('\n', '')
    else:
        content = str(text)
    if len(content) > _MESSAGE_MAX_CHARS:
        content = content[:_MESSAGE_MAX_CHARS] + f'...(truncated, {len(content)} chars)'
    return content

def message(*text):
    if _in_test():
        return
    print(f'print {_format_message(text)}', flush=True)

def message_test(*text):
    if not _in_test():
        return
    print(f'print {_format_message(text)}', flush=True)

def wait(interval):
    time_dict = {'ks': 0.001, 's': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000, 'ps': 1000000000000, }
    temp = interval.split(' ')
    tm = float(temp[0])
    scal = temp[1]

    if _in_test():
        assert (scal in time_dict), "Incorrect dimension of time to wait"
        return

    if scal in time_dict:
        time.sleep(tm / time_dict[scal])
    else:
        message("Incorrect dimension of time to wait")

def to_infinity():
    limit = 50 if _in_test() else None
    index = 0
    while limit is None or index < limit:
        yield index
        index += 1

def scans(num_of_scans):
    limit = 1 if _in_test() else num_of_scans
    index = 1
    while index <= limit:
        yield index
        index += 1

# Plotting guards. Above these sizes the data is strided down for *display only*
# (the arrays held by the script and written to disk are never modified). The
# caps sit well under the LivePlotClient shared-memory limit and keep pyqtgraph
# from freezing the GUI on multi-million-point payloads.
_PLOT_MAX_POINTS_1D = 2_000_000
_PLOT_MAX_CELLS_2D = 4_000_000

def _notify(text):
    """Push a line to the main-window log regardless of test/normal mode."""
    print(f'print {text}', flush=True)

def _safe_call(target, args, kwargs):
    """Run a plotter call, turning any failure into a log line instead of a
    crash. Used for both the sync and the threaded (`pr=`) paths so a plotting
    error can never kill the experiment or vanish inside a background Thread."""
    try:
        target(*args, **kwargs)
    except Exception as e:
        _notify(f"plot failed: {e!r}")


class _AsyncPlotHandle:
    """Returned by the async (`pr=`) plot path. The coalescing worker owns
    ordering now, so join() is a no-op kept only for API compatibility with the
    old per-call Thread return (a script may still call `pr.join()`)."""
    __slots__ = ()
    def join(self, *args, **kwargs):
        return None

_ASYNC_HANDLE = _AsyncPlotHandle()


class _PlotWorker:
    """One daemon thread that serialises the async (`pr=`) plot sends and
    *coalesces per plot name*: if a frame for a given plot name is still pending
    when a newer one arrives, the newer replaces it. So a slow GUI can no longer
    pace the experiment — the measurement thread just drops the frame into a slot
    (~microseconds) and moves on, and only the freshest state of each live plot
    is drawn. Superseded intermediate frames are skipped; this is safe because
    the `pr=` path only does full-array replots (plot_1d / plot_2d / label) whose
    data lives in the script arrays and on disk. The incremental append_1d path
    has no `pr=` and stays synchronous, so no appended points are ever dropped."""

    def __init__(self):
        self._cond = threading.Condition()
        self._pending = {}      # name -> (target, args, kwargs); dict keeps
                                # insertion order and coalesces on re-key
        self._busy = False
        self._closed = False
        self._thread = threading.Thread(target=self._run,
                                        name='AtomizePlotWorker', daemon=True)
        self._thread.start()

    def submit(self, key, target, args, kwargs):
        with self._cond:
            # Re-assigning an existing key updates the value without moving its
            # position, so distinct plots stay FIFO while same-name frames merge.
            self._pending[key] = (target, args, kwargs)
            self._cond.notify()

    def _run(self):
        while True:
            with self._cond:
                while not self._pending and not self._closed:
                    self._cond.wait()
                if self._closed and not self._pending:
                    return
                key = next(iter(self._pending))
                target, args, kwargs = self._pending.pop(key)
                self._busy = True
            _safe_call(target, args, kwargs)
            with self._cond:
                self._busy = False
                self._cond.notify_all()   # wake flush() waiters

    def flush(self, timeout=5.0):
        """Block until the queue has drained and the in-flight send finished, so
        the final frame of a run is actually drawn. Bounded by `timeout` (each
        send is itself bounded by the client's socket timeout), so a dead GUI
        can't hang process exit."""
        deadline = time.monotonic() + timeout if timeout is not None else None
        with self._cond:
            while self._pending or self._busy:
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    return
                self._cond.wait(remaining)

_plot_worker = None

def _get_plot_worker():
    """Lazy singleton worker; registers a flush at interpreter exit so the last
    live-plot frame is not lost when the script ends."""
    global _plot_worker
    if _plot_worker is None:
        _plot_worker = _PlotWorker()
        atexit.register(_plot_worker.flush)
    return _plot_worker

def _downsample_1d(xd, yd, max_points):
    """Stride (xd, yd) down so each curve has <= max_points samples. Returns
    (xd, yd, step); step == 1 leaves the inputs untouched. yd may be 1D (one
    curve) or 2D / a tuple of two arrays (two curves) — the last axis is the
    sample axis in every case, and xd is strided to match."""
    shape = np.shape(yd)
    n = shape[-1] if shape else 0
    if n <= max_points:
        return xd, yd, 1
    step = int(np.ceil(n / max_points))
    return np.asarray(xd)[..., ::step], np.asarray(yd)[..., ::step], step

def _downsample_2d(data, start_step, max_cells):
    """Stride a 2D image down to <= max_cells, scaling start_step so the axes
    stay correct. Returns (data, start_step, factor); factor == 1 is a no-op.

    A 3D array is treated as a stack of frames (n_frames, ny, nx) — e.g. the
    real/imag pair of a complex 2D result that plot_2d shows as toggleable
    frames; only the two image axes are strided and every frame is kept."""
    arr = np.asarray(data)
    if arr.ndim >= 3:
        size = int(np.prod(arr.shape[-2:]))
        if size <= max_cells:
            return data, start_step, 1
        factor = int(np.ceil(np.sqrt(size / max_cells)))
        data_ds = arr[..., ::factor, ::factor]
    else:
        size = int(np.prod(arr.shape)) if arr.shape else 0
        if size <= max_cells:
            return data, start_step, 1
        factor = int(np.ceil(np.sqrt(size / max_cells)))
        data_ds = arr[::factor, ::factor]
    if start_step is None:
        new_ss = ((0, factor), (0, factor))
    else:
        (x0, xs), (y0, ys) = start_step
        new_ss = ((x0, xs * factor), (y0, ys * factor))
    return data_ds, new_ss, factor

def _dispatch_plot(target, args, kwargs, pr, get_first=None):
    """
    Call `target(*args, **kwargs)` synchronously (`pr == 'None'`), or hand it to
    the coalescing plot worker when `pr` is anything else. Both paths go through
    `_safe_call`, so a plotter error becomes a log line rather than crashing the
    script or being swallowed by a thread.

    The async path is non-blocking: the frame is dropped into a per-name slot and
    the worker draws the freshest one, so a slow GUI never paces the experiment.
    Superseded intermediate frames are skipped (safe — see `_PlotWorker`).

    If `get_first` is provided, skip the call when it returns NaN or raises
    IndexError/TypeError — this is what makes a live `digitizer_get_curve` that
    returns None (no new buffer this call) skip the replot. The check runs here,
    on the caller's thread, so a None frame is never queued. Returns an async
    handle (when async) or None.
    """
    if get_first is not None:
        try:
            if np.isnan(get_first()):
                return None
        except (IndexError, TypeError) as e:
            _notify(f"plot skipped: empty or non-numeric data ({e!r})")
            return None

    if pr == 'None':
        _safe_call(target, args, kwargs)
        return None

    # Coalesce per plot name (args[0] is the plot id for plot_xy/plot_z/label);
    # fall back to the target name for anything without a string id.
    key = args[0] if args and isinstance(args[0], str) else getattr(target, '__name__', 'plot')
    _get_plot_worker().submit(key, target, args, kwargs)
    return _ASYNC_HANDLE

def _plot_1d_impl(strname, xd, yd, label, xname, xscale, yname, yscale,
                  scatter, timeaxis, vline, pr, text):
    xd, yd, step = _downsample_1d(xd, yd, _PLOT_MAX_POINTS_1D)
    if step > 1:
        _notify(f"plot '{strname}': downsampled {step}x for display "
                f"(> {_PLOT_MAX_POINTS_1D} points); saved data is unaffected")
    kwargs = {'label': label, 'xname': xname, 'xscale': xscale,
              'yname': yname, 'yscale': yscale, 'scatter': scatter,
              'timeaxis': timeaxis, 'vline': vline, 'text': text}
    return _dispatch_plot(_plotter().plot_xy, (strname, xd, yd), kwargs, pr,
                          lambda: np.take(yd, 0))

def plot_1d(strname, xd, yd, label='label', xname='X',
        xscale='arb. u.', yname='Y', yscale='arb. u.', scatter='False',
        timeaxis='False', vline='False', pr = 'None', text=''):

    if _in_test():
        return None
    if pr == 'None' and _async_default:
        pr = _ASYNC_HANDLE
    return _plot_1d_impl(strname, xd, yd, label, xname, xscale, yname, yscale,
                         scatter, timeaxis, vline, pr, text)

def plot_1d_test(strname, xd, yd, label='label', xname='X',
        xscale='arb. u.', yname='Y', yscale='arb. u.', scatter='False',
        timeaxis='False', vline='False', pr = 'None', text=''):

    if not _in_test():
        return None
    return _plot_1d_impl(strname, xd, yd, label, xname, xscale, yname, yscale,
                         scatter, timeaxis, vline, pr, text)

def append_1d(strname, value, start_step=(0, 1), label='label', xname='X',
    xscale='arb. u.', yname='Y', yscale='arb. u.', scatter='False',
    timeaxis='False', vline='False'):

    if _in_test():
        return
    _plotter().append_y(strname, value, start_step=start_step, label=label, xname=xname,
            xscale=xscale, yname=yname, yscale=yscale,
            timeaxis=timeaxis, vline=vline)

def _plot_2d_impl(strname, data, start_step, xname, xscale, yname, yscale,
                  zname, zscale, pr, text):
    data, start_step, factor = _downsample_2d(data, start_step, _PLOT_MAX_CELLS_2D)
    if factor > 1:
        _notify(f"plot '{strname}': downsampled {factor}x per axis for display "
                f"(> {_PLOT_MAX_CELLS_2D} cells); saved data is unaffected")
    kwargs = {'start_step': start_step, 'xname': xname, 'xscale': xscale,
              'yname': yname, 'yscale': yscale, 'zname': zname,
              'zscale': zscale, 'text': text}
    return _dispatch_plot(_plotter().plot_z, (strname, data), kwargs, pr,
                          lambda: np.asarray(data).flat[0])

def plot_2d(strname, data, start_step=None,
    xname='X', xscale='arb. u.', yname='Y', yscale='arb. u.', zname='Z',
    zscale='arb. u.', pr='None', text=''):

    if _in_test():
        return None
    if pr == 'None' and _async_default:
        pr = _ASYNC_HANDLE
    return _plot_2d_impl(strname, data, start_step, xname, xscale, yname,
                         yscale, zname, zscale, pr, text)

def plot_2d_test(strname, data, start_step=None,
    xname='X', xscale='arb. u.', yname='Y', yscale='arb. u.', zname='Z',
    zscale='arb. u.', pr='None', text=''):

    if not _in_test():
        return None
    return _plot_2d_impl(strname, data, start_step, xname, xscale, yname,
                         yscale, zname, zscale, pr, text)

def append_2d(strname, data, start_step=None,
    xname='X', xscale='arb. u.', yname='Y', yscale='arb. u.',
    zname='Z', zscale='arb. u.'):

    if _in_test():
        return
    _plotter().append_z(strname, data, start_step=start_step,
            xname=xname, xscale=xscale, yname=yname, yscale=yscale,
            zname=zname, zscale=zscale)

def text_label(strlabel, text, value, pr='None'):
    if _in_test():
        return None
    combined = str(text) + str(value)
    return _dispatch_plot(_plotter().label, (strlabel, combined), {}, pr)

def plot_remove(strname):
    if _in_test():
        return
    _plotter().remove(strname)

def round_to_closest(x, y):
    """
    A function to round x to be divisible by y
    """
    return int( y * ( ( x // y) + (x % y > 0) ) )

def const_shift(x, shift):
    """
    A function to add a specified shift to x
    """
    #'800 ns' -> '1294 ns'
    return str( int(x.split(' ')[0]) + shift ) + ' ns'

def numpy_round(x, base):
    """
    A function to round x to be divisible by y
    """
    return base * np.round(x / base)

_bot_cache = None

def _get_bot():
    """Lazy TeleBot singleton + chat id loaded from main_config.ini."""
    global _bot_cache
    if _bot_cache is None:
        import telebot
        path_config_file, _ = lconf.load_config()
        config = configparser.ConfigParser()
        config.read(path_config_file)
        cfg = config['DEFAULT']
        bot = telebot.TeleBot(str(cfg['telegram_bot_token']))
        _bot_cache = (bot, cfg['message_id'])
    return _bot_cache

def bot_message(*text):
    if _in_test():
        return
    bot, chat_id = _get_bot()
    payload = str(text[0]) if len(text) == 1 else str(text)
    bot.send_message(chat_id, payload)

def fmt(raw_str, w):
    """Left-pad the "name:" half of a "name: value" string to width `w`."""
    if ':' in raw_str:
        name, val = raw_str.split(':', 1)
        return f"{name.strip() + ':':<{w}} {val.strip()}"
    return raw_str