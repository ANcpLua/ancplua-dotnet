# Test quality and evidence

Use this reference for a requested review or a behavior-changing test edit.
For an isolated API correction, go directly to the relevant assertion, data or
lifecycle guidance. Work within the named change or test scope.

## Choose the question before the workflow

| Question | Evidence to collect |
| --- | --- |
| Is this test misleading, fragile or difficult to maintain? | Read its executed assertions, helpers, fixture and relevant production behavior; report concrete effects. |
| Which formal test smell applies? | Use the named taxonomy only when requested and justify the category from code. A label is not proof of a defect. |
| Does this assertion distinguish correct output from a plausible wrong result? | Compare the oracle with the public contract and identify an accepted wrong value. |
| Would these tests miss a behavior change? | Map observable outcomes to reaching tests; distinguish source-proven gaps from unexecuted fault hypotheses. |
| Do these tests verify this fix or feature? | Bind focused passing and failing evidence to the relevant revisions or reproducible patches. |

Read the actual test and follow custom assertions, fixture callbacks and child
reports. A method body without `Assert` may delegate its checks. Report an
unawaited assertion or swallowed required failure as a false-pass defect, not as
an absence of assertions. Do not invent findings to fill a checklist; a review
may conclude that the scope is clean.

## Keep tests expressive and independently diagnosable

- Use native data rows for independently selectable scenarios. A loop that
  checks all elements of one result can be appropriate; a loop that hides many
  independent scenarios behind the first failure loses case reporting.
- Give rows stable, meaningful labels. Where supported, `ArgumentsDisplayName`
  supplies the argument label while retaining the test method name. Preserve
  original discovery locations through execution wrappers.
- Share expensive immutable preparation at the appropriate fixture lifetime;
  isolate mutable state and child execution per case. Shared publication is not
  inherently a smell. An unrelated, costly fixture dependency is a concrete
  reason to split ownership. Follow [lifecycle](lifecycle.md).
- A deliberate end-to-end workflow may verify several related outcomes and use
  real services. Make dependencies explicit; do not replace the boundary under
  test with mocks merely to make it look like a unit test.
- Await observable conditions with a bounded timeout and cancellation. Fixed
  sleeps provide neither readiness nor reliable synchronization.
- Use existing domain types and published constants before inventing local
  wrappers or duplicate string catalogs. Keep enum policy selectors typed.

Trace a suspected static dependency or private coupling to an actual obstacle
before adding a seam. Prefer the existing public entrypoint and native lifecycle.
Do not introduce a factory, interface, injected clock, processor or adapter merely
because a search found `static`, `new`, time or I/O. A testability change needs a
specific benefit without hiding the behavior being verified.

## Make the oracle independent and complete enough

Write a short mapping when it helps resolve uncertainty:

`contract -> input or sequence -> observable result -> named case -> assertion`

Expected results come from requirements, protocol semantics or independently
specified examples. Computing them with the same normalization, filtering or
serialization routine being tested can reproduce the defect. Production
constants are appropriate for shared identifiers; literal adversarial inputs
and independently specified expected wire values can be appropriate oracles.

Presence, non-null and count checks are useful only for the contract they cover.
For structured output, consider type, exact identity, value, order, duplication,
required absence and ownership where relevant. Do not mechanically demand all
of them, add assertion quotas or use assertion diversity as a quality score.
One precise equality assertion can fully verify a behavior.
For a configuration-default case, arrange that the override is absent and assert
the independently specified default value. A non-null endpoint can still be the
wrong endpoint; a reader lock does not arrange an empty environment.

Required preconditions must fail visibly. For example, a test promising parent
span preservation must require a parent before comparing its ID. An `if` that
silently skips this check permits a false pass. Distinguish an intentionally
absent result from a required result that never arrived.

## Verify only the uncertainty that matters

Run the smallest affected set with the repository's real runner; confirm cases
executed, rather than treating build success as test success. Existing tests may
already cover a change. Reuse their results while relevant inputs are unchanged.
Do not add duplicate tests, full-suite runs or mutation campaigns as ceremony.

When failure sensitivity is uncertain and execution is in scope, use one
buildable, relevant fault: restore the old defect, disable the changed behavior
or substitute a plausible wrong output. Keep assertions intact. A compiler
error, unrelated setup failure or killed process does not prove the assertion
detects the fault. Check the expected case, diagnostic and structured outcome;
then restore the exact original files and confirm the corrected behavior.
For an intentional refactor, passing before and after is expected.

Record enough identity to reproduce the evidence: revision or patch, relevant
configuration/packages, command, cases and result. Distinguish a static finding,
an unverified hypothesis, a fault actually detected, and a passing corrected
run. Coverage percentages alone establish none of these. Documentation-only
changes need review and link/package checks, not fabricated execution evidence.

## Upstream reading

The guidance adapts these distinct dotnet/skills topics, reviewed 2026-10-17;
they are optional source links, not installed dependencies or a required chain:

- [Test smell detection](https://github.com/dotnet/skills/blob/main/plugins/dotnet-test/skills/test-smell-detection/SKILL.md) and its [formal catalog](https://github.com/dotnet/skills/blob/main/plugins/dotnet-test/skills/test-smell-detection/references/test-smell-catalog.md).
- [Practical anti-pattern review](https://github.com/dotnet/skills/blob/main/plugins/dotnet-test/skills/test-anti-patterns/SKILL.md).
- [Writing MSTest tests](https://github.com/dotnet/skills/blob/main/plugins/dotnet-test/skills/writing-mstest-tests/SKILL.md); resolve installed APIs before applying examples.
- [Test-value evidence](https://github.com/dotnet/skills/blob/main/plugins/dotnet-test/skills/test-value-evidence/SKILL.md).
- [Assertion quality](https://github.com/dotnet/skills/blob/main/plugins/dotnet-test/skills/assertion-quality/SKILL.md).
- [Test-gap analysis](https://github.com/dotnet/skills/blob/main/plugins/dotnet-test/skills/test-gap-analysis/SKILL.md).

[Testability obstacles](https://github.com/dotnet/skills/blob/main/plugins/dotnet-test/skills/testability-obstacle/SKILL.md)
and [static dependencies](https://github.com/dotnet/skills/blob/main/plugins/dotnet-test/skills/detect-static-dependencies/SKILL.md)
are supporting investigation routes when an actual obstacle exists.
Microsoft's [polyglot unit-testing agent article](https://devblogs.microsoft.com/dotnet/polyglot-unit-testing-agent/)
also motivates repository discovery and behavior-sensitive checks; its unit-test
scope is not evidence about integration, end-to-end or Native AOT behavior.
