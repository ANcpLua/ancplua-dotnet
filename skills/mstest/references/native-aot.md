# Native AOT test projects (MSTest.Sdk 4.5.1)

Sources: `MSTest.Sdk/4.5.1/Sdk/Runner/NativeAOT.targets` and
https://learn.microsoft.com/dotnet/core/testing/unit-testing-mstest-sdk (reflection source generator).

## What NativeAOT mode changes

With `<PublishAot>true</PublishAot>`, MSTest.Sdk switches to its NativeAOT runner targets:

- It references `Microsoft.Testing.Platform.MSBuild`, `MSTest.TestFramework` and `MSTest.SourceGeneration`
  (compile-time discovery). Under CPM it adds the matching `PackageVersion` items itself.
- It fails the build for `EnableAspireTesting`, `EnablePlaywright` and `EnableWindowsUIAutomation`.
- It warns that CrashDump, HangDump, HotReload and Retry may not work. It calls the Azure DevOps,
  GitHub Actions and JUnit reports unsupported.

Outside NativeAOT, opt into source generation with
`<EnableMSTestSourceGeneration>true</EnableMSTestSourceGeneration>`. With the generator active,
`[TestClass]` must be on the class itself, not inherited (MSTEST0069). Source generation for a
netstandard target is a build error.

## Reflection-free mode

For trimmed and Native AOT projects, `MSTestSourceGenMode` defaults to `ReflectionFree` (4.3.2+).
Plain synchronous `[TestMethod]` and `[DataRow]` methods use generated metadata and invokers. Async
tests, custom test-method attributes, `DynamicData` and custom `ITestDataSource` implementations
take a reflection fallback, which a real Native AOT binary may not support. The generator reports
test shapes it can't handle (static or open generic classes, inaccessible classes, generic methods,
`ref`/`in`/`out` parameters) as build diagnostics; fix the shape instead of suppressing them.

## Four separate claims

Prove each one on its own:

1. **Discovery is generated:** the build output contains the generated registration, and
   `--list-tests` lists the tests.
2. **Invocation is generated:** the tests run without the reflection fallback in reflection-free
   mode.
3. **The fallback is known:** every test that needs reflection is listed and accepted, or rewritten.
4. **The AOT binary runs:**

   ```bash
   dotnet publish tests/Foo.Tests -c Release -r osx-arm64 -o artifacts/aot/Foo.Tests
   ./artifacts/aot/Foo.Tests/Foo.Tests --report-trx
   ```

   Read the exit code (`SKILL.md` section 3). Only this run proves AOT compatibility.

A JIT `dotnet test` run proves none of claims 2 to 4, and ReadyToRun is not Native AOT. Trim and
AOT warnings (IL2xxx, IL3xxx) during publish are failures to fix, not noise.

## Analyzers that matter here

- MSTEST0072: shared `[AssemblyFixtureProvider]` fixtures are skipped without dynamic code, so declare
  fixtures directly in AOT test assemblies.
- MSTEST0088: host-created test classes aren't supported with AOT or source generation.
- ANcpLua.Analyzers AL1402-AL1409 flag trimming and AOT hazards (`dynamic`, `Expression.Compile`,
  `Activator.CreateInstance`, `Type.GetType` with a computed name) in projects that set `PublishAot`
  or `IsAotCompatible`.
