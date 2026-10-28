# Object graphs: what AreEquivalent really proves

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

Read [EqualityExamples.cs](../examples/EqualityExamples.cs) for executable positive
and negative cases, including value-equal distinct instances, operator equality
and the record/array trap.
The expected failures in those examples verify assertion semantics; ordinary
application tests should directly assert the production result.
