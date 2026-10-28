# Known version evidence

Inspected on 2026-10-15. These snapshots guide lookups; they are not supported
version limits or guarantees for later releases. Use
[version resolution](version-resolution.md) for the current consumer.

| Framework / adapter | MTP with matching SDK | Package repository commit |
| --- | --- | --- |
| 4.4.1 | 2.4.1 | `9a14d19cb8ef1ec6a2aae81d4223a09190f96593` |
| 4.5.1 | 2.5.1 | `0bf77e3aedbf86f1fa16220bc951d3b52ba56763` |

The supplied [API delta](https://github.com/ANcpLua/MSTest-4.4.1/blob/591f0cda03de14f908a337f97b114f764704dd68/delta/4.5.1/api.md)
compares upstream v4.4.1 and v4.5.1. Its branch still pins the example SDK to
4.4.1, so it does not establish 4.5.1 execution. Published packages and their
commits were resolved separately. The covered public surfaces have additions
and no removals; behavior and packaging also changed.

Lifecycle and global-state details rechecked on 2026-10-17 against the installed
4.5.1 package and its recorded commit: synchronous versus async ownership,
lock acquisition before test-instance construction, invocation-based analyzer
visibility and per-test temporary-directory lifetime. Source pointers:
[parallel scheduler](https://github.com/microsoft/testfx/blob/0bf77e3aedbf86f1fa16220bc951d3b52ba56763/src/Adapter/MSTestAdapter.PlatformServices/Execution/TestExecutionManager.ParallelExecution.cs),
[mutation analyzer](https://github.com/microsoft/testfx/blob/0bf77e3aedbf86f1fa16220bc951d3b52ba56763/src/Analyzers/MSTest.Analyzers/UndeclaredProcessGlobalStateMutationAnalyzer.cs),
[TestContext](https://github.com/microsoft/testfx/blob/0bf77e3aedbf86f1fa16220bc951d3b52ba56763/src/TestFramework/TestFramework.Extensions/TestContext.cs),
and [hosting package contract](https://github.com/microsoft/testfx/blob/0bf77e3aedbf86f1fa16220bc951d3b52ba56763/src/Adapter/MSTest.Extensions.Hosting/PACKAGE.md).
See [lifecycle](lifecycle.md) for the task-specific guidance.

Relevant 4.5.1 changes:

- `TestContext.Current` is experimental (`MSTESTEXP`); the matching adapter
  establishes it around execution wrappers. It is absent from the inspected
  4.4.1 package. An internal override can declare the experimental dependency
  without suppressing diagnostics. The class-composition sample checks its token
  against the context injected into each test invocation.

- `DataRowAttribute` and `TestDataRow<T>` gain `ArgumentsDisplayName`, retaining
  the method name. Full `DisplayName` overrides have precedence according to
  each type's contract. Dynamic labels need an updated adapter. Automatically
  generated names also escape control characters differently.
- Optional, independently versioned prerelease `MSTest.Extensions.Hosting`
  provides `AddMSTestTestClassInjection` with `MSTESTEXP`. The application owns
  the host/root provider; each invocation, data row and retry receives a scope.
  The inspected integration excludes source generation, Native AOT and
  browser/AOT execution. Recheck restrictions for later versions.
- Built-in assertion diagnostics can be enabled with
  `CaptureAssertionFailureDiagnostics` /
  `mstest:execution:captureAssertionFailureDiagnostics`. Inspect this before
  implementing custom capture. Deferred attachment reporting and collection
  assertion behavior also have fixes despite unchanged signatures.
- Analyzer changes include hosting compatibility, duplicate data-row names and
  conflicting labels (`MSTEST0087`–`MSTEST0089`). Keep diagnostics enabled.
- MTP 2.5.1 adds optional hosting/configuration integration and experimental
  orchestration middleware. Middleware composes around one invocation, not a
  multi-run retry/shard operation. Resolve platform versions and `TPEXP`
  annotations separately from MSTest framework attributes.
- Windows UI automation and packaged-app APIs have optional dependencies and
  platform requirements; they are not defaults for a portable extension.

Sources: [upstream framework API at the package commit](https://github.com/microsoft/testfx/blob/0bf77e3aedbf86f1fa16220bc951d3b52ba56763/src/TestFramework/TestFramework/PublicAPI/PublicAPI.Shipped.txt),
the [API delta](https://github.com/ANcpLua/MSTest-4.4.1/blob/591f0cda03de14f908a337f97b114f764704dd68/delta/4.5.1/api.md),
and [release summary](https://github.com/ANcpLua/MSTest-4.4.1/blob/591f0cda03de14f908a337f97b114f764704dd68/delta/4.5.1/changelog.md).
Executable checks and limits are recorded in the repository README and the
[packaged capability evidence](executable-evidence.md), refreshed on 16 October
2026. API notes alone do not establish hosting, Native AOT or model evaluation.

Native invocation context and lazy assembly ownership were checked on 17 October
2026 against restored 4.5.1 packages and the
[architecture prototype lifecycle correction](https://github.com/ANcpLua/mstest-architecture-prototype/commit/bacb74e3f2fdb3f49110e71bbb91ac6fde3b2661).
That consumer evidence includes real service processes, discovery and unit-only
selection without a collector. It does not replace verification of another
consumer's resolved runner or establish new capability-verifier/AOT evidence.
