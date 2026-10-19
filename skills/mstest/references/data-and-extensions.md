# Data-driven tests and extension points (MSTest 4.5.1)

Every API below compiles in `fixtures/mstest-probe/ApiSurface.cs`.

## Data sources

| Need | Use |
|---|---|
| A few literal cases | `[TestMethod]` plus `[DataRow(1, "a", DisplayName = "...")]` |
| Computed cases | `[DynamicData(nameof(Cases))]` with `public static IEnumerable<(int, string)> Cases` |
| Per-row display name, ignore reason or categories | `IEnumerable<TestDataRow<T>>`: `new(value) { DisplayName = ..., IgnoreMessage = ..., TestCategories = ... }` |
| Keep the method name, rename only the argument part | `TestDataRow<T>.ArgumentsDisplayName` (4.5). Don't combine with `DisplayName` (MSTEST0089) |
| Every combination of parameter values | `[CombinatorialData]` from `Microsoft.VisualStudio.TestTools.UnitTesting.Combinatorial`, with `[CombinatorialValues(...)]`, `[CombinatorialRange(from, count)]` or an `ICombinatorialValuesProvider` per parameter; `bool` parameters expand to both values. It produces the full Cartesian product, not pairwise |
| A reusable source | an attribute implementing `ITestDataSource`; one `object?[]` per invocation |

Rules:

- `DynamicDataSourceType` is inferred; don't state it (MSTEST0052). Avoid `IEnumerable<object[]>`,
  which loses types.
- Display names must be unique per method (MSTEST0087) and free of control characters, which
  break TRX export.
- Data sources are enumerated at discovery and again at execution. They must be deterministic: no
  I/O, no randomness, no shared mutable instances. Create mutable state inside the test.
- The unfolding strategy (`UnfoldingStrategy`) lives on `TestMethodAttribute` since v4, not on data
  attributes.

## Conditions

- Built in: `[OSCondition(OperatingSystems.Linux | OperatingSystems.OSX)]` and
  `[CICondition(ConditionMode.Exclude)]`.
- Custom: derive from `ConditionBaseAttribute`, pass `ConditionMode.Include` or `Exclude` to the
  base constructor, return the raw predicate from `IsConditionMet`, and name a `GroupName`.
  Conditions in the same group combine with OR; different groups combine with AND.
- `IsConditionMet` replaced v3's `ShouldRun`.

## Extending execution

- Wrap a test by deriving from `TestMethodAttribute` and overriding
  `ExecuteAsync(ITestMethod testMethod)`. Call the base or the inner implementation and return its
  `TestResult[]`.
  - Never call `MethodInfo.Invoke` yourself. Assertion failures arrive as `TestResult` outcomes,
    not exceptions, so a try/catch never sees them.
  - Propagate the caller-info constructor parameters:
    `([CallerFilePath] string callerFilePath = "", [CallerLineNumber] int callerLineNumber = -1) : base(callerFilePath, callerLineNumber)`.
- Apply a wrapper to every method of a class by deriving from `TestClassAttribute` and overriding
  `GetTestMethodAttribute`, wrapping the original attribute.
- Check that discovery still sees the tests you expect with the test app's `--list-tests json`.
- A domain assertion is an extension method on `Assert.That` (`Assert.That.IsValidOrder(order)`).
  It fails through `Assert.Fail` with a business message and has its own rejection test.

## Experimental APIs in 4.5.1

Retry customization (`RetryBaseAttribute.ExecuteAsync`, `RetryContext`, `RetryResult`), test filters
(`ITestFilter`, `TestFilterProvider`), `TestContext.Current`, `Assert.Scope` (soft assertions) and
`Assert.AddValueFormatter` are marked experimental. Acknowledge them where they're used, with
`[Experimental]` on the consuming member or a targeted pragma, never with a project-wide `NoWarn`, and
expect API changes on minor upgrades.
