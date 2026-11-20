#!/usr/bin/env python3
"""Open web URLs in sandboxed Firefox on the existing tablet desktop."""
# ponytail: one tablet profile; add profile selection if other desktops need this helper.
import argparse
import fcntl
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import time
from urllib.parse import urlsplit

PREFIX = Path('/data/data/com.termux/files/usr')
BASE = Path('/data/data/com.termux/files/home/.local/share/linux-desktop/firefox-sandbox')
ROOTFS = PREFIX / 'var/lib/proot-distro/containers/debian/rootfs'
PROFILE = os.environ.get('LINUX_DESKTOP_PROFILE', '/root/.ld-test/xfce-config')
FIREFOX_PROFILE = PROFILE + '/mozilla/firefox/gtehrka8.default-esr'
NATIVE = PREFIX.is_dir()
SHARED_TMP = Path(os.environ.get('LINUX_DESKTOP_RUNTIME', str(PREFIX / 'tmp'))) if NATIVE else Path('/tmp')
RUNTIME = SHARED_TMP / 'linux-desktop-firefox-10528'
SOCKET = RUNTIME / 'open.sock'
GOOGLE = 'https://www.google.com/'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def web_url(value):
    require(isinstance(value, str) and 0 < len(value) <= 4096
            and not any(ord(c) < 32 or ord(c) == 127 for c in value), 'Invalid web URL')
    parsed = urlsplit(value)
    require(parsed.scheme in ('http', 'https') and bool(parsed.hostname), 'Only HTTP(S) URLs supported')
    return value


