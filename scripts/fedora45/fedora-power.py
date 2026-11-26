#!/usr/bin/env python3
"""Safe shutdown controller for Fedora 45 XFCE session."""
import argparse
import re
import subprocess
import time


def xprop(*args):
    return subprocess.check_output(['xprop', *args], text=True, timeout=4)


def app_windows():
    listing = xprop('-root', '_NET_CLIENT_LIST')
    if 'window id #' not in listing:
        return []
    windows = []
    for window in re.findall(r'0x[0-9a-f]+', listing):
        try:
            kind = xprop('-id', window, '_NET_WM_WINDOW_TYPE')
        except subprocess.CalledProcessError:
            continue
        if not any(f'_NET_WM_WINDOW_TYPE_{name}' in kind for name in ('DESKTOP', 'DOCK', 'SPLASH')):
            windows.append(window)
    return windows


def close_apps(timeout_sec=4.0):
    for window in app_windows():
        try:
            protocols = xprop('-id', window, 'WM_PROTOCOLS').replace(',', '').split()
            if 'WM_DELETE_WINDOW' in protocols:
                subprocess.run(['wmctrl', '-ic', window], check=False, timeout=4)
        except subprocess.CalledProcessError:
            continue
    deadline = time.monotonic() + timeout_sec
    while app_windows():
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.15)
    return True


def dialog(*options):
    return subprocess.run(
        ['zenity', '--width=400', '--title=Fedora 45', *options],
        check=False,
    ).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yes', action='store_true', help='Skip initial confirmation prompt')
    args = parser.parse_args()

    if not args.yes:
        rc = dialog(
            '--question',
            '--ok-label=Tắt Fedora',
            '--cancel-label=Hủy',
            '--text=Fedora sẽ yêu cầu các ứng dụng đóng và cho phép lưu dữ liệu trước khi tắt.\n'
            'Nếu có ứng dụng đang chờ xác nhận lưu, phiên sẽ tiếp tục mở.',
        )
        if rc != 0:
            return 0

    if not close_apps():
        if not args.yes:
            dialog(
                '--info',
                '--ok-label=OK',
                '--text=Vẫn còn ứng dụng đang mở hoặc đang chờ xác nhận lưu.\n'
                'Hãy lưu/đóng cửa sổ rồi bấm Tắt Fedora lại.',
            )
        print('KEPT_OPEN: applications still open or awaiting save confirmation')
        return 2

    subprocess.run(['xfce4-session-logout', '--logout'], check=True, timeout=10)
    print('LOGOUT_SENT')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        try:
            dialog('--error', f'--text=Chưa tắt được Fedora.\n{error}')
        except Exception:
            pass
        raise SystemExit(str(error)) from error
