import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "skills/mstest-extensions/scripts/inspect_mstest.py"
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


if __name__ == "__main__":
    unittest.main()
