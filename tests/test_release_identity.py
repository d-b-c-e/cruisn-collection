from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'harness'))
from release_identity import source_identity


class SourceIdentityTests(unittest.TestCase):
    def test_checkout_line_endings_do_not_change_source_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            names = ['harness/code.py', 'lib/toolkit/LICENSE', 'lib/toolkit/VERSION',
                     'profiles/force-profiles.user.ini.example', 'fixtures/signals/hit.csv',
                     'fixtures/controls.cfg', 'fixtures/controls.xml']
            for name in names:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'first\nsecond\n')
            subprocess.run(['git', '-C', str(root), '-c', 'core.autocrlf=false', 'add', '.'], check=True)
            first = source_identity(root)
            for name in names:
                (root / name).write_bytes(b'first\r\nsecond\r\n')
            self.assertEqual(source_identity(root), first)
            (root / names[1]).write_bytes(b'a real licence edit\r\n')
            changed = source_identity(root)
            self.assertNotEqual(changed['sha256'], first['sha256'])
            self.assertEqual([name for name in names if changed['files'][name] != first['files'][name]], [names[1]])

    def test_binary_newlines_remain_significant(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            for name in ['fixtures/nvram-game/nvram', 'fixtures/binary.cfg', 'media/texture.png']:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'\0first\r\nsecond')
            before = source_identity(root)
            for name in before['files']:
                path = root / name
                path.write_bytes(path.read_bytes().replace(b'\r\n', b'\n'))
            after = source_identity(root)
            self.assertNotEqual(before['sha256'], after['sha256'])
            self.assertTrue(all(before['files'][name] != after['files'][name] for name in before['files']))
