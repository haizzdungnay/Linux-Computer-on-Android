#!/usr/bin/env python3
"""Start or reopen the tablet's managed Debian XFCE session from Termux."""
import ctypes
import errno
import fcntl
import os
from pathlib import Path
import secrets
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time


PREFIX = Path('/data/data/com.termux/files/usr')
BASE = PREFIX.parent / 'home/.local/share/linux-desktop'
INSTALL = '/root/.local/share/linux-desktop'
ROOTFS = PREFIX / 'var/lib/proot-distro/containers/debian/rootfs'
PROFILE = '/root/.ld-test/xfce-config'
DISPLAY = ':2'
VIEWER_PACKAGE = 'com.termux.x11'
TMP = PREFIX / 'tmp'
READY = BASE / 'workstation.ready'
PR_SET_PDEATHSIG = 1


def listener(path):
    with socket.socket(socket.AF_UNIX) as sock:
        sock.settimeout(.5)
        try:
            sock.connect(str(path))
        except OSError as error:
            if error.errno in (errno.ENOENT, errno.ECONNREFUSED):
                return None
            raise
        return struct.unpack('3i', sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[:2]


def x_endpoint(runtime):
    return Path(runtime) / '.X11-unix' / f'X{DISPLAY[1:]}'


def deadline(seconds, probe, *children):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        for child in children:
            if child.poll() is not None:
                raise RuntimeError(f'{Path(child.args[0]).name} exited ({child.returncode})')
        if probe():
            return
        time.sleep(.15)
    raise RuntimeError('Startup timed out')


def stop(child):
    if child.poll() is None:
        child.terminate()
    child.wait(timeout=6)


def command(*args, env=None):
    return subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, timeout=7)


def spawn(args, env, log, *, stop_with_parent=True):
    parent = os.getpid()
    libc = ctypes.CDLL(None, use_errno=True)

    def bind_to_parent():
        if libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM, 0, 0, 0) or os.getppid() != parent:
            os._exit(125)

    with (BASE / log).open('ab') as output:
        return subprocess.Popen(args, env=env, stdin=subprocess.DEVNULL,
                                stdout=output, stderr=subprocess.STDOUT,
                                preexec_fn=bind_to_parent if stop_with_parent else None)


def start_audio(runtime, env):
    cookie = runtime / 'pulse-cookie'
    cookie.write_bytes(secrets.token_bytes(256))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    server = f'tcp:127.0.0.1:{port}'
    sink = 'module-sles-sink sink_name=tablet'
    auth = f'module-native-protocol-tcp listen=127.0.0.1 port={port} auth-cookie={cookie}'
    pulse = spawn(['pulseaudio', '-n', '--daemonize=no', '--use-pid-file=no', '--exit-idle-time=-1',
                   '-L', auth, '-L', sink],
                  {**env, 'PULSE_RUNTIME_PATH': str(runtime), 'PULSE_STATE_PATH': str(runtime)},
                  'workstation-audio.log')
    try:
        deadline(6, lambda: command('pactl', '-s', server, 'list', 'short', 'sinks',
                                    env={**env, 'PULSE_COOKIE': str(cookie)}).stdout.split()[1:2] == ['tablet'], pulse)
    except BaseException:
        stop(pulse)
        raise
    return pulse, server


def serve(lock_fd):
    # Keep the inherited flock until XFCE, its display and native helpers have exited.
    os.fstat(lock_fd)
    with tempfile.TemporaryDirectory(prefix='ld-work-', dir=TMP) as directory:
        runtime = Path(directory)
        env = {**os.environ, 'TMPDIR': directory, 'LINUX_DESKTOP_RUNTIME': directory,
               'LINUX_DESKTOP_PROFILE': PROFILE, 'TERMUX_X11_OVERRIDE_PACKAGE': VIEWER_PACKAGE}
        args = ['proot-distro', 'login', '--isolated', '--bind', directory + ':/tmp', 'debian', '--']
        x11 = spawn(['termux-x11', DISPLAY, '-nolisten', 'tcp', '-noreset'],
                    env, 'workstation-x11.log')
        helpers = []
        session = None
        try:
            deadline(10, lambda: listener(x_endpoint(runtime)) == (x11.pid, os.getuid()), x11)
            audio, server = start_audio(runtime, env)
            helpers.append(audio)
            session = spawn(args + ['sh', INSTALL + '/tablet-session.sh', DISPLAY, PROFILE, server],
                            env, 'workstation-xfce.log', stop_with_parent=False)
            deadline(35, lambda: (runtime / 'xfce-ready').is_file(), x11, session)
            battery = ROOTFS / INSTALL.lstrip('/') / 'tablet-battery.py'
            helpers.append(spawn([sys.executable, str(battery), 'publish'], env, 'workstation-battery.log'))
            firefox = PREFIX.parent / 'home/.local/share/linux-desktop/firefox-sandbox/firefox-tablet.py'
            helpers.append(spawn([sys.executable, str(firefox), '--serve'], env, 'workstation-firefox.log'))
            staged = runtime / 'ready'
            staged.write_text(f'{directory}\n{x11.pid}\n')
            staged.replace(READY)
            while x11.poll() is None and session.poll() is None:
                time.sleep(.25)
        finally:
            READY.unlink(missing_ok=True)
            try:
                stop(x11)
                if session is not None:
                    # PRoot reaps its tracees when the main Debian command exits.
                    session.wait(timeout=12)
            finally:
                for child in reversed(helpers):
                    stop(child)
            if session is not None and session.returncode:
                raise RuntimeError(f'XFCE exited ({session.returncode})')
            if VIEWER_PACKAGE == 'com.termux.x11':
                command('am', 'broadcast', '--user', '0', '-a', 'com.termux.x11.ACTION_STOP',
                        '-p', VIEWER_PACKAGE)


