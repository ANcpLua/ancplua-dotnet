---
name: mstest
description: Sets up, writes, runs and reviews MSTest tests on MSTest.Sdk 4.5.1 with Microsoft.Testing.Platform (MTP) 2.5.1 and native .NET 10 `dotnet test`, never VSTest. Use when creating or converting a test project, choosing TestingExtensionsProfile, wiring coverage (Microsoft.Testing.Extensions.CodeCoverage, dotcov), running or filtering tests, reading MTP exit codes, writing MSTest v4 assertions, or reviewing test code for smells.
license: Apache-2.0
metadata:
  mstest: "4.5.1"
  mtp: "2.5.1"
  dotnet-sdk: "10.0.402"
---

# MSTest on Microsoft.Testing.Platform

Target stack: `MSTest.Sdk` 4.5.1 (brings MSTest 4.5.1 and MTP 2.5.1), .NET SDK 10.0.4xx, the native
MTP mode of `dotnet test`. VSTest, `Microsoft.NET.Test.Sdk`, `coverlet` and `.runsettings`-only
workflows are out of scope: replace them, don't bridge them.

Before stating a version-gated option, check it: build the test project and run
`<test-app> --help` (or `dotnet test --project <proj> --help`). Docs on learn.microsoft.com mix
MSTest and MTP version numbers; the binary's `--help` is ground truth.

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
  ("Testing with VSTest target is no longer supported by MTP on .NET 10 SDK and later").
- `msbuild-sdks` pins the SDK version once; project files say `Sdk="MSTest.Sdk"` without a version.

Test project:

```xml
<Project Sdk="MSTest.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <TestingExtensionsProfile>AllMicrosoft</TestingExtensionsProfile>
    <EnableMicrosoftTestingExtensionsFakes>false</EnableMicrosoftTestingExtensionsFakes>
  </PropertyGroup>
  <ItemGroup>
    <ProjectReference Include="../../src/Foo/Foo.csproj" />
  </ItemGroup>
</Project>
```

MSTest.Sdk already sets `OutputType=Exe`, `IsTestProject`, `IsPackable=false`, `EnableMSTestRunner`
and the MSTest/MTP package references. Delete these when converting a project:
`<PackageReference Include="MSTest*|Microsoft.NET.Test.Sdk|Microsoft.Testing.Extensions.*|coverlet.*">`,
`<OutputType>Exe`, `<IsTestProject>`, `<EnableMSTestRunner>`, `<TestingPlatformDotnetTestSupport>`,
`<TestingPlatformCaptureOutput>`, `<TestingPlatformShowTestsFailure>`.

Facts verified by building MSTest.Sdk 4.5.1:

- The MSTest namespace is a global using only with `ImplicitUsings` enabled. Otherwise every
  file needs `using Microsoft.VisualStudio.TestTools.UnitTesting;` (CS0246 on `TestClass`).
- `MSTest.Sdk` derives from `Microsoft.NET.Sdk`. A test project that needs `Microsoft.NET.Sdk.Web`
  or another top-level SDK uses `Microsoft.NET.Sdk` plus the `MSTest` package and
  `EnableMSTestRunner=true`, `OutputType=Exe`.
- A helper library that uses MSTest.Sdk but contains no tests sets
  `<IsTestApplication>false</IsTestApplication>`.

## 2. TestingExtensionsProfile

| Profile | Extensions in the shipped 4.5.1 package | `--help` options |
|---|---|---|
| `None` | none | platform only |
| `Default` | TrxReport, CodeCoverage | 38 |
| `AllMicrosoft` | Default + CrashDump, HangDump, HtmlReport, Retry, HotReload, AzureDevOpsReport, GitHubActionsReport, Fakes | 85 (Fakes off) |

- Learn's table says `Default` also includes the GitHub Actions and Azure DevOps reports from
  4.3.0. The 4.5.1 package doesn't. Trust the package.
- Turn single extensions on or off with `Enable<PackageIdWithoutDots>`, for example
  `EnableMicrosoftTestingExtensionsFakes=false`, `EnableMicrosoftTestingExtensionsRetry=true`.
- Fakes needs Visual Studio Enterprise on Windows. Disable it in cross-platform and macOS repos.
- Retry and HotReload use the Microsoft Testing Platform Tools license. It's free for individuals,
  open source and small organizations, but larger companies need a Visual Studio subscription.
  Mention it when proposing `AllMicrosoft` for a company repository.
- What `AllMicrosoft` buys an existing project: `--crashdump`/`--hangdump` evidence for CI hangs,
  `--retry-failed-tests` for genuinely external flakiness, `--report-html`, `--report-gh` step
  summaries and annotations, and hot reload via `dotnet watch`. All of these stay inactive until
  their option is passed, so the cost is about 10 MB of restore and no change to a plain run.
- The property exists only in MSTest.Sdk. The `MSTest` metapackage ignores it; there you
  reference `Microsoft.Testing.Extensions.<Name>` packages individually, aligned to the MTP version.

## 3. Running tests

```bash
dotnet test                                   # solution/project found in the current directory
dotnet test --project tests/Foo.Tests         # one project
dotnet test --solution Foo.slnx               # explicit solution
dotnet test --test-modules "artifacts/**/*.Tests.dll"
dotnet test --project tests/Foo.Tests --filter "FullyQualifiedName~Orders"
dotnet test --project tests/Foo.Tests --report-trx --coverage --coverage-output-format cobertura
dotnet test --minimum-expected-tests 50 -- --minimum-expected-tests 5   # whole run, then per module
./artifacts/bin/Foo.Tests/release/Foo.Tests --list-tests              # the test app is an executable
```

- In native mode, options go straight to `dotnet test`. A `--` separator is optional and marks
  where test-application arguments begin.
