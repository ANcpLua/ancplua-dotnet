# ancplua-dotnet

Rules and workflows for SDK-style .NET repositories, written for Claude Code and Codex from one tree.
They cover MSBuild authoring and review, NuGet version chains and Central Package Management,
Roslyn analyzer adoption and suppression hygiene, MSTest on Microsoft.Testing.Platform, and layered
NuGet releases that wait for nuget.org to index each layer before the next one moves.

The facts about MSTest.Sdk 4.5.1 and Microsoft.Testing.Platform 2.5.1 were checked by building and
running test projects against those versions. The antipattern examples come from fixing real
repositories.

## Skills

| Skill | Use it for |
|---|---|
| `msbuild` | csproj/props/targets edits, custom targets, package build assets, analyzer packaging, binlog diagnosis, build reviews |
| `nuget-versions` | where versions live, `Version.props` truth chains, `global.json` pins and rollForward, CPM, NU error codes, Renovate annotations |
| `analyzers` | how analyzers arrive, severity precedence, suppression hygiene, `CompilerVisibleProperty`, ANcpLua.Analyzers specifics |
| `mstest` | MSTest.Sdk 4.5.1 projects, `TestingExtensionsProfile`, native `dotnet test`, MTP exit codes, coverage with dotcov, MSTest v4 API, test smells |
| `release` | layered releases, tag-driven vs push-driven publishing, trusted publishing, waiting for the NuGet index (`scripts/wait-nuget.sh`), moving consumers |
| `audit` | read-only fleet audits that separate certain fixes from judgment calls |

## Agents (Claude Code)

| Agent | Role |
|---|---|
| `dotnet-auditor` | Read-only audit of one repository; returns a ledger with file:line evidence. Fan out one per repository. |
| `build-change-reviewer` | Reviews a diff that touches build, package or test-platform files; reports only findings that pass a veracity gate. |

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
```

Then start a new session.

## Layout

```text
.claude-plugin/plugin.json   Claude Code manifest
plugin.json                  Agent Plugins manifest with the Codex interface (extensions.com.openai)
skills/<name>/SKILL.md       shared by both tools; Agent Skills frontmatter only
agents/<name>.md             Claude Code subagents
fixtures/mstest-probe/       MSTest.Sdk 4.5.1 probe: every API the mstest skill names, --help snapshots per profile
scripts/verify.sh            manifest/frontmatter checks plus the probe (CI runs it on push, PRs and weekly)
evals/                       claude plugin eval cases: one per skill, a negative and a boundary case
```

Both manifests carry the same `version`; raise it with every change.

## Verify

```bash
scripts/verify.sh                       # facts still hold for the pinned packages
scripts/verify.sh --update              # after a deliberate MSTest.Sdk bump: refresh the --help snapshots
claude plugin eval . --runs 1 --ablation none   # quick behavior check (model calls on your account)
claude plugin eval .                            # full: 3 runs, with and without the plugin
```

When `verify.sh` fails after a version bump, fix the skill text first, then refresh the snapshots.

## License

Apache-2.0. See `NOTICE` for research sources.
