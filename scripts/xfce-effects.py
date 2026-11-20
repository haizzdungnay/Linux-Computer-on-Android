#!/usr/bin/env python3
"""Manual Picom controls for the tablet's verified Debian XFCE session."""
import argparse
import ctypes as C
import fcntl
import os
from pathlib import Path
import runpy
import select
import signal
import subprocess
import time


# ponytail: one profile, one backend. Add session selection only with lifecycle support.
BASE = Path('/root/.local/share/linux-desktop/picom-xfce')
PICOM = BASE / 'usr/bin/picom'
COMMAND = [str(PICOM), '--backend', 'xrender', '--config', str(BASE / 'picom.conf')]
DISPLAY = os.environ.get('DISPLAY', ':2').removesuffix('.0') + '.0'
CONTROL = Path(os.environ['XDG_RUNTIME_DIR']) if Path('/tmp/xfce-ready').is_file() else BASE


def owner():
    xlib = C.CDLL('libX11.so.6')
    for name, args, result in (
        ('XOpenDisplay', [C.c_char_p], C.c_void_p),
        ('XInternAtom', [C.c_void_p, C.c_char_p, C.c_int], C.c_ulong),
        ('XGetSelectionOwner', [C.c_void_p, C.c_ulong], C.c_ulong),
        ('XCloseDisplay', [C.c_void_p], C.c_int),
    ):
        function = getattr(xlib, name)
        function.argtypes, function.restype = args, result
    display = xlib.XOpenDisplay(DISPLAY.encode())
    if not display:
        raise RuntimeError(f'Cannot open {DISPLAY}')
    try:
        atom = xlib.XInternAtom(display, b'_NET_WM_CM_S0', 1)
        return xlib.XGetSelectionOwner(display, atom) if atom else 0
    finally:
        xlib.XCloseDisplay(display)


def start_time(process):
    return (process / 'stat').read_text().rsplit(')', 1)[1].split()[19]


def maps_picom(process):
    # PRoot can expose its loader via /proc/PID/exe. Match the executable mapping.
    binary = PICOM.stat()
    for line in (process / 'maps').read_text().splitlines():
        _, permissions, _, device, inode, *_ = line.split(maxsplit=5)
        if 'x' in permissions and int(inode) == binary.st_ino:
            major, minor = (int(part, 16) for part in device.split(':'))
            if os.makedev(major, minor) == binary.st_dev:
                return True
    return False


def owned_process():
    fd = None
    try:
        pid, started = (CONTROL / 'pid').read_text().split()
        fd = os.pidfd_open(int(pid))
        process = Path('/proc') / pid
        if start_time(process) == started:
            args = (process / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
            env = (process / 'environ').read_bytes().split(b'\0')
            if (args == [os.fsencode(arg) for arg in COMMAND]
                    and maps_picom(process)
                    and os.fsencode('DISPLAY=' + DISPLAY) in env and b'LIBGL_ALWAYS_SOFTWARE=1' in env):
                return fd
    except (FileNotFoundError, ProcessLookupError):
        pass
    except Exception:
        if fd is not None:
            os.close(fd)
        raise
    if fd is not None:
        os.close(fd)
    return None


def stop(fd):
    poller = select.poll()
    poller.register(fd, select.POLLIN)
    try:
        signal.pidfd_send_signal(fd, signal.SIGTERM)
        if not poller.poll(2000):
            signal.pidfd_send_signal(fd, signal.SIGKILL)
            if not poller.poll(2000):
                raise RuntimeError('Picom did not exit after SIGKILL')
    except ProcessLookupError:
        pass


def exit_on_signal(signum, _frame):
    raise SystemExit(128 + signum)


def run(seconds):
    for event in (signal.SIGHUP, signal.SIGTERM):
        signal.signal(event, exit_on_signal)
    if CONTROL == BASE:
        runpy.run_path(str(BASE.parent / 'style-tablet-xfce.py'))['session']()
    elif not os.environ.get('DBUS_SESSION_BUS_ADDRESS') or os.environ.get('LIBGL_ALWAYS_SOFTWARE') != '1':
        raise RuntimeError('Run from the managed XFCE session')
    compositor = subprocess.check_output([
        'xfconf-query', '-c', 'xfwm4', '-p', '/general/use_compositing',
    ], text=True, timeout=5).strip()
    if compositor != 'false':
        raise RuntimeError('Xfwm4 compositing must be off')

    child = None
    fd = None
    try:
        with (CONTROL / 'control.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            existing_fd = owned_process()
            if existing_fd is not None:
                os.close(existing_fd)
                print('Effects already running')
                return
            if existing := owner():
                raise RuntimeError(f'Compositor selection already owned by {existing:#x}')

            env = dict(os.environ, DISPLAY=DISPLAY, LIBGL_ALWAYS_SOFTWARE='1',
                       LD_LIBRARY_PATH=str(BASE / 'usr/lib/aarch64-linux-gnu'))
            with (BASE / 'picom.log').open('w') as log:
                child = subprocess.Popen(COMMAND, env=env, stdin=subprocess.DEVNULL,
                                         stdout=log, stderr=subprocess.STDOUT)
            fd = os.pidfd_open(child.pid)
            pid_file = CONTROL / 'pid.next'
            pid_file.write_text(f'{child.pid} {start_time(Path(f"/proc/{child.pid}"))}\n')
            pid_file.replace(CONTROL / 'pid')

        print(f'Picom PID {child.pid}, xrender on {DISPLAY}, limit {seconds}', flush=True)
        result = child.wait(timeout=seconds)
        if result not in (0, -signal.SIGTERM, -signal.SIGKILL):
            raise RuntimeError(f'Picom exited {result}. See {BASE / "picom.log"}')
    except subprocess.TimeoutExpired:
        print('Trial time expired', flush=True)
    finally:
        if child is not None and child.poll() is None:
            if fd is None:
                child.kill()
            else:
                stop(fd)
            child.wait()
        if fd is not None:
            os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['run', 'off', 'status'])
    parser.add_argument('seconds', type=int, nargs='?')
    args = parser.parse_args()
    if args.seconds is not None and (args.action != 'run' or not 1 <= args.seconds <= 120):
        parser.error('run trial limit must be 1-120 seconds')

    if args.action == 'run':
        run(args.seconds)
        return
    with (CONTROL / 'control.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        fd = owned_process()
        try:
            if args.action == 'off':
                if fd is not None:
                    stop(fd)
                print('Managed Picom stopped' if fd is not None else 'No managed Picom running')
            else:
                print(f'Owned Picom: {fd is not None}, X11 selection: {owner():#x}')
        finally:
            if fd is not None:
                os.close(fd)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, AssertionError, subprocess.SubprocessError) as error:
        raise SystemExit(f'XFCE effects: {error}') from error
