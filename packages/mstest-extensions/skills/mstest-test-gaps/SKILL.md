---
name: mstest-test-gaps
description: "Find caller-visible behavioral changes that existing MSTest cases would miss. Use for scoped blind-spot analysis; evidence for a specific fix or feature belongs to mstest-test-value."
---

# Find observable test gaps

The [opinionated native stack](../mstest-extensions/references/native-stack.md)
is MSTest.Sdk 4.5.1 / MTP 2.5.1 with `AllMicrosoft` and Microsoft.CodeCoverage.

Inventory the requested public outcomes and the tests that reach them. The
checked native baseline is MSTest 4.5.1 / MTP 2.5.1; framework/package uncertainty
is resolved only where it changes the analysis. A focused risk does not imply
an audit of every behavior written by the same method.

Trace successful, negative, boundary, cancellation, disposal and delivery paths
where relevant. Admission requires a caller-visible difference. An equivalent
internal mutation is not a gap, and a synthetic seam that hides the real boundary
can invalidate the conclusion. Case names and coverage percentages alone do not
establish what the assertions distinguish.

For an advisory review, source/assertion mapping can establish an uncovered
outcome without executing mutations. Label empirical survival unverified.
When survivor verification is requested, use the smallest existing baseline and
a buildable plausible fault, preserve assertions and inspect the expected case's
actual outcome. Restore all changes after each probe. New tests are added when
requested to close demonstrated gaps, not to fill a quota.

Report each distinct outcome, reaching cases, missing distinguishing check and
the evidence status. Keep static absence, suspected weakness, detected fault and
executed survivor separate. [Quality guidance](../mstest-extensions/references/test-quality.md)
contains examples and [test scopes](../mstest-extensions/references/test-scopes.md)
separates source, component and package-consumer boundaries.
