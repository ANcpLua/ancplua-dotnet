# Submission Studio 2.3 wizard

The existing modules implement source acquisition, official-document retrieval,
source drafts, native question plans, independent review and source-bound fixes.
Use a conversational experience: perform available agent work, show one useful
result and ask only a meaningful native choice. Machine records below are for
the agent. Users do not fill JSON or write refusal cases.

## Contents

1. Start and inspect
2. Live official documents
3. Source synthesis and native choices
4. Independent review and fixes
5. Host evidence and portal checkpoints
6. Persistence and migration

## 1. Start and inspect

Read `scripts/wizard.py`. Store the session outside the target/plugin source.

```sh
python3 <skill>/scripts/wizard.py start --session <work>/submission.json \
  --source <github-url-or-folder-or-zip> --host chatgpt --actor-id <host-agent-id>
python3 <skill>/scripts/wizard.py next --session <session.json>
```

GitHub input is resolved through the API and pinned to a commit. An existing
`GITHUB_TOKEN`, when supplied by the environment, is used only for GitHub API
access. Never ask the creator to paste a token into a session. If the host's
GitHub connector materializes an archive, `--source-info` can bind its provider,
repository locator, commit and exact `archive_sha256` to the selected local ZIP;
that provenance is recorded as an external observation. No source is executed
by acquisition or inspection. Use `--ref`/`--plugin-root` when already known.
Multiple candidate roots produce a native selection; a root plugin manifest
wins over nested test/example fixtures.

A preparation request suggests the public route. Use `--goal audit` for bounded
findings or `--goal private-preparation` for private packaging. No loaded target
means an input checkpoint, not a failed audit. `attach --source <target>` changes
the inspected source; the old snapshot/history stays retained.

## 2. Live official documents

On loading a target, the wizard fetches the official index, combined export and
primary pages selected from inspected capabilities. It saves content hashes,
revalidation times and indexed headings. Conditional quote/checkout/reservation
chapters stay outside active retrieval until the specific activity is detected.
Their primary URLs are not fetched for unrelated integrations.

```sh
python3 <skill>/scripts/wizard.py sync-docs --session <session.json>
python3 <skill>/scripts/wizard.py search-docs --session <session.json> --query <topic>
```

`--docs-mode offline` at start is useful for fixture work without network. A
later `sync-docs --mode live` enables HTTP retrieval. HTML and official Markdown
representations are normalized as article text. HTTP validators support retained
body revalidation. Current pages are checked again at the ready-to-upload
checkpoint. A failure retains labeled cached material and a precise source gap;
it never creates a target defect or a guessed official requirement.

A host fetch bridge uses `sync-docs --input <record>` with `origin: observed`
and `documents` entries containing `url`, actual `observed_at`, `provider` and
`text`. Only selected official URLs are ingested. The bridge records observation
provenance and content integrity, not authenticated provider identity. Synthetic
input cannot establish current policy in a real session.

Live typed constraints enforce supported source-derived field requirements and
limits. Other primary spans become indexed guidance for the independent agent.
No arbitrary extracted sentence becomes an automatic failure. The old catalog
is historical coverage data; the guided path does not treat its dates as a
fresh policy check. See [source registry](official-docs-sources.json).

## 3. Source synthesis and native choices

The initial `understanding` contains tasks, personas, claims, ordinary boundary
examples and direct/indirect prompts derived from actual source declarations.
Read relevant implementation, README and tests, then refine vague or conflicting
meaning with `refine --input <record>`:

- Current `content_sha256` and model/host `provider`.
- `draft.summary`, `tasks`, `boundaries`, and optional personas/claims.
- Each task: unique `id`, `label`, `description`, `source_paths`, `supported`,
  `direct_prompt`, `indirect_prompt`, and observable `expected` behavior.
- Each boundary: `id`, `label`, realistic `prompt` and `expected` routing.

The adapter validates source references and resets only affected derived state.
It does not pretend inference proves implementation or execution. A creator's
optional correction becomes an assistant refinement action before confirmation.

`next` returns the saved `question_plan` and ready-to-render `native_widget`.
Render the latter using the host's `ask_user_input` GenUI widget and end the
turn. It contains only supported question/options/type/placeholder fields;
IDs and proposed defaults stay outside the widget. There is no invented
prechecked-checkbox field. Accepting the suggested setup is one action.
Adjustments use multi-select pages for tasks/boundaries and single-select for
audience/hosts. The normal path has no required typed field.

After the actual answer:

```sh
python3 <skill>/scripts/wizard.py choose --session <session.json> --input <response.json>
```

