#!/usr/bin/env python3
"""Private Termux desktop lifecycle. stdout is reserved for the launcher protocol."""
import ctypes
import errno
import fcntl
import json
import os
from pathlib import Path
import platform
import select
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid

HOME = Path(os.environ['HOME'])
PREFIX = Path(os.environ.get('PREFIX', '/data/data/com.termux/files/usr'))
RUNTIME = HOME / '.local/linux-desktop/runtime'
STATE = RUNTIME / 'state.json'
TMP = PREFIX / 'tmp'
COMPONENTS = Path(__file__).with_name('xfce-components.sh')
DISPLAY_NUMBER = os.environ.get('LINUX_DESKTOP_DISPLAY', '2')
LOCK_WAIT = 2
START_WAIT = 45
STOP_WAIT = 5
PROBE_WAIT = 5


class Failure(Exception):
    pass


if not DISPLAY_NUMBER.isdigit() or not 2 <= int(DISPLAY_NUMBER) <= 99:
    raise Failure('LINUX_DESKTOP_DISPLAY must be a display number from 2 to 99')
DISPLAY = ':' + DISPLAY_NUMBER


def proc_info(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        if fields[0] == 'Z':
            return None
        cmdline = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        status = Path(f'/proc/{pid}/status').read_text().splitlines()
        status_fields = dict(line.split(':', 1) for line in status if ':' in line)
        return {'start': fields[19], 'ppid': int(fields[1]),
                'tracer': int(status_fields.get('TracerPid', '0').strip()),
                'cmd': [arg.decode(errors='replace') for arg in cmdline if arg]}
    except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
        return None


def boot_id():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def pidfd_open(pid):
    if hasattr(os, 'pidfd_open'):
        return os.pidfd_open(pid)
    if platform.machine() not in ('aarch64', 'arm64'):
        raise Failure('pidfd unavailable on this architecture')
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.syscall(434, pid, 0)
    if fd < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return fd


def pidfd_signal(fd, sig):
    if hasattr(signal, 'pidfd_send_signal'):
        signal.pidfd_send_signal(fd, sig)
        return
    if platform.machine() not in ('aarch64', 'arm64'):
        raise Failure('pidfd signal unavailable on this architecture')
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.syscall(424, fd, sig, 0, 0) < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def load_state():
    try:
        fd = os.open(STATE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(fd) as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise Failure('state must be a regular file')
        state = json.load(stream)
    if (not isinstance(state, dict) or state.get('version') != 1 or
            not isinstance(state.get('token'), str) or len(state['token']) != 32 or
            not isinstance(state.get('boot_id'), str) or not state['boot_id']):
        raise Failure('invalid state file; refusing to modify it')
    if state['boot_id'] != boot_id():
        raise Failure('previous-boot state requires manual inspection')
    return state


def save_state(state, initial=False):
    data = json.dumps(state).encode()
    path = RUNTIME / ('state-' + uuid.uuid4().hex)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if initial:
            os.link(path, STATE, follow_symlinks=False)
        else:
            os.replace(path, STATE)
    finally:
        if path.exists():
            path.unlink()
    directory_fd = os.open(RUNTIME, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def gated_launch(command, state, kind):
    current = load_state()
    if current is None and set(state) != {'version', 'boot_id', 'token'}:
        raise Failure('missing committed state with existing process records')
    if current is not None and current != state:
        raise Failure('state changed; refusing to overwrite process records')
    if kind in state:
        raise Failure(f'{kind} already recorded')
    read_fd, write_fd = os.pipe()
    error_read, error_write = os.pipe()
    try:
        pid = os.fork()
    except BaseException:
        for fd in (read_fd, write_fd, error_read, error_write):
            os.close(fd)
        raise
    if pid == 0:
        try:
            keep = sorted((read_fd, error_write))
            os.closerange(3, keep[0])
            os.closerange(keep[0] + 1, keep[1])
            os.closerange(keep[1] + 1, 2147483647)
            os.setsid()
            null = os.open(os.devnull, os.O_RDWR)
            for stream in (0, 1, 2):
                os.dup2(null, stream)
            if null > 2:
                os.close(null)
            if os.read(read_fd, 1) == b'1':
                os.close(read_fd)
                os.execvp(command[0], command)
        except BaseException:
            try:
                os.write(error_write, b'error')
            except OSError:
                pass
        os._exit(127)
    os.close(read_fd)
    os.close(error_write)
    released = False
    try:
        info = proc_info(pid)
        if not info:
            raise Failure(f'{kind} child exited before recording identity')
        record = {'pid': pid, 'start': info['start'], 'session_id': state['token'],
                  'phase': 'starting', 'command': list(command)}
        updated = {**state, kind: record}
        save_state(updated, initial=current is None)
        if os.write(write_fd, b'1') != 1:
            raise Failure(f'{kind} gate release failed')
        released = True
        if not select.select([error_read], [], [], START_WAIT)[0]:
            raise Failure(f'{kind} exec confirmation timed out; ownership unknown')
        if os.read(error_read, 16):
            os.waitpid(pid, 0)
            raise Failure(f'{kind} exec failed; state retained')
    except BaseException:
        os.close(write_fd)
        if not released:
            os.waitpid(pid, 0)
        raise
    finally:
        os.close(error_read)
    os.close(write_fd)
    return updated


def process_table():
    table = {}
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            info = proc_info(int(entry.name))
            if info:
                table[int(entry.name)] = info
    return table


def owned(token):
    found = {'x11': [], 'session': []}
    rootfs = str(PREFIX / 'var/lib/proot-distro/containers/debian/rootfs')
    for pid, info in process_table().items():
        args, joined = info['cmd'], ' '.join(info['cmd'])
        if (args and args[0].startswith('termux-x11 com.termux.x11 ') and
                DISPLAY in args[0].split() and f'LINUX_DESKTOP_INSTANCE={token}' in joined):
            found['x11'].append(pid)
        if (args and Path(args[0]).name == 'proot' and '--kill-on-exit' in args and
                any(arg.endswith('/debian/rootfs') and (arg == '--rootfs=' + rootfs or arg.startswith('--rootfs='))
                    for arg in args) and f'LINUX_DESKTOP_INSTANCE={token}' in joined):
            found['session'].append(pid)
    return found


def record_info(state, kind):
    record = state.get(kind)
    if not isinstance(record, dict) or record.get('session_id') != state['token']:
        return None
    info = proc_info(record.get('pid'))
    return info if info and info['start'] == record.get('start') else None


def descendants(root_pid, table=None):
    table = table or process_table()
    result, frontier = set(), {root_pid}
    while frontier:
        children = {pid for pid, info in table.items() if info['ppid'] in frontier} - result
        result.update(children)
        frontier = children
    return result


def session_tracees(state):
    info = record_info(state, 'session')
    if not info or not info['cmd'] or Path(info['cmd'][0]).name != 'proot':
        return None
    table = process_table()
    root_pid = state['session']['pid']
    tracees = {pid: table[pid] for pid in descendants(root_pid, table)
               if pid in table and table[pid]['tracer'] == root_pid}
    token = f'LINUX_DESKTOP_INSTANCE={state["token"]}'
    supervisors = [pid for pid, item in tracees.items()
                   if item['cmd'] and Path(item['cmd'][0]).name == 'sh' and token in ' '.join(item['cmd'])]
    if len(supervisors) != 1:
        return None
    return supervisors[0], tracees


def verified_fd(state, kind):
    info = record_info(state, kind)
    if not info:
        return None
    if kind == 'x11':
        if state['x11']['pid'] not in owned(state['token'])['x11']:
            raise Failure('X11 identity mismatch; refusing to signal')
    elif session_tracees(state) is None:
        raise Failure('PRoot tracee ownership unproven; refusing to signal')
    else:
        raise Failure('PRoot is tracer; never signal it directly')
    return pidfd_open(state[kind]['pid'])


def alive(state, kind):
    info = record_info(state, kind)
    if not info:
        return False
    if kind == 'x11':
        return state['x11']['pid'] in owned(state['token'])['x11']
    return session_tracees(state) is not None


def probe(*args):
    command = ['proot-distro', 'login', '--isolated', '--shared-tmp', '--env',
               'DISPLAY=' + DISPLAY, 'debian', '--', *args]
    try:
        return subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, text=True, timeout=PROBE_WAIT, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None


def component_probe():
    result = probe('sh', '-c',
        'id=$(xprop -root _NET_SUPPORTING_WM_CHECK 2>/dev/null) || exit 1; '
        'id=${id##* }; case "$id" in 0x[0-9a-fA-F]*) ;; *) exit 1;; esac; '
        'xprop -id "$id" _NET_WM_NAME 2>/dev/null | grep -qi xfwm4 && '
        'pgrep -x xfdesktop >/dev/null && pgrep -x xfce4-panel >/dev/null && '
        'pgrep -x xfce4-terminal >/dev/null')
    return bool(result and result.returncode == 0)


def desktop_ready(state):
    result = probe('xdpyinfo')
    return alive(state, 'x11') and alive(state, 'session') and bool(result and result.returncode == 0) and component_probe()


def display_occupied():
    if os.path.lexists(TMP / f'.X{DISPLAY_NUMBER}-lock') or os.path.lexists(TMP / f'.X11-unix/X{DISPLAY_NUMBER}'):
        return True
    number = int(DISPLAY_NUMBER)
    for family, address in ((socket.AF_UNIX, f'\0/tmp/.X11-unix/X{DISPLAY_NUMBER}'),
                            (socket.AF_INET, ('127.0.0.1', 6000 + number)),
                            (socket.AF_INET6, ('::1', 6000 + number))):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(.3)
                result = sock.connect_ex(address)
                if result == 0:
                    return True
                if result not in (errno.ENOENT, errno.ECONNREFUSED):
                    raise Failure(f'display {DISPLAY} probe failed: {os.strerror(result)}')
        except OSError as error:
            if error.errno not in (errno.EAFNOSUPPORT, errno.EPROTONOSUPPORT):
                raise
    return False


def status(state):
    if state is None:
        return 'UNKNOWN' if display_occupied() else 'STOPPED'
    running = {kind: alive(state, kind) for kind in ('x11', 'session')}
    if not any(running.values()):
        return 'UNKNOWN' if display_occupied() else 'STOPPED'
    if not all(running.values()):
        return 'FAILED'
    return 'RUNNING' if desktop_ready(state) else 'STARTING'


def stop(state):
    if state is None:
        return
    trace_data = session_tracees(state) if state.get('session') else None
    if state.get('session') and trace_data is None:
        raise Failure('PRoot tracee ownership is uncertain; refusing cleanup')
    x11_fd = verified_fd(state, 'x11') if state.get('x11') else None
    targets = []
    try:
        if trace_data:
            _, tracees = trace_data
            allowed = {'sh', 'sleep', 'xfsettingsd', 'xfwm4', 'xfdesktop', 'xfce4-panel',
                       'xfce4-terminal', 'xfce4-appfinder', 'dbus-run-session', 'dbus-daemon'}
            if any(not item['cmd'] or Path(item['cmd'][0]).name not in allowed for item in tracees.values()):
                raise Failure('unrecognized PRoot tracee; refusing cleanup')
            for pid in tracees:
                targets.append((pidfd_open(pid), pid))
        if x11_fd is not None:
            targets.append((x11_fd, state['x11']['pid']))
            x11_fd = None
        for fd, _ in targets:
            pidfd_signal(fd, signal.SIGTERM)
        deadline = time.monotonic() + STOP_WAIT
        for fd, pid in targets:
            if not select.select([fd], [], [], max(0, deadline - time.monotonic()))[0]:
                raise Failure(f'owned process {pid} did not exit; no forced kill performed')
        if state.get('session') and session_tracees(state):
            raise Failure('PRoot session remains; state retained')
        STATE.unlink(missing_ok=True)
    finally:
        for fd, _ in targets:
            os.close(fd)
        if x11_fd is not None:
            os.close(x11_fd)


def launch_x11(state):
    command = ['termux-x11', DISPLAY]
    LOG_DIR = RUNTIME / 'logs'
    LOG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    record = {'pid': os.getpid(), 'start': proc_info(os.getpid())['start'],
              'session_id': state['token'], 'phase': 'starting', 'command': command}
    updated = {**state, 'x11': record}
    save_state(updated, initial=True)
    log_path = LOG_DIR / 'x11.log'
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'ab') as log:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 start_new_session=True, close_fds=True,
                                 env={**os.environ, 'LINUX_DESKTOP_INSTANCE': state['token']})
    info = proc_info(child.pid)
    if not info:
        raise Failure('Termux:X11 exited before identity was recorded')
    record = {**record, 'pid': child.pid, 'start': info['start'], 'phase': 'running', 'log': str(log_path)}
    updated = {**updated, 'x11': record}
    save_state(updated)
    return updated


def launch_session(state):
    command = ['proot-distro', 'login', '--isolated', '--shared-tmp', '--env',
               'DISPLAY=' + DISPLAY, 'debian', '--', 'env',
               f'LINUX_DESKTOP_INSTANCE={state["token"]}', 'sh', str(COMPONENTS), DISPLAY]
    LOG_DIR = RUNTIME / 'logs'
    LOG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    record = {'pid': os.getpid(), 'start': proc_info(os.getpid())['start'],
              'session_id': state['token'], 'phase': 'starting', 'command': command}
    updated = {**state, 'session': record}
    save_state(updated)
    log_path = LOG_DIR / 'session.log'
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'ab') as log:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 start_new_session=True, close_fds=True,
                                 env={**os.environ, 'LINUX_DESKTOP_INSTANCE': state['token']})
    deadline = time.monotonic() + START_WAIT
    while time.monotonic() < deadline:
        matches = owned(state['token'])['session']
        if len(matches) == 1:
            info = proc_info(matches[0])
            if info:
                record = {**record, 'pid': matches[0], 'start': info['start'],
                          'phase': 'running', 'log': str(log_path)}
                updated = {**updated, 'session': record}
                save_state(updated)
                if session_tracees(updated):
                    return updated
        time.sleep(.1)
    raise Failure('PRoot ownership could not be verified; state retained')


