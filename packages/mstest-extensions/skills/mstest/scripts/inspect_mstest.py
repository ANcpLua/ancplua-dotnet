"""Resolve a consumer's MSTest API evidence without assuming a release or cache location."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


def relevant(name):
    return name.lower().startswith(("mstest", "microsoft.testing."))


def run_json(command, cwd):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise ValueError(result.stderr or result.stdout)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(f"MSBuild did not return JSON: {result.stdout}") from error


def evaluate(project, properties, framework=None):
    command = ["dotnet", "msbuild", str(project), "-nologo",
               "-getProperty:ProjectAssetsFile,TargetFramework,TargetFrameworks,MSTestVersion,"
               "UsingMSTestSdk,EnableMSTestSourceGeneration,MSTestSourceGenMode,Configuration,"
               "RuntimeIdentifier,RuntimeIdentifiers,UseVSTest,EnableMSTestRunner,"
               "TestingPlatformDotnetTestSupport,TestingExtensionsProfile,PublishAot,PublishTrimmed",
               "-getItem:PackageReference,PackageVersion"]
    command += [f"-p:{value}" for value in properties]
    if framework:
        command.append(f"-p:TargetFramework={framework}")
    return run_json(command, project.parent)


def normalized_range(value):
    value = value.strip()
    if value.startswith(("[", "(")):
        return value.replace(" ", "")
    return f"[{value},)"


def check_requests(evaluation, assets, framework):
    """Compare evaluated direct requests with restore inputs, not just resolved versions."""
    requested = assets.get("project", {}).get("frameworks", {}).get(framework, {}).get("dependencies", {})
    restored = {name.lower(): data for name, data in requested.items()}
    central = {item["Identity"].lower(): item.get("Version", "")
               for item in evaluation["Items"].get("PackageVersion", [])}
    problems = []
    current_names = set()
    for item in evaluation["Items"].get("PackageReference", []):
        name = item["Identity"]
        if not relevant(name):
            continue
        current_names.add(name.lower())
        version = item.get("VersionOverride") or item.get("Version") or central.get(name.lower())
        prior = restored.get(name.lower(), {}).get("version")
        if not version or not prior or normalized_range(version) != normalized_range(prior):
            problems.append(f"{framework}: {name} requests {version!r}; assets record {prior!r}. Restore required.")
    for name in restored:
        if relevant(name) and name not in current_names and not restored[name].get("autoReferenced"):
            problems.append(f"{framework}: {name} remains in assets but is no longer requested. Restore required.")
    return problems


def package_evidence(package_id, version, library, package_folders, target_assets):
    relative = library.get("path", f"{package_id.lower()}/{version}")
    root = next((Path(folder) / relative for folder in package_folders
                 if (Path(folder) / relative).is_dir()), None)
    if root is None:
        raise ValueError(f"Package missing from restored cache: {package_id}/{version}")
    nuspec = root / f"{package_id.lower()}.nuspec"
    repository = None
    if nuspec.exists():
        element = ET.parse(nuspec).find(".//{*}repository")
        repository = element.attrib if element is not None else None
    selected = sorted(set(target_assets.get("compile", {})) | set(target_assets.get("runtime", {})))
    files = []
    for relative_path in selected:
        path = root / relative_path
        if path.suffix != ".dll" or not path.exists():
            continue
        record = {"path": relative_path, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        documentation = path.with_suffix(".xml")
        if documentation.exists():
            record["xml"] = str(documentation)
            record["xml_sha256"] = hashlib.sha256(documentation.read_bytes()).hexdigest()
        files.append(record)
    return {"id": package_id, "version": version, "root": str(root),
            "package_sha512": library.get("sha512"), "repository": repository, "assets": files}


def sdk_evidence(evaluation):
    for item in evaluation["Items"].get("PackageReference", []):
        for parent in Path(item.get("DefiningProjectFullPath", "")).parents:
            if parent.parent.name.lower() == "mstest.sdk":
                return {"version": parent.name, "root": str(parent)}
    return None


def inspect(project, properties=()):
    evaluation = evaluate(project, properties)
    props = evaluation["Properties"]
    frameworks = (props["TargetFramework"] or props["TargetFrameworks"]).split(";")
    contexts, problems = [], []
    for framework in frameworks:
        current = evaluate(project, properties, framework) if len(frameworks) > 1 else evaluation
        assets_path = Path(current["Properties"]["ProjectAssetsFile"])
        if not assets_path.is_absolute():
            assets_path = project.parent / assets_path
        if not assets_path.exists():
            raise ValueError(f"Restore required: {assets_path} is absent")
        assets = json.loads(assets_path.read_text())
        problems.extend(check_requests(current, assets, framework))
        targets = {key: value for key, value in assets["targets"].items()
                   if key.split("/", 1)[0] == framework}
        if not targets:
            raise ValueError(f"Restore required: no assets target for {framework}")
        for target, entries in targets.items():
            packages = []
            for key, data in sorted(entries.items()):
                package_id, version = key.rsplit("/", 1)
                if data.get("type") == "package" and relevant(package_id):
                    packages.append(package_evidence(package_id, version, assets["libraries"][key],
                                                     assets["packageFolders"], data))
            contexts.append({"target": target, "sdk": sdk_evidence(current),
                             "properties": {k: v for k, v in current["Properties"].items()
                                            if k != "ProjectAssetsFile"}, "packages": packages})
    if not any(p["id"].lower() == "mstest.testframework" for c in contexts for p in c["packages"]):
        raise ValueError("No resolved MSTest.TestFramework package found")
    runner = None
    for parent in [project.parent, *project.parent.parents]:
        global_json = parent / "global.json"
        if global_json.exists():
            # SDK global.json accepts comments; leave those to the caller if not strict JSON.
            try:
                runner = json.loads(global_json.read_text()).get("test", {}).get("runner")
            except json.JSONDecodeError:
                problems.append(f"Inspect runner selection manually in {global_json} (non-strict JSON).")
            break
    identity = {"runner": runner, "contexts": []}
    for context in contexts:
        identity["contexts"].append({
            "target": context["target"], "sdk": (context["sdk"] or {}).get("version"),
            "properties": context["properties"],
            "packages": [{k: v for k, v in package.items() if k not in ("root", "assets")}
                         | {"assets": [{k: v for k, v in asset.items() if k != "xml"}
                                       for asset in package["assets"]]}
                         for package in context["packages"]],
        })
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return {"schema": 1, "project": str(project), "runner_selection": runner,
            "api_fingerprint": fingerprint, "contexts": contexts, "problems": problems,
            "limits": "Evaluated requests and resolved assets; XML is documentation, not a complete public API. "
                      "Use --restore to refresh transitive/floating resolution before relying on it."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--property", action="append", default=[], help="MSBuild NAME=VALUE; repeat as needed")
    parser.add_argument("--restore", action="store_true", help="Refresh assets with the project's existing package pins")
    parser.add_argument("--previous", type=Path, help="Previous JSON report for this consumer/configuration")
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    if args.restore:
        result = subprocess.run(["dotnet", "restore", str(project), "--force-evaluate",
                                 *[f"-p:{value}" for value in args.property]],
                                cwd=project.parent, text=True, capture_output=True, timeout=120)
        if result.returncode:
            raise ValueError(result.stderr or result.stdout)
    report = inspect(project, args.property)
    previous = json.loads(args.previous.read_text()) if args.previous else None
    report["requires_api_refresh"] = bool(report["problems"]) or previous is None or bool(previous.get("problems")) or (
        previous.get("api_fingerprint") != report["api_fingerprint"])
    print(json.dumps(report, indent=2))
    return 2 if report["problems"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.TimeoutExpired, ET.ParseError) as error:
        print(f"MSTest inspection failed: {error}", file=sys.stderr)
        sys.exit(2)
