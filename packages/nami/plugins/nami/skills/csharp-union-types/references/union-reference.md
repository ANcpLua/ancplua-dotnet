# Union reference — .NET 11

Baseline: SDK `11.0.100`, the [.NET 11.0.0 release](https://github.com/dotnet/core/blob/main/release-notes/11.0/11.0.0/11.0.0.md) of 2026-11-10, with C# 15.0 and compiler `5.12.0-1.26529.118`. See [verification.md](verification.md) for source and reproducible checks. Recheck implementation-dependent behavior when changing SDKs. Moving the pin from RC3 (`11.0.100-rc.3.26522.148`, compiler `5.12.0-1.26522.148`) to this release changed no diagnostic ID, severity or message and no runtime result among the 42 checks the verifier had then.

## Declaration and conversion

`union U(A, B);` creates a struct containing an `object?` value and implementing `IUnion`. Value-type cases are boxed. Case types may include classes, structs, interfaces, type parameters and nullable types.

A body permits computed properties and methods but no additional instance fields, auto-properties or field-like events. Public single-parameter constructors are reserved for case creation. Other constructors must chain to a generated constructor. A conditional between two case types does not necessarily resolve a constructor overload; prefer a factory with an explicit union return type. [unions.cs](../examples/unions.cs) includes one.

Conversions work where the target union is known. They do not chain through another union or an arbitrary user-defined conversion. `Task.FromResult<Outcome>(new Accepted(...))` works; inferred `Task<Accepted>` is not `Task<Outcome>`. Custom implicit operators can shadow union conversion.

Overlapping cases need not make a declaration invalid. Better-conversion rules may select a case; unrelated applicable interfaces can make conversion ambiguous. Runtime matching sees the contained object, not a separate case tag.

Generic declarations retain their case types: `Result<int>(Success<int>, Failure)` accepts
`Success<int>`, not `Success<string>`. Distinct success/error cases keep their roles separate
when payload types coincide. The example `Result<T>` has runtime checks for `int`, `string`,
failure and default; compiler checks reject a wrong closed case (`CS0029`) and an omitted
failure arm (`CS8509`, promoted to an error). Generic type safety does not imply unboxed storage.

## Functional composition

`examples/functional.cs` composes pure functions with `Map`, `Bind` and `Match`. Map transforms
only a successful payload; Bind calls a function returning another Result; both propagate the
same Failure object without invoking the success callback. Match evaluates just the selected
branch. Expected parse/validation failures remain values. Null delegates and uninitialized unions
are programming errors; callback exceptions propagate unchanged. There is no implicit exception
capture, I/O or mutable shared state. Callbacks must themselves be pure for the composition to
be pure. The example uses explicit invariant culture and widens before multiplication.

The verifier checks representative map identity/composition and bind identity/associativity laws
for success and failure, alongside explicit expected outputs and skipped-callback checks. This
does not imply deep immutability of arbitrary payloads or allocation-free generic composition.

## Patterns

| Pattern | Input examined |
| --- | --- |
| `Accepted a`, `Accepted { Message: ... }` | Contents |
| Constant, relational, `null` / `not null` | Contents, with applicable null wrappers/references |
| Untyped property/positional pattern | Wrapper members |
| List pattern | Wrapper count/indexing members; a list case alone is insufficient |
| `var x`, `_` | Wrapper |

`u is { }` does not check whether a struct union contains a value. `not null and var x` still binds the wrapper. A type pattern must be compatible with at least one case type; interfaces on the wrapper are not automatically interfaces of its contents. `u is U` therefore produces `CS8121` unless a case type can match `U`; it is not a runtime test of the wrapper. The [language reference](https://learn.microsoft.com/dotnet/csharp/language-reference/builtin-types/union#union-pattern-matching) and the [feature specification](https://learn.microsoft.com/dotnet/csharp/language-reference/proposals/csharp-15.0/unions) state the same rules.

## Completeness and null

Only switch **expressions** receive exhaustiveness analysis. For unions and closed hierarchies, promote these diagnostics when missing cases must fail the build:

```xml
<WarningsAsErrors>$(WarningsAsErrors);CS8509;CS8655;CS8846</WarningsAsErrors>
```

They cover missing cases, missing null handling and coverage dependent on guards. Preserve existing warning settings and inspect effective project properties.

`default(U)` has null contents. Non-nullable cases can still make analysis assume non-null contents on this SDK; no missing-null diagnostic is guaranteed. Add an explicit null arm when defaults can arrive. It handles the default hole without swallowing future cases. Do not silently translate an invalid default into a normal business state.

A `U?` has both nullable-wrapper absence and possible null contents. Preserve that distinction when it matters to the domain.

## Custom storage

`[Union]` with the basic creation/access pattern lets classes or structs participate. Public single-parameter constructors define cases; `Value` exposes contents. A public nested `IUnionMembers` interface can instead provide `Create` factories and access members. Compiler lookup then uses that provider.

Optional `HasValue`/`TryGetValue(out Case)` enable typed matching without object-valued access. Constructors/storage must avoid boxing too. Four behavioral invariants are assumed, not proved: sound contents, stable creation, equivalent behavior for overlapping conversions, and consistent accessors.

A record-class provider can recurse accidentally through its synthesized copy constructor. Execute factory examples before adopting them. Upstream `QLang2` variants `CLASS_PROVIDER` and `CAST_FIX` are safe checks; `REC_RECURSE` intentionally crashes and is excluded from the verifier.

## System.Text.Json unions

Sources: [Serialize union types](https://learn.microsoft.com/dotnet/standard/serialization/system-text-json/union-types), [What's new in .NET 11 libraries](https://learn.microsoft.com/dotnet/core/whats-new/dotnet-11/libraries), [SYSLIB1220-1229](https://learn.microsoft.com/dotnet/fundamentals/syslib-diagnostics/syslib1220-1229), [polymorphism](https://learn.microsoft.com/dotnet/standard/serialization/system-text-json/polymorphism) and the [API proposal](https://github.com/dotnet/runtime/issues/127299). Unless a statement names another source, the bundled `QUnionJson` probe or the [tagged-union example](../examples/json-tagged-union.cs) executes it on SDK `11.0.100`. Where the proposal and the shipped behavior differ (the proposal threw for JSON `null` without a nullable case and deferred built-in classifiers), the shipped behavior is recorded.

**Writing.** The serializer writes the active case value without a wrapper or discriminator. A default generated union writes `null`.

**Reading.** The default classifier picks the case from the JSON token kind: number, string, Boolean, array or object. A token that no case accepts throws `JsonException`. Cases that share a token kind are ambiguous: two object cases, `int` and `string` under `JsonSerializerOptions.Web` (see `QSrcGen`), or, as the libraries article says, `T` and `T?` for a non-null payload. The source generator reports `SYSLIB1227` as a warning, and reading throws `JsonException` ("JSON value type 'Object' is ambiguous").

**Structural classifier.** `[JsonUnion(TypeClassifier = typeof(JsonUnionTypeStructuralClassifier))]` narrows object cases by root-level property names; per the union article, missing required properties and disallowed unmapped members also remove cases. It never reads values: with a `Kind` property on both cases, `{"Kind":"square","Radius":1}` selected the circle case. `{}` throws `JsonException`. When one case can never be selected uniquely, because another case recognizes all of its property names, building the classifier throws `NotSupportedException`. That happens at the first use of the type's metadata; the build reports nothing.

**Custom classifier.** Derive from `JsonTypeClassifierFactory<T>`; `CreateJsonClassifier` returns a `JsonTypeClassifier`, a `Type? (ref Utf8JsonReader reader)` delegate. Read the tag, return the case type for each known value and `null` for anything else, which the serializer reports as `JsonException`. The serializer reads the selected case from the start of the value afterwards, so the tag may appear anywhere in the object. Skip other values with `TrySkip`: [`Skip`](https://learn.microsoft.com/dotnet/api/system.text.json.utf8jsonreader.skip) throws when the reader does not hold the final block, as in streaming reads, and `ValueTextEquals` compares escaped property names correctly. The [example](../examples/json-tagged-union.cs) also rejects a missing, repeated or non-string tag, and its verification streams an array through a 16-byte buffer.

Classifier precedence, each step observed in `QUnionJson`:

1. `JsonTypeInfo.TypeClassifier`, set through a contract modifier. It overrode the `[JsonUnion]` factory on source-generated metadata.
2. The `[JsonUnion(TypeClassifier = typeof(...))]` factory. It overrode a matching options-level factory with reflection metadata.
3. The options-level factories in `JsonSerializerOptions.TypeClassifiers`. `[JsonSourceGenerationOptions(TypeClassifiers = ...)]` fills this list in the generated default options of the context (`Context.Default`). A context constructed with your own `JsonSerializerOptions` uses that instance's list instead, and a factory added there applied to the source-generated metadata.
4. Token-kind classification.

**JSON null** never reaches a classifier. It selects the first nullable case: for `union NullableCase(Circle, Square?)`, the serializer constructed the `Square?` case with `null`. Without a nullable case it produces the default union. A `required` union property therefore accepts JSON `null` as an empty union; validate it in the domain.

**Converters and shapes.** A union with `[JsonConverter]` keeps its converter: its contract kind is `None`, and the generator reports no `SYSLIB1227` for it. The serializer needs public single-parameter case constructors and a public `Value`, as the basic union pattern requires. A union that uses a member provider (`IUnionMembers` with static `Create` methods) compiles, but the generator reports `SYSLIB1228`, and its generated contract throws `InvalidOperationException` ("must specify at least one union case") at first use. Reflection metadata reports the kind `Union` and throws when it serializes a value. According to the union article, `[JsonUnion]` on an ordinary type doesn't make it a union. `[JsonPolymorphic]` is valid only on classes and interfaces, so on a `union` declaration it is `CS0592`.

**Diagnostics as build gates.** `SYSLIB1227` and `SYSLIB1228` are warnings; adding them to `WarningsAsErrors` fails the build. The generator cannot tell which union an options-level factory covers, so any `JsonSourceGenerationOptions.TypeClassifiers` entry suppresses `SYSLIB1227` for every union in that context. An uncovered union there still builds with both IDs promoted and throws `JsonException` when read. Test reading every union.

**Contracts you own.** A `closed` hierarchy with `[JsonPolymorphic(InferClosedTypePolymorphism = true)]` writes the discriminator first, for example `{"$type":"PartlyApproved","Approver":...}` in `QClosedJson`, and selects the case independently of the other properties. The tag is serializer metadata: serialize through the base type, because the same `PartlyApproved` serialized through its own contract has no tag, and, as the polymorphism article advises, keep the discriminator name distinct from the properties.

**Recorded evidence from a production contract.** On 2026-11-15, Nami's C10 spike replaced four generated union converters with tag classifiers of this shape on SDK `11.0.100`. The publish reported no IL2xxx or IL3xxx warning, and in the native executable all 28 wire checks, 15 writes and 13 read-then-write round trips, were byte-identical to the hand-written converters, as was a stream read through a 16-byte buffer. That spike is not bundled; this repository's own JIT and NativeAOT checks are listed in [verification.md](verification.md).

## Closed hierarchies and JSON

`closed` is implicitly abstract and restricts direct subclasses to the assembly. Do not add `abstract` as well. It does not automatically seal descendants; seal concrete cases when external extension is unwanted. Closing an existing storage hierarchy may preserve behavior with less disruption than converting it to a struct union.

For multiple levels, mark each intermediate node `closed` if its descendants must
remain known to exhaustive matching. A switch expression can then cover the concrete
leaves. A normal nonsealed intermediate node stays open: another assembly may derive
from it even though the root is closed. Matching that open branch covers its unknown
future descendants, not a fixed set of leaves.

[closed-hierarchies.cs](../examples/closed-hierarchies.cs) demonstrates a closed
`GateState` root, a closed `GateMoving` branch, sealed leaves and explicit null rejection.
The verifier also removes a leaf arm to require `CS8509`, accepts external derivation
through an open branch, and rejects direct external derivation from a closed intermediate
node with `CS9382`. These are source-level checks on the pinned compiler, not a promise
that an already compiled consumer understands future library cases.

Bare union JSON adds no discriminator. Two empty cases can both serialize to `{}`, making reconstruction impossible without another tag. Structural classification can also be ambiguous for overlapping property sets. Unknown fields must not downgrade malformed input into another valid case.

Prefer schema-owned discriminators, read by a tag classifier or an existing converter. `JsonPolymorphic`/`JsonDerivedType` configure class hierarchy serialization. Do not replace stable persisted tags with inferred CLR names. Source-generated metadata must be checked through the actual options/context. `QSrcGen`, `QClosedJson` (reflection metadata) and `QUnionJson` run under JIT only; the NativeAOT check covers the tagged JSON example alone.

For strict System.Text.Json boundaries around closed hierarchies:

- Apply `JsonUnmappedMemberHandling(Disallow)` to concrete cases. Do not assume
  placing it only on the root rejects extra fields on every derived contract.
  A payload must not combine a valid case tag with fields belonging to another case.
- `JsonRequired` checks that a property is present; an explicit JSON `null` still
  needs domain validation when that value is invalid. Non-nullable C# annotations
  do not make untrusted JSON non-null, including collection elements.
- A missing discriminator on an abstract root can produce `NotSupportedException`
  rather than `JsonException` with the default resolver. Check the real serializer
  and HTTP boundary so malformed input cannot silently become a server error.
- Test independently specified wire JSON in both directions. A serialize-then-
  deserialize round trip alone can miss a discriminator changed on both sides.

These are serializer/application-boundary rules, not additional guarantees supplied
by `closed` or `union`. Keep HTTP error translation in the application, and retain
the distinction between the wrapper and its payload when inspecting failed cases.

## Continuous analyzer checks

A Roslyn analyzer can find unions and closed types through their symbols (see [Roslyn API versions](#roslyn-api-versions)) and flag catch-all arms, switching on object-valued `Value`, missing default guards under a chosen policy, and reliance on switch statements for completeness. Scope rules to the intended operation; deliberate `Value` access and defaults at parse boundaries remain valid.

An analyzer cannot generally prove byte-identical JSON, AOT execution or allocation counts. Use the relevant runtime/application checks for those claims; do not substitute a clean compiler result for behavior that was not executed.

### Roslyn API versions

Which APIs exist depends on the Roslyn assemblies the analyzer or generator compiles against, not on the SDK that builds its consumers. Compared on 2026-11-10: the NuGet packages `Microsoft.CodeAnalysis.Common` 5.9.0 (`Microsoft.CodeAnalysis.dll`) and `Microsoft.CodeAnalysis.CSharp` 5.9.0 (`Microsoft.CodeAnalysis.CSharp.dll`), both `lib/netstandard2.0` with informational version `5.9.0-1.26357.3`, and the same two assemblies bundled in SDK `11.0.100-rc.3.26522.148` (`sdk/11.0.100-rc.3.26522.148/Roslyn/bincore`, informational version `5.12.0-1.26522.148`). Rechecked on 2026-11-15 against the 5.12.0 packages, which nuget.org published on 2026-11-13 (`lib/netstandard2.0` and `lib/net10.0`, informational version `5.12.0-1.26502.2`), and against the assemblies in SDK `11.0.100` (informational version `5.12.0-1.26529.118`).

Member presence comes from `ref assembly`, which does not list attributes. The experimental status comes from `ilspycmd` 11.1 decompilations, which show `[Experimental("RSEXPERIMENTAL006")]` on each 5.9.0 member marked experimental below and on none of the listed 5.12.0 members. Compiling a program that uses these members confirmed it: against 5.9.0 every use failed with RSEXPERIMENTAL006, against the RC3 compiler's assemblies and, on 2026-11-15, against the NuGet 5.12.0 packages it compiled without diagnostics.

| API | NuGet 5.9.0 | NuGet 5.12.0 and the SDK 11.0.100 compiler |
| --- | --- | --- |
| `ITypeSymbol.IsUnion` | experimental | present |
| `ITypeSymbol.IsClosed` | experimental | present |
| `ITypeSymbol.GetClosedDerivedTypeInfo(CancellationToken)`, returning `ClosedDerivedTypeInfo` with `ClosedDerivedTypes` and `IsComplete` | experimental | present |
| `ITypeSymbol.UnionCaseTypes` | absent | present |
| `LanguageVersion.CSharp15` | absent; parse with `LanguageVersion.Preview` | present |
| `SyntaxKind.UnionKeyword`, `SyntaxKind.ClosedKeyword`, `SyntaxKind.UnionDeclaration`, `UnionDeclarationSyntax` | experimental | present |

"Experimental" means the member exists but each use is compile error `RSEXPERIMENTAL006` until that diagnostic is suppressed; a repository that forbids suppressions cannot use these members on 5.9.0. With the suppression allowed, the same program compiled `union` and `closed` declarations under `LanguageVersion.Preview` against 5.9.0 without errors, and `IsUnion` and `IsClosed` were true for them. Version 5.9.0 exposes no list of a union's case types.

`GetClosedDerivedTypeInfo` returns only the **direct** derived types, closed intermediate types included, as its doc comment says, and throws `InvalidOperationException` when `IsClosed` is false. For closed `A`, closed `B : A`, sealed `C : B` and sealed `D : A`, it returned `[B, D]` for `A` and `[C]` for `B`, identically on 5.9.0, the RC3 compiler, NuGet 5.12.0 and the SDK 11.0.100 compiler. To reach the leaves, an analyzer must recurse into every returned type whose `IsClosed` is true. A returned type that is neither closed nor sealed stays open to other assemblies, so its descendants cannot be enumerated. `IsComplete` is false when the returned set is incomplete, for example when a generic closed type has an unspeakable derived type.

Compiling against 5.12.0, from NuGet or from the SDK's assemblies, raises the minimum compiler that can load the analyzer to 5.12.0; older hosts report CS9057. SDK 11.0.100 carries a 5.12.0 compiler. Keep the repository's pinned Roslyn version unless an upgrade is requested.
