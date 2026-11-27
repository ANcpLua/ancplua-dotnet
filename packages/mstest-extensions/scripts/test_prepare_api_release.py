from datetime import date
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from prepare_api_release import prepare


class ApiReleaseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.package = self.root / "packages/mstest-extensions"
        self.docs = self.package / "skills/mstest/references/public-api.md"
        self.docs.parent.mkdir(parents=True)
        self.docs.write_text("original\n")
        self.readme = self.root / "README.md"
        self.readme.write_text("| `mstest-extensions` | MSTest | 4.1.9; two skills |\n")
        self.changelog = self.package / "CHANGELOG.md"
        self.changelog.write_text("# Changelog\n\n## 4.1.9 — 2026-01-01\n\n- First entry.\n")
        self.manifest = self.package / "plugin.json"
        self.manifest.write_text(json.dumps({"version": "4.1.9", "extensions": {
            "com.openai": {"publication": {"release_notes": "Original notes"}}}}))
        self.git("init", "--quiet")
        self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", "-c", "user.name=Test",
                                        "-c", "user.email=test@example.invalid", *args], cwd=self.root, text=True)

    def commit(self):
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "fixture")

    def test_catalog_change_advances_once_and_noop_leaves_git_clean(self):
        prepare(self.package, date(2026, 1, 2))
        self.assertEqual("", self.git("status", "--porcelain"))
        self.docs.write_text("generated\n")
        prepare(self.package, date(2026, 1, 2))
        self.assertEqual("4.1.10", json.loads(self.manifest.read_text())["version"])
        self.assertIn("| 4.1.10;", self.readme.read_text())
        self.assertIn("## 4.1.10 — 2026-01-02", self.changelog.read_text())
        snapshot = self.git("diff")
        prepare(self.package, date(2026, 1, 3))
        self.assertEqual(snapshot, self.git("diff"))
        self.commit()
        prepare(self.package, date(2026, 1, 3))
        self.assertEqual("", self.git("status", "--porcelain"))

    def test_prepared_editorial_release_notes_are_preserved(self):
        self.docs.write_text("generated\n")
        specific = "# Changelog\n\n## 4.1.10 — 2026-01-02\n\n- Precise release note.\n"
        self.changelog.write_text(specific)
        prepare(self.package, date(2026, 1, 3))
        self.assertEqual(specific, self.changelog.read_text())
        self.assertEqual("Original notes", json.loads(self.manifest.read_text())
                         ["extensions"]["com.openai"]["publication"]["release_notes"])


if __name__ == "__main__":
    unittest.main()
