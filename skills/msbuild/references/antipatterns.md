# MSBuild antipatterns: signal, harm, fix

A signal is a search starting point (`rg -n '<pattern>' -g '*.{csproj,props,targets}'`). Read the
surrounding file before reporting: several patterns have legitimate uses, listed under "Fix".

## Correctness (can produce a wrong or broken build)

| Rule | Signal | Harm | Fix |
|---|---|---|---|
| tfm-property-in-props | `PropertyGroup Condition=".*TargetFramework` or property `Condition` on `$(TargetFramework)` in a `*.props` | never matches in single-TFM projects | move to `.targets` or the project; item/target conditions are fine |
| sdk-value-in-props | `$(OutputPath)`, `$(TargetPath)`, `$(OutputType)` read in `.props` | not set yet | move to `.targets` |
| target-in-props | `<Target` in `*.props` | hooks into targets that don't exist yet | move to `.targets` |
| overwrite-list | `<NoWarn>X</NoWarn>`, `<DefineConstants>X</DefineConstants>` without `$(...)` | drops inherited values | `$(NoWarn);X` |
| overwrite-dependson | `<(Build\|Compile\|CoreBuild\|Clean)DependsOn>` without self-reference | removes SDK targets | `$(CompileDependsOn);Mine` or `BeforeTargets` |
| redefine-sdk-target | `<Target Name="(Build\|CoreCompile\|Pack\|Publish)"` in repo files | replaces the SDK target | new name plus `BeforeTargets`/`AfterTargets` |
| self-msbuild-fork | `<MSBuild Projects="$(MSBuildProjectFullPath)"` | second build into the same bin/obj races | `DependsOnTargets` |
| same-tfm-settargetframework | `SetTargetFramework="TargetFramework=X"` on a single-TFM reference whose TFM is X | duplicate build to one path | remove |
| shared-intermediate | the same `BaseIntermediateOutputPath`/`OutputPath` across projects | `project.assets.json` collisions | per-project defaults or `UseArtifactsOutput` |
| multitfm-shared-output | `<TargetFrameworks>` with an `OutputPath` lacking `$(TargetFramework)` | TFMs overwrite each other | keep the SDK default |
| unquoted-condition | `Condition="$(` or `== true` unquoted | empty values parse wrong | `'$(X)' == 'true'` |
| dbp-casing | `Directory.build.props`, `directory.Build.targets` | ignored on Linux/macOS | exact casing |
| nested-dbp-unchained | an inner `Directory.Build.props` without `GetPathOfFileAbove` import | loses root settings | import the parent |
| eval-time-generated-glob | `<Compile Include="$(IntermediateOutputPath)` outside a target | file missing at evaluation | add inside the generating target |
| package-build-name | `build/*.props` whose name differs from the PackageId | NuGet never imports it | `build/<PackageId>.props` |
| buildtransitive-tfm | `buildTransitive/<tfm>/` forwarders using `$(TargetFramework)` or importing a TFM-less path | `MSB4019` for transitive consumers | derive the folder from `$(MSBuildThisFileDirectory)` |
| exclude-without-include | `Update=".*" Exclude=` or `Remove=".*" Exclude=` | Exclude only applies to Include | restructure |
| dynamic-project-reference | `ProjectReference` added inside a `<Target>` | `/graph` fails (MSB4260) | static item |

## Incrementality and performance

