#!/data/data/com.termux/files/usr/bin/sh
# One-shot / idempotent installer for Linux Computer on Android (Termux + PRoot Debian 13 + XFCE).
# Usage on Termux:
#   sh scripts/install.sh [--dry-run] [--skip-pkgs] [--skip-themes]
set -eu

DRY_RUN=0
SKIP_PKGS=0
SKIP_THEMES=0

usage() {
    cat <<'EOF'
Usage: install.sh [OPTIONS]

Install and configure Debian 13 (PRoot) + XFCE + WhiteSur + Picom + Termux:X11
workstation scripts on Android Termux.

Options:
  --dry-run      Print actions without modifying the system
  --skip-pkgs    Skip pkg / apt package installation
  --skip-themes  Skip cloning/installing WhiteSur themes, icons & wallpaper
  -h, --help     Show this help message
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1 ;;
        --skip-pkgs) SKIP_PKGS=1 ;;
        --skip-themes) SKIP_THEMES=1 ;;
        -h|--help) usage; exit 0 ;;
        *)
            printf 'Unknown option: %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
TERMUX_HOME="${HOME:-/data/data/com.termux/files/home}"
TERMUX_APP_DIR="$TERMUX_HOME/.local/share/linux-desktop"
TERMUX_SHORTCUTS="$TERMUX_HOME/.shortcuts"
TERMUX_PROPS="$TERMUX_HOME/.termux/termux.properties"

DEBIAN_ROOTFS="$PREFIX/var/lib/proot-distro/containers/debian/rootfs"
DEBIAN_APP_DIR="/root/.local/share/linux-desktop"
DEBIAN_PICOM_DIR="$DEBIAN_APP_DIR/picom-xfce"
DEBIAN_APPS_DIR="/root/.local/share/applications"
DEBIAN_PROFILE="/root/.ld-test/xfce-config"

run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '[dry-run]'
        for arg in "$@"; do
            printf ' %s' "$arg"
        done
        printf '\n'
    else
        "$@"
    fi
}

log() {
    printf '==> %s\n' "$1"
}

if [ "$DRY_RUN" -eq 0 ] && [ ! -d "$PREFIX" ]; then
    printf 'Error: Termux PREFIX not found at %s (run inside Termux or use --dry-run).\n' "$PREFIX" >&2
    exit 1
fi

# 1. Termux packages
if [ "$SKIP_PKGS" -eq 0 ]; then
    log "Installing Termux packages (x11-repo, proot-distro, termux-x11-nightly, pulseaudio, python, git)"
    run pkg update -y
    run pkg install -y x11-repo
    run pkg install -y proot-distro termux-x11-nightly pulseaudio xorg-xrandr python git
fi

# 2. Termux properties for widget / external launcher
log "Configuring Termux external-apps property"
if [ "$DRY_RUN" -eq 1 ]; then
    printf '[dry-run] ensure allow-external-apps = true in %s\n' "$TERMUX_PROPS"
else
    mkdir -p "$(dirname "$TERMUX_PROPS")"
    if [ ! -f "$TERMUX_PROPS" ]; then
        printf 'allow-external-apps = true\n' > "$TERMUX_PROPS"
    elif ! grep -Eq '^[[:space:]]*allow-external-apps[[:space:]]*=[[:space:]]*true' "$TERMUX_PROPS"; then
        printf '\nallow-external-apps = true\n' >> "$TERMUX_PROPS"
    fi
fi

# 3. Install Debian PRoot container if missing
if [ ! -d "$DEBIAN_ROOTFS" ]; then
    log "Installing Debian PRoot container via proot-distro"
    run proot-distro install debian
else
    log "Debian PRoot container already exists at $DEBIAN_ROOTFS"
fi

# 4. Install Debian packages
if [ "$SKIP_PKGS" -eq 0 ]; then
    log "Installing Debian XFCE, Picom, Firefox, and theme build dependencies"
    run proot-distro login --isolated --shared-tmp debian -- sh -eu -c '
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get install -y \
            xfce4 xfce4-whiskermenu-plugin xfce4-clipman-plugin xfce4-genmon-plugin \
            dbus-x11 x11-utils x11-xserver-utils picom firefox-esr \
            mousepad thunar xfce4-terminal \
            fonts-noto-core fonts-noto-mono kf6-breeze-icon-theme \
            sassc git curl python3
    '
fi

# 5. Deploy Termux-side launcher & battery scripts
log "Deploying Termux-side scripts to $TERMUX_APP_DIR and $TERMUX_SHORTCUTS"
run mkdir -p "$TERMUX_APP_DIR" "$TERMUX_SHORTCUTS"
run cp -p "$REPO_ROOT/scripts/minimal-launcher/tablet-workstation.py" "$TERMUX_APP_DIR/tablet-workstation.py"
run cp -p "$REPO_ROOT/scripts/tablet-battery.py" "$TERMUX_APP_DIR/tablet-battery.py"
run cp -p "$REPO_ROOT/scripts/minimal-launcher/linux-resume.sh" "$TERMUX_SHORTCUTS/linux-resume.sh"
run chmod +x "$TERMUX_APP_DIR/tablet-workstation.py" "$TERMUX_APP_DIR/tablet-battery.py" "$TERMUX_SHORTCUTS/linux-resume.sh"

