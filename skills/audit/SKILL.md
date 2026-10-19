---
name: audit
description: Audits one or more .NET repositories for build, package, analyzer and test-platform problems and separates certain fixes from judgment calls. Use when asked to check, compare or clean up how repositories build, pin SDKs, consume shared packages or analyzers, or run tests, or before a cross-repository version rollout.
license: Apache-2.0
---

# .NET repository audit

Read-only until the report is accepted. The output is a ledger; every line can be checked by
someone opening the cited file.

## 1. Scope

- Name the repositories and their default-branch state: `git -C <repo> status -sb`, and whether
  the working tree has someone else's uncommitted work (never touch it).
- For a fleet audit, start with an inventory table: repository, `global.json` (`sdk.version`,
  `rollForward`, `msbuild-sdks`, `test.runner`), SDK used by the projects, shared-package versions
  and where each is set, test stack, release mechanism.

## 2. Passes

Run each pass with its skill as the rulebook. When the environment supports subagents, give each
pass (or each repository) to its own subagent with the rulebook named in the prompt and a
read-only instruction, then merge the ledgers. Otherwise run the passes in sequence.

| Pass | Rulebook | Looks at |
|---|---|---|
| Versions | `nuget-versions` | global.json, Version.props, Directory.Packages.props, csproj versions, Renovate annotations, stale overrides |
| Build | `msbuild` (`references/antipatterns.md`) | csproj, props, targets, slnx, CI build steps |
| Analyzers | `analyzers` | how analyzers arrive, analysis modes, every suppression, stale IDs |
| Tests | `mstest` (`references/test-smells.md`) | test project shape, runner, profile, coverage, CI test commands, test code smells |
| Release | `release` | publish workflows, gates, credentials model, tag hygiene |

Useful searches (ripgrep; skip `bin/`, `obj/`, `artifacts/`, `node_modules/`, `TestResults/`):

```bash
rg -n --glob '*.{csproj,props,targets}' '<NoWarn>|WarningsNotAsErrors|TreatWarningsAsErrors|AnalysisMode|RunAnalyzers'
rg -n --glob '{.editorconfig,*.globalconfig}' 'dotnet_diagnostic\.[A-Z]+[0-9]+\.severity'
rg -n --glob '*.cs' '#pragma warning disable|SuppressMessage\('
rg -n --glob '*.{csproj,props,targets}' 'Version="[0-9]|VersionOverride|LangVersion|<Nullable>'
rg -n --glob '*.{csproj,props}' 'Microsoft\.NET\.Test\.Sdk|coverlet|TestingPlatformDotnetTestSupport|UseVSTest'
rg -n --glob '*.{yml,yaml,sh,ps1,cs}' 'dotnet test[^\n]*(--filter|--logger|--collect|\| *(grep|tail|head))'
```

## 3. Classify every finding

- **Certain**: objectively wrong, with exactly one correct fix that changes no intended behavior.
  Examples: a suppression of a rule ID that no longer exists, an override equal to SDK truth,
  `msbuild-sdks` entries for packages that aren't MSBuild SDKs, VSTest flags under MTP.
- **Judgment call**: several reasonable fixes, or the fix changes behavior someone may rely on
  (raising a severity, deleting a blanket suppression that hides real diagnostics, switching
  test frameworks). Give your recommended option and the reason, and don't apply it without
  agreement.
- **Veracity gate** before any "broken" verdict: is it broken today on every OS and CI, and has it
  shipped unchanged without failing? If not, call it a risk, not a defect.

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
