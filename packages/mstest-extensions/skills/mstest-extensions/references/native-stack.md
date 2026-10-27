# Opinionated native MSTest stack

Use this stack for new tests and extension examples unless the user explicitly
selects another configuration:

| Component | Choice |
| --- | --- |
| MSBuild project SDK | `MSTest.Sdk` 4.5.1 |
| Framework and adapter | SDK-managed MSTest 4.5.1 |
| Runner | Native `Microsoft.Testing.Platform` 2.5.1 |
| Extension profile | `AllMicrosoft` |
| Coverage | SDK-managed `Microsoft.Testing.Extensions.CodeCoverage`, enabled when requested |
| C# version | Target-framework default; omit a speculative `latest` override |

MTP 2.5.1 is the platform version, not the MSTest.Sdk package version. Native MTP
means the supported platform runner; it does not mean every test runs as Native
AOT. AOT requires separate publication and execution evidence.

The root configuration for the checked .NET 10 baseline is:

```json
{
  "sdk": { "version": "10.0.401", "rollForward": "latestFeature" },
  "msbuild-sdks": { "MSTest.Sdk": "4.5.1" },
  "test": { "runner": "Microsoft.Testing.Platform" }
}
```

```xml
<Project Sdk="MSTest.Sdk">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <TestingExtensionsProfile>AllMicrosoft</TestingExtensionsProfile>
  </PropertyGroup>
</Project>
```

Let the SDK import the framework, adapter, native runner entrypoint and profile
extensions. Do not add another bootstrap, VSTest bridge, duplicate references or
manual registration for an extension the SDK already supplies. A custom MTP host
extension is warranted only for actual host behavior. The profile includes
extensions; runtime use of reporting or coverage can still require its option.
Do not assume AllMicrosoft also opts into every experimental or API-only feature.
The native coverage extension is `Microsoft.Testing.Extensions.CodeCoverage`;
do not add a VSTest coverage collector or duplicate profile-owned references.

Use constructor/property `TestContext` injection in ordinary tests and the native
experimental `TestContext.Current` in an executor that needs invocation context.
MSTest establishes and flows that context; do not copy its cancellation token
into another AsyncLocal, create a substitute ambient context, add a
`CancellationToken.None` fallback or a compatibility `#if`. Scope the experimental
dependency to the member that uses it. A custom scope marker used to prove a
decorator is executing is distinct from reimplementing the invocation context.

The SDK runs native fixture/lifecycle hooks. A custom attribute still implements
its own policy and composes with the supplied original executor once; the SDK
cannot infer that policy. Preserve result arrays and row identities. Independent
cases use native rows with named shared contract constants and typed enum
selectors. A literal whose exact spelling is being tested needs an independent
oracle; using one constant on both sides must not conceal a wire-contract change.

For an existing repository, inspect its actual resolved configuration before
making claims. Report a mismatch with this stack; change existing pins or runner
settings when migration is requested. Reviews remain read-only. Version
inspection exists to detect drift and resolve APIs, not to maintain legacy
fallback implementations in examples.

Sources: [MSTest SDK configuration](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-sdk)
and the [runner and generation guidance](runner-and-generation.md). Use the
[lifecycle](lifecycle.md) reference for resource ownership and cleanup.
