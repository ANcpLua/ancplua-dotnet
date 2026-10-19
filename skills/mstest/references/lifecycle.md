# Lifecycle, isolation and parallelism (MSTest 4.5.1)

Sources: https://learn.microsoft.com/dotnet/core/testing/unit-testing-mstest-writing-tests-lifecycle,
https://learn.microsoft.com/dotnet/core/testing/unit-testing-mstest-writing-tests-controlling-execution,
and `fixtures/mstest-probe/ApiSurface.cs`, which compiles every API named here.

## Order

Stages, outermost first: assembly (`[AssemblyInitialize]`/`[AssemblyCleanup]`, once), class
(`[ClassInitialize]`/`[ClassCleanup]`, once per class; cleanup always runs at the end of its class in
v4), global test (`[GlobalTestInitialize]`/`[GlobalTestCleanup]`, around every test in the assembly),
test.

Per test, and again for every data row and retry attempt:

1. Constructor.
2. `TestContext` property set (if declared as a property).
3. Every `[GlobalTestInitialize]` method.
4. `[TestInitialize]`, base class first.
5. The test method (async tests are awaited; there is no `SynchronizationContext`).
6. The outcome is written to `TestContext`.
7. `[TestCleanup]`, derived class first.
8. Every `[GlobalTestCleanup]` method.
9. `DisposeAsync`, then `Dispose`.

## When setup fails

| Fails in | Cleanup and Dispose |
|---|---|
| Constructor | don't run, because no instance exists; roll back partial acquisition inside the constructor |
| `[TestInitialize]` | still run, so cleanup code must tolerate half-initialized state |

Constructor or `[TestInitialize]`?

- The constructor allows `readonly` fields but can't be async or time out.
- `[TestInitialize]` can be async and honors `[Timeout]`.
- Use both when you need to: the constructor for synchronous fields, `[TestInitialize]` for async
  setup that depends on them.

## Global test hooks (3.10+)

- `public static`, returning `void`, `Task` or `ValueTask`, with exactly one `TestContext` parameter,
  in a `[TestClass]`.
- Several are allowed; their relative order is undefined, so they must not depend on each other.
- Since 4.4 they honor `[Timeout]` and the global fixture timeout settings.
- They run around every test: keep them cheap.

## Parallelism

- Enable once per assembly: `[assembly: Parallelize(Scope = ExecutionScope.MethodLevel)]`
  (`ClassLevel` runs classes in parallel and the methods of one class in sequence).
- `[DoNotParallelize]` moves a test into the sequential phase. It's a last resort.
- `[ResourceLock("key")]` serializes only the tests that name the same key:
  - Keys compare ordinal and case-sensitive. Use `const` fields (MSTEST0073).
  - The default mode is exclusive. `Mode = ResourceAccessMode.Read` lets readers share.
  - Process state has built-in keys: `WellKnownResources.EnvironmentVariables`,
    `WellKnownResources.CurrentDirectory`, `WellKnownResources.Console`.
  - With `MethodLevel` a lock covers the test plus its initialize and cleanup. With `ClassLevel` the
    class holds the union of its locks for its whole lifecycle.
  - Locks coordinate tests inside one test assembly only, not across processes or machines.
  - Locks do nothing when parallelization is off, and `[DoNotParallelize]` overrides them.
- Isolation analyzers worth enabling (4.4+): MSTEST0074 (a test mutating process-global state
  should declare a lock), MSTEST0076 (process-wide culture changes), MSTEST0077 (shared file system
  paths). MSTEST0082 flags base and derived test classes compiled against different MSTest majors.

## Per-test files

`TestContext.TestTempDirectory` gives a directory unique to the current test and data row, created
on first access. Use it instead of `Path.GetTempPath()` plus a hand-made name, and never share a
fixed path between tests.

## Timeouts and cancellation

- `[Timeout(ms, CooperativeCancellation = true)]` cancels `TestContext.CancellationToken` when the
  time is up. It doesn't stop code that ignores the token, so pass the token into every awaited call.
- When an operation is cancelled, wait for it to finish before disposing the resources it uses.
  Otherwise cleanup races the still-running work.

## Host-created test classes (experimental)

MSTest 4.5's `MSTest.Extensions.Hosting` (`AddMSTestTestClassInjection`, diagnostic `MSTESTEXP`) lets a
`Microsoft.Extensions.Hosting` container construct test classes with one DI scope per invocation,
data row and retry. It's reflection-based: no Native AOT and no source generation (MSTEST0088, an
error under `Recommended`).
