# MSTest Extensions plugin

A portable plugin with two independently usable skills for native MSTest testing.
Each owns its local references and executable resources. Choose the requested
workflow inside `mstest`; only that workflow's references need to be loaded.

| Skill | Use it for |
| --- | --- |
| [mstest](skills/mstest/SKILL.md) | API lookup, test implementation, native MTP execution, extensions, scoped reviews and Native AOT verification. |
| [mstest-assertions](skills/mstest-assertions/SKILL.md) | Precise built-in assertion selection and corrections, equality and AOT semantics. |

The checked stack is **MSTest.Sdk/MSTest 4.5.1**, native **MTP 2.5.1**,
**AllMicrosoft** and **Microsoft.CodeCoverage**. Consumer pins control actual API
availability. The plugin identifier remains `mstest-extensions`; invoke `$mstest`
or `$mstest-assertions`. The display name remains **MSTest Extensions**.
See [CHANGELOG.md](CHANGELOG.md) for releases.

The former nine additional skill entrypoints are now task references inside
`mstest`. Their writing, execution, extension, review and AOT instructions remain
available locally. The API catalog and runner fixtures have one owner; there are
no sibling-skill links or copied reference trees. The unchanged upstream validator
and reference-closure checks enforce this structure in CI.

## Staying current

The skill resolves the **consumer's installed version on every task**. Its
[inspector](skills/mstest/scripts/inspect_mstest.py) evaluates MSBuild,
checks restored package requests, and records framework/adapter/MTP versions,
SDK, target, source commits and assembly fingerprints. A changed version or
fingerprint requires fresh API evidence before reusing guidance. This works for
versions beyond those listed in the repository.

```sh
python3 skills/mstest/scripts/inspect_mstest.py --project /path/to/tests.csproj
# Refresh restore assets when appropriate for implementation:
python3 skills/mstest/scripts/inspect_mstest.py --project /path/to/tests.csproj --restore
```

Use repeated `--property NAME=VALUE` for configuration/target/RID and `--previous`
with an earlier JSON report to detect changes. The inspector returns exit 2 for
missing or stale evidence. It does not automatically upgrade packages or rewrite
instructions. An unchanged direct pin does not establish fresh transitive or
floating resolution; restore when needed. XML documents help locate APIs;
version-matched source and compilation establish their public contract.

[Version resolution](skills/mstest/references/version-resolution.md)
explains the workflow. [Known version notes](skills/mstest/references/version-notes.md)
record the 4.4.1 → 4.5.1 delta, including argument display labels, optional
hosting, built-in diagnostics and MTP changes. These are dated evidence, not a
hardcoded support ceiling or guarantees for future releases.

## Current maintenance

`make update-mstest-api` regenerates the public API reference from the configured
release tags; `make check-mstest-api` checks without writing. The Python dependencies
are locked with uv. `make verify-assertions` runs the relocated 18-case assertion
suite and positive/negative AOT analysis with its original pinned .NET 11 SDK.
The runner, hosting and native-consumer probes keep their independent .NET 10 baseline.

The six adapted test workflows use native MSTest APIs rather than transferring
another framework's execution or fixture assumptions. Their shared
[quality reference](skills/mstest/references/test-quality.md) separates
static findings, possible gaps and executed evidence without assertion quotas.

[Failure-prevention lessons](skills/mstest/references/failure-prevention.md)
turn capture/conversion/privacy findings into reusable examples of likely agent
mistakes. They are independent of the original phase plan and project-specific
scenario names. [Protocol examples](skills/mstest/references/telemetry-contracts.md)
remain available when that boundary is in scope.

The AOT workflow distinguishes generated discovery, direct invocation, managed
fallback and actual Native AOT execution. Repository-specific telemetry stacks
and project placement belong to local repository guidance. The shared plugin
keeps native testing mechanisms and general contract examples independent of
a particular producer, receiver or storage implementation.

Native cancellation, base/derived lifecycle, sequential versus concurrent work,
shared versus per-invocation resources, typed enum selectors and named string
constants apply across these scopes. Required evidence must be asserted, and
structured values retain their actual types. API details stay in the relevant
reference instead of being copied into every skill.

Previous runtime checkpoint (2026-10-17): account plugin 3.2.0 is saved and read back: all 28
uploaded files match source and archive, all 29 remote paths are retained and
the generated manifest is synchronized. Compatibility checks pass on 4.4.1
(29 sample cases) and 4.5.1 (31), each with five expected-outcome runner probes
and seven native source-location checks. Scoped JetBrains inspection reports
zero findings; package, JSON/YAML and 71 local links validate. The
[audited 3.0.1 evaluation](evals/automatic-discovery/3.0.1.md) retains its initial
activation miss, retry and corrected failures. No fresh model evaluation is
claimed for 3.2.0. The obsolete artifacts and two owned evaluation workspaces
were removed after retaining the compact audit. Native AOT/hosting assets are
unchanged; their existing dated evidence remains separate from these checks.

