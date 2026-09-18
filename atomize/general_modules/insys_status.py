"""FPGA ownership and reboot recovery for the existing libs/status file."""

import os
from pathlib import Path
import tempfile
import uuid


REBOOT_REQUIRED = 'FPGA recovery requires reboot. Reboot the computer before starting another acquisition.'
_OWNER_KEYS = ('PID', 'Started', 'Boot', 'Token')


def status_path():
    return Path(__file__).resolve().parents[2] / 'libs' / 'status'


def boot_id():
    try:
        return Path('/proc/sys/kernel/random/boot_id').read_text().strip() or None
    except OSError:
        return None


def process_identity(pid):
    """Return Linux process state and start ticks, including unreaped zombies."""
    text = Path(f'/proc/{int(pid)}/stat').read_text()
    fields = text.rsplit(')', 1)[1].split()
    return fields[0], fields[19]


def _read(path):
    try:
        text = Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        return {'Status': 'Off'}
    data = {}
    for line in text.splitlines():
        key, separator, value = line.partition(':')
        if separator:
            data[key.strip()] = value.strip()
    if data.get('Status') not in ('On', 'Off'):
        raise ValueError('Invalid FPGA status file')
    return data


def _write(path, data):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='status-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(''.join(f'{key}:  {value}\n' for key, value in data.items()))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _legacy_previous_boot(path):
    """Recognize pre-ownership status files left on disk before the Linux boot."""
    try:
        for line in Path('/proc/stat').read_text().splitlines():
            if line.startswith('btime '):
                return Path(path).stat().st_mtime < int(line.split()[1])
    except (OSError, ValueError):
        pass
    return False


def blocking_reason(path=None):
    """Read availability without changing status, including during test mode."""
    path = status_path() if path is None else path
    try:
        data = _read(path)
    except (OSError, ValueError) as exc:
        return f'Cannot verify FPGA status: {exc}'
    if data['Status'] == 'Off':
        return None
    current_boot = boot_id()
    if data.get('Boot') and current_boot and data['Boot'] != current_boot:
        return None
    if not data.get('Boot'):
        if _legacy_previous_boot(path):
            return None
        return 'Insys FPGA is marked busy without owner information. Stop the active acquisition or reboot the computer.'
    if data.get('Recovery') == 'Required':
        return REBOOT_REQUIRED
    if not current_boot:
        return 'Cannot verify FPGA ownership on this system. Acquisition remains blocked.'
    try:
        state, started = process_identity(data['PID'])
    except (FileNotFoundError, ProcessLookupError):
        return REBOOT_REQUIRED
    except (OSError, ValueError, KeyError, IndexError):
        return 'Cannot verify the FPGA owner. Acquisition remains blocked.'
    if state in ('Z', 'X', 'x') or started != data.get('Started'):
        return REBOOT_REQUIRED
    return f"Insys FPGA card is already opened by process {data['PID']}. Stop the active acquisition first."


def ensure_available(path=None):
    reason = blocking_reason(path)
    if reason:
        raise RuntimeError(reason)


def claim(path=None):
    """Record this process before hardware initialization; never used by tests."""
    path = status_path() if path is None else path
    ensure_available(path)
    current_boot = boot_id()
    if not current_boot:
        raise RuntimeError('Cannot identify the Linux boot; FPGA initialization refused.')
    _, started = process_identity(os.getpid())
    owner = {'PID': str(os.getpid()), 'Started': started,
             'Boot': current_boot, 'Token': uuid.uuid4().hex}
    _write(path, {'Status': 'On', **owner})
    return owner


def is_owner(owner, path=None):
    if not owner or owner.get('PID') != str(os.getpid()):
        return False
    path = status_path() if path is None else path
    data = _read(path)
    state, started = process_identity(os.getpid())
    return (data['Status'] == 'On' and owner.get('Boot') == boot_id()
            and state not in ('Z', 'X', 'x') and owner.get('Started') == started
            and all(data.get(key) == owner.get(key) for key in _OWNER_KEYS))


def release(owner, path=None):
    path = status_path() if path is None else path
    if not is_owner(owner, path):
        raise RuntimeError('FPGA status belongs to another acquisition; it was not cleared.')
    if _read(path).get('Recovery') == 'Required':
        raise RuntimeError(REBOOT_REQUIRED)
    _write(path, {'Status': 'Off'})


def require_reboot(owner, path=None):
    path = status_path() if path is None else path
    if is_owner(owner, path):
        _write(path, {'Status': 'On', **owner, 'Recovery': 'Required'})
