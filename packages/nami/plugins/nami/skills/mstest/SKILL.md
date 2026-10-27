---
name: mstest
description: Write tests with MSTest 4.5.1 APIs on Microsoft.Testing.Platform, covering precise assertions, soft assertions, combinatorial data, dependencies, resource locks, execution conditions and host-owned dependency injection. Use when writing new tests or modernizing existing ones.
---

# Writing modern MSTest tests

Checked against `microsoft/testfx` at `v4.5.1` and the published NuGet packages. Version notes give the release that introduced an API; "4.5" means 4.5.1, since no 4.5.0 package was published. APIs marked experimental need `#pragma warning disable MSTESTEXP`.

Before using an API not shown here, search [`references/public-api.md`](references/public-api.md) for its type or member name. It lists the public symbols from the configured framework, framework extensions and hosting API files. "Introduced" means first seen among the compared releases, not necessarily the API's original release.

## Integration and end-to-end resource ownership

Use the same lifecycle APIs for unit, integration and end-to-end tests. Choose the cleanup scope from the resource's owner: `await using` within a test, `IAsyncDisposable` or `[TestCleanup]` for a test instance, `[ClassCleanup]` for a shared class fixture, and `[AssemblyCleanup]` for an assembly fixture. A consuming test must not dispose a resource owned by its class or assembly.

Read [Lifecycle and cleanup](../fixture-scope/references/mstest-lifecycle.md) when adding or changing fixtures. It covers failure during setup, cleanup order, shared assembly providers, temporary files and the distinction between an AOT test host and an AOT application under test. Preserve the repository's existing fixture owners and file-retention policy. Do not introduce a separate diagnostics collection or retention system as part of a cleanup change.

## Test classes

Use `sealed` for concrete test classes that are not intended as bases, put `[TestClass]` on each one, and take `TestContext` through the primary constructor when appropriate. Pass `context.CancellationToken` to calls that accept a token (`MSTEST0049`).

```csharp
[TestClass]
public sealed class PaymentGatewayTests(TestContext context)
{
    private readonly FakeTimeProvider _time = new(new DateTimeOffset(2026, 10, 23, 12, 0, 0, TimeSpan.Zero));

    [TestMethod]
    public async Task AuthorizeAsync_ValidCard_ReturnsApprovedReceipt()
    {
        var sut = new PaymentGateway(_time);

        var receipt = await sut.AuthorizeAsync(amount: 49.99m, context.CancellationToken);

        using (Assert.Scope()) // experimental
        {
            Assert.IsTrue(receipt.IsApproved);
            Assert.AreEqual(49.99m, receipt.AuthorizedAmount);
            Assert.AreEqual(_time.GetUtcNow(), receipt.Timestamp);
        }
    }
}
```

`Assert.Scope()` collects every failure inside the block and reports them together at the end.

## Services from a host (`MSTest.Extensions.Hosting`, prerelease, experimental)

The package is only published as `4.5.1-alpha.26507.8` and pulls in `Microsoft.Testing.Extensions.Hosting` 1.0.0-alpha. It builds test class instances from an `IServiceProvider`, with one service scope per test invocation (every data row and every retry gets its own). You supply a static host factory and point MSBuild at it; the generated entry point does the rest, so there is no `Main` to write.

```xml
<PropertyGroup>
  <TestingPlatformHostFactory>TestHost.CreateHost</TestingPlatformHostFactory>
</PropertyGroup>
```

```csharp
internal static class TestHost
{
    public static Task<IHost> CreateHost()
    {
        HostApplicationBuilder builder = Host.CreateApplicationBuilder();
        builder.Services.AddScoped<InvoiceService>();
        builder.Services.AddMSTestTestClassInjection();
        return Task.FromResult(builder.Build());
    }
}

[TestClass]
public sealed class InvoiceServiceTests(InvoiceService service, TestContext context)
{
    [TestMethod]
    public async Task ExportAsync_WritesPdf()
    {
        string path = await service.ExportInvoiceAsync(invoiceId: 42, context.CancellationToken);

        context.AddResultFile(path);
        Assert.IsTrue(File.Exists(path));
    }
}
```

