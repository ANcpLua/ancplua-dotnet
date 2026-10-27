# Source-driven preparation with native choices

Status: implemented in 2.3.0. Source acquisition and effectful adapters live in
`wizard.py`, source inference in `audit_target.py`, policy/index transforms in
`openai_core.py`, and native questions/session decisions in `wizard_core.py`.
The existing workflow/bundle modules consume these records directly. Actual
host-dependent verification is reported separately in the release evidence.

Read the [implementation plan](implementation-plan-2.3.md) for work packages and
acceptance criteria. The [source registry](official-docs-sources.json) is a
discovery plan, not a frozen rulebook. The existing [wizard contract](wizard.md)
describes commands that can already run.

## Contents

1. Product behavior
2. Five-stage flow
3. Components and ownership
4. Live documentation and applicable rules
5. Source-driven understanding
6. Native ChatGPT questions
7. Independent review and actionable fixes
8. Persistence and change handling
9. Evidence and rollout boundaries

## 1. Product behavior

Assume a developer who invokes Submission Studio wants constructive help
finishing the selected task. For a request to prepare a public submission,
draft that route immediately. A public repository is useful input, not a
reason to interrogate its creator. Honor explicit private, audit-only or
ZIP-only requests just as directly.
For an otherwise unspecified preparation request on a public repository,
propose public-submission preparation as the default. This starts useful work;
it does not change visibility or authorize the final publication action.

Do the inspection, drafting, requirement mapping and available checks before
asking for information. Generate personas, supported tasks, realistic prompts,
ordinary limitations and proposed metadata from the repository. Let the
developer accept the suggested setup or adjust it through native choices.
Never require the developer to author a use-case inventory, refusal policy,
evidence JSON, test plan or justification for a public repository.

Treat negative examples as ordinary routing and product boundaries: unrelated
requests, missing input, unsupported operations, or cases better handled by
another tool. Do not fill the interface with hypothetical misconduct scenarios.
A concrete permission or data problem found in the target still gets a precise
fix. The question is what this integration actually does and what the applicable
official rule requires.

Keep inferred defaults distinguishable from confirmed choices internally.
That provenance supports reproducibility; it is not another questionnaire.
Suggested publication settings do not perform a publication or accept a legal
declaration. Obtain the relevant sign-off at the actual action checkpoint.

## 2. Five-stage flow

| Stage | Automated work | Human interaction | Saved result |
| --- | --- | --- | --- |
| 1. Source + live docs | Resolve the provided repository/ref or ZIP, detect the plugin root and capabilities, synchronize the official index and applicable primary pages. | Only a concrete ambiguity such as two plausible plugin roots or unavailable repository access. | Immutable source snapshot, capability evidence, documentation snapshot. |
| 2. Understanding + tests | Draft a plain-language product summary, personas, tasks, direct/indirect/negative prompts, expected outcomes and supported listing claims. Compare docs, implementation and tests. | None while source can answer the question. | Proposed understanding and test plan, with source references and real unknowns. |
| 3. Native choices | Render the proposed setup and only material ambiguities through the `chatgpt.app` Q&A harness. | Accept the proposed setup, select changed tasks or adjust a genuine ambiguity. | Versioned confirmed selections, without recopying the draft. |
| 4. Independent preflight | Run an independent agent assessment and available automated checks against the confirmed scope and current applicable rules. Draft precise patches for findings. | Actionable decisions only: apply a prepared fix, adjust the supported claim, or continue other work. | Observed checks, review findings, patches and remaining external steps. |
| 5. Submission bundle | Generate the ZIP, listing, prompts, reviewer notes and a resumable checkpoint from the same confirmed record. Guide remaining portal actions. | Final audience/publishing sign-off and actual portal steps when requested. | Bound artifacts and recorded observations; no manual reconstruction of fields. |

Run independent inspection, documentation retrieval and tests concurrently when
their inputs are fixed. Background execution uses an actual host job/agent
capability and recorded job IDs. A process that cannot survive a turn is not
described as a persistent background job.

## 3. Components and ownership

Use pure transformations for decisions, with explicit adapters for effects.
Keep the plugin usable with host file, network, question and agent capabilities;
adding a standalone MCP server or custom web UI is not a prerequisite.

| Component | Implemented ownership |
| --- | --- |
| Source acquisition, GitHub/connector bridge | `wizard.py`: `acquire_source`, `--source-info`. |
| Source inventory and initial understanding | `audit_target.py`: `source_details`, `draft_understanding`. |
| Live docs, HTTP/cache and indexing adapter | `wizard.py`: `fetch_url`, `sync_documents`, `document_records`. |
| Selection, rule spans and typed constraints | `openai_core.py`: `select_documents`, `validate_rule`, `policy_context`. |
| Model-assisted draft refinement | `wizard.py`: `refine_understanding`, validated host-model input. |
| Native question planning and returned choices | `wizard_core.py`: `question_plan`, `apply_choices`, `derive_test_plan`. |
| Independent agent intake/runner and repairs | `wizard.py`: `import_review`, `run-review`, `propose_fix`, `apply_fix`. |
| Execution/artifact bindings and bundles | Existing `workflow_core.py`, `openai_core.py`, `prepare_workflow.py`, `wizard.py`. |