Expansion checks (3.2.1, 2026-10-17): nine unique skills pass frontmatter and UI
metadata validation; 106 local links and the 45-file archive validate. Installer
checks cover all-skill idempotence and conflict detection before any link is
created. The native runner/hosting/AOT fixtures are unchanged from the passing
3.2.0 CI run. The new skill descriptions have not had a fresh-chat selection
evaluation; historical evaluations remain evidence for their recorded versions.

Scope correction (3.2.2): the portable package contains eight generic skills and
43 files, with 101 local links checked. Project-specific registration, packages and
the distinctions among its four projects now live in the consuming repository's
local skill. The unit-generation isolation advice stays scoped to unit tests.

Native stack checkpoint (3.2.3): the examples use AllMicrosoft and native 4.5.1
APIs without compatibility compilation branches or a copied invocation token.
The 31 examples, five outcome probes and seven declaration-location checks pass.
Runner policies, real hosting and published managed/Native AOT consumers pass
with AllMicrosoft. Scoped inspection reports zero findings. The eight skills,
111 local links and 44-file package validate. The plugin description explicitly
records the chosen SDK, platform, extension profile and coverage provider.

Lifecycle guidance checkpoint (3.3.0): resource-lock scheduling, mutation-analyzer
visibility, optional hosted injection and per-test temporary-directory behavior
were checked against the installed 4.5.1 package and its exact upstream commit.
The eight skills, UI metadata, 113 local links and 44-file archive validate.
Executable fixtures and scripts are unchanged; their dated runtime evidence
above is retained. No fresh model-selection or runtime-probe result is claimed
for this guidance-only release.

Execution/routing checkpoint (3.4.0, 2026-10-19): native MTP on .NET SDK 10.0.402
discovered and ran both existing fixture rows, producing TRX and Cobertura.
The coverage file had no classes, so no coverage percentage is claimed.
The same fixture passed through a `.slnf` referencing `.slnx`. Independent
description-level review selected the intended skill for 16 requests across
execution, project inclusion, extensions, reviews and an unrelated request.
This is not a fresh-host automatic-selection benchmark. No regression tests
were added; the existing helper checks and packaged-skill validation were used.

The repository-local facts live in [AGENTS.md](AGENTS.md). Validation commands and
reviewed evidence remain below. Historical model-selection evaluations are
version-specific and do not establish fresh model behavior for later releases.

## Installation