def legacy_audio():
    # Existing X11 clients can keep their original D-Bus and profile until the first logout.
    with (BASE / 'workstation-legacy-audio.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        endpoint = x_endpoint(TMP)
        original = listener(endpoint)
        if not original or original[1] != os.getuid():
            raise RuntimeError('Original display is absent')
        with tempfile.TemporaryDirectory(prefix='ld-audio-', dir=TMP) as directory:
            env = {**os.environ, 'TMPDIR': directory}
            pulse, server = start_audio(Path(directory), env)
            try:
                config = ROOTFS / 'root/.config/pulse'
                config.mkdir(mode=0o700, exist_ok=True)
                client = config / 'client.conf'
                if client.exists():
                    raise RuntimeError('Pulse client configuration already exists')
                setup = (f"autospawn = no\ndefault-server = {server}\n"
                         f"cookie-file = /tmp/{Path(directory).name}/pulse-cookie\n")
                with client.open('x') as output:
                    output.write(setup)
                try:
                    while pulse.poll() is None and listener(endpoint) == original:
                        time.sleep(.5)
                finally:
                    if client.is_file() and client.read_text() == setup:
                        client.unlink()
            finally:
                stop(pulse)


def ready():
    try:
        directory, pid = READY.read_text().splitlines()
    except FileNotFoundError:
        return False
    return listener(x_endpoint(directory)) == (int(pid), os.getuid())


def open_desktop():
    with (BASE / 'workstation.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            children = ()
        else:
            if listener(x_endpoint(TMP)):
                return 3  # Existing manual desktop. The widget uses its verified Resume path.
            for endpoint in [*(TMP / '.X11-unix').glob('X*'), *TMP.glob('ld-work-*/.X11-unix/X*')]:
                if listener(endpoint):
                    raise RuntimeError('Another Termux:X11 server is using the viewer')
            READY.unlink(missing_ok=True)
            with (BASE / 'workstation-launch.log').open('ab') as log:
                fd = lock.fileno()
                child = subprocess.Popen([sys.executable, __file__, 'serve', str(fd)],
                                         stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                         pass_fds=(fd,), start_new_session=True)
            children = (child,)
        deadline(45, ready, *children)
    viewer = command('am', 'start', '--user', '0', '-n', f'{VIEWER_PACKAGE}/.MainActivity')
    if viewer.returncode or 'Error:' in viewer.stdout or 'Error:' in viewer.stderr:
        raise RuntimeError('Android rejected the Termux:X11 viewer')
    print('Linux is running')
    return 0


def interrupted(signum, _frame):
    raise SystemExit(128 + signum)


if __name__ == '__main__':
    os.umask(0o077)
    try:
        if BASE.stat().st_uid != os.getuid() or BASE.stat().st_mode & 0o077:
            raise RuntimeError('Workstation directory must be private to Termux')
        if sys.argv[1:] == ['open']:
            sys.exit(open_desktop())
        if sys.argv[1:] == ['legacy-audio']:
            legacy_audio()
            sys.exit(0)
        if len(sys.argv) != 3 or sys.argv[1] != 'serve':
            raise RuntimeError('Usage: tablet-workstation.py open')
        for signum in (signal.SIGHUP, signal.SIGTERM):
            signal.signal(signum, interrupted)
        serve(int(sys.argv[2]))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(f'Linux: {error}. See {BASE / "workstation-launch.log"}.') from error
