# Claude preparation

Use A1 for the route and account eligibility, A7 for a plugin repository, and A8
for a hosted connector. A4 and A6 are their different checklists. A3 describes
host support. Links are in [sources](sources.md); verify them live.

## Choose the submission unit

A connector submission describes a hosted MCP service. A plugin submission
contains skills or other bundled components in a GitHub folder. When the plugin
references a remote server the publisher owns, submit the server as a connector
as well. Keep separate identities, review evidence, and status records.

A plugin folder has `.claude-plugin/plugin.json`, its runtime components,
README, and a license file or manifest declaration. The directory README must
contain at least 40 prose words. Keep everything the plugin loads inside that
folder. Use regular files and portable names. Runtime symlinks, submodules and LFS
pointers block directory validation; non-runtime occurrences can warn. The
checker declines symlinks at its input boundary rather than following them.
Remove operating-system metadata. Consult A4 for repository limits and distinctions
between blocking findings, warnings, and reviewer holds.

For remote servers, use `type: http`, `sse`, or `ws` with an absolute HTTPS/WSS
URL, a documented `${user_config.KEY}` substitution, or an empty configurable
URL. Resolve configuration and test the resulting connection separately.
Claude loads default `.mcp.json` first, then manifest `mcpServers` declarations;
later entries override the same server name. Custom skill directories add to
the default `skills/` directory. Native format support and public eligibility
are different: MCP bundles can load locally but trigger a hold, or a blocker
when fetched from a URL, in the directory checklist.

A4 sets repository limits below 50 MiB archived, 256 MiB unpacked and 10,000
files/folders; plugin files must be below 5 MiB. More than 512 plugin files,
non-image/font files at least 256 KiB, and other binary formats trigger holds.
Keep export-ignore/export-subst out of all repository `.gitattributes` files;
content-rewriting filters are restricted at the root, above and inside the
plugin. Without the full repository, those checks remain incomplete.

Pin every launcher package (`npx`, `bunx`, `pnpm/yarn dlx`, `uvx`, `pipx run`)
to an exact version. `uv run` needs `--locked` or `--frozen`. Even pinned
launchers require review. Package-source overrides with launchers block;
indirect commands and certain installs also need review. The checker handles
common declarations and flags ambiguous flags for manual/native validation;
it does not recursively interpret scripts or prove dependency safety.

Run `claude plugin validate <folder>` if available. It checks structure, not
all directory rules. The portal validates a specific repository commit; a later
push needs a fresh validation. A private repository can be reviewed subject to
access and scanning consent; publication needs a public repository. Making a
repository public is a separate authorized action, not an automatic repair.

## Functional testing is a separate obligation

A2 explicitly instructs authors to test on each surface their users will use.
Before submission, check both component loading and useful behavior in the
intended Claude Code, claude.ai, and Cowork surfaces. A4 also calls for real
prompt comparisons with and without the plugin. Record the source revision,
case, surface, enabled components, baseline result, plugin result, and evidence.

Respect A3's capability matrix: an agent or local MCP server being ignored in
Chat is expected behavior, not a failed supported feature. Do not claim a
surface was tested if only a different host ran the scenario.

Local validation and directory scanning examine package construction and policy;
they do not establish functional correctness. These guides do not establish a
universal requirement to upload a suite scoring 100% across every Claude model
and surface. Describe comparable testing obligations without inventing an
identical universal pass rule or treating an internal eval score as approval.

## Hosted connector materials

Prepare the actual endpoint and authentication settings, documentation/privacy
pages, support information, icon, and at least three working examples/use cases.
Confirm live policy and form requirements. Provide a dedicated sample account
when needed. Exercise every tool through MCP Inspector and a real Claude
connection. Every exposed tool must succeed with valid parameters and handle
invalid input with useful, actionable errors. Unexplained generic errors can
fail functional review. Three working examples demonstrate core use cases;
they do not replace testing every exposed tool. Keep a complete tool inventory
and mark each tool's Inspector and real-Claude execution separately. A8's
Test & launch attestation requires truthful run evidence and reviewer access,
not just a declaration that tests exist. A single generic HTTP executor that hides read/write operations is
not an acceptable substitute for individually defined tools.

For a connector with MCP App UI, A8 asks for 3–5 PNG screenshots at least 1,000
pixels wide, with the example prompt supplied separately. Capture the real UI
and its actual results. Do not impose those screenshots on a text-only connector.

## Per-tool review

Use the [tool worksheet](../templates/tool-review.md). A6 requires a tool title,
a name at most 64 characters, a precise description, and the applicable hint:
`readOnlyHint: true` for reads or `destructiveHint: true` for modifications and
deletions. Verify real behavior and permissions, not only the presence of a
boolean. Custom query tools that accept caller-constructed endpoint paths,
query strings or bodies must name or link the target API documentation in
the description. This extra requirement does not apply to fixed-endpoint tools.
Separate safe reads from writes; a generic method-switching executor is not
sufficient. Inspect input/output schema, sensitive returned data, authorization,
and side effects for each tool, then attach its actual execution records.

## Compatibility and publishing

Skills load across Chat, Cowork, and Claude Code; executable code and local
servers have different support. For example, a local stdio server isn't a
working remote connection in Chat. Check A3 before promising parity. Keep
useful text/structured results when UI is unavailable.

Follow A5 for discovery, registration, callback, and refresh requirements; do
not infer OAuth compatibility from one successful host. Check current client
registration options in the portal and test the configured route.

A7 covers plugin source validation, listing, data handling, acknowledgements,
submission, review, and publishing settings. A8 has the connector's own launch
flow. Inspect the live state after every action and name that state accurately.
Do not promise that a scan or a submission means a public listing exists.
Preserve the existing repository/folder identity during updates. Record the
tracked revision and actual publication/auto-publish settings; never assume
that pushing a commit has published it.

## Do not infer coverage from prompt counts

A single example can invoke several tools. Do not subtract the number of
example prompts from the number of exposed tools or invent how many tools are
untested. Compare the complete tool inventory with actual per-tool execution
evidence; without that evidence, coverage is unknown.

