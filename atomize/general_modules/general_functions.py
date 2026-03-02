#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
from threading import Thread
import configparser
import numpy as np
import atomize.main.local_config as lconf
from atomize.main.client import LivePlotClient
#from liveplot import LivePlotClient

# Test run parameters
if len(sys.argv) > 1:
    test_flag = sys.argv[1]
else:
    test_flag = 'None'
    plotter = LivePlotClient()

def message(*text):
    if test_flag != 'test':
        if len(text) == 1:
            if isinstance(text[0], np.ndarray):
                content = np.array2string(
                    text[0], 
                    separator=',', 
                    threshold=np.inf, 
                    max_line_width=np.inf
                )
                content = content.replace('\n', '')
                print(f'print {content}', flush=True)
            else:
                content = str(text[0]).replace('\n', '')
                print(f'print {content}', flush=True)
        else:
            print(f'print {text}', flush=True)
    elif test_flag == 'test':
        pass

def message_test(*text):
    if test_flag != 'test':
        pass
    elif test_flag == 'test':
        if len(text) == 1:
            if isinstance(text[0], np.ndarray):
                content = np.array2string(
                    text[0], 
                    separator=',', 
                    threshold=np.inf, 
                    max_line_width=np.inf
                )
                content = content.replace('\n', '')
                print(f'print {content}', flush=True)
            else:
                content = str(text[0]).replace('\n', '')
                print(f'print {content}', flush=True)
        else:
            print(f'print {text}', flush=True)

def wait(interval):
    time_dict = {'ks': 0.001, 's': 1, 'ms': 1000, 'us': 1000000, 'ns': 1000000000, 'ps': 1000000000000, }

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
        temp = interval.split(' ')
        tm = float(temp[0])
        scal = temp[1]
        assert (scal in time_dict), "Incorrect dimension of time to wait"

def to_infinity():
    if test_flag != 'test':
        index = 0
        while True:
            yield index
            index += 1
    elif test_flag == 'test':
        index = 0
        while index < 50:
            yield index
            index += 1

def scans(num_of_scans):
    if test_flag != 'test':
        index = 1
        while index <= num_of_scans:
            yield index
            index += 1
    elif test_flag == 'test':
        index = 1
        while index <= 1:
            yield index
            index += 1

def plot_1d(strname, xd, yd, label='label', xname='X', 
        xscale='arb. u.', yname='Y', yscale='arb. u.', scatter='False', 
        timeaxis='False', vline='False', pr = 'None', text=''):

    if test_flag != 'test':
        
        if pr == 'None':
            try:
                if not np.isnan(np.take(yd, 0)):
                    plotter.plot_xy(strname, xd, yd, label=label, xname=xname,
                                    xscale=xscale, yname=yname, yscale=yscale, 
                                    scatter=scatter, timeaxis=timeaxis, vline=vline, 
                                    text=text)
            except (IndexError, TypeError):
                pass
        else:
            try:
                pr.join()
            except (AttributeError, NameError, TypeError):
                pass

            try:
                if not np.isnan(np.take(yd, 0)):
                    p1 = Thread(target=plotter.plot_xy, args=(strname, xd, yd, ), 
                        kwargs={'label': label, 'xname': xname, 
                        'xscale': xscale, 'yname': yname, 'yscale': yscale, 
                        'scatter': scatter, 'timeaxis': timeaxis, 
                        'vline': vline, 'text': text, } )
                    p1.start()
                    return p1
            except (IndexError, TypeError):
                pass

    elif test_flag == 'test':
        pass

def append_1d(strname, value, start_step=(0, 1), label='label', xname='X',
    xscale='arb. u.', yname='Y', yscale='arb. u.', scatter='False', 
    timeaxis='False', vline='False'):

    if test_flag != 'test':
        plotter.append_y(strname, value, start_step=start_step, label=label, xname=xname,
                xscale=xscale, yname=yname, yscale=yscale, 
                timeaxis=timeaxis, vline=vline)

    elif test_flag == 'test':
        pass

def plot_2d(strname, data, start_step=None,
    xname='X', xscale='arb. u.', yname='Y', yscale='arb. u.', zname='Z', 
    zscale='arb. u.', pr='None', text=''):
    
    if test_flag != 'test':
        if pr == 'None':
            try:
                if not np.isnan(data.flat[0]):
                    plotter.plot_z(strname, data, start_step=start_step,
                            xname=xname, xscale=xscale, yname=yname, yscale=yscale, 
                            zname=zname, zscale=zscale, text=text)
                else:
                    pass
            except (IndexError, TypeError):
                pass
        
        else:
            try:
                pr.join()
            except ( AttributeError, NameError, TypeError ):
                pass
            
            try:
                if not np.isnan(data.flat[0]):
                    p1 = Thread(target=plotter.plot_z, args=(strname, data, ), 
                        kwargs={'start_step': start_step, 'xname': xname, 
                        'xscale': xscale, 'yname': yname, 'yscale': yscale, 
                        'zname': zname, 'zscale': zscale, 'text': text, } )
                    p1.start()
                    return p1
                else:
                    pass

            except (IndexError, TypeError):
                pass

    elif test_flag == 'test':
        pass

def append_2d(strname, data, start_step=None,
    xname='X', xscale='arb. u.', yname='Y', yscale='arb. u.', 
    zname='Z', zscale='arb. u.'):

    if test_flag != 'test':
        plotter.append_z(strname, data, start_step=start_step,
                xname=xname, xscale=xscale, yname=yname, yscale=yscale, 
                zname=zname, zscale=zscale)

    elif test_flag == 'test':
        pass

def text_label(strlabel, text, value, pr='None'):
    if test_flag != 'test':
        
        if pr == 'None':
            plotter.label(strlabel, str( str(text) + str(value) ) )
        else:
            try:
                pr.join()
            except ( AttributeError, NameError, TypeError ):
                pass
            
            p1 = Thread(target=plotter.label, args=(strlabel, str( str(text) + str(value) ), ) )
            p1.start()
            #p1.join()

            return p1

    elif test_flag == 'test':
        pass

def plot_remove(strname):
    if test_flag != 'test':
        plotter.remove(strname)

    elif test_flag == 'test':
        pass

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

def bot_message(*text):
    import telebot
    # configuration data
    #path_to_main = os.path.abspath(os.path.join(os.path.dirname(__file__ ), '..'))
    #path_config_file = os.path.join(path_to_main, 'atomize/config.ini')
    path_config_file, path_config2 = lconf.load_config()
    config = configparser.ConfigParser()
    config.read(path_config_file)

    bot = telebot.TeleBot(str(config['DEFAULT']['telegram_bot_token']))
    chat_id = config['DEFAULT']['message_id']
    if test_flag != 'test':
        if len(text) == 1:
            bot.send_message(chat_id, str(text[0]))
            bot.send_message(760577263, str(text[0]))
        else:
            bot.send_message(chat_id, str(text))
            bot.send_message(760577263, str(text))
    elif test_flag == 'test':
        pass

def fmt(raw_str, w):
    if ':' in raw_str:
        name, val = raw_str.split(':', 1)
        return f"{name.strip() + ':':<{w}} {val.strip()}"
    return raw_str

def main():
    pass

if __name__ == "__main__":
    main()