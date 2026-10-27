# Implementation plan: dynamic docs and low-friction choices

Status: implemented as the 2.3.0 runtime. The existing modules were refactored
in place rather than adding the proposed stack of adapter modules. This file
retains acceptance scenarios and records how the shipped implementation maps
to the plan. See `evals/2.3.0.md` at the plugin root for actual validation scope.

Read [architecture](architecture-2.3.md) for the interaction and authority
contract and [source registry](official-docs-sources.json) for the complete
requested documentation inventory. This plan replaces an intake based on
open-ended creator-authored use cases with automated drafts and native choices.

## Contents

1. Work packages
2. Data contracts and interfaces
3. Existing-file integration
4. Acceptance scenarios
5. Release evidence and completion

## 1. Work packages

| Work package | Deliverable | Depends on | Completion evidence |
| --- | --- | --- | --- |
| A. Source acquisition | Pinned GitHub/ZIP/folder snapshots, plugin-root selection and capability evidence. | Existing bounded file reader. | Public repo, authorized private repo, monorepo and ZIP fixtures; no unnecessary intent question. |
| B. Documentation sync | Official index/export retrieval, primary-page revalidation, normalized local index and conditional-page selector. | Registry and fetch adapter. | Recorded HTTP fixtures plus a clearly labeled live smoke run when network is available. |
| C. Rule resolution | Source-bound candidate rules, applicability and enforcement classification; migration of hard-coded policy assertions. | A and B. | Supported/unsupported/conflicting rule cases and targeted invalidation tests. |
| D. Understanding + choices | Automatic source-backed draft, generated test plan and native Q&A adapter with default-accept and adjustment flows. | A, B and question-provider contract. | Deterministic contract tests and actual-host widget selection evidence. |
| E. Independent preflight | Independent agent job, existing executable checks, grouped actionable findings and prepared fixes. | C and D. | Raw agent outputs, controlled execution logs, fix/retest journey and unavailable-provider case. |
| F. Bundle + migration | Version-2 session, derived listing/reviewer materials, export/restore and impact-aware recomputation. | A–E. | Relocation, version-1 import and exact source/docs/selection binding tests. |
| G. Release validation | Full acceptance suite, negative fixtures and host exercise; a truthful capability inventory. | A–F. | Versioned evidence and release notes with unperformed checks clearly identified. |

Implement A and B independently, then C/D, then E/F. Keep each work package
reviewable. New adapters accept injectable inputs so most checks do not depend
on live network, paid model calls or external uploads. Do not add a legacy MCP
server to orchestrate this workflow.

## 2. Data contracts and interfaces

The following records are implemented across the existing modules. The wizard
reference documents the current CLI and host handoffs.

| Record | Minimum fields | Producer / consumer |
| --- | --- | --- |
| `SourceSnapshot` | kind, locator, resolved commit or archive hash, plugin root, file inventory, observed visibility, capability facts with evidence. | Source adapter → inspector/reducer. |
| `DocumentSnapshot` | source ID, requested/resolved primary URL, role, fetched/revalidated time, body hash, body/heading index, HTTP validators, retrieval status. | Docs adapter → rule resolver/bundle. |
| `RuleCandidate` | stable ID, primary document hash and span, classification, applicability predicate, parsed constraint and extraction provenance. | Resolver → structured validation. |
| `RuleFinding` | rule ID, target evidence, observed outcome, status, actionable fix and impacted artifact/case IDs. | Checks → next-action reducer. |
| `UnderstandingDraft` | source/docs bindings, summary, personas, task IDs, success criteria, constraints, prompts, claims, provenance and unresolved ambiguities. | Synthesis adapter → creator choices/review. |
| `QuestionPlan` | ID, reason, session revision, binding, mode, unique option IDs/labels, proposed defaults and next transition. | Pure question planner → native adapter. |
| `ChoiceEvent` | question ID/revision, selected IDs or explicit draft acceptance, provider response provenance and time. | Native response → reducer. |
| `PreflightJob` | job ID/provider, snapshot bindings, check kind, state, output references and actual start/finish observations. | Host adapter → reducer. |
| `SubmissionBundle` | source, docs, understanding and choice hashes; output inventory; actual checks; pending actions. | Generator → export/restore. |

Pure functions should cover `select_documents`, `validate_rule`,
`draft_question_plan`, `apply_choices`, `derive_test_plan`, `next_action`,
`affected_by_change` and `build_bundle_manifest`. HTTP, GitHub access, model
requests, native widget rendering, filesystem writes and agent execution belong
to adapters. Do not hide these effects inside a verdict function.

