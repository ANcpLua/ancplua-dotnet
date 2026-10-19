---
name: audit
description: Audits one or more .NET repositories for build, package and analyzer problems and separates certain fixes from judgment calls. Use for repository or fleet build-policy audits, shared SDK/package consistency and cross-repository version rollouts. Focused MSTest setup, execution and test-quality reviews belong to mstest-extensions.
license: Apache-2.0
---

# .NET repository audit

Read-only until the report is accepted. The output is a ledger; every line can be checked by
someone opening the cited file.

## 1. Scope

- Name the repositories and their default-branch state: `git -C <repo> status -sb`, and whether
  the working tree has someone else's uncommitted work (never touch it).
- For a fleet audit, start with an inventory table: repository, `global.json` (`sdk.version`,
  `rollForward`, `msbuild-sdks`), SDK used by the projects, shared-package versions
  and where each is set, release mechanism. Include test-platform observations when requested,
  using the [MSTest routing table](references/mstest-routing.md).

## 2. Passes

Run each pass with its skill as the rulebook. When the environment supports subagents, give each
pass (or each repository) to its own subagent with the rulebook named in the prompt and a
read-only instruction, then merge the ledgers. Otherwise run the passes in sequence.

| Pass | Rulebook | Looks at |
|---|---|---|
| Versions | `nuget-versions` | global.json, Version.props, Directory.Packages.props, csproj versions, Renovate annotations, stale overrides |
| Build | `msbuild` (`references/antipatterns.md`) | csproj, props, targets, slnx, CI build steps |
| Analyzers | `analyzers` | how analyzers arrive, analysis modes, every suppression, stale IDs |
| MSTest, when in scope | [Companion skill routing](references/mstest-routing.md) | delegate project setup, execution, extensions and test-quality analysis to their focused owners |
| Release | `release` | publish workflows, gates, credentials model, tag hygiene |
| Runtime cost, when requested | [performance](../performance/SKILL.md) | existing measurements or source hypotheses; retain the audit's read-only scope |
| Constants/dead code, when requested | [constant reconciliation](../csharp-refactoring/references/constant-reconciliation.md) | complete declaration/caller inventory, indirect production uses, disposition and measured cost |

Useful searches (ripgrep; skip `bin/`, `obj/`, `artifacts/`, `node_modules/`, `TestResults/`):

```bash
rg -n --glob '*.{csproj,props,targets}' '<NoWarn>|WarningsNotAsErrors|TreatWarningsAsErrors|AnalysisMode|RunAnalyzers'
rg -n --glob '{.editorconfig,*.globalconfig}' 'dotnet_diagnostic\.[A-Z]+[0-9]+\.severity'
rg -n --glob '*.cs' '#pragma warning disable|SuppressMessage\('
rg -n --glob '*.{csproj,props,targets}' 'Version="[0-9]|VersionOverride|LangVersion|<Nullable>'
```

## 3. Classify every finding

- **Certain**: objectively wrong, with exactly one correct fix that changes no intended behavior.
  Examples: a suppression of a rule ID that no longer exists, an override equal to SDK truth,
  `msbuild-sdks` entries for packages that aren't MSBuild SDKs.
- **Judgment call**: several reasonable fixes, or the fix changes behavior someone may rely on
  (raising a severity, deleting a blanket suppression that hides real diagnostics, changing
  an import contract). Give your recommended option and the reason, and don't apply it without
  agreement.
- **Veracity gate**: demonstrate the failure in an affected supported environment
  or configuration. State that scope; a platform-specific defect is still a defect.
  Treat an unverified failure mechanism as a risk rather than claiming reproduction.

## 4. Ledger format

One block per repository, then a cross-repository table:

```text
<repo>
  certain:   file:line | rule | evidence | fix
  judgment:  file:line | rule | evidence | options -> recommended (why)
  ok:        what was checked and found correct (one line per pass)
```

Totals per category must equal the number of lines listed. When the audit leads to fixes, apply
certain fixes per repository in one commit each, verify (build, tests), and list what changed
beyond the request as side effects.
