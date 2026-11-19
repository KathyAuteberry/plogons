"""Update one plugin's entry in mostly-harmless.json; no network or publication.

`release` records a published release ZIP (version, API level, download links).
`metadata` refreshes the presentation fields and the changelog from a checkout of the
plugin's source master, without changing the published version.
"""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]

# Allow-list: only these plugins can be published, each only from its own repository: releases
# host "<InternalName>-<version>.zip"; `metadata` and `changelog` are paths in its source tree.
PLUGINS = {
    'FluffySim': {
        'repo': 'KathyAuteberry/FluffySim',
        'metadata': 'AnoMech/FluffySim.json',
        'changelog': 'docs/releases/CHANGELOG.md',
    },
    'Kotodama': {
        'repo': 'KathyAuteberry/Kotodama',
        'metadata': 'Kotodama/Kotodama.json',
        'changelog': 'CHANGELOG.md',
    },
}

# Fields owned by the source repository's master. Everything else in an entry comes from the
# release ZIP and is tied to the binary, so `metadata` never touches it.
SOURCE_FIELDS = {
    'Author': str,
    'Punchline': str,
    'Description': str,
    'Tags': list,
    'CategoryTags': list,
    'RepoUrl': str,
    'IconUrl': str,
    'ImageUrls': list,
    'AcceptsFeedback': bool,
    'FeedbackMessage': str,
    'ApplicableVersion': str,
}
GENERATED_FIELDS = {'Changelog'}
URL_FIELDS = ('RepoUrl', 'IconUrl', 'ImageUrls')
# Sections that matter to contributors, not to someone deciding whether to update.
SKIPPED_SECTIONS = {'internal'}
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.0')


def _plugin(plugin):
    if plugin not in PLUGINS:
        raise ValueError('Unknown plugin; add it to PLUGINS first')
    return PLUGINS[plugin]


def _load():
    path = ROOT / 'mostly-harmless.json'
    original = path.read_bytes()
    entries = json.loads(original)
    if not isinstance(entries, list) or any(not isinstance(x, dict) or not x.get('InternalName') for x in entries):
        raise ValueError('Expected array of plugin objects')
    ids = [x['InternalName'] for x in entries]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate InternalName')
    return path, original, entries, ids


def _save(path, original, entries):
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


def _binary_fields(entry):
    return {k: v for k, v in entry.items() if k not in SOURCE_FIELDS and k not in GENERATED_FIELDS}


def release(archive, version, plugin):
    repo = _plugin(plugin)['repo']
    if not VERSION.fullmatch(version):
        raise ValueError('Expected four-part version with revision zero')
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise ValueError('Corrupt ZIP')
        names = package.namelist()
        if len(names) != len(set(names)) or f'{plugin}.dll' not in names:
            raise ValueError('Missing DLL or duplicate ZIP entries')
        entry = json.loads(package.read(f'{plugin}.json'))
    if (entry.get('Name'), entry.get('InternalName'), entry.get('AssemblyVersion')) != (plugin, plugin, version):
        raise ValueError('Release identity/version mismatch')
    if not isinstance(entry.get('DalamudApiLevel'), int) or not entry.get('Author') or not entry.get('Description'):
        raise ValueError('Missing Dalamud metadata')
    for field in GENERATED_FIELDS:
        entry.pop(field, None)
    url = f'https://github.com/{repo}/releases/download/v{version}/{plugin}-{version}.zip'
    for field in ('DownloadLinkInstall', 'DownloadLinkUpdate', 'DownloadLinkTesting'):
        entry[field] = url
    entry['IsHide'] = False
    entry['IsTestingExclusive'] = False
    path, original, entries, ids = _load()
    if plugin in ids:
        index = ids.index(plugin)
        previous = entries[index]
        old = previous['AssemblyVersion']
        if tuple(map(int, old.split('.'))) > tuple(map(int, version.split('.'))):
            raise ValueError('Refusing version downgrade')
        if old == version:
            # A rerun of the same release keeps whatever `metadata` has synced since.
            if _binary_fields(previous) != _binary_fields(entry):
                raise ValueError('Same version has different release metadata')
            return
        entries[index] = entry
    else:
        entries.append(entry)
    _save(path, original, entries)


def _plain(text):
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text.replace('**', '').replace('`', '').strip()


def _first_sentence(text):
    return re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip(), maxsplit=1)[0]


def _summarise(item):
    lead = re.match(r'\*\*(.+?)\*\*\s*(.*)', item, re.S)
    if lead:
        title, rest = lead.group(1).strip(), lead.group(2).strip()
        title = title.rstrip('.:')
        return f'{_plain(title)}: {_plain(_first_sentence(rest))}' if rest else _plain(title)
    return _plain(_first_sentence(item))


