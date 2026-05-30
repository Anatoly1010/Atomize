#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
from threading import Thread
import configparser
import numpy as np
import atomize.main.local_config as lconf
from atomize.main.client import LivePlotClient

# Test run parameters
test_flag = sys.argv[1] if len(sys.argv) > 1 else 'None'

_plotter_instance = None

def _plotter():
    """Lazy LivePlotClient singleton. Connects on first call, not at import."""
    global _plotter_instance
    if _plotter_instance is None:
        _plotter_instance = LivePlotClient()
    return _plotter_instance

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
    Call `target(*args, **kwargs)` synchronously, or on a background Thread
    when `pr` is not the sentinel string 'None' (joining the prior Thread first).
    Both paths go through `_safe_call`, so a plotter error becomes a log line
    rather than crashing the script or being swallowed by a Thread.
    If `get_first` is provided, skip the call when it returns NaN or raises
    IndexError/TypeError. Returns the Thread (when async) or None.
    """
    if pr != 'None':
        try:
            pr.join()
        except (AttributeError, NameError, TypeError):
            pass

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

    p1 = Thread(target=_safe_call, args=(target, args, kwargs))
    p1.start()
    return p1

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