import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('owner_setup', ROOT/'image/live-owner/usr/lib/orez/owner_setup.py')
owner = importlib.util.module_from_spec(spec); spec.loader.exec_module(owner)


class OwnerSetupTests(unittest.TestCase):
    def test_password_validation_rejects_blank_short_and_injected_records(self):
        for value in ['', 'short', 'a'*129, 'long password\nroot:attack', 'long password\x00']:
            with self.subTest(size=len(value)), self.assertRaises(ValueError):
                owner.validate_password(value)
        owner.validate_password('A long test passphrase')

    def test_live_guard_rejects_ordinary_user_and_persistent_boot(self):
        with patch.object(owner.os, 'getuid', return_value=1000):
            with self.assertRaises(ValueError): owner.require_live()
        with patch.object(owner.os, 'getuid', return_value=0), patch.object(owner.os, 'geteuid', return_value=0):
            for text in ['root=/dev/example', 'boot=casper persistent', 'boot=casper persistent=yes']:
                with patch.object(Path, 'read_text', return_value=text), self.assertRaises(ValueError): owner.require_live()
            with patch.object(Path, 'read_text', return_value='boot=casper quiet'): owner.require_live()

    def test_password_is_stdin_only_and_subprocess_errors_are_not_disclosed(self):
        secret = 'Dummy password for test'
        with patch.object(owner.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as child:
            owner.run(['/usr/sbin/chpasswd'], 'owner:'+secret+'\n')
            self.assertNotIn(secret, repr(child.call_args.args))
            self.assertEqual(child.call_args.kwargs['input'], 'owner:'+secret+'\n')
            self.assertEqual(child.call_args.kwargs['timeout'], 20)
            self.assertNotIn('shell', child.call_args.kwargs)
        with patch.object(owner.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, secret, secret)):
            with self.assertRaises(ValueError) as caught: owner.run(['/usr/sbin/chpasswd'], secret)
            self.assertNotIn(secret, str(caught.exception))

    def test_failed_password_change_relocks_owner_and_keeps_setup_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); request=root/'request'; request.write_text('owner\n'); ready=root/'ready'
            for failure in ['command', 'post-validation']:
                calls=[]
                def operation(args, data=None):
                    calls.append((args,data))
                    if failure=='command' and args==['/usr/sbin/chpasswd']: raise ValueError('system failure')
                with patch.multiple(owner, REQUEST=request, READY=ready), \
                     patch.object(owner, 'require_live'), patch.object(owner, 'private_directory'), \
                     patch.object(owner, 'validate_owner', side_effect=[None, ValueError('post-validation')]), \
                     patch.object(owner, 'run', side_effect=operation):
                    with self.assertRaises(ValueError): owner.complete('owner','Dummy password for test')
                self.assertEqual(calls[-1][0], ['/usr/sbin/usermod','--lock','owner'])
                self.assertTrue(request.exists()); self.assertFalse(ready.exists())

    def test_completion_receipt_contains_no_password_and_request_is_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); request=root/'request'; request.write_text('owner\n'); ready=root/'ready'
            with patch.multiple(owner, REQUEST=request, READY=ready), \
                 patch.object(owner, 'require_live'), patch.object(owner, 'private_directory'), \
                 patch.object(owner, 'validate_owner'), patch.object(owner, 'run'):
                owner.complete('owner','Dummy password for test')
            self.assertFalse(request.exists()); self.assertNotIn('password',ready.read_text())
            self.assertEqual(ready.stat().st_mode & 0o777, 0o600)

    def test_pipe_input_is_denied_before_reading_password(self):
        with tempfile.TemporaryDirectory() as directory:
            request=Path(directory)/'request';request.write_text('owner\n')
            with patch.multiple(owner, REQUEST=request, READY=Path(directory)/'absent'), \
                 patch.object(owner,'require_live'),patch.object(owner,'root_file'),patch.object(owner,'validate_owner'), \
                 patch.object(owner.sys.stdin,'isatty',return_value=False),patch.object(owner.getpass,'getpass') as prompt:
                with self.assertRaisesRegex(ValueError,'local console'): owner.enroll()
                prompt.assert_not_called()

    def test_cancel_and_mismatch_do_not_change_account(self):
        with tempfile.TemporaryDirectory() as directory:
            request=Path(directory)/'request';request.write_text('owner\n')
            for replies in [[KeyboardInterrupt()], ['Dummy password for test','Different password for test']]:
                with contextlib.redirect_stdout(io.StringIO()), patch.multiple(owner, REQUEST=request, READY=Path(directory)/'absent'), \
                     patch.object(owner,'require_live'),patch.object(owner,'root_file'),patch.object(owner,'validate_owner'), \
                     patch.object(owner.sys.stdin,'isatty',return_value=True),patch.object(owner.sys.stdout,'isatty',return_value=True), \
                     patch.object(owner.getpass,'getpass',side_effect=replies) as prompt,patch.object(owner,'prepare_console'),patch.object(owner,'complete') as complete:
                    with self.assertRaises((KeyboardInterrupt,ValueError)): owner.enroll()
                    complete.assert_not_called()
                    self.assertGreaterEqual(prompt.call_count, 1)

    def test_unprotected_password_fallback_is_denied_before_input(self):
        import warnings
        def fallback(prompt):
            warnings.warn('Cannot disable terminal echo', owner.getpass.GetPassWarning)
            self.fail('Unprotected input must never be read')
        with patch.object(owner.getpass, 'getpass', side_effect=fallback):
            with self.assertRaisesRegex(ValueError, 'Cannot hide password'):
                owner.hidden_password('Password: ')

    def test_real_terminal_password_is_not_echoed(self):
        import os, pty, select, sys, termios, time
        master, slave = pty.openpty()
        path = ROOT/'image/live-owner/usr/lib/orez/owner_setup.py'
        code = "import importlib.util; s=importlib.util.spec_from_file_location('owner', %r); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); value=m.hidden_password('Password: '); print('READ-OK' if value=='ephemeral test input' else 'READ-FAILED')" % str(path)
        process = None
        captured = b''
        try:
            process = subprocess.Popen([sys.executable, '-c', code], stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
            deadline = time.monotonic()+5
            while b'Password: ' not in captured:
                self.assertLess(time.monotonic(), deadline, 'No password prompt')
                if select.select([master], [], [], .1)[0]: captured += os.read(master, 4096)
            self.assertFalse(termios.tcgetattr(slave)[3] & termios.ECHO)
            os.write(master, b'ephemeral test input\n')
            process.wait(timeout=5)
            while select.select([master], [], [], .1)[0]: captured += os.read(master, 4096)
            self.assertIn(b'READ-OK', captured)
            self.assertNotIn(b'ephemeral test input', captured)
            self.assertTrue(termios.tcgetattr(slave)[3] & termios.ECHO)
        finally:
            if process and process.poll() is None: process.kill(); process.wait()
            os.close(master); os.close(slave)

    def test_owner_boot_components_never_enter_normal_package_allowlist(self):
        manifest=(ROOT/'image/installer/installed-files.txt').read_text()
        self.assertNotIn('owner_setup',manifest);self.assertNotIn('orez-owner-setup',manifest)
        service=(ROOT/'image/live-owner/usr/lib/systemd/system/orez-owner-setup.service').read_text()
        for value in ['ConditionKernelCommandLine=boot=casper','PrivateNetwork=yes','TTYPath=/dev/tty1','StandardOutput=tty','NoNewPrivileges=yes']:
            self.assertIn(value,service)
        dependency=(ROOT/'image/live-owner/etc/systemd/system/sddm.service.d/10-orez-owner.conf').read_text()
        self.assertIn('Requires=orez-owner-setup.service',dependency)
        self.assertIn('After=orez-owner-setup.service',dependency)