def wait_for(predicate, state, kind, message, timeout=START_WAIT):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        if not alive(state, kind):
            raise Failure(f'{kind} exited before readiness')
        time.sleep(.3)
    raise Failure(message)


def start(state):
    if state is not None:
        current = status(state)
        if current == 'RUNNING':
            return
        if current != 'STOPPED':
            raise Failure(f'cannot replace session in state {current}')
        STATE.unlink(missing_ok=True)
    if display_occupied():
        raise Failure(f'display {DISPLAY} has existing endpoint; not removing it')
    fd = pidfd_open(os.getpid())
    try:
        pidfd_signal(fd, 0)
    finally:
        os.close(fd)
    state = {'version': 1, 'boot_id': boot_id(), 'token': uuid.uuid4().hex}
    save_state(state, initial=True)
    try:
        state = launch_x11(state)
        wait_for(lambda: bool((result := probe('xdpyinfo')) and result.returncode == 0),
                 state, 'x11', 'X11 readiness timed out')
        state = launch_session(state)
        wait_for(component_probe, state, 'session', 'XFCE readiness timed out')
    except BaseException:
        try:
            stop(state)
        except Exception as error:
            print(f'cleanup failed: {error}', file=sys.stderr)
        raise


def resume(state):
    if status(state) != 'RUNNING':
        raise Failure('desktop is not running; refusing to open viewer')


