"""Regression checks for complete marketplace validator coverage."""
import json
from pathlib import Path
import tempfile
import unittest
from check_skills import marketplace_scopes, verify_coverage


class CoverageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        catalog = self.root / ".agents/plugins/marketplace.json"
        catalog.parent.mkdir(parents=True)
        entries = []
        for name in ("first", "second"):
            package = self.root / "packages" / name
            skill = package / "skills" / name / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: " + name + "\ndescription: Fixture skill.\n---\n")
            (package / "plugin.json").write_text(json.dumps({"name": name}))
            entries.append({"name": name, "source": {"source": "git-subdir", "path": "./packages/" + name}})
        catalog.write_text(json.dumps({"plugins": entries}))

    def test_all_catalog_packages_are_discovered(self):
        self.assertEqual(["packages/first/skills", "packages/second/skills"], marketplace_scopes(self.root))

    def test_missing_skill_directory_cannot_silently_reduce_coverage(self):
        (self.root / "packages/second/skills/second/SKILL.md").unlink()
        with self.assertRaisesRegex(ValueError, "no discoverable skills"):
            marketplace_scopes(self.root)

    def test_matching_count_does_not_hide_duplicate_or_wrong_skill(self):
        scopes = marketplace_scopes(self.root)
        report = {"counts": {"skillCount": 2}, "skills": [
            {"skillMdPath": "packages/first/skills/first/SKILL.md"},
            {"skillMdPath": "packages/second/skills/second/SKILL.md"}]}
        self.assertEqual(2, verify_coverage(self.root, scopes, report))
        for wrong in ("packages/first/skills/first/SKILL.md", "packages/second/skills/wrong/SKILL.md"):
            with self.subTest(wrong=wrong):
                report["skills"][1]["skillMdPath"] = wrong
                with self.assertRaisesRegex(ValueError, "exactly once"):
                    verify_coverage(self.root, scopes, report)

    def test_source_cannot_escape_repository(self):
        catalog = self.root / ".agents/plugins/marketplace.json"
        data = json.loads(catalog.read_text())
        data["plugins"][0]["source"]["path"] = "../outside"
        catalog.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "escapes repository"):
            marketplace_scopes(self.root)


if __name__ == "__main__":
    unittest.main()
