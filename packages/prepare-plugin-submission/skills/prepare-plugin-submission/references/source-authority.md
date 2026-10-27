# Source authority for 2.0.0

Checked on 2026-10-15. This is a per-topic retrieval record, not a claim that
all linked pages or all historical checker rules have been revalidated.
The two supplied specifications define the requested product scope; they are
not official platform policy. Missing prose and unavailable baseline records
are omitted without invented replacements.

| Source | Observed guidance | Authority and scope |
| --- | --- | --- |
| [Plugin packaging](https://developers.openai.com/plugins/build/plugins) | Portable root manifest, fixed skills/MCP paths, OpenAI extension and compatibility fallback. | Official package guidance. |
| [Submit](https://developers.openai.com/plugins/deploy/submission) | Remote MCP initial review uses five positive and three negative cases and a real demo; skills-only is exempt. Upload, review and publication are separate. | Official submission requirements, conditional on route. |
| [Remote review](https://developers.openai.com/plugins/deploy/app-review) | Public endpoint, verified identity, review access; annotations reflect actual server behavior. | Official remote MCP review guidance. |
| [OpenAI server tutorial](https://developers.openai.com/plugins/build/mcp-server) | The retrieved tutorial still uses monolithic TypeScript SDK imports. | Host engineering guide with a generation conflict; do not copy its v1 imports into a v2 project. |
| [MCP SDK v2](https://ts.sdk.modelcontextprotocol.io/v2/) | Split client/server packages are the stable v2 line for the 2026-07-28 specification. | Official TypeScript implementation authority. |
| [Protocol support](https://ts.sdk.modelcontextprotocol.io/v2/migration/support-2026-07-28.html) | Hand-constructed clients default to legacy; modern pinning and SDK serving factories are explicit. | Official SDK negotiation guidance; SDK version alone does not establish wire era. |
| [MCP specification](https://modelcontextprotocol.io/specification/2026-07-28) | Modern core is stateless with per-request capabilities. | Protocol authority, not host-support evidence. |
| [mcpdo](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/mcpdo) | Named agent calls, bare JSON payloads, parked auth/elicitation, tasks, explicit era and automatic daemon. | Experimental client guidance; installed help governs available commands. |
| [Inspector security](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/security) and [configuration](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/configuration) | Stdio process privileges, private daemon limits, cross-process secret storage. | Tool-specific operational guidance. |
| [Responses MCP](https://developers.openai.com/api/docs/guides/tools-connectors-mcp) | Custom remote servers use server_url. Built-in connector_id has the documented model-date deprecation. | API caller contract, distinct from product host support. |

Prefer protocol/SDK sources for modern implementation APIs and OpenAI sources
for OpenAI host policy. Record conflicting examples instead of declaring all
OpenAI hosts modern-compatible. Test each claimed environment.

Historical offline checker findings retain their original source dates. Reopen
the relevant primary page before enforcing one as a current official rule.
In 2.0.0, generated OpenAI checks used `source_checked_at: null` until the
acting agent verified a rule. The 2.1.0 catalog below replaces those eleven
generic records with individually sourced rows and separates official rules
from engineering recommendations. A source date establishes the documentation
check; each target's result still needs its own observation and evidence.

No reference to a 1.5.0 evaluation baseline establishes prior validation: the
editable installed release was 1.2.1, and that unavailable baseline was omitted.

## 2.1.0 preflight coverage

The 2026-10-16 catalog in [requirements.json](requirements.json) records 49
individual requirements across all 32 supplied topic pages and the desktop-only
guide. Its dates are documentation checks, not target execution. Loaded target
audit results carry their own observations, status and local evidence. Human
portal handoffs and target-inapplicable rules are explicit. Synthetic fixture
checks do not establish partner eligibility, real host behavior or publication.

## 2.2.0 guided interaction

The wizard is a user-requested product workflow, not an official OpenAI submission requirement. The submission, desktop-only and connect/test primary pages were checked on 2026-10-16 for the implemented flow. Portal access, package checks, review and optional publication remain separate. Session events record creator reports and source-bound evidence; they do not authenticate human observers or perform portal operations.

## 2.2.1 design revision

The [planned source registry](official-docs-sources.json) lists all 32 primary
topic pages requested by the creator and the existing desktop-only route. It
contains discovery/applicability hints, not newly verified constraints. The
[architecture](architecture-2.3.md) replaces static rule assumptions with
per-run official retrieval and primary-page checks in the planned runtime.

On 2026-10-16 the live index and the HTML primary pages for use-case planning,
metadata optimization, submission errors, remote review and submission were
retrieved for this design. The available web reader rejected Markdown twins
as an unsupported content type, and the combined export fetch returned
DisabledError. Those are retrieval limitations, not failures of a target
plugin. The design therefore includes HTML fallback and explicit source gaps.
No specialized conversion page was fetched or enforced for this design task.

The available host Q&A schema was also inspected: it supports single-select,
multi-select and an optional typed correction, but exposes no preselected
checkbox field. The architecture keeps proposed defaults in session data and
uses an explicit accept-suggestion action. These observations do not establish
that the future native-question adapter has been implemented or host-tested.

## 2.3.0 implemented retrieval

The runtime now fetches the live index/export and selected primary pages,
normalizes and indexes their contents, and retains provider, requested/resolved
URL, timestamp, body hash, HTTP validators and retrieval status. The registry's
33 entries are applicability hints, not 33 universally imposed requirements.
Current primary evidence determines each enforced official finding; the older
49-row catalog is historical coverage data in the guided runtime.

The 2026-10-16 HTTP smoke on the synthetic skills/remote-MCP fixture retrieved
21 records: the index, filtered export and 19 applicable primary pages. All
retrievals succeeded. None of the three specialized conversion primary URLs
was requested. The retrieved app quickstart contained only a Todo heading and
Add; retrieval success did not supply substantive guidance or justify a rule.
The independently saved review uses exact current-primary spans and target
observations. Recorded responses and old snapshots remain evidence of those
reads, not permanently current policy.

The combined export worked through the implemented HTTP adapter, resolving the
earlier design-time reader limitation. An actual public GitHub transport smoke
resolved octocat/Hello-World to its exact commit and archive hash; that small
repository is not a plugin readiness or private-access test. Private access,
conditional-page selection, changed policy, unavailable retrieval and HTTP 304
behavior have controlled regression coverage.

The native question contract and returned-choice mapping are implemented and
tested with synthetic selections. Actual host rendering/selection is unverified.
Independent agent review was exercised with actual separate agent output; no
target endpoint, installed-host, recording, creator-declaration or portal result
is inferred from it. See the versioned 2.3.0 release evidence.
