#!/usr/bin/env python3
"""Start, inspect, or reopen the isolated Fedora 45 PRoot XFCE session from Termux."""
import ctypes
import errno
import fcntl
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time


PREFIX = Path('/data/data/com.termux/files/usr')
HOME = Path('/data/data/com.termux/files/home')
BASE = HOME / '.local/share/fedora45-desktop'
CONTAINER = 'fedora45'
INSTALL = '/root/.local/share/fedora45-desktop'
PROFILE = '/root/.config/fedora45-xfce'
DISPLAY = ':7'
VNC_HOST = '127.0.0.1'
VNC_PORT = 5907
AVNC_PACKAGE = 'com.gaurav.avnc'
AVNC_URI = 'vnc://?ConnectionName=Fedora'
TMP = PREFIX / 'tmp'
ROOTFS = PREFIX / 'var/lib/proot-distro/containers' / CONTAINER / 'rootfs'
READY = BASE / 'workstation.ready'
LOCK = BASE / 'workstation.lock'
PR_SET_PDEATHSIG = 1


def tcp_open(host=VNC_HOST, port=VNC_PORT, timeout=0.5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except OSError as error:
            if error.errno in (errno.ECONNREFUSED, errno.ETIMEDOUT, errno.ENETUNREACH):
                return False
            return False


def deadline(seconds, probe, *children):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        for child in children:
            if child.poll() is not None:
                raise RuntimeError(f'{Path(child.args[0]).name} exited ({child.returncode})')
        if probe():
            return
        time.sleep(0.2)
    raise RuntimeError('Startup timed out')


def stop_proc(child, timeout=8, *, pgid=False):
    if child is None:
        return
    if child.poll() is None:
        if pgid:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        else:
            child.terminate()
    try:
        child.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if pgid:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            child.kill()
        child.wait(timeout=4)


def command(*args, env=None, timeout=8):
    return subprocess.run(
        args, stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, timeout=timeout
    )


def spawn(args, env, log_name, *, stop_with_parent=True, new_session=False):
    parent = os.getpid()
    libc = ctypes.CDLL(None, use_errno=True)

    def bind_to_parent():
        if libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM, 0, 0, 0) or os.getppid() != parent:
            os._exit(125)

    with (BASE / log_name).open('ab') as output:
        return subprocess.Popen(
            args,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            preexec_fn=bind_to_parent if stop_with_parent else None,
            start_new_session=new_session,
        )


def start_audio(runtime, env):
    cookie = runtime / 'pulse-cookie'
    cookie.write_bytes(os.urandom(256))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    server = f'tcp:127.0.0.1:{port}'
    sink = 'module-sles-sink sink_name=fedora_tablet'
    auth = f'module-native-protocol-tcp listen=127.0.0.1 port={port} auth-cookie={cookie}'
    pulse = spawn(
        [
            'pulseaudio',
            '-n',
            '--daemonize=no',
            '--use-pid-file=no',
            '--exit-idle-time=-1',
            '-L', auth,
            '-L', sink,
        ],
        {**env, 'PULSE_RUNTIME_PATH': str(runtime), 'PULSE_STATE_PATH': str(runtime)},
        'workstation-audio.log',
    )
    try:
        deadline(
            8,
            lambda: command(
                'pactl', '-s', server, 'list', 'short', 'sinks',
                env={**env, 'PULSE_COOKIE': str(cookie)},
            ).stdout.split()[1:2] == ['fedora_tablet'],
            pulse,
        )
    except BaseException:
        stop_proc(pulse)
        raise
    return pulse, server


def ensure_writable_rootfs():
    mode = ROOTFS.stat().st_mode & 0o777
    if not (mode & 0o200):
        os.chmod(ROOTFS, mode | 0o200)


