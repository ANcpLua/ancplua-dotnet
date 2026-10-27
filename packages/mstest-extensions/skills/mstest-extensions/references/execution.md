# Execution attributes and policies

## Wrap the framework invocation

For the async invocation API checked in 4.4.1 and 4.5.1, derive from
`TestMethodAttribute` and override
`Task<TestResult[]> ExecuteAsync(ITestMethod testMethod)`. For an attribute written
on a test method, expose optional `[CallerFilePath]` / `[CallerLineNumber]`
constructor parameters and forward those parameters to the base constructor.
The compiler captures the attribute's declaration site for discovery.
Prefer `await base.ExecuteAsync(testMethod)` for a method-level wrapper.
`ITestMethod.InvokeAsync` is a public invocation API for a deliberately distinct
executor; it is not needed to reproduce the base executor in an ordinary
decorator. For class composition, delegate to the supplied original attribute.

Never invoke `MethodInfo` directly: that bypasses MSTest's invocation handling.
An assertion failure can be represented by a returned `TestResult`; a
`try/catch` around the await is not sufficient to detect failed tests. Preserve
every result's outcome, exception, attachments, duration, and identity. Do not
replace results with newly constructed passing objects.

Use `[TestInitialize]`/`[TestCleanup]` for resource lifetime. A custom invocation
attribute is not a substitute for all runner scheduling and lifecycle hooks.
Keep invocation-local state local; do not retain mutable test state in attribute
instances.

For class-wide behavior, override
`TestClassAttribute.GetTestMethodAttribute(TestMethodAttribute)`. Compose around
the provided attribute so a method's own execution semantics survive; blindly
returning a new base attribute erases them. Use built-in STA attributes when
supported and needed instead of inventing a synchronization context or executor.
Verify platform support and continuation affinity separately.

### Source navigation belongs to discovery

Distinguish the declared test attribute from a wrapper created by
`GetTestMethodAttribute` for execution. In the inspected adapter, discovery
(`TypeEnumerator`) takes the source file and line from the **original declared
attribute**. MTP's node conversion exposes that location. The class-level
execution wrapper is created later and does not control navigation metadata.

Construct it with the behavior/dependencies it needs:

```csharp
public override TestMethodAttribute GetTestMethodAttribute(TestMethodAttribute original)
    => new ExecutionWrapperAttribute(original);
```

Do not pass `original.DeclaringFilePath` / `original.DeclaringLineNumber` into
that factory call solely to preserve IDE navigation. Do not add a ReSharper
`ExplicitCallerInfoArgument` suppression or an inspection exception to support
that unnecessary copy. Let optional caller parameters take their normal values;
retain constructor-to-base forwarding where the attribute/analyzer contract
requires it. An attribute actually declared on a test still needs its own
declaration-site capture.

Verify navigation through the real runner's JSON discovery output
(`--list-tests json` on the checked MTP versions), comparing `location.file`,
`lineStart`, and `lineEnd` with the original method attribute. A unit test that
only checks copied properties on a wrapper does not establish IDE navigation.
Keep testing original invocation semantics and failed results separately.
Recheck the adapter's discovery/conversion path when version evidence changes.

