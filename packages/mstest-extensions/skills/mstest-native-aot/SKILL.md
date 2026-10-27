---
name: mstest-native-aot
description: "Publish and verify MSTest consumers under Native AOT, trimming or generated discovery. Use for compatibility claims, generator failures and reflection fallbacks; ordinary managed test edits belong to mstest-writing-tests."
---

# Verify native test execution

The [opinionated native stack](../mstest-extensions/references/native-stack.md)
is MSTest.Sdk 4.5.1 / MTP 2.5.1 with `AllMicrosoft` and Microsoft.CodeCoverage.

Establish the consumer's actual SDK, target framework, runtime identifier,
MSTest packages and runner. The checked baseline is MSTest 4.5.1 with MTP 2.5.1;
these are different versioned components. Preserve the consumer's pins unless
migration is requested. [Version resolution](../mstest-extensions/references/version-resolution.md)
provides the package and MSBuild evidence.

Separate generated discovery, generated direct invocation, managed reflection
fallback and execution of a Native AOT binary. Enabling
`EnableMSTestSourceGeneration` and passing a managed run proves neither of the
last two. ReadyToRun retains a CLR execution model and is not Native AOT.

Inspect generated sources and relevant `AOTSG`, trimming and AOT diagnostics.
Prefer supported framework attributes and generated invocation over scanning
assemblies or invoking private members. Public provider metadata parameters are
not themselves a reflection workaround. Use evaluated MSBuild properties such
as `TargetPath` for build identity rather than reflecting assembly configuration.
Read [runner and generation](../mstest-extensions/references/runner-and-generation.md)
for the resolved feature's limits.

Inheritance, custom execution attributes, dynamic data, assembly fixture
providers and optional hosting need evidence for their particular shape.
A passing plain test does not establish support for a different extension.
Do not suppress diagnostics globally, replace real tests with easier shapes or
claim automatic fixture discovery survived when it did not.
In the inspected 4.5.1 family, experimental `AddMSTestTestClassInjection` uses
reflection and excludes source-generated/AOT test execution. A managed hosted
suite can still exercise a separately published Native AOT application; keep
those artifact claims distinct. See the
[hosting limits](../mstest-extensions/references/lifecycle.md#hosting-integration-when-available).

Publish for the intended RID and execute that published binary through its
supported entrypoint. Inspect case identities, outcomes and required negative
behavior; a compiler error or startup crash is not an expected assertion failure.
Record artifact identity, runtime mode and relevant dependency versions.
[The packaged verifier](../mstest-extensions/references/executable-evidence.md)
already checks defined managed/AOT shapes; reuse its unchanged evidence rather
than publishing unrelated consumers.

Application instrumentation is a separate compatibility boundary. SDK
`AddInstrumentation` is a provider registration API, not a CLR profiler.
Classic CLR profiler injection is not available to a Native AOT application;
source or SDK instrumentation still needs an artifact-level check. Modern unsafe
accessors do not stabilize private runtime payload shapes. Report the verified
shape and unresolved dependencies precisely.
