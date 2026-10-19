# ancplua-dotnet

Rules and workflows for SDK-style .NET repositories, written for Claude Code and Codex from one tree.
They cover C# refactoring, MSBuild authoring and review, NuGet version chains and CPM,
Roslyn analyzer adoption, runtime performance and diagnostics, and layered
NuGet releases that wait for nuget.org to index each layer before the next one moves.

MSTest work belongs to the [MSTest Extensions](https://github.com/ANcpLua/mstest-extensions-plugin)
companion. This plugin keeps a compact [routing table](skills/audit/references/mstest-routing.md)
for mixed build/test requests. The antipattern examples come from fixing real repositories.

## Skills

| Skill | Use it for |
|---|---|
| `msbuild` | csproj/props/targets edits, custom targets, package build assets, analyzer packaging, binlog diagnosis, build reviews |
| `nuget-versions` | where versions live, `Version.props` truth chains, `global.json` pins and rollForward, CPM, NU error codes, Renovate annotations |
| `analyzers` | how analyzers arrive, severity precedence, suppression hygiene, `CompilerVisibleProperty`, ANcpLua.Analyzers specifics |
| `csharp-refactoring` | binding-aware structural changes, generated/partial code and runtime/API contracts |
| `performance` | BenchmarkDotNet comparisons, CPU/GC/allocation evidence, hot-path reviews and crash/hang collection |
| `release` | layered releases, tag-driven vs push-driven publishing, trusted publishing, waiting for the NuGet index (`scripts/wait-nuget.sh`), moving consumers |
| `audit` | read-only fleet audits that separate certain fixes from judgment calls |

## Agents (Claude Code)

| Agent | Role |
|---|---|
| `dotnet-auditor` | Read-only audit of one repository; returns a ledger with file:line evidence. Fan out one per repository. |
| `build-change-reviewer` | Reviews build/package diffs and routes MSTest concerns to the companion; reports only findings that pass a veracity gate. |

Codex doesn't load agents from plugins; the `audit` skill tells Codex to spawn its own subagents per pass.

## Install

Claude Code:

```bash
claude plugin marketplace add ANcpLua/ancplua-anthropic
claude plugin install ancplua-dotnet@ancplua-anthropic
```

Then run `/reload-plugins` in an open session.

Codex:

```bash
codex plugin marketplace add ANcpLua/ancplua-openai
codex plugin add ancplua-dotnet@ancplua-openai
codex plugin add mstest-extensions@ancplua-openai
```

Then start a new session.

## Layout

```text
.claude-plugin/plugin.json   Claude Code manifest
plugin.json                  Agent Plugins manifest with the Codex interface (extensions.com.openai)
skills/<name>/SKILL.md       shared by both tools; Agent Skills frontmatter only
agents/<name>.md             Claude Code subagents
scripts/verify.sh            manifest/frontmatter checks (CI runs it on push, PRs and weekly)
evals/                       existing Claude behavior evaluations and an unrelated-request check
```

Both manifests carry the same `version`; raise it with every change.

## Verify

```bash
scripts/verify.sh                       # package structure and skill frontmatter
claude plugin eval . --runs 1 --ablation none   # quick behavior check (model calls on your account)
claude plugin eval .                            # full: 3 runs, with and without the plugin
```

MSTest APIs and runner verification live in the companion repository.

## 0.4.0

Add compact C# refactoring and runtime-performance skills. Extend existing build
and package skills with measured build diagnosis, item/copy contracts, conditional
CPM migration and isolated SDK selection. Correct import-order, analyzer-asset and
implicit-package guidance. References load only for the relevant task; the seven
skills preserve automatic invocation and route MSTest work to the companion.

## 0.3.0

Remove the duplicate `mstest` skill, its references, probe and three evaluation cases.
Route MSTest work to the companion's nine focused skills. Keep MSBuild, NuGet,
analyzer configuration and release artifact integrity here.

## License

Apache-2.0. See `NOTICE` for research sources.
