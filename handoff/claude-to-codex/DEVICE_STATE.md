# Device State

> **Sau triển khai 2026-11-19:** APT cũ đã tự hoàn tất, audit sạch; giao diện/app thiết yếu đã triển khai và kiểm tra. NetSurf HTTPS đạt, Firefox còn lỗi font. Người dùng xác nhận menu cảm ứng, kéo cửa sổ và Home Resume. Xem [trạng thái mới nhất](DESKTOP_COMPLETION_2026-11-19.md); dữ liệu bên dưới là snapshot trước triển khai.

**Observed:** 2026-11-19 over ADB. Values below are observations, not instructions to mutate device.

## Device / OS / resources

| Field | Current observation |
|---|---|
| ADB | Device `f422eebd`, state `device`, product `muyu_global`, model string `24091RPADG`. |
| Consumer model | Xiaomi Pad 7 Pro, as identified by project owner. |
| Android | Release 16, API 36. |
| HyperOS | `OS3.0.303.0.WOYMIXM` (ro.mi.os.version.incremental). |
| ABI | `arm64-v8a`. |
| Display | `wm size`: `Physical size: 2136x3200`; `wm density`: `Physical density: 440`. Read-only; no override was set by the final check. Never change global resolution/density. |
| RAM | `free -h`: 7.3G total; 7.1G used, ~225M free; 8.0G swap, 4.2G used, ~3.7G free. Snapshot fluctuates; not a performance benchmark. |
| `/data` | `df -h /data`: 225G total, 127G used, 98G available (57%). |
| ADB access | Connected and authorized during this audit. |

## Android packages

Observed via `pm list packages` / `dumpsys package` on 2026-11-19:

| Package | Present | Reported version metadata |
|---|---:|---|
| `com.termux` | Yes | `versionCode=1002`, minSdk 24, targetSdk 28. Version name not printed by the chosen grep. Prior report gives Termux 0.118.3, not freshly verified here. |
| `com.termux.x11` | Yes | `versionCode=15`, minSdk 26, targetSdk 34. Prior report gives `1.03.01-caa7553-13.07.26`; not freshly read as versionName here. |
| `com.termux.widget` | Yes | `versionCode=1001`, minSdk 24, targetSdk 28. Earlier install evidence identifies upstream Widget v0.15.0. |
| `dev.local.linuxdesktop.launcher` | No | `dumpsys package` returned no package metadata; package absent from `pm list packages`. |

Other Android browsers present include `com.sec.android.app.sbrowser`, `com.brave.browser`, and `com.github.android` (GitHub app); this does not establish Linux browser functionality.

Earlier evidence (historical): Termux:Widget official GitHub release v0.15.0 asset SHA-256 `780ae459be479bedef2146eb00f7bc79f2a4f89dba2bffa7b55c470165bc66ed`; installed Termux/Termux:X11 signer SHA-256 `b6da01480eefd5fbf2cd3771b8d1021ec791304bdd6c4bf41d3faabad48ee5e1`; Widget signer matched. This showed signing compatibility, not original download provenance of the already installed apps.

## Termux packages / PRoot

Read-only package check via `run-as com.termux` on 2026-11-19:

- `proot`: `5.1.107.86`
- `proot-distro`: `5.4.1`
- `termux-tools`: `1.45.0`
- `termux-x11-nightly`: `1.03.01-5`
- `x11-repo`: `8.4-1`
- `proot-distro list`: installed containers `debian`, `ubuntu`.

Do not remove, reset, restore or reinstall either container. Ubuntu must remain untouched.

## Debian and display

- Debian GNU/Linux 13 (`trixie`), `arm64` architecture.
- XFCE core packages present: `xfce4 4.20.1`, `xfce4-panel 4.20.4-1`, `xfce4-settings 4.20.1-1`, `xfce4-terminal 1.1.4-1`, `xfdesktop4 4.20.1-1`, `xfwm4 4.20.0-1`, `dbus-x11 1.16.2-2`.
- PRoot user is presented as `uid=0(root)` in Debian. This maps to Termux's app UID on Android; PRoot root is not Android root.
- Known active profile path in process environment: `XDG_CONFIG_HOME=/root/.ld-test/xfce-config`; `DISPLAY=:2`; `LIBGL_ALWAYS_SOFTWARE=1` on primary component processes. WM launched `xfwm4 --compositor=off`.
- Read-only `xrandr --current` using `DISPLAY=:2` reported `Screen 0: current 1280 x 960`, output `builtin connected 1280x960`, 119.89 Hz. This is Termux:X11 virtual geometry, not Android global screen size.
- WM root property was verified earlier in this session: `_NET_SUPPORTING_WM_CHECK` window `0xe00032`. It is not proof of current on-screen usability.

### Active process snapshot (2026-11-19; volatile)

Read only with Termux UID access to `/proc`; do not use PIDs for any signal/cleanup operation. PID reuse and multiple experimental sessions make PID-based assumptions unsafe.