| Rule | Signal | Harm | Fix |
|---|---|---|---|
| target-without-io | `<Target .*(BeforeTargets\|AfterTargets)=` without `Inputs=`/`Outputs=` that writes files | runs every build | Inputs including `$(MSBuildProjectFile)`, Outputs under `$(IntermediateOutputPath)` |
| volatile-outputs | `Now`, `Ticks`, `NewGuid` in `Outputs` | never up to date | stable path |
| unlisted-output | a task writes a file not in `Outputs` | downstream reruns | list it |
| missing-filewrites | generated file without `FileWrites` | `dotnet clean` leaves it | add `FileWrites` |
| touching-writer | `WriteLinesToFile` without `WriteOnlyWhenDifferent="true"` | changes timestamps every build | add it |
| outputs-on-query | `Target Name="Get.*" Outputs=` | skipped, returns stale data | `Returns=` |
| copy-always | `CopyToOutputDirectory.*Always` | copies every build | `PreserveNewest` |
| eval-file-io | `$([System.IO.File]::(Read\|Write)` in a PropertyGroup | runs on every evaluation, including IDE design-time builds | move into a target |
| broad-glob | `Include="**/*` at the repository root, globs over `node_modules` | slow evaluation | scope globs, `DefaultItemExcludes` |
| serial-msbuild-task | `<MSBuild Projects="@(` without `BuildInParallel="true"` | serial child builds | `BuildInParallel="true"` |
| restore-every-step | several `dotnet build/test/pack` in CI without `--no-restore` | repeated restores | one restore, then `--no-restore` |
| bare-binlog | `-bl` without a file name, or binlogs deleted by `git clean -fdx` | evidence overwritten | `-bl:artifacts/logs/<step>.binlog` |
| analyzers-off-as-fix | `RunAnalyzers=false` / `EnforceCodeStyleInBuild=false` committed to speed up builds | loses enforcement | measure analyzer time from the binlog; tune severities |

## Hygiene and modernization

| Rule | Signal | Harm | Fix |
|---|---|---|---|
| restated-default | `<OutputType>Library`, `<EnableDefaultItems>true`, `<AppendTargetFrameworkToOutputPath>true` | noise | delete |
| manual-compile | `<Compile Include="*.cs"` in an SDK C# project | duplicates the SDK glob | delete; `Compile Remove` to exclude |
| sdk-owned-property | `LangVersion`, `Nullable`, `TreatWarningsAsErrors`, `ImplicitUsings` in a csproj under an SDK that owns them | drift from the repo policy | delete |
| langversion-latest | `<LangVersion>latest` | varies by installed SDK | omit; pin the SDK in global.json |
| hintpath-package | `<HintPath>.*packages` | no dependency resolution | `PackageReference` |
| analyzer-without-privateassets | `PackageReference Include=".*(Analyzers\|SourceLink\|MinVer\|GitVersioning)"` without `PrivateAssets` | leaks to consumers | `PrivateAssets="all"` |
| scattered-version | `Version=` on `PackageReference` under CPM | NU1008, drift | `Directory.Packages.props` |
| copy-paste-props | the same `PropertyGroup` in 3+ projects | drift | `Directory.Build.props` |
| exec-for-builtin | `<Exec Command="(mkdir\|cp\|copy\|rm\|del\|mv\|move\|echo .* >)` | not portable, not incremental | MSBuild tasks |
| exec-for-strings | `Exec` with `sed`, `awk`, `powershell -c` to compute a value | shell-dependent | property functions |
| os-exec-unguarded | `<Exec Command="(chmod\|cmd /c\|bash)"` without an OS condition | fails on the other OS | `IsOSPlatform` condition |
| absolute-path | `[A-Z]:\\`, `/Users/`, `/home/`, `/usr/` in build files | machine-specific | property-relative paths |
| hardcoded-obj | `obj/`, `bin/` literals | breaks artifacts layout | `$(IntermediateOutputPath)`, `$(OutputPath)` |
| assemblyinfo-duplicate | `Properties/AssemblyInfo.cs` with version attributes in an SDK project | CS0579 duplicates | properties, or `GenerateAssemblyInfo=false` |
| legacy-project | `ToolsVersion=`, `xmlns=".*2003"`, `<ProjectGuid>`, `Microsoft.CSharp.targets` | no SDK features | SDK-style project |
| redundant-transitive-reference | `ProjectReference` to Y when a referenced X already references Y and Y isn't used directly | graph noise | keep direct dependencies |
| unregistered-project | a csproj missing from the `.slnx` | CI never builds or tests it | `dotnet sln add` |

## False positives to avoid

- Backslashes in `<Import Project=` and item `Include=` are style only; they matter inside `Exec`
  commands and in files written by `WriteLinesToFile`.
- An unconditioned `<Import>` inside a packed `build/<tfm>/` forwarder is correct: the file is
  always present in the package.
- `AppendTargetFrameworkToOutputPath` may be set deliberately to fix a multi-TFM clash; check
  before calling it a restated default.
- Analyzer-heavy repositories run analyzers in every build on purpose; don't recommend turning
  them off for speed.
