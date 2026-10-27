---
name: mstest-test-review
description: "Review MSTest tests for false confidence, flakiness, ownership and maintainability. Use for a practical report-only audit; formal smell taxonomy, assertion-only analysis and implementation edits have separate workflows."
---

# Review MSTest tests

The [opinionated native stack](../mstest-extensions/references/native-stack.md)
is MSTest.Sdk 4.5.1 / MTP 2.5.1 with `AllMicrosoft` and Microsoft.CodeCoverage.

Read the named tests, their helpers and only the production context that changes
the verdict. Determine the actual runner and dependency boundary. Native MSTest
4.5.1 / MTP 2.5.1 is the checked baseline, with the consumer's resolved stack
controlling version-specific claims.

Trace each significant expectation to its executed assertion. Delegated checks,
exception assertions, child reports and explicit verification count as checks.
Unawaited operations, swallowed required failures, conditional required evidence
and assertions derived from the production algorithm can produce false passes.

Review lifetime and isolation at the relevant scope: data-row mutable state,
base/derived setup, shared publication, invocation cancellation and cleanup of
owned work. Real infrastructure is appropriate when it is the declared boundary.
A shared immutable fixture or a deliberate multi-step workflow is not itself a
defect. Fixed sleeps and hidden environmental dependencies need concrete effects
before a severity claim.

Report confirmed findings by impact, with file/line evidence, the accepted wrong
behavior or likely race, and a native replacement. Keep static findings separate
from unexecuted fault hypotheses. Clean code can receive a clean report. This
workflow does not authorize edits, a repository-wide scan or new model trials.

[Quality and evidence](../mstest-extensions/references/test-quality.md) provides
calibration. [Lifecycle](../mstest-extensions/references/lifecycle.md) provides
native ordering and cancellation details where those determine a finding.
