import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate import ROOT, validate


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / 'plugins', self.root / 'plugins')

    def tearDown(self):
        self.temporary.cleanup()

    def test_package_has_three_self_contained_skills(self):
        self.assertEqual([], validate(self.root))

    def test_missing_fixture_example_is_rejected(self):
        (self.root / 'plugins/nami/skills/fixture-scope/examples/FixtureLifecycleTests.cs').unlink()
        self.assertTrue(any('missing destination' in error for error in validate(self.root)))

    def test_unexpected_fourth_skill_is_rejected(self):
        extra = self.root / 'plugins/nami/skills/extra'
        extra.mkdir()
        (extra / 'SKILL.md').write_text('---\nname: extra\ndescription: Unexpected skill\n---\n')
        self.assertTrue(any('Expected exactly three skills' in error for error in validate(self.root)))

    def test_missing_skill_is_rejected(self):
        (self.root / 'plugins/nami/skills/fixture-scope/SKILL.md').unlink()
        with self.assertRaises(FileNotFoundError):
            validate(self.root)

    def test_legacy_provider_tree_is_rejected(self):
        (self.root / '.codex').mkdir()
        self.assertIn('Unexpected compatibility tree: .codex', validate(self.root))

    def test_independent_union_changes_are_detected(self):
        path = self.root / 'plugins/nami/skills/csharp-union-types/SKILL.md'
        path.write_text(path.read_text() + '\nIndependent change\n')
        self.assertTrue(any('Union export differs' in error for error in validate(self.root)))

    def test_extra_union_file_is_detected(self):
        (self.root / 'plugins/nami/skills/csharp-union-types/extra.md').write_text('not exported')
        self.assertIn('Union export inventory differs from its source receipt', validate(self.root))

    def test_broken_local_reference_is_detected(self):
        path = self.root / 'plugins/nami/skills/fixture-scope/SKILL.md'
        path.write_text(path.read_text() + '\n[bad](references/missing.md)\n')
        self.assertTrue(any('missing destination' in error for error in validate(self.root)))

    def test_standalone_marketplace_is_rejected(self):
        path = self.root / '.agents/plugins/marketplace.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'name': 'nami', 'plugins': []}))
        self.assertIn('Use the central ancplua-dotnet marketplace; no standalone catalog', validate(self.root))

    def test_plugin_identity_is_checked(self):
        path = self.root / 'plugins/nami/plugin.json'
        value = json.loads(path.read_text())
        value['name'] = 'different-plugin'
        path.write_text(json.dumps(value))
        self.assertIn('Plugin must be named nami', validate(self.root))


if __name__ == '__main__':
    unittest.main()
