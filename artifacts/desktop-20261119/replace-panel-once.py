import json,os,subprocess,time
from pathlib import Path
env=dict(item.split('=',1) for item in Path('/proc/5115/environ').read_bytes().decode().split('\0') if '=' in item)
assert env['DISPLAY']==':2' and env['XDG_CONFIG_HOME']=='/root/.ld-test/xfce-config'
assert env['LIBGL_ALWAYS_SOFTWARE']=='1'
assert Path('/proc/5326/comm').read_text().strip()=='xfce4-panel'
assert 'TracerPid:\t5096' in Path('/proc/5326/status').read_text()
os.environ.update({key:env[key] for key in ['HOME','DISPLAY','LIBGL_ALWAYS_SOFTWARE','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS']})
os.setgid(10528);os.setuid(10528)
def run(*args):
 return subprocess.check_output(args,text=True,timeout=20)
assert '5326' in run('dbus-send','--session','--type=method_call','--print-reply','--dest=org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus.GetConnectionUnixProcessID','string:org.xfce.Panel')
run('xfce4-panel','--quit')
for _ in range(100):
 if not Path('/proc/5326').exists():break
 time.sleep(.1)
else:raise RuntimeError('old panel did not exit')
config=json.loads(Path('/root/.local/share/linux-desktop/backups/20261119-tablet-ui/intended-settings.json').read_text())['xfce4-panel']
for prop,(kind,value) in config.items():
 args=['xfconf-query','-c','xfce4-panel','-p',prop,'--create']
 for item in value if isinstance(value,list) else [value]: args+=['--type',kind,'--set',item]
 if isinstance(value,list):args+=['--force-array']
 run(*args)
os.execvp('xfce4-panel',['xfce4-panel'])
