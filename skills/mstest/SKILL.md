---
name: mstest
description: Sets up, writes, runs and reviews MSTest tests on MSTest.Sdk 4.5.1 with Microsoft.Testing.Platform (MTP) 2.5.1 and native .NET 10 `dotnet test`, never VSTest. Use when creating or converting a test project, choosing TestingExtensionsProfile, wiring coverage (Microsoft.Testing.Extensions.CodeCoverage, dotcov), running or filtering tests, reading MTP exit codes, writing MSTest v4 assertions, data-driven or lifecycle-sensitive tests, testing Native AOT, extending MSTest, or reviewing whether tests prove a change.
license: Apache-2.0
metadata:
  mstest: "4.5.1"
  mtp: "2.5.1"
  dotnet-sdk: "10.0.402"
---

# MSTest on Microsoft.Testing.Platform

Target stack: `MSTest.Sdk` 4.5.1 (brings MSTest 4.5.1 and MTP 2.5.1), .NET SDK 10.0.4xx, and the
native MTP mode of `dotnet test`. Replace VSTest, `Microsoft.NET.Test.Sdk`, `coverlet` and
runsettings-only workflows; don't bridge them.

Every fact here is checked by `scripts/verify.sh` in this plugin's repository against a probe
project (`fixtures/mstest-probe`). Before relying on a version-gated option in a different
repository, run its test app with `--help`. Learn mixes MSTest, MTP and .NET SDK version
numbers; the binary is ground truth.

| Task | Read |
|---|---|
| Lifecycle order, setup failures, parallelism, `ResourceLock`, temp directories, global hooks | `references/lifecycle.md` |
| `DataRow`, `DynamicData`, `TestDataRow<T>`, combinatorial data, custom data sources, extension points, conditions | `references/data-and-extensions.md` |
| Native AOT test projects and source generation | `references/native-aot.md` |
| Assertions and analyzers (v4 API) | `references/mstest-v4-api.md` |
| Reviewing tests: smells, assertion strength, change evidence, gap mapping | `references/test-smells.md`, `references/test-evidence.md` |

## 1. Project shape

`global.json` at the repository root:

```json
{
  "sdk": { "version": "10.0.402", "rollForward": "latestFeature" },
  "msbuild-sdks": { "MSTest.Sdk": "4.5.1" },
  "test": { "runner": "Microsoft.Testing.Platform" }
}
```

