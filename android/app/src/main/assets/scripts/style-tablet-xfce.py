#!/usr/bin/env python3
"""Incremental Mojave styling for the verified live :2 session; --check is read-only."""
# ponytail: one tablet/profile; add session selection only with separate lifecycle work.
import argparse
import json
import os
from pathlib import Path
import re
import subprocess


PROFILE = Path('/root/.ld-test/xfce-config')
BACKUP = Path('/root/.local/share/linux-desktop/backups/20261119-mojave')
WALLPAPER = '/root/.local/share/backgrounds/planet-space-129992.jpg'
FAVORITES = ['firefox-esr.desktop', 'xfce4-terminal.desktop', 'thunar.desktop',
             'org.xfce.mousepad.desktop', 'xfce-settings-manager.desktop',
             'xfce4-taskmanager.desktop', 'org.xfce.ristretto.desktop']


def run(*args):
    return subprocess.check_output(args, text=True, timeout=30).strip()


def session():
    found = {name: [] for name in ['xfsettingsd', 'xfwm4', 'xfdesktop', 'xfce4-panel']}
    for process in Path('/proc').glob('[0-9]*'):
        try:
            name = (process / 'comm').read_text().strip()
            if name not in found:
                continue
            env = dict(item.split('=', 1) for item in (process / 'environ').read_bytes()
                       .decode().split('\0') if '=' in item)
            if env.get('DISPLAY') not in [':2', ':2.0'] or env.get('XDG_CONFIG_HOME') != str(PROFILE):
                continue
            status = dict(line.split(':', 1) for line in (process / 'status').read_text().splitlines()
                          if ':' in line)
        except (OSError, UnicodeError):
            continue
        assert env.get('LIBGL_ALWAYS_SOFTWARE') == '1' and env.get('HOME') == '/root'
        assert int(status['Uid'].split()[0]) == 10528
        found[name].append((process, env, int(status['TracerPid'])))
    assert all(len(items) == 1 for items in found.values()), found
    tracers = {items[0][2] for items in found.values()}
    assert len(tracers) == 1 and next(iter(tracers)) > 0, tracers
    _, env, _ = found['xfsettingsd'][0]
    for key in ['HOME', 'DISPLAY', 'LIBGL_ALWAYS_SOFTWARE', 'XDG_CONFIG_HOME',
                'XDG_CACHE_HOME', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS']:
        os.environ[key] = env[key]
    os.environ['LANG'] = 'C.UTF-8'
    wm = run('xprop', '-root', '_NET_SUPPORTING_WM_CHECK').split('# ')[-1]
    assert run('xprop', '-id', wm, '_NET_WM_PID').split('= ')[-1] == found['xfwm4'][0][0].name
    assert '--compositor=off' in (found['xfwm4'][0][0] / 'cmdline').read_text()
    os.setgid(10528)
    os.setuid(10528)
    reply = run('dbus-send', '--session', '--type=method_call', '--print-reply',
                '--dest=org.freedesktop.DBus', '/org/freedesktop/DBus',
                'org.freedesktop.DBus.GetConnectionUnixProcessID', 'string:org.xfce.Panel')
    assert 'uint32 ' + found['xfce4-panel'][0][0].name in reply, reply
    return {name: int(items[0][0].name) for name, items in found.items()}


SETTINGS = {
    'xsettings': {
        '/Net/ThemeName': ('string', 'Mojave-Dark-solid'),
        '/Net/IconThemeName': ('string', 'WhiteSur-dark'),
        '/Gtk/FontName': ('string', 'Noto Sans 11'),
        '/Gtk/MonospaceFontName': ('string', 'Noto Sans Mono 11'),
        '/Xft/DPI': ('int', '120'),
    },
    'xfwm4': {
        '/general/theme': ('string', 'Mojave-Dark-solid'),
        '/general/title_font': ('string', 'Noto Sans Bold 11'),
        '/general/use_compositing': ('bool', 'false'),
    },
    'xfce4-terminal': {
        '/font-name': ('string', 'Noto Sans Mono 11'),
        '/color-background': ('string', '#202124'),
        '/color-foreground': ('string', '#e9e9ef'),
        '/color-cursor': ('string', '#67c9ea'),
        '/color-use-theme': ('bool', 'false'),
        '/background-mode': ('string', 'TERMINAL_BACKGROUND_SOLID'),
        '/run-custom-command': ('bool', 'true'),
        '/custom-command': ('string', '/bin/bash'),
    },
    'xfce4-panel': {
        '/panels/panel-1/size': ('uint', '38'),
        '/panels/panel-1/icon-size': ('uint', '24'),
        '/panels/panel-1/background-style': ('uint', '0'),
        '/panels/panel-1/autohide-behavior': ('uint', '0'),
        '/panels/panel-2/size': ('uint', '64'),
        '/panels/panel-2/icon-size': ('uint', '48'),
        '/panels/panel-2/background-style': ('uint', '0'),
        '/panels/panel-2/autohide-behavior': ('uint', '1'),
        '/panels/panel-2/position': ('string', 'p=10;x=0;y=0'),
        '/panels/panel-2/length': ('uint', '1'),
        '/panels/panel-2/length-adjust': ('bool', 'true'),
        '/panels/panel-2/plugin-ids': ('int', ['14', '15', '24', '13', '23', '16', '25', '26', '27']),
        '/plugins/plugin-2/show-labels': ('bool', 'false'),
        '/plugins/plugin-2/show-handle': ('bool', 'false'),
        '/plugins/plugin-2/flat-buttons': ('bool', 'true'),
        '/plugins/plugin-2/show-tooltips': ('bool', 'true'),
        '/plugins/plugin-21/button-title': ('string', 'Menu'),
        '/plugins/plugin-21/button-icon': ('string', 'distributor-logo-debian'),
        '/plugins/plugin-21/show-button-title': ('bool', 'true'),
        '/plugins/plugin-21/show-button-icon': ('bool', 'true'),
        '/plugins/plugin-21/menu-width': ('int', '350'),
        '/plugins/plugin-21/menu-height': ('int', '520'),
        '/plugins/plugin-21/launcher-show-name': ('bool', 'true'),
        '/plugins/plugin-21/launcher-show-description': ('bool', 'false'),
        '/plugins/plugin-21/launcher-icon-size': ('int', '2'),
        '/plugins/plugin-21/category-show-name': ('bool', 'false'),
        '/plugins/plugin-21/category-icon-size': ('int', '1'),
        '/plugins/plugin-21/position-categories-alternate': ('bool', 'true'),
        '/plugins/plugin-21/position-search-alternate': ('bool', 'true'),
        '/plugins/plugin-21/position-profile-alternate': ('bool', 'true'),
        '/plugins/plugin-21/favorites': ('string', FAVORITES),
        '/plugins/plugin-21/show-command-settings': ('bool', 'true'),
        '/plugins/plugin-21/show-command-lockscreen': ('bool', 'false'),
        '/plugins/plugin-21/show-command-switchuser': ('bool', 'false'),
        '/plugins/plugin-21/show-command-logoutuser': ('bool', 'false'),
        '/plugins/plugin-21/show-command-restart': ('bool', 'false'),
        '/plugins/plugin-21/show-command-shutdown': ('bool', 'false'),
        '/plugins/plugin-21/show-command-suspend': ('bool', 'false'),
        '/plugins/plugin-21/show-command-hibernate': ('bool', 'false'),
        '/plugins/plugin-21/show-command-logout': ('bool', 'false'),
        '/plugins/plugin-8/digital-layout': ('uint', '3'),
        '/plugins/plugin-8/digital-time-format': ('string', '%H:%M'),
        '/plugins/plugin-8/digital-time-font': ('string', 'Noto Sans Bold 10'),
        '/plugins/plugin-16/items': ('string', ['taskmanager.desktop']),
    },
    'xfce4-desktop': {
        '/desktop-icons/style': ('int', '2'),
        '/desktop-icons/gravity': ('int', '2'),
        '/desktop-icons/icon-size': ('uint', '48'),
        '/desktop-icons/use-custom-font-size': ('bool', 'true'),
        '/desktop-icons/font-size': ('double', '11'),
        '/desktop-icons/file-icons/show-home': ('bool', 'true'),
        '/desktop-icons/file-icons/show-filesystem': ('bool', 'false'),
        '/desktop-icons/file-icons/show-trash': ('bool', 'false'),
        '/desktop-icons/file-icons/show-removable': ('bool', 'false'),
    },
}
for workspace in [0, 1]:
    prefix = f'/backdrop/screen0/monitorbuiltin/workspace{workspace}/'
    SETTINGS['xfce4-desktop'][prefix + 'last-image'] = ('string', WALLPAPER)
    SETTINGS['xfce4-desktop'][prefix + 'image-style'] = ('int', '5')

CSS = '''/* Tablet panels: opaque, no compositor required. */
.panel-1 { background-color: #1c1d22; border: none; color: #efeff5; }
.panel-2 { background-color: #222329; border: 1px solid #44444e; border-radius: 0; padding: 0 6px; -XfcePanelWindow-autohide-size: 12; -XfcePanelWindow-popup-delay: 100; -XfcePanelWindow-popdown-delay: 600; }
.panel-2 button { padding: 4px; margin: 0 2px; border-radius: 6px; }
#whiskermenu-window { background-color: #24252a; color: #efeff5; }
#whiskermenu-window treeview { background-color: #24252a; color: #efeff5; }
#whiskermenu-window treeview.view { padding: 3px; }
#whiskermenu-window entry { min-height: 34px; }
#whiskermenu-window button { min-height: 32px; }
'''


def check():
    for channel, properties in SETTINGS.items():
        for prop, (kind, expected) in properties.items():
            actual = run('xfconf-query', '-c', channel, '-p', prop)
            if isinstance(expected, list):
                actual = actual.splitlines()[2:]
            elif kind == 'double':
                actual, expected = float(actual), float(expected)
            assert actual == expected, (channel, prop, actual, expected)
    assert (PROFILE / 'gtk-3.0/gtk.css').read_text().endswith(CSS)
    assert Path('/root/Desktop/Work').resolve() == Path('/root/Work')
    for theme in ['/root/.themes/Mojave-Dark-solid/gtk-3.0/gtk.css',
                  '/root/.themes/Mojave-Dark-solid/xfwm4/themerc',
                  '/root/.local/share/icons/WhiteSur-dark/index.theme', WALLPAPER]:
        assert Path(theme).is_file(), theme
    geometry = re.search(r'current (\d+) x (\d+)', run('xrandr'))
    assert geometry and min(map(int, geometry.groups())) >= 600
    for plugin in SETTINGS['xfce4-panel']['/panels/panel-2/plugin-ids'][1]:
        items = run('xfconf-query', '-c', 'xfce4-panel', '-p', f'/plugins/plugin-{plugin}/items').splitlines()[2:]
        assert items and all((PROFILE / f'xfce4/panel/launcher-{plugin}' / item).is_file() for item in items)
    print('PASS: Mojave settings, assets, launchers, UID/session, software rendering, compositor off, '
          + 'x'.join(geometry.groups()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print('SESSION', session())
    if args.apply:
        assert (BACKUP / 'before.tar').is_file(), 'create reviewed backup first'
        assert not (BACKUP / 'applied.json').exists(), 'already applied; use --check'
        for asset in ['/root/.themes/Mojave-Dark-solid/gtk-3.0/gtk.css',
                      '/root/.themes/Mojave-Dark-solid/xfwm4/themerc',
                      '/root/.local/share/icons/WhiteSur-dark/index.theme', WALLPAPER]:
            assert Path(asset).is_file(), asset
        for app in FAVORITES:
            assert (Path('/usr/share/applications') / app).is_file(), app
        css = PROFILE / 'gtk-3.0/gtk.css'
        css.parent.mkdir(exist_ok=True)
        original = css.read_text() if css.exists() else ''
        (BACKUP / 'gtk-css-before.json').write_text(json.dumps({'existed': css.exists(), 'text': original}))
        css.write_text(original + '\n' + CSS)
        launcher = PROFILE / 'xfce4/panel/launcher-16/taskmanager.desktop'
        launcher.write_text('[Desktop Entry]\nType=Application\nName=Task Manager\n'
                            'Exec=xfce4-taskmanager\nIcon=utilities-system-monitor\n'
                            'Terminal=false\nStartupNotify=true\n')
        desktop = Path('/root/Desktop')
        desktop.mkdir(exist_ok=True)
        assert not (desktop / 'Work').exists()
        (desktop / 'Work').symlink_to('/root/Work', target_is_directory=True)
        # Existing channel exports and before.tar retain the previous configuration.
        (BACKUP / 'applied.json').write_text(json.dumps(SETTINGS, indent=2))
        for channel, properties in SETTINGS.items():
            for prop, (kind, value) in properties.items():
                command = ['xfconf-query', '-c', channel, '-p', prop, '--create']
                for item in value if isinstance(value, list) else [value]:
                    command += ['--type', kind, '--set', item]
                if isinstance(value, list):
                    command += ['--force-array']
                run(*command)
        run('xfdesktop', '--arrange')
    check()


if __name__ == '__main__':
    main()