# 6. Deploy Debian-side scripts, desktop entries, and panel CSS
log "Deploying Debian-side workstation scripts and desktop entries"
run proot-distro login --isolated --shared-tmp debian -- mkdir -p \
    "$DEBIAN_APP_DIR" "$DEBIAN_PICOM_DIR" "$DEBIAN_APPS_DIR" "$DEBIAN_PROFILE/gtk-3.0"

copy_to_debian() {
    src=$1
    dst=$2
    mode=${3:-644}
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '[dry-run] install -m %s %s -> debian:%s\n' "$mode" "$src" "$dst"
    else
        proot-distro login --isolated --shared-tmp debian -- sh -eu -c "cat > '$dst' && chmod $mode '$dst'" < "$src"
    fi
}

copy_to_debian "$REPO_ROOT/scripts/minimal-launcher/tablet-session.sh" "$DEBIAN_APP_DIR/tablet-session.sh" 755
copy_to_debian "$REPO_ROOT/scripts/minimal-launcher/tablet-power.py" "$DEBIAN_APP_DIR/tablet-power.py" 755
copy_to_debian "$REPO_ROOT/scripts/configure-tablet-xfce.py" "$DEBIAN_APP_DIR/configure-tablet-xfce.py" 755
copy_to_debian "$REPO_ROOT/scripts/style-tablet-xfce.py" "$DEBIAN_APP_DIR/style-tablet-xfce.py" 755
copy_to_debian "$REPO_ROOT/scripts/whitesur-tablet-xfce.py" "$DEBIAN_APP_DIR/whitesur-tablet-xfce.py" 755
copy_to_debian "$REPO_ROOT/scripts/firefox-tablet.py" "$DEBIAN_APP_DIR/firefox-tablet.py" 755
copy_to_debian "$REPO_ROOT/scripts/whitesur-panel.css" "$DEBIAN_PROFILE/gtk-3.0/gtk.css" 644

copy_to_debian "$REPO_ROOT/scripts/xfce-effects.py" "$DEBIAN_PICOM_DIR/xfce-effects.py" 755
copy_to_debian "$REPO_ROOT/scripts/picom-xrender.conf" "$DEBIAN_PICOM_DIR/picom.conf" 644

copy_to_debian "$REPO_ROOT/scripts/linux-desktop-effects-on.desktop" "$DEBIAN_APPS_DIR/linux-desktop-effects-on.desktop" 644
copy_to_debian "$REPO_ROOT/scripts/linux-desktop-effects-off.desktop" "$DEBIAN_APPS_DIR/linux-desktop-effects-off.desktop" 644
copy_to_debian "$REPO_ROOT/scripts/minimal-launcher/linux-workstation-power.desktop" "$DEBIAN_APPS_DIR/linux-workstation-power.desktop" 644
copy_to_debian "$REPO_ROOT/scripts/minimal-launcher/com.microsoft.VSCode.desktop" "$DEBIAN_APPS_DIR/com.microsoft.VSCode.desktop" 644
copy_to_debian "$REPO_ROOT/scripts/minimal-launcher/synaptic.desktop" "$DEBIAN_APPS_DIR/synaptic.desktop" 644

# 7. Optional: install WhiteSur GTK/Xfwm4 theme, icons, and Monterey wallpaper
if [ "$SKIP_THEMES" -eq 0 ]; then
    log "Installing WhiteSur GTK theme, WhiteSur icons, and Monterey wallpaper"
    run proot-distro login --isolated --shared-tmp debian -- sh -eu -c '
        SRC=/root/.local/share/linux-desktop/sources
        mkdir -p "$SRC" /root/.themes /root/.local/share/icons /root/.local/share/backgrounds

        if [ ! -d "$SRC/WhiteSur-gtk-theme/.git" ]; then
            git clone --depth=1 https://github.com/vinceliuice/WhiteSur-gtk-theme.git "$SRC/WhiteSur-gtk-theme"
        fi
        if [ ! -d /root/.themes/WhiteSur-Dark ]; then
            "$SRC/WhiteSur-gtk-theme/install.sh" -d /root/.themes -c Dark -N glassy || true
        fi

        if [ ! -d "$SRC/WhiteSur-icon-theme/.git" ]; then
            git clone --depth=1 https://github.com/vinceliuice/WhiteSur-icon-theme.git "$SRC/WhiteSur-icon-theme"
        fi
        if [ ! -d /root/.local/share/icons/WhiteSur-dark ]; then
            "$SRC/WhiteSur-icon-theme/install.sh" -d /root/.local/share/icons || true
        fi

        if [ ! -f /root/.local/share/backgrounds/WhiteSur-Monterey.jpg ]; then
            curl -fsSL -o /root/.local/share/backgrounds/WhiteSur-Monterey.jpg \
                https://raw.githubusercontent.com/vinceliuice/WhiteSur-wallpapers/main/2k/Monterey.jpg || true
        fi
    '
fi

log "Installation complete!"
printf '\nNext steps on Android:\n'
printf '  1. Start or resume workstation: %s/linux-resume.sh\n' "$TERMUX_SHORTCUTS"
printf '  2. Or via Termux:Widget: add the "linux-resume.sh" shortcut to your Home screen.\n'
