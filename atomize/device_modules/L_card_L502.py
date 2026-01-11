#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import time
import ctypes
import numpy as np
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general
from atomize.device_modules.config.L502_regs import *

# ------------------------------ Structures of L502 ------------------------------
# handle of the device is an opaque pointer
class _Opaque(ctypes.Structure):
    pass

class Read_x502(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('arr', ctypes.c_uint32 * 1),
                ('devs', ctypes.c_uint32)]

class t_x502_cbr_coef(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('offs', ctypes.c_double),
                ('k', ctypes.c_double)]

class t_x502_cbr(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('adc', t_x502_cbr_coef*6),
                ('rez1', ctypes.c_uint32*64),
                ('dac', t_x502_cbr_coef*2),
                ('rez2', ctypes.c_uint32*20)]

class t_x502_info(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('BrdName', ctypes.c_char*32),
                ('SerNum', ctypes.c_char*32),
                ('devflags', ctypes.c_uint32),
                ('fpga_ver', ctypes.c_uint16),
                ('plda_ver', ctypes.c_uint8),
                ('board_rev', ctypes.c_uint8),
                ('mcu_firmware_ver', ctypes.c_uint32),
                ('factory_mac', ctypes.c_uint8*6),
                ('rezerv', ctypes.c_uint8*110),
                ('cbr', t_x502_cbr)]
# --------------------------------------------------------------------------------

