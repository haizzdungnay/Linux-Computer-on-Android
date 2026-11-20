#!/data/data/com.termux/files/usr/bin/sh
set -eu

PREFIX=/data/data/com.termux/files/usr
PATH=$PREFIX/bin:/system/bin
export PATH

workstation=/data/data/com.termux/files/home/.local/share/linux-desktop/tablet-workstation.py
if [ -r "$workstation" ]; then
    result=0
    "$PREFIX/bin/python" "$workstation" open || result=$?
    # Exit 3 means the original, manually launched X11 server is still live.
    [ "$result" -eq 3 ] || exit "$result"
fi

DISPLAY=:2
XDG_CONFIG_HOME=/root/.ld-test/xfce-config
fail() {
    printf 'linux-resume: %s\n' "$1" >&2
    exit 2
}

one_component() {
    name=$1
    pids=$($PREFIX/bin/pgrep -x "$name" 2>/dev/null || :)
    count=0
    for pid in $pids; do
        [ -r "/proc/$pid/environ" ] || continue
        env=$(tr '\000' '\n' < "/proc/$pid/environ")
        printf '%s\n' "$env" | grep -Fqx "DISPLAY=$DISPLAY" || continue
        printf '%s\n' "$env" | grep -Fqx "XDG_CONFIG_HOME=$XDG_CONFIG_HOME" || continue
        printf '%s\n' "$env" | grep -Fqx 'LIBGL_ALWAYS_SOFTWARE=1' || continue
        parent=$(awk '/^PPid:/ { print $2 }' "/proc/$pid/status")
        tracer=$(awk '/^TracerPid:/ { print $2 }' "/proc/$pid/status")
        count=$((count + 1))
        result="$pid $parent $tracer"
    done
    [ "$count" -eq 1 ] || fail "$name on $DISPLAY is absent or ambiguous ($count matches)"
    printf '%s\n' "$result"
}

socket_identity() {
    # Widget cannot inspect run-as processes. Pin the listener via kernel credentials.
    "$PREFIX/bin/python" - "$PREFIX/tmp" <<'PY'
import os
from pathlib import Path
import socket
import stat
import struct
import sys

tmp = Path(sys.argv[1])
lock = tmp / ".X2-lock"
addr = tmp / ".X11-unix/X2"
uid = os.getuid()
try:
    lock_stat = lock.lstat()
    addr_stat = addr.lstat()
    if (lock_stat.st_uid != uid or not stat.S_ISREG(lock_stat.st_mode)
            or addr_stat.st_uid != uid or not stat.S_ISSOCK(addr_stat.st_mode)):
        raise ValueError("unexpected X2 file ownership or type")
    expected_pid = int(lock.read_text().strip())
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(2)
        client.connect(str(addr))
        pid, peer_uid, _ = struct.unpack("3i", client.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    if pid <= 0 or (pid, peer_uid) != (expected_pid, uid):
        raise ValueError("X2 listener does not match Termux UID and X2 lock PID")
    print(f"{pid}:{uid}:{addr_stat.st_dev}:{addr_stat.st_ino}:{addr_stat.st_ctime_ns}")
except (OSError, ValueError) as error:
    raise SystemExit(f"linux-resume: {error}") from None
PY
}

verify_processes() {
    server_pid=$1
    [ -r "/proc/$server_pid/cmdline" ] || fail 'Termux:X11 server identity unavailable'
    server_cmd=$(tr '\000' ' ' < "/proc/$server_pid/cmdline")
    set -- $server_cmd
    [ "$#" -eq 3 ] && [ "$1" = termux-x11 ] && [ "$2" = com.termux.x11 ] && [ "$3" = :2 ] || fail 'Termux:X11 server command does not match display :2'
    server_parent=$(awk '/^PPid:/ { print $2 }' "/proc/$server_pid/status")
    [ "$server_parent" = 1 ] || fail 'Termux:X11 server has unexpected parent; ownership unknown'
    test_uid=$(id -u)
    server_uid=$(awk '/^Uid:/ { print $2 }' "/proc/$server_pid/status")
    [ "$server_uid" = "$test_uid" ] || fail 'Termux:X11 server UID does not match Termux'

    for component in xfsettingsd xfwm4 xfdesktop xfce4-panel; do
        component_info=$(one_component "$component")
        set -- $component_info
        component_uid=$(awk '/^Uid:/ { print $2 }' "/proc/$1/status")
        [ "$component_uid" = "$test_uid" ] || fail "$component UID does not match Termux"
    done

    settings=$(one_component xfsettingsd)
    set -- $settings; settings_parent=$2; settings_tracer=$3
    wm=$(one_component xfwm4)
    set -- $wm; wm_pid=$1; wm_parent=$2; wm_tracer=$3
    [ -r "/proc/$wm_pid/cmdline" ] || fail 'XFCE window manager identity unavailable'
    wm_cmd=$(tr '\000' ' ' < "/proc/$wm_pid/cmdline")
    case "$wm_cmd" in *'--compositor=off'*) ;; *) fail 'XFCE window manager does not match verified configuration' ;; esac
    desktop=$(one_component xfdesktop)
    set -- $desktop; desktop_parent=$2; desktop_tracer=$3
    panel=$(one_component xfce4-panel)
    set -- $panel; panel_tracer=$3

    # The panel may be reparented by its native restart. Match its PRoot tracer.
    [ "$settings_parent" = "$wm_parent" ] && [ "$wm_parent" = "$desktop_parent" ] ||
        fail 'XFCE settings, window manager and desktop do not share one verified supervisor'
    [ "$settings_tracer" -gt 0 ] && [ "$settings_tracer" = "$wm_tracer" ] &&
        [ "$wm_tracer" = "$desktop_tracer" ] && [ "$desktop_tracer" = "$panel_tracer" ] ||
        fail 'XFCE components do not share one verified Debian PRoot'

    supervisor_parent=$(awk '/^PPid:/ { print $2 }' "/proc/$settings_parent/status")
    supervisor_cmd=$(tr '\000' ' ' < "/proc/$supervisor_parent/cmdline")
    case "$supervisor_cmd" in *dbus-run-session*) ;; *) fail 'XFCE supervisor is not under the verified D-Bus session' ;; esac
    proot_cmd=$(tr '\000' ' ' < "/proc/$settings_tracer/cmdline")
    case "$proot_cmd" in *"$PREFIX/var/lib/proot-distro/containers/debian/rootfs"*) ;; *) fail 'XFCE process owner is not the Debian PRoot' ;; esac
    printf '%s\n' "$wm_pid"
}

