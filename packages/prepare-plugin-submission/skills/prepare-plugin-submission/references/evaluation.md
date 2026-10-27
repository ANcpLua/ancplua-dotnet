# Evaluation and acceptance

Use two independent layers and retain failures:

1. Inspect and validate the exact source/archive: structure, schemas, paths,
   references, listing data, runtime files, and absence of packaged secrets.
   Record tool/version/command, exit status, and archive hash.
2. Use live official documentation and native host tools, then test behavior
   in the real intended surface. Read back any saved Plugin Creator package
   and compare its source/version to the archive. Inspect its rendered listing
   and invocation. A successful upload is only package acceptance.

## Intended surfaces, all tools, and baseline comparison

For Claude plugins, use A2 and A4 to test loading and behavior on each intended
surface, and compare real prompts with and without the plugin. Record both
outputs and the usefulness difference; no measured improvement is also a valid
result. `claude plugin eval <folder> --ablation with-without` can run the
comparison in Claude Code. This cannot stand in for claude.ai or Cowork testing.

For Claude connectors, test every exposed tool through MCP Inspector and as a
custom connector in Claude. Verify successful valid-input results, validation,
permission boundaries, and useful errors. The three required working examples
are review material, not complete tool coverage. Provide a sample-data testing
account and sufficient access instructions. Report unexecuted tools explicitly.

Keep automated package/scan findings separate from functional review evidence.
Do not invent a directory requirement for a 100% suite score over every model
and surface. A local all-green suite proves only its actual cases, versions,
and tested surfaces. Apply A3's support matrix when deciding what should load.

For each representative prompt, evaluate these observations, not keyword hits:

- Did it select the correct OpenAI/Claude connector/plugin route?
- Did it inspect supplied source and preserve the intended integration?
- Did it complete available work rather than ask the creator to draft everything?
- Were missing facts separated from observed facts and real results?
- Did it use the correct platform-specific fields and required materials?
- Did it keep credentials private and avoid unrequested publication?
- Did the final handoff name actual artifacts, status, and next action?

Exercise: a skills-only package; a dual-platform remote server; malformed review
metadata; a ZIP with escaping paths; an OAuth-dependent demo; a legacy connector
question; an update under review; and a host missing terminal/browser access.
Use the bundled [scenario set](../../../evals/cases.json) and native case definitions
in that same directory. They include prompts and expected outcomes; no
developer checkout is needed. Run prompts
through the installed skill when possible. Static checks of those expectations
are not an LLM evaluation. If only one surface is tested, don't claim all hosts.

Screenshots prove what the UI visibly displays, not server correctness. A report
preview is separate from an installed-plugin screenshot. A model result without
source inspection or tool evidence cannot establish that an integration works.
Record blocked checks honestly and finish other work. Do not redefine acceptance
to make missing evidence disappear.

## Do not infer coverage from prompt counts

A single example can invoke several tools. Do not subtract the number of
example prompts from the number of exposed tools or invent how many tools are
untested. Compare the complete tool inventory with actual per-tool execution
evidence; without that evidence, coverage is unknown.

## Run the bundled scenario suite

Use the full plugin distribution for this optional benchmark. Its `evals/`
directory is at the package root, outside loaded component directories as the
native runner requires. A standalone skill installation still supports the
preparation workflow; to run the benchmark, use the full versioned distribution
from the source repository identified in its README. Evaluation definitions
are hidden from the candidate by the native runner.


The ten reusable scenarios exercise the skill's explanations through an actual
agent. In Claude Code, first inspect `claude plugin eval --help` and record the
runner and model versions. With an existing authorized account, use:

```sh
claude plugin eval <installed-plugin-folder> \
  --eval-dir evals --runs 3 \
  --model <explicit-agent-model> --judge-model <explicit-judge-model> \
  --ablation none --no-publish --trust-plugin \
  --output-dir <outside-package-results> --json <outside-package-results.json>
```

These calls consume the account's model allowance. Set an appropriate
`--max-cost-usd` limit if supported. Use three bounded trials per case, fixed
thresholds and fresh workspaces. Preserve every outcome. Do not rerun merely
to replace a failure. A with/without comparison measures a different question
from an old/new-version comparison. Keep the model, fixture, rubric and grants
identical for the latter. An internal rubric change requires regrading both.

Deterministic acceptance tests live in `tests/` and `evals/runtime/` in the full
plugin distribution. They use `tests/fixtures/` and exercise the preflight tool;
their results do not claim a real ChatGPT/Codex run or directory approval.
External host captures use the [report ingestion contract](host-reports.md).

## Evidence states and coverage

Bind each row to a case ID, actual host surface, tested source revision and
package SHA-256. Record tool grants, fixture hash, agent/judge versions, expected
and observed outcome, and a redacted evidence location. Keep correctness,
execution evidence and communication judgments separate. Check discovery and
repeat counts: zero cases, missing tools, malformed grader results and partial
runs are Blocked or Failed, never Passed. Curated synthetic grader examples
are useful calibration; do not label them human-reviewed without a human.

Keep local checks, behavioral evaluation, live host verification, review
materials, submission, approval and publication in distinct fields. For OpenAI,
O7 requires every submitted case to pass on each supported intended surface
before functional verification is complete. For Claude, retain all-tool
connector evidence and intended-surface loading/behavior checks. An offline
fixture on Claude Code does not verify ChatGPT, Codex, claude.ai, Cowork, OAuth
or a real remote server. Use the [readiness record](../templates/readiness.md).