def browser_command(url):
    found = {name: [] for name in ('xfsettingsd', 'xfwm4', 'xfdesktop', 'xfce4-panel')}
    for process in Path('/proc').glob('[0-9]*'):
        try:
            name = (process / 'comm').read_text().strip()
            if name not in found:
                continue
            env = dict(x.split('=', 1) for x in (process / 'environ').read_bytes().decode().split('\0') if '=' in x)
            if env.get('DISPLAY') not in (':2', ':2.0') or env.get('XDG_CONFIG_HOME') != PROFILE:
                continue
            status = dict(x.split(':', 1) for x in (process / 'status').read_text().splitlines() if ':' in x)
            require(int(status['Uid'].split()[0]) == 10528 and env.get('HOME') == '/root'
                    and env.get('LIBGL_ALWAYS_SOFTWARE') == '1', 'Desktop ownership/rendering mismatch')
            if name == 'xfwm4':
                require(b'--compositor=off' in (process / 'cmdline').read_bytes(), 'Unexpected compositor')
            found[name].append((env, int(status['TracerPid'])))
        except (OSError, UnicodeError):
            continue
    require(all(len(rows) == 1 for rows in found.values()), 'Desktop :2 absent or ambiguous; use Home Resume')
    tracers = {rows[0][1] for rows in found.values()}
    require(len(tracers) == 1 and next(iter(tracers)) > 0, 'Desktop PRoot ownership mismatch')
    args = Path(f'/proc/{next(iter(tracers))}/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    require(args[0] == str(PREFIX / 'bin/proot') and '--rootfs=' + str(ROOTFS) in args
            and args.count('--change-id=0:0') == 1 and '/bin/bash' in args, 'Unexpected desktop PRoot command')
    if SHARED_TMP != PREFIX / 'tmp':
        require(f'--bind={SHARED_TMP}:/tmp' in args, 'Desktop runtime does not match the Firefox helper')
    args = [str(BASE / 'proot')] + args[1:args.index('/bin/bash')]
    args[args.index('--change-id=0:0')] = '--change-id=10528:10528'
    env = {k: found['xfsettingsd'][0][0][k] for k in (
        'HOME', 'DISPLAY', 'LIBGL_ALWAYS_SOFTWARE', 'XDG_CONFIG_HOME',
        'XDG_CACHE_HOME', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS')}
    env.update(PATH='/usr/local/bin:/usr/bin:/bin', LANG='C.UTF-8', USER='aid_u0_a528', LOGNAME='aid_u0_a528')
    for key in ('PULSE_SERVER', 'PULSE_COOKIE'):
        if value := found['xfsettingsd'][0][0].get(key):
            env[key] = value
    args += ['/usr/bin/env', '-i'] + [f'{k}={v}' for k, v in env.items()]
    args += ['/usr/bin/firefox-esr', '--profile', FIREFOX_PROFILE, '--new-tab', web_url(url)]
    native_env = dict(PATH=str(PREFIX / 'bin') + ':/system/bin', HOME=str(PREFIX.parent / 'home'),
                      TMPDIR=str(PREFIX / 'tmp'), LANG='en_US.UTF-8', PROOT_L2S_DIR=str(ROOTFS / '.l2s'),
                      PROOT_LOADER=str(BASE / 'loader'), PROOT_LOADER_32=str(BASE / 'loader32'))
    return args, native_env


def receive(connection):
    data = bytearray()
    while not data.endswith(b'\n'):
        chunk = connection.recv(8192 - len(data))
        require(chunk and len(data) + len(chunk) < 8192, 'Incomplete or oversized request')
        data.extend(chunk)
    return json.loads(data)


def request(payload):
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(5)
        connection.connect(str(SOCKET))
        connection.sendall(json.dumps(payload).encode() + b'\n')
        result = receive(connection)
    require(result.get('ok'), result.get('error', 'Firefox launcher failed'))
    return result


def serve():
    require(NATIVE and os.getuid() == 10528, 'Server must run in native Termux UID 10528')
    os.umask(0o077)
    RUNTIME.mkdir(mode=0o700, exist_ok=True)
    info = RUNTIME.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o700, 'Unsafe Firefox runtime directory')
    with (RUNTIME / 'server.lock').open('a') as lock, socket.socket(socket.AF_UNIX) as server:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if SOCKET.exists():
            require(stat.S_ISSOCK(SOCKET.lstat().st_mode), 'Unexpected Firefox socket path')
            SOCKET.unlink()  # Only this helper's socket, under its exclusive lock and private directory.
        server.bind(str(SOCKET))
        server.listen(4)
        children = []
        while True:
            connection, _ = server.accept()
            with connection:
                connection.settimeout(5)
                try:
                    payload = receive(connection)
                    require(isinstance(payload, dict), 'Invalid request')
                    if payload == {'ping': True}:
                        result = {'ok': True, 'pid': os.getpid(), 'display': ':2'}
                    else:
                        require(set(payload) == {'url'}, 'Unsupported request')
                        args, env = browser_command(payload['url'])
                        with (BASE / 'firefox.log').open('ab', buffering=0) as output:
                            child = subprocess.Popen(args, env=env, cwd=BASE, stdin=subprocess.DEVNULL,
                                                     stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
                        children = [p for p in children if p.poll() is None] + [child]
                        result = {'ok': True, 'proot_pid': child.pid}
                except Exception as error:
                    result = {'ok': False, 'error': str(error)}
                try:
                    connection.sendall(json.dumps(result).encode() + b'\n')
                except OSError:
                    pass


def ensure():
    require(NATIVE, 'Use Home Resume to start the native Firefox helper')
    try:
        return request({'ping': True})
    except OSError:
        pass
    browser_command(GOOGLE)  # Refuse startup without the verified desktop.
    with (BASE / 'helper.log').open('ab', buffering=0) as output:
        child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--serve'], stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(30):
        try:
            return request({'ping': True})
        except OSError:
            require(child.poll() is None, 'Firefox helper exited; inspect helper.log')
            time.sleep(0.1)
    raise RuntimeError('Firefox helper startup timed out')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--serve', action='store_true')
    mode.add_argument('--ensure', action='store_true')
    mode.add_argument('--check', action='store_true')
    parser.add_argument('url', nargs='?', default=GOOGLE)
    args = parser.parse_args()
    if args.serve:
        serve()
    elif args.ensure:
        print(json.dumps(ensure()))
    elif args.check:
        for bad in ('', '--no-sandbox', 'file:///etc/passwd', 'https://', 'https://google.com/\n'):
            try:
                web_url(bad)
            except (RuntimeError, ValueError):
                continue
            raise RuntimeError('Invalid URL accepted')
        require(web_url(GOOGLE) == GOOGLE, 'Valid URL rejected')
        if NATIVE:
            command, env = browser_command(GOOGLE)
            require(not any('SANDBOX' in x for x in command + list(env)), 'Unexpected sandbox override')
            subprocess.run([str(BASE / 'proot'), '-r', '/', str(BASE / 'check-firefox-seccomp')],
                           env=env, check=True, timeout=15)
        print('PASS: URL validation; Firefox helper', json.dumps(request({'ping': True})))
    else:
        print(json.dumps(request({'url': web_url(args.url)})))


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f'Firefox: {error}. If helper unavailable, tap Home Resume.', file=sys.stderr)
        sys.exit(1)
