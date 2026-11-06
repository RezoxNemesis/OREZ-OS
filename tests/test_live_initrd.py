import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'build' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load('patch-live-initrd')
audit = load('audit-live-initrd')
media = load('update-media-checksums')


def entry(name, data=b'', mode=stat.S_IFREG | 0o755):
    # Independent fixture producer, not production archive code.
    name = name.encode() + b'\0'
    values = [123, mode, 0, 0, 1, 1700000000, len(data), 0, 0, 0, 0, len(name), 0]
    value = b'070701' + b''.join(f'{v:08X}'.encode() for v in values) + name
    value += b'\0' * (-len(value) % 4)
    return value + data + b'\0' * (-len(data) % 4)


class InitrdPatchTests(unittest.TestCase):
    def fixture(self):
        old, new = builder.sources()
        prefix = b'early firmware fixture\0'
        plain = (entry('unchanged-before', b'preserve before') + entry(builder.HOOK, old)
                 + entry('unchanged-after', b'preserve after') + entry('TRAILER!!!', mode=0))
        data = prefix + builder.pack(plain)
        return old, new, prefix, plain, data

    def pins(self, prefix, plain, data):
        return patch.multiple(builder, EXPECTED_INITRD_SHA256=builder.sha(data),
                              PREFIX_BYTES=len(prefix), PREFIX_SHA256=builder.sha(prefix),
                              ARCHIVE_SHA256=builder.sha(plain))

    def test_replacement_preserves_every_other_byte_and_is_reversible(self):
        old, new, prefix, plain, data = self.fixture()
        changed = builder.replace_hook(plain, old, new)
        expected = (entry('unchanged-before', b'preserve before') + entry(builder.HOOK, new)
                    + entry('unchanged-after', b'preserve after') + entry('TRAILER!!!', mode=0))
        self.assertEqual(changed, expected)
        self.assertEqual(builder.replace_hook(changed, new, old), plain)

    def test_wrong_missing_duplicate_and_malformed_member_refused(self):
        old, new, prefix, plain, data = self.fixture()
        bad = [entry('TRAILER!!!', mode=0), plain.replace(old, b'x'*len(old)),
               entry(builder.HOOK, old) + plain, plain[:-1], plain + b'extra archive',
               plain.replace(b'070701', b'badbad', 1)]
        for archive in bad:
            with self.subTest(size=len(archive)), self.assertRaises(ValueError):
                builder.replace_hook(archive, old, new)

    def test_wrong_upstream_and_existing_outputs_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original, output, report = root/'original', root/'patched', root/'report'
            original.write_bytes(b'unrecognized initrd')
            with self.assertRaisesRegex(ValueError, 'unrecognized initrd'):
                builder.patch(original, output, report)
            self.assertFalse(output.exists())
            output.write_bytes(b'previous evidence')
            with self.assertRaises(ValueError):
                builder.patch(original, output, report)
            self.assertEqual(output.read_bytes(), b'previous evidence')

    def test_prefix_preservation_roundtrip_and_tamper_detection(self):
        old, new, prefix, plain, data = self.fixture()
        with tempfile.TemporaryDirectory() as directory, self.pins(prefix, plain, data):
            root = Path(directory)
            original, output, report = root/'original', root/'patched', root/'report'
            original.write_bytes(data)
            builder.patch(original, output, report)
            self.assertTrue(output.read_bytes().startswith(prefix))
            builder.verify(output, report)
            # Even a forged manifest cannot authorize unrelated CPIO edits.
            changed = builder.replace_hook(plain, old, new).replace(b'preserve after', b'corrupt! after')
            output.write_bytes(prefix + builder.pack(changed))
            value = json.loads(report.read_text()); value['patched_sha256'] = builder.sha(output.read_bytes())
            report.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'unrelated changes'):
                builder.verify(output, report)

    def test_manifest_cannot_change_verified_prefix(self):
        old, new, prefix, plain, data = self.fixture()
        with tempfile.TemporaryDirectory() as directory, self.pins(prefix, plain, data):
            root = Path(directory)
            original, output, report = root/'original', root/'patched', root/'report'
            original.write_bytes(data)
            builder.patch(original, output, report)
            value = json.loads(report.read_text()); value['early_prefix_bytes'] = 2
            report.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'prefix'):
                builder.verify(output, report)

    def test_decoder_output_is_bounded(self):
        data = builder.pack(b'x' * 4096)
        with patch.object(builder, 'MAX_ARCHIVE_BYTES', 1024):
            with self.assertRaises(subprocess.SubprocessError):
                builder.unpack(data)

    def test_symlink_and_oversized_input_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'original').write_bytes(b'fixture')
            (root/'link').symlink_to(root/'original')
            with self.assertRaises(ValueError):
                builder.read_initrd(root/'link')
            with patch.object(builder, 'MAX_INITRD_BYTES', 2), self.assertRaises(ValueError):
                builder.read_initrd(root/'original')

    def test_hook_uses_local_repositories_without_weakening_authentication(self):
        hook = ROOT / 'image/initramfs' / builder.HOOK
        subprocess.run(['sh', '-n', str(hook)], check=True)
        text = hook.read_text()
        for expected in ['Dir::Etc::sourcelist=/etc/apt/sources.list.d/cdrom.sources',
                         'Dir::Etc::sourceparts=-', '--kill-after=5s 90s', 'log_warning_msg']:
            self.assertIn(expected, text)
        for forbidden in ['--allow-unauthenticated', 'AllowInsecureRepositories', 'NOPASSWD', 'ResultActive=yes', 'rm -f', 'apt-get install']:
            self.assertNotIn(forbidden, text)