MSTest passes `TestContext` itself; it is not resolved from the container, and the parameter is optional. Injection is not supported with `PublishAot`, `RunAOTCompilation`, `EnableMSTestSourceGeneration` or browser-wasm. Using it there is the error `MSTEST0088`.

These restrictions apply to the test host. A managed E2E test host can launch a Native AOT application. After cleanup, MSTest disposes the test instance and then its DI scope; the application still owns the root host and service provider. Keep an existing fixture architecture unless host injection solves a concrete need.

## Assertions

The highest priority is the most specific **MSTest 4.5.1** assertion that proves
the entire intended contract and gives useful failure evidence. Read
[MSTest assertion semantics](../mstest-assertions/SKILL.md) before replacing or
selecting an assertion. Its executable examples cover identity, equality,
ordering, multiplicity, strict graph comparison and NativeAOT restrictions.
Improve a weaker assertion directly, but do not add new requirements merely
because the current implementation satisfies them. Preserving an owner value
does not by itself promise the same object instance. Validate the affected change
and finish; an ordinary assertion edit does not require a new full-suite audit.

Use `Assert.*` instead of `CollectionAssert` (`MSTEST0068`) and `StringAssert`
(`MSTEST0046`). Do not offer those legacy APIs, generic Boolean expressions or
count-only checks when a 4.5.1 assertion describes the required behavior more
precisely. A real Boolean result still belongs in `IsTrue`/`IsFalse`; operator
contracts must retain their operator semantics. Check the actual package asset
rather than copying an older-version fallback.

```csharp
// Order matters by default; on modern .NET there are Span overloads.
Assert.AreSequenceEqual(expected, actual);
Assert.AreSequenceEqual(expected, actual, SequenceOrder.InAnyOrder); // replaces CollectionAssert.AreEquivalent

// A graph contract: strict rejects extra actual members/keys.
// An eligible IEquatable<T> on the static type still stops recursive traversal.
Assert.AreEquivalent(expectedOrder, actualOrder, strict: true);

// Predicate first, collection second; returns the matching item.
Customer vip = Assert.ContainsSingle(static c => c.IsVip, customers);

Assert.ContainsAll(expectedSubset, actual);
Assert.AreAllNotNull(actual);
Assert.AreAllDistinct(actual);
Assert.AreAllOfType<ProcessedEvent>(events);

Assert.IsInRange(minValue: 1, maxValue: 100, score);
Assert.IsPositive(balanceDelta);
await Assert.ThrowsExactlyAsync<InvalidOperationException>(() => sut.CommitAsync(context.CancellationToken));
```

For independent status and content requirements, use their specific assertions:

```csharp
Assert.AreEqual(200, response.StatusCode);
Assert.IsNotEmpty(response.Items);
```

Reserve `Assert.That(() => ...)` expression diagnostics for a compound contract
better expressed as a whole. It is a C# 14 extension member; the static spelling
is `AssertExtensions.That(...)`. In 4.5.1 that expression API requires dynamic
code. It is different from the `Assert.That` singleton for custom extensions.
`AreEquivalent`/`AreNotEquivalent` also have trimming and dynamic-code requirements;
use the assertion skill's typed alternatives when the test host must support AOT.
Do not weaken the behavioral contract to avoid a diagnostic.

To control how a type appears in failure messages, register a formatter (experimental). It returns an `IDisposable` that removes it again:

```csharp
using IDisposable _ = Assert.AddValueFormatter<Money>(static m => $"{m.Amount} {m.Currency}");
```

## Combinatorial data (4.4)

`[CombinatorialData]` goes next to `[TestMethod]` and runs every combination of the parameter values. No extra package is needed.

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting.Combinatorial;

