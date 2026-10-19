# Packaging build assets and Roslyn analyzers

## Package folders

| Folder | Imported for | Notes |
|---|---|---|
| `build/<PackageId>.props/.targets` | direct references only | file name must equal the PackageId, or NuGet skips it |
| `buildTransitive/<PackageId>.props/.targets` | direct and transitive references | use for consumer configuration; share a guarded implementation if supporting multiple folder layouts |
| `buildMultiTargeting/` | the outer build of a multi-TFM project | rarely needed |
| `analyzers/dotnet/cs/` | the C# compiler of every consumer | analyzer, code fix and dependency DLLs |
| `lib/<tfm>/` | compile and runtime references | not for analyzers |

Per-TFM forwarders (`buildTransitive/net8.0/X.props`) find their own folder from
`$(MSBuildThisFileDirectory)`, never from `$(TargetFramework)`, which is unset for transitive
consumers at that point.

## Analyzer package checklist

- Analyzer and code-fix projects target `netstandard2.0`. The compiler host loads them into its own
  process, and a newer TFM fails to load in older IDEs and SDKs.
- `<IsRoslynComponent>true</IsRoslynComponent>` and `<EnforceExtendedAnalyzerRules>true</EnforceExtendedAnalyzerRules>`
  on analyzer projects (RS1036 and related rules catch banned APIs).
- `Microsoft.CodeAnalysis.*` references are `PrivateAssets="all"` and no newer than the oldest
  compiler you support. An analyzer built against a newer Roslyn than the consumer's compiler
  fails with CS9057.
- Pack layout: `<None Include="$(OutputPath)\$(AssemblyName).dll" Pack="true" PackagePath="analyzers/dotnet/cs" Visible="false" />`
  for the analyzer, the code-fix assembly and every bundled dependency (for example
  `ANcpLua.Roslyn.Utilities.dll`). Analyzer dependencies aren't resolved from NuGet at compile time;
  they must sit next to the analyzer.
- `<IncludeBuildOutput>false</IncludeBuildOutput>` so nothing lands in `lib/`;
  `<DevelopmentDependency>true</DevelopmentDependency>` so consumers get `PrivateAssets="all"` by
  default; `<SuppressDependenciesWhenPacking>true</SuppressDependenciesWhenPacking>` when every
  dependency is bundled.
- Both the analyzer and code-fix assemblies ship in the same package; an IDE without the code-fix
  DLL shows diagnostics but no fixes.
- Release tracking: `AnalyzerReleases.Shipped.md` and `AnalyzerReleases.Unshipped.md` as
  `AdditionalFiles` (RS2000-RS2008). Moving rows from Unshipped to Shipped is part of a release.
- `CompilerVisibleProperty` items must reach the consumer compilation. Put transitive
  configuration in `buildTransitive/<PackageId>.props`; verify the actual imports in
  `obj/*.nuget.g.props` and the emitted `build_property.*` keys in the generated analyzer config.
- Severity profiles ship as `.editorconfig`/`.globalconfig` files under `buildTransitive/` and are
  selected by a property (ANcpLua: `<AlAnalysisMode>`), not by asking consumers to copy rules.

## Validation before publishing

- `dotnet pack -c Release -o artifacts`, then list the package: `unzip -l artifacts/<id>.<v>.nupkg`.
  Confirm `analyzers/dotnet/cs/*.dll`, the build and buildTransitive files, and that no `lib/`
  folder sneaks in.
- `<EnablePackageValidation>true</EnablePackageValidation>` with
  `<PackageValidationBaselineVersion>` catches accidental API breaks in `lib/` packages.
- SourceLink plus `ContinuousIntegrationBuild=true` in CI, and `Deterministic` builds. Publish
  `.snupkg` symbols for libraries.
- Local development of a package that the repository's own SDK also injects: give the local
  project a dummy `PackageId` (ANcpLua uses `PackageId=Dummy`) and pass the real one only at pack
  time (`-p:PackageId=ANcpLua.Analyzers`), which avoids the self-reference cycle.
