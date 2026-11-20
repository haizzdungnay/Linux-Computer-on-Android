#!/usr/bin/env python3
"""Session controls opened by XFCE's power button."""
import os
from pathlib import Path
import re
import runpy
import select
import signal
import socket
import struct
import subprocess
import time


BASE = Path('/root/.local/share/linux-desktop')
PREFIX = '/data/data/com.termux/files/usr'
MANAGED = Path('/tmp/xfce-ready').is_file()


def xprop(*args):
    return subprocess.check_output(['xprop', *args], text=True, timeout=4)


def app_windows():
    listing = xprop('-root', '_NET_CLIENT_LIST')
    if 'window id #' not in listing:
        raise RuntimeError('Cannot verify which windows are open')
    windows = []
    for window in re.findall(r'0x[0-9a-f]+', listing):
        try:
            kind = xprop('-id', window, '_NET_WM_WINDOW_TYPE')
        except subprocess.CalledProcessError:
            continue  # Window disappeared while checking.
        if not any(f'_NET_WM_WINDOW_TYPE_{name}' in kind for name in ('DESKTOP', 'DOCK')):
            windows.append(window)
    return windows


def close_apps():
    for window in app_windows():
        try:
            protocols = xprop('-id', window, 'WM_PROTOCOLS').replace(',', '').split()
            if 'WM_DELETE_WINDOW' in protocols:
                subprocess.run(['wmctrl', '-ic', window], check=True, timeout=4)
        except subprocess.CalledProcessError:
            if window in app_windows():
                raise
    deadline = time.monotonic() + 3
    while app_windows():
        if time.monotonic() >= deadline:
            return False
        time.sleep(.15)
    return True


def peer(path):
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(2)
        client.connect(path)
        return struct.unpack('3i', client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[:2]


def terminate(pid, command):
    with_pid = os.pidfd_open(pid)
    try:
        status = Path(f'/proc/{pid}')
        cmd = (status / 'cmdline').read_bytes().strip(b'\0').split(b'\0')
        if status.stat().st_uid != os.getuid() or cmd != command:
            raise RuntimeError('Original helper identity changed')
        signal.pidfd_send_signal(with_pid, signal.SIGTERM)
        poller = select.poll()
        poller.register(with_pid, select.POLLIN)
        if not poller.poll(2000):
            raise RuntimeError('Original helper did not exit')
    finally:
        os.close(with_pid)


def stop_legacy():
    # Only the original :2 server and the matching private Firefox helper are in scope.
    try:
        runpy.run_path(str(BASE / 'style-tablet-xfce.py'))['session']()
    except AssertionError as error:
        raise RuntimeError('Không xác minh được phiên XFCE cũ.') from error
    x11 = '/tmp/.X11-unix/X2'
    pid, uid = peer(x11)
    x11_fd = os.pidfd_open(pid)
    try:
        if (uid != os.getuid() or int(Path('/tmp/.X2-lock').read_text()) != pid
                or peer(x11) != (pid, uid)
                or Path(f'/proc/{pid}/cmdline').read_bytes().strip(b'\0') != b'termux-x11 com.termux.x11 :2'):
            raise RuntimeError('The original display is no longer the verified :2 server')
        stop_legacy_firefox()
        # The old publisher watched for the socket file, which X11 can leave behind.
        battery = PREFIX + '/var/lib/proot-distro/containers/debian/rootfs' + str(BASE / 'tablet-battery.py')
        command = [os.fsencode(PREFIX + '/bin/python'), os.fsencode(battery), b'publish']
        for process in Path('/proc').glob('[0-9]*'):
            try:
                if (process / 'cmdline').read_bytes().strip(b'\0').split(b'\0') == command:
                    terminate(int(process.name), command)
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
        # The old XFCE components exit on disconnect. PRoot then reaps its tracees.
        signal.pidfd_send_signal(x11_fd, signal.SIGTERM)
    finally:
        os.close(x11_fd)


def stop_legacy_firefox():
    helper = '/tmp/linux-desktop-firefox-10528/open.sock'
    try:
        pid, uid = peer(helper)
    except (FileNotFoundError, ConnectionRefusedError, ProcessLookupError):
        return
    command = [os.fsencode(PREFIX + '/bin/python'),
               b'/data/data/com.termux/files/home/.local/share/linux-desktop/firefox-sandbox/firefox-tablet.py',
               b'--serve']
    if uid != os.getuid():
        raise RuntimeError('Unexpected Firefox helper owner')
    terminate(pid, command)


def dialog(*options):
    return subprocess.run(['yad', '--center', '--width=420', '--title=Linux', *options]).returncode


def main():
    action = dialog('--text=Linux sẽ yêu cầu đóng ứng dụng rồi đăng xuất. Mở lại từ Linux Resume trên Android.\n'
                    'Bấm nút nguồn tablet để ngủ. Giữ Nguồn + Tăng âm lượng để mở menu nguồn Android.',
                    '--button=Hủy:1', '--button=Đăng xuất và tắt Linux:3')
    if action == 3:
        if not close_apps():
            dialog('--text=Ứng dụng vẫn đang mở. Xử lý hộp thoại lưu hoặc đóng cửa sổ còn lại rồi thử lại.',
                   '--button=OK:0')
        elif MANAGED:
            subprocess.run(['xfce4-session-logout', '--logout'], check=True, timeout=10)
        else:
            stop_legacy()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        dialog(f'--text=Chưa tắt được Linux.\n{error}', '--no-markup', '--button=OK:0')
        raise SystemExit(str(error)) from error
