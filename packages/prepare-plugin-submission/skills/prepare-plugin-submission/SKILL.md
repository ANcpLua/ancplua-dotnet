---
name: prepare-plugin-submission
description: Guide developers from a GitHub repository, ZIP or source folder through source-backed understanding, live official docs, native multiple-choice confirmation, repairs, tests, packaging and submission preparation. Use for OpenAI plugin creation, contribution, submission readiness, saved wizard sessions and modern MCP v2 engineering.
---

# Submission Studio

Own the preparation work. Assume constructive intent and help the developer
finish a correct submission with minimal effort. Inspect and pre-draft before
asking anything. Do not ask why a repository is public, demand a creator-written
use-case inventory, or impose enterprise paperwork on an ordinary integration.
Honor explicit private, audit-only or ZIP-only requests.

## Start the implemented wizard

1. Read [wizard workflow](references/wizard.md) and `scripts/wizard.py` before
   executing it. Store sessions outside the target and installed plugin.
2. Start from the selected source:

   ```sh
   python3 <skill>/scripts/wizard.py start --session <work>/submission.json \
     --source <github-url-or-local-folder-or-zip> --host chatgpt --actor-id <this-agent-id>
   ```

3. Read the saved next action and follow its owner:

   ```sh
   python3 <skill>/scripts/wizard.py next --session <work>/submission.json
   ```

Use `--goal audit` for a bounded audit or `--goal private-preparation` when that
scope was selected. Unspecified preparation defaults to the suggested public
route. Source inspection never executes target code. GitHub acquisition pins a
commit; `--ref` and `--plugin-root` select a known revision/root. Reuse authorized
GitHub access. If direct retrieval is unavailable, use an available GitHub
connector to materialize the exact source and provide its provenance through
`--source-info`; never ask the developer to set up credentials unnecessarily.

The existing modules implement source acquisition, live doc sync/indexing,
source drafts, persisted native questions, independent review intake/runner,
source-bound repairs and portable bundles. Read [architecture](references/architecture-2.3.md)
for component ownership and [implementation coverage](references/implementation-plan-2.3.md)
for exact validation scope. Do not confuse an implemented adapter with a host
interaction that has actually been exercised.

## Follow the current action

Use `next.id`, `next.actor`, `pending_jobs`, `question_plan` and `native_widget`.
Do assistant-owned inspection, model-assisted synthesis, authorized repairs,
tests and drafting yourself. Reuse existing facts and answers. Show the current
stage, useful result and next action in plain language; keep machine records
and command details internal unless requested.

The automatic draft uses declared skills/tools, implementation registrations,
README/context and existing tests. Read the relevant implementation and refine
its meaning before presenting it when declarations are vague or disagree with
code. Use `refine --input <record>` with current `content_sha256`, `provider`
and a complete `draft` containing source-referenced tasks, concrete direct and
indirect prompts, expected behavior, ordinary boundary examples and claims.
This is agent work; the creator does not fill the record. Inferences describe
intent and supported behavior; they are never execution results.

### Native Q&A only for actual choices

Use the available `chatgpt.app` question harness. The adapter's `native_widget`
already uses its supported schema. Emit that object through the native GenUI
`ask_user_input` widget and end the turn. Persisted defaults stay in the session;
the widget exposes no prechecked-checkbox field. Offer **Use suggested setup**
first and let the creator adjust compatible tasks/boundaries using multi-select,
or audience/hosts using single-select. Optional prose is a correction escape
hatch, not a normal requirement.

After the real answer, call `choose --input <response>` with the saved
`question_id`, `revision` and selected IDs/labels. Include an optional correction
or actual external `observation` only when supplied/observed. The business logic
rejects stale choices and generates the test plan, claims and reviewer notes.
Never invent a native selection. If this host lacks the question provider,
continue independent work and leave only the dependent choice pending.

### Independent agent and execution preflight

