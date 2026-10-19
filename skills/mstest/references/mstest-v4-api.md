# MSTest 4.x API reference for writing tests

Version notes: the APIs below are present in MSTest 4.5.1. Items marked (3.x→4) changed or were
removed in the v4 major; the migration source is
https://learn.microsoft.com/dotnet/core/testing/unit-testing-mstest-migration-v3-v4.

## Assertions

| Intent | Use | Not |
|---|---|---|
| Exact exception type | `Assert.ThrowsExactly<T>(() => sut.Do())` | `[ExpectedException]` (removed in v4), `Assert.ThrowsException` (removed in v4) |
| Exception or subtype | `Assert.Throws<T>(...)` | `try { ... } catch (T) { }` |
| Async exception | `await Assert.ThrowsExactlyAsync<T>(() => sut.DoAsync())` | the same call without `await` (it always passes) |
| Inspect the exception | `var ex = Assert.ThrowsExactly<T>(...); Assert.AreEqual("x", ex.ParamName);` | `catch` blocks with asserts |
| Type and cast | `var t = Assert.IsInstanceOfType<T>(value);` | `IsInstanceOfType(value, typeof(T))` followed by `(T)value`; the v3 `out var` overload (3.x→4) |
| Equality | `Assert.AreEqual(expected, actual)` | swapped arguments (MSTEST0017) |
| Reference identity | `Assert.AreSame` on reference types | `AreSame` on value types (MSTEST0038, always fails) |
| Null | `Assert.IsNull` / `Assert.IsNotNull` | `Assert.IsTrue(x != null)` |
| Booleans | `Assert.IsFalse(x)` | `Assert.IsTrue(!x)` (MSTEST0023) |
| Unconditional failure | `Assert.Fail("reason")` | `Assert.IsTrue(false)` (MSTEST0025) |
| Count | `Assert.HasCount(3, items)` | `Assert.IsTrue(items.Count == 3)` (MSTEST0037) |
| Empty | `Assert.IsEmpty(items)` / `Assert.IsNotEmpty(items)` | `Count == 0` / `Any()` checks |
| Membership | `Assert.Contains(item, items)` / `Assert.DoesNotContain(...)` | `IsTrue(items.Contains(item))` |
| Single element | `var only = Assert.ContainsSingle(items);` | `Count == 1` then `items[0]` |
| Strings | `Assert.Contains("x", s)`, `Assert.StartsWith`, `Assert.EndsWith`, `Assert.MatchesRegex` | `StringAssert.*` (MSTEST0046) |
| Ranges | `Assert.IsInRange(min, max, value)`, `Assert.IsGreaterThan(lowerBound, value)`, `Assert.IsLessThanOrEqualTo(upperBound, value)` | reversed bound arguments |
| Sign | `Assert.IsPositive(value)`, `Assert.IsNegative(value)` | `IsTrue(value > 0)` |
| Every expected item present (with multiplicity) | `Assert.ContainsAll(expectedItems, actual)` | a loop of `Contains` |
| Same elements, order significant or not | `Assert.AreSequenceEqual(expected, actual)` or with `SequenceOrder` | `AreEqual` on collections (MSTEST0065), `CollectionAssert.*` (MSTEST0068) |
| Deep structural equality of object graphs | `Assert.AreEquivalent(expected, actual)` (both of type `T`; a `bool` overload makes extra members on `actual` fail) | comparing serialized JSON |
| Negative string checks | `Assert.DoesNotStartWith`, `Assert.DoesNotMatchRegex` | `IsFalse(s.StartsWith(...))` |

v4 signature change: overloads that took `message` plus `object[] args` now take only `message`;
use string interpolation. Assertion messages explain the business meaning, not "values differ".

Newer analyzers worth knowing: MSTEST0064 (prefer the async assertion overloads in async tests),
MSTEST0066 (`[Ignore]` needs a justification), MSTEST0067 (no sync-over-async blocking in tests).

## Attributes and lifecycle

- `[TestClass]` on a `sealed` class. `[TestMethod]` for every test, data-driven or not; `[DataTestMethod]`
  is obsolete (MSTEST0044).
- `[DataRow(1, "a")]`, with `DisplayName = "..."` when the generated name would contain control
  characters or long values.
- `[DynamicData(nameof(Cases))]` where `Cases` is `IEnumerable<(int, string)>` or
  `IEnumerable<TestDataRow<T>>`; the source type is inferred (MSTEST0052 flags an explicit
  `DynamicDataSourceType`).
- Constructor injection: `public OrdersTests(TestContext context)`, stored in a readonly field.
  Never a `static TestContext` (MSTEST0024).
- `[TestInitialize]`/`[TestCleanup]` for async setup and teardown; constructor/`IDisposable` for
  synchronous ones.
- `[ClassInitialize]`/`[ClassCleanup]` are static and take `TestContext`. v4 always runs class
  cleanup at the end of its class (`ClassCleanupBehavior` removed). End-of-assembly work goes in
  `[AssemblyCleanup]`.
- `[Timeout(2000, CooperativeCancellation = true)]` plus `TestContext.CancellationToken` passed into
  the code under test. `TestTimeout.Infinite` is removed; use `int.MaxValue`.
- `[OSCondition(OperatingSystems.Linux | OperatingSystems.OSX)]` and `[CICondition]`-style
  conditions instead of `if (OperatingSystem.IsWindows()) return;` (MSTEST0061).
- `[Retry(3)]` only for external dependencies; `[DoNotParallelize]` only for tests that share
  process-wide state that can't be isolated.
- `[assembly: Parallelize(Scope = ExecutionScope.MethodLevel)]` once per test assembly when the
  tests are independent.

## TestContext in v4

- `TestContext.Properties` is `IDictionary<string, object>`: use `ContainsKey`, not `Contains`.
- `TestContext.ManagedType` is removed; use `FullyQualifiedTestClassName`.
- `TestName` throws inside `AssemblyInitialize`/`ClassInitialize`; `FullyQualifiedTestClassName`
  throws inside `AssemblyInitialize`.
- Output: `TestContext.WriteLine` instead of `Console.WriteLine`.

## Custom test attributes (v4)

- Override `ExecuteAsync(ITestMethod)` returning `Task<TestResult[]>`; `Execute` is gone.
- Propagate caller info: `public MyTestMethodAttribute([CallerFilePath] string f = "", [CallerLineNumber] int l = -1) : base(f, l) { }`.
- Display names via `DisplayName = "..."`, not the positional constructor argument.

## Source generation and Native AOT

- Native AOT test projects include `MSTest.SourceGeneration` automatically. Others opt in with
  `<EnableMSTestSourceGeneration>true</EnableMSTestSourceGeneration>`.
- With the generator active, `[TestClass]` must be on the class itself, not inherited (MSTEST0069).
- Verify Native AOT on the published artifact (`dotnet publish -c Release -r <rid>` then run the
  executable); a JIT `dotnet test` run doesn't prove AOT compatibility.
