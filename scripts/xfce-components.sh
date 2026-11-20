#!/bin/sh
# Run inside Debian with --shared-tmp. Do not change Android's display resolution.
# Mesa hardware GL hangs in PRoot; use llvmpipe and disable xfwm4 compositing.
# ponytail: skip xfce4-session while Mesa init hangs; restore if that root cause is fixed.
set -eu
DISPLAY=${1:?usage: xfce-components.sh :N}
case "$DISPLAY" in :[2-9]|:[1-9][0-9]) ;; *) echo "invalid display: $DISPLAY" >&2; exit 2;; esac
R=/root/.local/linux-desktop
mkdir -p "$R/config" "$R/cache" "$R/run" "$R/logs"
chmod 700 "$R/run"
export HOME=/root LANG=C.UTF-8 DISPLAY LIBGL_ALWAYS_SOFTWARE=1
export XDG_CONFIG_HOME="$R/config" XDG_CACHE_HOME="$R/cache" XDG_RUNTIME_DIR="$R/run"
exec dbus-run-session -- sh -c '
set -eu
L=/root/.local/linux-desktop/logs
pids=""
cleanup() {
  for pid in $pids; do kill -TERM "$pid" 2>/dev/null || :; done
  for pid in $pids; do wait "$pid" 2>/dev/null || :; done
}
trap cleanup EXIT HUP INT TERM
if xprop -root _NET_SUPPORTING_WM_CHECK | grep -q "window id"; then
  echo "WM already on $DISPLAY; abort" >&2; exit 1
fi
xfsettingsd --no-daemon >"$L/xfsettingsd.log" 2>&1 & settings=$!; pids="$pids $settings"
sleep 2
xfwm4 --compositor=off >"$L/xfwm4.log" 2>&1 & wm=$!; pids="$pids $wm"
i=0
until xprop -root _NET_SUPPORTING_WM_CHECK | grep -q "window id"; do
  kill -0 "$wm" 2>/dev/null || { echo "xfwm4 exited" >&2; exit 1; }
  i=$((i+1)); [ "$i" -lt 35 ] || { echo "xfwm4 not ready after 35s" >&2; exit 1; }
  sleep 1
done
xfdesktop >"$L/xfdesktop.log" 2>&1 & desktop=$!; pids="$pids $desktop"
xfce4-panel >"$L/xfce4-panel.log" 2>&1 & panel=$!; pids="$pids $panel"
xfce4-terminal --title="Linux Desktop" >"$L/xfce4-terminal.log" 2>&1 & terminal=$!; pids="$pids $terminal"
wait "$wm"'