- `test.runner` is mandatory. MTP v2 refuses the VSTest-based `dotnet test` on the .NET 10 SDK
  ("Testing with VSTest target is no longer supported by Microsoft.Testing.Platform on .NET 10
  SDK and later").
- `msbuild-sdks` pins the SDK version once; project files say `Sdk="MSTest.Sdk"` without a version.

Test project:

```xml
<Project Sdk="MSTest.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <TestingExtensionsProfile>AllMicrosoft</TestingExtensionsProfile>
  </PropertyGroup>
  <ItemGroup>
    <ProjectReference Include="../../src/Foo/Foo.csproj" />
  </ItemGroup>
</Project>
```

MSTest.Sdk 4.5.1 sets these itself (verified by evaluation):

- `OutputType=Exe`, `IsPackable=false`, `EnableMSTestRunner=true`, `IsTestingPlatformApplication=true`
  and `UsingMSTestSdk=true`.
- The MSTest and MTP package references.

It does **not** set `IsTestProject`. Before deleting an explicit `<IsTestProject>true</IsTestProject>`,
search the repository's build files and the SDKs it imports for logic keyed on it. ANcpLua.NET.Sdk,
for example, imports its test targets and gates roll-forward and pack settings on
`IsTestProject`. If you delete it, move that logic to `IsTestingPlatformApplication` or
`UsingMSTestSdk`.

Delete these when converting a project:

- Package references: `MSTest`, `MSTest.TestFramework`, `MSTest.TestAdapter`, `MSTest.Analyzers`,
  `Microsoft.NET.Test.Sdk`, `Microsoft.Testing.Extensions.*` (use the profile instead), `coverlet.*`.
- Properties: `<OutputType>Exe`, `<IsPackable>false`, `<EnableMSTestRunner>`,
  `<TestingPlatformDotnetTestSupport>`, `<TestingPlatformCaptureOutput>`,
  `<TestingPlatformShowTestsFailure>`.

More facts:

- The MSTest namespace is a global using only with `ImplicitUsings` enabled. Otherwise every file
  needs `using Microsoft.VisualStudio.TestTools.UnitTesting;` (CS0246 on `TestClass`).
  Combinatorial data lives in `Microsoft.VisualStudio.TestTools.UnitTesting.Combinatorial`.
- A test project that needs another base SDK (for example `Microsoft.NET.Sdk.Web`) layers
  MSTest.Sdk with explicit imports, which keeps the profile and extension switches:

  ```xml
  <Project>
    <Import Project="Sdk.props" Sdk="Microsoft.NET.Sdk.Web" />
    <Import Project="Sdk.props" Sdk="MSTest.Sdk" />
    <!-- properties and items -->
    <Import Project="Sdk.targets" Sdk="MSTest.Sdk" />
    <Import Project="Sdk.targets" Sdk="Microsoft.NET.Sdk.Web" />
  </Project>
  ```

  Don't fall back to the `MSTest` metapackage: it depends on `Microsoft.NET.Test.Sdk`, which brings
  VSTest back.
- A helper library that uses MSTest.Sdk but contains no tests sets
  `<IsTestApplication>false</IsTestApplication>`.

## 2. TestingExtensionsProfile

| Profile | Extensions in the shipped 4.5.1 package | Options in `--help` (snapshot in `fixtures/mstest-probe/help/`) |
|---|---|---|
| `None` | none | platform options only |
| `Default` | TrxReport, CodeCoverage | 38 |
| `AllMicrosoft` | Default + CrashDump, HangDump, HtmlReport, Retry, HotReload, AzureDevOpsReport, GitHubActionsReport, Fakes | 83 |

- Learn's table says `Default` also includes the GitHub Actions and Azure DevOps reports from
  4.3.0. The 4.5.1 package doesn't. Trust the package.
- Turn single extensions on or off with `Enable<PackageIdWithoutDots>`, for example
  `EnableMicrosoftTestingExtensionsRetry=true`.
- Opt-in extensions no profile includes: `EnableMicrosoftTestingExtensionsJUnitReport` and
  `EnableMicrosoftTestingExtensionsCtrfReport` (both prerelease). Feature switches:
  `EnableAspireTesting`, `EnablePlaywright`, `EnableWindowsUIAutomation`.
- Fakes: the extension restores and loads on every OS. Only generating Fakes assemblies needs
  Visual Studio Enterprise on Windows, so cross-platform repositories gain nothing from it. Set
  `EnableMicrosoftTestingExtensionsFakes=false` for clarity, not because it breaks.
- Retry and HotReload use the Microsoft Testing Platform Tools license. It's free for individuals,
  open source and small organizations, but larger companies need a Visual Studio subscription.
  Mention it when proposing `AllMicrosoft` for a company repository.
- What `AllMicrosoft` buys an existing project:
  - `--crashdump`/`--hangdump` evidence for CI hangs.
  - `--retry-failed-tests` for genuinely external flakiness.
  - `--report-html`, and `--report-gh` step summaries and annotations.
  - Hot reload through `dotnet watch`.

  Every one stays inactive until its option is passed. The cost is about 10 MB of restore and no
  change to a plain run.
- The property exists only in MSTest.Sdk. With `Microsoft.NET.Sdk`, reference
  `Microsoft.Testing.Extensions.<Name>` packages individually, aligned with the MTP version.

## 3. Running tests

```bash
dotnet test                                   # solution or project in the current directory
dotnet test --project tests/Foo.Tests         # one project
dotnet test --solution Foo.slnx               # explicit solution
dotnet test --test-modules "artifacts/**/*.Tests.dll"
dotnet test --project tests/Foo.Tests --filter "FullyQualifiedName~Orders"
dotnet test --project tests/Foo.Tests --report-trx --coverage --coverage-output-format cobertura
dotnet test --minimum-expected-tests 50 -- --minimum-expected-tests 5   # whole run, then per module
./artifacts/bin/Foo.Tests/release/Foo.Tests --list-tests                # the test app is an executable
```

- In native mode, options go straight to `dotnet test`. A `--` separator is optional; it marks where
  test-application arguments begin and makes `--minimum-expected-tests` per-module.
- The whole-run minimum counts skipped tests and the per-module minimum doesn't.
- Build options (`-c`, `-f`, `-r`, `--no-build`, `--no-restore`, `-v`) go before `--`.
  `--artifacts-path` reaches MTP mode only from the .NET 11 SDK.
- Some `dotnet test`-level features need the .NET 11 SDK even with MTP 2.5.1: run-wide
  `--maximum-failed-tests`, `--results-directory-layout` and the aggregated zero-tests verdict. The
  test app's own options (`--maximum-failed-tests`, `--timeout`, `--list-tests json`) work
  per module on SDK 10.
- MSTest filters:
  - `--filter` takes the TestCase filter syntax: `FullyQualifiedName~X`, `Name=Y`,
    `ClassName=Ns.Type` (the namespace is required), `TestCategory=Z`, `Priority=1`, `Id=...`,
    combined with `&`, `|`, `!`.
  - `--filter-uid` takes test UIDs.
  - `--filter-method`, `--filter-class` and `--treenode-filter` belong to xUnit v3 and TUnit, not
    MSTest.
- `--settings <file.runsettings>` stays valid under MTP for MSTest settings and
  `TestRunParameters` (also `--test-parameter key=value`). VSTest-only parts such as most of
  `RunConfiguration`, data collectors and loggers are ignored. Map VSTest flags like this:
  - `--logger trx` becomes `--report-trx`.
  - `--collect "Code Coverage"` becomes `--coverage`.
  - `--blame-crash` and `--blame-hang` become `--crashdump` and `--hangdump`.
- Per-project defaults: `<TestingPlatformCommandLineArguments>$(TestingPlatformCommandLineArguments) --minimum-expected-tests 10</TestingPlatformCommandLineArguments>`
  or a `testconfig.json` next to the project.
- For agent-friendly output, `--output Minimal` trims result blocks. `--show-stdout` and
  `--show-stderr` control captured output.
- A filtered run that reports green proves nothing until you check the executed count.

Exit codes (MTP 2.5.1 `ExitCode` enum):

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | generic failure |
| 2 | at least one test failed |
| 3 | session aborted (Ctrl+C) |
| 4 | invalid extension setup |
| 5 | invalid command line, for example an option whose extension isn't registered |
| 6 | no longer produced |
| 7 | test host exited non-gracefully (crash) |
| 8 | zero tests ran (or all skipped under `--zero-tests-policy strict`) |
| 9 | fewer tests than `--minimum-expected-tests` |
| 10 | test framework infrastructure failure |
| 11 | a dependent process exited (`--exit-on-process-exit`) |
| 12 | incompatible protocol versions between platform processes |
| 13 | `--maximum-failed-tests` reached |
| 14 | coverage threshold failed |
| 15 | execution stopped early because the configured deadline was approaching; not every test ran |

- Never pipe `dotnet test` into `grep`, `tail` or `head` when the exit code matters. Capture the
  output to a file, then inspect the file.
- `--ignore-exit-code 8` is for projects that intentionally have no runnable tests. It's not for
  hiding a wrong filter.

## 4. Coverage

- Under MTP, `--coverage` comes from `Microsoft.Testing.Extensions.CodeCoverage` (18.12.0 with
  MSTest.Sdk 4.5.1). The `Default` and `AllMicrosoft` profiles include it.
- `Microsoft.CodeCoverage` is the VSTest data collector that `Microsoft.NET.Test.Sdk` brings in.
  A direct reference to it does nothing for an MTP run. `coverlet.collector` is VSTest-only.
- Cobertura for gates and diffs: `--coverage --coverage-output-format cobertura`. Use
  `--coverage-settings <file>` for include and exclude rules.
- Gate with dotcov, the ANcpLua coverage gate for any Cobertura report:
  - `dotcov test --min-line 90 --min-branch 80` runs `dotnet test` with coverage into a fresh
    `TestResults/<run>`. `dotcov check TestResults/ --min-line 90` gates an existing report.
  - Exit codes: 0 pass, 1 below threshold, 6 the test run itself failed. Run
    `dotcov --help` for the remaining codes and the CRAP and exclusion options of the installed
    version.
- Never compute coverage or CRAP numbers in your head. Read them from the Cobertura report.

## 5. Writing tests (MSTest 4.x)

Read `references/mstest-v4-api.md` before writing assertions. The rules most often broken:

- `[TestClass]` classes are `sealed`. Use the constructor for synchronous setup and
  `[TestInitialize]` for async setup. A throwing constructor skips cleanup; see
  `references/lifecycle.md`.
- Exceptions: `Assert.ThrowsExactly<T>(() => ...)` or `Assert.Throws<T>` (derived types allowed).
  The async forms must be awaited. `[ExpectedException]` and `Assert.ThrowsException` are removed
  in v4.
- `var typed = Assert.IsInstanceOfType<T>(value);` returns the cast value.
- Collections: `Assert.HasCount`, `IsEmpty`, `IsNotEmpty`, `Contains`, `DoesNotContain`,
  `ContainsSingle`, `ContainsAll`, `AreSequenceEqual`, `AreEquivalent`, not
  `Assert.IsTrue(list.Count == n)`.
- `Assert.AreEqual(expected, actual)`: the expected value comes first.
- Data: `[TestMethod]` with `[DataRow(...)]` (`[DataTestMethod]` is obsolete); `[DynamicData]` with
  tuples or `TestDataRow<T>`, not `object[]`. See `references/data-and-extensions.md`.
- Cancellation: take `TestContext` through the constructor and pass `TestContext.CancellationToken`.
  `[Timeout(..., CooperativeCancellation = true)]` only signals the token; code that ignores it
  still hangs.
- Platform-specific tests use `[OSCondition(OperatingSystems.Windows)]` instead of an `if`. Shared
  process state uses `[ResourceLock(...)]` instead of disabling parallelism.
- Time and randomness: `TimeProvider`/`FakeTimeProvider` and seeded `Random`. Never `DateTime.Now`,
  `Thread.Sleep` or `Task.Delay` as synchronization.
- `[Retry]` only for a test that depends on something external you can't control. A race in your
  own code is a bug, so fix it.
- v4 behavior:
  - AppDomain isolation is off under MTP.
  - `TreatDiscoveryWarningsAsErrors` is on.
  - `ClassCleanup` runs at the end of its class.
  - `TestContext.TestName` throws in `AssemblyInitialize` and `ClassInitialize`.

Analyzer mode: `<MSTestAnalysisMode>Recommended</MSTestAnalysisMode>` escalates suggestions to
warnings and makes MSTEST0003, MSTEST0043 and MSTEST0088 errors. Fix diagnostics instead of
suppressing them.

## 6. Reviewing test code

Pick the mode the request asks for; don't run them all by default.

- **Smells**: apply `references/test-smells.md`, a grep-able catalog with fixes.
- **Does this test prove the change?** Use `references/test-evidence.md`: assertion strength, the
  counterexample probe and gap mapping.

Report each finding as `file:line | finding | evidence | fix`, and keep three evidence classes
apart: static finding (read in code), hypothesis (not executed), executed result (failed or
passed for a stated reason). Severity is about false confidence first: a test that can pass while
the behavior is broken (missing `await` on an async assert, an assertion inside `catch`, no
assertion, a self-comparison) outranks style.

## 7. Done means

1. `dotnet build -c Release` with zero warnings, including MSTEST analyzers.
2. `dotnet test` in native mode, with the exit code read directly and the executed test count
   compared with the expectation (new tests raise it).
3. Coverage checked through dotcov or Cobertura when coverage was part of the request.
4. For Native AOT, the published executable ran (`references/native-aot.md`).
