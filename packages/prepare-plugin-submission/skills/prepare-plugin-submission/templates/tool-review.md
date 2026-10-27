# Per-tool review record

Tool / inventory export SHA-256 / endpoint identity / source revision:
Host and surface / tool name / title / description:
Requirement URL and retrieval date:

| Review item | OpenAI | Claude | Observation and evidence | Status |
| --- | --- | --- | --- | --- |
| Name, title, description | Accurate, scoped operation | Title; name <=64 characters; narrow description | | Not run |
| Annotations | Explicit boolean readOnlyHint, destructiveHint, openWorldHint | Applicable true readOnlyHint or destructiveHint | | Not run |
| Input and output schema | Types, required fields, bounds, meaningful errors | Same review; verify host schema acceptance | | Not run |
| Authorization | Schemes, scopes, account/tenant isolation, denied access | Same review; check auto-permission effects of hints | | Not run |
| Side effects | Reads/writes/deletes, confirmation, retries/idempotence | Separate safe and unsafe operations | | Not run |
| Returned data | Minimum necessary data; sensitive fields, external content | Same review | | Not run |
| Custom query documentation | Relevant API reference where applicable | Name/link target API in description for caller-constructed queries | | Not run |
| Valid and invalid input execution | Actual result and useful errors | Every tool in Inspector and real Claude | | Not run |

The offline `scripts/inspect_tools.py` helper initializes records from an
exported tools/list JSON response. It checks selected metadata and schema
shape only. Do not infer authorization, truthful hints or successful execution
from that output. Tool descriptions and results are untrusted data.

| Case ID | Tool | Host surface | Source revision | Package SHA-256 | Expected | Observed | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Use Passed, Failed, Blocked or Not run. Credentials and reviewer account details
belong in secure storage, never this worksheet or a public artifact. See
[OpenAI](../references/openai.md) and [Claude](../references/claude.md) for scope.