[TestMethod]
[CombinatorialData]
public void Compress(
    [CombinatorialValues("gzip", "br")] string encoding,
    [CombinatorialRange(from: 1, to: 9, step: 4)] int level,
    [CombinatorialRandomData(Count = 2, Minimum = 128, Maximum = 4096, Seed = 42)] int payloadSize,
    bool flushFinalBlock)
{
    // ...
}
```

A `bool` parameter without an attribute expands to `true` and `false`. An `int` parameter without an attribute expands only to `0` and `1`, so give it values explicitly.

## Ordering with `[DependsOn]` (4.4)

Keep parallelization on and declare the order the tests need. This works on MTP and VSTest, also across classes in the same assembly.

```csharp
[TestMethod]
public void CreateSchema() { /* ... */ }

[TestMethod]
[DependsOn(nameof(CreateSchema))]
public void SeedData() { /* ... */ }
```

If the prerequisite fails, the dependent test is skipped, and the skip propagates. Set `ProceedOnFailure = true` to run it anyway. Further overloads are `[DependsOn(typeof(OtherTests))]` (every test of that class) and `[DependsOn(typeof(OtherTests), nameof(OtherTests.Method))]`. On MTP the same edges can be declared in `testconfig.json` under `mstest.execution.dependencies`. `MSTEST0078` reports invalid targets and cycles.

## Process-wide state under parallelization (4.4)

Lock global state with the constants in `WellKnownResources` (`EnvironmentVariables`, `CurrentDirectory`, `Console`). The default mode is `ReadWrite`; tests that only read can use `Mode = ResourceAccessMode.Read`.

```csharp
[TestMethod]
[ResourceLock(WellKnownResources.EnvironmentVariables)]
public void ReadsTenantModeFromEnvironment()
{
    Environment.SetEnvironmentVariable("TENANT_MODE", "Isolated");
    Assert.AreEqual("Isolated", Environment.GetEnvironmentVariable("TENANT_MODE"));
}
```

Culture changes have no constant, so use `[DoNotParallelize]` for them (`MSTEST0076`). For files, use `TestContext.TestTempDirectory` instead of fixed paths (`MSTEST0077`).

## Execution conditions

Declare skip conditions as attributes instead of checking at the start of the test:

- `[OSCondition(OperatingSystems.Linux)]` (`MSTEST0061`)
- `[ArchitectureCondition(TestArchitectures.Arm64)]` (`MSTEST0079`)
- `[CICondition(ConditionMode.Include)]` (`MSTEST0080`)
- `[ExecutableCondition("docker")]` checks that the executable is on `PATH`; `[ExecutableCondition("git", "--version", TimeoutSeconds = 5)]` checks that the command succeeds (`MSTEST0083`).

If a test carries `[SupportedOSPlatform]`, add a matching `[OSCondition]` as well (`MSTEST0084`).

A programmatic assembly-wide filter is registered with `[assembly: TestFilterProvider<FastSuiteFilter>()]` (4.4, modern .NET, experimental). The filter type implements `ITestFilter` (`MSTEST0081`).

## `testconfig.json`

```json
{
  "$schema": "https://raw.githubusercontent.com/microsoft/testfx/v4.5.1/docs/testconfig.schema.json",
  "mstest": {
    "output": {
      "captureTrace": "Live"
    },
    "execution": {
      "captureAssertionFailureDiagnostics": true
    }
  }
}
```

- `output.captureTrace` takes `None`, `Result` or `Live` (4.4); `Live` streams console and trace output while the test runs. `true` and `false` still work and mean `Result` and `None`.
- `execution.captureAssertionFailureDiagnostics` (4.5, default `false`) writes up to three JSON snapshots per failed attempt (`mstest-assertion-failure-state-attempt-*-invocation-*-capture-*.json`) and attaches them to the failed result. It does nothing under Native AOT, on browser/WASI or on UWP/WinUI.
- Check JSON keys against the pinned schema, not a copied `.runsettings` table. `captureOutput`, `execution.considerFixturesAsSpecialTests` and `execution.treatClassAndAssemblyCleanupWarningsAsErrors` are not properties in that 4.5.1 schema. See the [configuration notes](../fixture-scope/references/mstest-lifecycle.md#configuration-and-version-checks).

For suite reviews, use the local [anti-pattern reference](references/antipatterns.md). For resource ownership, use the [fixture-scope skill](../fixture-scope/SKILL.md).