def open_viewer():
    result = subprocess.run(['am', 'start', '-n', 'com.termux.x11/.MainActivity'],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=10, check=False)
    if result.returncode:
        raise Failure('could not open Termux:X11 viewer')


def main(action):
    if action not in ('start', 'stop', 'status', 'resume'):
        raise Failure('unknown action')
    if action != 'status':
        RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
    if RUNTIME.is_symlink():
        raise Failure('runtime directory must not be a symlink')
    try:
        flags = os.O_RDONLY if action == 'status' else os.O_RDWR | os.O_CREAT
        fd = os.open(RUNTIME / 'lock', flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    except FileNotFoundError:
        if action != 'status':
            raise
        print('UNKNOWN' if display_occupied() else 'STOPPED')
        return 0
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise Failure('lock must be a regular file')
        deadline = time.monotonic() + LOCK_WAIT
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    print('BUSY')
                    return 2
                time.sleep(.05)
        state = load_state()
        if action == 'start':
            start(state)
            open_viewer()
            print('RUNNING')
        elif action == 'resume':
            resume(state)
            open_viewer()
            print('RUNNING')
        elif action == 'stop':
            stop(state)
            print('STOPPED')
        else:
            result = status(state)
            print(result)
            return 0 if result in ('RUNNING', 'STOPPED') else 1
        return 0
    finally:
        os.close(fd)


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1]))
    except Exception as error:
        print(f'linux-desktop: {error}', file=sys.stderr)
        print('ERROR')
        sys.exit(1)
