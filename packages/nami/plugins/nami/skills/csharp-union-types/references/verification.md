# Local verification

All required probe source is included in this repository. An ordinary source-directory copy or ZIP works: no Git checkout, submodule initialization, remote repository or documentation fetch is required.

## Use versus maintenance

Normal skill use means reading SKILL.md and only the relevant local reference sections. Do not run the full verifier or browse sources merely to answer a covered language question.

Run the verifier when changing the examples/polyfills, validating an implementation change, or rechecking the recorded compiler behavior. It requires Python 3.10+, SDK 11.0.100 and the required target framework reference packs. Like normal dotnet builds, restore may obtain framework/reference packages if they are not already installed. It never fetches probe source or documentation.

```sh
python3 scripts/verify.py
python3 scripts/verify.py --native-aot   # also publish and run the tagged JSON example with NativeAOT
```

`--native-aot` needs the platform's [NativeAOT prerequisites](https://learn.microsoft.com/dotnet/core/deploying/native-aot/#prerequisites); CI installs them and uses the flag. Without it, no NativeAOT claim is checked.

The runner copies the supplied local source to a temporary directory and builds sequentially with at most two workers. It checks exact expected error-code sets and runtime results. An unexpected diagnostic, missing result, failed process, or timeout fails the run. No console-green or empty run is counted as proof.

## Included coverage

| Local source | What is checked |
| --- | --- |
| examples/unions.cs and verification/Examples | Readonly unions compile with C# 15.0 and warnings as errors; executed cases check text, unit conversion, default/null handling, zero/false and scalar access consistency |
| examples/unions.cs Result<T> | Generic int/string successes, failure and default execute; a wrong generic case produces CS0029 and an omitted failure arm produces CS8509 |
| examples/functional.cs | Map/Bind/Match results, skipped callbacks and preserved failures, identity/composition laws, parse/validation pipeline, invalid defaults, null callbacks and exception propagation |
| examples/closed-hierarchies.cs | Every leaf of a multi-level closed hierarchy, null rejection and a missing-leaf CS8509 failure |
| examples/json-tagged-union.cs and verification/Examples/JsonExamples.cs | A tag classifier with source-generated metadata and reflection disabled: case values and `null` written; tag first, last and escaped; unknown, missing, repeated and non-string tags, mixed fields, a missing required field, arrays and strings rejected; an array streamed through a 16-byte buffer. With `--native-aot`, the same checks in a NativeAOT executable whose publish has no IL2xxx or IL3xxx warning |
| probes/QLang | Missing-null runtime failure and explicit null handling |
| probes/QLang2 | Custom provider construction and default access |
| probes/QConv | Target typing, generic Task construction and selected invalid conversions |
| probes/QIface | Matching interfaces implemented by contents |
| probes/QRoslyn | UnionCaseTypes for generated/custom unions and an ordinary type |
| probes/QSrcGen | Web numeric ambiguity versus strict union JSON handling with generated metadata |
| probes/QClosedJson | Five closed-hierarchy roundtrips with the discriminator written first; a derived type serialized through its own contract without it; absent/unknown discriminator rejection |
| probes/QUnionJson | System.Text.Json unions: case values and `null` written, token-kind reading, SYSLIB1227 and SYSLIB1228 as warnings and as promoted errors, structural-classifier limits, classifier precedence, JSON null and nullable cases, a required union property, a converter-backed union, CS0592 for `[JsonPolymorphic]`, and SYSLIB1227 silenced by a generation-time classifier |
| probes/QClosed and QClosedLib | Cross-assembly closure and warning promotion |
| probes/QClosed and QClosedLib, intermediate branches | External derivation through an open child succeeds; direct external derivation from a closed intermediate node fails with CS9382 |
| probes/QClosed and QClosedLib, binary update | Compile the old consumer, replace only the library with an added case, verify the unchanged consumer hash and its SwitchExpressionException for that case |
| Markdown files | Local destinations and section anchors exist; examples inside fenced code do not create anchors |
| verification/Diagnostics | All union and closed-hierarchy diagnostic rows listed in diagnostics.md |
| verification/PolyfillConsumer | Bundled support types on netstandard2.0/net10.0 and use of BCL types on net11.0 |

## Scope limits and local guidance

- The default run opens no web server and does not verify ASP.NET binding, MVC validation or request delegate generation. For an application change, test its real endpoint and confirm that generated RDG code contains it before attributing behavior to that path.
- EF mappings need tests against the chosen provider. A union type is not automatically a persisted discriminator model; preserve a deliberate mapping and roundtrip all states.
- Source-generated JSON under JIT is not an AOT proof. `--native-aot` covers only the tagged JSON example; publish and execute the actual application's NativeAOT path before claiming it works.
- The example's warmed scalar construction/matching loop measures zero managed bytes on the current thread. This is a bounded JIT-path check, not an application benchmark or NativeAOT proof. Reading a present scalar through `Value` still boxes it.
- Exhaustiveness after recompilation is not old-binary compatibility. The library-only replacement check demonstrates that an old exhaustive consumer can throw for an added case; it does not label the change backward compatible.

## Explicit one-way export

Run `scripts/sync.py` from the canonical source, the `ANcpLua/csharp-union-types`
repository, with one or more `--target` directories. It replaced the copy in the
Nami product repository, and its receipts keep the source identity
`nami:csharp-union-types`. The default is a drift check; add `--apply` to export.
Target edits are never imported, and independent modifications are rejected. The
deterministic `.sync-manifest.json` records managed paths so obsolete exported
files can be removed without deleting unrelated target files.

The skill is not coupled to nami or any other application. Follow the consuming repository's own build/test and schema-generation commands when applying it.
