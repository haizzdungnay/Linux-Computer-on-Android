# Working Commands and Proven Configuration

## Safety status

The following describes historical/manual behavior and read-only probes. It is not blanket authorization to run commands. `scripts/xfce-components.sh`, Python manager lifecycle operations, and any cleanup must not be run on a live session. The user explicitly prohibited process termination, session/display changes, resolution changes, and cleanup without approval. An APT transaction was interrupted during this handoff; do not run APT/dpkg until safely authorized and database/lock status is known.

## Environment facts

Historical manual XFCE run (2026-11-18) and the active profile observed in process environment on 2026-11-19:

```sh
DISPLAY=:2
LIBGL_ALWAYS_SOFTWARE=1
XDG_CONFIG_HOME=/root/.ld-test/xfce-config
```

- X11 socket sharing: `proot-distro login --isolated --shared-tmp debian ...`; PRoot's shared `/tmp` is needed for the Termux:X11 socket.
- Separate D-Bus session via `dbus-run-session`.
- WM must use `xfwm4 --compositor=off`.
- Existing Termux:X11 server `:2` was process `termux-x11 com.termux.x11 :2` in a prior read-only observation. `:3` also exists. Never start a second server or assume an unoccupied display from process list alone.
- Debian GUI identity: `uid=0(root)` inside PRoot, mapped to Termux Android UID 10528; PRoot does not provide an Android security boundary.

## Historical component sequence (manually tested, not a production start command)

On 2026-11-18, an isolated D-Bus shell launched these programs in order:

```sh
xfsettingsd --no-daemon
sleep 2
xfwm4 --compositor=off
# Waited for xprop -root _NET_SUPPORTING_WM_CHECK to report a WM.
xfdesktop
xfce4-panel
sleep 3
xfce4-terminal --title="XFCE TEST TERMINAL :2"
```

All were under `DISPLAY=:2`, `LIBGL_ALWAYS_SOFTWARE=1`, a D-Bus session and `XDG_CONFIG_HOME=/root/.ld-test/xfce-config`; logs were historically under `/root/.ld-test/logs`. User confirmed the UI/menu/terminal/drag on that date. The exact shell is preserved in historical report and a later process command line; no exact paste-ready launch invocation is endorsed here because the running session must be preserved and other `:2` experimental processes exist.

The current `scripts/xfce-components.sh` is not that exact known-good environment: it sets `XDG_CONFIG_HOME=/root/.local/linux-desktop/config`, XDG cache/run/log there; sets its own D-Bus session; includes an EXIT/HUP/INT/TERM trap that sends TERM to tracked child PIDs; starts terminal; and waits on `xfwm4`. It is unverified end-to-end and must not be used to start a parallel session on the live `:2`.

## Resume script

Workspace source: `scripts/minimal-launcher/linux-resume.sh`  
Device copy: `/data/data/com.termux/files/home/.shortcuts/linux-resume.sh`  
Purpose: validate identity of existing XFCE on display `:2`, verify the WM X11 property and open Termux:X11 viewer activity. It does not start `termux-x11`, XFCE components, or a Debian session.

Important implementation details:

- Sets `PREFIX=/data/data/com.termux/files/usr`, `PATH=$PREFIX/bin:/system/bin`, `DISPLAY=:2`, `XDG_CONFIG_HOME=/root/.ld-test/xfce-config`.
- Checks one Termux:X11 server with expected command/UID/parent.
- Requires unique `xfsettingsd`, `xfwm4`, `xfdesktop`, `xfce4-panel` matching DISPLAY/config/software GL and shared process ancestry/PRoot tracer.
- Requires WM cmdline `--compositor=off`, PRoot rootfs path Debian, D-Bus supervisor, and X11 WM PID/name properties matching XFWM.
- On success runs:

```sh
/data/data/com.termux/files/usr/bin/am start --user 0 -n com.termux.x11/com.termux.x11.MainActivity
```

- Previous direct live test passed and printed:

```text
RESUME_REQUESTED: existing XFCE on :2; no desktop process started.
```

- This proves only a resume request against then-running session. It cannot cold-start after processes end or survive reboot by itself. If checks fail/ambiguous, the script exits fail-closed; do not weaken checks merely to make shortcut launch.
- `PATH` is required when invoking `proot-distro`; without Termux `PATH`, previous call failed `proot utility does not exist on your system`.

## Safe read-only commands (verify current conditions, no repair)

Invoke ADB via Windows Git Bash quoting carefully; avoid paths being rewritten with `C:/Program Files/Git/...`. Current known ADB executable:

```sh
ADB=/c/Users/PC/AppData/Local/Android/Sdk/platform-tools/adb.exe
"$ADB" devices -l
"$ADB" -s f422eebd shell wm size
"$ADB" -s f422eebd shell wm density
"$ADB" -s f422eebd shell free -h
"$ADB" -s f422eebd shell 'df -h /data'
```

Termux app inventory / installed containers:

```sh
"$ADB" -s f422eebd shell 'run-as com.termux env PATH=/data/data/com.termux/files/usr/bin:/system/bin /data/data/com.termux/files/usr/bin/dpkg-query -W proot proot-distro termux-tools termux-x11-nightly x11-repo'
"$ADB" -s f422eebd shell 'run-as com.termux env PATH=/data/data/com.termux/files/usr/bin:/system/bin /data/data/com.termux/files/usr/bin/proot-distro list'
```

Debian read-only inventory pattern:

```sh
"$ADB" -s f422eebd shell 'run-as com.termux env PATH=/data/data/com.termux/files/usr/bin:/system/bin /data/data/com.termux/files/usr/bin/proot-distro login --isolated --shared-tmp debian -- sh -c '\''cat /etc/os-release; dpkg --print-architecture; dpkg-query -W xfce4 xfce4-panel xfce4-settings xfce4-terminal xfdesktop4 xfwm4; df -h /'\'''
```

Caveat: avoid broad process matching followed by action. Use read-only, narrow inspection and do not rely on PID beyond one snapshot. Do not run `proot-distro ps` without assessing side effects; project history found it can prune stale registry entries.

## Appearance/config state before appearance work

Snapshot `snapshots/xfce-config-20261119T103201/xfce-config.snapshot.tar` records saved profile:

- `xfce4-panel.xml`: two panels, top panel size 26, lower panel size 48, original plugin IDs/config retained.
- `xfwm4.xml`: theme `Default`, title font `Sans Bold 9`.
- `xsettings.xml`: `Net/ThemeName`, `Net/IconThemeName`, Xft DPI/font settings are empty; GTK font unset. Decoration layout `icon,menu:minimize,maximize,close`.
- `xfce4-desktop.xml`: no wallpaper property set.

Do not overwrite active configuration. Snapshot payload was 16 regular files (39,959 bytes) per report, tar file includes metadata/dirs; live-copied while running. SHA-256 and storage limitations in `HANDOFF.md`/`ACCEPTANCE_MATRIX.md`.
