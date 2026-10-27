# Telemetry contract tests

Use this reference when telemetry capture or a telemetry-backed policy is the
requested behavior. It is an example of [test quality and evidence](test-quality.md),
not a requirement to add telemetry to other tests. Establish the consumer's
actual instrumentation, conventions, transport and storage packages first.

## Keep boundaries visible

| Boundary | What its test can establish |
| --- | --- |
| Producer instrumentation | Correct attributes/events on the intended native span, capture configuration and ownership. |
| Export and ingestion | Actual wire value types survive conversion; policy admits or drops the specified inputs. |
| Persistence | The stored row contains the expected representation and excludes prohibited values. |
| Read surface | The response returned through the real read/redaction path protects sensitive values. |

An `Activity` tag test does not prove persistence. A collector test supplied with
synthetic payloads does not prove the producer emitted them. Ingestion dropping
and read-time redaction are separate protections; neither proves the other.
Use the corresponding real DTOs and entrypoints at each boundary. For example,
a producer can use its instrumentation and published conventions without
depending on collector storage types; a storage integration test should inspect
the actual collector payload and row instead of a lookalike local model.

Keep an automatic fixture responsible for startup, observation, bounded waiting
and disposal. Keep expected domain values in the test's scenario contract.
An attribute can select a typed policy; it must not manufacture observations or
turn unavailable evidence into a pass. Distinguish success, a policy violation
and insufficient evidence, preserving the original test result and failures.

## Capture and privacy examples

Select cases from the changed contract rather than generating a Cartesian
product of every option. The following examples originated in captured-field
verification; they are not a claim that every producer supports these features.

- **Normalization:** distinguish `X-Request-Id` from `X_Request_Id`. Check the
  independently specified keys `http.request.header.x-request-id` and
  `http.request.header.x_request_id` on the same span so a collision is visible.
- **Value shape:** require `string[]`, including a one-element array for a
  single value. Check multi-value contents and contractually required order;
  string joining or `ToString()` can hide a type error.
- **Collector policy:** prove benign HTTP headers and RPC metadata reach the
  persisted JSON as arrays. Separately prove credentials are absent after
  ingestion, malformed bare prefixes are rejected, and a promised dropped-value
  metric changes. Observe the relevant measurement and labels in isolation;
  unrelated parallel traffic must not determine the expected count. A missing
  attribute alone does not establish the metric.
- **Read-time privacy:** use sensitive values inside arrays through the actual
  redactor/read path and inspect returned elements. Include benign arrays to
  detect indiscriminate redaction. Never use live credentials as fixtures.
- **Opt-in configuration:** check both unset and empty configuration. Assert
  absence across the relevant attribute prefix, not just one sample key.
- **HTTP:** include selected general and content headers on both request and
  response. Exercise contentless messages and a failed request with no response;
  request capture must remain observable when that is the promised behavior.
- **gRPC:** check case-insensitive duplicate aggregation and encounter order,
  binary metadata exclusion, and both initial headers and trailing headers.
  Use an actual binary entry that fails if its string value is accessed; testing
  only a key ending in `-bin` does not cover the entry's binary representation.

Use published constants for known configuration keys, sources and shared profile
identifiers; do not normalize away intentionally hostile or distinct test input.
A shared profile label prevents spelling drift but is not an expected-output
oracle. Keep enum policy selectors distinct from string scenario names.

## Native ownership, cancellation and publication

Verify the source, operation, kind, status and parent relationship that the
scenario promises. Require its parent where applicable; do not conditionally
skip the assertion. If an exact operation set matters, check identities and
uniqueness as well as count: duplicated spans can otherwise replace missing
ones. Do not create replacement spans merely to satisfy the verifier.

Use the instrumentation library's supported registration and lifetime APIs.
For an OpenTelemetry SDK component, a provider-owned instrumentation factory
may fit an `IDisposable` observer; a processor with no processing callbacks is
not justified solely to obtain disposal. SDK `AddInstrumentation` registration
does not imply CLR profiler instrumentation. Neither that name nor a successful
managed run establishes trimming or Native AOT compatibility. Private payload
access also requires runtime-specific evidence, even with modern accessor APIs.

Publish an expensive consumer once at its fixture's supported lifetime and run
independent profiles as native MSTest rows with isolated child processes.
Forward native test cancellation to publication, process waits and other
cancellable work; join owned processes before removing their workspace.
Use the [lifecycle](lifecycle.md) and [data](data.md) guidance for those mechanics.

Keep source tests, local published consumers and consumers restored from the
released package as distinct evidence. Native AOT proof needs execution of the
actual published artifact and an appropriate runtime check, not just a publish
exit code. Report which artifact, configuration and boundary were verified.
