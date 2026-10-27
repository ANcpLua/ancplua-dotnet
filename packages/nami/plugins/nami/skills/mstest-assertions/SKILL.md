---
name: mstest-assertions
description: Select the most precise MSTest 4.5.1 assertion for each test contract. Use for assertion authoring, reviews, replacements, equality and collection semantics, or NativeAOT constraints; never weaken the contract or recommend legacy fallbacks.
---

# MSTest 4.5.1: the best assertion for the contract

Verified against the published MSTest.TestFramework **4.5.1** (`lib/net9.0`,
consumed from .NET 11), its release sources, and the current TestFX sources.
This skill targets the **4.5.1 API**. The highest priority is the most specific
assertion that proves the intended contract and produces useful failure evidence.
Improve an inferior assertion directly; leave an already suitable assertion alone.
Do not recommend weaker checks, legacy assertions, or historical fallbacks.
Check the resolved package/asset when compiling; if a different
version is installed, report that mismatch rather than silently downgrading the
recommendation. The `main` branch is research material, not the package contract.
See [version evidence](references/version-evidence.md)
when comparing releases, checking AOT annotations, or updating this skill.

The skill, examples and verifier are self-contained. They do not depend on an
application repository, global skill installation, or other skills in the plugin.

## Selection priority

Select the dedicated 4.5.1 assertion for the behavior the test promises. The
contract comes from the requested behavior and public API, not merely from what
the current implementation happens to do. Preserve required aspects without
inventing additional ones. More restrictive is not automatically more correct.
Prefer dedicated assertions over equivalent hand-written Boolean expressions.
Do not add redundant assertions merely to use more methods.

For example, preserving an assignee usually means preserving its value, not its
object identity. Use `AreEqual` for that contract. Use `AreSame` when reusing the
exact instance is itself promised, such as preserving a failure object through
`Map`/`Bind`. Do not turn incidental reference reuse into a new API requirement.

| Required contract | Preferred assertion |
| --- | --- |
| Value equality | `AreEqual(expected, actual)`, with the intended comparer/tolerance where needed |
| Same reference instance | `AreSame(expected, actual)` |
| Null / non-null result | `IsNull` / `IsNotNull`; add state/content checks when those are the contract |
| Assignable to a required type, then access typed members | `var typed = IsInstanceOfType<T>(actual)` |
| Exactly N items | `HasCount(n, collection)` |
| Empty / non-empty | `IsEmpty` / `IsNotEmpty` |
| Exactly one total item / one matching item | `ContainsSingle(collection)` / `ContainsSingle(predicate, collection)`; use the returned item |
| Ordered element equality | `AreSequenceEqual(expected, actual)` |
| Unordered equality including duplicate frequencies | `AreSequenceEqual(expected, actual, SequenceOrder.InAnyOrder)` |
| Element membership / subset | `Contains` / `DoesNotContain` / `ContainsAll`, only for membership/subset contracts |
| Unique elements / all non-null / all of a type | `AreAllDistinct` / `AreAllNotNull` / `AreAllOfType<T>` |
| String prefix / suffix / substring / regex | `StartsWith` / `EndsWith` / `Contains` / `MatchesRegex`, with intended comparison options |
| Numeric lower/upper bound, range, positivity | `IsGreaterThan`, `IsLessThan`, `IsInRange`, `IsPositive`; expected bounds first |
| Exception type, allowing derived types | `Throws<T>` / `ThrowsAsync<T>` |
| Exact exception type | `ThrowsExactly<T>` / `ThrowsExactlyAsync<T>`; inspect the returned exception when its properties matter |
| Recursive public-member graph contract | `AreEquivalent`, explicitly choosing strictness and accounting for its equality shortcuts |
| Actual Boolean or overloaded-operator contract | `IsTrue` / `IsFalse` |

## Make the improvement and finish

Read the affected test and enough implementation or API documentation to understand
its contract, then make the justified change. Do not require a repository-wide
audit, benchmark, extra agent, or new approval for an ordinary assertion edit.
Use `ref` or the pinned sources when an API or overload is genuinely uncertain;
do not repeat metadata research already established for the same resolved version.