def reap_pgid(pid):
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    time.sleep(0.3)
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def serve(lock_fd):
    os.fstat(lock_fd)
    ensure_writable_rootfs()
    with tempfile.TemporaryDirectory(prefix='f45-work-', dir=TMP) as directory:
        os.chmod(directory, 0o700)
        runtime = Path(directory)
        env = {
            **os.environ,
            'TMPDIR': directory,
            'LINUX_DESKTOP_RUNTIME': directory,
            'LINUX_DESKTOP_PROFILE': PROFILE,
        }
        args = [
            'proot-distro', 'login', '--isolated',
            '--bind', f'{directory}:/tmp',
            CONTAINER, '--',
            '/bin/sh', f'{INSTALL}/fedora-session.sh', DISPLAY, str(VNC_PORT), PROFILE,
        ]
        audio = None
        session = None
        try:
            audio, pulse_server = start_audio(runtime, env)
            session = spawn(
                args + [pulse_server],
                env,
                'workstation-xfce.log',
                stop_with_parent=False,
                new_session=True,
            )
            deadline(
                55,
                lambda: (runtime / 'xfce-ready').is_file() and tcp_open(VNC_HOST, VNC_PORT),
                audio,
                session,
            )
            staged = runtime / 'ready.json'
            staged.write_text(json.dumps({
                'runtime': directory,
                'display': DISPLAY,
                'vnc_port': VNC_PORT,
                'session_pid': session.pid,
                'audio_pid': audio.pid,
                'serve_pid': os.getpid(),
            }) + '\n')
            staged.replace(READY)
            while session.poll() is None:
                if audio.poll() is not None:
                    # Audio restarted only if needed; keep XFCE alive.
                    pass
                time.sleep(0.25)
        finally:
            READY.unlink(missing_ok=True)
            if session is not None:
                if session.poll() is None:
                    stop_proc(session, timeout=12, pgid=True)
                reap_pgid(session.pid)
            stop_proc(audio, timeout=6)
            if session is not None and session.returncode not in (0, -signal.SIGTERM, None):
                raise RuntimeError(f'Fedora XFCE exited ({session.returncode})')


def read_ready():
    try:
        data = json.loads(READY.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    runtime = Path(data.get('runtime', ''))
    pid = data.get('serve_pid')
    if not runtime.is_dir() or not isinstance(pid, int):
        return None
    if not Path(f'/proc/{pid}').is_dir():
        return None
    if not tcp_open(VNC_HOST, int(data.get('vnc_port', VNC_PORT))):
        return None
    return data


def launch_avnc():
    res = command(
        'am', 'start', '--user', '0',
        '-a', 'android.intent.action.VIEW',
        '-d', AVNC_URI,
        AVNC_PACKAGE,
    )
    if res.returncode or 'Error:' in res.stdout or 'Error:' in res.stderr:
        raise RuntimeError(f'Android rejected AVNC viewer: {res.stdout} {res.stderr}'.strip())
    return res.stdout.strip()


def open_desktop():
    BASE.mkdir(mode=0o700, parents=True, exist_ok=True)
    with LOCK.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # Another invocation owns startup or the live session.
            deadline(60, lambda: read_ready() is not None)
        else:
            if tcp_open(VNC_HOST, VNC_PORT):
                raise RuntimeError(f'Port {VNC_HOST}:{VNC_PORT} is already in use outside managed session')
            READY.unlink(missing_ok=True)
            with (BASE / 'workstation-launch.log').open('ab') as log:
                fd = lock.fileno()
                child = subprocess.Popen(
                    [sys.executable, __file__, 'serve', str(fd)],
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    pass_fds=(fd,),
                    start_new_session=True,
                )
            deadline(60, lambda: read_ready() is not None, child)
    out = launch_avnc()
    print('Fedora 45 is running')
    if out:
        print(out)
    return 0


def status():
    data = read_ready()
    if data is None:
        print(json.dumps({'running': False}))
        return 1
    print(json.dumps({'running': True, **data}))
    return 0


def interrupted(signum, _frame):
    raise SystemExit(128 + signum)


if __name__ == '__main__':
    os.umask(0o077)
    try:
        BASE.mkdir(mode=0o700, parents=True, exist_ok=True)
        if BASE.stat().st_uid != os.getuid() or (BASE.stat().st_mode & 0o077):
            os.chmod(BASE, 0o700)
        if sys.argv[1:] == ['open']:
            sys.exit(open_desktop())
        if sys.argv[1:] == ['status']:
            sys.exit(status())
        if len(sys.argv) == 3 and sys.argv[1] == 'serve':
            for sig in (signal.SIGHUP, signal.SIGTERM):
                signal.signal(sig, interrupted)
            serve(int(sys.argv[2]))
            sys.exit(0)
        raise RuntimeError('Usage: fedora-workstation.py [open|status]')
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(f'Fedora: {error}. See {BASE / "workstation-launch.log"}.') from error
