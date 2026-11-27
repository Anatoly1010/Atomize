#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import gc
import sys
import json
import time
import queue
import base64
import threading
import subprocess
import atomize.main.local_config as lconf
import atomize.device_modules.config.config_utils as cutil
import atomize.general_modules.general_functions as general

"""
Magnetic field of a Bruker spectrometer, set through the Xepr API of a running
Xepr program on another PC.

XeprAPI runs only on Python 2 (2.5 to 2.7) on the Xepr PC, so this module keeps
one SSH session open and runs a small Python 2 helper there (_BRIDGE below). The
helper is sent over the session itself, so nothing is installed on the Xepr PC.
Requests and answers are single JSON lines; one call takes about 1 ms on a LAN.

Needed on the Xepr PC:
1. SSH key login for the user that runs Xepr (ssh-copy-id user@host).
2. Xepr running, with Processing -> XeprAPI -> Enable Xepr API.

The field is set through a CW experiment of its own (the experiment name in the
config, created on first use). The AcqHidden experiment has no field controller.
The target is written to the experiment before it is activated, so activating it
never sends the magnet to Xepr's default field first.

The field readback (fieldCtrl.StaticFieldMon) follows the setpoint, not a field
measurement. Setting the field returns at once and does not wait for the magnet:
use the field_wait config parameter or general.wait() before measuring.
"""

_BRIDGE = r'''
import sys, os, json
_out = os.fdopen(os.dup(1), 'w', 0)
os.dup2(2, 1)
sys.stdout = sys.stderr
sys.path.insert(0, API_PATH)

def reply(**kw):
    _out.write(json.dumps(kw) + '\n')

try:
    import XeprAPI
    instances = XeprAPI.getXeprInstances()
    if PID:
        if PID not in instances:
            raise RuntimeError('Xepr pid %d has no API enabled; with API: %r' % (PID, instances))
        pid = PID
    elif len(instances) == 1:
        pid = list(instances)[0]
    elif not instances:
        raise RuntimeError('no Xepr with the API enabled: Processing -> XeprAPI -> Enable Xepr API')
    else:
        raise RuntimeError('several Xepr instances with the API enabled %r: set xepr_pid in the config' % instances)
    X = XeprAPI.Xepr(pid=pid)
    hidden = X.XeprExperiment('AcqHidden')
    lo = hidden['*sysConf.Er032tMinField'].value
    hi = hidden['*sysConf.Er032tMaxField'].value
except Exception as e:
    reply(ok=False, error='%s: %s' % (e.__class__.__name__, e))
    sys.exit(1)

state = {'exp': None}

def experiment(create):
    if state['exp'] is None:
        try:
            state['exp'] = X.XeprExperiment(EXP)
        except Exception:
            if not create:
                return None
            state['exp'] = X.XeprExperiment(EXP, exptype='C.W.', axs1='Field', ordaxs='Signal channel')
    return state['exp']

def get_field():
    e = experiment(False)
    if e is None or e.isClosed:
        return None
    return e['*fieldCtrl.StaticFieldMon'].value

def set_field(value):
    value = float(value)
    if not lo <= value <= hi:
        raise ValueError('field %s G outside the Xepr limits %s to %s G' % (value, lo, hi))
    e = experiment(True)
    if e.isClosed:
        e['CenterField'].value = value
        e['FieldPosition'].value = value
        e.aqExpActivate()
    e['FieldPosition'].value = value
    return value

handlers = {
    'hello': lambda: {'pid': pid, 'min_field': lo, 'max_field': hi, 'experiment': EXP},
    'get_field': get_field,
    'set_field': set_field,
}

reply(ok=True, result=handlers['hello']())
for line in iter(sys.stdin.readline, ''):
    try:
        req = json.loads(line)
        if req['cmd'] == 'quit':
            break
        reply(ok=True, result=handlers[req['cmd']](*req.get('args', [])))
    except Exception as e:
        reply(ok=False, error='%s: %s' % (e.__class__.__name__, e))
'''


