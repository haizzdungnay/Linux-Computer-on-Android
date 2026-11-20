import fcntl
import errno
import importlib.util
import socket
from unittest import mock
import json
import sys
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.runtime = self.home / '.local/linux-desktop/runtime'
        self.env = dict(os.environ, HOME=str(self.home), PREFIX=str(self.home / 'prefix'))
        self.runtime.mkdir(parents=True)
        (self.runtime / 'lock').touch()

    def tearDown(self):
        self.temp.cleanup()

    def run_script(self, action):
        return subprocess.run(['bash', str(SCRIPTS / f'{action}-linux.sh')],
                              env=self.env, text=True, capture_output=True, timeout=12)

    def test_absent_state_with_free_display_is_stopped(self):
        for action in ('status', 'stop'):
            result = self.run_script(action)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, 'STOPPED\n')

    def test_absent_state_with_occupied_display_is_unknown(self):
        tmp = Path(self.env['PREFIX']) / 'tmp'
        tmp.mkdir(parents=True)
        lock = tmp / '.X2-lock'
        lock.write_text('foreign')
        for action in ('status', 'stop'):
            result = self.run_script(action)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, 'UNKNOWN\n')
            self.assertEqual(lock.read_text(), 'foreign')

    def test_status_does_not_create_runtime_or_lock(self):
        (self.runtime / 'lock').unlink()
        self.runtime.rmdir()
        result = self.run_script('status')
        self.assertEqual(result.stdout, 'STOPPED\n')
        self.assertFalse(self.runtime.exists())

    def test_status_preserves_previous_boot_state(self):
        state_path = self.runtime / 'state.json'
        original = json.dumps({'version': 1, 'boot_id': 'previous-boot', 'token': 'a' * 32})
        state_path.write_text(original)
        (self.runtime / 'lock').touch()
        before = {path.name for path in self.runtime.iterdir()}
        result = self.run_script('status')
        self.assertEqual(result.stdout, 'STOPPED\n')
        self.assertEqual(state_path.read_text(), original)
        self.assertEqual({path.name for path in self.runtime.iterdir()}, before)

    def test_invalid_display_is_rejected(self):
        self.env['LINUX_DESKTOP_DISPLAY'] = '2;id'
        for action in ('start', 'stop', 'status'):
            result = self.run_script(action)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, 'ERROR\n')

    def test_configured_display_artifact_blocks_start(self):
        self.env['LINUX_DESKTOP_DISPLAY'] = '7'
        tmp = Path(self.env['PREFIX']) / 'tmp'
        tmp.mkdir(parents=True)
        lock = tmp / '.X7-lock'
        lock.write_text('foreign')
        result = self.run_script('start')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('display :7', result.stderr)
        self.assertEqual(lock.read_text(), 'foreign')

    def spawn_fake(self, argv, token=None):
        env = dict(self.env)
        if token:
            env['LINUX_DESKTOP_INSTANCE'] = token
        code = 'import os,sys; os.execve("/bin/sh", sys.argv[1:], dict(os.environ))'
        process = subprocess.Popen([sys.executable, '-c', code, *argv], env=env)
        self.addCleanup(lambda: (process.kill(), process.wait(timeout=5)) if process.poll() is None else None)
        self.wait_for(lambda: Path(f'/proc/{process.pid}/cmdline').read_bytes().startswith(argv[0].encode()))
        return process

    def write_state(self, token):
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        (self.runtime / 'state.json').write_text(json.dumps({'version': 1, 'boot_id': boot, 'token': token}))

    def load_desktop(self):
        spec = importlib.util.spec_from_file_location('desktop', SCRIPTS / 'desktop.py')
        desktop = importlib.util.module_from_spec(spec)
        with mock.patch.dict(os.environ, self.env):
            spec.loader.exec_module(desktop)
        return desktop

    def test_owned_finds_only_processes_with_session_token(self):
        token, other = 'a' * 32, 'b' * 32
        rootfs = '--rootfs=/x/containers/debian/rootfs'
        x11 = self.spawn_fake(['termux-x11 com.termux.x11 :2', '-c', 'sleep 60; :'], token)
        self.spawn_fake(['termux-x11 com.termux.x11 :2', '-c', 'sleep 60; :'], other)
        self.spawn_fake(['termux-x11 com.termux.x11 :20', '-c', 'sleep 60; :'], token)
        session = self.spawn_fake(['/usr/bin/proot', '-c', 'sleep 60; :', '--kill-on-exit', rootfs,
                                   f'env LINUX_DESKTOP_INSTANCE={token} sh'])
        self.spawn_fake(['/usr/bin/proot', '-c', 'sleep 60; :', '--kill-on-exit', rootfs,
                         f'env LINUX_DESKTOP_INSTANCE={other} sh'])
        self.spawn_fake(['/usr/bin/proot', '-c', 'sleep 60; :', '--kill-on-exit', '--rootfs=/x/ubuntu/rootfs',
                         f'env LINUX_DESKTOP_INSTANCE={token} sh'])
        found = self.load_desktop().owned(token)
        self.assertEqual(found, {'x11': [x11.pid], 'session': [session.pid]})

    def test_stop_terminates_owned_x11_and_clears_state(self):
        token = 'a' * 32
        self.write_state(token)
        x11 = self.spawn_fake(['termux-x11 com.termux.x11 :2', '-c', 'sleep 60; :'], token)
        result = self.run_script('stop')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'STOPPED\n')
        self.assertIsNotNone(x11.poll())
        self.assertFalse((self.runtime / 'state.json').exists())

    def test_stop_never_signals_proot_directly(self):
        token = 'a' * 32
        self.write_state(token)
        session = self.spawn_fake(['/usr/bin/proot', '-c', 'sleep 60; :', '--kill-on-exit',
                                   '--rootfs=/x/debian/rootfs', f'env LINUX_DESKTOP_INSTANCE={token} sh'])
        result = self.run_script('stop')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'ERROR\n')
        self.assertIsNone(session.poll())
        self.assertTrue((self.runtime / 'state.json').exists())

    def test_status_with_dead_session_is_stopped_and_partial_is_failed(self):
        token = 'a' * 32
        self.write_state(token)
        self.assertEqual(self.run_script('status').stdout, 'STOPPED\n')
        self.spawn_fake(['termux-x11 com.termux.x11 :2', '-c', 'sleep 60; :'], token)
        result = self.run_script('status')
        self.assertEqual(result.stdout, 'FAILED\n')
        self.assertTrue((self.runtime / 'state.json').exists())

    def test_fifo_lock_returns_error_without_blocking(self):
        (self.runtime / 'lock').unlink()
        os.mkfifo(self.runtime / 'lock')
        for action in ('start', 'stop', 'status'):
            result = self.run_script(action)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, 'ERROR\n')
            self.assertTrue((self.runtime / 'lock').is_fifo())

    def test_fifo_state_returns_error_without_blocking(self):
        os.mkfifo(self.runtime / 'state.json')
        for action in ('start', 'stop', 'status'):
            result = self.run_script(action)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, 'ERROR\n')
            self.assertTrue((self.runtime / 'state.json').is_fifo())

    def test_missing_boot_id_preserves_state_for_all_actions(self):
        state_path = self.runtime / 'state.json'
        original = json.dumps({'version': 1, 'token': 'a' * 32})
        state_path.write_text(original)
        for action in ('start', 'stop', 'status'):
            result = self.run_script(action)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, 'ERROR\n')
            self.assertTrue(state_path.exists(), 'state file must not be renamed')
            self.assertEqual(state_path.read_text(), original)
            self.assertEqual({path.name for path in self.runtime.iterdir()}, {'lock', 'state.json'})

    def test_status_with_state_but_no_lock_fails_closed(self):
        (self.runtime / 'lock').unlink()
        state_path = self.runtime / 'state.json'
        state_path.write_text('{}')
        result = self.run_script('status')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'ERROR\n')
        self.assertEqual(state_path.read_text(), '{}')
        self.assertFalse((self.runtime / 'lock').exists())

    def gated_runner(self, stage):
        marker = self.home / 'executed'
        ready = self.home / 'ready'
        program = '''
import fcntl, importlib.util, json, os, stat, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location('desktop', sys.argv[1])
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)
state = {'version': 1, 'token': 'a' * 32, 'boot_id': desktop.boot_id()}
if sys.argv[2] == 'fds':
    lock = open(desktop.RUNTIME / 'lock', 'r+')
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
    extra = open(desktop.RUNTIME / 'extra', 'w')
    def checkpoint_fds(state, *args, **kwargs):
        Path(sys.argv[3]).write_text(json.dumps({'pid': state['x11']['pid'], 'lock': lock.fileno(), 'extra': extra.fileno()}))
        while True:
            time.sleep(.01)
    desktop.save_state = checkpoint_fds
if sys.argv[2] == 'syncfail':
    original_fsync = desktop.os.fsync
    def fail_dir_fsync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError('simulated directory fsync failure')
        original_fsync(fd)
    desktop.os.fsync = fail_dir_fsync
original = desktop.save_state
def checkpoint(state, *args, **kwargs):
    if sys.argv[2] != 'before':
        original(state, *args, **kwargs)
    Path(sys.argv[3]).write_text(json.dumps(state['x11']))
    while True:
        time.sleep(.01)
if sys.argv[2] in ('before', 'after'):
    desktop.save_state = checkpoint
command = [sys.executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text(Path(sys.argv[2]).read_text())', sys.argv[4], str(desktop.STATE)]
try:
    desktop.gated_launch(command, state, 'x11')
except Exception:
    if sys.argv[2] == 'syncfail':
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            print('child reaped', file=sys.stderr)
        else:
            print('child not reaped: ' + str(pid), file=sys.stderr)
    raise
'''
        process = subprocess.Popen([sys.executable, '-c', program, str(SCRIPTS / 'desktop.py'),
                                    stage, str(ready), str(marker)], env=self.env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        return process, ready, marker

    def wait_for(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.02)
        self.fail('timed out waiting for process state')

    def assert_child_exited(self, pid):
        def exited():
            try:
                stat = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
                return stat[0] == 'Z'
            except FileNotFoundError:
                return True
        self.wait_for(exited)

    def test_initial_state_is_published_only_after_full_file_fsync(self):
        program = '''
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('desktop', sys.argv[1])
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)
original = os.fsync
def pause(fd):
    Path(sys.argv[2]).write_text('ready')
    while True: pass
desktop.os.fsync = pause
desktop.save_state({'version': 1, 'token': 'a' * 32, 'boot_id': desktop.boot_id()}, initial=True)
'''
        ready = self.home / 'ready'
        process = subprocess.Popen([sys.executable, '-c', program, str(SCRIPTS / 'desktop.py'), str(ready)], env=self.env)
        try:
            self.wait_for(lambda: ready.exists() or process.poll() is not None)
            self.assertTrue(ready.exists())
            self.assertFalse((self.runtime / 'state.json').exists())
        finally:
            process.kill()
            process.wait(timeout=5)

    def test_gated_launch_rejects_missing_state_with_existing_record(self):
        program = '''
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location('desktop', sys.argv[1])
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)
state = {'version': 1, 'token': 'a' * 32, 'boot_id': desktop.boot_id(), 'x11': {'pid': 123, 'start': '123'}}
try:
    desktop.gated_launch(['/bin/true'], state, 'session')
except desktop.Failure:
    pass
else:
    raise AssertionError('missing committed state accepted')
assert not desktop.STATE.exists()
'''
        result = subprocess.run([sys.executable, '-c', program, str(SCRIPTS / 'desktop.py')], env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_gate_return_marks_exec_outcome_inconclusive(self):
        program = '''
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location('desktop', sys.argv[1])
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)
state = {'version': 1, 'token': 'a' * 32, 'boot_id': desktop.boot_id()}
state, outcome = desktop.gated_launch(['/bin/true'], state, 'x11')
assert outcome == 'exec-unconfirmed'
assert state['x11']['phase'] == 'starting'
os.waitpid(state['x11']['pid'], 0)
'''
        result = subprocess.run([sys.executable, '-c', program, str(SCRIPTS / 'desktop.py')], env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_gated_launch_returns_updated_state_for_sequential_launch(self):
        program = '''
import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location('desktop', sys.argv[1])
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)
state = {'version': 1, 'token': 'a' * 32, 'boot_id': desktop.boot_id()}
desktop.save_state(state, initial=True)
state, _ = desktop.gated_launch(['/bin/true'], state, 'x11')
state, _ = desktop.gated_launch(['/bin/true'], state, 'session')
assert 'x11' in state and 'session' in state
assert desktop.load_state() == state
for kind in ('x11', 'session'): os.waitpid(state[kind]['pid'], 0)
'''
        result = subprocess.run([sys.executable, '-c', program, str(SCRIPTS / 'desktop.py')], env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_gated_child_detaches_session_and_standard_streams(self):
        program = '''
import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location('desktop', sys.argv[1])
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)
state = {'version': 1, 'token': 'a' * 32, 'boot_id': desktop.boot_id()}
child = 'import os,sys,json; open(sys.argv[1],"w").write(json.dumps([os.getsid(0), os.getpid(), os.readlink("/proc/self/fd/0"), os.readlink("/proc/self/fd/1"), os.readlink("/proc/self/fd/2")]))'
state, _ = desktop.gated_launch([sys.executable, '-c', child, sys.argv[2]], state, 'x11')
os.waitpid(state['x11']['pid'], 0)
'''
        marker = self.home / 'streams'
        result = subprocess.run([sys.executable, '-c', program, str(SCRIPTS / 'desktop.py'), str(marker)], env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        session, pid, stdin, stdout, stderr = json.loads(marker.read_text())
        self.assertEqual(session, pid)
        self.assertEqual((stdin, stdout, stderr), ('/dev/null', '/dev/null', '/dev/null'))

    def test_gated_launch_reports_exec_failure_and_reaps_child(self):
        program = '''
import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location('desktop', sys.argv[1])
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)
state = {'version': 1, 'token': 'a' * 32, 'boot_id': desktop.boot_id()}
try:
    desktop.gated_launch(['/no-such-executable-linux-desktop'], state, 'x11')
except desktop.Failure as error:
    assert 'exec' in str(error)
    try: os.waitpid(-1, os.WNOHANG)
    except ChildProcessError: pass
    else: raise AssertionError('failed child not reaped')
else:
    raise AssertionError('exec failure not reported')
assert desktop.load_state()['x11']['command'] == ['/no-such-executable-linux-desktop']
'''
        result = subprocess.run([sys.executable, '-c', program, str(SCRIPTS / 'desktop.py')], env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_gated_launch_commits_identity_before_exec(self):
        process, _, marker = self.gated_runner('release')
        _, error = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, error)
        self.wait_for(marker.exists)
        recorded = json.loads(marker.read_text())
        self.assertEqual(recorded['boot_id'], Path('/proc/sys/kernel/random/boot_id').read_text().strip())
        self.assertEqual(recorded['token'], 'a' * 32)
        self.assertEqual(recorded['x11']['session_id'], recorded['token'])
        self.assertEqual(recorded['x11']['phase'], 'starting')
        self.assertGreater(recorded['x11']['pid'], 1)
        self.assertTrue(recorded['x11']['start'].isdigit())
        self.assertEqual(recorded['x11']['command'][0], sys.executable)

    def test_gated_child_exits_if_parent_crashes_before_commit(self):
        process, ready, marker = self.gated_runner('before')
        self.wait_for(lambda: ready.exists() or process.poll() is not None)
        self.assertTrue(ready.exists(), process.stderr.read() if process.poll() is not None else '')
        child = json.loads(ready.read_text())
        self.assertFalse(marker.exists())
        process.kill()
        process.communicate(timeout=5)
        self.assert_child_exited(child['pid'])
        self.assertFalse((self.runtime / 'state.json').exists())
        self.assertFalse(marker.exists())

    def test_gated_child_exits_if_parent_crashes_after_commit(self):
        process, ready, marker = self.gated_runner('after')
        self.wait_for(lambda: ready.exists() or process.poll() is not None)
        self.assertTrue(ready.exists(), process.stderr.read() if process.poll() is not None else '')
        child = json.loads(ready.read_text())
        self.assertEqual(json.loads((self.runtime / 'state.json').read_text())['x11'], child)
        self.assertFalse(marker.exists())
        process.kill()
        process.communicate(timeout=5)
        self.assert_child_exited(child['pid'])
        self.assertFalse(marker.exists())
        self.assertTrue((self.runtime / 'state.json').exists())

    def test_gated_child_closes_inherited_lock_and_unrelated_fds(self):
        process, ready, _ = self.gated_runner('fds')
        self.wait_for(lambda: ready.exists() or process.poll() is not None)
        self.assertTrue(ready.exists(), process.stderr.read() if process.poll() is not None else '')
        info = json.loads(ready.read_text())
        descriptors = Path(f"/proc/{info['pid']}/fd")
        self.wait_for(lambda: not (descriptors / str(info['lock'])).exists() and
                      not (descriptors / str(info['extra'])).exists())
        self.assertTrue(descriptors.exists(), 'gated child exited before descriptor check')
        process.kill()
        process.communicate(timeout=5)
        self.assert_child_exited(info['pid'])

    def test_gated_launch_does_not_release_after_directory_fsync_failure(self):
        process, _, marker = self.gated_runner('syncfail')
        _, error = process.communicate(timeout=5)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn('simulated directory fsync failure', error)
        self.assertIn('child reaped', error)
        child = json.loads((self.runtime / 'state.json').read_text())['x11']
        self.assert_child_exited(child['pid'])
        self.assertFalse(marker.exists())

    def test_lock_timeout_is_busy(self):
        with (self.runtime / 'lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_script('status')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'BUSY\n')

    def test_stop_never_signals_foreign_pid_in_state(self):
        foreign = subprocess.Popen(['sleep', '60'])
        def cleanup():
            if foreign.poll() is None:
                foreign.terminate()
            foreign.wait(timeout=5)
        self.addCleanup(cleanup)
        stat = Path(f'/proc/{foreign.pid}/stat').read_text().rsplit(')', 1)[1].split()
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        (self.runtime / 'state.json').write_text(json.dumps({
            'version': 1, 'boot_id': boot, 'token': 'a' * 32,
            'x11': {'pid': foreign.pid, 'start': stat[19]},
            'session': {'pid': foreign.pid, 'start': stat[19]},
        }))
        result = self.run_script('stop')
        self.assertEqual(result.stdout, 'STOPPED\n')
        self.assertIsNone(foreign.poll())

    def test_previous_boot_never_signals_reused_pid(self):
        foreign = subprocess.Popen(['sleep', '60'])
        def cleanup():
            if foreign.poll() is None:
                foreign.terminate()
            foreign.wait(timeout=5)
        self.addCleanup(cleanup)
        stat = Path(f'/proc/{foreign.pid}/stat').read_text().rsplit(')', 1)[1].split()
        (self.runtime / 'state.json').write_text(json.dumps({
            'version': 1, 'boot_id': 'previous-boot', 'token': 'a' * 32,
            'x11': {'pid': foreign.pid, 'start': stat[19]},
        }))
        result = self.run_script('stop')
        self.assertEqual(result.stdout, 'STOPPED\n')
        self.assertFalse((self.runtime / 'state.json').exists())
        self.assertIsNone(foreign.poll())

    def test_display_probe_fails_closed_on_ambiguous_socket_errors(self):
        spec = importlib.util.spec_from_file_location('desktop', SCRIPTS / 'desktop.py')
        desktop = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(desktop)
        desktop.TMP = self.home / 'empty-tmp'
        for index in range(3):
            for error in (errno.EACCES, errno.ETIMEDOUT, errno.EAGAIN):
                with self.subTest(endpoint=index, error=error):
                    outcomes = [errno.ENOENT] * 3
                    outcomes[index] = error
                    with mock.patch.object(desktop.socket, 'socket') as factory:
                        connect = factory.return_value.__enter__.return_value.connect_ex
                        connect.side_effect = outcomes
                        with self.assertRaises((desktop.Failure, OSError)):
                            desktop.display_occupied()
                        self.assertEqual(connect.call_count, index + 1)

    def test_display_probe_rejects_connection_refusal_and_accepts_enoent(self):
        spec = importlib.util.spec_from_file_location('desktop', SCRIPTS / 'desktop.py')
        desktop = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(desktop)
        desktop.TMP = self.home / 'empty-tmp'
        with mock.patch.object(desktop.socket, 'socket') as factory:
            factory.return_value.__enter__.return_value.connect_ex.return_value = errno.ENOENT
            self.assertFalse(desktop.display_occupied())
        for index in range(3):
            with self.subTest(endpoint=index), mock.patch.object(desktop.socket, 'socket') as factory:
                results = [errno.ENOENT] * 3
                results[index] = errno.ECONNREFUSED
                factory.return_value.__enter__.return_value.connect_ex.side_effect = results
                with self.assertRaises((desktop.Failure, OSError)):
                    desktop.display_occupied()
        with mock.patch.object(desktop.socket, 'socket', side_effect=OSError(errno.EAFNOSUPPORT, 'unsupported')):
            self.assertFalse(desktop.display_occupied())

    def test_bound_non_listening_abstract_display_is_not_vacant(self):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind('\0/tmp/.X11-unix/X2')
        self.addCleanup(server.close)
        spec = importlib.util.spec_from_file_location('desktop', SCRIPTS / 'desktop.py')
        desktop = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(desktop)
        desktop.TMP = self.home / 'empty-tmp'
        with self.assertRaises((desktop.Failure, OSError)):
            desktop.display_occupied()

    def test_abstract_display_socket_is_detected(self):
        import socket
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind('\0/tmp/.X11-unix/X2')
        server.listen()
        self.addCleanup(server.close)
        result = self.run_script('start')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'ERROR\n')
        self.assertIn('display :2', result.stderr)

    def test_foreign_display_artifact_is_not_removed(self):
        tmp = Path(self.env['PREFIX']) / 'tmp'
        tmp.mkdir(parents=True)
        lock = tmp / '.X2-lock'
        lock.write_text('foreign')
        result = self.run_script('start')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'ERROR\n')
        self.assertEqual(lock.read_text(), 'foreign')


class LaunchGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Path(self.temp.name) / 'runtime'
        self.runtime.mkdir()
        self.token = 'a' * 32
        self.state = {'version': 1, 'boot_id': 'test-boot', 'token': self.token}
        spec = importlib.util.spec_from_file_location('desktop_launch_gate', SCRIPTS / 'desktop.py')
        self.desktop = importlib.util.module_from_spec(spec)
        with mock.patch.dict(os.environ, {'HOME': self.temp.name, 'PREFIX': self.temp.name}):
            spec.loader.exec_module(self.desktop)
        self.desktop.RUNTIME = self.runtime
        self.desktop.STATE = self.runtime / 'state.json'

    def tearDown(self):
        self.temp.cleanup()

    def test_x11_launch_uses_identity_gate_not_direct_popen(self):
        with mock.patch.object(self.desktop, 'gated_launch', return_value=({**self.state, 'x11': {}}, 'exec-unconfirmed')) as gate, \
             mock.patch.object(self.desktop, 'proc_info', return_value={'start': '11'}), \
             mock.patch.object(self.desktop.subprocess, 'Popen') as popen:
            result = self.desktop.launch_x11(self.state)
        gate.assert_called_once()
        popen.assert_not_called()
        self.assertIn('x11', result)

    def test_session_launch_uses_identity_gate_not_direct_popen(self):
        with mock.patch.object(self.desktop, 'gated_launch', return_value=({**self.state, 'session': {}}, 'exec-unconfirmed')) as gate, \
             mock.patch.object(self.desktop, 'save_state'), \
             mock.patch.object(self.desktop, 'owned', return_value={'x11': [], 'session': [123]}), \
             mock.patch.object(self.desktop, 'proc_info', return_value={'start': '12'}), \
             mock.patch.object(self.desktop, 'session_tracees', return_value=(123, {})), \
             mock.patch.object(self.desktop.subprocess, 'Popen') as popen:
            result = self.desktop.launch_session(self.state)
        gate.assert_called_once()
        popen.assert_not_called()
        self.assertEqual(result['session']['pid'], 123)
        self.assertEqual(result['session']['session_id'], self.token)
        self.assertEqual(result['session']['phase'], 'running')
        self.assertIn('LINUX_DESKTOP_INSTANCE=' + self.token, gate.call_args.args[0])
        self.assertEqual(gate.call_args.args[2], 'session')
        self.assertEqual(result['session']['command'], gate.call_args.args[0])
        self.assertEqual(result['session']['start'], '12')
        self.assertEqual(result['session']['log'], str(self.runtime / 'logs/session.log'))
        self.assertEqual(gate.call_args.args[0][-2:], [str(SCRIPTS / 'xfce-components.sh'), ':2'])
        self.assertEqual(gate.call_args.args[0][8:11], ['env', 'LINUX_DESKTOP_INSTANCE=' + self.token, 'sh'])
        self.assertEqual(gate.call_args.args[1], self.state)
        self.assertEqual(gate.call_args.kwargs['log_path'], self.runtime / 'logs/session.log')
        self.assertEqual(gate.call_count, 1)
        self.assertEqual(popen.call_count, 0)


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
