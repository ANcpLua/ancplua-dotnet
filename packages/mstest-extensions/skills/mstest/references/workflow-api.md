# Resolve MSTest API questions

Start with the requested symbol or behavior. For a consumer project, resolve its
MSTest package and target asset before applying version-specific guidance. The
checked baseline here is 4.5.1; a question alone needs no restore or project edits.
Use [version resolution](version-resolution.md)
when the installed version or assembly differs from that baseline.

1. Search [public-api.md](public-api.md) for the type or member when
   its availability or signature is uncertain. Do not load the entire catalog.
2. For combinatorial data, dependencies, resource locks, conditions, hosting or
   configuration, read the relevant section of
   [modern-apis.md](modern-apis.md). These are version-checked examples.
3. Distinguish a declaration from runtime behavior. Use the matching source or
   packaged probe when an answer depends on execution, serialization or AOT.
4. Explain the resolved API and its limits. Run a focused probe only when the
   requested answer needs evidence not already available.

## Boundaries and gotchas

- Catalog versions mean first appearance among the configured compared releases,
  not necessarily the API's original release. Source `main` is research material,
  not proof of the consumer's package contract.
- Experimental acknowledgments belong to the affected API use, not a blanket
  project suppression. Use the diagnostic emitted by the actual package.
- Host-injected tests and a NativeAOT test host have different compatibility
  limits. A managed test can still launch a NativeAOT application under test.
- An API lookup does not authorize rewriting tests or creating a custom runner.

For implementation use [test implementation](workflow-writing-tests.md).
For a precise assertion choice or replacement use
[resolved assertion APIs](assertions.md); for a report-only strength
assessment use [assertion review](workflow-assertion-review.md).
Do not load all three for an ordinary API question.

For catalog maintenance only, follow
[public-api-maintenance.md](public-api-maintenance.md). The configured
release tags and template are maintained with the generator under `scripts/`.
