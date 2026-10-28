# NativeAOT and trimming

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
intended test semantics. See [TypedAssertions.cs](../examples/TypedAssertions.cs).
If deep reflection is actually needed, isolate it in a managed test host; that
host can still test a separately published NativeAOT application.

`IsAotCompatible=true` enables compatibility analysis; it does not certify every
API, dependency, or execution path. Do not blanket-suppress IL2026/IL3050 or swap
to weaker assertions just to make diagnostics disappear. A clean analyzer build
is different evidence from an actual NativeAOT publish and run.
