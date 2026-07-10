import atexit
import threading
import time
import json
import uuid
import warnings
import numpy as np
import logging
from PyQt6.QtNetwork import QLocalSocket, QAbstractSocket
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
        #self.system = platform.system()

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
        self.timeout = timeout
        # Consume the connect-handshake 'ok' the server writes in accept().
        # Left unread, it satisfies the FIRST frame's ack wait instead, and
        # from then on every wait is satisfied by the PREVIOUS frame's ack:
        # the client runs one frame ahead of the receiver and overwrites the
        # shared-memory block before the receiver has copied it, so frames
        # render under the previous frame's meta (data jumping between two
        # plots that alternate sends).
        if self.sock.bytesAvailable() == 0:
            self.sock.waitForReadyRead(self.timeout)
        self.sock.readAll()
        self.is_connected = True
        # Serialises send_to_plotter across the two threads that reach it on
        # this one client (the AtomizePlotWorker daemon and the caller's own
        # thread); see send_to_plotter for why.
        self._send_lock = threading.Lock()
        # The receiver answers every 320-byte meta frame with one 2-byte 'ok'
        # AFTER copying the frame's array out of shared memory. Count the
        # outstanding acks so a late ack (one that missed its 2 s window) can
        # never be taken for the current frame's ack — that mispairing is
        # exactly what mixes data between plots. _ack_carry holds an odd
        # leftover byte should an 'ok' ever arrive split across reads.
        self._acks_pending = 0
        self._ack_carry = 0
        
        atexit.register(self.close)

    def close(self):
        self.shared_mem.detach()

    def send_to_plotter(self, meta, arr=None):
        if not self.is_connected:
            return
        # Both the AtomizePlotWorker daemon thread (async pr= plots) and the
        # caller's own thread (synchronous plot / incremental append) reach
        # this method on the SAME LivePlotClient. Serialise the whole
        # shared-memory copy + meta/'ok' socket handshake so the two never
        # race: concurrent QSharedMemory.lock() ("QSharedMemory::lock: already
        # locked") and interleaved 320-byte meta writes that steal each
        # other's ack ("Receiver did not send 'ok'").
        with self._send_lock:
            self._send_to_plotter_locked(meta, arr)

    def _drain_acks(self):
        """Wait until every sent frame has been acked ('ok', 2 bytes each) or
        the timeout runs out. On timeout the debt is kept: when the stale ack
        finally arrives it pays off the OLD frame instead of being mistaken
        for the ack of the frame currently being sent."""
        deadline = time.monotonic() + self.timeout / 1000.0
        while self._acks_pending > 0:
            if self.sock.bytesAvailable() == 0:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not self.sock.waitForReadyRead(max(1, int(remaining * 1000))):
                    logging.warning("Timeout: Receiver did not send 'ok' for %s ms" % self.timeout)
                    return
            n = self._ack_carry + len(bytes(self.sock.readAll()))
            self._acks_pending -= n // 2
            self._ack_carry = n % 2
        if self._acks_pending < 0:
            self._acks_pending = 0

    def _send_to_plotter_locked(self, meta, arr=None):
        if meta.get("name") is None:
            meta["name"] = "*"

        # If the previous frame's ack timed out, the receiver may still be
        # copying that frame out of shared memory. Never overwrite the block
        # while an ack is outstanding, or the old meta gets rendered with this
        # frame's array.
        self._drain_acks()

        if arr is not None:
            # Normalize to a contiguous float64 array without an extra copy when the
            # caller already handed us one (the live-plot case), then transfer it into
            # the shared block with a single np.copyto. This replaces the former
            # np.array + .astype + .tobytes + slice-assign chain (four ~20 MB copies of
            # a 2D frame, three of them holding the GIL) that was stalling the
            # measurement thread; np.copyto releases the GIL for the memcpy.
            arr = np.ascontiguousarray(arr, dtype=np.float64)
            arrsize = arr.nbytes
            if arrsize > self.shared_mem.size():
                raise ValueError("Array too big %s > %s" % (arrsize, self.shared_mem.size()))
            
            meta['arrsize'] = arrsize
            meta['dtype'] = str(arr.dtype)
            meta['shape'] = arr.shape
            
            if self.shared_mem.lock():
                try:
                    ptr = self.shared_mem.data()
                    dst = np.frombuffer(memoryview(ptr).cast('B')[:arrsize], dtype=np.float64)
                    np.copyto(dst, arr.reshape(-1))
                finally:
                    self.shared_mem.unlock()
        else:
            meta['arrsize'] = 0

        meta_json = json.dumps(meta).encode('utf-8')
        if len(meta_json) > 320:
            raise ValueError("meta object is too large (> 320 char)")

        meta_bytes = meta_json.ljust(320, b' ') 

        self.sock.write(meta_bytes)
        self.sock.flush()

        self._acks_pending += 1
        self._drain_acks()

        self.sock.waitForBytesWritten(1000)

    def plot_y(self, name, arr, extent=None, start_step=(0, 1), label=''):
        arr = np.asarray(arr)
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
        self.send_to_plotter(meta, arr)
        #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([0]))

    def plot_z(self, name, arr, extent=None, start_step=None, xname='X axis',\
     xscale='arb. u.', yname='Y axis', yscale='arb. u.', zname='Z axis', zscale='arb. u.', text=''):
        '''
        extent is ((initial x, final x), (initial y, final y))
        start_step is ((initial x, delta x), (initial_y, final_y))
        '''
        arr = np.asarray(arr)
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
        self.send_to_plotter(meta, arr)
        #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([0]))

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
            self.send_to_plotter(meta, np.array([xs, ys]))
            #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([0]))        
        elif len( np.shape( ys ) ) == 2:
            # simultaneous plot of two curves
            self.send_to_plotter(meta, np.array([[xs, xs], ys]))
            #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([0]))

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
        #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([0]))

    def append_xy(self, name, x, y, label=''):
        self.send_to_plotter({
            'name': name,
            'operation': 'append_xy',
            'value': (x, y),
            'rank': 1,
            'label': label,
        })
        #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([0]))

    def append_z(self, name, arr, start_step=None, xname='X axis',\
     xscale='arb. u.', yname='Y axis', yscale='arb. u.', zname='Y axis', zscale='arb. u.'):
        arr = np.asarray(arr)
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
        self.send_to_plotter(meta, arr)
        #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([0]))

    def update_z(self, name, arr, index, full_shape, start_step=None, xname='X axis',\
     xscale='arb. u.', yname='Y axis', yscale='arb. u.', zname='Z axis', zscale='arb. u.', text=''):
        '''
        Partial rank-2 update: replace the columns
        [index : index + arr.shape[-1]) along the LAST axis of the image
        `name`, leaving every other column as it is. The receiver keeps a
        full-size array of shape `full_shape` (allocated zero on the first
        update or whenever the shape changes) and redraws it with the slice
        applied, so only the changed columns cross the shared memory.
        '''
        arr = np.asarray(arr)
        meta = {
            'name': name,
            'operation':'update_z',
            'rank': 2,
            'start_step': start_step,
            'index': int(index),
            'full_shape': [int(s) for s in full_shape],
            'X': xscale,
            'Y': yscale,
            'Z': zscale,
            'Xname': xname,
            'Yname': yname,
            'Zname': zname,
            'value': text,
            }
        self.send_to_plotter(meta, arr)

    def label(self, name, text):
        self.send_to_plotter({
            'name': name,
            'operation': 'label',
            'value': text
        })
        #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([0]))

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
        
        #self.send_to_plotter({'name':'none', 'operation':'none'}, np.array([0]))
        
    def disconnect_received(self):
        self.is_connected = False
        #warnings.warn('Disconnected from LivePlotter server, plotting has been disabled')
