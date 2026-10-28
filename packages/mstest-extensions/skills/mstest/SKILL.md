---
name: mstest
description: Write, run, review and troubleshoot native MSTest tests and reusable extensions. Use for test projects, MTP commands, API/version lookup, data and lifecycle, quality or gap reviews, and generated/Native AOT execution. Focused built-in assertion replacements belong to mstest-assertions.
---

# Native MSTest testing

Handle the requested testing task using the consumer's resolved MSTest and
Microsoft.Testing.Platform APIs. This skill owns its references, API catalog,
inspection scripts and executable fixtures; they work without another skill.

The checked [native stack](references/native-stack.md) is MSTest.Sdk/MSTest
4.5.1, MTP 2.5.1, `AllMicrosoft` and Microsoft.CodeCoverage. Preserve the
consumer's pins and runner unless a migration is requested. A conceptual
question needs no project creation or restore; a review stays read-only.

## Select the requested workflow

1. Identify the requested outcome and its boundary. Read the consumer's project
   instructions, SDK/package pins and test entrypoint when implementation or
   execution is requested. Use [version resolution](references/version-resolution.md)
   and [the inspector](scripts/inspect_mstest.py) when its API evidence is unclear.
2. Read the matching workflow below and only the topic references it needs.
   A command-only answer does not authorize execution; a review does not authorize
   edits, mutation trials or a suite-wide audit.
3. For changes, verify the observable outcome through the normal repository
   entrypoint. Preserve required failures, cleanup and data-row identity.
   Report static findings, executed results and unresolved limits separately.

| Requested task | Read |
| --- | --- |
| API signature, availability, release difference or configuration | [API lookup](references/workflow-api.md) |
| Write or fix tests, create a test project, repair solution/CI inclusion | [Test implementation](references/workflow-writing-tests.md) |
| Run or discover tests, choose filters, collect TRX/coverage, diagnose zero tests | [Native MTP execution](references/workflow-run-tests.md) |
| Reusable data, domain assertions, execution attributes, policies or fixtures | [Extension design](references/workflow-extensions.md) |
| Practical correctness, ownership, flakiness or maintainability review | [Test review](references/workflow-test-review.md) |
| Focused report on assertion strength and accepted wrong results | [Assertion review](references/workflow-assertion-review.md) |
| Explicitly requested formal test-smell taxonomy | [Test smells](references/workflow-test-smells.md) |
| Outcomes the current suite would miss | [Test gaps](references/workflow-test-gaps.md) |
| Evidence for an identified change and revision | [Change evidence](references/workflow-test-value.md) |
| Generated invocation, trimming or published Native AOT tests | [Native verification](references/workflow-native-aot.md) |

## Evidence and API boundaries

Search [the public API catalog](references/public-api.md) by symbol; do not load
it wholesale. Its introduction labels cover the compared releases, not necessarily
the API's first release. [Modern examples](references/modern-apis.md) and
[anti-patterns](references/antipatterns.md) provide dated behavior and analyzer
notes. Installed packages and matching sources control consumer-specific claims.

Built-in assertion API selection must preserve the intended equality, identity,
ordering and exception contract. [Assertion guidance](references/assertions.md)
covers API resolution and reusable domain assertions; the separately installable
`mstest-assertions` skill provides detailed built-in corrections when that is the
requested task. Neither skill requires the other to complete its own workflow.

Do not copy another framework's fixture or parallelism rules. Required observation
and cleanup failures remain failures. Preserve absent results, cancellation and
resource ownership rather than weakening checks until a run succeeds.

For an isolated API inventory, from this skill directory:

```sh
python3 scripts/inspect_mstest.py --project /path/to/Tests.csproj
```

The inspector does not upgrade or edit the consumer. For runner, host-disposal
or published AOT proof, use [the capability verifier](references/executable-evidence.md)
with explicit versions. A managed pass does not establish Native AOT support.
For catalog maintenance only, read
[public API maintenance](references/public-api-maintenance.md).