class L_card_L502:

    def __init__(self):

        self.path_to_file = os.path.abspath(os.path.realpath(os.path.dirname(__file__)))
        self.error_dict = {'X502_ERR_OK': 0, 'X502_ERR_INVALID_HANDLE': -1, 'X502_ERR_MEMORY_ALLOC': -2, 'X502_ERR_ALREADY_OPENED': -3, 
                                     'X502_ERR_DEVICE_NOT_FOUND': -4, 'X502_ERR_DEVICE_ACCESS_DENIED': -5, 'X502_ERR_DEVICE_OPEN': -6, 
                                     'X502_ERR_INVALID_POINTER': -7, 
                                     'X502_ERR_STREAM_IS_RUNNING': -8, 'X502_ERR_RECV': -9, 'X502_ERR_SEND': -10, 
                                     'X502_ERR_STREAM_OVERFLOW': -11, 'X502_ERR_UNSUP_STREAM_MSG': -12, 'X502_ERR_MUTEX_CREATE': -13, 
                                     'X502_ERR_MUTEX_INVALID_HANDLE': -14, 'X502_ERR_MUTEX_LOCK_TOUT': -15, 'X502_ERR_MUTEX_RELEASE': -16,
                                     'X502_ERR_INSUFFICIENT_SYSTEM_RESOURCES': -17, 'X502_ERR_NOT_IMPLEMENTED': -18, 'X502_ERR_INSUFFICIENT_ARRAY_SIZE': -19, 
                                     'X502_ERR_FPGA_REG_READ': -20, 'X502_ERR_FPGA_REG_WRITE': -21, 'X502_ERR_STREAM_IS_NOT_RUNNING': -22, 
                                     'X502_ERR_INTERFACE_RELEASE': -23, 
                                     'X502_ERR_THREAD_START': -24, 'X502_ERR_THREAD_STOP': -25, 'X502_ERR_DEVICE_DISCONNECTED': -26, 
                                     'X502_ERR_IOCTL_INVALID_RESP_SIZE': -27, 'X502_ERR_INVALID_DEVICE': -28, 'X502_ERR_INVALID_DEVICE_RECORD': -29, 
                                     'X502_ERR_INVALID_CONFIG_HANDLE': -30, 'X502_ERR_DEVICE_NOT_OPENED': -31, 'X502_ERR_INVALID_OP_FOR_IFACE': -32,
                                     'X502_ERR_FPGA_NOT_LOADED': -33, 'X502_ERR_INVALID_USB_CONFIGURATION': -34, 'X502_ERR_INVALID_SVC_BROWSE_HANDLE': -35, 
                                     'X502_ERR_INVALID_SVC_RECORD_HANDLE': -36, 'X502_ERR_DNSSD_NOT_RUNNING': -37, 'X502_ERR_DNSSD_COMMUNICATION': -38, 
                                     'X502_ERR_SVC_RESOLVE_TIMEOUT': -39, 
                                     'X502_ERR_INSTANCE_NAME_ENCODING': -40, 'X502_ERR_INSTANCE_MISMATCH': -41, 'X502_ERR_NOT_SUP_BY_FIRMWARE': -42, 
                                     'X502_ERR_NOT_SUP_BY_DRIVER': -43, 'X502_ERR_OUT_CYCLE_SETUP_TOUT': -44, 'X502_ERR_UNKNOWN_FEATURE_CODE': -45, 
                                     'X502_ERR_INVALID_LTABLE_SIZE': -102, 'X502_ERR_INVALID_LCH_NUMBER': -103, 'X502_ERR_INVALID_LCH_RANGE': -104,
                                     'X502_ERR_INVALID_LCH_MODE': -105, 'X502_ERR_INVALID_LCH_PHY_NUMBER': -106, 'X502_ERR_INVALID_LCH_AVG_SIZE': -107,
                                     'X502_ERR_INVALID_ADC_FREQ_DIV': -108, 'X502_ERR_INVALID_DIN_FREQ_DIV': -109, 'X502_ERR_INVALID_MODE': -110, 
                                     'X502_ERR_INVALID_DAC_CHANNEL': -111, 'X502_ERR_INVALID_REF_FREQ': -112, 'X502_ERR_INVALID_INTERFRAME_DELAY': -113, 
                                     'X502_ERR_INVALID_SYNC_MODE': -114, 
                                     'X502_ERR_INVALID_STREAM_CH': -115, 'X502_ERR_INVALID_OUT_FREQ_DIV': -116, 'X502_ERR_REF_FREQ_NOT_LOCKED': -131, 
                                     'X502_ERR_IOCTL_FAILD': -132, 'X502_ERR_IOCTL_TIMEOUT': -133, 'X502_ERR_GET_INFO': -134, 
                                     'X502_ERR_DIG_IN_NOT_RDY': -135, 'X502_ERR_RECV_INSUFFICIENT_WORDS': -136, 'X502_ERR_DAC_NOT_PRESENT': -137,
                                     'X502_ERR_SEND_INSUFFICIENT_WORDS': -138, 'X502_ERR_NO_CMD_RESPONSE': -139, 'X502_ERR_PROC_INVALID_CH_NUM': -140,
                                     'X502_ERR_PROC_INVALID_CH_RANGE': -141, 'X502_ERR_FLASH_INVALID_ADDR': -142, 'X502_ERR_FLASH_INVALID_SIZE': -143, 
                                     'X502_ERR_FLASH_WRITE_TOUT': -144, 'X502_ERR_FLASH_ERASE_TOUT': -145, 'X502_ERR_FLASH_SECTOR_BOUNDARY': -146, 
                                     'X502_ERR_SOCKET_OPEN': -147, 
                                     'X502_ERR_CONNECTION_TOUT': -148, 'X502_ERR_CONNECTION_CLOSED_BY_DEV': -149, 'X502_ERR_SOCKET_SET_BUF_SIZE': -150, 
                                     'X502_ERR_NO_DATA_CONNECTION': -151, 'X502_ERR_NO_STREAM_END_MSG': -152, 'X502_ERR_CONNECTION_RESET': -153, 
                                     'X502_ERR_HOST_UNREACHABLE': -154, 'X502_ERR_TCP_CONNECTION_ERROR': -155, 'X502_ERR_LDR_FILE_OPEN': -180,
                                     'X502_ERR_LDR_FILE_READ': -181, 'X502_ERR_LDR_FILE_FORMAT': -182, 'X502_ERR_LDR_FILE_UNSUP_FEATURE': -183,
                                     'X502_ERR_LDR_FILE_UNSUP_STARTUP_ADDR': -184, 'X502_ERR_BF_REQ_TIMEOUT': -185, 'X502_ERR_BF_CMD_IN_PROGRESS': -186, 
                                     'X502_ERR_BF_CMD_TIMEOUT': -187, 'X502_ERR_BF_CMD_RETURN_INSUF_DATA': -188, 'X502_ERR_BF_LOAD_RDY_TOUT': -189,
                                     'X502_ERR_BF_NOT_PRESENT': -190, 'X502_ERR_BF_INVALID_ADDR': -191, 'X502_ERR_BF_INVALID_CMD_DATA_SIZE': -192,
                                     }
        self.ref_clock_list = [2.0, 1.5]
        self.flow_dict = {X502_STREAM_ADC: 'ADC', X502_STREAM_DIN: 'DIN', X502_STREAM_DAC1: 'DAC1', \
                          X502_STREAM_DAC2: 'DAC2', X502_STREAM_DOUT: 'DOUT', X502_STREAM_ALL_IN: 'AIN', \
                          X502_STREAM_ALL_OUT: 'AOUT', }

        ##pp = ctypes.pointer(Read_x502())

        #libname = os.path.join(path_to_file, '..', 'libx502api.so.1.1.14')
        self.libX = ctypes.cdll.LoadLibrary('/usr/local/lib/libx502api.so')
        self.libL = ctypes.cdll.LoadLibrary('/usr/local/lib/libl502api.so')

        # t_x502_info struct
        self.p_info = ctypes.pointer( t_x502_info() )

        # ctypes functions
        self.libX.X502_Close.argtypes = [ctypes.POINTER(_Opaque)]
        self.libX.X502_Free.argtypes = [ctypes.POINTER(_Opaque)]
        self.hCard = ctypes.POINTER(_Opaque)
        self.libX.X502_Create.restype = ctypes.POINTER(_Opaque)
        self.libL.L502_Open.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_char]
        self.libX.X502_SetRefFreq.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32]
        self.libX.X502_Configure.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32]
        self.libX.X502_SetSyncMode.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32]
        self.libX.X502_SetExtRefFreqValue.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_double]
        self.libX.X502_StreamsEnable.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32]
        self.libX.X502_StreamsDisable.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32]

        self.libX.X502_SetMode.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32]
        self.libX.X502_SetLChannelCount.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32]
        self.libX.X502_SetLChannel.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
        self.libX.X502_SetAdcInterframeDelay.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32]
        self.libX.X502_StreamsStart.argtypes = [ctypes.POINTER(_Opaque)]
        self.libX.X502_StreamsStop.argtypes = [ctypes.POINTER(_Opaque)]
        self.libX.X502_GetRecvReadyCount.argtypes = [ctypes.POINTER(_Opaque), ctypes.POINTER(ctypes.c_uint32)]

        self.libX.X502_SetStreamStep.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32, ctypes.c_uint32]
        self.libX.X502_GetEnabledStreams.argtypes = [ctypes.POINTER(_Opaque), ctypes.POINTER(ctypes.c_uint32)]

        self.libX.X502_SetOutFreqDivider.argtypes = [ctypes.POINTER(_Opaque), ctypes.c_uint32]

        self.libX.X502_Recv.argtypes = [ctypes.POINTER(_Opaque), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32]
        self.libX.X502_ProcessAdcData.argtypes = [ctypes.POINTER(_Opaque), ctypes.POINTER(ctypes.c_uint32), \
                                              ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
        self.libX.X502_ProcessData.argtypes = [ctypes.POINTER(_Opaque), ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32, ctypes.c_uint32, \
                                              ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32), \
                                              ctypes.POINTER(ctypes.c_uint32)]

        # limits
        self.sample_ref_clock_max = 1.5 # MHz
        self.max_log_channels = 256
        self.max_averages = 128
        self.max_common_ground_channels = 32
        self.max_diff_channels = 16
        self.max_interframe_delay = 0x1FFFFF

        # Test run parameters
        # These values are returned by the modules in the test run 
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':

            # Collect all parameters for digitizer settings
            self.reference_clock = 2 # MHz
            self.clock_mode = 0 # 0 is Internal; 1 is External
            self.flow_type = X502_STREAM_ADC
            self.points = 128 # number of points
            self.log_channels = 1 # number of logical channels
            self.interframe_delay = 0 # interframe delay

            # define the buffers
            self.recv_buffer = np.zeros( self.points, dtype = np.uint32 )
            self.buffer = np.zeros( self.points, dtype = np.double )

            # state counter
            self.state = 0

            # change of settings
            self.setting_change_count = 0
            
            # get_curve counter
            self.get_curve_counter = 0

        elif self.test_flag == 'test':        
            self.test_ref_clock = '2 MHz'
            self.test_clock_mode = 'Internal'
            self.test_flow_type = 'ADC'
            self.test_points = 128
            self.test_log_channels = 1
            self.interframe_delay = 0


            # define the buffers
            self.recv_buffer = np.zeros( self.test_points, dtype = np.uint32 )
            self.buffer = np.zeros( self.test_points, dtype = np.double )

            # state counter
            self.state = 0

            # change of settings
            self.setting_change_count = 0

            self.clock_mode = 0
            
            # get_curve counter
            self.get_curve_counter = 0

    # Module functions
    def digitizer_name(self):
        answer = 'L-card L502'
        return answer

    def digitizer_setup(self):
        """
        Write settings to the ADC. No argument; No output
        Everything except the buffer information will be write to the ADC

        This function should be called after all functions that change settings are called
        """
        if self.test_flag != 'test':
            
            if self.state == 0:
                # open card
                self.hCard = self.libX.X502_Create()
                if self.hCard == None:
                    general.message(f"No card found {self.__class__.__name__}")
                    sys.exit()

                # connect to the first found card
                ans = self.libL.L502_Open( self.hCard, ctypes.c_char() )
                #self.__error_check(ans)

                self.state = 1

            else:
                pass

            # writing settings
            # the PLD mode should be indicated
            self.libX.X502_SetMode( self.hCard, ctypes.c_uint32( 0 ) )

            #clock
            if self.clock_mode == 0: # Internal
                self.libX.X502_SetRefFreq( self.hCard, ctypes.c_uint32( MEGA(self.reference_clock) ) )
            elif self.clock_mode == 1: # External
                self.libX.X502_SetExtRefFreqValue( self.hCard, ctypes.c_double( MEGA(self.reference_clock) ) )

            #sync mode
            self.libX.X502_SetSyncMode( self.hCard, ctypes.c_uint32( self.clock_mode ) )
            # Flow
            self.libX.X502_StreamsEnable( self.hCard, ctypes.c_uint32( self.flow_type ) )
            #self.libX.X502_StreamsDisable( self.hCard, ctypes.c_uint32( X502_STREAM_DIN | X502_STREAM_DAC1 | X502_STREAM_DAC2 | X502_STREAM_DOUT ) )

            self.libX.X502_SetStreamBufSize( self.hCard, ctypes.c_uint32( 0 ), ctypes.c_uint32( 20000 )  )
            self.libX.X502_SetStreamStep( self.hCard, ctypes.c_uint32( 0 ), ctypes.c_uint32( 20000 )  )

            
            # interframe delay
            self.libX.X502_SetAdcInterframeDelay( self.hCard, ctypes.c_uint32( self.interframe_delay ) )

            # channels settings
            # number of logical channels
            self.libX.X502_SetLChannelCount( self.hCard, ctypes.c_uint32( self.log_channels ) ) 

            # settings of the logical channels
            # handle; number L channel; number physical channel (0-15); ADC mode; range; avg
            for i in range( self.log_channels ):
                self.libX.X502_SetLChannel( self.hCard, ctypes.c_uint32( i ), ctypes.c_uint32( i ), ctypes.c_uint32( 1 ), \
                                            ctypes.c_uint32( 2 ), ctypes.c_uint32( 0 ) )

            # configure
            ans = self.libX.X502_Configure( self.hCard, ctypes.c_uint32( 0 ) )
            self.__error_check(ans)

            
            # define the buffers
            self.recv_buffer = np.zeros( self.points, dtype = np.uint32 )
            self.buffer = np.zeros( self.points, dtype = np.double )

            # start stream
            start_time = time.time()
            self.libX.X502_StreamsStart( self.hCard ) # 22 ms
            general.message(str(time.time() - start_time))
            
        elif self.test_flag == 'test':
            pass
            # define the buffers
            #buffer; each point is 32 bits word
            #self.recv_buffer = ctypes.create_string_buffer( (32*self.points) )
            #( ctypes.c_uint32 * (32*self.points) )()
            #self.buffer = ctypes.create_string_buffer( (64*self.points) )
            #( ctypes.c_double * (64*self.points) )()

    def digitizer_get_curve(self, integral = False):
        """
        Start digitizer. No argument; No output
        Default settings:
        Sample clock is 2 MHz; Clock mode is 'Internal'; Reference clock is 2 MHz; Card mode is 'PLS';
        Number of averages is 1;
        Enabled channels is CH0 and CH1; Range of CH0 is '500 mV'; Range of CH1 is '500 mV';
        Number of points is 128 samples; Posttriger points is 64;
        Horizontal offset of CH0 and CH1 are 0%; 
        """
        if self.test_flag != 'test':

            self.get_curve_counter += 1
            
            # receive data to recv_buffer; 607 ms
            # handle; pointer to buffer; number of points; timeout in ms
            self.libX.X502_Recv( self.hCard, self.recv_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)), \
                                 ctypes.c_uint32( self.points ), ctypes.c_uint32( 2000 ) )
            # process data; 50 us
            # NULL pointer      ctypes.POINTER(ctypes.c_uint32)()
            self.libX.X502_ProcessData( self.hCard, self.recv_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)), ctypes.c_uint32( self.points ), \
                              ctypes.c_uint32( X502_PROC_FLAGS_VOLT ), self.buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), \
                              ctypes.byref( ctypes.c_uint32( self.points ) ), ctypes.POINTER(ctypes.c_uint32)(), ctypes.POINTER(ctypes.c_uint32)() )

            if self.get_curve_counter == 100:
                r2 = ctypes.c_uint32()
                self.libX.X502_GetRecvReadyCount( self.hCard, ctypes.byref(r2) )
                general.message(r2.value)
                self.get_curve_counter = 0

            return self.buffer

        elif self.test_flag == 'test':
            return np.zeros( self.points )

    def digitizer_close(self):
        """
        Close the ADC. No argument; No output
        """
        if self.test_flag != 'test':
            # stop streams
            self.libX.X502_StreamsStop( self.hCard )
            
            # clean up
            ans = self.libX.X502_Close( self.hCard )
            #self.__error_check( ans )

            ans = self.libX.X502_Free( self.hCard )
            #self.__error_check( ans )

            self.state == 0

        elif self.test_flag == 'test':
            pass

    def digitizer_reference_clock(self, *ref_clock):
        """
        Set or query reference clock;
        There are only two possible options for L502:
        X502_REF_FREQ_2000KHZ  = 2000000, /**< 2 MHz */
        X502_REF_FREQ_1500KHZ  = 1500000  /**< 1.5 MHz */

        Input: digitizer_reference_clock(2); Reference clock is in MHz;
        Default: '2';
        Output: '2 MHz'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(ref_clock) == 1:
                rate = round( float(ref_clock[0]), 1 )
                if self.clock_mode == 0:
                    if rate in self.ref_clock_list:
                        self.reference_clock = rate

                elif self.clock_mode == 1:
                    if rate <= 1.5:
                        self.reference_clock = rate

            elif len(ref_clock) == 0:
                return str(self.reference_clock) + ' MHz'

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(ref_clock) == 1:
                rate = round( float(ref_clock[0]), 1 )
                if self.clock_mode == 0:
                    assert(rate in self.ref_clock_list), f"Incorrect reference clock for Internal mode. The available clock are {self.ref_clock_list}"
                elif self.clock_mode == 1:
                    assert(rate <= 1.5), 'Incorrect reference clock for External mode. The available range is from 0 MHz to 1.5 MHz'

                self.reference_clock = rate

            elif len(ref_clock) == 0:
                return self.test_ref_clock
            else:
                assert( 1 == 2 ), 'Incorrect argument; clock: float'

    def digitizer_clock_mode(self, *mode):
        """
        Set or query clock mode; the driver needs to know the external fed in frequency
        Input: digitizer_clock_mode('Internal'); Clock mode is 'Internal' or 'External'
        Default: 'Internal';
        Output: 'Internal'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                if md == 'Internal':
                    self.clock_mode = 0
                elif md == 'External':
                    self.clock_mode = 1

            elif len(mode) == 0:
                if self.clock_mode == 0:
                    return 'Internal'
                elif self.clock_mode == 1:
                    return 'External'

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(mode) == 1:
                md = str(mode[0])
                assert(md == 'Internal' or md == 'External'), "Incorrect clock mode; mode: ['Internal', 'External']"
                if md == 'Internal':
                    self.clock_mode = 0
                elif md == 'External':
                    self.clock_mode = 1

            elif len(mode) == 0:
                return self.test_clock_mode
            else:
                assert( 1 == 2 ), "Incorrect argument; mode: ['Internal', 'External']"

    def digitizer_flow(self, *flow):
        """
        Set or query enabled flows of data;
        Input: digitizer_flow('ADC'); ['ADC','DIN','DAC1','DAC2','DOUT','AIN','AOUT']
        Default: 'ADC';
        Output: 'ADC'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(flow) == 1:
                fl = str(flow[0])
                self.flow_type = cutil.search_keys_dictionary( self.flow_dict, fl )
            elif len(flow) == 0:
                return self.flow_dict.get( self.flow_type  )

        elif self.test_flag == 'test':
            self.setting_change_count = 1
            
            if len(flow) == 1:
                fl = str(flow[0])
                assert(fl in self.flow_dict.values()), "Incorrect flow mode; flow: ['ADC', 'DIN', 'DAC1', 'DAC2', 'DOUT', 'AIN', 'AOUT']"
            elif len(flow) == 0:
                return self.test_flow_type
            else:
                assert( 1 == 2 ), "Incorrect argument; flow: ['ADC', 'DIN', 'DAC1', 'DAC2', 'DOUT', 'AIN', 'AOUT']"

    def digitizer_number_of_points(self, *points):
        """
        Set or query number of points;
        Input: digitizer_number_of_points(128)
        Default: 128;
        Output: '128'
        """
        if self.test_flag != 'test':
            self.setting_change_count = 1

            if len(points) == 1:
                pnts = int(points[0])
                if pnts < 1:
                    pnts = 1
                    general.message('Incorrect number of points. Number of points must be more than 1')
                else:
                    self.points = pnts

            elif len(points) == 0:
                return self.points

            # to update on-the-fly
            # TO DO

        elif self.test_flag == 'test':
            self.setting_change_count = 1

            if len(points) == 1:
                pnts = int(points[0])
                assert( pnts >= 1 ), "Incorrect number of points. Number of points must be more than 1"
                self.points = pnts
            elif len(points) == 0:
                return self.points
            else:
                assert( 1 == 2 ), 'Incorrect argument; points: int'

    # internal functions
    def __error_check(self, value):
        if value == 0:
            #pass
            general.message("No errors")
        else:
            error_name = cutil.search_keys_dictionary( self.error_dict, int( value ) )
            general.message( error_name )
            #sys.exit()

    def get_info(self, hnd):
        """
        """
        Info = self.libX.X502_GetDevInfo(hnd, self.p_info)

        print ('Info:', Info)
        print ('Board Name:', self.p_info.contents.BrdName)
        print ('Serial Number:', self.p_info.contents.SerNum)
        print ('devflags:', self.p_info.contents.devflags)
        print ('fpga_ver:', self.p_info.contents.fpga_ver)
        print ('plda_ver:', self.p_info.contents.plda_ver)
        print ('board_rev:', self.p_info.contents.board_rev)
        print ('mcu_firmware_ver:', self.p_info.contents.mcu_firmware_ver)

        for i in range(6):
            print ('-->ADC cbr_offs {}: {}'.format(i, self.p_info.contents.cbr.adc[i].offs))
            print ('-->ADC cbr_koef {}: {}'.format(i, self.p_info.contents.cbr.adc[i].k))

        for i in range(2):
            print ('-->DAC cbr_offs {}: {}'.format(i, self.p_info.contents.cbr.dac[i].offs))
            print ('-->DAC cbr_koef {}: {}'.format(i, self.p_info.contents.cbr.dac[i].k))
        #    coef_dac_list.append(pp2.contents.cbr.dac[i].offs)
        #    coef_dac_list.append(pp2.contents.cbr.dac[i].k)

if __name__ == '__main__':
    main()
