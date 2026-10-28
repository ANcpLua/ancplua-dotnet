# Data providers and scenarios

Use `[TestMethod]` with `[DataRow]` for literals. Prefer `[DynamicData]` and a
public static source for computed cases; typed tuples keep the source internally
typed, while `TestDataRow<T>` can add display names, categories, and ignore
reasons. The method/source signature still needs analyzer and discovery checks.
Do not introduce obsolete `[DataTestMethod]` for new work.

Repeatable rule markers such as `[VerifyPolicy(PolicyKind.Dependencies)]` and
`[VerifyPolicy(PolicyKind.Data)]` select policies for an invocation; they are not data
rows. `PolicyKind` remains an enum. See
[typed rule selection](execution.md#typed-rule-selection-and-repeatable-policies).

Keep the method's parameter count and types consistent with every row; attribute
arguments must be valid compile-time attribute values. Reuse published or shared
named constants for fixed contract strings in rows and expected metadata. Use
`nameof` for data-source member references. Retain independent literal checks
when the exact external spelling is the behavior under test.

Execution extensions must delegate to the original method attribute instead of
re-enumerating `DataRowAttribute` instances, looping over cases themselves or
calling `MethodInfo.Invoke`. MSTest owns row expansion, selection and reporting.
Preserve each row's arguments, display metadata, source location, cancellation,
initialization/cleanup and result objects. Do not merge row results or attach a
shared failure only to the final result. When an extension supports folded data,
inspect its resolved unfolding contract rather than assuming one execution call
always represents exactly one row. Verify the same row behavior through composed
extensions and their actual consuming runner to catch semantic drift.

Use a custom attribute when the same scenario vocabulary is useful across test
classes. The `ITestDataSource` pattern checked in 4.4.1 and 4.5.1 is synchronous;
resolve its signature again when the consumer's version changes:

```csharp
using System.Reflection;
using Microsoft.VisualStudio.TestTools.UnitTesting;

public sealed record ReadCase(string Name, int ChunkSize);

[AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
public sealed class ReadCasesAttribute : Attribute, ITestDataSource
{
    public IEnumerable<object?[]> GetData(MethodInfo methodInfo)
    {
        yield return [new ReadCase("single-byte", 1)];
        yield return [new ReadCase("fragmented", 3)];
    }

    public string GetDisplayName(MethodInfo methodInfo, object?[]? data)
        => $"{methodInfo.Name}({((ReadCase)data![0]!).Name})";
}
```

Each array contains the arguments for one invocation. For metadata from a custom
`ITestDataSource`, wrap each `TestDataRow<T>` in a **single-element** object array;
MSTest unwraps its value and applies the row metadata. A tuple value represents
multiple method arguments. `DynamicData` sources can return the typed rows
directly. Validate the exact shape with the adapter in use.

For versions supporting `ArgumentsDisplayName` (checked in 4.5.1), use it to
label only the arguments while retaining the method name. A full `DisplayName`
override takes precedence according to the attribute/row type's contract.
Dynamic rows require a supporting adapter as well as the framework API. Verify
the discovered names, not just the value stored on a row object.

Give rows stable, distinguishable names, including the meaningful configuration.
Enumeration may happen during discovery and again during execution. Avoid I/O,
ambient random state, timestamps, live streams, mutable singleton fixtures, or
async blocking in `GetData`. Describe how to create a resource and create it
inside the test/setup; the data source does not establish ownership or disposal.

Check repeatable enumeration, argument types/counts, row metadata, and runner
discovery. Folding rows changes reporting and selection: inspect the installed
`TestDataSourceOptionsAttribute` and discovery settings before assuming every row
has a separate result.

## Combinatorial providers

Introduced in 4.4 and checked in 4.4.1/4.5.1; confirm presence in the resolved
package before applying the pattern.

The built-in types are in
`Microsoft.VisualStudio.TestTools.UnitTesting.Combinatorial`. Use
`[CombinatorialData]` for a Cartesian product of independent axes. Supply explicit
values with `[CombinatorialValues]`, a range with `[CombinatorialRange]`, or
implement `ICombinatorialValuesProvider.GetValues(ParameterInfo)` on a parameter
attribute. It returns `object?[]`. Use one provider per parameter.

Make every combination meaningful. A Boolean input is inferred as both values;
other supported inferred types have specific defaults, not exhaustive domains.
For dependent rows, exclusions, or a curated scenario set, use `DynamicData` or
`ITestDataSource`. Do not claim built-in pairwise coverage. Seed random providers
when repeatability is part of the contract and verify the resulting case count.

Custom data providers run at runtime even when MSTest generates discovery
metadata. Implementing one does not require a Roslyn generator.

Sources: [data-driven tests](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-data-driven)
and the version-matched package symbols in [source routes](sources.md).
