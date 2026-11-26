#!/bin/sh
set -eu

export DISPLAY="$1"
RFB_PORT="$2"
export XDG_CONFIG_HOME="$3"
export PULSE_SERVER="$4"
export PULSE_COOKIE=/tmp/pulse-cookie
export HOME=/root
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
export GSK_RENDERER=cairo
export GLYCIN_DISABLE_SANDBOX=1
export NO_AT_BRIDGE=1
export LANG=C.UTF-8
export XDG_CACHE_HOME=/root/.cache/fedora45-xfce
export XDG_RUNTIME_DIR=/tmp/xdg-run
export XDG_CURRENT_DESKTOP=XFCE
export XDG_SESSION_TYPE=x11

BASE=/root/.local/share/fedora45-desktop
export PATH="$BASE/bin:$PATH"
PASS_FILE="$BASE/vnc.passwd"
mkdir -p -m 700 "$XDG_CONFIG_HOME" "$XDG_CONFIG_HOME/autostart" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR" /run/dbus /root/Desktop
cat > "$XDG_CONFIG_HOME/autostart/xfce-polkit.desktop" <<'EOF'
[Desktop Entry]
Hidden=true
EOF

DISPLAY_NUM="${DISPLAY#:}"
rm -f "/tmp/.X${DISPLAY_NUM}-lock" "/tmp/.X11-unix/X${DISPLAY_NUM}" /run/dbus/system_bus_socket /run/dbus/pid

XVNC_PID=""
DBUS_PID=""
POLKIT_PID=""
DNF5D_PID=""

cleanup() {
    for pid in "$DNF5D_PID" "$POLKIT_PID" "$DBUS_PID" "$XVNC_PID"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null || true
    rm -f /run/dbus/system_bus_socket /run/dbus/pid /tmp/xfce-ready
}
trap cleanup EXIT INT TERM HUP

Xvnc "$DISPLAY" \
    -rfbport "$RFB_PORT" \
    -localhost yes \
    -geometry 1600x1068 \
    -depth 24 \
    -dpi 120 \
    -SecurityTypes VncAuth \
    -PasswordFile "$PASS_FILE" \
    -AlwaysShared \
    -AcceptSetDesktopSize=1 \
    >/tmp/xvnc.log 2>&1 &
XVNC_PID=$!

for _ in $(seq 1 50); do
    if [ -S "/tmp/.X11-unix/X${DISPLAY_NUM}" ]; then
        break
    fi
    if ! kill -0 "$XVNC_PID" 2>/dev/null; then
        echo "Xvnc exited prematurely" >&2
        cat /tmp/xvnc.log >&2 || true
        exit 1
    fi
    sleep 0.2
done
[ -S "/tmp/.X11-unix/X${DISPLAY_NUM}" ] || { echo "Timed out waiting for Xvnc" >&2; exit 1; }

dbus-daemon --config-file="$BASE/system-dbus.conf" --nofork >/tmp/sysdbus.log 2>&1 &
DBUS_PID=$!
for _ in $(seq 1 30); do
    [ -S /run/dbus/system_bus_socket ] && break
    sleep 0.1
done

/usr/lib/polkit-1/polkitd --no-debug >/tmp/polkit.log 2>&1 &
POLKIT_PID=$!

/usr/sbin/dnf5daemon-server >/tmp/dnf5daemon.log 2>&1 &
DNF5D_PID=$!

dbus-run-session -- sh -ec '
    xfconf-query -c xfwm4 -p /general/use_compositing -n -t bool -s false
    xfconf-query -c xfce4-session -p /general/SaveOnExit -n -t bool -s false
    xfconf-query -c xfce4-session -p /startup/gpg-agent/enabled -n -t bool -s false
    xfconf-query -c xfce4-session -p /startup/ssh-agent/enabled -n -t bool -s false
    xfconf-query -c xfce4-session -p /sessions/Failsafe/Client0_Command -n -a \
        -t string -s xfwm4 -t string --set=--compositor=off
    xfconf-query -c xsettings -p /Xft/DPI -n -t int -s 120
    xfconf-query -c xsettings -p /Gtk/FontName -n -t string -s "Noto Sans 11"
    xfconf-query -c xsettings -p /Gtk/MonospaceFontName -n -t string -s "Noto Sans Mono 11"
    xfconf-query -c xsettings -p /Net/IconThemeName -r 2>/dev/null || true
    xfconf-query -c xsettings -p /Net/IconThemeName -n -t string -s Adwaita

    (
        for _ in $(seq 1 80); do
            windows=$(xwininfo -root -tree 2>/dev/null) || exit
            if printf "%s\n" "$windows" | grep -Fq "Xfdesktop Manager Selection" &&
                printf "%s\n" "$windows" | grep -Fq "\"Xfce4-panel\""; then
                touch /tmp/xfce-ready
                exit 0
            fi
            sleep 0.25
        done
    ) &

    exec xfce4-session --disable-tcp
'
