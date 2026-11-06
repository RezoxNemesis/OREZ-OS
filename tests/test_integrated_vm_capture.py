"""Regression for the actual scrot timeout that ended the fourth UEFI probe."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integrated_probe', ROOT / 'build/probe-integrated-live.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class IntegratedCaptureTests(unittest.TestCase):
    def test_timeout_removes_partial_frame_and_allows_later_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            frame = Path(directory) / 'guest.png'
            frame.write_bytes(b'truncated collector output')
            record = {'frames': []}
            with patch.object(probe.helper, 'own_window', return_value='123'), \
                    patch.object(probe.subprocess, 'run', side_effect=[
                        subprocess.TimeoutExpired(['scrot'], 15),
                        subprocess.CompletedProcess(['scrot'], 0)]):
                self.assertFalse(probe.capture_sdl_frame(100, {}, frame, record, 5))
                self.assertFalse(frame.exists())
                self.assertEqual(record['frames'], [])
                self.assertEqual(record['frame_errors'][0]['seconds'], 5)
                self.assertTrue(probe.capture_sdl_frame(100, {}, frame, record, 35))
                self.assertEqual(record['frames'], ['guest.png'])

    def test_ambiguous_window_still_refused_without_capture(self):
        with patch.object(probe.helper, 'own_window', return_value=None), \
                patch.object(probe.subprocess, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'unique visible window'):
                probe.capture_sdl_frame(100, {}, Path('/tmp/unused.png'), {'frames': []}, 5)
            run.assert_not_called()
