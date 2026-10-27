# TypeScript MCP implementation

Use this when the requested preparation includes changing TypeScript MCP code.
Inspect the existing implementation first; a package audit alone does not need
a new SDK dependency. Keep the integration's chosen language and runtime.

## Resolve the SDK generation before editing

Read `package.json`, the lockfile, runtime constraints, and actual imports.
Record the installed package versions, intended protocol revision, transports,
and client surfaces. The protocol date is not an npm version.

Open the [official SDK index](https://modelcontextprotocol.io/docs/2026-07-28/sdk)
and its [TypeScript repository](https://github.com/modelcontextprotocol/typescript-sdk).
Check the matching release documentation and installed package exports/types.
The verified 2026-10-15 baseline is v2: `@modelcontextprotocol/server` and
`@modelcontextprotocol/client`. The monolithic `@modelcontextprotocol/sdk` is
the maintained v1 line; finding it in an older tutorial does not make it the
current starting point. Use the [v2 docs](https://ts.sdk.modelcontextprotocol.io/v2/)
for v2 code; the SDK site's unversioned root serves v1 documentation.

For an authorized v1 migration, follow the
[migration guide](https://ts.sdk.modelcontextprotocol.io/v2/migration/upgrade-to-v2).
Use its official codemod when appropriate, inspect unresolved diagnostics,
update the lockfile, and verify the result. Do not combine v1 import paths with
v2 examples or silently turn a narrow submission fix into a major migration.
If current documentation and installed exports disagree, state the mismatch
and resolve the selected version before claiming runnable code. Record source
URLs and retrieval dates; recheck this baseline on the next implementation task.

## Use the SDK's implementation

| Work | Idiom and primary guide |
| --- | --- |
| Server tools | [Build a server](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-server): `McpServer` from `@modelcontextprotocol/server`, `server.registerTool(...)`, and complete Zod object schemas for the documented v2 example. |
| stdio serving | `serveStdio` from `@modelcontextprotocol/server/stdio`, with a `createServer()` factory returning a fresh instance on every invocation. The factory also serves negotiation probes. |
| Client calls | [Build a client](https://modelcontextprotocol.io/docs/2026-07-28/develop/build-client): `Client` from `@modelcontextprotocol/client`, `StdioClientTransport` from `@modelcontextprotocol/client/stdio`, then `connect`, `listTools`, and `callTool` using their installed signatures. |
| HTTP serving | `createMcpHandler(createServer)` with the matching framework adapter from the [v2 serving docs](https://ts.sdk.modelcontextprotocol.io/v2/serving/http.html). Its factory creates a fresh server per request. Choose the integration's transport; a stdio example is not a hosted connector. |

Do not reuse one `McpServer` instance through the factory. Directly wiring
`server.connect(new StdioServerTransport())` does not establish support for the
2026-07-28 negotiation path. Keep stdio diagnostic logging on stderr.

## Typed results without invented APIs

[Client Best Practices](https://modelcontextprotocol.io/docs/2026-07-28/develop/clients/client-best-practices)
describes a host generating typed functions from tool input and output schemas.
Its illustrative `mcp.callTool<T>(name, input)` wrapper is not evidence that the
SDK `Client` exposes that signature or a built-in code generator. Verify actual
APIs in the [client calling reference](https://ts.sdk.modelcontextprotocol.io/v2/clients/calling.html).

Prefer schema-derived types and the SDK's supported result handling over
parallel handwritten interfaces and ad hoc parsing of tool text. Respect
`isError`, structured output, and runtime validation. An absent `outputSchema`
leaves output untyped; a cast does not validate it. Use progressive discovery
or code mode when the host needs those capabilities, not as a prerequisite for
a small connector. Existing host authorization still applies to generated calls.

## Let the SDK handle protocol eras

Use [Versioning and Compatibility](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)
and the [stdio binding](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)
to interpret captures. Modern requests carry version metadata per request;
legacy clients use `initialize`. A recognized modern version error does not
mean “fall back to legacy.” A stdio compatibility probe can encounter different
legacy errors or silence, so a fallback keyed only to `-32601` is insufficient.
Modern-only clients need not probe, although stdio probing helps detect an
incompatible peer before an era-ambiguous tool call.

Check the installed [SDK protocol support](https://ts.sdk.modelcontextprotocol.io/v2/migration/support-2026-07-28.html)
before deleting custom negotiation. The verified v2 API already provides
`ClientOptions.versionNegotiation`: `mode: 'auto'` allows negotiation/fallback,
while `mode: { pin: '2026-07-28' }` requires that revision. Its default remains
legacy. Use `getProtocolEra()` to record the result. Let the SDK attach reserved
`_meta` fields and classify failures; transport/auth failures are not generic
permission to retry using another era.

Distinguish the wire format from the public SDK result. The current v2 protocol
layer consumes `resultType` and exposes normalized results; application code
should not add its own `result.resultType` dispatch. Inspect raw frames when
debugging that field, and verify the installed release's behavior for incomplete
or unsupported result kinds. The [Inspector era guide](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/protocol-eras)
helps read those frames; its examples are not proof that every depicted feature
exists in a particular SDK release.

## Authorization: match the helpers to the generation

Read [Understanding Authorization](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/authorization)
for the flow, then check the [v2 authorization reference](https://ts.sdk.modelcontextprotocol.io/v2/serving/authorization.html)
for implementation. The former still contains `@modelcontextprotocol/sdk/server/auth/*`
imports at this verification date. Do not paste those into a v2 project.

For v2 Express servers, `requireBearerAuth`, `mcpAuthMetadataRouter`, and
`getOAuthProtectedResourceMetadataUrl` come from `@modelcontextprotocol/express`.
Web-standard hosts use the corresponding server-package helpers. Preserve the
application's token verifier, audience/resource checks, scopes, and identity
provider configuration. SDK middleware does not decide application permissions.
Confirm compatible adapter versions: the v2 guide specifically documents an
older Express adapter that did not forward `expectedResource`.

The old authorization-server helpers are in `@modelcontextprotocol/server-legacy/auth`;
new services should use a dedicated identity provider. Removing handwritten
bearer parsing or metadata responses must retain real token validation and
unauthorized-request behavior.

## Remove duplication and prove the replacement

Within the authorized change, identify code duplicating SDK discovery,
negotiation, dispatch, transport lifecycle, schema validation, result handling,
or OAuth middleware. Map each piece to the chosen SDK API, replace it, and
delete the redundant implementation, obsolete imports, and unused dependencies.
Retain business logic, permissions, observability, and custom behavior that the
SDK does not supply. Explain any protocol wrapper that still has a concrete job.

Type-check/build with the resolved dependencies, then exercise discovery, a
valid tool call, invalid input, error handling, and cleanup through the real
client/server path. For auth edits, test missing/expired/wrong-audience tokens,
insufficient scopes, and metadata discovery as applicable.

Use the [Inspector CLI](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/cli)
for independent checks: each invocation connects, makes one request, and exits.
Capture machine-readable output and the actual exit/error class. Authentication,
unreachable-server, and tool failures must not collapse into success merely
because JSON was printed. Use `--stored-auth-only` for a noninteractive run
that should fail clearly when account access is missing.

When several steps must share a connection, follow [mcpdo testing](mcpdo.md).
It covers the installed agent guide, named connections, pending auth/elicitation,
supported task flows, transport recovery, and cleanup.

For claimed modern/legacy interoperability, set the era explicitly. Inspector
uses `--protocol-era`; mcpdo uses `connect --era`. Verify modern and legacy
separately, then exercise `auto` fallback if that behavior is claimed. The
default legacy run proves nothing about modern dispatch. Record the selected
and negotiated era, tool arguments/results, and relevant redacted wire traffic.
Test legacy rejection/silence and modern version errors when replacing fallback
logic; do not infer successful fallback from compilation or a captured probe.

Bind results to dependency versions, protocol era, source revision, and actual
host. Missing runtime or account access remains Not run or Blocked. Successful
SDK calls do not prove directory approval or a different host's behavior.

