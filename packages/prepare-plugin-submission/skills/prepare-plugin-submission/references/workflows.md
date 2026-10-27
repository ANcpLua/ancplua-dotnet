For guided preparation and continuation, start with the [conversational wizard](wizard.md). The commands below remain useful for bounded artifacts and engineering tasks.

# Executable preparation workflows

Submission Studio is a preflight meta-tool. Portal actions are human handoffs.
Unloaded records are expected templates, not incomplete audits. To inspect a
loaded target, run `prepare_workflow.py audit --source <target> --output <new-dir>`.
The resulting matrix and assessment documents contain source-bound observations.
See [host report ingestion](host-reports.md) for external ChatGPT/Codex captures.


Default platform: OpenAI. `init --platform openai` creates OpenAI records;
`--platform claude` selects the retained Claude workflow. Never apply Claude
policy clauses or host limits to an OpenAI project. OpenAI packs include the
architecture, protocol, security, tools, submission and operations records
described in [OpenAI lifecycle](openai-lifecycle.md). Their empty evidence stays
Not run until the agent implements and executes the relevant checks.


The bundled `scripts/prepare_workflow.py` generates real deliverables from one
integration record. Python 3.10+ generates and checks packs without dependencies.
Running a generated test kit requires Node 22.19+, npm, and the recorded SDK
dependencies. Its mcpdo adapter uses Inspector 2.10.1; inspect the current SDK
guidance when updating these pins. Use a new output directory for every revision.

## Existing integration

Capture the actual tool inventory with the SDK or mcpdo, then initialize:

```sh
python3 <skill>/scripts/prepare_workflow.py init --id my-integration \
  --inventory tools-list.json --output integration.json
```

Fill the record from source, configured services, and the creator's answers.
Keep unknowns explicit; do not fabricate fixtures, endpoint identity, or legal
facts. Inspect the generated case coverage and fill gaps before running it.

| Input | Required content |
| --- | --- |
| `source_revision`, optional `source_files` | Actual revision/digest; source files are hashed and checked before tests. |
| `hosts` | OpenAI: `chatgpt`, `codex`, `responses-api`. Explicit Claude route: `claude-ai`, `claude-desktop`, `claude-code`, `cowork`, `claude-mobile`. |
| `server.connection` | `transport: http/sse` plus `url`, or `stdio` plus `command`, string-array `args`, and `cwd`. Relative paths start at the input record. |
| `server.connection.env_from` / `headers_from_env` | Map child environment/header names to existing environment-variable names. An Authorization value includes its Bearer prefix. Never put secret values in the record. |
| `server` | `hosting: local/remote`, `distribution: custom/directory/plugin/desktop-extension`, required MCP capabilities, `auth.mode: none/oauth/organization-credential`, host settings. |
| `account_setup`, `sample_data`, `permissions` | Reproducible sample account setup, fixture reset instructions, expected privileges and effects. |
| `cases` | Unique `id`, advertised `tool`, `kind: valid/invalid/boundary/workflow`, `effect: read/write/destructive`, `arguments`, and `expected`. |

Each tool needs valid and invalid cases. Missing cases are generated with null
inputs/expectations and remain Blocked. A success expectation needs an actual
result assertion: `structured`, `text_contains`, `max_text_chars`, or an exact
`text_length`. Error kinds include `tool_error`, `protocol_error`, and `timeout`.
Optional `timeout_ms` applies to SDK calls. Use `engines` to scope an engine-specific
case; declare any remaining host coverage separately. Multi-step cases execute
in array order over one SDK/mcpdo connection. An `elicitation_response` provides
an explicitly authorized synthetic form response; absent responses remain pending.

`boundary_tests` expands supplied below/at/above values into executable cases:

```json
{
  "id": "output-size",
  "tool": "your_actual_tool",
  "dimension": "output",
  "effect": "read",
  "argument": "your_actual_size_argument",
  "arguments": {},
  "variants": [
    {"name": "below", "value": 149999, "expected": {"kind": "success", "max_text_chars": 150000}},
    {"name": "at", "value": 150000, "expected": {"kind": "success", "max_text_chars": 150000}},
    {"name": "above", "value": 150001, "expected": {"kind": "tool_error"}}
  ]
}
```

Choose values and expected behavior from the real tool contract; the example
is not a universal truncation/error requirement. Tag timeout cases `timeout`
and size cases `output`. Character counts cannot prove a token limit, and
local deadlines do not prove Claude's hosted 240-second behavior.

```sh
python3 <skill>/scripts/prepare_workflow.py prepare \
  --input integration.json --output submission-pack
python3 <skill>/scripts/prepare_workflow.py check submission-pack
```

`--workflow readiness|tests|policy|obligations|postlaunch` generates one part.
The default generates all five parts for an existing server, never a new server.
Each part contains reviewable artifacts; the root manifest hashes them. Edit
the input and regenerate instead of editing a hashed artifact and retaining
old claims.

For a loaded package, use `audit --source <target.zip> --output <audit-pack>`.
Select `--profile submission` to check public-route metadata as well. An
approved local partner route additionally uses `--submission-route desktop-only
--desktop-allowlist <confirmation.json>`. These flags are passed through to the
same package checker and recorded in the source inspection. Use `--synthetic`
only for controlled fixtures; synthetic confirmation and reserved URLs cannot
establish real submission eligibility. Recording URLs and review cases remain
observed definitions until playback and execution are actually verified.

