import tempfile
import unittest
from pathlib import Path
from install import install


class InstallTests(unittest.TestCase):
    def test_second_install_keeps_all_links_and_sources_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [root / "source" / name for name in ("first", "second")]
            for source in sources:
                source.mkdir(parents=True)
                (source / "SKILL.md").write_text(source.name)
            roots = [root / "agents", root / "claude"]
            destinations = [directory / source.name for directory in roots for source in sources]
            install(sources, roots)
            before = [destination.lstat().st_mtime_ns for destination in destinations]
            install(sources, roots)
            self.assertEqual(before, [destination.lstat().st_mtime_ns for destination in destinations])
            for directory in roots:
                for source in sources:
                    self.assertEqual(source.resolve(), (directory / source.name).resolve())
            for source in sources:
                self.assertEqual(source.name, (source / "SKILL.md").read_text())

    def test_conflict_is_detected_before_creating_any_link(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = [root / "source" / name for name in ("first", "second")]
            for source in sources:
                source.mkdir(parents=True)
            roots = [root / "agents", root / "claude"]
            occupied = roots[-1] / sources[-1].name
            occupied.mkdir(parents=True)
            (occupied / "user.txt").write_text("keep")
            with self.assertRaises(FileExistsError):
                install(sources, roots)
            self.assertFalse(roots[0].exists())
            self.assertFalse((roots[1] / sources[0].name).exists())
            self.assertEqual("keep", (occupied / "user.txt").read_text())


if __name__ == "__main__":
    unittest.main()
