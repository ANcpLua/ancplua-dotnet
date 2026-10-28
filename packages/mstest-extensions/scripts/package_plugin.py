"""Package every plugin skill and its fixtures, excluding local outputs."""
import argparse
import json
from pathlib import Path
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="ZIP path outside the plugin directory")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "plugin.json").read_text())
    if manifest["$schema"] != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise SystemExit("Unrecognized portable manifest schema")
    interface = manifest["extensions"]["com.openai"]["interface"]
    if len(interface["shortDescription"]) > 30:
        raise SystemExit("Plugin subtitle exceeds 30 characters")
    skills_root = root / "skills"
    skills = sorted(path.parent for path in skills_root.glob("*/SKILL.md"))
    if {skill.name for skill in skills} != {"mstest", "mstest-assertions"}:
        raise SystemExit("Expected exactly the mstest and mstest-assertions skills")
    output = args.output.resolve()
    if output.is_relative_to(root):
        raise SystemExit("Write the archive outside the plugin directory")
    files = [root / "plugin.json"]
    for document in ("LICENSE", "PRIVACY.md", "TERMS.md"):
        if (root / document).is_file():
            files.append(root / document)
    for asset in sorted((root / "assets").rglob("*")):
        if asset.is_symlink():
            raise SystemExit(f"Symlinks cannot be packaged: {asset}")
        if asset.is_file():
            files.append(asset)
    for path in sorted(skills_root.rglob("*")):
        if path.is_symlink():
            raise SystemExit(f"Symlinks cannot be packaged: {path}")
        if path.is_file() and not {"__pycache__", "bin", "obj", "artifacts"}.intersection(path.parts) and path.suffix in {".md", ".yaml", ".py", ".cs", ".csproj", ".props", ".json", ".j2"}:
            files.append(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(root))
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise SystemExit("Archive integrity check failed")
        for path in files:
            if archive.read(path.relative_to(root).as_posix()) != path.read_bytes():
                raise SystemExit(f"Archive content mismatch: {path}")
    print(f"Packaged {len(skills)} skills, {len(files)} files: {output}")


if __name__ == "__main__":
    main()
