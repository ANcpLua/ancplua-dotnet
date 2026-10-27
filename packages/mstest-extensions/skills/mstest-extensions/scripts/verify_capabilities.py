"""Verify runner policies and published consumers in an isolated, version-pinned workspace."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import tempfile
import xml.etree.ElementTree as ET

TRX = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def command(arguments, workspace, evidence, environment, expected=0, timeout=240):
    evidence.parent.mkdir(parents=True, exist_ok=True)
    with evidence.open("w") as log:
        child = subprocess.Popen(arguments, cwd=workspace, env=environment, text=True,
                                 stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=os.name != "nt")
        try:
            code = child.wait(timeout=timeout)
        except BaseException:
            if child.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], check=False,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if os.name != "nt": os.killpg(child.pid, signal.SIGKILL)
                    else: child.kill()
                    child.wait()
            raise
    output = evidence.read_text()
    require(code == expected, f"Expected exit {expected}, got {code}: {arguments}\n{output}\nEvidence: {evidence}")
    return output


def api_evidence(project, properties, workspace, evidence, environment, sdk_version, extra_packages=None):
    skill = Path(__file__).resolve().parents[1]
    arguments = ["python3", str(skill / "scripts/inspect_mstest.py"), "--project", str(project)]
    for name, value in properties.items(): arguments += ["--property", f"{name}={value}"]
    report = json.loads(command(arguments, workspace, evidence, environment))
    for context in report["contexts"]:
        require(context["sdk"]["version"] == sdk_version, "The requested MSTest SDK did not resolve.")
        packages = {package["id"]: package["version"] for package in context["packages"]}
        for name, version in {"MSTest.TestFramework": sdk_version, "MSTest.TestAdapter": sdk_version,
                              **(extra_packages or {})}.items():
            require(packages.get(name) == version, f"{name} resolved to {packages.get(name)}, expected {version}.")
    return report


def rows(path):
    result = {}
    for row in ET.parse(path).findall(".//t:UnitTestResult", TRX):
        name = row.attrib["testName"]
        require(name not in result, f"Duplicate result identity {name}: {path}")
        result[name] = (row.attrib["outcome"], " ".join(row.itertext()))
    require(result, f"The runner produced no test results: {path}")
    return result


def journal(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def run_case(application, name, workspace, output, environment, expected_exit, selection=None, native=False):
    directory = output / name
    directory.mkdir()
    ledger = directory / "journal.jsonl"
    variables = {**environment, "MSTEST_EVIDENCE_JOURNAL": str(ledger), "MSTEST_EVIDENCE_NATIVE": str(native)}
    arguments = [*application, "--report-trx", "--report-trx-filename", "results.trx",
                 "--results-directory", str(directory), "--output", "Detailed"]
    if selection:
        arguments += ["--filter", selection]
    text = command(arguments, workspace, directory / "execution.log", variables, expected_exit)
    return rows(directory / "results.trx"), journal(ledger), text


def single_outcome(found, name, outcome, marker=None):
    require(len(found) == 1, f"Expected exactly one result for {name}: {found}")
    key, (actual, text) = next(iter(found.items()))
    require(key.split("(", 1)[0].rstrip() == name and actual == outcome,
            f"Expected {name}: {outcome}, got {found}")
    if marker:
        require(marker in text, f"Original marker {marker!r} was lost: {text}")


def discover(application, workspace, evidence, environment, expected_count, original_source=None):
    text = command([*application, "--list-tests", "json"], workspace, evidence, environment)
    tests = json.loads(text)["tests"]
    require(len(tests) == expected_count, f"Expected {expected_count} discovered tests: {evidence}")
    if original_source:
        source = original_source.read_text().splitlines()
        for test in tests:
            location = test["location"]
            require(Path(location["file"]).resolve() == original_source.resolve(), f"Wrong discovery file: {test}")
            start = location["lineStart"]
            require(0 < start <= len(source) and "[TestMethod" in source[start - 1], f"Wrong declaration line: {test}")
            require(location["lineEnd"] == start, f"Unexpected declaration range: {test}")
    return tests


def runtime_identifier():
    system = {"Darwin": "osx", "Linux": "linux", "Windows": "win"}.get(platform.system())
    architecture = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "AMD64": "x64"}.get(platform.machine())
    require(system and architecture, "Supply a supported RID using --rid.")
    return f"{system}-{architecture}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mstest-sdk", required=True, help="Exact SDK/framework version for the isolated consumers")
    parser.add_argument("--dotnet-sdk", help="Exact installed .NET SDK; default is the fixture's recorded SDK")
    parser.add_argument("--target-framework", default="net10.0")
    parser.add_argument("--hosting", action="store_true", help="Also verify the independently versioned experimental hosting packages")
    parser.add_argument("--mstest-hosting-version", default="4.5.1-alpha.26507.8")
    parser.add_argument("--platform-hosting-version", default="1.0.0-alpha.26507.8")
    parser.add_argument("--native-aot", action="store_true", help="Publish and execute the native consumer; requires the RID's native toolchain")
    parser.add_argument("--rid", help="Actual publication RID, defaulting to this host")
    parser.add_argument("--output", type=Path, default=Path.cwd() / "artifacts/mstest-capabilities")
    args = parser.parse_args()
    require(re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", args.mstest_sdk), "Use an exact MSTest.Sdk version.")
    skill = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="run-", dir=args.output.resolve()))
    workspace = output / "workspace"
    shutil.copytree(skill / "assets/runner-evidence", workspace,
                    ignore=shutil.ignore_patterns("bin", "obj", "__pycache__"))
    config = json.loads((workspace / "global.json").read_text())
    config["msbuild-sdks"]["MSTest.Sdk"] = args.mstest_sdk
    if args.dotnet_sdk: config["sdk"]["version"] = args.dotnet_sdk
    (workspace / "global.json").write_text(json.dumps(config, indent=2) + "\n")
    props = workspace / "Directory.Build.props"
    props.write_text(props.read_text().replace("<EvidenceMSTestVersion>4.5.1</EvidenceMSTestVersion>",
        f"<EvidenceMSTestVersion>{args.mstest_sdk}</EvidenceMSTestVersion>").replace("<TargetFramework>net10.0</TargetFramework>",
        f"<TargetFramework>{args.target_framework}</TargetFramework>"))
    hosting = workspace / "Hosting/Hosting.csproj"
    hosting.write_text(hosting.read_text().replace('Version="4.5.1-alpha.26507.8"', f'Version="{args.mstest_hosting_version}"')
                       .replace('Version="1.0.0-alpha.26507.8"', f'Version="{args.platform_hosting_version}"'))
    (workspace / "NuGet.Config").write_text('<configuration><packageSources><clear/><add key="nuget.org" value="https://api.nuget.org/v3/index.json"/></packageSources></configuration>\n')
    environment = {**os.environ, "DOTNET_CLI_UI_LANGUAGE": "en", "DOTNET_NOLOGO": "1", "MSBUILDDISABLENODEREUSE": "1"}
    for key in list(environment):
        if key.startswith(("OTEL_", "MSTEST_EVIDENCE_")): del environment[key]
    environment["MSTEST_EVIDENCE_JOURNAL"] = str(output / "bootstrap-journal.jsonl")
    command(["dotnet", "--info"], workspace, output / "dotnet-info.log", environment)
    policies = workspace / "Policies/Policies.csproj"
    # Run invokes the executable, avoiding a claim about the separate MSBuild/TRX controller path.
    command(["dotnet", "run", "--project", str(policies), "-c", "Release", "--", "--list-tests", "json"],
            workspace, output / "policies-compile-discovery.log", environment)
    policy_app = ["dotnet", str(workspace / f"Policies/bin/Release/{args.target_framework}/Policies.dll")]
    discover(policy_app, workspace, output / "policies-discovery.json", environment, 7)
    found, ledger, _ = run_case(policy_app, "filter-decisions", workspace, output, environment, 0,
        "ClassName~Filter&ClassName!~FilterThrowProbe")
    require(len(found) == 2 and found["RunExecutesTheBody"][0] == "Passed" and
            found["SkipHasAReportedReason"][0] == "NotExecuted", f"Wrong run/skip/drop results: {found}")
    require("filter-skip-original-marker" in found["SkipHasAReportedReason"][1], "Skip reason was lost.")
    require(Counter(row[2] for row in ledger if row[0] == "filter") == Counter(["run", "skip", "drop"]), "Filter decisions were not all exercised.")
    require([row[1] for row in ledger if row[0] == "construct"] == ["FilterRunProbe"], "Skip/drop constructed a test class.")
    require([row[1] for row in ledger if row[0] == "body"] == ["FilterRunProbe"], "Unexpected filtered body execution.")
    found, ledger, _ = run_case(policy_app, "filter-cli-selection", workspace, output, environment, 0, "ClassName=MSTestExtensionEvidence.Policies.FilterRunProbe")
    single_outcome(found, "RunExecutesTheBody", "Passed")
    require(sum(row[0] == "filter" for row in ledger) == 1, "Programmatic filtering ran before command-line selection.")
    found, ledger, _ = run_case(policy_app, "filter-throws", workspace, output, environment, 2, "ClassName=MSTestExtensionEvidence.Policies.FilterThrowProbe")
    single_outcome(found, "AThrowIsAFailure", "Failed", "filter-throw-original-marker")
    require(not any(row[0] in ("construct", "body") for row in ledger), "Throwing filter constructed/executed a test.")
    found, ledger, text = run_case(policy_app, "retry-recovers", workspace, output, environment, 0, "ClassName=MSTestExtensionEvidence.Policies.RetryPassProbe")
    single_outcome(found, "FailureThenInconclusiveThenPass", "Passed")
    require([row[2] for row in ledger if row[0] == "retry-pass"] == ["1", "2", "3"], "Retry attempts changed.")
    require("retry-pass-original-marker" in text and "retry-inconclusive-original-marker" in text, "Original attempt failures disappeared.")
    require(any(row[0] == "policy-first" and "retry-pass-original-marker" in row[2] for row in ledger), "RetryContext lost the first failure.")
    found, ledger, text = run_case(policy_app, "retry-exhausted", workspace, output, environment, 2, "ClassName=MSTestExtensionEvidence.Policies.RetryExhaustedProbe")
    single_outcome(found, "ExhaustionPreservesTheFinalFailure", "Failed", "retry-exhausted-original-marker-3")
    require([row[2] for row in ledger if row[0] == "retry-exhausted"] == ["1", "2", "3"], "Retry limit did not hold.")
    require(all(f"retry-exhausted-original-marker-{n}" in text for n in (1, 2, 3)), "An original failed attempt was hidden.")
    found, ledger, _ = run_case(policy_app, "retry-cancelled", workspace, output, environment, 2, "ClassName=MSTestExtensionEvidence.Policies.RetryCancellationProbe")
    single_outcome(found, "CancellationJoinsTheBodyBeforeCleanup", "Failed")
    events = [row for row in ledger if row[0].startswith("cancel-")]
    require([row[0] for row in events] == ["cancel-start", "cancel-observed", "cancel-joined", "cancel-cleanup"] * 2,
            f"Cancellation/cleanup was not joined per attempt: {events}")
    require(len(set(row[1] for row in events if row[0] == "cancel-start")) == 2, "Retries reused the test instance.")
    print("Runner policies verified: run/skip/drop, CLI selection, filter exception, retry history/limit and joined cancellation.", flush=True)

    if args.hosting:
        command(["dotnet", "run", "--project", str(hosting), "-c", "Release", "--", "--list-tests", "json"],
                workspace, output / "hosting-compile-discovery.log", environment)
        discovery_events = journal(output / "bootstrap-journal.jsonl")
        require(not any(row[0].startswith("scope-") for row in discovery_events), "Hosting discovery acquired an invocation scope.")
        app = ["dotnet", str(workspace / f"Hosting/bin/Release/{args.target_framework}/Hosting.dll")]
        found, ledger, text = run_case(app, "hosting-scopes", workspace, output, environment, 0)
        require(len(found) == 3 and all(row[0] == "Passed" for row in found.values()), f"Wrong hosting outcomes: {found}")
        scopes = defaultdict(list)
        for action, identifier, detail, _ in ledger:
            if action.startswith("scope-"): scopes[identifier].append(action)
        require(len(scopes) == 4, f"Expected four independent scopes for two rows and two retry attempts: {scopes}")
        require(all(actions == ["scope-created", "scope-initialize", "scope-body", "scope-cleanup", "scope-disposed"]
                    for actions in scopes.values()), f"Incorrect scope ownership/order: {scopes}")
        # The MTP controller and worker can each create a host. Validate ownership per process,
        # rather than pretending the factory is called once across the entire run.
        hosts = defaultdict(list)
        for row in ledger:
            if row[0].startswith("host-"): hosts[row[3]].append(row[0])
        require(hosts and all(events == ["host-created", "host-started", "host-stopped", "host-disposed"]
                              for events in hosts.values()), f"A process did not complete its host lifetime: {hosts}")
        for process in {row[3] for row in ledger if row[0] == "scope-created"}:
            events = [row[0] for row in ledger if row[3] == process]
            require(max(i for i, action in enumerate(events) if action == "scope-disposed") < events.index("host-stopped"),
                    "The root host stopped before its invocation scopes were disposed.")
        require(Counter(row[2] for row in ledger if row[0] == "scope-body") == Counter(["2", "5", "retry-1", "retry-2"]),
                "The host did not execute the two distinct data rows and retry attempts.")
        require("hosting-retry-original-marker" in text, "Hosting retry lost the first failure.")
        print("Optional real host verified: two data rows, two retry scopes, async disposal after cleanup, root disposal last.", flush=True)

    project = workspace / "Generated/Generated.csproj"
    for native in ([False, True] if args.native_aot else [False]):
        name = "generated-native" if native else "generated-managed"
        publish = output / name / "publish"
        arguments = ["dotnet", "publish", str(project), "-c", "Release", "-o", str(publish),
                     f"-p:PublishAot={str(native).lower()}", "-nodeReuse:false", "-maxcpucount:4"]
        if native: arguments += ["-r", args.rid or runtime_identifier(), "--self-contained", "true"]
        else: arguments += ["--self-contained", "false"]
        command(arguments, workspace, output / f"{name}-publish.log", environment, timeout=900)
        api_properties = {"Configuration": "Release", "PublishAot": str(native).lower(), "SelfContained": str(native).lower()}
        if native: api_properties["RuntimeIdentifier"] = args.rid or runtime_identifier()
        api_evidence(project, api_properties, workspace, output / f"{name}-api.json", environment, args.mstest_sdk)
        binary = publish / ("Generated.exe" if os.name == "nt" and native else "Generated" if native else "Generated.dll")
        require(binary.is_file(), f"Published consumer missing: {binary}")
        app = [str(binary)] if native else ["dotnet", str(binary)]
        discover(app, workspace, output / f"{name}-discovery.json", environment, 6, workspace / "Generated/GeneratedTests.cs")
        found, ledger, _ = run_case(app, name + "-execution", workspace, output, environment, 2, native=native)
        require(Counter(row[0] for row in found.values()) == Counter({"Passed": 5, "Failed": 1}), f"Wrong published consumer outcomes: {found}")
        require("typed-value-original-marker" in found["RejectionKeepsTheOriginalFailure"][1], "Published consumer lost the original assertion.")
        identifiers = [row[1] for row in ledger if row[0] == "generated-initialize"]
        require(len(identifiers) == len(set(identifiers)) == 6, "Published data rows did not get independent lifecycles.")
        for identifier in identifiers:
            actions = [row[0] for row in ledger if row[1] == identifier]
            require(actions[0] == "generated-initialize" and actions[-1] == "generated-cleanup" and
                    actions.count("generated-body") == 1, f"Incomplete generated lifecycle: {actions}")
            body = next(row for row in ledger if row[1] == identifier and row[0] == "generated-body")
            if body[2] == "async":
                require(actions.count("generated-resumed") == 1 and actions.index("generated-resumed") < actions.index("generated-cleanup"),
                        "The async continuation did not complete before cleanup.")
        require(Counter(row[2] for row in ledger if row[0] == "generated-int64") == Counter([str(-(2 ** 63)), str(2 ** 63 - 1)]),
                "The published consumer received incorrect Int64 boundary arguments.")
        generated = list((workspace / "Generated/obj/generated").rglob("*.cs"))
        require(any("MSTestReflectionMetadata" in path.read_text() for path in generated), "Generated invocation source was not retained.")
        (output / f"{name}-artifact.json").write_text(json.dumps({"path":str(binary), "sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
            "native":native,"rid":args.rid or runtime_identifier() if native else None,"results":{"passed":5,"expected_failed":1},
            "generated_sources":[str(path.relative_to(workspace)) for path in generated]}, indent=2) + "\n")
        print(f"Published {name} consumer verified: 5 passed, 1 owned rejection, source navigation and joined lifecycles.", flush=True)
    for name in ["Policies"] + (["Hosting"] if args.hosting else []):
        extras = {"MSTest.Extensions.Hosting": args.mstest_hosting_version,
                  "Microsoft.Testing.Extensions.Hosting": args.platform_hosting_version} if name == "Hosting" else {}
        api_evidence(workspace / name / f"{name}.csproj", {"Configuration": "Release"}, workspace,
                     output / f"{name.lower()}-api.json", environment, args.mstest_sdk, extras)
    (output / "verified.json").write_text(json.dumps({"mstest_sdk": args.mstest_sdk, "dotnet_sdk": config["sdk"]["version"],
        "target_framework":args.target_framework,"hosting":args.hosting,"native_aot":args.native_aot,
        "entrypoints":"real executables; separate MSBuild/TRX controller compatibility is not asserted"}, indent=2) + "\n")
    print(f"VERIFIED capability evidence: {output}")


if __name__ == "__main__":
    main()
