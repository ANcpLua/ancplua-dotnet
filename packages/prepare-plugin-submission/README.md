# Submission Studio 2.3.2

Version 2.3.2 aligns the canonical and compatibility manifest versions and ships
the same source to the [fixed cloud entry](https://github.com/ANcpLua/ancplua-dotnet/blob/main/docs/cloud-plugins.md) and Git
marketplace. Version 2.3.1 clarified the wizard startup sequence. Runtime and
templates retain their imported 2.3.0 behavior; historical evidence keeps its
original version.

A guided preparation tool for OpenAI plugins. Point the agent at a GitHub
repository, ZIP or source folder; it inspects the implementation, retrieves
applicable current official documentation, drafts the submission and guides
the next useful action. Ordinary preparation uses suggested defaults and
native multiple-choice selections. Developers do not author audit JSON,
refusal policies or a use-case inventory.

The existing Python modules now implement the
[five-stage architecture](skills/prepare-plugin-submission/references/architecture-2.3.md):

1. Pin source, select the plugin root and synchronize official docs. Specialized
   quote, checkout and reservation primary pages activate only for detected activities.
2. Draft tasks, personas, prompts, expected outcomes and listing claims from source;
   let the host agent refine their meaning with inspected-file references.
3. Save native accept/adjust choices and derive cases from the selected tasks.
4. Run package checks and dispatch independent agent review when available;
   show concrete findings and apply source-bound prepared fixes.
5. Generate listing/reviewer materials and separate public ZIP/private checkpoint
   artifacts, retaining source, docs, choices and evidence through export/restore.

```sh
python3 skills/prepare-plugin-submission/scripts/wizard.py start --session ../submission.json --source target.zip --host chatgpt --actor-id primary-agent
python3 skills/prepare-plugin-submission/scripts/wizard.py next --session ../submission.json
```

The host agent renders `native_widget` using the advertised `chatgpt.app` Q&A
harness and maps the real response through `choose`. The same agent performs
model-assisted synthesis, independent-review dispatch and available host tests.
The Python runtime supplies executable adapters and persisted contracts; it
contains no model service, new MCP server or custom question UI. Actual native
widget rendering remains unverified in this release; deterministic tests cover
its payload, response mapping and continuation. See [release evidence](evals/2.3.0.md).

Use `--goal audit` or `--goal private-preparation` for those explicit scopes.
GitHub reads reuse available authorization and pin a commit; a connector archive
can carry exact-source provenance. Source inspection executes no target code.
An unavailable documentation page or agent provider is a recorded gap, not a
new submission rule. Current official findings require applicable primary spans
and target observations. Static checker rules and the older 49-row coverage
catalog retain their historical classification.

Public local MCP uses the documented desktop-only allowlisted partner route
when current guidance establishes it. Modern MCP v2 kits and ChatGPT/Codex
report ingestion remain available. The wizard guides remaining portal steps,
prepares fields and interprets actual observations; the creator performs portal
upload, review submission and publication. Blank templates are expected before
a target is loaded. A synthetic session never establishes an actual host pass
or public release.

Read the [workflow](skills/prepare-plugin-submission/SKILL.md),
[wizard commands](skills/prepare-plugin-submission/references/wizard.md),
[host report contract](skills/prepare-plugin-submission/references/host-reports.md),
and [implementation coverage](skills/prepare-plugin-submission/references/implementation-plan-2.3.md).
Historical [2.0.1 self-audit](self-audit/2.0.1/coverage-matrix.md) remains
versioned evidence for that earlier target.

```sh
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s evals/runtime -v
```

Synthetic broken-ZIP, desktop stdio and review-prep targets are under
`tests/fixtures/`. Native prompt/grader scenarios under `evals/` are separate
agent evaluations. TypeScript assets retain pinned v2 SDK dependencies and can
be built with `npm ci` and `npm run build`. Review-prep stays a ZIP so only the
Submission Studio product skill is discoverable.
