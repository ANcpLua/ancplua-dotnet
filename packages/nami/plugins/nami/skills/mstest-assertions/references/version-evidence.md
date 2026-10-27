# Version and source evidence

Checked 2026-10-27. Release baseline: `v4.5.1`, commit
`0bf77e3aedbf86f1fa16220bc951d3b52ba56763`. Research snapshot of `main`:
`2a0d80af834cf7c861dd0e90e2d84c1e5c7adbef`.

## Corrections to the supplied “4.2” prompt

The prompt combines several generations of the API. Its central equality advice
is useful, but it must not be labelled an API baseline for 4.2.

| API or behavior | Direct source comparison |
| --- | --- |
| AreEqual, HasCount, IsEmpty, IsNotEmpty, expression That | Already present in checked 4.2.3; this is not a claim about their first-ever release |
| AreSequenceEqual, SequenceOrder, ContainsSingle, deep AreEquivalent | Present in 4.3.0; absent from the checked 4.2.3 assertion surface |
| AreNotEquivalent and extra Span/Memory graph/sequence overloads | Present in 4.4.0, not in the checked 4.3.0 surface |
| RUC/RDC on every AreEquivalent/AreNotEquivalent overload | Present in 4.5.1; absent in checked 4.4.1 sources |
| RDC on expression That | Present in checked 4.3.0, 4.4.1 and 4.5.1; absent in checked 4.2.3 source |

The relevant AreEquivalent, AreNotEquivalent, AreSequenceEqual, ContainsSingle,
HasCount, IsEmpty and IsNotEmpty source files were identical between v4.5.1 and
the checked main snapshot. Assert.That implementation differed; do not transplant
main-only implementation details into claims about the installed 4.5.1 package.

The important semantic refinements are:

- Generic default equality can be replaced by explicit comparer overloads.
- The IEquatable shortcut depends on the **declared type**, not just the runtime
  object having some IEquatable implementation. This matters especially for records.
- `strict` neither disables equality shortcuts nor includes private state, and
  it does not require runtime-type identity.
- Dictionary comparison is key-based; ordinary enumerable comparison is ordered.
- Predicate `ContainsSingle` counts matches, not total collection size, and returns
  the match. Dropping its predicate is a contract change.
- Actual NativeAOT test hosts and managed tests of native applications have
  different constraints. Old missing annotations are not evidence of AOT support.

## Primary sources

- [4.5.1 release](https://github.com/microsoft/testfx/releases/tag/v4.5.1)
- [4.5.1 assertion directory](https://github.com/microsoft/testfx/tree/v4.5.1/src/TestFramework/TestFramework/Assertions)
- [AreEqual implementation](https://github.com/microsoft/testfx/blob/v4.5.1/src/TestFramework/TestFramework/Assertions/Assert.AreEqual.cs)
- [Sequence equality implementation](https://github.com/microsoft/testfx/blob/v4.5.1/src/TestFramework/TestFramework/Assertions/Assert.SequenceEqual.Implementation.cs)
- [AreEquivalent contract and annotations](https://github.com/microsoft/testfx/blob/v4.5.1/src/TestFramework/TestFramework/Assertions/Assert.AreEquivalent.cs)
- [Equivalence comparer: static type and IEquatable](https://github.com/microsoft/testfx/blob/v4.5.1/src/TestFramework/TestFramework/Assertions/Assert.AreEquivalent.Comparer.cs)
- [ContainsSingle overloads](https://github.com/microsoft/testfx/blob/v4.5.1/src/TestFramework/TestFramework/Assertions/Assert.ContainsSingle.cs)
- [Expression That](https://github.com/microsoft/testfx/blob/v4.5.1/src/TestFramework/TestFramework/Assertions/Assert.That.cs)
- [That singleton property](https://github.com/microsoft/testfx/blob/v4.5.1/src/TestFramework/TestFramework/Assertions/Assert.cs)
- [4.2.3 assertion directory](https://github.com/microsoft/testfx/tree/v4.2.3/src/TestFramework/TestFramework/Assertions)
- [4.3.0 assertion directory](https://github.com/microsoft/testfx/tree/v4.3.0/src/TestFramework/TestFramework/Assertions)
- [4.4.0 assertion directory](https://github.com/microsoft/testfx/tree/v4.4.0/src/TestFramework/TestFramework/Assertions)
- [Checked main snapshot](https://github.com/microsoft/testfx/tree/2a0d80af834cf7c861dd0e90e2d84c1e5c7adbef/src/TestFramework/TestFramework/Assertions)

## Installed-binary evidence

Resolved asset: `MSTest.TestFramework/4.5.1/lib/net9.0/MSTest.TestFramework.dll`.
Identity `MSTest.TestFramework, Version=4.5.1.0`, MVID
`4fd9e389-1b24-4781-8d85-0dd742721dfb`.

`ref assembly` confirms the API names on the selected asset. `ref aot inspect`
reports 10 RUC and 10 RDC annotations for AreEquivalent, the same counts for
AreNotEquivalent, and one RDC annotation for AssertExtensions.That. Its overall
assessment is `not-established` even though the assembly declares itself trimmable.

`ref reflection` finds MakeGenericType in the equivalence helpers and expression
compilation in the That implementation. Across the entire DLL its catalogue
reports 8 expression-compilation, 19 reflection-discovery and 17 reflection-invocation
call sites. Those are static references, not measurements or proof every assertion
executes reflection.

`scripts/verify_examples.py` supplies runtime counterexamples and positive/negative
AOT-analysis builds. Run it again when changing examples or upgrading the pin.

Validation on 2026-10-27 with .NET SDK 11.0.100-rc.3.26522.148:
The original 16 managed examples passed, none failed or skipped. The typed sample, including
the `Assert.That.HasReceipt` extension-point call, passed AOT analysis. The
negative probe produced exactly IL2026 and IL3050 on each structural assertion,
and IL3050 on the expression assertion; no unrelated compiler error was accepted.
This validation did not publish or execute a NativeAOT binary.

The later contract-selection revision adds
`PreservingAssigneeValueDoesNotRequireTheSameInstance`: equal reconstructed values
must satisfy a value-preservation contract, while a reference-identity assertion
must reject them. The verifier discovers all example methods from the current
source; run it for the current count rather than treating the historical count as
a gate. Agent-behavior evaluation is described separately in [evaluation.md](evaluation.md).
