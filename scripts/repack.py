#!/usr/bin/env python3
"""Verify an official archive and repack it for Pointman's release installer."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def binary_from_archive(data):
    entries = []
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in archive.infolist():
                path = PurePosixPath(member.filename)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('unsafe upstream archive path')
                if path.name == 'opencode' and not member.is_dir():
                    mode = member.external_attr >> 16
                    if mode & 0o170000 == 0o120000:
                        raise ValueError('upstream executable cannot be a symlink')
                    entries.append(archive.read(member))
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
            for member in archive.getmembers():
                path = PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('unsafe upstream archive path')
                if path.name == 'opencode':
                    if not member.isfile():
                        raise ValueError('upstream executable must be a regular file')
                    entries.append(archive.extractfile(member).read())
    if len(entries) != 1 or not entries[0]:
        raise ValueError('expected exactly one nonempty opencode executable')
    return entries[0]


def repack(data, target, pin, output):
    expected = pin['platforms'][target]['sha256']
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('official archive checksum mismatch')
    executable = binary_from_archive(data)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    name = f'opencode-{target}'
    dest = output / f'{name}.tar.gz'
    # Exact root filename is required by node/src/clients.rs release().
    members = [(name, executable, 0o755),
               ('LICENSE.opencode', (ROOT / 'LICENSE.opencode').read_bytes(), 0o644),
               ('upstream.json', (json.dumps(pin, indent=2) + '\n').encode(), 0o644)]
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', filename='', mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for filename, content, mode in members:
                item = tarfile.TarInfo(filename)
                item.size, item.mode, item.mtime = len(content), mode, 0
                archive.addfile(item, io.BytesIO(content))
    dest.write_bytes(buffer.getvalue())
    checksum = hashlib.sha256(dest.read_bytes()).hexdigest()
    dest.with_name(dest.name + '.sha256').write_text(f'{checksum}  {dest.name}\n')
    return dest


def main():
    pin = json.loads((ROOT / 'upstream.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=pin['platforms'], required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--archive', type=Path)
    source.add_argument('--download', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('release'))
    args = parser.parse_args()
    if args.download:
        with urllib.request.urlopen(pin['platforms'][args.target]['url'], timeout=120) as response:
            data = response.read()
    else:
        data = args.archive.read_bytes()
    print(repack(data, args.target, pin, args.output))


if __name__ == '__main__':
    main()
