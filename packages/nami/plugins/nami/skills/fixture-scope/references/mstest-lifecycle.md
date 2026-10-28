# MSTest 4.5.1 lifecycle and cleanup

Integration and end-to-end tests use the ordinary MSTest lifecycle. Scope cleanup to the resource's lifetime, and preserve the repository's existing ownership rules. This guide does not prescribe cleanup time limits or a new test-artifact system.

## Choose one owner

| Resource lifetime | Owner and cleanup |
|---|---|
| One operation or test body | Local `using` / `await using` |
| One test-class instance | `IDisposable`, `IAsyncDisposable`, or `[TestCleanup]` |
| One test class, shared by its tests | `[ClassInitialize]` and `[ClassCleanup]` |
| One test assembly, shared by its classes | `[AssemblyInitialize]` and `[AssemblyCleanup]` |
| A common action after every test in an assembly | `[GlobalTestCleanup]`, not an assembly-wide resource owner |

A class fixture is created once and released after the class's tests. Consuming tests borrow it; they do not dispose it. Existing helpers such as Nami's `SharedFixture<T>` can implement this ownership, but `SharedFixture<T>` is not a built-in MSTest type. Shared mutable state still requires isolation or an explicitly ordered scenario.

MSTest 4 runs `[ClassCleanup]` at the end of the class. The old `ClassCleanupBehavior.EndOfAssembly` pattern is gone; an assembly-owned resource belongs in `[AssemblyCleanup]`.

## Signatures and execution order

- `[TestCleanup]`: public instance method, no parameters, returning `void`, `Task` or `ValueTask`.
- `[ClassCleanup]` / `[AssemblyCleanup]`: public static method returning `void`, `Task` or `ValueTask`, with zero parameters or one `TestContext` parameter.
- `[GlobalTestCleanup]`: public static method returning `void`, `Task` or `ValueTask`, with exactly one `TestContext` parameter, in a `[TestClass]`.

The per-test sequence is:

```text
Construct test instance and inject TestContext
GlobalTestInitialize
TestInitialize (base to derived)
Test method
Update TestContext outcome
TestCleanup (derived to base)
GlobalTestCleanup
IAsyncDisposable.DisposeAsync
IDisposable.Dispose
```

Multiple global cleanup methods have no guaranteed order. Avoid registering both a cleanup hook and disposal to independently release the same resource. A hook that needs an open connection or process must run before the owning disposal closes it.

Source: [Microsoft lifecycle documentation](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-lifecycle).

## Failure during setup or cleanup

A failed constructor leaves no completed test instance for MSTest to clean up. Keep allocation-heavy setup out of constructors, or release already acquired resources before rethrowing. After a failure in `[TestInitialize]`, MSTest still runs test cleanup and disposal, so those methods must tolerate partially initialized state.

Await asynchronous cleanup. Do not swallow failures or retry until a test appears to pass. If a fixture owns several independent resources, attempt to release all of them and preserve the failures. Stop owned child processes and await their exit before deleting directories they may still write to.

Since MSTest 4.2, failures in class and assembly cleanup are reported as separate results. They must remain visible. Successful disposal cannot be guaranteed after the test process is forcibly terminated; retain an existing external owner for abandoned runs where the repository provides one.

Source: [Microsoft lifecycle documentation](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-lifecycle).

## Shared assembly fixtures and hosting

`[assembly: AssemblyFixtureProvider(typeof(SharedAssemblyFixtures))]` lets multiple test projects reuse a type's `[AssemblyInitialize]` and `[AssemblyCleanup]` methods. Each consuming assembly runs its own lifecycle; this does not create one shared resource across different test processes. Use it when there is actual duplicated assembly setup, not as a replacement for class fixtures.

Provider discovery is skipped when dynamic code is unavailable, including Native AOT test hosts. Declare assembly hooks in the test assembly in that case.

`MSTest.Extensions.Hosting` is an optional prerelease integration. `AddMSTestTestClassInjection()` provides a DI scope per invocation, data row and retry. The test instance is disposed before that scope; the application owns the root host and provider. Injection does not support an AOT test host, browser-wasm or MSTest source generation. A managed E2E host launching a Native AOT executable is a different situation and is not excluded by those restrictions.

Sources: [Lifecycle and hosting](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-lifecycle), [4.5.1-tagged changelog](https://github.com/microsoft/testfx/blob/v4.5.1/docs/Changelog.md).

## Temporary files and optional diagnostics

`TestContext.TestTempDirectory` (4.4) is created lazily and belongs to one test execution, including each data row. It returns `null` in class and assembly lifecycle methods. Use a separately owned directory for a shared fixture.

MSTest normally deletes a passing test's directory and retains a non-passing test's directory. Result attachments and `MSTEST_TEST_TEMP_DIRECTORY_RETAIN` can also cause retention. Automatic deletion is best effort; it is not a bounded-retention or abandoned-run recovery policy.

Here, diagnostics simply means files such as process output or a failed request that help explain a test failure. Attach an existing useful file with `context.AddResultFile(path)` when needed. Do not add mandatory collection, archives or new retention machinery just to implement cleanup. Keep the repository's existing rules for removing workspaces and retaining failed-run files.

`AddResultFile` predates 4.5.1. The newer change preserves attachments for deferred MTP reporters after deployment cleanup; it does not make arbitrary file deletion safe immediately after registering an attachment.

Sources: [TestContext at v4.5.1](https://github.com/microsoft/testfx/blob/v4.5.1/src/TestFramework/TestFramework.Extensions/TestContext.cs), [TestContext guide](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-testcontext), [changelog](https://github.com/microsoft/testfx/blob/v4.5.1/docs/Changelog.md).

## Configuration and version checks

Use the [versioned 4.5.1 JSON schema](https://github.com/microsoft/testfx/blob/v4.5.1/docs/testconfig.schema.json) for configuration names:

| Imported claim | Verified guidance |
|---|---|
| `"captureOutput": "Live"` | Use `mstest.output.captureTrace`; `None`, `Result` and `Live` are accepted. Boolean values remain compatible. |
| `execution.considerFixturesAsSpecialTests` or `execution.treatClassAndAssemblyCleanupWarningsAsErrors` | Neither is defined in the 4.5.1 JSON schema. Do not infer JSON support from a `.runsettings` table. |
| All MSTest packages have a stable `4.5.1` version | `MSTest.Extensions.Hosting` is published as `4.5.1-alpha.26507.8`; it is optional and experimental. |
| Native application under test prevents hosting or fixture providers | Check the test host's build mode and the feature's own restrictions. |

The [generated API table](https://github.com/ANcpLua/ancplua-dotnet/blob/main/packages/mstest-extensions/skills/mstest/references/public-api.md) describes symbols from the configured source files. Its first-seen version is relative to the compared releases. It does not establish JSON keys, package publication versions, lifecycle behavior or target compatibility; use the sources above for those contracts.

Upstream API-directory names are library targets, not the consumer's SDK version. Nami uses SDK `11.0.100-rc.3.26522.148` and targets `net11.0`; its resolved MSTest 4.5.1 assets are `net9.0`. The generator therefore reads the common and `PublicAPI/net9.0` extension files. This does not retarget Nami to .NET 9. Upstream declares `net8.0;net9.0` for its modern .NET builds in [Directory.Build.props](https://github.com/microsoft/testfx/blob/v4.5.1/Directory.Build.props); there is no dedicated `PublicAPI/net11.0` directory in that release.
