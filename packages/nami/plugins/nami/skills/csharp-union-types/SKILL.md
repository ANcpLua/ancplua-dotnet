---
name: csharp-union-types
description: "Design, review and implement the C# 15 `union` keyword and `closed` modifier in .NET 11 code, including custom unions marked with System.Runtime.CompilerServices.UnionAttribute (the framework type or the bundled source polyfill): exhaustive matching, default/null handling and System.Text.Json serialization with union classifiers. Not for union conventions built on attributes the compiler does not recognize. Do not upgrade earlier frameworks or replace working inheritance merely because unions exist."
---

# C# 15 unions for AI coding agents

Use unions for a finite set of alternatives whose types need not share inheritance. Use a `closed` class or record when existing alternatives share behavior or polymorphic serialization. Preserve open inheritance when callers must extend it.

## Agent execution

- Apply the latest user request and the consuming repository's instructions. Inspect existing edits before changing code; do not overwrite unrelated work or rewrite commit authorship.
- Read only the local reference sections needed for the task. Adapt the checked examples to the project's actual types, contracts and target framework.
- Make the smallest complete change. Verify changed behavior; do not rerun unchanged probes merely to repeat an explanation. Existing reports describe their recorded run, not later untested edits.
- Commit and push when authorized. Do not watch CI or wait for publication unless requested.
- Report the concrete improvement, relevant verification and delivery status briefly. Distinguish completed work from triggered CI or publication.

## Use the bundled knowledge

The skill is self-contained. For ordinary use, read only the needed local reference sections; do not fetch documentation, another repository or run all probes just to answer a covered question. The pinned compiler output and executed local examples supply the evidence. Run relevant checks when changing code or validating a version-specific claim.

## Establish the compiler and contract

1. Inspect the owning project, `global.json`, inherited build properties and installed SDK. Do not change framework or language version without an upgrade request.
2. On the verified SDK `11.0.100` (the .NET 11 release), C# 15 is the default language version for `net11.0`, so unions need no `LangVersion` setting; `15.0` also works. Earlier previews required `preview`; do not add it for unions, and leave an existing setting unless an upgrade is requested. C# 15 is supported only on .NET 11 and later; the bundled polyfills let older targets compile, which Microsoft does not support.
   Distinguish the SDK compiler, the active language version and any separately referenced `Microsoft.CodeAnalysis.CSharp` package. An older Roslyn package or IDE language service can lack `LanguageVersion.CSharp15` even when the SDK builds C# 15 successfully. The NuGet packages `Microsoft.CodeAnalysis.Common` and `Microsoft.CodeAnalysis.CSharp` 5.9.0, for example, have neither `LanguageVersion.CSharp15` nor `ITypeSymbol.UnionCaseTypes`, and mark their union and closed-type APIs experimental; 5.12.0 has all of them. Read [Roslyn API versions](references/union-reference.md#roslyn-api-versions) before writing an analyzer or generator. Use `#error version` temporarily to identify the compiler/language used by a build; inspect package versions separately for in-process compilation.
3. Identify the authoritative model and serializer. For TypeSpec or another generator, edit that source and regenerate. Never edit generated C# by hand. Separate wire and persistence models only for an explicit compatibility or storage requirement.
4. Before changing serialization, record the discriminator, null representation, numeric encoding and canonical ordering. Preserve persisted bytes and hashes unless a migration is intended.

## Implementation rules

- Switch on the union itself, not its object-valued `Value`. Prefer a **switch expression** covering every case and explicit `null => throw ...` when default values can arrive. A catch-all `_` or `var` masks future cases. An external JSON discriminator is an open input and still needs unknown-value rejection.
- Completeness diagnostics are warnings. Verify that `CS8509`, `CS8655` and `CS8846` fail the actual project build when completeness is required. A Roslyn test forcing warnings to errors does not establish production policy.
- Switch **statements** lack that completeness guarantee. Removing their default arm can silently omit work, including serialization.
- `default(U)` can contain null even when all cases are non-nullable. `U?` additionally has a nullable wrapper. Do not silently map an invalid default to a normal business state.
- Typed patterns match contents. Untyped property/positional patterns and `var` match the wrapper. `u is { }` is not a contents-presence check on a struct union; use `u is not null`. `u is U` is not a presence check either: unless a case type can match `U`, it is error `CS8121`.
- A declared union is a struct with object-backed storage and boxes value-type cases. Choose custom `[Union]` storage only for a concrete requirement. `HasValue`/`TryGetValue` enable non-boxing matching but do not eliminate allocations elsewhere. Measure performance claims.
- Use `readonly union` for immutable wrappers. Record-class cases still allocate; changing those cases to record structs merely moves their allocation to boxing in generated object storage. Custom nullable scalar cases must preserve zero/false as present values and map null/default consistently across every access member.
- Avoid overlapping generic success/error cases unless their conversion and matching behavior is intentional. `Task<Case>` does not convert to `Task<Union>`; give generic factories the intended type explicitly.
- For generic results, prefer distinct cases such as `Result<T>(Success<T>, Failure)` when success and error payload types could coincide. The success payload remains typed as `T`; this does not change the generated union's object-backed storage.
- For functional composition, use immutable cases and pure callbacks with `Map` (transform success), `Bind` (compose fallible functions), and `Match` (consume either case). Preserve failure values and skip success callbacks after failure. Keep expected domain errors as `Failure`; do not catch arbitrary callback exceptions or silently normalize an invalid default. See [functional.cs](examples/functional.cs). These operators do not guarantee callback purity or allocation freedom.

