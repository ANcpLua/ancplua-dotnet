# Submission Studio preflight lifecycle
## Contents

- 1. Purpose and product scope
- 2. Official documentation inventory
- 3. Requirement authority
- 4. Architecture and integration discovery
- 5. MCP server engineering
- 6. Skills engineering
- 7. Authentication and authorization
- 8. Packaging and compatibility
- 9. Interactive UI
- 10. Evaluation and host testing
- 11. Security and privacy
- 12. Directory preparation
- 13. Submission and publication
- 14. Maintenance and updates
- 15. API model compatibility
- 16. Specialized product workflows
- 17. Complete deliverable contract


> **Path convention:** deliverable paths below (`architecture/`, `readiness/`, `security/`, `publisher/` and similar) are relative to the output directory of the pack being produced (for example `prepare_workflow.py --output <dir>`). They are not paths in this repository and do not exist here.

OpenAI implementation scope • Original baseline: October 13, 2026 • Preflight scope clarified: October 16, 2026

## 1. Purpose and product scope

Submission Studio is a preflight auditing meta-tool for OpenAI plugins and MCP integrations. Inspect loaded targets, perform authorized engineering and local checks, prepare review materials, and produce source-bound findings. The human performs portal upload, review submission, legal attestations and publication while the assistant guides each step, validates the returned observations and helps resolve findings.

Blank generated templates are expected before a target is loaded. Apply target component requirements only after inspection; support for auditing servers or UI does not require Submission Studio itself to bundle a server or UI. Static preflight, executable tests, actual host verification and publication have separate completion states.

It must support skills-only plugins, remote MCP integrations, combined skill/MCP packages, optional interactive UI, platform extensions, and API applications using remote MCP tools.

Its primary environments are ChatGPT, Codex, and the relevant OpenAI Responses API. The agent must distinguish product integration from API-client integration and must never assume that a passing test in one environment proves compatibility in another.

The assistant must perform actual engineering work when tools and access are available: inspect code, implement components, run tests, generate artifacts, repair failures, package releases, and verify resulting state.

Cross-platform migration is an explicitly selected workflow, not the default behavior.

## 2. Official documentation inventory

