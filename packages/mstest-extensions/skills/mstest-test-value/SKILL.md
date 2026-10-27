---
name: mstest-test-value
description: "Assess test evidence for an identified fix, feature, refactor or test change. Use for revision-bound failure sensitivity and corrected behavior; hypothetical suite gaps belong to mstest-test-gaps."
---

# Assess evidence for a change

The [opinionated native stack](../mstest-extensions/references/native-stack.md)
is MSTest.Sdk 4.5.1 / MTP 2.5.1 with `AllMicrosoft` and Microsoft.CodeCoverage.

Bind the requested behavior to a revision or reproducible patch and its related
MSTest cases. The checked native baseline is 4.5.1 / MTP 2.5.1; use the actual
consumer's packages, runner and relevant artifacts. Existing unchanged tests may
already establish the changed contract.

Map requirement, input/sequence, public outcome, named row and distinguishing
assertion. Expectations come from requirements or protocol semantics, not the
same implementation used to calculate the actual value. Source tests, candidate
package consumers and public-package consumers establish different delivery paths.

When execution is in scope and failure sensitivity is uncertain, a buildable
counterexample can isolate the change: restore the defect or remove/corrupt the
behavior while retaining setup and assertions. The expected case and diagnostic
identify the failure. A missing symbol, unrelated crash or killed process does
not establish assertion sensitivity. Restore the exact original state afterward.
For a behavior-preserving refactor, passing both revisions is expected.

Record relevant input identities, commands, executed cases and observed outcomes.
Reuse valid evidence while those inputs are unchanged. Keep static findings,
proposed probes, actual failures and corrected passes distinct. Documentation
changes do not become executable verification by running unrelated tests.

[Evidence details](../mstest-extensions/references/test-quality.md) includes
counterexamples and boundaries. Runner-specific failures can use the existing
[child verifier](../mstest-extensions/references/executable-evidence.md), with
its declared compatibility limits; no new evaluation loop is implied.