After setup confirmation, dispatch the saved independent-review request through
a fresh available agent. Give it the pinned source, selected docs, confirmed
understanding and task; do not give it a desired verdict. Do this concurrently
with independent tests when possible. Use a host job ID and preserve actual
output. Record an actual outstanding dispatch using `review` with `status:
Running`, the same request binding, `provider`, `job_reference` and timezone-bearing
`dispatched_at`; resume that job rather than launching a duplicate. A configured external agent runner can instead use `run-review --runner
<argv-json>`, receiving the request on stdin and returning structured findings
on stdout; no shell is used.

Import actual agent evidence with `review --input <report>`. The report needs
current `binding`, `docs_sha256`, `request_sha256`, distinct `reviewer_id`,
`provider`, `origin: observed`, a summary, findings and `evidence.file/sha256`
for the raw output. Each finding needs ID, message, correction and inspected
source path. Official requirements and guidance also need a current primary document ID,
hash, exact supporting span, applicability and failed observation. Synthetic
reports are allowed only in explicit fixture sessions.

If the host has no independent agent, record `status: Unavailable` with a reason
using the same bound request. Keep preparing; do not ask the creator to become
the reviewer or label an unperformed check as passed.

Use the executed package report and available authorized tests to fix concrete
issues. `apply-fix --input <fix>` applies bounded replacements with an exact
source digest and per-file before hashes, then re-inspects and rechecks. A
prepared proposal can be presented with an apply/adjust native choice. Do
routine reversible work already authorized by the request without another
approval. For available SDK/Inspector/mcpdo/host workflows read
[commands](references/workflows.md), [host reports](references/host-reports.md)
and [evaluation](references/evaluation.md). A tool result, synthetic capture,
agent opinion or static scan does not establish an actual host pass.

## Live official authority

The wizard synchronizes the official `llms.txt`, retrieval export and primary
pages selected from inspected capabilities. `sync-docs` revalidates them;
`search-docs --query <text>` retrieves indexed headings/spans. A host fetcher can
supply observed documents through `sync-docs --input`; each needs its official
URL, text, provider and actual observation time. Use [source inventory](references/official-docs-sources.json).

Model training is not authority for OpenAI review rules. Enforced official
findings need current applicable primary evidence. Keep guidance, engineering
checks and creator choices distinct. An unavailable page is a retrieval gap,
not a defect in the target; continue independent preparation. Recheck primary
pages at release-sensitive decisions. Only fetch/activate quote, checkout or
restaurant conversion primary pages when implementation detects that activity.

Use modern MCP v2 for new implementation and record the actual dated wire
protocol separately. Read [SDK implementation](references/typescript-sdk.md),
[shared MCP](references/shared-mcp.md) and [mcpdo](references/mcpdo.md) when those
components apply. Avoid new v1/SSE scaffolds or hand-written protocol plumbing.
Default to OpenAI. Read [Claude guidance](references/claude.md) only for an
explicitly selected cross-platform/migration task.

## Save and continue

The bundle derives listing drafts, test prompts and reviewer notes from the
same confirmed selections. Keep working evidence separate from the public
plugin ZIP. Use `pause`, `resume`, `revisit`, `export` and `restore` to preserve
progress; version-1 sessions migrate without invented confirmations. Source,
choice and documentation changes recompute affected outputs while preserving
unrelated intent and still-valid evidence. Never edit a hashed generated pack
in place; use `rebuild`.

Persist the exported checkpoint through the host's durable file/project or
owning repository mechanism. A transient path alone is not cross-chat storage.
Blank unloaded templates are expected. Use [OpenAI lifecycle](references/openai-lifecycle.md)
and [review evidence](references/review-evidence.md) for remaining component work.

Guide each requested portal checkpoint with the exact ZIP and prepared fields,
interpret copied findings and handle repairs. The creator operates the portal
and confirms creator-owned declarations. Do not perform public uploads, submit
reviews or publish through this preflight workflow. Retain actual plugin/release
references and distinguish prepared, checked, host-verified, submitted, approved
and published. Finish with the concrete next action and verified limitations;
a directory of files alone is not a guided completion.
