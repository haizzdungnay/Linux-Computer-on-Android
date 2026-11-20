#!/usr/bin/env python3
"""Configure the existing :2 profile; --check verifies it without writing."""
# ponytail: one existing :2 profile; add session discovery only with cold-start work.
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile


PROFILE = "/root/.ld-test/xfce-config"
BACKUP = Path("/root/.local/share/linux-desktop/backups/20261119-tablet-ui")
CHECK = sys.argv[1:] == ["--check"]
assert not sys.argv[1:] or CHECK, "usage: configure-tablet-xfce.py [--check]"


def run(*args):
    return subprocess.check_output(args, text=True, timeout=30).strip()


matches = []
for process in Path("/proc").glob("[0-9]*"):
    try:
        if (process / "comm").read_text().strip() != "xfsettingsd":
            continue
        env = dict(item.split("=", 1) for item in (process / "environ").read_bytes()
                   .decode().split("\0") if "=" in item)
        if env.get("DISPLAY") == ":2" and env.get("XDG_CONFIG_HOME") == PROFILE:
            matches.append((process, env))
    except (OSError, UnicodeError):
        continue
assert len(matches) == 1, "existing settings process missing or ambiguous"
process, env = matches[0]
assert env.get("LIBGL_ALWAYS_SOFTWARE") == "1"
for key in ("HOME", "DISPLAY", "LIBGL_ALWAYS_SOFTWARE", "XDG_CONFIG_HOME",
            "XDG_CACHE_HOME", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
    os.environ[key] = env[key]
os.environ["LANG"] = "C.UTF-8"
wm = run("xprop", "-root", "_NET_SUPPORTING_WM_CHECK").split("# ")[-1]
wm_pid = run("xprop", "-id", wm, "_NET_WM_PID").split("= ")[-1]
assert "--compositor=off" in (Path("/proc") / wm_pid / "cmdline").read_text()
status = dict(line.split(":", 1) for line in (process / "status").read_text().splitlines()
              if ":" in line)
uid = int(status["Uid"].split()[0])
os.setgid(uid)
os.setuid(uid)

settings = {
    "xsettings": {
        "/Net/ThemeName": ("string", "Arc-Dark"),
        "/Net/IconThemeName": ("string", "Papirus-Dark"),
        "/Gtk/FontName": ("string", "Noto Sans 12"),
        "/Gtk/MonospaceFontName": ("string", "Noto Sans Mono 12"),
        "/Gtk/CursorThemeSize": ("int", "32"),
        "/Xft/DPI": ("int", "120"),
        "/Xft/Antialias": ("int", "1"),
        "/Xft/Hinting": ("int", "1"),
        "/Xft/HintStyle": ("string", "hintslight"),
        "/Net/DoubleClickTime": ("int", "500"),
        "/Net/DoubleClickDistance": ("int", "8"),
        "/Net/DndDragThreshold": ("int", "12"),
    },
    "xfwm4": {
        "/general/theme": ("string", "Arc-Dark"),
        "/general/title_font": ("string", "Noto Sans Bold 12"),
        "/general/use_compositing": ("bool", "false"),
        "/general/workspace_count": ("int", "2"),
    },
    "xfce4-terminal": {
        "/run-custom-command": ("bool", "true"),
        "/custom-command": ("string", "/bin/bash"),
        "/font-name": ("string", "Noto Sans Mono 12"),
    },
    "xfce4-panel": {
        "/panels/panel-1/size": ("uint", "44"),
        "/panels/panel-1/icon-size": ("uint", "28"),
        "/panels/panel-1/position": ("string", "p=6;x=0;y=0"),
        "/panels/panel-1/plugin-ids": ("int", ["21", "2", "3", "6", "8", "1"]),
        "/panels/panel-2/size": ("uint", "64"),
        "/panels/panel-2/icon-size": ("uint", "44"),
        "/panels/panel-2/autohide-behavior": ("uint", "0"),
        "/panels/panel-2/position": ("string", "p=10;x=0;y=0"),
        "/panels/panel-2/plugin-ids": ("int", ["15", "13", "14", "23", "24"]),
        "/plugins/plugin-21": ("string", "whiskermenu"),
        "/plugins/plugin-21/button-title": ("string", "Applications"),
        "/plugins/plugin-21/button-icon": ("string", "distributor-logo-debian"),
        "/plugins/plugin-21/show-button-title": ("bool", "true"),
        "/plugins/plugin-21/show-button-icon": ("bool", "true"),
        "/plugins/plugin-1": ("string", "xfce4-clipman-plugin"),
        "/plugins/plugin-23": ("string", "launcher"),
        "/plugins/plugin-23/items": ("string", ["settings.desktop"]),
        "/plugins/plugin-24": ("string", "launcher"),
        "/plugins/plugin-24/items": ("string", ["editor.desktop"]),
        "/plugins/plugin-8/digital-layout": ("uint", "3"),
        "/plugins/plugin-8/digital-date-format": ("string", "%a, %d %b"),
        "/plugins/plugin-8/digital-time-format": ("string", "%H:%M"),
        "/plugins/plugin-8/timezone": ("string", "Asia/Ho_Chi_Minh"),
    },
    "xfce4-desktop": {
        "/backdrop/screen0/monitorbuiltin/workspace0/last-image":
            ("string", "/usr/share/backgrounds/xfce/xfce-blue.jpg"),
        "/backdrop/screen0/monitorbuiltin/workspace0/image-style": ("int", "5"),
        "/backdrop/screen0/monitorbuiltin/workspace1/last-image":
            ("string", "/usr/share/backgrounds/xfce/xfce-blue.jpg"),
        "/backdrop/screen0/monitorbuiltin/workspace1/image-style": ("int", "5"),
    },
}

if not CHECK:
    assert not BACKUP.exists(), f"backup exists: {BACKUP}; use --check"
    BACKUP.mkdir(parents=True, mode=0o700)
    with tarfile.open(BACKUP / "xfce-config.tar", "w") as archive:
        archive.add(PROFILE, arcname="xfce-config")
    for channel in settings:
        (BACKUP / (channel + ".txt")).write_text(run("xfconf-query", "-c", channel, "-lv"))
    (BACKUP / "intended-settings.json").write_text(json.dumps(settings, indent=2))
    for plugin, name, command, icon in [
        (23, "Settings", "xfce4-settings-manager", "preferences-system"),
        (24, "Editor", "mousepad", "accessories-text-editor"),
    ]:
        folder = Path(PROFILE) / "xfce4/panel" / f"launcher-{plugin}"
        folder.mkdir(exist_ok=True)
        filename = "settings.desktop" if plugin == 23 else "editor.desktop"
        (folder / filename).write_text(
            f"[Desktop Entry]\nType=Application\nName={name}\nExec={command}\n"
            f"Icon={icon}\nTerminal=false\nStartupNotify=true\n")
    for channel, properties in settings.items():
        for prop, (kind, value) in properties.items():
            args = ["xfconf-query", "-c", channel, "-p", prop, "--create"]
            for item in value if isinstance(value, list) else [value]:
                args += ["--type", kind, "--set", item]
            if isinstance(value, list):
                args += ["--force-array"]
            run(*args)

for channel, properties in settings.items():
    for prop, (_, value) in properties.items():
        actual = run("xfconf-query", "-c", channel, "-p", prop)
        if isinstance(value, list):
            assert actual.splitlines()[2:] == value, (channel, prop, actual)
        else:
            assert actual == value, (channel, prop, actual)
print("PASS: live XFCE settings verified on :2; compositor off; backup:", BACKUP)
