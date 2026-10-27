---
name: analyzers
description: Configures, audits and fixes how Roslyn analyzers reach .NET projects (MSBuild-SDK injection, PackageReference, analysis modes, editorconfig and globalconfig severities, NoWarn, pragmas, SuppressMessage) and packages analyzer rules correctly, including ANcpLua.Analyzers (AL1000-AL1899, AlAnalysisMode). Use when a diagnostic should fire but doesn't, a suppression looks stale or too broad, rule IDs were renumbered, severities differ between IDE and CI, or analyzer behavior depends on MSBuild properties.
license: Apache-2.0
---

# Roslyn analyzer adoption and suppression hygiene

Keep analyzer loading, packaging and severity configuration here. For an MSTest
diagnostic's test-code correction, use the
[companion routing table](../audit/references/mstest-routing.md).

## 1. How an analyzer reaches a project

Find the path first. Each path has its own way to opt out and to pin the version:

| Path | Signal | Version from | Opt-out |
|---|---|---|---|
| MSBuild SDK injection | `<Project Sdk="ANcpLua.NET.Sdk">`; the SDK adds a `GlobalPackageReference` (under CPM) or an implicit `PackageReference` | SDK `Version.props` (`$(ANcpLuaAnalyzersVersion)`) | `DisableANcpLuaAnalyzers=true` |
| Central `GlobalPackageReference` | `Directory.Packages.props` | that item | remove the item |
| Direct `PackageReference` | csproj or `Directory.Build.props` (often conditioned) | `PackageVersion` | condition on the item |
| .NET SDK built-in | `EnableNETAnalyzers`, `AnalysisLevel`, `AnalysisMode` | the .NET SDK | `EnableNETAnalyzers=false` |

Confirm with evidence, not by reading project files:
`dotnet msbuild <proj> -getItem:Analyzer` lists the analyzer DLLs that actually load, and
`obj/<proj>.nuget.g.props` shows which package props files were imported.

## 2. Severity: who wins

From lowest to highest precedence:

1. The descriptor's default severity.
2. Global configs (`is_global = true`) in order of `global_level`. ANcpLua.NET.Sdk's bundled AL config
   uses level 13, and the `AlAnalysisMode` profiles use 50.
3. `.editorconfig` sections matching the source file (`[*.cs]`, `[tests/**/*.cs]`).
4. `#pragma warning disable` and `[SuppressMessage]` at the code location.

`NoWarn` removes a diagnostic; `WarningsAsErrors` and `TreatWarningsAsErrors` escalate what's
left.

Facts that make configurations silently inert:

- A regular (sectioned) `.editorconfig` applies only to files under its own directory. One that
  ships inside a NuGet package and is added through `EditorConfigFiles` matches nothing in the
  consumer. Package-shipped configs must be global configs without sections.
- A diagnostic reported on a non-C# file (an `AdditionalFiles` item such as `Directory.Packages.props`
  or `Version.props`) has no syntax tree, so `[*.cs]` sections never reach it. Configure it in a
  global config, or with `NoWarn` and `WarningsAsErrors`.
- Under `TreatWarningsAsErrors=true`, setting a rule to `warning` relaxes nothing. To relax for
  tests, use `suggestion` or `none` with a reason, or exclude the IDs with `WarningsNotAsErrors`.
- `dotnet_analyzer_diagnostic.severity = error` escalates only rules that are enabled by default,
  and it's ignored entirely when `AnalysisMode`/`AnalysisLevel` enables all rules. ID-specific
  entries from any config still win.

## 3. Suppression rules

- Every suppression names its reason on the same or the previous line. A suppression without a
  reason gets deleted or justified.
- Prefer the narrowest scope: a pragma around one statement, `[SuppressMessage(Justification = ...)]`
  on one member, a section for one generated file, a project `NoWarn`, and only then a repository
  `NoWarn`.
- A suppression for an ID that no package in the project defines is dead. After a renumbering,
  rewrite or delete every `NoWarn`, pragma, `SuppressMessage` and editorconfig entry. For
  ANcpLua.Analyzers 2.0 (`AL0xxx` became `AL1xxx`), the complete old-to-new map ships with this skill
  in `references/id-migration.md`; for example, AL0017 became AL1600 and AL0018 became AL1601.
- A pragma or `NoWarn` that works around a false positive is temporary: fix the analyzer, add a
  regression test, then delete the suppression.
- Two settings that cancel each other (a project `NoWarn` plus an editorconfig "warning" for the
  same ID) are both noise. Keep the one that states the intent.
- Generated code is excluded by name (`*.g.cs`, `*.generated.cs`, `obj/`) and by
  `GeneratedCodeAnalysisFlags.None`. A blanket `dotnet_analyzer_diagnostic.severity = none` in a
  generated-file section is legitimate; the same line in a `[*.cs]` section isn't.

## 4. MSBuild properties inside analyzers

An analyzer reads `build_property.<Name>` from `AnalyzerConfigOptions`, which works only if a
`<CompilerVisibleProperty Include="Name" />` item reaches the compilation.

- Ship consumer configuration in `buildTransitive/<PackageId>.props` when it must
  flow transitively. A `build/` copy alone does not establish that flow; verify
  the consumer's generated imports rather than assuming which folder won.
- Every key the analyzer source reads must have a matching item. Guard this with a test that scans
  the analyzer source for `"build_property.` keys and checks the props file.
- Prove it from a consumer: build a throwaway project against the local package and look for the
  key in `obj/**/<proj>.GeneratedMSBuildEditorConfig.editorconfig`.
- Tests that inject `build_property.*` through editorconfig prove the rule logic, not the wiring.

## 5. ANcpLua.Analyzers specifics

- IDs `AL1000`-`AL1899` in nine domain bands; `AL0xxx` belongs to sibling packages
  (AotReflection, ExtensibleEnumMirror, DiscriminatedUnion).
- `<AlAnalysisMode>`: `Default` (descriptor severities), `AllAsErrors`, or `Disabled`. Unset means
  no profile, so the SDK's bundled per-rule config applies in SDK projects and descriptor
  severities apply elsewhere.
- Projects outside ANcpLua.NET.Sdk that reference the package directly get descriptor severities.
  Together with `TreatWarningsAsErrors`, every Warning-default rule breaks the build there. That's
  intended, but a version bump can surface new hits; budget for fixing them.
- AL1406/AL1407 (dynamic, `Expression.Compile`) apply only to AOT-targeting projects
  (`PublishAot`/`IsAotCompatible`).
- AL1600-AL1602 report on props files (see section 2).

## 6. Worked examples (found in real repositories)

Read `references/examples.md` for before and after cases: stale renumbered IDs in `NoWarn`, a
package `build/` props that never reached consumers, editorconfig lines for props-file rules,
`WarningsAsErrors` without self-reference wiping the SDK's NuGetAudit escalation, a pragma hiding
a false positive, and test "relax" blocks that relax nothing.

## 7. Audit output

For each project: how the analyzer arrives (with evidence), which mode and severity sources apply, and
every suppression as `file:line | ID | scope | reason present? | still defined? | verdict`. Then
"certain" fixes (dead, duplicate or inert settings) and "judgment" items (raising or lowering a
severity, removing a suppression that hides live diagnostics) with a recommendation.
