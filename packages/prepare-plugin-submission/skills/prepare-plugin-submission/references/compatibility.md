# Compatibility without invented requirements

A custom MCP service is connected by its endpoint. It does not implement
`connector_id`; that API request field selects a legacy OpenAI built-in service
connector. O9 documents its deprecation for models released after September 1,
2026, and distinguishes `server_url` from Secure MCP Tunnel's `tunnel_id`.
Read the current API guide before giving model-specific advice. A question about
supporting older models is not an assertion that deprecation happened earlier:
answer it directly without claiming the creator reversed the cutoff. Older
models retaining the legacy API option does not add a requirement to a custom server.

For TypeScript changes, use the [SDK implementation workflow](typescript-sdk.md)
to match package generation, protocol revision, and tested negotiation. Prefer
the current SDK's supported helpers when replacing duplicated protocol code.

Keep four contracts separate:

| Contract | Evidence |
| --- | --- |
| MCP service | Negotiated protocol, transport, tools/schemas, auth, text/structured output, optional UI. |
| Plugin package | Correct manifest and contained components for each host. |
| Product surfaces | Real runs in each intended ChatGPT, Codex, Claude Chat, Cowork, or Code surface. |
| API caller | Specific tested model IDs and client configuration, if the creator owns an API client. |

A model release-date promise does not exempt an integration from directory
review or restrict the host's chosen model. Do not demand historical model
support without a documented requirement; do not promise every future model.

For a shared remote service, prefer the common supported Streamable HTTP path,
then verify actual protocol negotiation with each client. Separate host-specific
metadata. Return meaningful results without requiring UI. A local process or
Secure MCP Tunnel can support development testing; that does not satisfy the
stable public HTTPS endpoint requirement for remote directory review. Local MCP
packages have a separate approved desktop-only partner route; consult the current
[desktop-only guide](https://developers.openai.com/plugins/deploy/desktop-only).

Read O5 and A5 together for authorization. Test discovery challenges, protected
resource metadata, scopes/audience, client registration, PKCE/callbacks, expiry,
refresh, denied consent, and isolation using the supported flows. Do not log
or package tokens. OpenAI's current public form supports anonymous, OAuth,
and mixed access, not an arbitrary static bearer/API-key input. Nonempty server
headers are rejected in public uploads. Do not label a protected endpoint
anonymous to make connection validation pass.

Each exposed tool needs a truthful description, schema, and explicit boolean
annotations. Read-only/destructive hints describe behavior, not authorization.
O3 no longer requires annotation justifications; retain actual boolean hints.
A catch-all tool selecting arbitrary operations hides reviewable behavior.

