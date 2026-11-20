import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('desktop', ROOT / 'scripts/desktop.py')
desktop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(desktop)


class ManagerSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.prefix = self.home / 'prefix'
        self.runtime = self.home / '.local/linux-desktop/runtime'
        self.runtime.mkdir(parents=True)
        (self.runtime / 'lock').touch()
        self.env = {'HOME': str(self.home), 'PREFIX': str(self.prefix),
                    'PATH': os.environ['PATH'], 'LINUX_DESKTOP_DISPLAY': '2'}
        self.patch = mock.patch.dict(os.environ, self.env)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.old_runtime, self.old_state, self.old_tmp = desktop.RUNTIME, desktop.STATE, desktop.TMP
        desktop.RUNTIME, desktop.STATE, desktop.TMP = self.runtime, self.runtime / 'state.json', self.prefix / 'tmp'
        self.addCleanup(setattr, desktop, 'RUNTIME', self.old_runtime)
        self.addCleanup(setattr, desktop, 'STATE', self.old_state)
        self.addCleanup(setattr, desktop, 'TMP', self.old_tmp)

    def tearDown(self):
        self.temp.cleanup()

    def test_owned_requires_unique_token_and_exact_display_or_debian_root(self):
        token = 'a' * 32
        x11 = ['termux-x11 com.termux.x11 :2', 'DISPLAY=:2', f'LINUX_DESKTOP_INSTANCE={token}']
        unrelated = ['termux-x11 com.termux.x11 :2', 'DISPLAY=:2', f'LINUX_DESKTOP_INSTANCE={"b" * 32}']
        rootfs = str(self.prefix / 'var/lib/proot-distro/containers/debian/rootfs')
        session = ['/proot', '--kill-on-exit', '--rootfs=' + rootfs,
                   f'LINUX_DESKTOP_INSTANCE={token}']
        with mock.patch.object(desktop, 'process_table', create=True, return_value={
                101: {'start': '11', 'cmd': x11},
                102: {'start': '12', 'cmd': unrelated},
                103: {'start': '13', 'cmd': session},
                104: {'start': '14', 'cmd': ['/proot', '--kill-on-exit', '--rootfs=/x/ubuntu/rootfs',
                                             f'LINUX_DESKTOP_INSTANCE={token}']}}):
            self.assertEqual(desktop.owned(token), {'x11': [101], 'session': [103]})

    def test_status_reports_unknown_for_unowned_display_and_does_not_edit_state(self):
        state = {'version': 1, 'boot_id': desktop.boot_id(), 'token': 'a' * 32}
        desktop.save_state(state, initial=True)
        before = desktop.STATE.read_bytes()
        with mock.patch.object(desktop, 'display_occupied', return_value=True):
            self.assertEqual(desktop.status(state), 'UNKNOWN')
        self.assertEqual(desktop.STATE.read_bytes(), before)

    def test_stop_refuses_to_signal_prout_without_identified_tracee(self):
        token = 'a' * 32
        state = {'version': 1, 'boot_id': desktop.boot_id(), 'token': token,
                 'session': {'pid': 301, 'start': '31', 'session_id': token, 'phase': 'starting',
                             'command': ['proot-distro', 'login']}}
        with mock.patch.object(desktop, 'owned', return_value={'x11': [], 'session': [301]}), \
             mock.patch.object(desktop, 'verified_fd', return_value=999), \
             mock.patch.object(desktop, 'proc_info', return_value={'start': '31', 'cmd': ['/proot']}), \
             mock.patch.object(desktop, 'pidfd_signal') as signal_process:
            with self.assertRaises(desktop.Failure):
                desktop.stop(state)
            signal_process.assert_not_called()


if __name__ == '__main__':
    unittest.main()