[ -x "$PREFIX/bin/proot-distro" ] || fail 'proot-distro unavailable'
[ -x "$PREFIX/bin/termux-x11" ] || fail 'Termux:X11 command unavailable'

pin=/data/data/com.termux/files/home/.local/share/linux-desktop/resume-x2.identity
socket=$(socket_identity) || fail 'cannot verify the X2 listener'
servers=$($PREFIX/bin/pgrep -af 'termux-x11 com' 2>/dev/null | $PREFIX/bin/grep -E '^[0-9]+ termux-x11 com\.termux\.x11 :2[[:space:]]*$' || :)
server_count=$(printf '%s\n' "$servers" | $PREFIX/bin/grep -c . || :)
case "$server_count" in
    1)
        server_pid=${servers%% *}
        [ "${socket%%:*}" = "$server_pid" ] || fail 'X2 listener PID does not match the visible server'
        wm_pid=$(verify_processes "$server_pid")
        ;;
    0)
        case "$(id -Z 2>/dev/null)" in
            u:r:untrusted_app:s0*|u:r:untrusted_app_*:s0*) ;;
            *) fail 'Termux:X11 server on :2 is not visible' ;;
        esac
        wm_pid=
        ;;
    *) fail "expected one untagged Termux:X11 server on :2; found $server_count" ;;
esac

wm_check=$(timeout 8 "$PREFIX/bin/proot-distro" login --isolated --shared-tmp debian -- env DISPLAY="$DISPLAY" xprop -root _NET_SUPPORTING_WM_CHECK 2>/dev/null) ||
    fail 'cannot query the existing X11 window manager'
case "$wm_check" in *'window id #'*) ;; *) fail 'no window manager is active on :2' ;; esac
wm_window=${wm_check##*\# }
wm_properties=$(timeout 8 "$PREFIX/bin/proot-distro" login --isolated --shared-tmp debian -- env DISPLAY="$DISPLAY" xprop -id "$wm_window" _NET_SUPPORTING_WM_CHECK _NET_WM_PID _NET_WM_NAME 2>/dev/null) ||
    fail 'cannot verify X11 window manager identity'
printf '%s\n' "$wm_properties" | grep -Fxq "$wm_check" || fail 'X11 window manager check window is inconsistent'
printf '%s\n' "$wm_properties" | grep -Fxq '_NET_WM_NAME(UTF8_STRING) = "Xfwm4"' || fail 'X11 window manager name does not match XFCE'
x_pid=$(printf '%s\n' "$wm_properties" | sed -n 's/^_NET_WM_PID(CARDINAL) = \([1-9][0-9]*\)$/\1/p')
[ -n "$x_pid" ] && { [ -z "$wm_pid" ] || [ "$x_pid" = "$wm_pid" ]; } ||
    fail 'X11 window manager PID is missing or does not match XFCE'

identity="$socket $wm_window $x_pid"
if [ -n "$wm_pid" ]; then
    # Refresh the pin only after the original full profile and process checks pass.
    umask 077
    stage=$(mktemp "$pin.XXXXXX")
    printf '%s\n' "$identity" > "$stage"
    mv -f "$stage" "$pin"
else
    [ -r "$pin" ] && [ "$(cat "$pin")" = "$identity" ] ||
        fail 'X2 does not match the last verified Debian session'
fi
"$PREFIX/bin/python" /data/data/com.termux/files/home/.local/share/linux-desktop/firefox-sandbox/firefox-tablet.py --ensure ||
    printf 'linux-resume: Firefox helper unavailable; desktop resume continues.\n' >&2

viewer=$($PREFIX/bin/am start --user 0 -n com.termux.x11/com.termux.x11.MainActivity 2>&1) || {
    printf '%s\n' "$viewer" >&2
    fail 'Android rejected the Termux:X11 viewer request'
}
case "$viewer" in *'Error:'*|*'Exception:'*) printf '%s\n' "$viewer" >&2; fail 'Termux:X11 viewer request failed' ;; esac
printf '%s\n' "$viewer"
battery=$PREFIX/var/lib/proot-distro/containers/debian/rootfs/root/.local/share/linux-desktop/tablet-battery.py
if [ -r "$battery" ]; then
    "$PREFIX/bin/python" "$battery" ensure || printf 'linux-resume: battery monitor unavailable.\n' >&2
fi
printf 'RESUME_REQUESTED: existing XFCE on :2; no desktop process started.\n'