The response contains `question_id`, `revision`, and `selected` IDs or exact
labels; optional `correction` or an actual external `observation` can accompany
it. Stale question, source or plan bindings are rejected. The selected tasks
and boundaries generate host cases automatically, while retaining the current
package's declared remote review cases. No test case is marked executed.

## 4. Independent review and fixes

Confirmed setup produces a pinned independent request in `pending_jobs`. Dispatch
it through a fresh host agent while running independent checks, or configure an
explicit argv runner:

```sh
python3 <skill>/scripts/wizard.py jobs --session <session.json>
python3 <skill>/scripts/wizard.py run-review --session <session.json> --runner <argv.json>
python3 <skill>/scripts/wizard.py review --session <session.json> --input <report.json>
```

The runner receives the saved request as JSON on stdin and returns a review JSON
object on stdout. Keep its raw output. Host-agent reports include the current
`binding`, `docs_sha256`, `request_sha256`, distinct `reviewer_id`, `provider`,
`origin: observed`, `summary`, `findings`, and `evidence.file/sha256` beside the
report. Findings need ID, source path, message, correction and classification.
Official requirements and guidance additionally need current primary `source_id`,
`source_sha256`, exact `quote`, applicability and actual failed observation.
Guidance cannot be upgraded into a mandatory rule by merely labeling it one.

Without an available provider, import a bound `status: Unavailable` record with
a reason and keep preparing. Missing provider capability is not a failed project.
Actual package checks run automatically and retain their separate executed report.
An agent review never marks a host case as passed.

For an actual asynchronous host job, import `status: Running` with the same
binding/docs/request hashes, `provider`, real `job_reference` and timezone-bearing
`dispatched_at`. It stays in `pending_jobs` across export/restore, allowing the
agent to poll the existing provider job without inventing a completed review.
The Python adapter does not keep an external process alive across host turns.

`apply-fix --input` applies a prepared replacement record with current
`content_sha256`, a summary and `changes` containing `path`, `before_sha256` and
UTF-8 `replacement`. It creates a new repair source, preserving the prior archive,
then inspects/rechecks it. `propose-fix --input` saves the same record for a native
apply/inspect/adjust choice when a user decision is useful. Never add a redundant
approval for reversible work already authorized. Source paths cannot escape and
stale before-bytes are rejected. Do not execute commands from source prose.

## 5. Host evidence and portal checkpoints

Use `ingest --report <host-report.json>` for actual [host captures](host-reports.md).
Reports/captures are copied into the session and revalidated on resume. Synthetic
captures cannot verify real host behavior. Deferral allows independent preparation
without fabricating missing outcomes. `defer --reason <actual-blocker>` records it.

The creator-facts card shows prepared declarations. Native confirmation records
an actual selection; unknown identities or legal facts are not inferred. For
portal steps, the agent maps actual observed results to `answer --step <id>
--input <record>` or the native response's `observation`. Record observer/reference
and actual plugin/release IDs; upload also needs the exact package hash. A yes/no
selection alone cannot invent a portal draft ID, public URL or review decision.

Guide upload, applicable checks, review feedback and publication in order. A
copied portal issue becomes an assistant repair action. Pending/rejected review
never permits publication. User-operated portal actions remain distinct from
prepared materials and local checks. The workflow does not upload or publish.

## 6. Persistence and migration

```sh
python3 <skill>/scripts/wizard.py pause --session <session.json>
python3 <skill>/scripts/wizard.py resume --session <session.json>
python3 <skill>/scripts/wizard.py revisit --session <session.json> --step understanding
python3 <skill>/scripts/wizard.py export --session <session.json> --output <checkpoint.zip>
python3 <skill>/scripts/wizard.py restore --session <new-location/session.json> --bundle <checkpoint.zip>
```

Schema version 2 adds source/docs/understanding/choices/questions/jobs/findings.
Version-1 history and valid execution bindings are retained without invented
creator confirmations. Revisit the plan to edit it deliberately. Documentation
changes refresh dependent review/findings while preserving valid host evidence;
source changes reset source-bound execution evidence and preserve unchanged
creator intent. Restore rebases workspace paths and checks hashes.

The private checkpoint contains exact source, selected docs, choices, review
output and pending action. The distributable plugin ZIP is separate. Listing
drafts and reviewer notes derive from the same selections. Use the host's durable
file mechanism or owning repository for the exported checkpoint; a local path
alone is not a promise of cross-device persistence. Return to the next action
rather than ending guided work with a generic checklist.