Host adapters exchange data with pure reducers; source or documentation prose
does not become shell commands or an authority to alter the workflow.

## 4. Live documentation and applicable rules

### Discovery, retrieval and freshness

Start with the official [collection](https://developers.openai.com/plugins),
[index](https://developers.openai.com/plugins/llms.txt) and
[combined export](https://developers.openai.com/plugins/llms-full.txt).
Use the index to discover the current canonical pages. Use the combined export
as a retrieval aid, then verify the relevant primary page before enforcing a
release-sensitive rule. A bundled URL or old check date is not current evidence.

Keep all user-specified domains in `official-docs-sources.json`, including the
API compatibility and evaluation pages at `/api/docs/guides/`, outside the
`/plugins/` prefix. Follow current official index aliases; record requested URL,
resolved URL, retrieval time, content hash, document role and response validators.
Restrict this documentation adapter to the official collection and explicitly
registered API pages. A source repository cannot redirect policy retrieval.

Prefer an ingestible official representation. If the Markdown twin or combined
export cannot be retrieved, parse the main article of the current HTML page and
continue. Cache snapshots and index them by canonical URL, heading and hash;
exclude navigation, footers and repeated site chrome. Bound response sizes,
timeouts and retries. A failed fetch produces a precise retrieval gap, not a
new requirement imposed on the developer.

Refresh discovery for a new submission session. Revalidate applicable primary
pages before a release decision, including after restoring an old session.
An HTTP 304 can establish revalidation of a retained exact body. Cached content
can support drafting while offline; label any affected current-policy check
unverified and continue independent work. Never report an unfetched page as
read. Retain old and new snapshots when documentation changes.

### Conditional selection

Derive capabilities from inspected implementation/configuration and, when
available, actual tool/resource inventories. Use `present`, `absent` and
`unknown`, with evidence. Do not treat unknown as a detected commerce workflow.
README ambitions are clues for further inspection, not proof of implementation.

Only request and activate the specialized quote, checkout and reservation pages
when source inspection detects the corresponding activity. A general connector,
a stock-price quote, a calendar appointment, or a mention of commerce must not
trigger those specifications. Discovery may retain their URLs. If a combined
export contains these chapters, isolate them from active retrieval and rule
extraction until the matching activity is detected; do not follow their primary
URLs in a general-integration run.

Apply the same specificity to authentication, remote MCP review, local desktop,
UI, events, extensions, migration and Responses API pages. The registry gives
selection hints; the primary page determines whether a particular rule applies.
Broadening the source or confirmed scope can trigger a new documentation sync.

### Authority and enforcement

Model training is never the source of an OpenAI review rule. Model reasoning can
locate and interpret fetched text; every enforced official finding must retain:

- Current primary URL, retrieval/revalidation time, exact content hash and
  heading/span supporting the finding.
- The rule's stated scope and the target evidence that makes it applicable.
- The actual failed observation and a concrete correction or next check.

Separate `official_requirement`, `official_guidance`, `engineering_advice` and
`creator_choice`. A recommendation, a model-generated risk, or an unsupported
inference cannot be promoted to a submission blocker. Candidate rule extraction
must preserve document wording/scope and reject unsupported interpretations.
Conflicting or unavailable guidance becomes a focused uncertainty, while local
syntax and runtime failures retain their own engineering classification.

The existing static catalog remains historical coverage data during migration.
Existing structural checks remain useful; do not relabel every hard-coded check
as dynamically verified. The guided runtime uses the current-source resolver;
its acceptance results are retained with this release. Preserve confirmed
source facts when rule snapshots change and
re-evaluate only affected findings.

## 5. Source-driven understanding

Resolve a supplied public repository without asking why it is public. Use an
accessible private repository through its existing authorized connection. Ask
for a different source only when actual access fails. Pin the commit or archive
hash and plugin subdirectory; handle multiple candidate plugin roots with a
short generated selection. Source acquisition does not run project code.

Build an `UnderstandingDraft` containing a summary, inferred personas, task IDs,
input/context requirements, observable success criteria, supported/deferred
capabilities, direct and indirect triggers, realistic negative prompts, proposed
metadata claims and source references. Record whether each item came from
implementation, declared documentation, existing tests or a model inference.
Do not treat a passing test definition as an executed test.

Automatically cross-check the draft against live use-case and metadata guidance,
plus applicable submission-error categories. Detect gaps between intended
behavior and implementation and propose either a repair or a narrower claim.
Draft the alternative choices; do not make the creator design them from scratch.

Infer repository visibility as an observed fact. Infer proposed audience,
data-access description and preparation route from source and the request.
For a public-submission request, suggest public-directory preparation. Present
these together in one compact setup summary with an accept/adjust choice.
Unknown visibility is not a blocker; an optional private route remains available.
Do not silently change the installed plugin's audience or publish anything.

## 6. Native ChatGPT questions

Use the available `chatgpt.app` Q&A harness, not an invented HTTP API. In this
host, the advertised `ask_user_input` widget supports `single_select` and
`multi_select`, two to ten option labels, and a contextual free-text placeholder.
The typed row is an optional escape hatch; no normal path requires prose input.
Use two to four options by default and one focused question at a time. Do not
call the question harness when the answer is already established.

The exposed widget schema has no preselected-option or hidden-option-ID field.
Keep proposed defaults in the session. Show them before a first option such as
`Use suggested setup`. If the creator chooses to adjust tasks, render a native
multi-select page. Do not invent a `selected` field or claim boxes are visually
prechecked. Keep mutually exclusive audience/release choices single-select.

Example native payload, after showing the generated product summary:

```json
{
  "ask_user_input": {
    "questions": [
      {
        "question": "Use this suggested setup for the submission?",
        "options": [
          "Use suggested setup",
          "Adjust tasks and boundaries",
          "Prepare for private use"
        ],
        "type": "single_select",
        "free_text_placeholder": "Add a specific correction (optional)"
      }
    ]
  }
}
```

The internal `QuestionPlan` adds stable question/option IDs, proposed defaults,
decision reason, session revision, source/understanding hashes and an allowed
transition. Render only provider-supported fields. Keep a unique label-to-ID
map for the current revision; validate a returned selection against that map.
Replayed or stale selections cannot silently confirm a changed draft.

Native question rendering ends the current conversational turn in this host.
Persist before rendering and resume from the recorded question after the user
answers. Do not promise a synchronous in-process answer or generate a fabricated
response. If the harness is unavailable, continue independent automatic work
and mark only the dependent confirmation pending. Do not replace it with an
open-ended questionnaire or claim that a custom preview is the native harness.

For a prepared repair, present `Apply the suggested fix`, `Adjust the claim`,
or `Review details` as appropriate. Reuse existing authorization for reversible
local work; do not add a confirmation for every routine edit. A native choice
can initiate a prepared patch when the host supports the action. It does not
mean that a one-click action API exists in every host.

## 7. Independent review and actionable fixes

The independent agent receives the pinned source, selected documentation,
confirmed draft and checks to perform. It reads the evidence itself and is not
given the first agent's desired verdict. It returns supported findings with
affected tasks, source/rule references and proposed fixes. Its agreement is
analysis, not execution evidence or OpenAI approval.

Run deterministic package checks and available runtime/host tests in parallel
where possible. Follow the chosen sample-data and action scope. Retain results
using the existing report-ingestion contract. Missing host/agent capability is
reported as an unperformed check; it does not invalidate the project or prevent
other preparation. Do not demand enterprise processes for an ordinary target
unless an applicable current official requirement actually requires them.

Surface the next useful fix, its effect and an apply option. Group duplicated
findings and keep satisfied rules in the background. Keep exact logs and
official references available for inspection. Apply a source fix, regenerate
affected drafts, rerun relevant checks and return to the same guided process.

## 8. Persistence and change handling

Schema version 2 retains source in `snapshot`/`source_origin` and adds `docs`,
`understanding`, `choices`, `question_plan`, `jobs` and
`findings`. Give understanding items stable IDs; bind derived prompts, listing
claims and reviewer notes to those IDs. Store selections as IDs, revisions and
provenance, not a copied paragraph that can drift from the draft.

The resumable bundle contains the exact target archive, source provenance,
selected doc snapshots and hashes, generated drafts, confirmed selections,
test plan, relevant captures, patches, output manifest and pending next action.
Generate listing fields and reviewer notes from that record. Reuse existing
copy fields at human-operated portals; do not make the developer reconstruct
documents manually. Private working evidence is separate from the distributable
plugin ZIP. Include only deliberately public assets in that ZIP.

| Change | Recompute | Preserve |
| --- | --- | --- |
| Source commit/archive | Affected capabilities, draft claims, cases and evidence bindings. | Creator preferences and unaffected choices when their meaning is unchanged. |
| Task/audience selection | Affected cases, claims, applicable rules and bundle. | Source observations, unrelated answers and valid results. |
| Official page content | Rules and findings derived from that page. | Source facts, unrelated rules and still-relevant test observations. |
| Artifact regeneration | Artifact hashes and integrity checks. | Confirmed meaning and historical evidence. |

Import version-1 sessions without upgrading old assumptions into fresh facts.
Retain artifacts/history, derive missing drafts automatically, and ask only
about meaningful unresolved choices. The reducer decides invalidation; it
must not ask the creator to reconfirm every item after a cosmetic edit.

## 9. Evidence and rollout boundaries

The design aims to reduce avoidable errors and unnecessary questions. Measure
first-submission outcomes only with actual pilot results; do not promise OpenAI
approval or faster review based on local tests. Track false-positive findings,
missed seeded errors, questions asked, manual fields requested and evidence
traceability separately. Do not add analytics collection without a defined
scope and user authorization.

The 2.2.0 tests remain historical evidence. The 2.3.0 regression and independent
exercise evidence records the new adapters. Native widget rendering, actual
product-host behavior and portal outcomes must retain their own observed status.
