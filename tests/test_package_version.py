import importlib.util
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('package_info',ROOT/'build/package-info.py')
info=importlib.util.module_from_spec(spec);spec.loader.exec_module(info)


class PackageVersionTests(unittest.TestCase):
 def test_revision_advances_previous_verified_package(self):
  subprocess.run(['dpkg','--compare-versions',info.version(),'gt','0.1.0-1'],check=True)
 def test_unsafe_or_ambiguous_versions_are_rejected(self):
  for value in ['../evil','0.1.0-1;whoami','0.1.0-1\n0.2.0-1','1:0.1.0-1','0.1.0','$(id)-1','0.1.0-1/all']:
   with self.subTest(value=value), self.assertRaises(ValueError):info.version(value)
 def test_prerelease_sorts_before_same_release(self):
  candidate=info.version('0.2.0~rc1-1')
  subprocess.run(['dpkg','--compare-versions',candidate,'lt','0.2.0-1'],check=True)
 def test_artifact_path_matches_declared_version(self):
  result=subprocess.check_output(['python3',str(ROOT/'build/package-info.py'),'path'],text=True).strip()
  self.assertEqual(Path(result),ROOT/'dist'/('orez-shell_'+info.version()+'_all.deb'))
