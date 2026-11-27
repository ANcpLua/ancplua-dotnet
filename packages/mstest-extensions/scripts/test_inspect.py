import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

path = Path(__file__).resolve().parents[1] / "skills/mstest/scripts/inspect_mstest.py"
spec = importlib.util.spec_from_file_location("inspect_mstest", path)
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


class RestoreFreshnessTests(unittest.TestCase):
    def evaluation(self, version="4.5.1", central=False):
        item = {"Identity": "MSTest.TestFramework"}
        if not central:
            item["Version"] = version
        return {"Items": {"PackageReference": [item], "PackageVersion":
                         [{"Identity": "MSTest.TestFramework", "Version": version}] if central else []}}

    def assets(self, version="[4.5.1, )"):
        return {"project": {"frameworks": {"net10.0": {"dependencies": {
            "MSTest.TestFramework": {"version": version}}}}}}

    def test_changed_pin_requires_restore_even_when_assets_exist(self):
        self.assertTrue(inspector.check_requests(self.evaluation(), self.assets("[4.4.1, )"), "net10.0"))

    def test_equivalent_restore_request_remains_valid(self):
        self.assertEqual([], inspector.check_requests(self.evaluation(), self.assets(), "net10.0"))

    def test_central_version_is_checked(self):
        self.assertTrue(inspector.check_requests(self.evaluation(central=True), self.assets("[4.4.1, )"), "net10.0"))

    def test_other_framework_does_not_substitute_for_missing_target(self):
        self.assertTrue(inspector.check_requests(self.evaluation(), self.assets(), "net9.0"))

    def test_removed_reference_requires_restore(self):
        self.assertTrue(inspector.check_requests({"Items": {"PackageReference": []}}, self.assets(), "net10.0"))

    def test_version_override_takes_precedence(self):
        evaluated = self.evaluation("4.4.1")
        evaluated["Items"]["PackageReference"][0]["VersionOverride"] = "4.5.1"
        self.assertEqual([], inspector.check_requests(evaluated, self.assets(), "net10.0"))


class RuntimeIdentifierTests(unittest.TestCase):
    targets = {"net11.0": {}, "net11.0/osx-arm64": {"native": "mac"},
               "net10.0/linux-x64": {"native": "linux"}}

    def test_runtime_identifier_selects_only_its_restored_graph(self):
        self.assertEqual({"net11.0/osx-arm64": {"native": "mac"}},
                         inspector.restored_targets(self.targets, "net11.0", "osx-arm64"))

    def test_missing_runtime_graph_requires_a_restore_for_that_runtime(self):
        with self.assertRaisesRegex(ValueError, "Restore required: no assets target for net11[.]0/linux-x64"):
            inspector.restored_targets(self.targets, "net11.0", "linux-x64")

    def test_unspecified_runtime_enumerates_the_frameworks_restored_graphs(self):
        self.assertEqual({"net11.0": {}, "net11.0/osx-arm64": {"native": "mac"}},
                         inspector.restored_targets(self.targets, "net11.0", ""))


class PackageEvidenceTests(unittest.TestCase):
    def test_missing_selected_dll_identifies_package_version_and_asset(self):
        with TemporaryDirectory() as cache:
            (Path(cache) / "mstest.testframework/4.5.3").mkdir(parents=True)
            for group in ("compile", "runtime"):
                with self.subTest(group=group), self.assertRaisesRegex(
                        ValueError, r"MSTest\.TestFramework/4\.5\.3/lib/net9\.0/MSTest\.TestFramework\.dll"):
                    inspector.package_evidence("MSTest.TestFramework", "4.5.3", {}, [cache],
                                               {group: {"lib/net9.0/MSTest.TestFramework.dll": {}}})

    def test_selected_dll_without_xml_is_usable_and_placeholder_is_ignored(self):
        with TemporaryDirectory() as cache:
            folder = Path(cache) / "mstest.testframework/4.5.3/lib/net9.0"
            folder.mkdir(parents=True)
            (folder / "Framework.DLL").write_bytes(b"fixture")
            evidence = inspector.package_evidence("MSTest.TestFramework", "4.5.3", {}, [cache],
                                                  {"compile": {"lib/net9.0/Framework.DLL": {}},
                                                   "runtime": {"lib/net9.0/_._": {}}})
            self.assertEqual(["lib/net9.0/Framework.DLL"], [a["path"] for a in evidence["assets"]])
            self.assertNotIn("xml", evidence["assets"][0])


if __name__ == "__main__":
    unittest.main()