This distinction was verified in the
[architecture prototype correction](https://github.com/ANcpLua/mstest-architecture-prototype/commit/3d4acd28d28385455cde31b3d119d6b4f3a4ff04)
and is exercised by this repository's runner regression.

Check built-in assertion-failure diagnostics in the resolved version before
creating a capture wrapper; see [known version changes](version-notes.md).
Optional custom diagnostics can inspect results and append to `LogOutput`.
Contain failures from both capture and output so they cannot replace the test
failure. Keep cleanup failures visible. Test a failing body and broken diagnostic
capture through the actual adapter; check both the report and nonzero process
exit. Test successful invocation and data arguments too.

## Native invocation context and cancellation

The inspected 4.5.1 framework exposes experimental `TestContext.Current`, and its
matching adapter establishes that context around execution of a custom method
executor. This API is absent from the inspected 4.4.1 package. Resolve both the
framework and adapter before using it; do not infer runtime availability from a
signature alone. Outside a native invocation the property can be null.

An internal class-created wrapper can declare the dependency on its override:

```csharp
[Experimental("MSTESTEXP")]
public override async Task<TestResult[]> ExecuteAsync(ITestMethod method)
{
    var context = TestContext.Current
        ?? throw new InvalidOperationException(MissingInvocationContext);
    context.CancellationToken.ThrowIfCancellationRequested();
    return await original.ExecuteAsync(method);
}
```

Here `original` is the supplied method attribute and `MissingInvocationContext`
is an owned named diagnostic constant. Import `System.Diagnostics.CodeAnalysis`.
With the matching diagnostic ID, the declaration acknowledges the experimental
API inside that member without a warning suppression. Keep the concrete wrapper
internal: exposing experimental members publicly can require consumers to
acknowledge that dependency too. This is an API dependency declaration, not proof
that the API is stable. The repository's class-composition example checks the
native token against constructor-injected `TestContext` on 4.5.1.

Pass the invocation token through owned startup and evidence waits. Do not store
`TestContext` in process-wide state, inspect adapter-private fields, substitute
an assembly-initialization token for an invocation token, or add a compatibility
fallback that silently loses cancellation. On a version without this API, use
supported constructor/property injection in native lifecycle methods and make
any required consumer plumbing explicit. Cleanup still needs a bounded chance
to terminate and join resources after the invocation token is cancelled.

## Required verification and failure preservation

Keep original result arrays and objects. Evaluate every relevant result rather
than applying a class-wide verdict only to `results[^1]`. Preserve an empty array
without indexing it; an actual cleanup failure must still be reported.

After the original executor returns, evidence waits, verification and disposal
can each fail. Retain an existing assertion exception as the primary failure and
attach the infrastructure diagnostics; mark an otherwise passing result failed
when required verification or cleanup fails. If the executor itself throws,
retain its exception and stack while also reporting cleanup failures. A throwing
`finally` must not replace it. Suppressing errors is appropriate only for optional
best-effort diagnostics, never required evidence collection or resource cleanup.

For telemetry contracts, distinguish conformance, a measured violation and
insufficient evidence. Empty observations do not prove that a forbidden action
never happened. Declare which producers, calls, state changes or terminal events
the scenario requires. Matching HTTP client/server spans alone does not establish
that database spans, background work, logs or metrics have arrived. Wait on
explicit evidence with a deadline and cancellation. Metric predicates need a
producer identity, measurement window and appropriate baseline; metrics do not
inherently belong to one trace. Report what the observed scenario establishes.

## Constant strings and contracts

Prefer the installed framework's or domain library's named constants over copied
string values. For strings the extension owns, centralize stable contract names
in a small shared class: property-bag keys, event names, environment settings,
resource-lock identities and diagnostic markers. Reuse the same definitions at
production and consumption sites so a spelling change cannot silently disconnect
them. Extensions that exchange identifiers must reference one shared contract
definition/package, not maintain per-extension copies. In telemetry integrations,
prefer the resolved instrumentation/semantic
convention library's constants; do not duplicate its catalog locally.

Use `nameof` for dynamic-data member references and type-derived identifiers.
Keep protocol values exact, and preserve deliberately different data-row inputs
such as a hyphenated key and an underscored key. If the literal spelling is the
behavior under test, assert that spelling independently; importing the same
constant into both sides must not make a changed wire contract pass unnoticed.
A one-off descriptive assertion message need not become a global constant.

## Typed rule selection and repeatable policies

A domain policy can keep rule selection typed while using named constants for
its textual contracts. For example, this proposed attribute surface uses an enum,
not strings masquerading as enum values:

```csharp
public enum PolicyKind { Dependencies, Data }

[AttributeUsage(AttributeTargets.Method | AttributeTargets.Class,
    AllowMultiple = true, Inherited = false)]
public sealed class VerifyPolicyAttribute(PolicyKind family) : Attribute
{
    public PolicyKind Family { get; } = family;
}

public static class RuleDiagnosticCodes
{
    public const string DependencyViolation = "policy.dependencies.violation";
    public const string DataViolation = "policy.data.violation";
}
```

Place both policies on an existing test method:

```csharp
[TestMethod]
[VerifyPolicy(PolicyKind.Dependencies)]
[VerifyPolicy(PolicyKind.Data)]
```

`PolicyKind.Dependencies` and `PolicyKind.Data` are enum members. The diagnostic
codes are `const string` values. Keep those roles separate: do not use literal
family names, `.ToString()` or `nameof(PolicyKind.Dependencies)` as substitutes for
the typed argument. Reuse the same `PolicyKind` definition across extensions;
do not redeclare equivalent enums independently. If an external protocol needs
a string representation, map
the enum explicitly to its published or shared string constants at that boundary.

The policy marker above is an ordinary repeatable `Attribute`; it is not another
`TestMethodAttribute` or `TestClassAttribute`. One native executor, installed by
one class-level composition point or an existing supported method executor,
collects the policies, invokes the supplied original method attribute once and
evaluates both selected families. The consuming class still needs its native test
class declaration/composition. Do not stack competing executors, replace
`[TestMethod]`, invoke the test once per rule, or treat the two markers as two data
rows. Define class/method merging and duplicate-family behavior deliberately.
The snippet is a proposed domain surface, not an already implemented plugin API.

## Conditions

Start with a built-in condition when it fits. For a domain condition, derive from
`ConditionBaseAttribute`, pass `ConditionMode` to the base constructor, and
implement `GroupName` and `IsConditionMet`. Return the raw predicate:
`IsConditionMet` must not apply `Mode` itself. The framework handles include vs.
exclude. Conditions within one group are ORed; different groups are ANDed.

Make evaluation cheap and deterministic, with a useful `IgnoreMessage`. Default
to non-inherited attributes on classes/methods, matching the built-ins. Avoid
global environment mutations in parallel tests. Verify a false condition really
skips the body and a true one runs it. A skipped case is not evidence that the
tested behavior passed.

## Retry policies

Use `[Retry]` before writing a custom policy. `RetryBaseAttribute.ExecuteAsync`,
`RetryContext`, and `RetryResult` are experimental in the inspected versions and emit
`MSTESTEXP`; acknowledge that locally when the extension actually needs them.
The protected override returns `Task<RetryResult>`. Invoke
`retryContext.ExecuteTaskGetter()` for each retry and call `AddResult` with every
returned array. Return at least one retry attempt; the runner already made the
first attempt before entering this policy.

Inspect **all** results in an attempt. Define retryable outcomes, an attempt
limit, cancellation, delays, and idempotence explicitly. Failed/timed-out results
are different from an inconclusive result. Preserve `AllResults` rather than
fabricating success. MTP can expose superseded attempts; final reports and
VSTest have different reporting behavior. Process-level retries multiply
attribute-level attempts. Keep both disabled when measuring flakiness.

## Programmatic filtering

Register a concrete `ITestFilter` with a public parameterless constructor through
one assembly-level `TestFilterProvider` (the generic form was checked on modern
.NET with 4.4.1 and 4.5.1). Implement `Filter(TestFilterContext)` and deliberately choose
`TestFilterResult.Run`, `.Skip(reason)`, or `.Drop`. Dropping removes the result;
skipping reports it. This runs after command-line selection and before loading
the test class. Compose multiple strategies inside that one provider. The generic
registration is for modern .NET; use the non-generic form on .NET Framework.

The runner can call one provider concurrently, so keep filter state thread-safe.
Keep decisions independent of test-class initialization. A throwing filter
is an error, not a skip. Confirm experimental annotations and analyzer rules in
the installed version; current online SDK guidance can differ from package
metadata. Verify run/skip/drop and malformed registration with a real consumer
when implementing a filter, rather than merely calling `Filter` directly.

Sources: [execution control](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-controlling-execution),
[SDK](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-sdk),
and version-matched `ITestMethod`, `ConditionBaseAttribute`, `RetryResult`, and
`TestFilterProviderAttribute` in [source routes](sources.md).

The packaged [runner evidence](executable-evidence.md) checks these contracts
through the actual executable and TRX, including a throwing filter and joined
cooperative cancellation on each bounded retry attempt. A recoverable failed
attempt, an exhausted retry and a cancelled invocation are separate outcomes.
Do not retry a cancelled operation indefinitely or turn its failure into a skip.
