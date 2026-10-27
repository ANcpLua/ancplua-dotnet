---
name: mstest-assertion-review
description: "Assess the strength and meaning of existing MSTest assertions without editing them. Use for tautological, shallow, conditional or incomplete oracles; concrete assertion fixes belong to mstest-writing-tests."
---

# Assess assertion strength

The [opinionated native stack](../mstest-extensions/references/native-stack.md)
is MSTest.Sdk 4.5.1 / MTP 2.5.1 with `AllMicrosoft` and Microsoft.CodeCoverage.

Follow the executed check through helpers and child reports before deciding it
verifies nothing. Use resolved MSTest semantics; native 4.5.1 / MTP 2.5.1 is the
checked baseline. This is a focused assertion review, not a coverage campaign.

Ask which plausible wrong output would still pass. Presence and count checks can
be sufficient for some contracts and too weak for others. Consider exact type,
identity, ordered values, uniqueness, required absence and correlation only when
the contract makes them observable. One precise equality can fully verify a rule;
assertion variety or quantity is not a quality target.

Required preconditions are checks: a missing parent must fail before parent ID
comparison. A structured array compared through string joining can hide a wrong
representation. An expected value computed by the changed production routine can
repeat its defect. Awaited exception assertions differ from tasks merely created.

Report the concrete accepted wrong behavior and an appropriate native assertion
shape. Expected/actual order and specific typed assertions improve failure
output, but no custom fluent API or new assertion framework is implied. Keep a
source-proven weakness distinct from an unexecuted hypothetical fault.

[Assertions](../mstest-extensions/references/assertions.md) describes native APIs;
[quality guidance](../mstest-extensions/references/test-quality.md) calibrates
independent evidence and required preconditions.