class Bruker_Xepr:
    #### Basic interaction functions
    def __init__(self):

        #### Inizialization
        # setting path to *.ini file
        self.path_current_directory = lconf.load_config_device()
        self.path_config_file = os.path.join(self.path_current_directory, 'Bruker_Xepr_config.ini')

        # configuration data
        self.config = cutil.read_conf_util(self.path_config_file)
        self.specific_parameters = cutil.read_specific_parameters(self.path_config_file)

        # Ranges and limits; replaced by the limits Xepr reports once connected
        self.min_field = float(self.specific_parameters['min_field'])
        self.max_field = float(self.specific_parameters['max_field'])
        self.field_wait = float(self.specific_parameters['field_wait'])  # s after each field change
        self.field = None
        self.field_step = None
        self.start_field = None
        self._proc = None

        # Test run parameters
        # These values are returned by the modules in the test run
        if len(sys.argv) > 1:
            self.test_flag = sys.argv[1]
        else:
            self.test_flag = 'None'

        if self.test_flag != 'test':
            self._connect()
        elif self.test_flag == 'test':
            self.test_field = 3500.

    #### connection
    def _connect(self):
        host = self.config['ethernet_address']
        sp = self.specific_parameters
        pid = int(sp['xepr_pid']) if sp['xepr_pid'].strip() else None
        code = (f"API_PATH = {sp['api_path']!r}\nEXP = {sp['experiment']!r}\nPID = {pid!r}\n" + _BRIDGE)
        remote = (f'cd /tmp && exec {sp["remote_python"]} -u -c '
                  '"import sys, base64; exec(base64.b64decode(sys.stdin.readline()))"')
        try:
            self._proc = subprocess.Popen(
                # GSSAPIAuthentication=no: with it on, every login waits 20 s for a Kerberos timeout
                ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'GSSAPIAuthentication=no', '-o', 'ConnectTimeout=10',
                 '-o', 'ServerAliveInterval=10', '-o', 'LogLevel=ERROR', host, remote],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1)
        except OSError as exc:
            general.message(f"No connection {self.__class__.__name__}: {exc}")
            sys.exit()

        self._answers = queue.Queue()
        self._stderr = []
        threading.Thread(target=self._pump, args=(self._proc.stdout, self._answers.put), daemon=True).start()
        threading.Thread(target=self._pump, args=(self._proc.stderr, self._stderr.append), daemon=True).start()
        self._proc.stdin.write(base64.b64encode(code.encode()).decode() + '\n')
        self._proc.stdin.flush()

        self.status_flag = 1
        info = self._read(max(self.config['timeout'] / 1000, 30))
        self.xepr_pid = info['pid']
        self.min_field, self.max_field = info['min_field'], info['max_field']
        self.field = self._request('get_field')

    @staticmethod
    def _pump(stream, put):
        for line in iter(stream.readline, ''):
            put(line)

    def _read(self, timeout):
        try:
            answer = json.loads(self._answers.get(timeout=timeout))
        except queue.Empty:
            alive = self._proc.poll() is None
            log = ''.join(self._stderr[-5:]).strip()
            general.message(f"No answer {self.__class__.__name__}" + ('' if alive else ' (SSH session closed)')
                            + (f": {log}" if log else ''))
            self.close_connection()
            sys.exit()
        if not answer['ok']:
            general.message(f"{self.__class__.__name__}: {answer['error']}")
            self.close_connection()
            sys.exit()
        return answer['result']

    def _request(self, cmd, *args):
        if self.status_flag != 1 or self._proc.poll() is not None:
            self.status_flag = 0
            general.message(f"No connection {self.__class__.__name__}")
            sys.exit()
        self._proc.stdin.write(json.dumps({'cmd': cmd, 'args': list(args)}) + '\n')
        self._proc.stdin.flush()
        return self._read(self.config['timeout'] / 1000)

    def close_connection(self):
        if self.test_flag != 'test' and self._proc is not None:
            self.status_flag = 0
            try:
                if self._proc.poll() is None:
                    self._proc.stdin.write('{"cmd": "quit"}\n')
                    self._proc.stdin.close()
                    self._proc.wait(timeout=3)
            except (OSError, ValueError, subprocess.TimeoutExpired):
                self._proc.kill()
            self._proc = None
            gc.collect()
        elif self.test_flag == 'test':
            pass

    def __del__(self):
        try:
            self.close_connection()
        except Exception:
            pass

    #### device specific functions
    def magnet_name(self):
        answer = self.config['name']
        return answer

    def magnet_setup(self, start_field, field_step):
        if self.test_flag == 'test':
            assert(start_field <= self.max_field and start_field >= self.min_field),\
                f'Incorrect field range. The available range is from {self.min_field} to {self.max_field}'
        self.start_field = start_field
        self.field_step = field_step
        return self.magnet_field(start_field)

    def magnet_field(self, *field):
        if self.test_flag != 'test':
            if len(field) == 1:
                field = round(float(field[0]), 3)
                if field <= self.max_field and field >= self.min_field:
                    self.field = self._request('set_field', field)
                    if self.field_wait > 0:
                        time.sleep(self.field_wait)
                    return self.field
                else:
                    general.message(f"Field of {field} G is outside the range {self.min_field} to {self.max_field} G.")
                    sys.exit()

            elif len(field) == 0:
                answer = self._request('get_field')
                if answer is None:
                    general.message("Field hasn't been set yet and is thus still unknown.")
                return answer

        elif self.test_flag == 'test':
            if len(field) == 1:
                field = field[0]
                assert(field <= self.max_field and field >= self.min_field),\
                    f'Incorrect field range. The available range is from {self.min_field} to {self.max_field}'
                self.field = field
                return self.field
            elif len(field) == 0:
                answer = self.test_field
                return answer
            else:
                assert(1 == 2), 'Invalid argument; field: float'

    def magnet_sweep_up(self):
        if self.field_step is None:
            general.message("No sweep step size has been set - you must call the function magnet_setup() to be able to do sweeps.")
            sys.exit()
        return self.magnet_field(self.field + self.field_step)

    def magnet_sweep_down(self):
        if self.field_step is None:
            general.message("No sweep step size has been set - you must call the function magnet_setup() to be able to do sweeps.")
            sys.exit()
        return self.magnet_field(self.field - self.field_step)

    def magnet_reset_field(self):
        if self.start_field is None:
            general.message("Start field has not been defined  - you must call the function magnet_setup() before.")
            sys.exit()
        return self.magnet_field(self.start_field)

def main():
    pass

if __name__ == "__main__":
    main()
