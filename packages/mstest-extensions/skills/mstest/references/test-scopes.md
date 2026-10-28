# Test scopes, native composition and build metadata

Choose the observable boundary before selecting a fixture. A plugin packages
skills and resources; a project is a compiled code boundary. Four test projects
do not require four skills that compete for the same MSTest request. This
plugin's skills separate extension design, test writing and review goals; all
use the same native scope and API semantics described here.

## Different projects, different evidence

| Scope | Typical dependencies and evidence |
| --- | --- |
| Unit | In-memory assertions, filtering, policy decisions and evidence transformations. Explicit inputs and observable outputs; no automatic server/process startup. |
| Integration | Concrete receivers/exporters, transport, isolation, flush and disposal. Native fixtures own the participating components and their completion. |
| End-to-end | The assembled applications and required external components. A candidate-package claim exercises the actual packed package and its dependencies. |
| Shared test helpers | Reusable immutable data, assertions or lifecycle support. A helper library need not itself be a runnable test application. |

Names such as `*.Tests` alone do not establish one of these scopes. Inspect the
project SDK, references and actual cases. Template defaults are not evidence of
the intended framework version: one project can pin an older MSTest SDK even
when another project or a conversation selected a newer one. Resolve each
affected project through [version resolution](version-resolution.md).

Ordinary source tests can reference the implementation project. A package
consumer uses its package identity and a deliberate restore source. Candidate
packing precedes candidate-consumer restore; the consumer cannot silently fall
back to a source reference or a cached public release. Scope selection does not
change MSTest's row discovery, lifecycle or outcome semantics.

## Class composition and inherited lifecycle

For class-wide execution behavior, wrap the method attribute supplied to
`TestClassAttribute.GetTestMethodAttribute`. Await and return that original
attribute's `ExecuteAsync` results. For a method-level specialization, the
corresponding base executor preserves native invocation handling. Multiple
passive policy markers can share one executor and one invocation.

Base/derived setup is a framework lifecycle contract, not another executor to
recreate. Keep synchronous construction, async initialization, cleanup and
disposal at their native scopes. Resolve inherited class/assembly fixture rules
and base/derived ordering from [lifecycle](lifecycle.md); avoid manually calling
base hooks or constructing test classes for a second invocation.

MSTest owns data expansion. Independent scenarios use native rows; mutable
resources belong to executions. Async work can still be sequential. A shared
publication's lifetime token and an individual row's cancellable wait have
different owners. Cleanup observes and joins original operations before their
dependencies are disposed.

## Reflection is not a replacement for supported APIs

Use native context, original method attributes and discovery metadata rather
than private adapter fields, method scanning or `MethodInfo.Invoke`. Do not add
reflection to discover generated entrypoints or reconstruct a runner.
`MethodInfo`/`ParameterInfo` parameters required by public data-provider
interfaces are metadata contracts; their presence is not a reason to invoke a
test manually or to replace those interfaces.

MSBuild already knows `Configuration`, target framework, RID, output paths and
referenced project outputs. Build-time content deployment or evaluated target
metadata can make a child fixture available without runtime reflection over
assembly configuration. Source navigation comes from real runner discovery of
the original attributes, not a wrapper copying caller-location fields.

API research downloads are data. Keeping downloaded framework `.cs` under an
SDK project's default compile glob accidentally compiles foreign implementation
code. A separate research directory or non-source suffix preserves the evidence
without changing the project's compilation. Public API listings can contain
obsolete members; check annotations and the matching implementation before use.

## Child runners and AOT have specific purposes

A child runner is useful for native failure/inconclusive reporting, discovery,
or required process isolation. Pure unit assertions do not need a new runner.
Use the installed SDK's reporting extensions and structured results before
inventing an `IDataConsumer`, custom JSON reporter or builder hook. An extension
hook has a version-specific signature; an interface that resembles its concrete
builder type does not establish compatibility.

Managed discovery, generated discovery, generated invocation and a published
Native AOT executable are different evidence. A native claim requires executing
the actual artifact with the supported test shape. In the inspected stack,
assembly fixture-provider discovery and optional hosting have AOT restrictions;
direct fixture declarations in the consuming assembly may be the applicable
native route. Preserve supported framework generation rather than removing a
generated symbol merely because its name contains `Reflection`.

See [execution](execution.md) for result preservation and original discovery,
[runner and generation](runner-and-generation.md) for host/SDK boundaries, and
[telemetry contracts](telemetry-contracts.md) for capture-to-read evidence.
