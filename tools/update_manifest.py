"""Update only FluffySim from a published release ZIP; no network or publication."""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def update(archive, version):
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.0', version):
        raise ValueError('Expected four-part version with revision zero')
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise ValueError('Corrupt ZIP')
        names = package.namelist()
        if len(names) != len(set(names)) or 'FluffySim.dll' not in names:
            raise ValueError('Missing DLL or duplicate ZIP entries')
        entry = json.loads(package.read('FluffySim.json'))
    if (entry.get('Name'), entry.get('InternalName'), entry.get('AssemblyVersion')) != ('FluffySim', 'FluffySim', version):
        raise ValueError('Release identity/version mismatch')
    if not isinstance(entry.get('DalamudApiLevel'), int) or not entry.get('Author') or not entry.get('Description'):
        raise ValueError('Missing Dalamud metadata')
    url = f'https://github.com/KathyAuteberry/FluffySim/releases/download/v{version}/FluffySim-{version}.zip'
    for field in ('DownloadLinkInstall', 'DownloadLinkUpdate', 'DownloadLinkTesting'):
        entry[field] = url
    entry['IsHide'] = False
    entry['IsTestingExclusive'] = False
    path = ROOT / 'mostly-harmless.json'
    original = path.read_bytes()
    entries = json.loads(original)
    if not isinstance(entries, list) or any(not isinstance(x, dict) or not x.get('InternalName') for x in entries):
        raise ValueError('Expected array of plugin objects')
    ids = [x['InternalName'] for x in entries]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate InternalName')
    if 'FluffySim' in ids:
        index = ids.index('FluffySim')
        previous = entries[index]
        old = previous['AssemblyVersion']
        if tuple(map(int, old.split('.'))) > tuple(map(int, version.split('.'))):
            raise ValueError('Refusing version downgrade')
        if old == version:
            if previous != entry:
                raise ValueError('Same version has different metadata')
            return
        entries[index] = entry
    else:
        entries.append(entry)
    with tempfile.NamedTemporaryFile(mode='w', dir=ROOT, delete=False, encoding='utf-8') as temp:
        json.dump(entries, temp, indent=2)
        temp.write('\n')
        temporary = Path(temp.name)
    try:
        if path.read_bytes() != original:
            raise ValueError('Manifest changed concurrently; retry on latest history')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', required=True, type=Path)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    update(args.zip, args.version)
