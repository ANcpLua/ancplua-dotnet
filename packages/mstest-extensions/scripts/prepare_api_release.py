"""Prepare a patch release when CI regenerates the tracked MSTest API catalog."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess


def prepare(package, today):
    catalog = "skills/mstest/references/public-api.md"
    diff = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", catalog], cwd=package)
    if diff.returncode == 0:
        return
    if diff.returncode != 1:
        diff.check_returncode()

    manifest_path = package / "plugin.json"
    manifest = json.loads(manifest_path.read_text())
    committed = subprocess.check_output(
        ["git", "show", "HEAD:packages/mstest-extensions/plugin.json"], cwd=package, text=True)
    old = json.loads(committed)["version"]
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", old):
        raise ValueError(f"Expected a stable three-part version, found {old}")
    major, minor, patch = old.split(".")
    new = f"{major}.{minor}.{int(patch) + 1}"
    if manifest["version"] not in (old, new):
        raise ValueError("Unexpected uncommitted plugin version")

    readme = package.parents[1] / "README.md"
    catalog_row = r"^(\| `mstest-extensions` \| [^|]+ \| )(\d+\.\d+\.\d+)(?=;)"
    text = readme.read_text()
    rows = re.findall(catalog_row, text, re.MULTILINE)
    if len(rows) != 1 or rows[0][1] not in (old, new):
        raise ValueError("Missing or inconsistent MSTest version in the marketplace table")

    changelog = package / "CHANGELOG.md"
    changes = changelog.read_text()
    if not re.search(rf"^## {re.escape(new)}(?: |$)", changes, re.MULTILINE):
        title = "# Changelog\n"
        if not changes.startswith(title):
            raise ValueError("Unexpected MSTest changelog layout")
        note = "Refresh the generated MSTest public API reference."
        changes = title + f"\n## {new} — {today.isoformat()}\n\n- {note}\n" + changes[len(title):]
        manifest["extensions"]["com.openai"]["publication"]["release_notes"] = note
    manifest["version"] = new
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    readme.write_text(re.sub(catalog_row, lambda m: m[1] + new, text, flags=re.MULTILINE))
    changelog.write_text(changes)
    print(f"Prepared MSTest Extensions {new} for the regenerated catalog")


if __name__ == "__main__":
    prepare(Path(__file__).resolve().parents[1], datetime.now(timezone.utc).date())