def short_changelog(changelog, name, version):
    """Plain-text summary of one CHANGELOG.md entry: one line per bullet, grouped by section."""
    if not VERSION.fullmatch(version):
        raise ValueError('Expected four-part version with revision zero')
    sections = re.split(rf'(?m)^# {re.escape(name)} ', changelog)
    matches = [s for s in sections[1:] if s.splitlines()[0].split()[0] == version]
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one changelog entry for {name} {version}')
    lines, heading, items, paragraph = [], None, [], []

    def flush_paragraph():
        if paragraph:
            items.append(('text', ' '.join(paragraph)))
            paragraph.clear()

    def flush_section():
        flush_paragraph()
        if items and (heading or '').lower() not in SKIPPED_SECTIONS:
            if heading:
                if lines:
                    lines.append('')
                lines.append(heading)
            for kind, text in items:
                lines.append(('- ' if kind == 'bullet' else '') + _summarise(text))
        items.clear()

    for raw in matches[0].splitlines()[1:]:
        line = raw.rstrip()
        if line.startswith('## '):
            flush_section()
            heading = _plain(line[3:])
        elif line.startswith('- '):
            flush_paragraph()
            items.append(('bullet', line[2:]))
        elif not line.strip():
            flush_paragraph()
        elif raw.startswith((' ', '\t')) and items and items[-1][0] == 'bullet' and not paragraph:
            items[-1] = ('bullet', items[-1][1] + ' ' + line.strip())
        else:
            paragraph.append(line.strip())
    flush_section()
    if not lines:
        raise ValueError('Changelog entry is empty')
    return '\n'.join(lines)


def _check_source(plugin, repo, source):
    if not isinstance(source, dict):
        raise ValueError('Source metadata must be a JSON object')
    for field in ('Name', 'InternalName'):
        if field in source and source[field] != plugin:
            raise ValueError('Source metadata identity mismatch')
    for field, kind in SOURCE_FIELDS.items():
        if field in source and not isinstance(source[field], kind):
            raise ValueError(f'{field} must be {kind.__name__}')
    for field in ('Tags', 'CategoryTags', 'ImageUrls'):
        if any(not isinstance(x, str) or not x for x in source.get(field, [])):
            raise ValueError(f'{field} must contain non-empty strings')
    for field in ('Author', 'Description'):
        if not source.get(field, '').strip():
            raise ValueError(f'Source metadata needs {field}')
    allowed = (f'https://github.com/{repo}', f'https://raw.githubusercontent.com/{repo}/')
    for field in URL_FIELDS:
        values = source.get(field, [])
        for value in [values] if isinstance(values, str) else values:
            if not (value == allowed[0] or value.startswith(allowed[0] + '/') or value.startswith(allowed[1])):
                raise ValueError(f'{field} must point into {repo}')


def metadata(source_root, plugin):
    config = _plugin(plugin)
    source_root = Path(source_root)
    source = json.loads((source_root / config['metadata']).read_text(encoding='utf-8'))
    _check_source(plugin, config['repo'], source)
    path, original, entries, ids = _load()
    if plugin not in ids:
        raise ValueError('No published release to attach metadata to; publish a release first')
    index = ids.index(plugin)
    entry = dict(entries[index])
    for field in SOURCE_FIELDS:
        if field in source:
            entry[field] = source[field]
    changelog = (source_root / config['changelog']).read_text(encoding='utf-8')
    entry['Changelog'] = short_changelog(changelog, plugin, entry['AssemblyVersion'])
    if entry == entries[index]:
        return
    entries[index] = entry
    _save(path, original, entries)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_subparsers(dest='mode', required=True)
    rel = modes.add_parser('release', help='record a published release ZIP')
    rel.add_argument('--zip', required=True, type=Path)
    rel.add_argument('--version', required=True)
    rel.add_argument('--plugin', required=True, choices=sorted(PLUGINS))
    meta = modes.add_parser('metadata', help='sync metadata and changelog from a source checkout')
    meta.add_argument('--source', required=True, type=Path, help='checkout of the plugin repository')
    meta.add_argument('--plugin', required=True, choices=sorted(PLUGINS))
    meta.add_argument('--print-changelog', action='store_true', help='print the generated changelog')
    args = parser.parse_args(argv)
    if args.mode == 'release':
        release(args.zip, args.version, args.plugin)
    else:
        metadata(args.source, args.plugin)
        if args.print_changelog:
            entry = next(x for x in json.loads((ROOT / 'mostly-harmless.json').read_text()) if x['InternalName'] == args.plugin)
            print(entry['Changelog'])


if __name__ == '__main__':
    main()
