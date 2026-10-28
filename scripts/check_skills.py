"""Run the unmodified dotnet/skills static validator; Python 3.12+ and gh required."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ["packages/mstest-extensions/skills", "packages/nami/plugins/nami/skills"]


def official_validator(output):
    rid = {("Darwin", "arm64"): "osx-arm64", ("Linux", "x86_64"): "linux-x64",
           ("Linux", "aarch64"): "linux-arm64"}.get((platform.system(), platform.machine()))
    if not rid:
        raise SystemExit("Unsupported platform: supply --validator with the official binary")
    release = json.loads(subprocess.check_output([
        "gh", "api", "repos/dotnet/skills/releases/tags/skill-validator-nightly"], text=True))
    asset = next(a for a in release["assets"] if a["name"] == f"skill-validator-{rid}.tar.gz")
    digest = asset.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise SystemExit("Official release has no usable SHA-256 digest")
    sha = digest.split(":", 1)[1]
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ancplua-skill-validator" / sha
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / asset["name"]
    if not archive.exists():
        # Asset identity avoids downloading a different nightly if the tag moves.
        with tempfile.NamedTemporaryFile(dir=cache, delete=False) as download:
            temporary = Path(download.name)
            try:
                subprocess.run(["gh", "api", f"repos/dotnet/skills/releases/assets/{asset['id']}",
                                "-H", "Accept: application/octet-stream"], stdout=download, check=True)
                download.flush()
                with temporary.open("rb") as source:
                    if hashlib.file_digest(source, "sha256").hexdigest() != sha:
                        raise SystemExit("Downloaded validator does not match the official digest")
                temporary.replace(archive)
            finally:
                temporary.unlink(missing_ok=True)
    with archive.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != sha:
            raise SystemExit("Cached validator archive checksum mismatch")
    tool = cache / "tool"
    tool.mkdir(exist_ok=True)
    with tarfile.open(archive) as package:
        package.extractall(tool, filter="data")
    (output / "release.json").write_text(json.dumps({
        "repository": "dotnet/skills", "releaseId": release["id"], "tag": release["tag_name"],
        "publishedAt": release["published_at"], "assetId": asset["id"],
        "assetName": asset["name"], "digest": digest}, indent=2) + "\n")
    return tool / "skill-validator"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validator", type=Path, help="Previously verified official validator binary")
    args = parser.parse_args()
    output = ROOT / "artifacts/skill-validator"
    output.mkdir(parents=True, exist_ok=True)
    validator = args.validator.resolve(strict=True) if args.validator else official_validator(output)
    command = [str(validator), "check", "--skills", *SCOPES, "--json"]
    with (output / "upstream-check.json").open("w") as report:
        result = subprocess.run(command, cwd=ROOT, stdout=report)
    if result.returncode:
        print((output / "upstream-check.json").read_text(), file=sys.stderr)
        raise SystemExit(result.returncode)
    report = json.loads((output / "upstream-check.json").read_text())
    expected = sum(len(list((ROOT / scope).glob("*/SKILL.md"))) for scope in SCOPES)
    if expected == 0 or report["counts"]["skillCount"] != expected:
        raise SystemExit("Validator did not inspect every selected skill")
    errors = sum(len(skill["errors"]) for skill in report["skills"])
    if errors:
        raise SystemExit(f"Validator returned {errors} errors")
    warnings = sum(len(skill["warnings"]) for skill in report["skills"])
    print(f"Unmodified upstream validator: {expected} skills, {errors} errors, {warnings} warnings.")


if __name__ == "__main__":
    main()
