"""Safety and protocol regressions for the diskless graphical diagnostic."""
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('vm_probe', ROOT / 'build/probe-virgl-vm.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class VMProbeTests(unittest.TestCase):
    def test_both_boot_paths_have_only_offline_readonly_iso_and_private_control(self):
        for boot in ['direct', 'uefi']:
            cmd = probe.command(Path('/tmp/input.iso'), Path('/tmp/result'),
                                Path('/tmp/runtime'), boot, Path('/tmp/code.fd'))
            self.assertEqual(cmd[cmd.index('-nic') + 1], 'none')
            self.assertEqual(cmd[cmd.index('-monitor') + 1], 'none')
            self.assertTrue(cmd[cmd.index('-qmp') + 1].startswith('unix:/tmp/runtime/'))
            drives = [cmd[i + 1] for i, item in enumerate(cmd) if item == '-drive']
            writable = [d for d in drives if 'readonly=on' not in d]
            self.assertEqual(writable, [] if boot == 'direct' else
                             ['if=pflash,format=raw,unit=1,file=/tmp/runtime/vars.fd'])
            self.assertEqual(len(drives), 1 if boot == 'direct' else 3)
            for forbidden in ['-virtfs', '-fsdev', '-vnc', '-netdev', '-enable-kvm']:
                self.assertNotIn(forbidden, cmd)
            self.assertEqual('-kernel' in cmd, boot == 'direct')

    def test_device_input_refused_before_execution(self):
        result = subprocess.run([sys.executable, str(ROOT / 'build/probe-virgl-vm.py'),
                                 '--iso', '/dev/null', '--sha256', '0' * 64,
                                 '--output', '/tmp/not-created-by-device-check', '--boot', 'direct'],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertTrue('regular file' in result.stderr or 'never root' in result.stderr)

    def qmp_exchange(self, response, expected_error=None):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'qmp')
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(path)
            server.listen(1)
            errors = []

            def serve():
                try:
                    connection, _ = server.accept()
                    with connection, connection.makefile('rwb') as stream:
                        stream.write(b'{"QMP": {"version": {}}}\n'); stream.flush()
                        self.assertEqual(json.loads(stream.readline())['execute'], 'qmp_capabilities')
                        stream.write(b'{"return": {}}\n'); stream.flush()
                        self.assertEqual(json.loads(stream.readline())['execute'], 'query-status')
                        # Asynchronous events can precede a command response.
                        stream.write(b'{"event": "RESUME"}\n')
                        if response is not None:
                            for chunk in [response[:5], response[5:]]:
                                stream.write(chunk); stream.flush()
                except Exception as error:
                    errors.append(error)

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            client = probe.QMP(path)
            try:
                if expected_error:
                    with self.assertRaisesRegex(RuntimeError, expected_error):
                        client.call('query-status')
                else:
                    self.assertEqual(client.call('query-status'), {'running': True})
            finally:
                client.close(); server.close(); thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])

    def test_qmp_events_and_fragmented_reply(self):
        self.qmp_exchange(b'{"return": {"running": true}}\n')

    def test_qmp_error_is_not_a_pass(self):
        self.qmp_exchange(b'{"error": {"desc": "unsupported"}}\n', 'unsupported')

    def test_qmp_disconnect_is_not_a_pass(self):
        self.qmp_exchange(None, 'disconnected')

    def test_cleanup_terminates_child(self):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        probe.stop(child)
        self.assertIsNotNone(child.poll())


if __name__ == '__main__':
    unittest.main()