Synthesis is a model-assisted draft, with deterministic schema and reference
validation. Validate referenced files/doc spans, unique item IDs, route choices
and selected option membership. Do not pretend syntax validation proves an
inference correct; review actual source-backed meaning in the independent pass.

### Documentation pipeline

1. Load the official source registry and fetch the live index; resolve current
   aliases without losing original IDs.
2. Read source capabilities and select applicable primary pages. Gate each
   specialized commerce page on its specific detected activity.
3. Retrieve the combined export when available as a retrieval aid. Isolate
   conditional chapters until applicable. Fetch/revalidate selected primary
   pages; fall back from unavailable Markdown to the official HTML article.
4. Normalize bodies, headings and checksums. Record failures and freshness
   separately from target defects. Continue unaffected preparation.
5. Extract rule candidates from selected text; retain spans and classification.
   Validate their scope and test method before admitting official findings.
6. Revalidate release-sensitive sources at the relevant release checkpoint.
   Content changes invalidate only dependent rules/outputs, not all user input.

Do not substitute training-memory rules when discovery, a chapter or a primary
page is unavailable. Do not require the creator to repair an unavailable docs
endpoint. Keep the last supported observation and identify the affected check.

### Native-choice pipeline

1. Persist the generated draft, suggested settings and question plan.
2. If no meaningful ambiguity remains, show one concise summary and a native
   accept/adjust choice at the appropriate scope checkpoint. Avoid duplicate
   confirmation of explicit instructions already given in the conversation.
3. Render only the advertised `chatgpt.app` widget fields: question, options,
   `single_select`/`multi_select` and contextual optional free-text placeholder.
4. End the conversational turn after rendering. Resume on the real user answer,
   resolve labels through the saved map, and reject an obsolete revision.
5. Derive the confirmed record and all affected prompts/claims automatically.

Default acceptance is one action. Multi-select is used for adjusting compatible
tasks or boundaries; mutually exclusive route/audience choices are single-select.
The adapter must not emit unsupported preselection fields. Routine completion
must not require typing, authoring decline examples or entering machine JSON.

### Review and fix pipeline

Start independent review and executable checks with explicit inputs and job
records. Require the independent pass to inspect source/docs rather than echo
the drafter's conclusion. Aggregate findings by affected task/fix. Propose a
patch when feasible, apply within existing authorization, re-inspect source and
rerun affected tests. Show an apply/adjust choice only when a meaningful user
decision remains. Record actual job results before updating a check status.

## 3. Existing-file integration

| Existing file | Required change |
| --- | --- |
| `scripts/wizard.py` | Add source/docs/synthesis/question/job adapters; persist before host-question handoff; use existing evidence ingestion/export. |
| `scripts/wizard_core.py` | Extend the pure state machine with automatic sync/draft/review states and minimal human choices; classify blockers by evidence and authority. |
| `scripts/audit_target.py` | Expand observed source features and provenance; feed the understanding draft; avoid mapping unknown optional features to a positive detection. |
| `scripts/check_package.py` and `scripts/package_core.py` | Separate structural correctness from release-sensitive policy; accept a verified current rule context in the new path and label static fallback accurately. |
| `scripts/openai_core.py` and `scripts/workflow_core.py` | Make artifact/case derivation consume the confirmed understanding and resolved rules. |
| `scripts/prepare_workflow.py` | Generate listing/reviewer materials from the same selections; retain source/docs/choice IDs in output provenance. |
| `scripts/host_reports.py` | Preserve observed-vs-synthetic results and extend binding to the relevant understanding/test-plan revision. |
| `schemas/wizard-session.schema.json` | Add version-2 records and explicit migration while preserving version-1 history. |
| `references/requirements.json` | Retain as historical coverage/seed IDs; remove its authority as a fresh runtime rule source once the resolver is enabled. |
| `SKILL.md`, `references/wizard.md`, `agents/openai.yaml` | Describe the implemented choices and available adapters only; preserve presentation and starter prompts unless intentionally changed. |

Do not remove the working 2.2.0 path before its behavior is covered by the new
tests. Version-1 import must not fabricate missing choices, current doc reads or
agent results. Keep a capability status record so a staged installation can
say which work packages are actually available.

## 4. Acceptance scenarios

Use local synthetic targets and recorded official-page responses for repeatable
tests. Add current-source smoke checks separately. Do not upload fixture plugins
to a real portal or label synthetic captures as actual host/reviewer evidence.

