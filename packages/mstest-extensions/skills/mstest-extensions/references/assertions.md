# Assertions

Use built-in `Assert` operations when they already express the expectation. A
domain assertion is a C# extension method on the `Assert` instance type, invoked
through the singleton `Assert.That`:

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;

public static class TemperatureAssertions
{
    public static void BeWithin(
        this Assert _, double actual, double expected, double tolerance)
    {
        if (!double.IsFinite(tolerance) || tolerance < 0)
            throw new ArgumentOutOfRangeException(nameof(tolerance));

        if (!double.IsFinite(actual) || !double.IsFinite(expected)
            || Math.Abs(actual - expected) > tolerance)
        {
            Assert.Fail(FormattableString.Invariant(
                $"Expected {expected} +/- {tolerance}; actual {actual}."));
        }
    }
}

// Assert.That.BeWithin(actual: 20.1, expected: 20.0, tolerance: 0.2);
```

Specify the contract before implementing it: nulls, order, tolerance boundaries,
NaN/infinity, enumeration, and units can change what an assertion means. Invalid
assertion configuration can be an argument error; a rejected subject must produce
an MSTest assertion failure. Use `Assert.Fail` or `AssertFailedException`, not a
Boolean return that callers can accidentally ignore.

Synchronous assertions execute immediately. Async assertions must return a
`Task` that the test awaits; do not introduce `async void` or block async work.
There is no requirement for generated assertions or an awaitable fluent DSL.

Test the extension itself with values on both sides of its boundary. Check a
rejection with `Assert.ThrowsExactly<AssertFailedException>` and inspect useful
expected/actual information. An assertion test that only accepts good values
does not prove that it can fail. For async exceptions, await `ThrowsAsync` or
`ThrowsExactlyAsync`; choose whether derived exception types are acceptable.

Keep ordered equality and unordered equivalence separate. Use the installed
version's sequence/span assertions when appropriate; an assertion package
addition needs a concrete missing capability.

Check the consumer's enabled MSTest analyzers and resolved assertion APIs before
writing tests. Prefer the installed version's `Assert` string and sequence
operations over legacy `StringAssert` or `CollectionAssert` equivalents when
recommended by those analyzers. Establish required non-null values with an
assertion before using them, and pass the native test cancellation token to
asynchronous operations that support it. Keep compiler and analyzer diagnostics
visible and correct their causes through the focused test entrypoint.

Use assertions that preserve useful failure diagnostics: expected value first,
observed value second for equality; confirm the installed signature for bounds
and comparison APIs rather than copying the expression's operand order. When
available, use the value returned by `Assert.IsInstanceOfType<T>` instead of a
hard cast followed by a check. For an array-valued contract, establish the actual
array type before comparing its elements; a joined string can hide a wrong wire
representation. Check exact identities and uniqueness when a count alone would
accept the wrong collection. Preserve order only when it is part of the contract.

Do not gate a required assertion behind an optional precondition. Assert that
the required parent, result or event exists first, then check its properties.
An optional observation needs an explicit scenario contract explaining its
absence. Follow helper assertions and child-process reports before concluding
that a method has no checks. See [test quality and evidence](test-quality.md) for
independent oracles and meaningful failure probes.

Sources: [assertion documentation](https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-mstest-writing-tests-assertions)
and `Assert.That` in the [resolved framework package](sources.md).
