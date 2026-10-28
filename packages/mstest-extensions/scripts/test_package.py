"""Check that portable archives retain executable skill resources after relocation."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]

class PackageTests(unittest.TestCase):
    def test_archive_contains_api_generator_and_assertion_probes(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "plugin.zip"
            subprocess.run([sys.executable, "-B", str(ROOT / "scripts/package_plugin.py"),
                            "--output", str(output)], check=True, capture_output=True, text=True)
            with zipfile.ZipFile(output) as archive:
                for resource in ["mstest/scripts/api_table.md.j2", "mstest/scripts/versions.yaml",
                                 "mstest/scripts/generate_api.py", "mstest/references/public-api.md",
                                 "mstest-assertions/examples/EqualityExamples.cs",
                                 "mstest-assertions/examples/TypedAssertions.cs",
                                 "mstest-assertions/examples/global.json",
                                 "mstest-assertions/scripts/verify_examples.py"]:
                    name = "skills/" + resource
                    with self.subTest(resource=name):
                        self.assertEqual((ROOT / name).read_bytes(), archive.read(name))

if __name__ == "__main__":
    unittest.main()