## Closed hierarchies

Use `closed` when alternatives already share a base class or record, common state,
behavior, or polymorphic serialization. It restricts **direct** derivation to the
declaring assembly and is implicitly abstract; do not combine it with `abstract`,
`sealed`, or `static`.

Closure is not transitive. A normal, nonsealed child remains an extension point for
other assemblies. Mark intermediate nodes `closed` to extend exhaustive matching
through the hierarchy, and mark concrete leaves `sealed` when further derivation
is unwanted:

```csharp
public closed record GateState;
public closed record GateMoving(float Percent) : GateState;
public sealed record GateOpening(float Percent) : GateMoving(Percent);
public sealed record GateClosing(float Percent) : GateMoving(Percent);
```

Use a switch expression that covers the leaves, with explicit null handling when
null can arrive. Adding a new leaf should require updating affected matches; a
catch-all would hide it. See the compiled and executed
[closed-hierarchy example](examples/closed-hierarchies.cs) and the
[hierarchy reference](references/union-reference.md#closed-hierarchies-and-json).

## Serialization

System.Text.Json in .NET 11 writes a union as its active case value, with no wrapper and no discriminator, and a default union as `null`. Reading picks the case by JSON token kind, so two object cases are ambiguous: the source generator reports `SYSLIB1227` (a warning) and reading throws `JsonException`. Successful serialization is not proof of deserialization. Choose by contract:

| Contract | Use |
| --- | --- |
| Cases differ in JSON token kind (`int`, `string`, one object) | the default classifier |
| Object cases without a tag, told apart by root property names | `[JsonUnion(TypeClassifier = typeof(JsonUnionTypeStructuralClassifier))]` |
| Objects carry a tag, in a contract you don't control | a `JsonTypeClassifierFactory<T>` that reads the tag; adapt [json-tagged-union.cs](examples/json-tagged-union.cs) |
| You own the contract and want a tag | a `closed` hierarchy with `[JsonPolymorphic(InferClosedTypePolymorphism = true)]`, which writes the tag first |
| A hand-written converter already exists | keep `[JsonConverter]`; the union keeps it and gets no `SYSLIB1227` |

- Under `JsonSerializerOptions.Web`, numbers also read from JSON strings, so `int` and `string` cases are ambiguous as well.
- The structural classifier compares root property names, never values. It picks the wrong case when a tag and the fields disagree, and a case that can never be chosen uniquely throws `NotSupportedException` at first use, not at build time. Do not use it for tagged payloads.
- A tag classifier maps known tag values to case types and returns `null` for anything else, which the serializer turns into `JsonException`. It is not called for JSON `null`: null selects the first nullable case, otherwise the default union.
- `[JsonPolymorphic]` is valid only on classes and interfaces; on a `union` it is error `CS0592`.
- Promote `SYSLIB1227` and `SYSLIB1228` (a union shape System.Text.Json cannot use, such as a member-provider union) to errors. A context that declares any `JsonSourceGenerationOptions.TypeClassifiers` silences `SYSLIB1227` for all of its unions, so also test reading every union.

Preserve schema-owned tags. Check every case, null/default, unknown and missing tags, and structurally similar payloads. Source-generated JSON working under JIT is not NativeAOT proof; publish and execute the relevant application for that claim. The [JSON reference](references/union-reference.md#systemtextjson-unions) records classifier precedence, evidence and limits; the [closed-hierarchy reference](references/union-reference.md#closed-hierarchies-and-json) covers concrete-case strictness, explicit null payloads and missing-tag exception behavior at application boundaries.

## Verification

Read [the reference](references/union-reference.md), [diagnostic catalog](references/diagnostics.md) and [verification guide](references/verification.md). The verifier compiles and executes the examples in `examples/`.

`scripts/verify.py` uses only the bundled probe source, works in a temporary copy, and checks compiler diagnostics and runtime output, including expected failures. No Git/submodule or source download is involved. It does not run web servers or establish EF, RDG, NativeAOT or application-wide correctness. After application edits, also run the repository's own build and relevant tests.

Compiler diagnostics and executed probes are the technical verification. A separate Roslyn analyzer is optional for project-specific policies, not required for this skill. Report the SDK, checks run and remaining limits; a successful compilation alone does not prove runtime behavior.
