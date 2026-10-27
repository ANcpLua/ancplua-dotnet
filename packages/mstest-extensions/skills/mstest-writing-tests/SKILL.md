---
name: mstest-writing-tests
description: "Write, correct or explain native MSTest tests, built-in assertions, attributes and lifecycle. Create test projects or repair solution/CI inclusion. Reusable extension design belongs to mstest-extensions; execution-only requests and report-only reviews have focused skills."
---

# Write native MSTest tests

The [opinionated native stack](../mstest-extensions/references/native-stack.md)
is MSTest.Sdk 4.5.1 / MTP 2.5.1 with `AllMicrosoft` and Microsoft.CodeCoverage.

Use MSTest 4.5.1 / Microsoft.Testing.Platform 2.5.1 as the checked baseline.
For an existing consumer, its resolved packages and normal runner determine the
available APIs. [Version resolution](../mstest-extensions/references/version-resolution.md)
provides lookup when those inputs differ; conceptual questions need no restore.

Identify whether the behavior is pure logic, interacting components, a whole
application or a packaged consumer. The boundary determines the fixture and
observable outcome. [Scope guidance](../mstest-extensions/references/test-scopes.md)
also covers shared helpers, native base/derived lifecycle and child runners.
Unit-generation advice to isolate external dependencies applies to units.
Integration and end-to-end cases retain the real boundary they claim to verify.
Before adding a new case/project, establish its normal repository discovery and
CI entrypoint; a standalone green run does not prove that entrypoint finds it.
For project creation or missing solution/CI inclusion, read
[project discovery](../mstest-extensions/references/test-projects.md).

For a built-in API or configuration question, read only the relevant reference
and explain the native behavior; advice alone needs no edits or test run.
Execution-only requests belong to [mstest-run-tests](../mstest-run-tests/SKILL.md).

Use `[TestMethod]` with native `[DataRow]` for independently selectable constant
cases; typed `[DynamicData]` fits computed data. Framework expansion preserves
row identity and lifecycle. Immutable descriptions can be shared; mutable state
belongs to each invocation. Enum selectors stay typed; shared contract strings
use published or owned constants. No scenario needs a name copied from another
repository.

Prefer the resolved version's specific `Assert` operation, expected/actual order
and typed result over generic Boolean checks or hard casts. The oracle describes
the intended behavior independently of its implementation. Required parents,
results and events are asserted before their properties; conditional checks can
otherwise hide missing evidence. Async assertions and operations are awaited.

Match lifecycle signatures to the work: synchronous construction/setup and
`IDisposable` remain appropriate for synchronous resources; use native async
initialization and `IAsyncDisposable` for awaited acquisition and teardown.
These styles can coexist. Native `TestContext` supplies cancellation. Shared
startup has fixture ownership while individual tests can cancel their waits.
Cleanup releases and joins original
work before disposal, including after failed assertions. Sequential dependencies
remain sequential even in async code; concurrency applies to independent work.

Use the focused test entrypoint for compilation and execution, retaining native
failures and diagnostics. A real child runner is useful when runner outcomes or
process isolation are the contract; it is not a substitute for an ordinary unit
test. [Assertions](../mstest-extensions/references/assertions.md),
[data](../mstest-extensions/references/data.md) and
[lifecycle](../mstest-extensions/references/lifecycle.md) contain the relevant API details.
Read lifecycle's process-global state guidance before changing environment
variables, console streams or parallel resource locks; analyzer silence alone
does not establish isolation.
For conversion, capture or privacy changes, use the relevant
[failure-prevention lesson](../mstest-extensions/references/failure-prevention.md)
to choose a distinguishing case rather than copying an entire scenario suite.
