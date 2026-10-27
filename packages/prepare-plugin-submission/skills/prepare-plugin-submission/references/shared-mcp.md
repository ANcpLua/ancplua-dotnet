# Shared MCP Reference
## Contents

- 1. Purpose
- 2. Official protocol sources
- 3. MCP architecture
- 4. Protocol lifecycle
- 5. Protocol versions and compatibility
- 6. Transport implementations
- 7. JSON-RPC and message handling
- 8. Capability negotiation
- 9. Tools
- 10. Resources
- 11. Prompts
- 12. Authorization and authentication
- 13. Security and trust boundaries
- 14. Errors and failure handling
- 15. Session lifecycle and concurrency
- 16. Advanced capabilities
- 17. SDK usage
- 18. MCP Inspector and mcpdo testing
- 19. Test-kit generation
- 20. Independent verification
- 21. Observability and operational readiness
- 22. Versioned documentation and evidence
- 23. Shared MCP acceptance criteria


> **Path convention:** deliverable paths below (`architecture/`, `readiness/`, `security/`, `publisher/` and similar) are relative to the output directory of the pack being produced (for example `prepare_workflow.py --output <dir>`). They are not paths in this repository and do not exist here.

> Target: Submission Studio 2.0.0. This is the engineering contract, not a claim of completed implementation or verification. The installed source used for this update was 1.2.1; unavailable baseline records are omitted. Verify current primary pages before enforcing version-sensitive rules.

Standalone vendor-neutral MCP engineering specification • Baseline: October 13, 2026

## 1. Purpose

This reference defines the common MCP engineering contract used by independent platform-specific submission assistants.

It must cover protocol implementation, SDK usage, transports, discovery, tools, resources, prompts, capability negotiation, authorization, security, session lifecycle, error handling, testing, and operational behavior.

It must not contain OpenAI or Anthropic directory submission policies. Host-specific feature support, authentication configuration, and publication requirements belong in their respective vendor references.

## 2. Official protocol sources

