import atomize.general_modules.general_functions as general
import atomize.device_modules.Agilent_34410A as ag


dmm = ag.Agilent_34410A()
dmm.multimeter_reset()
dmm.multimeter_mode('DC Voltage')
dmm.multimeter_range('10 V')
dmm.multimeter_nplc(1)
dmm.multimeter_auto_zero('On')
dmm.multimeter_sample_count(1)
dmm.multimeter_trigger_source('Immediate')

reading = dmm.multimeter_get_data()
general.message(dmm.multimeter_name(), reading)
general.message_test(dmm.multimeter_name(), reading)

dmm.multimeter_sample_count(10)
dmm.multimeter_trigger_source('Bus')
dmm.multimeter_start()
dmm.multimeter_trigger()
readings = dmm.multimeter_fetch()
general.message(readings)
general.message_test(readings)
dmm.multimeter_stop()
dmm.close_connection()
