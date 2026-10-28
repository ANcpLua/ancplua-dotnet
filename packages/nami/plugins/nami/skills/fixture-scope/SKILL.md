---
name: fixture-scope
description: "Choose and implement explicit test, class or assembly ownership for MSTest fixtures. Use for shared input files, expensive setup, failure cleanup, parallel consumers and removing repeated fixture lifecycle wiring."
---

# Fixture scope

Inspect the repository's existing fixture owner, MSTest version and test runner.
Reuse that owner before adding a helper. Choose scope from the behavior being
tested: fresh mutable state per test; one resource per class when tests intentionally
share it; assembly ownership only for a resource actually used across classes.
Consumers do not dispose class- or assembly-owned resources.

The test author should declare the scope and consume a non-nullable fixture.
Central infrastructure owns creation, partially failed setup, disposal and invalid
lifecycle detection. Do not repeat `null!`, null checks, or lifecycle callbacks
across consumer tests just to satisfy the compiler.

The [working example](examples/Example.cs) uses public MSTest extension points:
`[UsesFixture(FixtureScope.Class)]` and `FixtureTests<InputFixture>`. Its inherited
hooks live in [FixtureTests.cs](examples/FixtureTests.cs). The factory and deletion
live in [InputFixture.cs](examples/InputFixture.cs). These are example helpers,
not built-in MSTest APIs. The [verification tests](examples/FixtureLifecycleTests.cs)
exercise shared class state, per-invocation isolation, distinct classes and cleanup.

Read [MSTest lifecycle](references/mstest-lifecycle.md) for API signatures,
cleanup ordering, host injection restrictions and temporary-file behavior.
Read [ownership boundaries](references/ownership.md) before changing retention.
For assertion-specific work, use `mstest-extensions:mstest-assertions`
([source](https://github.com/ANcpLua/ancplua-dotnet/blob/main/packages/mstest-extensions/skills/mstest-assertions/SKILL.md)) to select
the most precise 4.5.1 assertion for the intended contract, and the
`mstest-extensions:mstest` ([source](https://github.com/ANcpLua/ancplua-dotnet/blob/main/packages/mstest-extensions/skills/mstest/SKILL.md)) for general APIs.

Do not add a daemon, scheduler, unconditional archive or new retention policy.
Respect the repository's existing policy. Scope disposal works during normal
execution and exception unwinding; process termination and reboot need a separate
explicit repository contract and cannot be guaranteed by a C# destructor.

For shared class fixtures, creation cancellation belongs to the class owner.
A test token only cancels that test's `WaitAsync`, not the shared creation.
The working example covers waiter cancellation, cleanup during initialization,
and exactly-once disposal. Do not replace these ownership guarantees with a
lambda allocation optimization.
