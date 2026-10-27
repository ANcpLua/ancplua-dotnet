# Lifecycle, resources, and async isolation

## Order, setup and signatures

In the inspected 4.4.1 and 4.5.1 versions, the normal lifecycle is:

```text
AssemblyInitialize → ClassInitialize
→ constructor → TestContext property injection (if present)
→ GlobalTestInitialize → TestInitialize (base → derived) → test
→ TestContext outcome update
→ TestCleanup (derived → base) → GlobalTestCleanup
→ DisposeAsync → Dispose → ClassCleanup → AssemblyCleanup
```

The test-level portion runs separately for every data row. Ordering among
multiple global initializers, or among multiple global cleanups, is unspecified;
their positions around the per-test hooks are defined. Do not build dependencies
between global methods. Global fixtures were introduced in 3.10; their timeout
attributes and dedicated timeout settings are supported from 4.4.

Use constructors for synchronous initialization of `readonly` fields, and
`TestInitialize` for asynchronous setup or fixture timeouts. Combining both is
supported. `MSTEST0019` and `MSTEST0020` are opposing, optional style preferences,
not a prohibition on combining them. Async setup/cleanup can return `Task` or
`ValueTask` in the inspected versions. Roll back partial acquisition inside its
helper: a constructor failure leaves no completed instance for test cleanup or
disposal. A `TestInitialize` failure still runs cleanup and disposal.

Match disposal to the resource: synchronous restoration belongs in `Dispose` or
a synchronous cleanup hook; awaited shutdown belongs in `DisposeAsync` or an
async cleanup hook. Returning a completed `ValueTask` solely to make synchronous
environment/console setup appear asynchronous adds no capability. A genuinely
async lifecycle may still have a synchronous completion path. The inspected
MSTest framework has no test-class `IAsyncInitializer` or `IAsyncLifetime`
contract; do not import another framework's lifecycle interfaces.

MSTest supports `TestContext` injection through the test-class constructor in the
inspected versions, or the supported property pattern. Obtain cooperative cancellation
from `TestContext.CancellationToken`; do not assume arbitrary test-method token
injection. Thread it into owned operations. Inspect
`CurrentTestOutcome` in cleanup for failure diagnostics and use context output or
result attachments while their data remains available.

Class/assembly fixture methods are `public static` and return `void`, `Task`, or
`ValueTask` (the latter from 3.3). Initializers take one `TestContext`; cleanups
take none or one (from 3.8). Ordinary local declarations live in a `[TestClass]`,
with one initializer and cleanup per class or assembly respectively. In MSTest 4,
class cleanup occurs at the end of the class; do not transplant older
`ClassCleanupBehavior` examples. From 4.2, class/assembly cleanup failures have
separate results; include those results in verification. Global fixture methods
are `public static`, return the same supported types, and take exactly one
`TestContext`. Choose the narrowest scope that owns the resource.

For reusable assembly setup, inspect `AssemblyFixtureProviderAttribute` in the
installed adapter before choosing registration placement. Introduced in 4.3,
it lets a shared library advertise fixture methods to consuming assemblies;
the provider type does not need `[TestClass]`. Multiple provider types can
compose assembly fixtures, so the local one-per-assembly rule is not a limit of
one shared provider. Local assembly fixture declarations take precedence. From
4.4, provider discovery is skipped without dynamic-code support, including
Native AOT; declare fixtures directly in an AOT test assembly. Verify actual
initialization and cleanup in the consuming assembly instead of assuming that
referencing a fixture library is sufficient. Align the framework major version
of shared base/attribute libraries and consumers: v3/v4 attribute identity
mismatches can silently omit inherited tests and fixtures (`MSTEST0082`).

Async tests have no `SynchronizationContext` by default. UI tests and supported
STA execution with `UseSTASynchronizationContext = true` are exceptions; verify
the platform and continuation behavior before relying on thread affinity.

For timeouts, prefer `[Timeout(..., CooperativeCancellation = true)]` and flow
the native context token through cancellable work. MSTest signals cancellation
and awaits completion; code that ignores cancellation can still hang. A
noncooperative timeout can stop waiting while the operation continues. Neither
mode makes it safe to dispose dependencies before the original operation ends.

## Sequential work, asynchronous work and cancellation scope

`async` does not mean parallel. Await dependent steps in order: prepare the
resource, run the operation, observe its completion, verify its result, then
dispose. Starting verification or teardown before the producer has finished
creates races even when every method returns `Task`.

Run independent work concurrently only when its resources and ordering contract
allow it. Use `Task.WhenAll` to join every started operation; do not abandon
siblings when the first observation fails. Collect the failures needed for a
useful report. Avoid `Task.Run` for naturally asynchronous process/network I/O,
blocking `.Result`/`.Wait()`, and `async void`. A synchronous constructor is
appropriate for cheap synchronous setup; do not manufacture asynchronous work.

