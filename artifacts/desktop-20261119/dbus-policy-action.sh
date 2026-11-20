
set -eu
B=/root/.local/share/linux-desktop/backups/20261119-before-ui
umask 077
[ ! -e "$B" ] || { echo 'Backup path exists; abort'; exit 1; }
mkdir -p "$B"
tar -C /root/.ld-test -cf "$B/xfce-config.tar" xfce-config
cp -a /etc/dbus-1/session.d "$B/dbus-session.d"
dpkg-query -W >"$B/packages.tsv"
sha256sum "$B/xfce-config.tar"
python3 - <<'PY'
from pathlib import Path
for pid,name in [(5102,b'dbus-daemon'),(5115,b'xfsettingsd')]:
 p=Path('/proc')/str(pid)
 assert (p/'comm').read_bytes().strip()==name
 status=dict(line.split(':',1) for line in (p/'status').read_text().splitlines() if ':' in line)
 assert int(status['TracerPid'])==5096
 assert b'XDG_CONFIG_HOME=/root/.ld-test/xfce-config' in (p/'environ').read_bytes().split(b'\0')
out=Path('/etc/dbus-1/session.d/90-linux-desktop-termux.conf')
assert not out.exists()
out.write_text('''<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN" "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <!-- PRoot peers retain Termux UID. Keep EXTERNAL authentication; allow only this UID. -->
  <policy context="default">
    <allow user="10528"/>
  </policy>
</busconfig>
''')
out.chmod(0o644)
print('WROTE',out)
PY
sleep 2
python3 - <<'PY'
import os,subprocess
os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path=/tmp/dbus-wDHR1WjWUc'
os.setgid(10528);os.setuid(10528)
print('CLIENT_UID',os.getuid(),flush=True)
r=subprocess.run(['dbus-send','--session','--type=method_call','--print-reply','--dest=org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus.ListNames'],capture_output=True,text=True,timeout=10)
print(r.returncode,r.stdout,r.stderr)
PY
