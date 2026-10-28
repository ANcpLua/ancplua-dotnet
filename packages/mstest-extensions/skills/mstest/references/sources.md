# Source routes

Read one relevant topic first. Use the consumer's package versions to interpret
it, and follow another source only for an unresolved question.

| Topic | Official documentation |
| --- | --- |
| Test signatures and attributes | [Writing tests](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests) |
| Data rows, typed dynamic data, custom providers, combinations | [Data-driven tests](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-data-driven) |
| Assertions and `Assert.That` extensions | [Assertions](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-assertions) |
| Setup, cleanup, global fixtures | [Lifecycle](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-lifecycle) |
| Context, cancellation, diagnostics | [TestContext](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-testcontext) |
| Conditions, retries, parallelism, dependencies | [Execution control](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-controlling-execution) |
| SDK, MTP extensions, source generation | [MSTest.Sdk](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-sdk) |
| Runner options and configuration | [MSTest runner](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-runner-intro) |
| Analyzer diagnostics | [MSTest analyzers](https://learn.microsoft.com/en-us/dotnet/core/testing/mstest-analyzers/overview) |

Start with [version resolution](version-resolution.md). For exact signatures,
inspect the resolved assemblies and matching framework source; XML documentation
also includes non-public members and is not a complete public API contract. The
framework and adapter live in [microsoft/testfx](https://github.com/microsoft/testfx).
Use the package `.nuspec` repository commit to resolve provenance; do not assume
that the default branch matches an installed release. Read that commit's
`PublicAPI.Shipped.txt` and `PublicAPI.Unshipped.txt` for the relevant assembly
and target surface. Version/commit evidence belongs in
[known release notes](version-notes.md), not a permanent lookup URL to one release.

Useful symbols to search by task:

- Data: `ITestDataSource`, `DynamicDataAttribute`, `TestDataRow`,
  `CombinatorialDataAttribute`, `ICombinatorialValuesProvider`.
- Invocation: `TestMethodAttribute`, `ITestMethod`, `TestClassAttribute`,
  `ConditionBaseAttribute`, `RetryBaseAttribute`, `ITestFilter`.
- Lifecycle: `TestContext`, `ResourceLockAttribute`,
  `AssemblyFixtureProviderAttribute`, `GlobalTestInitializeAttribute`,
  `AddMSTestTestClassInjection` when a hosting integration is installed.
- Generation: `EnableMSTestSourceGeneration`, `MSTest.SourceGeneration`, `AOTSG`.

A local showcase supplies examples and test cases, not proof of framework
internals. Its intentionally invalid/failing projects may also suppress analyzer
diagnostics for demonstration; those suppressions are not consumer defaults.

If documentation and installed code differ, use the consumer's resolved API and
state any unresolved behavior. Optional packages can have independent versions
and prerelease status. A stable MSTest version does not make all of its extensions
stable or installed. Do not upgrade a consumer merely to make a sample compile.
