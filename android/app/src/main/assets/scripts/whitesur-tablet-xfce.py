#!/usr/bin/env python3
"""Apply, check or roll back WhiteSur on the existing tablet desktop."""
import argparse
import json
from pathlib import Path
import runpy
import subprocess


# ponytail: one live profile and its captured baseline; add profile selection with lifecycle support.
BASE = Path('/root/.local/share/linux-desktop')
BACKUP = BASE / 'backups/20261120-whitesur/before.json'
THEME = 'WhiteSur-Dark'
WALLPAPER = '/root/.local/share/backgrounds/WhiteSur-Monterey.jpg'
BACKDROP = '/backdrop/screen0/monitorbuiltin/workspace'
SETTINGS = {
    'xsettings:/Net/ThemeName': THEME,
    'xsettings:/Net/IconThemeName': 'WhiteSur-dark',
    'xsettings:/Gtk/DecorationLayout': 'close,minimize,maximize:',
    'xfwm4:/general/theme': THEME,
    'xfwm4:/general/button_layout': 'CHM|',
    f'xfce4-desktop:{BACKDROP}0/last-image': WALLPAPER,
    f'xfce4-desktop:{BACKDROP}1/last-image': WALLPAPER,
}


def query(key, *args):
    channel, prop = key.split(':', 1)
    return subprocess.check_output(
        ['xfconf-query', '-c', channel, '-p', prop, *args], text=True, timeout=8
    ).rstrip('\n')


def verify(expected):
    for key, value in expected.items():
        actual = query(key)
        if actual != value:
            raise RuntimeError(f'{key}: expected {value!r}, found {actual!r}')
        print(f'{key} = {actual}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['apply', 'check', 'restore'])
    action = parser.parse_args().action
    print('SESSION', runpy.run_path(str(BASE / 'style-tablet-xfce.py'))['session'](), flush=True)
    if action != 'restore':
        theme = Path('/root/.themes') / THEME
        for path in (theme / 'gtk-3.0/gtk.css', theme / 'xfwm4/themerc',
                     BASE.parent / 'icons/WhiteSur-dark/index.theme', Path(WALLPAPER)):
            if not path.is_file():
                raise FileNotFoundError(path)

    expected = SETTINGS
    if action != 'check':
        snapshot = json.loads(BACKUP.read_text())
        previous = {key: snapshot[key] for key in SETTINGS}
        if not all(isinstance(value, str) and value for value in previous.values()):
            raise ValueError('Incomplete WhiteSur rollback snapshot')
        if action == 'restore':
            expected = previous

        original = {key: query(key) for key in expected}
        changed = []
        try:
            for key, value in expected.items():
                if original[key] != value:
                    query(key, '-s', value)
                    changed.append(key)
            verify(expected)
        except Exception:
            for key in reversed(changed):
                query(key, '-s', original[key])
            raise
    else:
        verify(expected)


if __name__ == '__main__':
    main()