| Resource/work scope | Cancellation and ownership |
| --- | --- |
| One test invocation | Flow that invocation's native token to its operations; cleanup still terminates and joins them. |
| Shared immutable publication or startup | The fixture owns the work and its lifetime token; each test can cancel its wait without cancelling work required by other tests. |
| Mutable per-row child process or service partition | The row owns it; do not share it just because publication was shared. |
| Cleanup after cancellation | Use a separate bounded cleanup budget where needed, preserve the original failure, and wait for owned work to terminate. |

Do not let the first cancelled row permanently poison a shared `Lazy<Task<T>>`
or cancel another row's publication. Define the fixture's behavior after shared
startup failure explicitly. A timeout on a caller's wait does not stop shared
work; the fixture must still observe and join it at shutdown. Avoid automatically
retrying failed startup without a deliberate, tested retry policy.

## Lazy shared ownership and failure-safe cleanup

Automatic registration does not require eager infrastructure startup. An assembly
fixture can register a lightweight run-owned session, then start collectors,
servers or brokers only when a selected test needs them. Ordinary unit-test
selection should not gain an external-process dependency from loading a library.
Give caches and mutable resource registries an explicit consuming-run owner; a
process-wide singleton can couple assemblies and retain disposed resources.

In the inspected 4.5.1 adapter, lifecycle `TestContext.Properties` snapshots flow
reference-valued entries from assembly initialization into later native contexts.
Use a shared named constant for an owned property key. Do not assume that the
same dictionary or `TestContext` instance is reused. Verify propagation with the
consumer's runner, and explicitly compose registration when a local assembly
fixture overrides the library provider. This is version-specific evidence, not a
universal property-bag service locator.

Retain evidence before it becomes unavailable. Shutdown should attempt every
owned resource and attach already-written evidence even if stopping another
resource fails. Collect multiple failures without losing the original. Do not
place result attachment only after a successful shutdown await, or use an already
cancelled test token to prevent the essential stop-and-join work. Use owned,
unique artifact paths instead of a shared fixed filename that parallel runs can
overwrite. Restore any prior ambient invocation on scope exit and reject access
to a disposed scope. An ambient accessor identifies the invocation; it does not
own the assembly's resources.

## Hosting integration when available

Resolve the optional hosting package independently. In the inspected 4.5.1
release family, `AddMSTestTestClassInjection` connects a caller-owned host's
services to test-class construction, with a separate scope per invocation, row,
and retry. Ordinary test initialization/cleanup still applies. The application
owns the root host; the integration owns the invocation scope. The checked MTP
controller and worker each call the host factory, and discovery can bootstrap
a host too. Do not assume one host across all processes or allocate invocation
services during discovery. Verify each process's host lifetime and await scoped
async disposal after cleanup. The packaged [real-host probe](executable-evidence.md)
checks data-row and retry isolation with this ownership boundary.

The inspected integration is experimental and excludes source generation,
Native AOT and browser/AOT execution. Confirm current constraints and diagnostics
from the resolved package before using or rejecting it on a newer release.
`AddMSTestTestClassInjection` must be registered in the application-owned host
that actually runs MTP. An arbitrary `CreateHostBuilder` method is not that
connection, and `AllMicrosoft` does not supply constructor service injection by
itself. The package is separately versioned and prerelease in the inspected
4.5.1 source; scope its `MSTESTEXP` acknowledgment to the required code.
See [known version evidence](version-notes.md) for the source of these limits.

## Parallel execution and ownership

Declare a deliberate `[assembly: Parallelize(...)]` or
`[assembly: DoNotParallelize]` policy consistent with the repository, or use the
consumer's supported configuration mechanism. Do not declare duplicate source
attributes when MSBuild generates them. MSTest does not share TUnit's
parallel-by-default contract. Give each test its own workspace,
stream, mutable fixture, or server partition. Shared fixtures need immutable
state, separate per-test partitions, or synchronization.

`[DoNotParallelize]` coordinates only tests within the same assembly; it does
not isolate other assemblies or processes. The inspected runner defers these
tests until after that assembly's parallel set, but this scheduling order is an
implementation detail, not a public ordering contract.

When supported (introduced in 4.4), `[ResourceLock]` coordinates participating
tests in the same assembly. Reuse `WellKnownResources.EnvironmentVariables`,
`WellKnownResources.CurrentDirectory`, or `WellKnownResources.Console` for those
resources; use shared `const string` definitions for owned keys. Keys are ordinal
and case-sensitive; path-like keys do not establish parent/child locks. Default
access is exclusive; `ResourceAccessMode.Read` allows concurrent readers. Every
relevant reader and writer must participate. With class-level parallelization,
the runner combines class/method locks for the class lifecycle; with method-level
parallelization, locks cover each test's initialization and cleanup. Locks have
no effect when parallelization is disabled, and `DoNotParallelize` takes precedence.
These locks are not cross-process or cross-assembly locks.

