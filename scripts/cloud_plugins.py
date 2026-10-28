"""Build account plugin archives from Git sources and plan guarded cloud updates.

This command never authenticates, creates, uploads, installs or deletes a plugin.
Plugin Creator performs those actions using the identities recorded in cloud/plugins.json.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
COMPONENTS = {"skills", "assets", ".codex-plugin"}
DOCUMENTS = {"plugin.json", "LICENSE", "LICENSE.md", "LICENSE.txt", "PRIVACY.md", "TERMS.md"}
OUTPUT_PARTS = {"node_modules", "__pycache__", "bin", "obj", ".venv", "artifacts", "TestResults"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def packages(root):
    root = root.resolve()
    catalog = read_json(root / ".agents/plugins/marketplace.json")
    result = {}
    for entry in catalog["plugins"]:
        source = entry["source"]
        if source["source"] != "git-subdir" or source["url"] != "https://github.com/ANcpLua/ancplua-dotnet.git":
            raise ValueError("Cloud packages must come from this repository")
        folder = root / source["path"]
        if not folder.resolve().is_relative_to(root.resolve()) or folder.resolve() != folder.absolute():
            raise ValueError(f"Escaping or symlinked package: {folder}")
        manifest = read_json(folder / "plugin.json")
        if manifest.get("$schema") != SCHEMA or manifest["name"] != entry["name"]:
            raise ValueError(f"Invalid package identity: {folder}")
        if entry["name"] in result:
            raise ValueError(f"Duplicate package: {entry['name']}")
        result[entry["name"]] = (folder, manifest)
    return result


def targets(root, names):
    data = read_json(root / "cloud/plugins.json")
    if set(data["plugins"]) != set(names):
        raise ValueError("Cloud identities must cover the entire marketplace")
    ids = [p["plugin_id"] for p in data["plugins"].values() if p["plugin_id"] is not None]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"plugins?_[A-Za-z0-9]+", i) for i in ids):
        raise ValueError("Invalid or duplicated cloud identity")
    return data["plugins"]


def payload(root, folder, manifest):
    tracked = subprocess.check_output(["git", "ls-files", "-z", "--", str(folder)], cwd=root).decode().split("\0")
    files = {}
    for relative in filter(None, tracked):
        path = root / relative
        inner = path.relative_to(folder)
        if inner.parts[0] not in COMPONENTS and inner.as_posix() not in DOCUMENTS:
            continue
        if OUTPUT_PARTS.intersection(inner.parts):
            raise ValueError(f"Generated output tracked inside plugin components: {path}")
        if path.is_symlink() or path.resolve() != path.absolute():
            raise ValueError(f"Symlink cannot be packaged: {path}")
        files[inner.as_posix()] = path.read_bytes()
    if "plugin.json" not in files or not any(re.fullmatch(r"skills/[^/]+/SKILL.md", p) for p in files):
        raise ValueError(f"Incomplete plugin: {folder}")
    interface = manifest["extensions"]["com.openai"]["interface"]
    if len(interface["shortDescription"]) > 30:
        raise ValueError("Plugin subtitle exceeds 30 characters")
    for key in ("logo", "logoDark", "composerIcon", "composerIconDark"):
        if key in interface and interface[key].removeprefix("./") not in files:
            raise ValueError(f"Missing packaged {key}: {interface[key]}")
    compatibility = files.get(".codex-plugin/plugin.json")
    if compatibility:
        old = json.loads(compatibility)
        if any(old.get(k) != manifest.get(k) for k in ("name", "version")) or old.get("interface") != interface:
            raise ValueError("Compatibility manifest differs from canonical identity or presentation")
    return files


def build(root, output):
    root = root.resolve()
    sources = packages(root)
    bindings = targets(root, sources)
    output = output.resolve()
    if any(output.is_relative_to(folder.resolve()) for folder, _ in sources.values()):
        raise ValueError("Build output must be outside every plugin directory")
    output.mkdir(parents=True, exist_ok=True)
    result = {
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "source_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root)),
        "plugins": {},
    }
    for name, (folder, manifest) in sources.items():
        files = payload(root, folder, manifest)
        archive = output / f"{name}-{manifest['version']}.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for path, content in sorted(files.items()):
                info = zipfile.ZipInfo(f"{name}/{path}", date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = ((0o100755 if (folder / path).stat().st_mode & 0o111 else 0o100644) << 16)
                z.writestr(info, content)
        with zipfile.ZipFile(archive) as z:
            if z.testzip() or any(z.read(f"{name}/{p}") != b for p, b in files.items()):
                raise ValueError(f"Archive verification failed: {archive}")
        result["plugins"][name] = {
            "name": name, "version": manifest["version"], "plugin_id": bindings[name]["plugin_id"],
            "archive": str(archive), "sha256": sha256(archive.read_bytes()),
            "skills": sorted(p.split('/')[1] for p in files if re.fullmatch(r"skills/[^/]+/SKILL.md", p)),
            "files": {p: sha256(b) for p, b in sorted(files.items())},
        }
        print(f"{name} {manifest['version']}: {len(result['plugins'][name]['skills'])} skills, {len(files)} files")
    write_json(output / "packages.json", result)
    return result


def version(value):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
        raise ValueError(f"Expected a stable three-part package version: {value}")
    return tuple(map(int, value.split('.')))


def plan(candidate, binding, remote, receipt=None):
    """remote is metadata plus the COMPLETE file list from Plugin Creator."""
    if binding["plugin_id"] is None:
        if remote is not None:
            raise ValueError("Discover and bind the existing plugin instead of creating a duplicate")
        return {"action": "create", "archive": candidate["archive"]}
    if remote is None:
        raise ValueError("Bound plugin is missing: never recreate a fixed identity automatically")
    if remote["plugin_id"] != binding["plugin_id"] or remote["name"] != candidate["name"]:
        raise ValueError("Remote plugin identity does not match this source")
    if remote["scope"] != "USER" or remote["discoverability"] != "PRIVATE":
        raise ValueError("Expected the existing private personal plugin")
    if receipt and remote["current_release_id"] == receipt["release_id"] and candidate["sha256"] == receipt["sha256"] and candidate["version"] == remote["version"]:
        return {"action": "unchanged", "plugin_id": binding["plugin_id"]}
    if version(candidate["version"]) <= version(remote["version"]):
        raise ValueError("Bump the source version before uploading changed content; avoid server-only version bumps")
    if not remote.get("inventory_complete"):
        raise ValueError("Read every get_plugin_files page before planning an update")
    removals = []
    for path in remote["files"]:
        parsed = PurePosixPath(path)
        if parsed.is_absolute() or ".." in parsed.parts:
            raise ValueError(f"Unsafe remote path: {path}")
        if path not in candidate["files"] and path not in {".codex-plugin/plugin.json", ".mcp.json"}:
            removals.append(path)
    return {"action": "update", "plugin_id": binding["plugin_id"], "archive": candidate["archive"],
            "expected_release_id": remote["current_release_id"], "delete_paths": sorted(removals)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "plan"])
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/cloud-plugins")
    parser.add_argument("--remote-state", type=Path, help="Verified metadata and complete file inventories from Plugin Creator")
    args = parser.parse_args()
    built = build(ROOT, args.output)
    if args.command == "plan":
        if not args.remote_state:
            parser.error("plan requires --remote-state; do not infer account state from names")
        state = read_json(args.remote_state)
        bindings = targets(ROOT, built["plugins"])
        receipts = read_json(ROOT / "cloud/releases.json")["receipts"]
        plans = {name: plan(p, bindings[name], state.get("plugins", {}).get(name), receipts.get(name))
                 for name, p in built["plugins"].items()}
        write_json(args.output / "plan.json", plans)
        print(json.dumps(plans, indent=2))


if __name__ == "__main__":
    main()