| ID | Scenario | Required observation |
| --- | --- | --- |
| SRC-01 | Public repository containing one plugin | Resolve/pin it, inspect and draft without asking why it is public. |
| SRC-02 | ZIP and pinned repo with equivalent source | Same inferred tasks/rule selection, with truthful distinct source bindings. |
| SRC-03 | Monorepo with two plausible plugin roots | Generated root choices; no arbitrary silent selection. |
| SRC-04 | Authorized private repo or inaccessible source | Reuse available access; if denied, offer concrete source options without inventing access. |
| DOC-01 | Official index adds or moves a page | Discover current alias, record it and re-index without a source-code rule edit. |
| DOC-02 | A primary constraint changes while the export is old | Primary page wins; affected finding is recomputed with the new hash. |
| DOC-03 | Primary page unavailable, Markdown unsupported or export unavailable | HTML/cached drafting fallback works; no invented official requirement or fabricated freshness. |
| DOC-04 | General skills/MCP integration | No specialized quote/checkout/reservation primary fetches or active rules. |
| DOC-05 | Source implements exactly one specialized activity | Only its specialized primary page is fetched and its applicable rules activated. |
| DOC-06 | Stock quote, calendar appointment or commerce mention only | No accidental specialized-activity detection. |
| DOC-07 | Old catalog or model suggests a stronger rule than current text | Rule is not promoted to an official blocker. |
| SYN-01 | README promises more than code implements | Draft identifies the supported scope and automatically proposes repair/narrowing choices. |
| SYN-02 | Valid read-only free integration | Generate practical personas/tasks/prompts without enterprise paperwork or misconduct interrogation. |
| SYN-03 | Negative routing examples | Generate ordinary unrelated/unsupported requests; creator need not author them. |
| QA-01 | All suggested settings fit | One native acceptance action; no mandatory typed fields. |
| QA-02 | Creator adjusts tasks/audience | Native multi-select for compatible tasks, single-select for audience; all outputs derive from saved IDs. |
| QA-03 | Question answered after source/draft revision | Detect stale response and show only the relevant revised choice. |
| QA-04 | Widget provider schema lacks preselection or is unavailable | Emit no invented field; preserve suggested defaults; keep unrelated work moving. |
| REV-01 | Independent agent finds a seeded mismatch | Supported finding and prepared correction; first agent's desired verdict is not used as ground truth. |
| REV-02 | Package failure is repairable | Patch, recheck and update source binding with a concise actionable explanation. |
| REV-03 | Agent/host execution unavailable | Mark the unperformed check accurately; no false project rejection or simulated pass. |
| BND-01 | Export, relocate and restore | Exact source/docs/choices survive and no developer reconstructs the draft. |
| BND-02 | Change one task or one official page | Recompute affected outputs; retain unrelated confirmations and valid evidence. |
| BND-03 | Existing 2.2.0 session | Import history, generate missing drafts and avoid blanket reconfirmation. |
| BND-04 | Public package versus private work bundle | Only deliberately distributable files enter the plugin ZIP. |

Track false-positive official blockers, missed seeded failures and needless
questions separately. For deterministic fixtures, require zero unsupported
official blockers, zero specialized-page fetches for unrelated targets and no
missed seeded package failures. Human approval of a model draft must not convert
an unrun behavioral check into a pass.

The actual-host Q&A exercise must capture the rendered choices, selected option,
saved choice event and continued wizard step. Schema tests alone cannot prove
the harness works. The independent-agent test must retain its actual output;
two mock verdicts are not two independent agents.

## 5. Release evidence and completion

Re-run relevant Python suites, skill/package validation and any affected
TypeScript checks. Retain commands, exit codes, source hashes, actual doc fetch
records, native widget observations and independent agent artifacts. Use modern
MCP v2 if a new MCP component is genuinely needed; preserve existing modern
SDK/runtime tests and do not claim new protocol coverage from Python tests.

A–F are implemented in the existing source/inspection/policy/wizard/bundle
modules. The release evidence records acceptance results and host limitations. If a host-dependent check cannot run, name that
specific unverified capability instead of declaring the entire workflow tested.
First-pass submission rate and reviewer time need real, authorized pilot data;
they are goals to measure, not promised release outcomes.

The 2.3.0 runtime performs official retrieval/indexing and persists native
question contracts. An actual native selection or portal action is a separate
host observation; schema/contract tests never stand in for that evidence.