| PID | Process / observation |
|---:|---|
| 15917 | `termux-x11 com.termux.x11 :2`, UID 10528, PPID 1. |
| 841 | `termux-x11 com.termux.x11 :3`, UID 10528, PPID 1. |
| 5101 | `dbus-run-session` with historical one-off shell command for `/root/.ld-test`; PRoot tracer 5096. |
| 5115 | `xfsettingsd --no-daemon`, PPID 5104, tracer 5096; env `DISPLAY=:2`, `LIBGL_ALWAYS_SOFTWARE=1`, `XDG_CONFIG_HOME=/root/.ld-test/xfce-config`. |
| 5146 | `xfwm4 --compositor=off`, same supervisor/env as above. |
| 5324 | `xfdesktop`, same supervisor/env as above. |
| 5326 | `xfce4-panel`, same supervisor/env as above. |
| 21676 / 21682 / 21688 | Separate PRoot with `dbus-run-session -- sh -s`, child shell `sh -s`, and older `xfwm4` process. It had no `LIBGL_ALWAYS_SOFTWARE` or config-path env in inspected output; it is still present and not attributed to active visual desktop. Preserve it. |
| 2081 | At latest detailed process check: PRoot invoking `apt-get -y --no-install-recommends install arc-theme papirus-icon-theme fonts-noto fonts-noto-cjk`. |
| 2714 | PRoot shell `sh -s`, ownership/command not established. Preserve; do not assume orphan. |
| 5096 | Primary Debian PRoot process. |
| 16028 | PRoot process command includes `dbus-launch --exit-with-session xfce4-session`, from older experiment. |

Further process matching output included `proot --shm-helper` PID 5173. Exact APT child PIDs were not isolated. At last check, do not start another apt/dpkg process or signal any of these PIDs. Recheck safely before proceeding; process state may change.

## APT / package DB status after interrupted action

A core-app APT transaction in this handoff completed successfully; see next section. An appearance transaction was then attempted but canceled/interrupted by the user. Immediately after interruption, read-only `dpkg --audit` reported:

- Database locked by another writer.
- `papirus-icon-theme` status in a serious/broken state, missing list/md5sums control files.
- `arc-theme`, `fonts-noto`, `fonts-noto-cjk`, `fonts-noto-core`, `fonts-noto-mono`, `gnome-themes-extra`, `gnome-themes-extra-data`, `gtk2-engines-murrine`, `gtk2-engines-pixbuf`, `libgtk2.0-0t64`, and `libgtk2.0-common` unpacked but not configured.
- Pending triggers for `fontconfig` and `libc-bin`.
- Filesystem then had 99G free.

The user interrupted before any recovery command. Do not assert status still matches. First non-destructive inspect current APT process and lock, wait for legitimate completion if still active, and obtain authorization before repair. Never kill/force-stop package-related processes as cleanup.

## Debian package audit

The core app batch completed during this handoff using Debian stable, no recommends:

`xfce4-whiskermenu-plugin`, `thunar-archive-plugin`, `mousepad`, `ristretto`, `atril`, `engrampa`, `xfce4-taskmanager`, `xfce4-screenshooter`, `xfce4-clipman-plugin`, `xdg-utils`, `desktop-file-utils` (already installed).

A post-install `dpkg-query` confirmed those listed packages and `dpkg --audit` was empty at that moment, before the interrupted appearance transaction. This transaction installed 125 packages, fetched 87.8 MB, added ~412 MB according to APT output. It included heavy WebKit/GStreamer dependencies for Atril/Engrampa and `bubblewrap`/`xdg-dbus-proxy`; evaluate future app batches with reviewed simulations and `--no-install-recommends`, avoid duplicate installs. It showed one package not upgraded and removed none. The package setup emitted `procps: Applying updated sysctl configuration` and `grep: /proc/1/environ: No such file or directory`; no global Android setting was intentionally changed, but note this output.

Other present at last package query: existing `thunar`, `xfce4-settings`, `desktop-file-utils`, `git`, `python3`, `curl`, `wget`, `ca-certificates`, and XFCE terminal. Missing/not installed at that time: `firefox-esr`, `openssh-client`, `python3-venv`, `unzip`, `zip`, `rsync`. Appearance packages had an interrupted/unclean state as above. Existing `fonts-noto` family packages may be partially unpacked; they are not verified usable.

All graphical applications listed above are package-presence only. None of the new GUI app launches, content handlers, PDF/ZIP open tests, browser HTTPS, download, or resource behavior was tested.

## Existing Termux shortcut files

Verified via `run-as com.termux ls -lR`:

- Script: `/data/data/com.termux/files/home/.shortcuts/linux-resume.sh`, mode `700`, 5280 bytes at 12:57 local device time.
- Icon: `/data/data/com.termux/files/home/.shortcuts/icons/linux-resume.sh.png`, mode `600`, 2706 bytes at 12:27.
- The script is resume-only for existing XFCE on `:2`; see `WORKING_COMMANDS.md`.
- User reported home-screen pin completed after earlier UI-picker attempts. Do not assume current icon placement/click result without user's observation.

## Prior user-safety deviations recorded in earlier work

- An earlier troubleshooting action ran `am force-stop com.termux.widget`, violating the broad earlier instruction not to terminate any process; that stopped Widget, not XFCE. Do not repeat.
- Android display was temporarily set to `1600x1068` using `wm size`, then reset; latest read-only output says physical `2136x3200`, no override. Do not describe history as “never changed”. Do not change it again.
- Earlier ADB Widget APK installation was verified as successful after delayed completion, but some earlier install attempts failed `INSTALL_FAILED_VERIFICATION_FAILURE`.
