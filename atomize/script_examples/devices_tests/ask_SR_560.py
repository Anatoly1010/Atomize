import atomize.general_modules.general_functions as general
import atomize.device_modules.SR_560 as sr


sr560 = sr.SR_560()
sr560.preamplifier_input_source('A-B')
sr560.preamplifier_input_coupling('DC')
sr560.preamplifier_gain_mode('Low Noise')
sr560.preamplifier_gain(100)
sr560.preamplifier_filter_mode('Bandpass')
sr560.preamplifier_high_pass_frequency('10 Hz')
sr560.preamplifier_low_pass_frequency('100 kHz')
sr560.preamplifier_invert('Off')
sr560.preamplifier_vernier('Off')
sr560.preamplifier_blanking('Off')

general.message(sr560.preamplifier_name(), sr560.preamplifier_gain())
general.message_test(sr560.preamplifier_name(), sr560.preamplifier_gain())
sr560.close_connection()
