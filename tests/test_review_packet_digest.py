"""The packet digests a past commit's unit without a temporary directory. Inputs are synthetic."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import review_packet  # noqa: E402
from source_digest import tu_digest, tu_digest_blobs  # noqa: E402


class DigestAt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'u').mkdir()
        (self.root / 'u/A.cpp').write_text('int a;\n')
        (self.root / 'u/A.h').write_text('extern int a;\n')
        for argv in (['init', '-q'], ['add', '.'], ['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x']):
            subprocess.run(['git', *argv], cwd=self.root, check=True)
        self.commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=self.root, check=True,
                                     capture_output=True, text=True).stdout.strip()

    def test_matches_checkout_digest_without_a_temporary_directory(self):
        files = ['u/A.cpp', 'u/A.h']
        with patch('tempfile.mkdtemp', side_effect=FileNotFoundError('no usable temporary directory')):
            self.assertEqual(review_packet.digest_at(self.root, self.commit, files), tu_digest(self.root, files))

    def test_missing_file_at_commit_is_none(self):
        self.assertIsNone(review_packet.digest_at(self.root, self.commit, ['u/Missing.h']))

    def test_blob_digest_refuses_escaping_paths(self):
        with self.assertRaises(ValueError):
            tu_digest_blobs({'../x.h': b''})


if __name__ == '__main__':
    unittest.main()
