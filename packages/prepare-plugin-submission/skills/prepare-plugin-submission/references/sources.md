# Official source index

Historical source inventory: **2026-10-13**. Only the individually listed checks in [source authority](source-authority.md) were refreshed for 2.0.0 on 2026-10-15. Requirements can change. Open the current
primary page for the selected target before submission. These are references,
not pinned promises of current portal behavior.

| ID | Source | Purpose |
| --- | --- | --- |
| O1 | [Package your plugin](https://developers.openai.com/plugins/build/plugins) | Package your plugin. |
| O2 | [Upload and submit](https://developers.openai.com/plugins/deploy/submission) | Upload and submit. |
| O3 | [Plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines) | Plugin guidelines. |
| O4 | [Claude to OpenAI](https://developers.openai.com/plugins/guides/submit-claude-plugin) | Claude to OpenAI. |
| O5 | [OpenAI authentication](https://developers.openai.com/plugins/build/auth) | OpenAI authentication. |
| O6 | [Connect and test](https://developers.openai.com/plugins/deploy/connect-chatgpt) | Connect and test. |
| O7 | [Remote MCP review](https://developers.openai.com/plugins/deploy/app-review) | Remote MCP review. |
| O8 | [Submission errors](https://developers.openai.com/plugins/deploy/submission-errors) | Submission errors. |
| O9 | [MCP in the API](https://developers.openai.com/api/docs/guides/tools-connectors-mcp) | MCP in the API. |
| A1 | [Publish to Claude directory](https://claude.com/docs/directory/publish) | Publish to Claude directory. |
| A2 | [Claude plugin structure](https://claude.com/docs/plugins/build) | Claude plugin structure. |
| A3 | [Claude platform support](https://claude.com/docs/plugins/platform-support) | Claude platform support. |
| A4 | [Claude plugin checklist](https://claude.com/docs/plugins/pre-submission-checklist) | Claude plugin checklist. |
| A5 | [Claude connector authentication](https://claude.com/docs/connectors/building/authentication) | Claude connector authentication. |
| A6 | [Claude connector checklist](https://claude.com/docs/connectors/building/review-criteria) | Claude connector checklist. |
| A7 | [Submit a Claude plugin](https://claude.com/docs/plugins/submit) | Submit a Claude plugin. |
| A8 | [Submit a Claude connector](https://claude.com/docs/connectors/building/submission) | Submit a Claude connector. |
| A9 | [Test a Claude connector](https://claude.com/docs/connectors/building/testing) | Test a Claude connector. |
| A10 | [After publishing](https://claude.com/docs/connectors/building/after-publishing) | Server/package/listing updates, permanent identity, usage and delisting. |
| A11 | [Server readiness](https://claude.com/docs/connectors/building/index) | Supported capabilities, host limits, auth, hosting and distribution. |
| A12 | [First server](https://claude.com/docs/connectors/building/quickstart) | Runnable local server and real-call verification, distinct from production setup. |
| A13 | [Manage directory listing](https://claude.com/docs/connectors/building/managing-your-listing) | Listing review, health metric definitions and stable slug. |
| TERMS | [Publisher terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms) | Separate publisher decisions and ongoing obligations. |
| C1 | [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference) | Manifest component paths and native loading. |
| E1 | [Claude plugin evaluations](https://code.claude.com/docs/en/plugin-evals) | Native runner, grants, repeat counts and local reports. |
| E2 | [OpenAI evaluation practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) | Outcome graders and evidence-based iteration. |
| E3 | [Evaluating agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Trials, transcripts, outcomes and calibrated grading. |
| MCP | [MCP specification 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) | MCP specification 2026-07-28. |
| M1 | [Build an MCP server](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server) | Current TypeScript registration and serving idioms. |
| M2 | [Build an MCP client](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-client) | SDK client, transports, discovery, and calls. |
| M3 | [Client Best Practices](https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices) | Host-generated typed APIs and progressive discovery. |
| M4 | [Official MCP SDKs](https://modelcontextprotocol.io/docs/2026-07-28/sdk) | Canonical repositories and SDK tiers. |
| M5 | [Understanding Authorization](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/authorization) | Authorization flow; its TypeScript example still uses v1 imports. |
| M6 | [TypeScript SDK v2](https://ts.sdk.modelcontextprotocol.io/v2/) | Current SDK APIs; follow its migration and authorization references. |
| M7 | [Inspector CLI](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/cli) | Single-request protocol checks, JSON output, and failure classes. |
| M8 | [mcpdo connection client](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/mcpdo) | Experimental persistent connections for multi-step tests. |
| M9 | [Protocol eras](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/protocol-eras) | Explicit era selection and wire-level debugging. |
| M10 | [Versioning and Compatibility](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning) | Per-request versions and compatibility rules. |
| M11 | [stdio transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio) | Framing, discovery, and transport-specific fallback. |
| M12 | [Inspector security](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/security) | Daemon lifecycle, credential boundaries, and local process isolation. |
| POLICY | [Anthropic Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy) | Anthropic Directory Policy. |
| SCHEMA | [Agent Plugins schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json) | Agent Plugins schema. |

## Resolve inconsistencies

For OpenAI portal steps, prefer O2. O3 explicitly removes annotation
justification requirements while O7/O8 retain older wording. Use O3 for the
current annotation rule and inspect real validation findings. O2/O8 distinguish
skills-only packages from MCP review: do not require all four MCP listing URLs
for a skills-only package. A4/A7 distinguish local Claude schema checks from
directory validation and security scans. A7 and A8 cover different submission
units. A2/A4 require loading and behavioral tests on intended surfaces and a comparison
with and without the plugin. A6 requires every tool to work with valid inputs;
three examples do not replace all-tool testing. These obligations are distinct
from the automated package/security checks and do not specify a universal
all-models, all-surfaces 100% score submission rule. Record conflicting source text, the date, and actual portal behavior;
do not silently pick the easier rule.

For TypeScript implementation, M1/M2 use split v2 packages while M5 and some
host quickstarts still show the monolithic v1 SDK. Use the installed generation,
M4's canonical repository, and the matching API reference to resolve imports.
The unversioned TypeScript SDK documentation root is v1. Follow the
[SDK implementation workflow](typescript-sdk.md) to replace duplicated plumbing
and verify the actual protocol path; a documentation date alone proves neither
package compatibility nor a successful runtime test.

## Extra implementation references

The documentation collections include implementation details that should be
read when changing a server rather than just packaging it:

- [OpenAI documentation index](https://developers.openai.com/plugins/llms.txt)
- [OpenAI complete export](https://developers.openai.com/plugins/llms-full.txt)
- [OpenAI server build guide](https://developers.openai.com/plugins/build/mcp-server)
- [OpenAI MCP concepts](https://developers.openai.com/plugins/concepts/mcp-server)
- [OpenAI tools](https://developers.openai.com/plugins/plan/tools)
- [OpenAI UI](https://developers.openai.com/plugins/build/chatgpt-ui)
- [Claude documentation index](https://claude.com/docs/llms.txt)
- [Claude server build guide](https://claude.com/docs/connectors/building/index)
- [Claude first server](https://claude.com/docs/connectors/building/quickstart)
- [Anthropic Directory Terms](https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms)

The extra links are discovery references, not claims that each page was
retrieved in the recorded verification run.

## 1.1.0 rule refresh

On 2026-10-13 the audit refresh retrieved O1/O2/O3/O7/O8/O9, A2/A3/A4/A6,
C1, E1/E2/E3 and SCHEMA. The repository records content hashes and retrieval
times. Other links retain their earlier verification history and are discovery
references until reopened. O1 supplies absent/present OpenAI extension
precedence and canonical portable component paths. C1 supplies Claude's
additive custom paths and later-server override behavior. O2's required public
category and O8's default-on-import are different stages; the submission
profile requests an explicit category. A4 holds are not rejection or package
format errors. O7's all-submitted-case/supported-surface gate does not impose
a universal historical/future model suite on either platform.