- Build options (`-c`, `-f`, `-r`, `--no-build`, `--no-restore`, `-v`, `--artifacts-path`) belong
  before `--`.
- MSTest filters: `--filter` takes the TestCase filter syntax (`FullyQualifiedName~X`,
  `TestCategory=Y`, `ClassName=Z`, combined with `&`, `|`, `!`), and `--filter-uid` takes UIDs.
  `--filter-method`, `--filter-class` and `--treenode-filter` belong to xUnit v3 and TUnit, not
  MSTest.
- VSTest flags such as `--logger`, `--collect`, `--blame*`, `--settings` with `<RunConfiguration>`
  and `--filter` passed through `--` in bridge mode are the wrong platform. Map them to
  `--report-trx`, `--coverage`, `--crashdump`/`--hangdump`, `testconfig.json`.
- Per-project defaults go in `<TestingPlatformCommandLineArguments>`. Keep the self-reference:
  `$(TestingPlatformCommandLineArguments) --minimum-expected-tests 10`.
- A filtered run that reports green proves nothing until you check the executed count.

Exit codes (MTP):

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | unknown error |
| 2 | at least one test failed |
| 3 | session aborted (Ctrl+C) |
| 4 | invalid extension setup |
| 5 | invalid command line, for example an option whose extension isn't registered |
| 7 | session crashed |
| 8 | zero tests ran (or all skipped under `--zero-tests-policy strict`) |
| 9 | fewer tests than `--minimum-expected-tests` |
| 10 | test framework infrastructure failure |
| 13 | `--maximum-failed-tests` reached |
| 14 | coverage threshold failed |

- Never pipe `dotnet test` into `grep`, `tail` or `head` when the exit code matters.
- To read a summary, capture the output to a file, then inspect that file.
- `--ignore-exit-code 8` is for projects that intentionally have no runnable tests. It's not for
  hiding a wrong filter.

## 4. Coverage

- Under MTP, `--coverage` comes from `Microsoft.Testing.Extensions.CodeCoverage`. The `Default`
  and `AllMicrosoft` profiles include it.
- `Microsoft.CodeCoverage` is the VSTest data collector that `Microsoft.NET.Test.Sdk` brings in.
  A direct reference to it does nothing in an MTP project. `coverlet.collector` is VSTest-only.
- Cobertura for gates and diffs: `--coverage --coverage-output-format cobertura`. Use
  `--coverage-settings <file>` for include and exclude rules.
- Gate with dotcov, the ANcpLua coverage gate for any Cobertura report:
  `dotcov test --min-line 90 --min-branch 80` (runs `dotnet test` with coverage into a fresh
  `TestResults/<run>`), or `dotcov check TestResults/ --min-line 90`. The verdict is in the exit
  code: 0 pass, 1 fail, 6 the test run itself failed.
- Never compute coverage or CRAP numbers in your head. Read them from the Cobertura report.

## 5. Writing tests (MSTest 4.x)

Read `references/mstest-v4-api.md` before writing assertions. The rules most often broken:

- `[TestClass]` classes are `sealed`. Use the constructor for setup that is synchronous, and
  `[TestInitialize]` only for async setup.
- Exceptions: `Assert.ThrowsExactly<T>(() => ...)` or `Assert.Throws<T>` (derived types allowed);
  the async forms must be awaited. `[ExpectedException]` and `Assert.ThrowsException` are removed
  in v4.
- Type checks: `var typed = Assert.IsInstanceOfType<T>(value);` returns the cast value (v4).
- Collections: `Assert.HasCount`, `IsEmpty`, `IsNotEmpty`, `Contains`, `DoesNotContain`,
  `ContainsSingle`, not `Assert.IsTrue(list.Count == n)`.
- `Assert.AreEqual(expected, actual)`: the expected value comes first.
- Data: `[TestMethod]` with `[DataRow(...)]` (`[DataTestMethod]` is obsolete); `[DynamicData]` with
  `IEnumerable<(T1, T2)>` tuples or `TestDataRow<T>` for display names, not `object[]`.
- Cancellation: take `TestContext` through the constructor and pass `TestContext.CancellationToken`.
  `[Timeout(..., CooperativeCancellation = true)]` stops the work instead of abandoning it.
- Platform-specific tests: `[OSCondition(OperatingSystems.Windows)]` instead of an `if` inside the
  test.
- Time and randomness: `TimeProvider`/`FakeTimeProvider` and seeded `Random`; never
  `DateTime.Now`, `Thread.Sleep` or `Task.Delay` as synchronization.
- `[Retry]` only for a test that depends on something external you can't control. A race in your
  own code is a bug, so fix it.
- v4 behavior: AppDomain isolation is off under MTP, `TreatDiscoveryWarningsAsErrors` is on,
  `ClassCleanup` runs at the end of its class, and `TestContext.TestName` throws in
  `AssemblyInitialize`/`ClassInitialize`.

Analyzer mode: `<MSTestAnalysisMode>Recommended</MSTestAnalysisMode>` escalates suggestions to
warnings (MSTEST0003 and MSTEST0043 become errors). Fix diagnostics instead of suppressing them.

## 6. Reviewing test code

Apply `references/test-smells.md`, a grep-able catalog of smells with fixes. Report each finding
as `file:line | smell | evidence | fix`. Severity is about false confidence first: a test that can
pass while the behavior is broken (missing `await` on an async assert, assertions in a `catch`, no
assertion, a self-comparison) outranks style.

## 7. Done means

1. `dotnet build -c Release` with zero warnings, including MSTEST analyzers.
2. `dotnet test` in native mode, with the exit code read directly and the executed test count
   compared with the expectation (new tests raise it).
3. Coverage checked through dotcov or Cobertura when coverage was part of the request.
