#!/usr/bin/env python3
"""Publish Android battery capacity in Termux and display it in XFCE Genmon."""
import fcntl
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time


SCRIPT = Path(__file__).resolve()
STATE = SCRIPT.with_name('tablet-battery.state')
X_SOCKET = Path(os.environ.get('LINUX_DESKTOP_RUNTIME', '/data/data/com.termux/files/usr/tmp')) / '.X11-unix/X2'
PERIOD = 15


def display_live():
    with socket.socket(socket.AF_UNIX) as listener:
        listener.settimeout(1)
        try:
            listener.connect(str(X_SOCKET))
        except OSError:
            return False
        return True


def capacity(reply):
    # ponytail: Android 16 Parcel layout on this tablet. Use BatteryManager in an APK port.
    rows = re.findall(r'^\s*0x[0-9a-f]+:\s+([0-9a-f]{8}(?: [0-9a-f]{8})*)', reply, re.M)
    words = [int(word, 16) for row in rows for word in row.split()]
    if len(words) < 5 or words[:3] != [0, 0, 1] or words[4] != 0 or words[3] > 100:
        raise ValueError('Android battery capacity unavailable')
    return words[3]


def publish():
    os.umask(0o077)
    with STATE.with_suffix('.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        while display_live():
            try:
                reply = subprocess.check_output(
                    ['/system/bin/service', 'call', 'batteryproperties', '1', 'i32', '4'],
                    text=True, timeout=3,
                )
                staged = STATE.with_suffix('.next')
                staged.write_text(str(capacity(reply)), encoding='ascii')
                staged.replace(STATE)
            except (OSError, ValueError, subprocess.SubprocessError):
                STATE.unlink(missing_ok=True)
            time.sleep(PERIOD)


def show():
    try:
        with STATE.open(encoding='ascii') as snapshot:
            age = time.time() - os.fstat(snapshot.fileno()).st_mtime
            level = int(snapshot.read())
        if not 0 <= age <= 3 * PERIOD or not 0 <= level <= 100:
            raise ValueError('Stale or invalid capacity')
    except (OSError, ValueError):
        print('<icon>battery-missing-symbolic</icon><txt>--%</txt><tool>Android battery unavailable</tool>')
        return
    fill = ((level + 10) // 20) * 20
    print(f'<icon>battery-{fill:03d}-symbolic</icon><txt>{level}%</txt><tool>Android battery {level}%</tool>')


if __name__ == '__main__':
    if sys.argv[1:] == ['ensure']:
        if display_live():
            subprocess.Popen([sys.executable, str(SCRIPT), 'publish'], start_new_session=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.argv[1:] == ['publish']:
        publish()
    elif not sys.argv[1:]:
        show()
    else:
        raise SystemExit('usage: tablet-battery.py [ensure|publish]')
