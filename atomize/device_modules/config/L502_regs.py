def MEGA(m): return int( 1000 * 1000 * (m) )

X502_REF_FREQ_2000KHZ  = 2000000  # /**< 2 MHz */
X502_REF_FREQ_1500KHZ  = 1500000  # /**< 1.5 MHz */

X502_SYNC_INTERNAL        = 0 #  /**< Internal */
X502_SYNC_EXTERNAL_MASTER = 1 #  /**< External */
X502_SYNC_DI_SYN1_RISE    = 2 #  /**< Rise of DI_SYN1 */
X502_SYNC_DI_SYN1_FALL    = 3 #  /**< Fall of DI_SYN1 */
X502_SYNC_DI_SYN2_RISE    = 6 #  /**< Rise of DI_SYN2 */
X502_SYNC_DI_SYN2_FALL    = 7 #  /**< Fall of DI_SYN2 */

X502_STREAM_ADC  = 0x01 # /**< ADC */
X502_STREAM_DIN  = 0x02 # /**< digital inputs */
X502_STREAM_DAC1 = 0x10 # /**< DAC 1 */
X502_STREAM_DAC2 = 0x20 # /**< DAC 2 */
X502_STREAM_DOUT = 0x40 # /**< digital outputs */

X502_STREAM_ALL_IN = X502_STREAM_ADC | X502_STREAM_DIN #/** All inputs */
X502_STREAM_ALL_OUT = X502_STREAM_DAC1 | X502_STREAM_DAC2 | X502_STREAM_DOUT #/** All outputs */

X502_MODE_FPGA  = 0 # /**< PLS */
X502_MODE_DSP   = 1 # /**< BlackFin CPU with appropriate firmware */
X502_MODE_DEBUG = 2 # /**< debug */

X502_LCH_MODE_COMM = 0 # /**< Common ground; 32 channels */
X502_LCH_MODE_DIFF = 1 # /**< Diffrential; 16 channels */
X502_LCH_MODE_ZERO = 2 # /**< Zero */

X502_ADC_RANGE_10 = 0 # /**< Range +/-10V */
X502_ADC_RANGE_5  = 1 # /**<  +/-5V */
X502_ADC_RANGE_2  = 2 # /**<  +/-2V */
X502_ADC_RANGE_1  = 3 # /**<  +/-1V */
X502_ADC_RANGE_05 = 4 # /**<  +/-0.5V */
X502_ADC_RANGE_02 = 5 # /**<  +/-0.2V */

# /** Convert counts to Volts */
X502_PROC_FLAGS_VOLT            = 0x00000001
# 
X502_PROC_FLAGS_DONT_CHECK_CH   = 0x00010000
