# Worked examples

Each case was found and fixed in a real repository during the October 2026 ANcpLua rollout. The
pattern matters, not the repository.

## 1. Package props that never reached a consumer

Before (`ANcpLua.Analyzers` up to 2.1.6): the package shipped both folders.

```text
build/ANcpLua.Analyzers.props            <CompilerVisibleProperty Include="PublishAot" /> ...
buildTransitive/ANcpLua.Analyzers.props  AlAnalysisMode profile hook only
```

Every consumer's `obj/*.nuget.g.props` imported only `buildTransitive/`, and no consumer's
`GeneratedMSBuildEditorConfig.editorconfig` contained `build_property.PublishAot`. Three rules
read empty values in every real build, while their unit tests, which inject the keys, passed.

After: the items moved into `buildTransitive/ANcpLua.Analyzers.props` (plus `TargetFrameworks`, which
one rule read but nothing exposed), `build/` was deleted, and a convention test ties every
`"build_property.X"` literal in the analyzer source to a `CompilerVisibleProperty` item. The test
fails with the item removed and passes with it.

## 2. Renumbered IDs left in NoWarn

```xml
<!-- before: these IDs stopped existing in ANcpLua.Analyzers 2.0 -->
<NoWarn>$(NoWarn);AL0017;AL0018</NoWarn>
<NoWarn>$(NoWarn);AL0014;AL0025;AL0039</NoWarn>
<NoWarn>$(NoWarn);AL0140</NoWarn>          <!-- removed rule, no successor -->
```

Look each ID up in `docs/migration-catalog.md`. If the new ID's rule is still unwanted, write the
new ID with a reason. Otherwise delete the entry, build, and fix what appears.

## 3. Severity lines that can't reach their rule

```ini
[*.cs]
dotnet_diagnostic.AL1600.severity = error   # rule reports on Directory.Packages.props
dotnet_diagnostic.AL1601.severity = none    # rule reports on Directory.Build.props
```

Neither line has any effect: the diagnostics sit on props files, which `[*.cs]` never matches.
Move the setting to a `.globalconfig` (`is_global = true`) or use `NoWarn`, or delete it if the
default is what you want.

## 4. A list property overwritten

```xml
<!-- before: drops the SDK's NU1900-NU1904 escalation inherited from Common.props -->
<WarningsAsErrors>CA1816;CA2000;CA2012;CA2016</WarningsAsErrors>
<!-- after -->
<WarningsAsErrors>$(WarningsAsErrors);CA1816;CA2000;CA2012;CA2016</WarningsAsErrors>
```

The same applies to `NoWarn`, `DefineConstants` and `CompileDependsOn`.

## 5. A pragma hiding a false positive

```csharp
#pragma warning disable AL1210 // CodeFixes project doesn't reference ANcpLua.Roslyn.Utilities
    identifier.Contains('_', StringComparison.Ordinal);
#pragma warning restore AL1210
```

The comment was false: the project did reference the library. The real cause was that the rule
suggested `ContainsOrdinal(char)`, which doesn't exist. Fix: the rule now reports only when the
suggested extension has an overload for the call's argument types, regression tests cover
`Contains(char)` (silent) and `IndexOf(char)` (still reported), and the pragma is gone.

## 6. A test "relax" block that relaxes nothing

```ini
[tests/**/*.cs]
# Relax ANcpLua.Analyzers to warning for test code
dotnet_diagnostic.AL1000.severity = warning
... 38 more ...
```

With `TreatWarningsAsErrors=true`, warnings are errors, so nothing was relaxed. Rules whose
default is Info were in fact tightened. The block went; the one rule tests really need off stayed,
with a reason:

```ini
[tests/**/*.cs]
# AL1408: AnalyzerConventionTests instantiates every analyzer type through Activator.CreateInstance.
dotnet_diagnostic.AL1408.severity = none
```

## 7. A package-shipped sectioned editorconfig

`Config/GeneratedFiles.editorconfig` inside an MSBuild SDK package, added through
`EditorConfigFiles`:

```ini
[**/obj/**/*.cs]
dotnet_diagnostic.RS0030.severity = none
```

Sections in a non-global config resolve relative to the config file's directory, which is inside
`~/.nuget/packages`, so the file never matched consumer code. Deleting it changed no behavior.
Package-shipped configs must be global configs.

## 8. An analyzer ID reused for an MSBuild error

```xml
<Error Code="AL1601" Text="Version.props not imported..." />
```

The SDK target used the analyzer's ID for a different check. `NoWarn` can't silence an MSBuild
`<Error>`, and searching for the ID finds two unrelated things. It was renamed to the SDK's own
code family (`ANCPSDK002`, next to `ANCPSDK001`).
