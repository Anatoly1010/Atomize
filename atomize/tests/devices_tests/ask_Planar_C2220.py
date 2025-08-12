import time
import numpy as np
import atomize.general_modules.general_functions as general
import atomize.device_modules.Planar_C2220 as c2220

xs = np.array([])
ys = []

C2220 = c2220.Planar_C2220()


# SOURce<Ch>:POWer[:LEVel][:IMMediate][:AMPLitude] <power>
#Устанавливает или считывает уровень мощности всех портов при сканировании по частоте.
#Разрешение 0.01 дБм
general.message( C2220.vector_analyzer_command("SOURce1:POWer 0") )

#Ch 1 - 16
general.message( C2220.vector_analyzer_query("1:BANDwidth?") )
#C2220.vector_analyzer_command("SENSe1:BANDwidth 2000")
#general.message( C2220.vector_analyzer_query("SENSe1:BANDwidth?") )

general.message( C2220.vector_analyzer_query("SENSe1:FREQuency:CENTer?") )

general.message( C2220.vector_analyzer_query("SENSe1:FREQuency:SPAN?") )

C2220.vector_analyzer_command("SENSe1:SWEep:POINts 80")
#better not to change
#general.message( C2220.vector_analyzer_query("SENSe1:SWEep:CW:TIME?") )


#TRIG

#TRIGger[:SEQuence]:SOURce <char>
#{INT|EXT|MAN|BUS}
#TRIG:SOUR EXT
C2220.vector_analyzer_command("TRIGger:SOURce BUS")
#INIT
#INITiate<Ch>:CONTinuous {OFF|ON|0|1}
C2220.vector_analyzer_command("INITiate1:CONTinuous 0")
#INITiate<Ch>[:IMMediate]
#Переводит канал в режим инициации "Однократно". Канал должен находиться в состоянии "Остановлен", иначе возникает ошибка и команда игнорируется. Канал переходит в состояние "Остановлен" в результате команды INIT:CONT OFF.
C2220.vector_analyzer_command("INIT1")

#TRIGger[:SEQuence]:SINGle
#Вырабатывает сигнал триггера и запускает сканирование при соблюдении следующих условий:
#1. Источник триггера установлен командой TRIG:SOUR BUS в состояние "Шина", в противном случае возникает ошибка и команда игнорируется.
#2. Анализатор должен находиться в состоянии "Ожидание триггера", если анализатор находится в состоянии "Цикл измерения" или "Стоп" возникает ошибка и команда игнорируется.
#В отличие от команды TRIG, данная команда является незавершенной до окончания сканирования. Для ожидания окончания сканирования, инициированного командой TRIG:SING может быть использован запрос *OPC?.
C2220.vector_analyzer_command("TRIG:SING")

general.message( C2220.vector_analyzer_query("*OPC?"))

#general.message( C2220.vector_analyzer_name() )

# freq axis
#general.message( C2220.vector_analyzer_query("SENSe1:FREQuency:DATA?") )

"""
<numeric 2n–1> реальная часть исправленных измерений;
<numeric 2n> мнимая часть исправленных измерений.

<char> определяет S-параметры:
S11, S21, S12, S22
<char> определяет тестовый приемник:
A(1), A(2), B(1), B(2)
где первый индекс - номер порта приемника, а второй индекс - номер порта источника.

<char> определяет опорный приемник:
R11, R21, R12, R22
где первый индекс - номер порта приемника, а второй индекс - номер порта источника.


Current data; with 0.
"""
xs = C2220.vector_analyzer_query("SENSe1:DATA:RAWData? S11")
general.message( xs )

#sr860.lock_in_get_data()

#C2220.lock_in_time_constant('1000 ms')
#i = 0

#while i < 6:
#   sr860.lock_in_ref_frequency(100000 + i*10000)
#   general.plot_1d('SR 860', xs, ys, label='test data')
#   general.wait('300 ms')
#   i += 1

#Plot_xy Test
#for i in range(100):
#   start_time = time.time()
#    xs = np.append(xs, i);
    #ys = np.append(ys, sr860.lock_in_get_data());
#    ys = np.append(ys, np.random.randint(10,size=1));
#    general.plot_1d('SR 860', xs, ys, label='test data')
#    general.wait('300 ms')

#   general.message(str(time.time() - start_time))


#sr.close_connection()


# Append_y Test
#for i in range(100):
#    start_time = time.time()
#    general.append_1d('Append Y Test', sr.lock_in_get_data(), start_step=(0, 1), label='test data')
#    general.wait('30 ms')

#    general.message(str(time.time() - start_time))


#sr.close_connection()