Primary specification: [MCP specification, July 28, 2026](https://modelcontextprotocol.io/specification/2026-07-28).

Documentation discovery: [MCP documentation index](https://modelcontextprotocol.io/llms.txt).

The implementation must maintain an explicit protocol-version record. When supporting another protocol version, document differences and test negotiation rather than silently assuming compatibility.

The following describes the engineering coverage required by this handoff. The precise normative behavior for a given version must be checked against the official specification.

## 3. MCP architecture

The architecture consists of hosts, clients, and servers.

The host provides the environment in which an MCP client connects to an MCP server. The server exposes capabilities through protocol-defined operations.

Implementations must distinguish transport-level connectivity, protocol initialization, advertised capabilities, authorization, and successful execution.

A successful HTTP connection alone does not prove MCP compatibility.

## 4. Protocol lifecycle

Implement and test the applicable lifecycle. This is a conceptual coverage list, not a fixed wire-message sequence. Resolve discovery, initialization and negotiation against the selected protocol era and installed SDK; do not impose legacy messages on a different protocol version:

1. Establish transport.
2. Initialize the protocol connection.
3. Negotiate or confirm supported protocol version.
4. Exchange capabilities.
5. Discover the server's available tools, resources, prompts, and other negotiated capabilities.
6. Invoke supported operations.
7. Process responses, notifications, and errors.
8. Maintain or terminate sessions according to the negotiated transport and protocol behavior.
9. Release resources and close the connection cleanly.

The implementation must distinguish connection establishment, initialization, capability negotiation, and successful tool execution.

Acceptance: A client must initialize successfully, discover supported capabilities, invoke representative operations, and terminate without leaving unintended resources or processes.

## 5. Protocol versions and compatibility

The baseline specification is:

[https://modelcontextprotocol.io/specification/2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)

The assistant must maintain explicit protocol-version support.

It must verify the actual version negotiated between client and server rather than assuming that the newest specification is supported by every host.

Test applicable behavior for:

- Matching client and server versions.
- Supported older versions.
- Unsupported versions.
- Unknown capabilities.
- Optional capabilities not advertised by the server.
- Version-specific transport or feature differences.

Produce:

```
protocol/
  supported-versions.json
  capability-matrix.json
  compatibility-tests.json
  negotiation-results.json
```

Acceptance: Every claimed protocol version must have supporting negotiation and functional evidence. Features introduced in newer specifications must not be treated as universally available.

## 6. Transport implementations

Support the MCP transports appropriate to the deployment.

### Standard input/output

Stdio is appropriate for local process integrations.

Verify process startup, protocol message framing, standard output discipline, standard error logging, lifecycle handling, and clean termination.

Protocol output must not be corrupted by unrelated application logs.

### Streamable HTTP

For remote integrations, implement the applicable HTTP transport requirements, including request handling, content negotiation, sessions, streaming behavior where supported, and protocol errors.

Verify both client and server behavior rather than assuming that an HTTP endpoint returning status 200 is an MCP server.

### Transport compatibility

Record transport availability independently from protocol capability support.

A server supporting stdio does not automatically support remote HTTP connections.

A development tunnel does not automatically satisfy a platform's public-directory hosting requirements.

Deliverables: transport configuration, executable connection tests, logs, and compatibility results.

## 7. JSON-RPC and message handling

MCP uses JSON-RPC message structures for applicable requests, responses, and notifications.

Use the SDK-provided behavior for the following, adding custom protocol handling only for a verified SDK gap:

- Request identifiers.
- Method dispatch.
- Parameters.
- Successful results.
- Protocol errors.
- Notifications.
- Request correlation.
- Malformed-message handling.
- Unsupported-method behavior.

Do not confuse JSON-RPC protocol errors with tool-execution errors returned through an otherwise successful protocol response.

Acceptance: Invalid messages and unsupported operations must produce appropriate protocol behavior without corrupting the connection or executing unintended operations.

## 8. Capability negotiation

Advertise only capabilities that the server actually implements.

Support conditional discovery of tools, resources, prompts, and applicable advanced capabilities.

Do not assume that a host implements every capability defined by the protocol.

The client and server must handle unsupported optional capabilities gracefully.

Produce a capability inventory tied to the actual server revision.

Acceptance: Advertised capabilities must correspond to implemented behavior. Unsupported capabilities must not be silently simulated as successful.

## 9. Tools

Tools expose callable operations.

Each tool should have an accurate name, description, input schema, and applicable output schema or result contract.

Design tools around meaningful user operations rather than one unrestricted catch-all executor.

Separate read operations from writes and destructive actions where appropriate.

### Required testing

For each exposed tool, verify:

- Discovery.
- Valid input.
- Invalid input.
- Schema boundaries.
- Successful execution.
- Error behavior.
- Authorization.
- Expected side effects.
- Actual returned content.
- Relevant timeout behavior.
- Relevant concurrency behavior.

Maintain an inventory of every exposed tool and its execution evidence.

A prompt count is not a tool-coverage count.

### Deliverables

```
tools/
  inventory.json
  schemas.json
  cases.json
  results.json
  coverage.json
```

Acceptance: Each tool must behave consistently with its declared contract. Tool results must be verified against actual execution, not only expected text.

## 10. Resources

Resources expose retrievable content through the protocol.

Where supported and applicable, implement resource discovery, identifiers, metadata, retrieval, and updates or subscriptions.

Verify content types, authorization, missing resources, invalid identifiers, and stale-resource behavior.

Resources must not expose data outside the authenticated user's permitted scope.

Acceptance: Resource discovery and retrieval must return the intended content with correct access controls.

## 11. Prompts

Where supported, MCP prompts provide discoverable prompt templates or structured prompt workflows.

Implement applicable discovery, argument definitions, argument validation, and retrieval.

Do not confuse MCP prompts with vendor-specific plugin skills.

Verify required and optional arguments, malformed requests, and actual returned prompt content.

Acceptance: Advertised prompts must be retrievable and usable by a compatible client.

## 12. Authorization and authentication

Use the applicable MCP authorization specification for HTTP-based integrations.

The implementation must account for:

- Protected resource metadata.
- Authorization server discovery.
- Client registration.
- Authorization requests.
- Redirect validation.
- PKCE where applicable.
- Token validation.
- Audience restrictions.
- Scope restrictions.
- Token expiration.
- Refresh.
- Revocation.
- Consent denial.
- User and tenant isolation.

Authorization is separate from descriptive tool annotations.

A tool marked read-only still requires appropriate access control when reading protected data.

A static bearer-token test proves only the tested token-handling behavior, not a complete OAuth implementation.

### Deliverables

```
security/
  authorization-architecture.md
  scopes.json
  access-matrix.json
  oauth-cases.json
  authorization-results.json
```

Acceptance: Unauthorized requests must fail safely, while authorized requests must remain restricted to the permissions actually granted.

## 13. Security and trust boundaries

Treat tool arguments, tool outputs, retrieved resources, and external content as potentially untrusted.

Implement applicable protections against:

- Unauthorized data access.
- Cross-user and cross-tenant leakage.
- Prompt injection.
- Command injection.
- Path traversal.
- Server-side request forgery.
- Credential disclosure.
- Unsafe logging.
- Unintended destructive actions.
- Excessive resource consumption.
- Untrusted redirects.
- Insecure transport configuration.

Apply least privilege and explicit authorization for sensitive operations.

Separate the model's request for an operation from the server's authority to perform it.

Acceptance: Security tests must verify actual boundaries. A clean static scan is not proof that all security properties hold.

## 14. Errors and failure handling

Implement useful, distinguishable errors for:

- Invalid arguments.
- Unsupported operations.
- Authentication failure.
- Authorization failure.
- Missing resources.
- Backend unavailability.
- Rate limiting.
- Timeouts.
- Cancelled operations.
- Session expiration.
- Transport failure.
- Internal execution failure.

Do not return misleading success results when an operation did not complete.

Errors must not expose secrets or unnecessary internal details.

Acceptance: Failure tests must verify that no unintended side effects occurred and that the caller receives an appropriate error.

## 15. Session lifecycle and concurrency

Where applicable, verify:

- Session creation.
- Session identification.
- Session expiration.
- Reconnection.
- Session termination.
- Concurrent requests.
- Request cancellation.
- Long-running operations.
- Resource cleanup.
- Graceful shutdown.

Do not assume all MCP transports use the same session model.

Acceptance: Sessions must not leak data or state between unrelated users, and shutdown must not leave uncontrolled processes or resources.

## 16. Advanced capabilities

The assistant must discover and conditionally support advanced MCP capabilities rather than treating them as mandatory.

These may include:

- Elicitation.
- Sampling.
- Progress notifications.
- Logging.
- Resource subscriptions.
- Long-running tasks.
- Interactive UI extensions.
- Other capabilities defined by the selected protocol version.

For each advanced capability, verify both protocol support and host support.

Acceptance: An advanced feature is supported only when its implementation and relevant client behavior have been tested.

## 17. SDK usage

Prefer a maintained MCP SDK compatible with the selected language and protocol version.

The implementation must inspect SDK documentation and version information before generating code.

Pin dependencies appropriately and retain lock files.

Avoid inventing SDK methods, transport classes, or command-line flags.

Use official SDK APIs for server initialization, tool registration, transport, and message handling.

### Verification

Build the generated project.

Run SDK integration tests.

Connect an independent MCP client.

Verify tool discovery and execution.

Where feasible, compare results across more than one client implementation.

Acceptance: Successful compilation is necessary but insufficient. The server must work through an actual MCP client.

## 18. MCP Inspector and mcpdo testing

MCP Inspector and applicable `mcpdo` commands can provide independent protocol and tool-execution evidence.

Verify installed tool versions and supported command syntax before running them.

Test:

- Server connection.
- Initialization.
- Tool inventory.
- Tool invocation.
- Valid inputs.
- Invalid inputs.
- Returned content.
- Protocol errors.
- Authorization behavior where supported.
- Timeouts.
- Session behavior.

Maintain raw execution logs and structured results.

Do not label an Inspector run as verification inside Claude Chat or ChatGPT.

### Deliverables

```
testing/
  inspector/
    commands.json
    results.json
    logs/
  mcpdo/
    commands.json
    results.json
    logs/
```

Acceptance: Reports must identify which tool actually executed each case and which checks remain unverified.

## 19. Test-kit generation

For an existing MCP server, the assistant should generate a reusable test kit based on the discovered implementation.

The test kit must not depend on manually supplied completed test results.

Inputs may include source code, server configuration, sample data, and supported credentials.

The assistant must derive the tool inventory, schemas, relevant boundaries, and expected operations from actual evidence.

Generate:

```
test-kit/
  README.md
  package.json
  src/
  fixtures/
  plans/
  reports/
```

Use equivalent files for non-JavaScript implementations.

Include valid, invalid, authorization, timeout, and side-effect tests as applicable.

Acceptance: The generated test kit must execute against the target server and produce reproducible evidence.

## 20. Independent verification

The system must distinguish:

1. Source inspection.
2. Static validation.
3. SDK integration testing.
4. MCP Inspector or mcpdo testing.
5. Agent-behavior evaluation.
6. Vendor-host verification.
7. Directory review.
8. Publication.

A successful result at one layer must not automatically establish success at another.

Use actual observed behavior and independent expected results.

Do not generate both the implementation and its supposedly independent correctness oracle from the same unverified assumptions.

## 21. Observability and operational readiness

Prepare structured logging, request correlation, error classification, health checks, deployment documentation, and operational recovery procedures.

Logs must avoid exposing credentials and protected user data.

Prepare monitoring for relevant failures and regressions after deployment. Continuing scheduled operation requires an explicitly configured and authorized external runner; this document or an ended conversation does not establish active monitoring.

Produce:

```
operations/
  observability.md
  health-checks.md
  deployment.md
  rollback.md
  incident-response.md
```

Acceptance: Operational procedures must reference real deployment components rather than invented infrastructure.

## 22. Versioned documentation and evidence

Every protocol requirement must be associated with:

- Protocol version.
- Source URL.
- Source retrieval date.
- Implementation revision.
- Applicable transport.
- Applicable capability.
- Test case.
- Observed result.
- Evidence location.

When the MCP specification changes, preserve previous results under their original protocol versions.

Do not silently reinterpret old results using a newer specification.

## 23. Shared MCP acceptance criteria

A complete MCP implementation must demonstrate, where applicable:

- Successful initialization.
- Correct version negotiation.
- Accurate capability advertisement.
- Working transport.
- Tool discovery and execution.
- Correct input validation.
- Correct response and error behavior.
- Effective authorization.
- Resource and prompt functionality.
- Appropriate session handling.
- Safe failure behavior.
- Reproducible tests.
- Actual observed results.
- Clear documentation of unsupported capabilities.

Meeting these acceptance criteria establishes only the demonstrated protocol and engineering readiness, not vendor-directory approval. The reference document alone establishes neither.
