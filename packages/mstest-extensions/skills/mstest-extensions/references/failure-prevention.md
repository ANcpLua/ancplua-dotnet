# Prevent false confidence in test implementations

These are transferable lessons from capture, conversion and privacy work. Use
only the lesson relevant to the changed contract. They predict plausible agent
mistakes; they are not a phase plan, required suite or project-specific policy.

| Likely mistake | Distinguishing check | Fixture responsibility |
| --- | --- | --- |
| Over-normalizing distinct inputs into one output key | Put punctuation variants on the same record and require both independently specified keys and values. | Produce one identifiable operation and retain its original typed evidence. |
| Converting a collection into a scalar or joined string | Assert the actual collection type and elements for both single and multiple values across the changed boundary. | Expose raw transport or stored representation, without coercing it for assertions. |
| Treating one privacy layer as proof of another | Verify admission/drop, persisted representation and read-time redaction at their respective entrypoints. Include benign controls. | Reach the real component under test; do not substitute a lookalike policy model. |
| Accepting malformed configuration because a positive case passes | Exercise empty/unset configuration and invalid bare prefixes, with absence checked over the relevant namespace. | Supply isolated configuration before startup and restore owned state afterward. |
| Testing only the convenient collection | Select values from each contributing collection and each promised response phase. | Expose general/content or initial/trailing observations distinctly. |
| Accessing a value before checking its representation | Use an actual binary or otherwise incompatible entry that throws on the wrong accessor. | Preserve representation flags and field presence. |
| Assuming a response or content always exists | Exercise contentless input and failed operations with no response; still require the promised request evidence. | Capture failures and completion without inventing a response. |
| Checking a missing field but overlooking a promised drop metric | Assert the relevant isolated measurement and dimensions separately from field absence. | Partition measurements by resource or exemplar; avoid unrelated traffic. |
| Hiding missing observations behind conditional assertions | Require the operation, parent or event before asserting its properties. | Time out with useful missing-evidence diagnostics rather than silently pass. |
| Replacing a missing native span with a duplicate | Check expected identities, uniqueness and required parent relationships as well as count. | Observe the real producer and retain its scope/source identity. |
| Hiding independent scenarios in a manual loop | Use selectable native rows with row-specific outcomes and cancellation. | Share expensive immutable publication while isolating each invocation. |
| Racing cleanup with work that survived an assertion failure | Release and await the original operation before disposing its dependencies. | Own bounded shutdown and child reaping, even when verification fails. |
| Calling a successful build an AOT or package-consumer pass | Run the exact published artifact or deliberately restored candidate package. | Record artifact identity and keep source, candidate and public-package evidence distinct. |

For example, a typed policy attribute selects which invariant to verify. One
executor invokes the original MSTest method, awaits evidence for that invocation
and evaluates the selected policies. The fixture provides observation and
lifetime; the test's contract provides expected values. Neither a shared profile
constant nor the producer's normalization routine is an independent oracle.

See [telemetry examples](telemetry-contracts.md) when the actual protocol is in
scope, [execution](execution.md) for composition and result preservation, and
[lifecycle](lifecycle.md) for shared versus invocation ownership. These examples
do not require adding telemetry or custom attributes to ordinary tests.
