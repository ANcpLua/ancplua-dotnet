#!/usr/bin/env python3
"""Run the pinned examples and positive/negative AOT-analysis probes in temp storage."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

skill = Path(__file__).resolve().parents[1]


def run(args, cwd, expected_success=True):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if (result.returncode == 0) != expected_success:
        raise RuntimeError(f"{args!r} returned {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


with tempfile.TemporaryDirectory(prefix="mstest-assertions-") as scratch:
    root = Path(scratch)
    shutil.copy2(skill / "examples/global.json", root / "global.json")
    managed = root / "managed"
    managed.mkdir()
    shutil.copy2(skill / "examples/EqualityExamples.cs", managed)
    (managed / "Examples.csproj").write_text('''<Project Sdk="MSTest.Sdk/4.5.1">
  <PropertyGroup>
    <TargetFramework>net11.0</TargetFramework>
    <LangVersion>15</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
</Project>
''')
    run(["dotnet", "test", "--project", str(managed / "Examples.csproj"),
         "--report-trx", "--report-trx-filename", "examples.trx",
         "--results-directory", str(root / "results")], root)
    report = ET.parse(root / "results/examples.trx")
    ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
    results = report.findall(".//t:UnitTestResult", ns)
    expected_names = set(re.findall(r"public void (\w+)\(\)", (managed / "EqualityExamples.cs").read_text()))
    actual_names = {r.attrib["testName"].split(".")[-1] for r in results}
    if actual_names != expected_names or any(r.attrib["outcome"] != "Passed" for r in results):
        raise RuntimeError("Unexpected test discovery/results: " + str([r.attrib for r in results]))
    print(f"Managed examples: Passed {len(results)}, Failed 0, Skipped 0")

    for name, source, success in [
        ("typed", (skill / "examples/TypedAssertions.cs").read_text(), True),
        ("reflection", '''using Microsoft.VisualStudio.TestTools.UnitTesting;
public static class UnsafeForAot {
  public static void Check(object expected, object actual) {
    Assert.AreEquivalent(expected, actual, strict: true);
    Assert.AreNotEquivalent(expected, actual);
    Assert.That(() => expected == actual);
  }
}
''', False),
    ]:
        folder = root / name
        folder.mkdir()
        (folder / "Probe.cs").write_text(source)
        (folder / "Probe.csproj").write_text('''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net11.0</TargetFramework><LangVersion>15</LangVersion>
    <Nullable>enable</Nullable><ImplicitUsings>enable</ImplicitUsings>
    <IsAotCompatible>true</IsAotCompatible>
    <WarningsAsErrors>$(WarningsAsErrors);IL2026;IL3050</WarningsAsErrors>
  </PropertyGroup>
  <ItemGroup><PackageReference Include="MSTest.TestFramework" Version="4.5.1" /></ItemGroup>
</Project>
''')
        output = run(["dotnet", "build", str(folder / "Probe.csproj"), "--nologo"], root, success)
        if not success:
            codes = set(re.findall(r"\berror (\w+)\b", output))
            if codes != {"IL2026", "IL3050"}:
                raise RuntimeError(f"Unexpected negative-probe diagnostics: {codes}\n{output}")
            expected_diagnostics = {4: {"IL2026", "IL3050"}, 5: {"IL2026", "IL3050"}, 6: {"IL3050"}}
            for line, expected_codes in expected_diagnostics.items():
                actual_codes = set(re.findall(r"Probe\.cs\(" + str(line) + r",\d+\): error (\w+)", output))
                if actual_codes != expected_codes:
                    raise RuntimeError(f"Wrong diagnostics at probe line {line}: {actual_codes}\n{output}")
        print(f"AOT analysis {name}: {'PASS' if success else 'expected IL2026 + IL3050'}")
    print("AOT checks are analyzer evidence, not a NativeAOT publish/run certification.")
