"""Exercise archive verification and the exact layout the node installs."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('repack', ROOT / 'scripts/repack.py')
repack = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repack)


def tar_blob(name='opencode', kind=tarfile.REGTYPE):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        item = tarfile.TarInfo(name)
        item.type = kind
        if kind == tarfile.REGTYPE:
            item.size = 15
            archive.addfile(item, io.BytesIO(b'synthetic bytes'))
        else:
            item.linkname = '/outside/opencode'
            archive.addfile(item)
    return buffer.getvalue()


class Repack(unittest.TestCase):
    def test_official_pins_cover_only_reviewed_platforms(self):
        pin = json.loads((ROOT / 'upstream.json').read_text())
        self.assertEqual(pin['version'], '2.2.1')
        self.assertEqual(set(pin['platforms']), {'darwin-arm64', 'darwin-x64', 'linux-arm64', 'linux-x64'})
        for item in pin['platforms'].values():
            self.assertTrue(item['url'].startswith('https://opencode.ai/files/bin/2.2.1/'))
            self.assertRegex(item['sha256'], r'^[0-9a-f]{64}$')

    def test_repacked_root_matches_release_asset_and_is_deterministic(self):
        blob = tar_blob()
        pin = {'platforms': {'linux-arm64': {'sha256': hashlib.sha256(blob).hexdigest()}}}
        with tempfile.TemporaryDirectory() as folder:
            dest = repack.repack(blob, 'linux-arm64', pin, folder)
            first = dest.read_bytes()
            self.assertEqual(repack.repack(blob, 'linux-arm64', pin, folder).read_bytes(), first)
            with tarfile.open(dest, 'r:gz') as archive:
                executable = archive.getmember(dest.name.removesuffix('.tar.gz'))
                self.assertEqual(executable.mode, 0o755)
                self.assertTrue(executable.isfile())
                self.assertEqual(archive.extractfile(executable).read(), b'synthetic bytes')
                self.assertIn('LICENSE.opencode', archive.getnames())
                self.assertIn('upstream.json', archive.getnames())
            checksum = dest.with_name(dest.name + '.sha256').read_text().split()[0]
            self.assertEqual(checksum, hashlib.sha256(first).hexdigest())

    def test_bad_checksum_creates_no_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                repack.repack(tar_blob(), 'linux-x64', {'platforms': {'linux-x64': {'sha256': '0' * 64}}}, folder)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_zip_executable_and_argument_independent_layout(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('bin/opencode', b'synthetic bytes')
        self.assertEqual(repack.binary_from_archive(buffer.getvalue()), b'synthetic bytes')

    def test_rejects_path_traversal_and_symlink_executable(self):
        for blob in (tar_blob('../opencode'), tar_blob('/opencode'), tar_blob(kind=tarfile.SYMTYPE)):
            with self.assertRaises(ValueError):
                repack.binary_from_archive(blob)

    def test_rejects_duplicate_and_missing_executable(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('one/opencode', b'one')
            archive.writestr('two/opencode', b'two')
        for blob in (buffer.getvalue(), tar_blob('other')):
            with self.assertRaisesRegex(ValueError, 'exactly one'):
                repack.binary_from_archive(blob)


if __name__ == '__main__':
    unittest.main()
