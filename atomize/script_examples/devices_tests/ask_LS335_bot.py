import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Lakeshore_335 as ls
import sys
import telebot
import datetime

bot = telebot.TeleBot('')

xs = []
ys = []

i = 0;

ls335 = ls.Lakeshore_335()

if len(sys.argv) > 1:
        test_flag = sys.argv[1]
else:
    test_flag = 'None'

while i < 500:

    i += 1

    if test_flag == 'test':
        pass
    else:
        bot.send_message(406712189, datetime.datetime.now())
        bot.send_message(406712189, 'B: ' + str(ls335.tc_temperature('B')))
        bot.send_message(406712189, 'A: ' + str(ls335.tc_temperature('A')))

    xs = np.append(xs, i);
    ys = np.append(ys, ls335.tc_temperature('B'));
    general.plot_1d('Temperature', xs, ys, label='test data')
    general.wait('180 s')