class MediaChecksumTests(unittest.TestCase):
    def test_updates_only_orez_files_and_preserves_upstream_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / 'fixture'; fixture.write_bytes(b'changed')
            original = '0' * 32 + '  ./casper/initrd\n' + '1' * 32 + '  ./casper/filesystem.squashfs\n'
            result = media.parse(media.update(original, {name: fixture for name in media.NAMES}))
            self.assertEqual(result['./casper/filesystem.squashfs'], '1' * 32)
            for name in media.NAMES:
                self.assertEqual(result[name], hashlib.md5(b'changed').hexdigest())

    def test_malformed_missing_duplicate_and_escaping_paths_refused(self):
        line = '0' * 32 + '  ./casper/initrd\n'
        for value in ['', line + line, line + '0' * 32 + '  ./../escape\n', 'bad digest  ./casper/initrd\n']:
            with self.assertRaises(ValueError):
                media.parse(value)
        with self.assertRaises(ValueError):
            media.update(line, {'./casper/other': Path('/dev/null')})


class LiveAuthAuditTests(unittest.TestCase):
    def fixture(self, root, grants=True):
        folder = root / 'scripts/casper-bottom'; folder.mkdir(parents=True)
        (folder/'25adduser').write_text('echo "$USERNAME ALL=(ALL) NOPASSWD: ALL"\ndb_set passwd/user-password-crypted U6aMy0wojraho\n' if grants else '# reviewed elsewhere\n')
        (folder/'44pk_allow_ubuntu').write_text('Action=*\nResultActive=yes\nResultInactive=yes\n' if grants else '# reviewed elsewhere\n')

    def test_both_privilege_paths_and_empty_password_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            result = audit.inspect(root)
            self.assertEqual({f['code'] for f in result['findings']}, {'PASSWORDLESS_SUDO', 'BLANK_LIVE_PASSWORD', 'WILDCARD_POLKIT'})
            self.assertEqual(result['status'], 'BLOCKED')
            self.assertFalse(result['owner_authentication_qualified'])

    def test_absence_of_patterns_never_claims_runtime_security(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root, False)
            result = audit.inspect(root)
            self.assertEqual(result['findings'], [])
            self.assertFalse(result['effective_policy_tested'])
            self.assertFalse(result['owner_authentication_qualified'])
            self.assertIn('REVIEW', result['status'])

    def test_missing_or_linked_hooks_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                audit.inspect(root)
            self.fixture(root)
            hook = root/'scripts/casper-bottom/25adduser'; hook.unlink(); hook.symlink_to('/dev/null')
            with self.assertRaises(ValueError):
                audit.inspect(root)


if __name__ == '__main__':
    unittest.main()
