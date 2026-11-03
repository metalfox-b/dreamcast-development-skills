#!/usr/bin/env python3
"""Verify that the lock actually records bytes and detects drift."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class ToolchainLock(unittest.TestCase):
    def test_record_verify_modified_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'tool'
            source.write_bytes(b'compiler fixture')
            lock = root/'toolchain.lock.json'
            lock.write_text(json.dumps({'files': {'tool': None}, 'generated_assets': []}))
            cmd = [sys.executable, str(Path(__file__).with_name('toolchain_lock.py'))]
            result = subprocess.run(cmd+['record', str(lock), '--version', 'compiler=fixture',
                                         '--commit', 'KOS=revision'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(lock.read_text())
            self.assertEqual(data['files']['tool'], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(data['versions']['compiler'], 'fixture')
            self.assertEqual(data['commits']['KOS'], 'revision')
            self.assertEqual(subprocess.run(cmd+['verify', str(lock)], capture_output=True).returncode, 0)
            source.write_bytes(b'modified compiler')
            result = subprocess.run(cmd+['verify', str(lock)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('DRIFT: tool', result.stdout)
            source.unlink()
            self.assertEqual(subprocess.run(cmd+['verify', str(lock)], capture_output=True).returncode, 1)
            lock.write_text('{"files": {}}')
            self.assertNotEqual(subprocess.run(cmd+['verify', str(lock)], capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
