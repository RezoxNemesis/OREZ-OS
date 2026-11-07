import importlib.util, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('orez_drivers', ROOT / 'overlay/usr/lib/orez/drivers.py')
d = importlib.util.module_from_spec(spec); sys.modules['orez_drivers'] = d; spec.loader.exec_module(d)


def fake_pci(root, name, vendor, cls, driver=None):
    dev = root / name; dev.mkdir(parents=True)
    (dev / 'vendor').write_text(vendor + '\n'); (dev / 'class').write_text(cls + '\n')
    if driver:
        target = root / 'drivers' / driver; target.mkdir(parents=True, exist_ok=True)
        (dev / 'driver').symlink_to(target)


class DriverStatusTests(unittest.TestCase):
    def test_rtx_on_nouveau_needs_setup(self):
        with tempfile.TemporaryDirectory() as t:
            r = Path(t); fake_pci(r, '0000:01:00.0', '0x10de', '0x030000', 'nouveau')
            fake_pci(r, '0000:00:14.0', '0x8086', '0x0c0330', 'xhci_hcd')
            st = d.status(r)
            self.assertTrue(st['nvidia_gpu']); self.assertEqual(st['driver'], 'nouveau'); self.assertTrue(st['needs_setup'])

    def test_nvidia_driver_in_use_needs_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            r = Path(t); fake_pci(r, '0000:01:00.0', '0x10de', '0x030000', 'nvidia')
            self.assertFalse(d.status(r)['needs_setup'])

    def test_no_nvidia_gpu_needs_nothing(self):
        with tempfile.TemporaryDirectory() as t:
            r = Path(t); fake_pci(r, '0000:00:02.0', '0x1af4', '0x030000', 'virtio-pci')
            self.assertFalse(d.status(r)['needs_setup'])

    def test_install_uses_only_ubuntu_drivers_through_pkexec(self):
        src = (ROOT / 'overlay/usr/lib/orez/drivers.py').read_text()
        self.assertIn("['pkexec', 'ubuntu-drivers', 'install']", src)
        self.assertNotIn('.run', src.replace('.run(', ''))


if __name__ == '__main__':
    unittest.main()