Reduce repeated arrangement when a small fixture or helper makes ownership and
inputs clearer. Keep meaningful differences visible. Separate scenarios when a
failure would otherwise hide independent outcomes; do not manufacture extra cases
or abstractions just to increase the test count. Share expensive setup only when
its mutable state and cleanup remain isolated. Per-test processes are a tradeoff,
not a universal requirement.

Run the affected checks, fix demonstrated failures, and stop once the change is
validated. Report what changed and what passed. Do not keep broadening verification
or turn a focused improvement into a speculative test redesign.

Do not recommend `CollectionAssert`, `StringAssert`, or `ThrowsException` as
4.5.1 alternatives. Do not replace content checks with count, a precise type
check with a hard cast, or typed exception assertions with manual try/catch.
`IsInstanceOfType<T>` allows derived types; if the contract requires the exact
runtime type, assert equality with `typeof(T)` instead. A genuine presence-only
contract is correctly tested by `IsNull`/`IsNotNull`; do not invent extra requirements.

## Equality and collection semantics

Choose the assertion whose semantics match the test contract. Expected first,
actual second. Preserve the distinction between identity, equality, ordering,
cardinality, multiplicity, and the particular members the test promises to verify.

```csharp
Assert.AreEqual(expected, actual);
Assert.AreSame(expectedInstance, actualInstance);
Assert.HasCount(expectedCount, collection);
Assert.AreSequenceEqual(expectedItems, actualItems);
Assert.AreSequenceEqual(expectedItems, actualItems, SequenceOrder.InAnyOrder);
Assert.IsEmpty(collection);
Assert.IsNotEmpty(collection);
var only = Assert.ContainsSingle(collection);
var matching = Assert.ContainsSingle(item => item.IsPending, collection);
```

- Generic `AreEqual<T>` without an explicit comparer uses
  `EqualityComparer<T>.Default`. It is not an automatic recursive graph comparison.
  Specialized overloads, for example strings and floating-point tolerance, have
  their own contracts; inspect the overload actually selected.
- A C# union is a wrapper, not an instance of its contained case. To assert the
  payload type, use `Assert.IsInstanceOfType<Failure>(result.Value)` and inspect
  the returned value. Applying that assertion to `result` boxes the wrapper and
  tests the wrong object. A deliberate `result is Failure` pattern also inspects
  the case; do not mechanically rewrite it as a type assertion on the wrapper.
- Generic `AreSequenceEqual<T>` without an explicit comparer uses default element
  equality. Nested arrays/collections do not automatically become deep comparisons.
  `SequenceOrder.InAnyOrder` ignores order but retains duplicate frequencies.
  A supplied `IEqualityComparer<T>` deliberately changes element equality.
  Prefer supported Span/Memory overloads over conversions at the call site;
  this is not a blanket allocation-free guarantee. In 4.5.1 the graph-comparison
  Span overloads themselves use `ToArray()` internally.
- `HasCount` proves only count; `IsEmpty`/`IsNotEmpty` prove emptiness/non-emptiness.
  These collection assertions are not a replacement for an explicit null contract.
- `ContainsSingle(collection)` proves exactly one total item and returns it.
  `ContainsSingle(predicate, collection)` proves exactly one matching item; other
  nonmatching items may exist. Keep the predicate when replacing `Single(predicate)`.
- `ImmutableArray<T>.Equals` and `==` compare the underlying array identity.
  For element equality use `AreSequenceEqual` with the intended order/comparer.
- Do not blindly replace `Assert.IsTrue(a == b)` with `AreEqual(a, b)`: an
  overloaded operator can intentionally differ from `Equals`/`IEquatable<T>`.
  Likewise, preserve overload-specific null semantics and reference identity.
- Replace `CollectionAssert.AreEquivalent` with the supported
  `AreSequenceEqual(..., SequenceOrder.InAnyOrder)` only when that is the same
  intended element/comparer contract. It is not the new `Assert.AreEquivalent`.

## Object graphs: what AreEquivalent really proves

`AreEquivalent(expected, actual, strict: true)` recursively compares eligible
public instance fields and readable, non-indexed public instance properties.
Private state, static members, and indexers are outside that contract.

