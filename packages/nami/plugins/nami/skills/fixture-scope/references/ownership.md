# Ownership boundaries

| Intended lifetime | Owner |
| --- | --- |
| One operation | Local `using` / `await using` |
| One test invocation or data row | Existing test fixture owner / inherited per-test hooks |
| All selected tests of one class | Class fixture owner and class cleanup |
| Multiple test classes in one assembly | Assembly fixture owner and assembly cleanup |

A class fixture remains alive between its tests. Do not implement class lifetime
by counting currently active test methods: that count can reach zero between two
methods even though the class is not finished. Let the test framework end the class.

Share immutable inputs freely within their explicit owner. Shared mutable state
needs a deliberate sequence or synchronization; accidentally depending on test
order is not a fixture contract. Failed creation must release resources already
acquired. Failed tests must not suppress cleanup.

The example includes a small generic base to centralize public MSTest lifecycle
hooks. It does not require experimental host injection or access to internal
`ITestClassInstanceFactory` / `ITestClassInstanceLease` interfaces. Verify actual
visibility in the selected package: XML documentation can describe internal types.

The example targets .NET 11 and MSTest.Sdk 4.5.1. Apply the pattern to a consuming
project's installed API level; do not retarget a project to use this example.

## Cancellation follows ownership

Shared fixture creation uses the class owner's lifetime token, never a token
borrowed from the first test instance. Each test awaits the shared creation with
its own cancellation token using `WaitAsync`. Cancelling one waiter must not
cancel or poison the shared initialization. Class cleanup cancels pending
creation, awaits it, and disposes a successfully created fixture exactly once.
The published Lazy owns the class state; losing ConcurrentDictionary factories
must not allocate resources that need cleanup.

A factory that acquires resources before failing remains responsible for cleaning
up that partial initialization. The fixture owner cannot dispose an instance
that was never returned.