Install publicly from the [ANcpLua Codex marketplace](https://github.com/ANcpLua/ancplua-dotnet):

```sh
codex plugin marketplace add ANcpLua/ancplua-dotnet
codex plugin add mstest-extensions@ancplua-dotnet
```

This installs the plugin's two native skills and their supporting files. Start a
new session after installation. Use one active installation source for this plugin
to avoid duplicate skill triggers. Marketplace distribution is separate from the
OpenAI public directory review process.

The preferred ChatGPT/Codex installation is the **MSTest Extensions** plugin,
which packages the skills and their references without an MCP server or external
service dependency. Version 3.4.0 preserves automatic invocation for relevant
MSTest code work. [Fresh-chat evaluations](evals/automatic-discovery/README.md),
including a [run with memory disabled](evals/automatic-discovery/without-memory.md)
and the [3.0.0 scenarios](evals/automatic-discovery/3.0.0.md),
record actual selection and navigation behavior separately from the example
suite. Selection remains the agent's decision on each request.

Build an account-upload archive with:

```sh
python3 scripts/package_plugin.py --output /tmp/mstest-extensions.zip
```

The archive contains `plugin.json` and both directories under `skills/`. Upload it
through Plugin Creator, then install the returned plugin in the intended account.
After confirming installation, remove a duplicate standalone installation of
the same skill from that host's discovery directory. Keep one active source.

For clients using standalone skill directories, the following remains an
alternative installation path:

Python 3.10+ and directory symlink support are required for the helper scripts.
The skill's prose can also be copied into another Agent Skills-compatible client.

```sh
python3 scripts/install.py
# Also install for Claude Code:
python3 scripts/install.py --claude
```

The default links both skills under `~/.agents/skills` for Codex. `--claude`
also links them under `~/.claude/skills`. All destinations are checked before any
link is created; existing unrelated destinations are preserved. Use `--agents-dir` / `--claude-dir` for custom discovery roots.

Invoke `$mstest` with, for example: “Create a reusable MSTest data
attribute and custom assertion for these scenarios, including rejection tests.”

## Verification

The checked-in sample SDK is 4.5.1, with .NET SDK 10.0.401 and MTP 2.5.1.
The verifier copies the examples into temporary workspaces and selects an exact
MSTest.Sdk version through each copy's global.json. It checks resolved versions,
discovery, behavior, original failure reports, changed API fingerprints and
reuse of unchanged evidence. Consumer projects are not modified.

```sh
python3 scripts/verify_versions.py 4.5.1
python3 scripts/test_inspect.py
python3 scripts/test_install.py
python3 scripts/check_links.py
```

Pass another exact SDK version to the same verifier when updating. CI runs the
native 4.5.1 baseline on pushes and supports a manually selected version. It does
not claim compatibility until that version's checks pass.

| SDK / framework / adapter | MTP | Passing examples | Verified runner probes |
| --- | --- | ---: | ---: |
| 4.5.1 | 2.5.1 | 31 | 5 |

Two cases verify inline and dynamic `ArgumentsDisplayName` through discovered
names and executed arguments. Their source uses native 4.5.1 APIs directly.
Shared examples cover custom data,
assertion rejection, conditions, execution attributes, diagnostic failure,
async suspension/cancellation and per-row resource isolation. Recommended MSTest
analyzers remain enabled and warnings are errors.

A real child-runner discovery check verifies file/line navigation for declared
method attributes and tests with a class-created execution wrapper. Navigation
comes from the original declared attribute; the wrapper factory copies no caller
metadata and requires no `ExplicitCallerInfoArgument` suppression. On 4.5.1,
the internal executor declares its experimental dependency and reads the native
invocation token; the existing rows compare native context identity with
constructor injection. The failure
probe project references the example assembly, exercising the same extension
implementation rather than compiling another copy.

For JetBrains inspections after tests have compiled the projects:

```sh
jb inspectcode MSTestExtensions.slnx --no-build --severity=SUGGESTION --format=Xml --output=artifacts/inspections.xml --properties=Configuration=Release --no-updates
```

The solution includes the intentionally failing probe executable; use the
verifiers above for execution rather than treating a whole-solution test
failure as an unexpected regression.

The probe verifier also checks seven original declaration locations through native
JSON discovery and resolves the child assembly through MSBuild TargetPath.

The probe executable deliberately returns exit 2: three failures must preserve
their original messages, one result is inconclusive, and one condition skips its
body. The verifier checks every outcome in TRX. Logs and reports stay in ignored
`artifacts/`; raw local paths, package caches and test outputs are not installed
or published with the skill.

The plugin also packages an isolated capability verifier and its fixtures:

```sh
python3 skills/mstest/scripts/verify_capabilities.py --mstest-sdk 4.5.1 --hosting --native-aot
```

It verifies seven discovered runner-policy cases across six real child runs:
run/skip/drop, CLI selection before the provider, a throwing filter, retry
recovery/exhaustion and cooperative cancellation joined before cleanup. Three
hosted case identities use four distinct scopes across two data rows and a retry;
async disposal follows cleanup, and every controller/worker host is disposed.
The managed and osx-arm64 Native AOT published consumers each execute six cases:
five pass and one deliberate typed-value rejection preserves its original
failure. Generated invocation, original discovery locations, exact Int64 data
arguments and async lifecycle ordering are checked independently. The full
[evidence contract](skills/mstest/references/executable-evidence.md)
keeps versions, entrypoints and limits separate.

These checks cover the stated fixtures. They do not establish optional hosting
under AOT, Windows UI, browser execution, arbitrary custom attributes or every
retry/filter policy. The direct executable checks do not claim to fix the
separate official MSBuild/TRX controller limitation. Fresh-chat evaluations above
record individual 1.0.1 installed-host requests; they do not establish model
quality or trigger reliability for later releases across models, prompts or hosts.

## Sources

The initial examples were authored using the supplied MSTest 4.4.1 capability
suite (historical provenance; the current examples no longer target 4.4.1). The [4.5.1 API notes](https://github.com/ANcpLua/MSTest-4.4.1/tree/scout/mstest-4.5.1/delta/4.5.1)
guided the update; the sample suite on that branch still pins 4.4.1, so published
4.5.1 packages were resolved and tested separately. Framework source is
[microsoft/testfx](https://github.com/microsoft/testfx), with per-package commits
recorded in the version notes. Portable [source routes](skills/mstest/references/sources.md)
always begin with the consumer's resolved API.

## License

MIT. See [LICENSE](LICENSE). The package includes its license, app icon,
[privacy policy](PRIVACY.md) and [terms of use](TERMS.md).
