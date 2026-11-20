#!/bin/sh
set -eu

export DISPLAY=$1 XDG_CONFIG_HOME=$2 PULSE_SERVER=$3 PULSE_COOKIE=/tmp/pulse-cookie
export HOME=/root LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LANG=C.UTF-8
export XDG_CACHE_HOME="${XDG_CONFIG_HOME%-config}-cache" XDG_RUNTIME_DIR=/tmp/xdg-run
export XDG_CURRENT_DESKTOP=XFCE XDG_SESSION_TYPE=x11
mkdir -p -m 700 "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR"

exec dbus-run-session -- sh -ec '
    xfconf-query -c xfwm4 -p /general/use_compositing -n -t bool -s false
    xfconf-query -c xfce4-session -p /general/SaveOnExit -n -t bool -s false
    xfconf-query -c xfce4-session -p /startup/gpg-agent/enabled -n -t bool -s false
    xfconf-query -c xfce4-session -p /sessions/Failsafe/Client0_Command -n -a \
        -t string -s xfwm4 -t string --set=--compositor=off

    (
        for _ in $(seq 1 40); do
            windows=$(xwininfo -root -tree 2>/dev/null) || exit
            if printf "%s\n" "$windows" | grep -Fq "Xfdesktop Manager Selection" &&
                printf "%s\n" "$windows" | grep -Fq "\"Xfce4-panel\""; then
                touch /tmp/xfce-ready
                exec /usr/bin/python3 /root/.local/share/linux-desktop/picom-xfce/xfce-effects.py run
            fi
            sleep .5
        done
    ) &
    exec xfce4-session --disable-tcp
'
