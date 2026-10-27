"""Verify intentional MSTest failures through the real runner and its TRX report."""
import os
import json
import re
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET


def verify_navigation(root, output, environment):
    target = subprocess.run(
        ["dotnet", "msbuild", "examples/MSTestExtensionSamples/MSTestExtensionSamples.csproj",
         "-property:Configuration=Release", "-getProperty:TargetPath"],
        cwd=root, env=environment, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=120)
    (output / "sample-target-path.log").write_text(target.stdout)
    assembly = Path(target.stdout.strip())
    if target.returncode != 0 or not assembly.is_file():
        raise SystemExit(f"Could not resolve the built sample through MSBuild: {target.stdout}")
    result = subprocess.run(
        ["dotnet", str(assembly), "--list-tests", "json"],
        cwd=root, env=environment, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=120)
    (output / "sample-discovery.json").write_text(result.stdout)
    if result.returncode != 0:
        raise SystemExit(f"Sample discovery failed: {result.stdout}")
    tests = json.loads(result.stdout)["tests"]
    expected = {
        "Class_wrapper_preserves_data_arguments": ("ComposedExecutionTests", 2),
        "Wrapper_preserves_initialization_and_data": ("ExecutionExtensionTests", 1),
        "Broken_optional_diagnostics_preserve_the_original_failure": ("ExecutionExtensionTests", 3),
        "Exclude_mode_is_applied_by_the_framework": ("ExecutionExtensionTests", 1),
    }
    for method, (test_class, count) in expected.items():
        source = root / "examples/MSTestExtensionSamples" / f"{test_class}.cs"
        lines = source.read_text().splitlines()
        method_line = next(index for index, line in enumerate(lines)
                           if re.search(r"\bpublic\b.*\b" + re.escape(method) + r"\s*\(", line))
        declaration = max(index + 1 for index, line in enumerate(lines[:method_line])
                          if re.match(r"\s*\[(?:TestMethod|DiagnosticTestMethod)(?:\]|\()", line))
        rows = [test for test in tests if test["type"]["typeName"] == test_class
                and test["type"]["methodName"] == method]
        if len(rows) != count:
            raise SystemExit(f"Expected {count} native rows for {method}, found {len(rows)}")
        for row in rows:
            location = row["location"]
            if (Path(location["file"]).resolve() != source.resolve()
                    or location["lineStart"] != declaration or location["lineEnd"] != declaration):
                raise SystemExit(f"Discovery lost the original declaration for {method}: {location}")
    print("Verified 7 native row locations for ordinary, method-level and class-composed execution.")


def main():
    root = Path(__file__).resolve().parents[1]
    artifacts = root / "artifacts" / "mstest-probes"
    artifacts.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="run-", dir=artifacts))
    command = [
        "dotnet", "test", "--project", "examples/MSTestExtensionProbes",
        "-c", "Release", "--report-trx", "--report-trx-filename", "probes.trx",
        "--results-directory", str(output), "--minimum-expected-tests", "5",
    ]
    environment = {**os.environ, "DOTNET_CLI_UI_LANGUAGE": "en"}
    for label, arguments, expected_exit in [
        ("discovery", command[:6] + ["--list-tests"], 0),
        ("execution", command, 2),
    ]:
        result = subprocess.run(arguments, cwd=root, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        (output / f"{label}.log").write_text(result.stdout)
        if result.returncode != expected_exit:
            raise SystemExit(f"{label}: expected exit {expected_exit}, got {result.returncode}\n"
                             f"{result.stdout}\nEvidence: {output}")

    verify_navigation(root, output, environment)
    report = output / "probes.trx"
    ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
    document = ET.parse(report)
    results = document.findall(".//t:UnitTestResult", ns)
    expected = {
        "Original_failure_is_reported": ("Failed", "original-failure-marker"),
        "Broken_capture_preserves_failure": ("Failed", "capture-original-marker"),
        "Broken_output_preserves_failure": ("Failed", "output-original-marker"),
        "Inconclusive_stays_inconclusive": ("NotExecuted", "inconclusive-marker"),
        "False_condition_skips_body": ("NotExecuted", "capability-unavailable-marker"),
    }
    if len(results) != len(expected):
        raise SystemExit(f"Expected {len(expected)} results, found {len(results)}: {report}")
    for name, (outcome, marker) in expected.items():
        matching = [result for result in results if result.attrib["testName"].split("(", 1)[0].rstrip() == name]
        if len(matching) != 1:
            raise SystemExit(f"Expected one result for {name}: {report}")
        result = matching[0]
        text = " ".join(result.itertext())
        if result.attrib["outcome"] != outcome or marker not in text:
            raise SystemExit(f"Wrong outcome or missing original marker for {name}: {report}")
        if name == "Original_failure_is_reported" and "diagnostic: " not in text:
            raise SystemExit(f"The wrapper did not append diagnostics: {report}")
    print("Verified 5 runner probes: 3 original failures, 1 inconclusive, 1 conditional skip; exit 2.")
    print(f"Evidence: {output}")


if __name__ == "__main__":
    main()