Under method-level parallelization the scheduler takes the chunk's locks before
constructing the test instance. Instance constructors and field initializers are
therefore covered, as are initialization, execution, cleanup and disposal. That
guarantee does not cover discovery, static initialization that ran earlier or an
application host's bootstrap. Under class-level parallelization the chunk is the class;
method locks are combined for that class, not held just around their methods.

### Process-global mutations and analyzer visibility

For environment variables and console streams, save the prior value under the
appropriate exclusive lock, restore it before releasing the lock and dispose
only resources the fixture creates. Reader locks coordinate only with other
participating readers/writers; reading an unchanged ambient environment does
not establish that a configuration variable is absent. Prefer explicit inputs
when the actual behavior does not require process-global mutation.

In the inspected 4.5.1 analyzer, `MSTEST0074` examines mutation invocations in
recognized tests and fixtures; it does not trace arbitrary helper call graphs.
Encapsulated resource helpers can still be useful, but their callers need an
explicit matching lock/isolation contract. Do not hide mutations merely to
silence a diagnostic or assume that moving them into a helper transfers a lock.
Direct mutations in recognized lifecycle methods retain analyzer visibility.

The rule defaults to Info and activates when assembly parallelization is
syntactically enabled, or when `.editorconfig` sets
`mstest_parallel_safety_mode = always`. Parallelization supplied only by
runsettings or MSBuild may require that option for analysis. A diagnostic is
not necessarily a failing build; inspect the consumer's effective severity.

`MSTEST0076` concerns process-wide `DefaultThreadCurrentCulture` and
`DefaultThreadCurrentUICulture` mutations. On modern .NET, ambient
`CultureInfo.CurrentCulture`/`CurrentUICulture` flow with the execution context
and are not equivalent process-wide changes. Shared filesystem paths
(`MSTEST0077`), environment variables, the current directory and static caches
also need isolation. Assembly-local locks or `DoNotParallelize` cannot protect
process-global state from unrelated concurrently executing assemblies; use
separate processes when that boundary is required.

### Per-test temporary files

The inspected `TestContext.TestTempDirectory` is created lazily and gives each
test/data case its own directory. Prefer it for invocation-owned files when
supported by the resolved runner. It is unavailable outside a test, including
class/assembly fixtures. Passing tests normally remove it; failures, result
attachments inside it and `MSTEST_TEST_TEMP_DIRECTORY_RETAIN` can retain it.
That directory lifetime does not stop child work: close handles and join owned
operations/processes before framework cleanup. Shared class/assembly artifacts
need a separately owned workspace and lifetime.

Join owned threads and terminate/reap owned child processes before deleting
their workspace. On **.NET Framework**, MSTest 4 under MTP disables AppDomain
isolation by default; an abandoned foreground thread can therefore hang the
process instead of being aborted when the isolated AppDomain unloads. Modern
.NET does not provide that AppDomain unloading model either. Resource ownership
must not depend on the runner aborting threads.

## Actual async suspension

A completed `Task` is not a suspension test. Use a controllable dependency with
separate reached/resume signals and asynchronous continuations. Record that the
operation reached the intended point and is still pending; then resume it and
check its result. Prove cancellation in a separate case.

Always join the **original operation** before disposing its dependencies,
including when an observation/assertion fails. A `WaitAsync` timeout only ends
the wait; it does not stop that original operation. A timeout attribute also does
not make uncooperative code safe to dispose. Establish what terminates the whole
operation, not just its current stream read. Use an owned process with explicit
termination/reaping when a hard bound is required for uncooperative work.

For a finite cooperative copy, keep assertions after releasing and joining:

```csharp
var copying = source.CopyToAsync(destination, token);
bool wasPending;
try
{
    await Task.WhenAny(source.Paused, copying);
    wasPending = source.Paused.IsCompletedSuccessfully && !copying.IsCompleted;
}
finally
{
    source.Resume();
}
await copying;
Assert.IsTrue(wasPending);
```

`WhenAny` does not propagate the copy's exception; the final await does. This
observation block has no throwing assertions or independently cancelled wait.
If it gains them, move joining into cleanup and retain both observation and
cleanup failures, for example as an aggregate with the original first. Do not
let an exception from an awaited `finally` replace the original failure.

Only optional diagnostics may swallow errors. Resource cleanup and application
faults must stay visible. Check capture failure and sink failure independently;
non-blocking snapshots are preferable to promises of timeouts around arbitrary
logging.

Sources: [lifecycle](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-lifecycle),
[TestContext](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-testcontext),
[execution and parallelism](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-controlling-execution),
[v4 migration](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-migration-v3-v4),
[culture isolation](https://learn.microsoft.com/en-us/dotnet/core/testing/mstest-analyzers/mstest0076),
and the package contracts in [source routes](sources.md).