The primary official documentation collection is [OpenAI Plugins](https://developers.openai.com/plugins). Use the [documentation index](https://developers.openai.com/plugins/llms.txt) to discover pages and the [combined documentation export](https://developers.openai.com/plugins/llms-full.txt) as a source for retrieval and indexing. These are not substitutes for checking the current primary page when enforcing a release-sensitive rule.

| Domain | Official documentation |
| --- | --- |
| Architecture | [Plugin concepts](https://developers.openai.com/plugins/concepts/plugins), [MCP server concepts](https://developers.openai.com/plugins/concepts/mcp-server), [Skills concepts](https://developers.openai.com/plugins/concepts/skills) |
| Planning | [Use-case planning](https://developers.openai.com/plugins/plan/use-case), [Tool design](https://developers.openai.com/plugins/plan/tools) |
| Getting started | [Plugin quickstart](https://developers.openai.com/plugins/quickstart), [App quickstart](https://developers.openai.com/plugins/build/app-quickstart) |
| Server implementation | [Build an MCP server](https://developers.openai.com/plugins/build/mcp-server), [Examples](https://developers.openai.com/plugins/build/examples) |
| Skills | [Build skills](https://developers.openai.com/plugins/build/skills) |
| Authentication | [Authentication](https://developers.openai.com/plugins/build/auth) |
| UI | [ChatGPT UI](https://developers.openai.com/plugins/build/chatgpt-ui), [UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines), [UI reference](https://developers.openai.com/plugins/reference) |
| Additional capabilities | [MCP Events](https://developers.openai.com/plugins/build/mcp-events), [Extensions](https://developers.openai.com/plugins/build/extensions), [Monetization](https://developers.openai.com/plugins/build/monetization) |
| Packaging | [Package your plugin](https://developers.openai.com/plugins/build/plugins), [Optimize metadata](https://developers.openai.com/plugins/guides/optimize-metadata) |
| Testing | [Connect and test](https://developers.openai.com/plugins/deploy/connect-chatgpt), [Troubleshooting](https://developers.openai.com/plugins/deploy/troubleshooting) |
| Security and policy | [Plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines), [Security and privacy](https://developers.openai.com/plugins/guides/security-privacy) |
| Review | [Remote MCP review](https://developers.openai.com/plugins/deploy/app-review), [Submission errors](https://developers.openai.com/plugins/deploy/submission-errors) |
| Publication | [Upload and submit](https://developers.openai.com/plugins/deploy/submission) |
| Desktop partner route | [Submit desktop-only plugins](https://developers.openai.com/plugins/deploy/desktop-only) |
| Migration | [Submit a Claude plugin to OpenAI](https://developers.openai.com/plugins/guides/submit-claude-plugin) |
| API compatibility | [MCP tools and connectors](https://developers.openai.com/api/docs/guides/tools-connectors-mcp) |
| Evaluation design | [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) |

Specialized product workflows are conditionally applicable: [local-services quote conversion](https://developers.openai.com/plugins/guides/local-services-request-quote-conversion-spec), [product checkout](https://developers.openai.com/plugins/guides/product-checkout-conversion-spec), and [restaurant reservations](https://developers.openai.com/plugins/guides/restaurant-reservation-conversion-spec).

The specialized documents must not be imposed on integrations that do not implement those activities.

## 3. Requirement authority

Every enforceable requirement must have a source-backed record distinguishing official platform requirement, recommended engineering practice, and unverified or unresolved claim.

Use a record such as:

```
requirement_id: OAI-PKG-001
platform: openai
scope: public_plugin_submission
source_url: https://developers.openai.com/plugins/build/plugins
source_checked_at: null
classification: official_requirement
applicability: remote_mcp_plugin
summary: Resolve effective package configuration before validation.
verification: static_package_inspection
status: not_run
evidence: []
```

The example identifier and wording are internal conventions, not official OpenAI identifiers.

Maintain documentation retrieval dates, source revisions where available, conflicts, and observed portal behavior. A URL listed in the inventory is not proof that its full page was read.

## 4. Architecture and integration discovery

For a new project, establish the user outcomes, operations, data model, identity requirements, supported environments, UI needs, deployment architecture, and acceptance criteria.

For an existing project, inspect repository instructions, manifests, MCP declarations, skills, tools, UI assets, authentication, CI, deployment, previous releases, and review records before making changes.

Produce `architecture/assessment.md`, `architecture/components.json`, `architecture/tool-inventory.json`, `architecture/host-matrix.md`, and `readiness/initial-assessment.md`.

The assistant must select the simplest supported component structure. Skills are appropriate for instructions and repeatable workflows; MCP is appropriate when external capabilities or remote operations are required; UI is optional.

Acceptance requires each discovered capability to be traceable to source or explicitly identified as proposed. The assistant must not infer functionality from a product description alone.

## 5. MCP server engineering

Applicable when a target needs an MCP integration. Public local stdio submission uses the approved desktop-only partner route; remote submission uses its remote endpoint requirements.

Inputs include the operations to expose, authentication architecture, intended transport, data permissions, expected results, deployment constraints, and supported host environments.

The assistant must implement or verify server initialization, protocol negotiation, transport, tool discovery, input schemas, invocation, outputs, error handling, permissions, session behavior, observability, shutdown, and applicable optional resources, prompts, events, and UI.

Use `shared-mcp.md` for protocol behavior and OpenAI documentation for host-specific requirements.

Produce runnable source, dependency and lock files, configuration examples, tool inventory, tests, deployment instructions, and operational guidance.

When executable testing is authorized, verify by building and starting the controlled server, connecting an MCP client, discovering tools, invoking representative operations, and observing results and side effects. Compilation or static schema validation alone cannot prove runtime behavior. The loaded-target `audit` command only inspects files and never executes target code or contacts endpoints.

For a server not accessible from the testing environment, retain the implementation and tests but mark live verification blocked.

## 6. Skills engineering

Applicable to skills-only and combined plugins.

Inspect intended user tasks, available host capabilities, supporting scripts, and required reference materials. Create `skills/<skill-name>/SKILL.md`, any scripts and resources, and reproducible behavioral evaluations.

Verify the final packaged skill loads and can perform representative tasks. Do not treat keyword searches in a skill file as evidence of agent behavior.

A skills-only package must not be forced to provide MCP-specific OAuth configuration, server review cases, or an MCP demonstration recording.

## 7. Authentication and authorization

The assistant must establish whether the integration is anonymous, authenticated, or mixed-access, then implement the currently supported OpenAI connection flow.

For OAuth-based integrations, verify applicable protected-resource metadata, authorization-server discovery, client registration, PKCE, redirects, scopes, audience, expiry, refresh, denied consent, revocation, and user/tenant isolation.

Produce `security/auth-architecture.md`, configuration templates, `security/permission-matrix.md`, and execution evidence.

Protected operations must reject unauthorized access. Authorized calls must remain within granted permissions. Credentials must not appear in public packages, reports, screenshots, or repository files.

A static bearer-token test does not prove a complete OAuth flow. A successful login in another MCP host does not prove OpenAI compatibility.

## 8. Packaging and compatibility

The assistant must resolve the effective package format and component declarations before applying validation.

Inspect the target plugin's root `plugin.json`, applicable `extensions.com.openai` metadata, documented compatibility overlays, the target plugin's `mcp.json`, supported legacy MCP configuration (`.mcp.json`), skills, icons, and UI resources.

Handle the documented precedence between portable and compatibility configuration. An unresolved MCP declaration must never silently turn a package into “skills-only.”

For public submission, validate the currently applicable restrictions on lifecycle hooks, private app bindings, static server headers, required metadata, asset references, supported transport, and package contents.

Produce a submission archive, file inventory, effective-configuration report, validation report, content hash, and reproducible build instructions.

Acceptance requires checking the finished archive, not just the working tree. Unknown rules or unsupported layouts must remain visibly unverified.

## 9. Interactive UI

Applicable only when the integration exposes UI.

Implement host-compatible resources, rendering, interactions, loading and error states, accessibility, appearance handling, and safe navigation.

Produce UI source, integration tests, actual-host screenshots, interaction traces, and compatibility findings.

Verify the UI in the claimed product environment. A mockup is not installed-host evidence; a screenshot does not prove backend correctness.

## 10. Evaluation and host testing

Use four independent testing layers:

1. Static package, manifest, reference, and schema checks.
2. Deterministic integration tests against actual processes and controlled state.
3. Agent-behavior evaluations using realistic user tasks.
4. Verification in the intended ChatGPT and Codex product surfaces.

Each case must record source revision, package hash, environment, prompt, expected tools, actual calls, expected behavior, observed output, side effects, status, and evidence location.

For initial remote MCP review, the October 2026 documentation baseline describes five positive and three negative cases, subject to current submission guidance. Do not apply this remote-specific requirement to skills-only or local-only desktop targets.

A negative case should represent a genuinely unsupported or disallowed request, not a valid empty result.

The host-verification gate must verify applicable cases across claimed and applicable supported surfaces. Mocked runs, local MCP Inspector results, and API-client tests cannot substitute for product-host verification. A completed local preflight may still have unrun host checks; do not require a portal action to finish the audit.

## 11. Security and privacy

Inspect data access, retention, transmission, logs, credentials, authorization, tenant isolation, destructive operations, external destinations, prompt-injection boundaries, dependencies, and reviewer access.

Produce a security assessment, data-flow inventory, permissions matrix, privacy evidence, remediation changes, and unresolved findings.

Technical claims must be grounded in code or observed behavior. A filename-based secret scan is not a comprehensive security assessment.

Legal and data-practice statements require creator-confirmed facts.

## 12. Directory preparation

Prepare applicable listing metadata, developer identity, descriptions, category, icons, starter prompts, support information, website, privacy and terms pages, review cases, release notes, demo materials, reviewer account setup, and any commerce or localization declarations.

Suggested deliverables:

```
submission/
  listing.md
  metadata.json
  review-cases.json
  reviewer-access.md
  demo-plan.md
  release-notes.md
  readiness.md
```

Review credentials belong in secure fields, not public artifacts.

Verify URLs and actual recording playback. A drafted policy page is not a published policy URL; a demo script is not a video.

The assistant must identify which fields are not applicable to skills-only or non-UI submissions.

## 13. Submission and publication

Prepare the creator's handoff using the current official submission guide. Portal operations are performed externally by a human; this meta-tool records supplied observations without uploading targets, attesting legal facts, submitting review or publishing.

Track separate states for local completion, private installation, uploaded draft, validation, review submission, approval, and publication.

Read back saved identities and versions after any authorized action. Never infer publication from an upload or a repository push.

Submission, public publication, legal attestations, and cloud installation updates are separate operations.

## 14. Maintenance and updates

Inspect the existing plugin identity, server endpoint, source revision, package version, tool schemas, authentication changes, listing changes, and review history.

Prepare change-impact analysis, regression tests, release notes, rollout and rollback instructions, updated package, and publication-state record.

Distinguish a changed MCP deployment, changed plugin package, changed directory listing, and changed API client.

A GitHub commit or local build is not evidence that a cloud installation or public listing was updated.

## 15. API model compatibility

Maintain four separate contracts: MCP service, plugin package, product host, and API caller.

For a custom remote MCP server, the Responses API caller uses `server_url`. `connector_id` refers to the legacy built-in connector option; it is not a server-side interface a custom MCP service must implement.

The October 2026 documentation baseline describes `connector_id` as deprecated for models released after September 1, 2026. Earlier-model support does not create a requirement for a custom server to implement that field.

Use specific tested model IDs when documenting API-client compatibility. A release-date promise does not automatically establish compatibility with future models or exempt an integration from directory review.

## 16. Specialized product workflows

When applicable, load the relevant conversion specification for local-services quotes, product checkout, or restaurant reservations.

The assistant must implement the required operation contracts, schemas, authentication, expected state transitions, and host tests for the chosen product category.

It must not claim these category-specific requirements apply to unrelated plugins.

## 17. Complete deliverable contract

A finished OpenAI project handoff should contain, where applicable:

- Source and runnable implementation.
- Plugin archive and manifest inventory.
- Tool and skill inventory.
- Authentication and security assessment.
- UI resources and evidence.
- Test cases and actual execution results.
- Host compatibility record.
- Listing and review materials.
- Publisher-confirmed facts.
- Deployment and maintenance runbook.
- Source revision, package hash, and verification report.
- Actual submission and publication state, if those actions occurred.

Use `Passed`, `Failed`, `Blocked`, `Not run`, and `Not applicable` at the check level.

Keep `Prepared`, `Locally validated`, `Host verified`, `Review-ready`, `Submitted`, `Approved`, and `Published` as distinct lifecycle states.

No single local checker result may establish all lifecycle states.
