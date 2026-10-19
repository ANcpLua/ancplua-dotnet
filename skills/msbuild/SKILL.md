---
name: msbuild
description: Writes and reviews MSBuild evaluation, properties, items, imports, custom targets and build/buildTransitive package assets for SDK-style .NET repositories. Use for ignored or empty properties/items, generated files, analyzer/build-asset packaging, build-file reviews, binlog diagnosis and incremental-build problems. Focused MSTest project setup, runner configuration and test commands belong to mstest-extensions.
license: Apache-2.0
---

# MSBuild for SDK-style repositories

For MSTest-specific project or runner work, use the
[companion routing table](../audit/references/mstest-routing.md).

## 1. Evaluation order decides where things go

SDK-style projects import SDK props before their body and SDK targets afterward.
`Directory.Build.props` and `Directory.Build.targets` are imported *inside* that
SDK/common chain; the latter is late, but later SDK imports can still replace
its values or target definitions. Trace the actual order with `-preprocess`.

- `.props` files run before the project body. Put overridable defaults there, conditioned on
  emptiness: `<Foo Condition="'$(Foo)' == ''">x</Foo>`.
- Read project/SDK-derived values where they are available. A project-body
  `TargetFramework` is usually unset in early props; global properties and inner
  builds can already supply it. Check the actual evaluation before moving a condition.
- Keep build logic in `.targets`. A target declared in `.props` is legal;
  imported target definitions can replace it, rather than hooks requiring an
  already-declared target. Command-line global properties normally resist local
  reassignment; inspect `TreatAsLocalProperty` when that behavior differs.
- An inner `Directory.Build.props` stops the upward search. Import the parent explicitly:
  `<Import Project="$([MSBuild]::GetPathOfFileAbove('Directory.Build.props', '$(MSBuildThisFileDirectory)../'))" />`.
- Use exact discovery names (`Directory.Build.props`, `Directory.Packages.props`)
  for portability to case-sensitive filesystems.

## 2. Rules for everyday edits

- Omit restated defaults after checking the effective SDK settings. Preserve
  deliberate overrides and explicit source ordering when the project requires them.
- List-like properties keep their previous value: `$(NoWarn);X`, `$(DefineConstants);X`,
  `$(CompileDependsOn);CustomStep`.
- Quote both sides of conditions: `'$(X)' == 'true'`.
- Paths come from properties (`$(MSBuildThisFileDirectory)`, `$(MSBuildProjectDirectory)`,
  `$(IntermediateOutputPath)`, `$(ArtifactsPath)`). Never use absolute paths, `obj/` literals or
  backslashes inside `Exec`.
- Use MSBuild tasks for file work: `MakeDir`, `Copy`, `Delete`, `WriteLinesToFile`, `Touch`. Use
  property functions for string work (`$([System.IO.Path]::Combine(...))`, `$(X.Replace(...))`).
  `Exec` is for real external tools, and an OS-specific one is guarded with
  `$([MSBuild]::IsOSPlatform('Windows'))`.
- A value shared by three or more projects moves to `Directory.Build.props`. A value the SDK of
  the repository already owns (for ANcpLua.NET.Sdk: `LangVersion`, `Nullable`,
  `TreatWarningsAsErrors`, `ImplicitUsings` and the analyzer set) is never restated in a project.
- Analyzer and build-tool packages (`*.Analyzers`, SourceLink, MinVer, Nerdbank.GitVersioning) are
  `PrivateAssets="all"`, or a `GlobalPackageReference` from the SDK or `Directory.Packages.props`.
- Use [items and outputs](references/items-and-outputs.md) for Include/Update/Remove,
  metadata batching and the copy contract, including outputs mutated by the app.

## 3. Custom targets

```xml
<Target Name="GenerateBuildInfo"
        BeforeTargets="CoreCompile"
        Inputs="$(MSBuildProjectFile);@(BuildInfoSource)"
        Outputs="$(IntermediateOutputPath)BuildInfo.g.cs">
  <WriteLinesToFile File="$(IntermediateOutputPath)BuildInfo.g.cs" Lines="@(_BuildInfoLines)"
                    Overwrite="true" WriteOnlyWhenDifferent="true" />
  <ItemGroup>
    <Compile Include="$(IntermediateOutputPath)BuildInfo.g.cs" />
    <FileWrites Include="$(IntermediateOutputPath)BuildInfo.g.cs" />
  </ItemGroup>
</Target>
```

- `Inputs` and `Outputs` on every target that produces files, or it runs on every build.
  `Outputs` must not contain times or GUIDs.
- Generated code goes under `$(IntermediateOutputPath)`, is added to `Compile` inside the target
  (it doesn't exist at evaluation time), and is registered in `FileWrites` so `dotnet clean` removes
  it.
- Hook with `BeforeTargets`/`AfterTargets` or by appending to `$(XDependsOn)`. Never redefine an SDK
  target name (`Build`, `CoreCompile`) and never overwrite a `DependsOn` list without
  self-reference.
- Query targets return data with `Returns=`, not `Outputs=`.
- Calling `<MSBuild Projects="$(MSBuildProjectFullPath)" Targets="Publish">` on the same project
  starts a second build into the same bin/obj and races. Use `DependsOnTargets` instead.

## 4. Packaging build assets and analyzers

Read `references/packaging.md` before changing a package's `build/`, `buildTransitive/` or
`analyzers/` content. In brief: file names equal the PackageId, analyzers go to
`analyzers/dotnet/cs`, and their dependencies ship next to them.

## 5. Diagnosing

1. Reproduce with a binary log: `dotnet build -bl:artifacts/logs/build.binlog` (one name per run).
2. Read the first error, not the last. For restore errors, see the `nuget-versions` skill.
3. Inspect with the binlog tools available in the session (a binlog MCP server: call its tool list
   first) or `dotnet msbuild -preprocess:pp.xml` for the fully evaluated project.
4. For "why is this property X?", use `dotnet msbuild -getProperty:X -getItem:Y` on the project.
5. For slow builds, use [performance evidence](references/performance.md): controlled
   cold/incremental/no-op samples, evaluation versus execution, task time and dependency waits.
6. Duplicate outputs: two projects or two global-property sets writing the same `bin`/`obj` (shared
   `BaseIntermediateOutputPath`, `SetTargetFramework` to the project's own single TFM, the same
   project in two solutions built in one script).

## 6. Review

Check changes against `references/antipatterns.md`. A build-defect finding identifies
the affected supported environment/configuration and evidence of failure. A Linux-only
or conditional-build failure is still a defect; distinguish it from an unverified risk.
Report findings as `file:line | rule | evidence | fix`, most severe first.
