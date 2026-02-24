import atexit
import json
import uuid
import warnings
import numpy as np
import logging
import platform
import time
from PyQt6.QtNetwork import QLocalSocket
from PyQt6.QtCore import QCoreApplication, QSharedMemory

logging.root.setLevel(logging.WARNING)

class LivePlotClient(object):
    
    def __init__(self, timeout=2000, size=2**28):
        # from 06-08-2021; Freezing GUI when import general module
        
        #self.app = QCoreApplication.instance()
        #if self.app is None:
        #    self.app = QCoreApplication([])

        self.sock = QLocalSocket()
        self.sock.connectToServer("LivePlot")
        self.system = platform.system()

        if not self.sock.waitForConnected():
            raise EnvironmentError("Couldn't find LivePlotter instance")
        self.sock.disconnected.connect(self.disconnect_received)

        key = str(uuid.uuid4())
        self.shared_mem = QSharedMemory(key)
        if not self.shared_mem.create(size):
            raise Exception("Couldn't create shared memory %s" % self.shared_mem.errorString())
        logging.debug('Memory created with key %s and size %s' % (key, self.shared_mem.size()))
        
        self.sock.write(key.encode())      
        self.sock.waitForBytesWritten()
        self.is_connected = True
        self.timeout = timeout
        
        atexit.register(self.close)


    def close(self):
        self.shared_mem.detach()

    def send_to_plotter(self, meta, arr=None):
        if not self.is_connected:
            return
        if meta["name"] is None:
            meta["name"] = "*"
        if arr is not None:
            arrbytes = arr.tobytes()
            arrsize = len(arrbytes)
            if arrsize > self.shared_mem.size():
                raise ValueError("Array too big %s > %s" % (arrsize, self.shared_mem.size()))
            meta['arrsize'] = arrsize
            meta['dtype'] = str(arr.dtype)
            meta['shape'] = arr.shape
        else:
            meta['arrsize'] = 0
        meta_bytes = json.dumps(meta).ljust(320)
        if len(meta_bytes) > 320:
            raise ValueError("meta object is too large (> 320 char)")
        
        if arr is None:
            self.sock.write(meta_bytes.encode())
        else:
            if not self.sock.bytesAvailable():
                # should be clarified
                self.sock.waitForReadyRead(2000)
            self.sock.read(2)
            if self.shared_mem.lock():
                try:
                    # Get the pointer and cast to a writable memoryview
                    ptr = self.shared_mem.data()
                    region = memoryview(ptr).cast('B') 
                    region[:len(arrbytes)] = arrbytes
                finally:
                    self.shared_mem.unlock()

                self.sock.write(meta_bytes.encode())

    def plot_y(self, name, arr, extent=None, start_step=(0, 1), label=''):
        arr = np.array(arr)
        if extent is not None and start_step is not None:
            raise ValueError('extent and start_step provide the same info and are thus mutually exclusive')
        if extent is not None:
            x0, x1 = extent
            nx = len(arr)
            start_step = x0, float(x1 - x0)/nx
        meta = {
            'name': name,
            'operation':'plot_y',
            'start_step': start_step,
            'rank': 1,
            'label': label,
        }
        self.send_to_plotter(meta, arr.astype('float64'))
        if self.system == 'Windows':
            #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([]))
            pass
        else:
            self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([np.nan]))

    def plot_z(self, name, arr, extent=None, start_step=None, xname='X axis',\
     xscale='arb. u.', yname='Y axis', yscale='arb. u.', zname='Y axis', zscale='arb. u.', text=''):
        '''
        extent is ((initial x, final x), (initial y, final y))
        start_step is ((initial x, delta x), (initial_y, final_y))
        '''
        arr = np.array(arr)
        if extent is not None and start_step is not None:
            raise ValueError('extent and start_step provide the same info and are thus mutually exclusive')
        if extent is not None:
            (x0, x1), (y0, y1) = extent
            nx, ny = arr.shape
            start_step = (x0, float(x1 - x0)/nx), (y0, float(y1 - y0)/ny)
        meta = {
            'name': name,
            'operation':'plot_z',
            'rank': 2,
            'start_step': start_step,
            'X': xscale,
            'Y': yscale,
            'Z': zscale,
            'Xname': xname,
            'Yname': yname,
            'Zname': zname,
            'value': text,
        }
        self.send_to_plotter(meta, arr.astype('float64'))
        if self.system == 'Windows':
            #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([]))
            pass
        else:
            self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([np.nan]))

    def plot_xy(self, name, xs, ys, label='', xname='X axis', xscale='arb. u.',\
     yname='Y axis', yscale='arb. u.', scatter='False', timeaxis='False', vline='False', text=''):
    
        meta = {
            'name': name,
            'operation':'plot_xy',
            'rank': 1,
            'label': label,
            'X': xscale,
            'Y': yscale,
            'Xname': xname,
            'Yname': yname,
            'Scatter': scatter,
            'TimeAxis': timeaxis,
            'Vline': vline,
            'value': text,
        }


        if len( np.shape( ys ) ) == 1:
            self.send_to_plotter(meta, np.array([xs, ys]).astype('float64'))
            if self.system == 'Windows':
                #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([]))
                pass
            else:
                self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([np.nan]))        
        elif len( np.shape( ys ) ) == 2:
            # simultaneous plot of two curves
            self.send_to_plotter(meta, np.array([[xs, xs], ys]).astype('float64'))
            if self.system == 'Windows':
                #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([]))
                pass
            else:
                self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([np.nan]))

    def append_y(self, name, point, start_step=(0, 1), label='', xname='X axis',\
     xscale='arb. u.', yname='Y axis', yscale='arb. u.',scatter='False', timeaxis='False', vline='False'):
        self.send_to_plotter({
            'name': name,
            'operation': 'append_y',
            'value': point,
            'start_step': start_step,
            'rank': 1,
            'label': label,
            'X': xscale,
            'Y': yscale,
            'Xname': xname,
            'Yname': yname,
            'Scatter': scatter,
            'TimeAxis': timeaxis,
            'Vline': vline
        })

        if self.system == 'Windows':
            #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([]))
            pass
        else:
            self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([np.nan]))

    def append_xy(self, name, x, y, label=''):
        self.send_to_plotter({
            'name': name,
            'operation': 'append_xy',
            'value': (x, y),
            'rank': 1,
            'label': label,
        })

        if self.system == 'Windows':
            #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([]))
            pass
        else:
            self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([np.nan]))

    def append_z(self, name, arr, start_step=None, xname='X axis',\
     xscale='arb. u.', yname='Y axis', yscale='arb. u.', zname='Y axis', zscale='arb. u.'):
        arr = np.array(arr)
        meta = {
            'name': name,
            'operation':'append_z',
            'rank': 2,
            'start_step': start_step,
            'X': xscale,
            'Y': yscale,
            'Z': zscale,
            'Xname': xname,
            'Yname': yname,
            'Zname': zname,
            }
        self.send_to_plotter(meta, arr.astype('float64'))

        if self.system == 'Windows':
            #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([]))
            pass
        else:
            self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([np.nan]))

    def label(self, name, text):
        self.send_to_plotter({
            'name': name,
            'operation': 'label',
            'value': text
        })

        if self.system == 'Windows':
            #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([]))
            pass
        else:
            self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([np.nan]))

    def clear(self, name=None):
        self.send_to_plotter({
            'name': name,
            'operation': 'clear'
        })

    def hide(self, name=None):
        self.send_to_plotter({
            'name': name,
            'operation': 'close'
        })

    def remove(self, name=None):
        self.send_to_plotter({
            'name': name,
            'operation': 'remove'
        })

        if self.system == 'Windows':
            #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([]))
            pass
        else:
            self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([np.nan]))
        
    def disconnect_received(self):
        self.is_connected = False
        #warnings.warn('Disconnected from LivePlotter server, plotting has been disabled')
