import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('owner_metadata',Path(__file__).resolve().parents[1]/'build/verify-live-owner.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class OwnerMetadataTests(unittest.TestCase):
    listing='\n'.join(mode+' '+owner+' 128 2026-11-05 00:00 '+path for mode,owner,path in [
        ('drwxr-xr-x','0/0','squashfs-root'),('drwxr-xr-x','0/0','squashfs-root/usr'),
        ('drwxr-xr-x','0/0','squashfs-root/usr/lib'),('-rw-r--r--','0/0','squashfs-root/usr/lib/helper.py')])
    def test_canonical(self):module.verify_metadata(self.listing,['usr/lib/helper.py'])
    def test_user_owned_directory_rejected(self):
        with self.assertRaises(ValueError):module.verify_metadata(self.listing.replace('0/0','1000/1000',1),['usr/lib/helper.py'])
    def test_unreadable_or_writable_file_rejected(self):
        for mode in ['-rw-------','-rw-rw-r--','lrwxrwxrwx']:
            with self.assertRaises(ValueError):module.verify_metadata(self.listing.replace('-rw-r--r--',mode),['usr/lib/helper.py'])
    def test_missing_file_rejected(self):
        with self.assertRaises(ValueError):module.verify_metadata(self.listing,['usr/lib/missing.py'])
