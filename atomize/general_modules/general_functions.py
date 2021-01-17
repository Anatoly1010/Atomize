#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import socket
import threading
from liveplot import LivePlotClient

time_dict = {'ks': 0.001, 's': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000, 'ps': 1000000000000, };

# Test run parameters
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'
    plotter = LivePlotClient()

def message(*text):
    if test_flag != 'test':
        sock = socket.socket()
        sock.connect(('localhost', 9091))
        if len(text) == 1:
            sock.send(str(text[0]).encode())
            sock.close()
        else:
            sock.send(str(text).encode())
            sock.close()
    elif test_flag == 'test':
        pass

def wait(interval):
    if test_flag != 'test':
        temp = interval.split(' ')
        tm = float(temp[0])
        scal = temp[1]
        if scal in time_dict:
            coef = time_dict[scal]
            time.sleep(tm/coef)
        else:
            message("Incorrect dimension of time to wait")
    elif test_flag == 'test':
        pass

def plot_1d(strname, xd, yd, label='label', xname='X',\
 xscale='arb. u.', yname='Y', yscale='arb. u.', scatter='False'):

    if test_flag != 'test':
        plotter.plot_xy(strname, xd, yd, label=label, xname=xname,\
            xscale=xscale, yname=yname, yscale=yscale, scatter=scatter)

    elif test_flag == 'test':
        pass

def append_1d(strname, value, start_step=(0, 1), label='label', xname='X',\
 xscale='arb. u.', yname='Y', yscale='arb. u.'):

    if test_flag != 'test':
        plotter.append_y(strname, value, start_step=start_step, label=label, xname=xname,\
            xscale=xscale, yname=yname, yscale=yscale)

    elif test_flag == 'test':
        pass

def plot_2d(strname, data, start_step=None,\
 xname='X', xscale='arb. u.', yname='Y', yscale='arb. u.', zname='Z', zscale='arb. u.'):

    if test_flag != 'test':
        plotter.plot_z(strname, data, start_step=start_step,\
            xname=xname, xscale=xscale, yname=yname, yscale=yscale, zname=zname, zscale=zscale)

    elif test_flag == 'test':
        pass

def append_2d(strname, data, start_step=None,\
 xname='X', xscale='arb. u.', yname='Y', yscale='arb. u.', zname='Z', zscale='arb. u.'):

    if test_flag != 'test':
        plotter.append_z(strname, data, start_step=start_step,\
            xname=xname, xscale=xscale, yname=yname, yscale=yscale, zname=zname, zscale=zscale)

    elif test_flag == 'test':
        pass

def text_label(strlabel, text, value):
    if test_flag != 'test':
        plotter.label(strlabel, str(str(text) + ' %d' %value))

    elif test_flag == 'test':
        pass

def plot_remove(strname):
    if test_flag != 'test':
        plotter.remove(strname)

    elif test_flag == 'test':
        pass

def main():
    pass

if __name__ == "__main__":
    main()