"""Protect identity, deletion and version semantics of cloud delivery."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import cloud_plugins as cloud


class CloudDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {"name": "sample", "version": "1.1.0", "archive": "/tmp/sample.zip", "sha256": "new", "files": {"plugin.json": "x", "skills/sample/SKILL.md": "y"}}
        self.binding = {"plugin_id": "plugins_1234"}
        self.remote = {"plugin_id": "plugins_1234", "name": "sample", "version": "1.0.0", "scope": "USER", "discoverability": "PRIVATE", "current_release_id": "release_1", "inventory_complete": True, "files": ["plugin.json", "skills/sample/SKILL.md", "skills/sample/obsolete.md", ".codex-plugin/plugin.json"]}

    def test_update_retains_identity_guards_release_and_explicitly_removes_retired_files(self):
        result = cloud.plan(self.candidate, self.binding, self.remote)
        self.assertEqual(result["plugin_id"], "plugins_1234")
        self.assertEqual(result["expected_release_id"], "release_1")
        self.assertEqual(result["delete_paths"], ["skills/sample/obsolete.md"])

    def test_missing_or_wrong_remote_never_creates_a_replacement(self):
        for remote in (None, {**self.remote, "plugin_id": "plugins_different"}, {**self.remote, "name": "other"}, {**self.remote, "scope": "WORKSPACE"}, {**self.remote, "discoverability": "LISTED"}):
            with self.subTest(remote=remote), self.assertRaises(ValueError):
                cloud.plan(self.candidate, self.binding, remote)

    def test_same_version_changed_bytes_and_incomplete_inventory_are_rejected(self):
        for remote in ({**self.remote, "version": "1.1.0"}, {**self.remote, "inventory_complete": False}, {**self.remote, "files": ["../escape"]}):
            with self.subTest(remote=remote), self.assertRaises(ValueError):
                cloud.plan(self.candidate, self.binding, remote)

    def test_verified_identical_release_is_not_republished(self):
        result = cloud.plan(self.candidate, self.binding, {**self.remote, "version": "1.1.0"}, {"release_id": "release_1", "sha256": "new"})
        self.assertEqual(result["action"], "unchanged")

    def test_existing_unbound_plugin_requires_binding(self):
        with self.assertRaises(ValueError):
            cloud.plan(self.candidate, {"plugin_id": None}, self.remote)

    def test_archive_is_reproducible_and_excludes_untracked_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", root], check=True)
            folder = root / "packages/sample"
            (folder / "skills/sample").mkdir(parents=True)
            manifest = {"$schema": cloud.SCHEMA, "name": "sample", "version": "1.0.0", "extensions": {"com.openai": {"interface": {"shortDescription": "Sample"}}}}
            cloud.write_json(folder / "plugin.json", manifest)
            (folder / "skills/sample/SKILL.md").write_text("---\nname: sample\ndescription: Test sample.\n---\n")
            cloud.write_json(root / ".agents/plugins/marketplace.json", {"plugins": [{"name": "sample", "source": {"source": "git-subdir", "url": "https://github.com/ANcpLua/ancplua-dotnet.git", "path": "./packages/sample"}}]})
            cloud.write_json(root / "cloud/plugins.json", {"plugins": {"sample": {"plugin_id": None}}})
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"], cwd=root, check=True)
            (folder / "skills/sample/untracked-secret.txt").write_text("do not ship")
            first = cloud.build(root, root / "output")["plugins"]["sample"]
            second = cloud.build(root, root / "output")["plugins"]["sample"]
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(set(first["files"]), {"plugin.json", "skills/sample/SKILL.md"})
            self.assertEqual(first["skills"], ["sample"])


if __name__ == "__main__":
    unittest.main()
