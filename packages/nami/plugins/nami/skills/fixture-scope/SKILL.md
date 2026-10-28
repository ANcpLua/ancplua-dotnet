---
name: fixture-scope
description: "Choose and implement explicit test, class or assembly ownership for MSTest fixtures. Use for shared input files, expensive setup, failure cleanup, parallel consumers and removing repeated fixture lifecycle wiring."
---

# Fixture scope

1. Inspect the existing fixture owner, MSTest version and runner. Reuse that
   owner before adding a helper. Choose fresh mutable state per test, class scope
   for intentional sharing, or assembly scope for a resource used across classes.
2. Declare the scope and consume a non-nullable fixture. Central infrastructure
   owns creation, partially failed setup, disposal and invalid lifecycle detection.
   Consumers do not dispose class- or assembly-owned resources. Do not repeat
   `null!`, null checks or lifecycle callbacks across tests to satisfy the compiler.
3. Verify the chosen scope's isolation, sharing, setup failure and cleanup through
   the normal test entrypoint. The [verification tests](examples/FixtureLifecycleTests.cs)
   cover shared class state, per-invocation isolation, distinct classes and cleanup.

The declaration in the [working example](examples/Example.cs) makes class ownership
explicit:

```csharp
[UsesFixture(FixtureScope.Class)]
public sealed class InputTests : FixtureTests<InputFixture>
```

These are example helpers built on public MSTest extension points, not built-in
MSTest APIs. Inherited hooks live in [FixtureTests.cs](examples/FixtureTests.cs);
creation and deletion live in [InputFixture.cs](examples/InputFixture.cs).

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
