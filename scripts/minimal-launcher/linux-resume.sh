#!/data/data/com.termux/files/usr/bin/sh
set -eu

PREFIX=/data/data/com.termux/files/usr
PATH=$PREFIX/bin:/system/bin
export PATH
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

[ -x "$PREFIX/bin/proot-distro" ] || fail 'proot-distro unavailable'
[ -x "$PREFIX/bin/termux-x11" ] || fail 'Termux:X11 command unavailable'

servers=$($PREFIX/bin/pgrep -af 'termux-x11 com' 2>/dev/null | $PREFIX/bin/grep -E '^[0-9]+ termux-x11 com\.termux\.x11 :2[[:space:]]*$' || :)
server_count=$(printf '%s\n' "$servers" | $PREFIX/bin/grep -c . || :)
[ "$server_count" -eq 1 ] || fail "expected one untagged Termux:X11 server on :2; found $server_count"
server_pid=${servers%% *}
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
set -- $settings; settings_pid=$1; settings_parent=$2; settings_tracer=$3
wm=$(one_component xfwm4)
set -- $wm; wm_pid=$1; wm_parent=$2; wm_tracer=$3
[ -r "/proc/$wm_pid/cmdline" ] || fail 'XFCE window manager identity unavailable'
wm_cmd=$(tr '\000' ' ' < "/proc/$wm_pid/cmdline")
case "$wm_cmd" in *'--compositor=off'*) ;; *) fail 'XFCE window manager does not match verified configuration' ;; esac
desktop=$(one_component xfdesktop)
set -- $desktop; desktop_pid=$1; desktop_parent=$2; desktop_tracer=$3
panel=$(one_component xfce4-panel)
set -- $panel; panel_pid=$1; panel_parent=$2; panel_tracer=$3

# Native panel replacement can reparent it; its UID, environment and PRoot tracer
# still must match the same verified Debian session below.
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

wm_check=$(PATH="$PATH" $PREFIX/bin/proot-distro login --isolated --shared-tmp debian -- env DISPLAY="$DISPLAY" xprop -root _NET_SUPPORTING_WM_CHECK 2>/dev/null) ||
    fail 'cannot query the existing X11 window manager'
case "$wm_check" in *'window id #'*) ;; *) fail 'no window manager is active on :2' ;; esac
wm_window=${wm_check##*\# }
wm_properties=$(PATH="$PATH" $PREFIX/bin/proot-distro login --isolated --shared-tmp debian -- env DISPLAY="$DISPLAY" xprop -id "$wm_window" _NET_WM_PID _NET_WM_NAME 2>/dev/null) ||
    fail 'cannot verify X11 window manager identity'
printf '%s\n' "$wm_properties" | grep -Fq "_NET_WM_PID(CARDINAL) = $wm_pid" || fail 'X11 window manager PID does not match running XFCE process'
printf '%s\n' "$wm_properties" | grep -Fq '_NET_WM_NAME(UTF8_STRING) = "Xfwm4"' || fail 'X11 window manager name does not match XFCE'

# Ensure only the Firefox URL helper; never start another desktop.
$PREFIX/bin/python /data/data/com.termux/files/home/.local/share/linux-desktop/firefox-sandbox/firefox-tablet.py --ensure ||
    printf 'linux-resume: Firefox helper unavailable; desktop resume continues.\n' >&2

viewer=$($PREFIX/bin/am start --user 0 -n com.termux.x11/com.termux.x11.MainActivity 2>&1) || {
    printf '%s\n' "$viewer" >&2
    fail 'Android rejected the Termux:X11 viewer request'
}
case "$viewer" in *'Error:'*|*'Exception:'*) printf '%s\n' "$viewer" >&2; fail 'Termux:X11 viewer request failed' ;; esac
printf '%s\n' "$viewer"
printf 'RESUME_REQUESTED: existing XFCE on :2; no desktop process started.\n'
