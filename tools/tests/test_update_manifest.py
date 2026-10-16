import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('updater', Path(__file__).resolve().parents[1] / 'update_manifest.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        old = module.ROOT
        module.ROOT = Path(self.temp.name)
        self.addCleanup(setattr, module, 'ROOT', old)
        self.path = module.ROOT / 'mostly-harmless.json'
        self.other = {'InternalName': 'Other', 'AssemblyVersion': '9.0.0.0', 'Extra': [1, 2]}
        self.path.write_text(json.dumps([self.other]))

    def archive(self, version='2.0.0.0', **overrides):
        entry = dict(Name='FluffySim', InternalName='FluffySim', AssemblyVersion=version,
                     Author='Contributors', Description='Practice', DalamudApiLevel=15)
        entry.update(overrides)
        path = module.ROOT / 'release.zip'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('FluffySim.dll', b'example')
            z.writestr('FluffySim.json', json.dumps(entry))
        return path

    def test_preservation_urls_and_idempotence(self):
        archive = self.archive()
        module.update(archive, '2.0.0.0')
        original = self.path.read_bytes()
        entries = json.loads(original)
        self.assertEqual(entries[0], self.other)
        self.assertEqual(entries[1]['DownloadLinkInstall'], 'https://github.com/KathyAuteberry/FluffySim/releases/download/v2.0.0.0/FluffySim-2.0.0.0.zip')
        module.update(archive, '2.0.0.0')
        self.assertEqual(self.path.read_bytes(), original)

    def test_downgrade_and_equal_version_replacement_leave_original(self):
        module.update(self.archive(), '2.0.0.0')
        original = self.path.read_bytes()
        for version, overrides in [('1.0.0.0', {}), ('2.0.0.0', {'Description': 'Changed'})]:
            archive = self.archive(version, **overrides)
            with self.assertRaises(ValueError):
                module.update(archive, version)
            self.assertEqual(self.path.read_bytes(), original)

    def test_identity_version_and_schema_rejected(self):
        for overrides in [dict(InternalName='AnoMech'), dict(AssemblyVersion='9.0.0.0'), dict(DalamudApiLevel=None)]:
            original = self.path.read_bytes()
            with self.assertRaises(ValueError):
                module.update(self.archive(**overrides), '2.0.0.0')
            self.assertEqual(self.path.read_bytes(), original)

    def test_duplicate_entries_rejected(self):
        self.path.write_text(json.dumps([self.other, self.other]))
        with self.assertRaises(ValueError):
            module.update(self.archive(), '2.0.0.0')


if __name__ == '__main__':
    unittest.main()
