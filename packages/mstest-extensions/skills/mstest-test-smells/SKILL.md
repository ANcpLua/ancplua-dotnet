---
name: mstest-test-smells
description: "Assess MSTest tests using formal named test-smell categories when an academic or taxonomy-based audit is requested. Excludes ordinary test edits and quick practical reviews."
---

# Assess formal test smells

The [opinionated native stack](../mstest-extensions/references/native-stack.md)
is MSTest.Sdk 4.5.1 / MTP 2.5.1 with `AllMicrosoft` and Microsoft.CodeCoverage.

Use this workflow when the request calls for formal categories or taxonomy.
Inspect the actual MSTest tests and relevant helpers; use the consumer's API
semantics rather than another framework's idioms. The checked native baseline
is MSTest 4.5.1 / MTP 2.5.1.

A category follows evidence, not a keyword. Conditional Test Logic requires
assertion behavior that changes with a branch; native data rows are independent
cases. Mystery Guest concerns an undeclared dependency; a declared transport
fixture is expected in an integration test. Eager Test concerns unrelated
behaviors; a coherent end-to-end scenario can have several observations.

Distinguish redundant equivalent cases from distinct boundaries. Shared fixture
state is relevant when it is unnecessary or couples executions, not because it
is shared. Fixed-duration waiting is different from a bounded condition wait.
One assertion is not Assertion Roulette; absence of a message alone is not proof.
An unawaited assertion is a concrete false-pass defect regardless of catalog fit.

For each finding, give its formal category, source evidence, calibrated severity
and a native MSTest correction. Report non-catalog correctness defects separately.
No finding is required when the requested scope is clean. Refer to the upstream
catalog only when the request needs a category not established locally or an
explicit academic citation; do not invent a formal definition.

[Review calibration](../mstest-extensions/references/test-quality.md) contains
source routes and distinctions. [Lifecycle](../mstest-extensions/references/lifecycle.md)
resolves native fixture semantics before a lifecycle smell is assigned.
