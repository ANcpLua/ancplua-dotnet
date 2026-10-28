"""Run the examples and failure probes against explicit SDK releases in isolated copies."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def execute(command, workspace, log, expected=0):
    result = subprocess.run(command, cwd=workspace, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=180,
                            env={**os.environ, "DOTNET_CLI_UI_LANGUAGE": "en"})
    log.write_text(result.stdout)
    if result.returncode != expected:
        raise SystemExit(f"Expected exit {expected}, got {result.returncode}: {' '.join(command)}\n{result.stdout}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("versions", nargs="+", help="Exact MSTest.Sdk package versions; no implicit upgrades")
    parser.add_argument("--output", type=Path, help="Evidence root; default is repository artifacts/compatibility")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    artifacts = args.output or root / "artifacts/compatibility"
    artifacts.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="run-", dir=artifacts))
    previous = None
    for version in args.versions:
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
            raise SystemExit(f"Use an exact package version: {version}")
        if tuple(map(int, version.split("-", 1)[0].split("."))) < (4, 5, 1):
            raise SystemExit("These native-only examples require MSTest.Sdk 4.5.1 or later.")
        evidence = output / version
        evidence.mkdir()
        with tempfile.TemporaryDirectory(prefix="mstest-compat-") as temporary:
            workspace = Path(temporary)
            for folder in ["examples", "scripts", "skills"]:
                shutil.copytree(root / folder, workspace / folder,
                                ignore=shutil.ignore_patterns("bin", "obj", "__pycache__"))
            config = json.loads((root / "global.json").read_text())
            config["msbuild-sdks"]["MSTest.Sdk"] = version
            (workspace / "global.json").write_text(json.dumps(config, indent=2) + "\n")
            command = ["dotnet", "test", "--project", "examples/MSTestExtensionSamples", "-c", "Release"]
            discovery = execute(command + ["--list-tests"], workspace, evidence / "discovery.log")
            count = 31
            if not re.search(rf"Discovered {count} tests\.", discovery):
                raise SystemExit(f"Expected {count} discovered cases for {version}; see {evidence}")
            for display in ["Inline_label_keeps_method_name (inline-label)",
                            "Dynamic_label_keeps_method_name (dynamic-label)"]:
                if display not in discovery:
                    raise SystemExit(f"Missing argument display label {display}: {evidence}")
            execute(command + ["--minimum-expected-tests", str(count)], workspace, evidence / "execution.log")
            execute([sys.executable, "scripts/verify_mstest_probes.py"], workspace, evidence / "probes.log")
            shutil.copytree(workspace / "artifacts/mstest-probes", evidence / "probes")
            inspect_base = [sys.executable, "skills/mstest/scripts/inspect_mstest.py",
                            "--project", "examples/MSTestExtensionSamples/MSTestExtensionSamples.csproj",
                            "--property", "Configuration=Release"]
            inspect_command = inspect_base.copy()
            if previous:
                inspect_command += ["--previous", str(previous)]
            report_path = evidence / "api.json"
            report = json.loads(execute(inspect_command, workspace, report_path))
            if not report["requires_api_refresh"]:
                raise SystemExit("A different package version incorrectly reused the earlier API evidence")
            for context in report["contexts"]:
                if context["sdk"]["version"] != version:
                    raise SystemExit(f"SDK did not resolve to {version}")
                for package in context["packages"]:
                    if package["id"] in ("MSTest.TestFramework", "MSTest.TestAdapter") and package["version"] != version:
                        raise SystemExit(f"{package['id']} did not resolve to {version}")
            stable_command = inspect_base + ["--previous", str(report_path)]
            stable = json.loads(execute(stable_command, workspace, evidence / "unchanged-api.json"))
            if stable["requires_api_refresh"]:
                raise SystemExit("Unchanged resolved APIs should permit evidence reuse")
            previous = report_path
            print(f"{version}: {count} examples + 5 runner probes passed; resolved APIs recorded.", flush=True)
    print(f"Evidence: {output}")


if __name__ == "__main__":
    main()
