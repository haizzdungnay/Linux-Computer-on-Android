#!/data/data/com.termux/files/usr/bin/sh
set -eu

PREFIX=/data/data/com.termux/files/usr
PATH=$PREFIX/bin:/system/bin
export PATH

exec "$PREFIX/bin/python3" /data/data/com.termux/files/home/.local/share/fedora45-desktop/fedora-workstation.py open
