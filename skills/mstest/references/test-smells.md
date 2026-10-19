# Test smells: detection signal, why it matters, fix

Ordered by damage: the first group lets a broken behavior pass. Each signal is a starting point for
a search; confirm it by reading the test before reporting it.

## Group A: false confidence (report first)

| Smell | Signal | Fix |
|---|---|---|
| Unawaited async assert | `Assert.Throws(Exactly)?Async` or `Assert.*Async` without `await` | `await` it |
| No assertion | a `[TestMethod]` body with no `Assert.`, `Verify`, or helper that asserts | assert the observable outcome |
| Assert in catch | `catch (...) { Assert.` | `Assert.ThrowsExactly<T>` |
| Swallowed exception | `catch { }` / `catch (Exception) { }` with no assert or rethrow | remove the try, or assert |
| Self-comparison | `Assert.AreEqual(x, x)`, comparing an object's field with itself | an independent expected value |
| Always true | `Assert.IsTrue(true)`, MSTEST0032 | real assertion |
| Weak oracle | `Assert.AreNotEqual(old, actual)`, `IsNotNull(result)` as the only check | assert the exact expected value |
| No-op input | input already in the output form (lowercase into `ToLower`) | input that must change, exact output |
| Commented-out asserts | `// Assert.` | restore or delete |
| Zero-test green | a run reporting success with 0 executed or a filter that matched nothing | check the count; `--minimum-expected-tests` |

## Group B: flaky or environment-bound

| Smell | Signal | Fix |
|---|---|---|
| Sleep as sync | `Thread.Sleep(`, `Task.Delay(` used to wait for work | await the operation, poll a condition with a timeout, `FakeTimeProvider` |
| Wall clock | `DateTime.Now`, `DateTime.UtcNow`, `DateTimeOffset.Now` in test or code under test | inject `TimeProvider` |
| Unseeded randomness | `new Random()` without a seed, `Guid.NewGuid()` inside an expected value | seed, or inject |
| Machine paths | `C:\`, `/tmp/`, `/Users/` literals | `Path.GetTempPath()`, temp directories per test |
| Shared mutable static | `static` fields written by tests | per-test state; `[DoNotParallelize]` only when unavoidable |
| Hidden dependency | `File.ReadAllText`, real `HttpClient`, `Environment.GetEnvironmentVariable` in a unit test | explicit fixture or fake |
| Retry hiding a race | `[Retry(` on a test of in-process code | fix the race |
| Platform `if` | `if (OperatingSystem.Is...` inside a test | `[OSCondition]` |

## Group C: diagnosability and maintenance

| Smell | Signal | Fix |
|---|---|---|
| Template leftovers | `UnitTest1`, `TestMethod1`, `Class1` | delete, name by behavior |
| Vague names | `Test1`, `Works`, `ShouldWork` | `Method_Scenario_Expected` or a sentence |
| Copy-paste tests | three or more bodies differing by one literal | `[DataRow]` / `[DynamicData]` |
| Giant test | more than ~30 lines or several behaviors | split per behavior |
| Interleaved phases | asserts between acts | arrange, act, assert |
| Echo messages | `"Expected and actual are not equal"` | say what the business rule is |
| Implementation coupling | `BindingFlags.NonPublic`, `MethodInfo.Invoke`, internal casts | public API; `InternalsVisibleTo` only by decision |
| Over-mocking | more `Setup`/`Verify` lines than logic, exact call-count sequences | assert outcomes |
| Print debugging | `Console.WriteLine` in tests | `TestContext.WriteLine` or remove |
| Ignored tests | `[Ignore]` without a tracked reason, `#if false` | fix or delete |
| Static TestContext | `static TestContext` | constructor injection |
| Unsealed test class | `public class ...Tests` with `[TestClass]` | `sealed` |

## Project-level smells

| Smell | Signal | Fix |
|---|---|---|
| VSTest leftovers | `Microsoft.NET.Test.Sdk`, `coverlet.collector`, `--logger`, `--collect`, `TestingPlatformDotnetTestSupport` | MSTest.Sdk + native MTP |
| Missing runner selection | no `"test": { "runner": "Microsoft.Testing.Platform" }` in global.json | add it |
| Profile-less extension refs | explicit `Microsoft.Testing.Extensions.*` references in an MSTest.Sdk project | `TestingExtensionsProfile` / `Enable*` properties |
| `Microsoft.CodeCoverage` in an MTP project | direct reference | remove; the profile brings `Microsoft.Testing.Extensions.CodeCoverage` |
| Unregistered test project | test csproj missing from the `.slnx` | add it; CI discovers 0 otherwise |
| Exit code hidden | `dotnet test ... \| grep`/`tail` in scripts | run directly, inspect output afterwards |