Ordinary enumerables are order-sensitive. Dictionaries are compared by keys and
recursive values, using their lookup semantics, rather than enumeration order.
Without `strict: true`, extra actual members and dictionary keys are allowed.
Strict mode rejects those extras, but does not itself require identical runtime
types or add comparisons of private state. Enumerable length must match even in
non-strict mode; non-strict is not an arbitrary collection-subset comparison.

**An eligible `IEquatable<T>` on the declared/static type stops recursion.**
Plain `object.Equals` overrides alone do not trigger that shortcut. Records
normally implement `IEquatable<T>`: a record containing an array can therefore
fail `AreEquivalent` despite equal array elements. Conversely, a type whose
equality checks only an ID can pass despite different other members.
`strict: true` does not disable this shortcut. Generic type inference, member
declarations and element types matter; do not claim unconditional deep equality.
`AreEquivalent<object>` may have different behavior, and remains reflection-based.

If every field of a known contract must be verified, use explicit typed member
assertions with sequence assertions for collection members. Add new member
checks when that contract grows; do not replace a full-contract check with only
an ID, count, `IsNotNull`, or a successful round trip.

Read [EqualityExamples.cs](examples/EqualityExamples.cs) for executable positive
and negative cases, including value-equal distinct instances, operator equality
and the record/array trap.
The expected failures in those examples verify assertion semantics; ordinary
application tests should directly assert the production result.

## NativeAOT and trimming

In the resolved 4.5.1 modern-.NET assembly, all ten overloads each of
`AreEquivalent` and `AreNotEquivalent` carry both `RequiresUnreferencedCode`
and `RequiresDynamicCode`. Their runtime-type reflection and generic type
construction are real constraints. Earlier source versions lacking these
annotations are not proof of safety.

The expression-tree assertion `Assert.That(() => condition)` is a different API
from the singleton property used by `Assert.That.MyCustomAssertion(...)`.
The expression API has `RequiresDynamicCode` on the modern-.NET 4.5.1 asset.
The singleton property does not impose that requirement; assess each custom
extension's implementation. Do not confuse it with NUnit's `Assert.That`.

NativeAOT restrictions apply when the test host actually targets that mode;
do not use a hypothetical AOT requirement to discard the best managed assertion.
For a NativeAOT test host, use statically typed assertions that retain the full
intended test semantics. See [TypedAssertions.cs](examples/TypedAssertions.cs).
If deep reflection is actually needed, isolate it in a managed test host; that
host can still test a separately published NativeAOT application.

`IsAotCompatible=true` enables compatibility analysis; it does not certify every
API, dependency, or execution path. Do not blanket-suppress IL2026/IL3050 or swap
to weaker assertions just to make diagnostics disappear. A clean analyzer build
is different evidence from an actual NativeAOT publish and run.

## Verify changes and new claims

Use `ref help` to select supported commands, then inspect the resolved asset:

```sh
ref packages path/to/obj/project.assets.json --json
ref assembly path/to/resolved/MSTest.TestFramework.dll --type 'Microsoft.VisualStudio.TestTools.UnitTesting.Assert*' --json
ref reflection path/to/resolved/MSTest.TestFramework.dll --json
ref aot inspect path/to/resolved/MSTest.TestFramework.dll --json
```

Member presence, annotations, static IL calls, and observed runtime behavior are
different evidence. `ref reflection` reports catalogued call sites, not executed
paths; `ref aot inspect` can correctly say `not-established` for a trimmable DLL.
Read the matching release source for implementation details; compile/run the
selected overload and a counterexample when equality semantics are uncertain.

For this skill's pinned examples on .NET 11 with Python 3 available:

```sh
python3 scripts/verify_examples.py
```

The script runs the example tests, parses their TRX report, and verifies that
typed assertions pass AOT analysis while the reflection/expression probe fails
with IL2026 and IL3050. All generated projects live in temporary directories;
it does not edit the consuming solution, install SDKs, or publish a native app.

When evaluating or revising the skill itself, use the focused scenarios in
[evaluation.md](references/evaluation.md). These are agent-behavior checks, not
additional steps required for ordinary test edits.