## 1. Server readiness

`readiness/record.json` and `review.md` bind capability, transport, auth, hosting,
distribution and per-host limits to the input. They identify unsupported or
unreachable configurations and map boundary fixtures to intended surfaces.
OAuth checks cover registration, callbacks, refresh, denied access, audience
and isolation. Fill `server.auth` with actual configuration; executing the
appropriate tests is still required. A configured value is not a successful
OAuth test. Inspect the record's concrete next actions and resolve them.

## 2. Start without a server

Only use this mode when creating a new server is requested:

```sh
python3 <skill>/scripts/prepare_workflow.py starter --name my-server --output my-server
cd my-server
npm ci
npm run build
npm test -- --engine sdk --era modern --report results/sdk.json
npm test -- --engine mcpdo --era modern --report results/mcpdo.json
```

This creates a current-SDK TypeScript server with a deterministic `add_numbers`
tool, runnable valid/invalid tests, a source-bound plan, and production gaps.
`npm start` serves stdio. `npm start -- --http` binds HTTP to 127.0.0.1 only.
Keep the fresh-server factory and SDK transport handling. Authentication,
public hosting and hosted-surface verification are explicit remaining work.

## 3. Execute and assess a connector test kit

Run the generated `tests/` project with `npm ci`, `npm run build`, and `npm test`
as above. The SDK and mcpdo engines discover the live inventory, compare names,
execute assertions, and save local evidence next to the report. See
[mcpdo operation](mcpdo.md) for persistent/pending behavior.

Use `--allow-writes` or `--allow-destructive` only within existing authorization
and sample-data scope. Unknown effects are blocked. `--engine inspector` uses
independent one-request CLI checks. `--engine claude-code --allow-model-calls`
uses the actual Claude CLI account and verifies matching tool-use/result events,
with a default $2 per-case cap. Missing access stays Blocked. This does not test
claude.ai or Cowork on their behalf.

`--receipts receipts.jsonl` matches fresh server records containing `tool` and
the actual `arguments` to cases. The starter can write these using
`SUBMISSION_RECEIPTS_FILE`; pass that variable through `env_from`. For another
service, export equivalent sample-data receipts from its own logs. Missing
receipts leave server-side confirmation Not run.

```sh
python3 <skill>/scripts/prepare_workflow.py assess submission-pack \
  --report sdk.json --report mcpdo.json --report claude-code.json
```

Assessment checks revision bindings and evidence hashes, then reports case/tool/
engine/host coverage and server confirmation separately. Keep each run's adjacent
`.evidence` directory when moving the report. Exit 2 means incomplete coverage;
exit 1 means a detected failure. Separate manual real-host evidence is still
needed for surfaces this runner cannot drive. Never promote an SDK pass into a
hosted-Claude pass or a package check into integration correctness.

## 4. Policy applicability and evidence

The clause counts and publisher terms below apply only to `platform: claude`.
OpenAI records use current OpenAI primary sources with unresolved requirements
left unverified. New input records default to `platform: openai`.


`policy/record.json` and `review.md` cover all 32 policy entries (introductory
continuing compliance and clauses 1.A–5.G). In the input's `policy`, key decisions
by clause. Supply `applies: yes/no/unknown`, `behavior`, `rationale`, `finding`,
`confirmed_by`, `confirmed_at`, and `evidence` items with `kind` and `path`.
The generated row identifies its required kind: `behavior`, `document`, or
`owner`. Supplied files are hashed and copied into the pack. URLs are references
only; a privacy URL cannot close a behavioral data-handling requirement.

Non-applicability requires a rationale and creator confirmation. Open findings
remain open. `preparation_complete` describes the record, while
`legal_compliance_certified` remains false. Confirm current policy and any
exception directly; the generator cannot authorize one.

## 5. Publisher obligations

`obligations/` is a separate record covering the terms' 14 commitments. Populate
`publisher.name` and `publisher.decisions` by the generated clause ID, with
`statement`, creator identity/date, and an `owner` evidence file. These include
rights, disclosures, licenses, indemnity, security maintenance, vulnerability
intake, branding, and changes to terms. Technical test results never fill these
answers. Generation and validation do not accept terms or submit anything.

## 6. Post-launch preparation

Provide `release.before` and `release.after`, each with separate `server`,
`package`, and `listing` identities/versions. An inapplicable unit must say
`applicable: false` with `reason`. Include owner, support/security contacts,
concrete `rollout` and `rollback` commands/steps, and `health_source`.

`postlaunch/` contains the computed change impact, regression case IDs,
listing-update material, runbook and a runnable one-shot health checker.
Changed slugs, non-increasing changed-package versions and missing decisions
are findings. Server changes, package scan/publication and reviewed listing
edits stay separate. Read current portal rules before executing release actions.

Fill `health-input.json` from actual portal measurements, then run
`python3 postlaunch/check_health.py postlaunch/health-input.json`. Preview,
suppressed, stale or missing figures remain Unknown. It requires the request-error
denominator, rather than substituting tool-error metrics. The 48-hour freshness
default is a configurable local policy. It does not start monitoring. The
runbook includes the distinct plugin and connector delisting procedures;
preparing them does not authorize sending a request or delisting.

