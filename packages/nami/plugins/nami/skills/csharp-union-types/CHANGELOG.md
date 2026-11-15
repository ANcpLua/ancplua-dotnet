# Changelog

## 2026-11-15 — .NET 11 release (SDK 11.0.100) and System.Text.Json unions

- Moved every pin from `11.0.100-rc.3.26522.148` to `11.0.100` (`global.json`, the verifier and the documentation). On identical inputs, the 42 existing checks produced the same diagnostic IDs, severities, messages and runtime output on both SDKs; only the compiler build changed, from `5.12.0-1.26522.148` to `5.12.0-1.26529.118`.
- Rechecked the version-specific guidance against the release: C# 15 is the default for `net11.0` and is supported only on .NET 11 and later (polyfill note added); `u is U` is `CS8121` by language rule, not an RC3 quirk; the Roslyn API table now records the NuGet 5.12.0 packages of 2026-11-13, which have every union and closed-type API without the experimental marking, while 5.9.0 still fails each use with RSEXPERIMENTAL006.
- Added System.Text.Json union guidance: case values without a discriminator, token-kind reading, `SYSLIB1227` and `SYSLIB1228`, the structural classifier's limits, custom classifiers, classifier precedence, JSON null, converters, `CS0592` for `[JsonPolymorphic]`, and the closed-hierarchy alternative.
- Added the `QUnionJson` probe, a tagged-union example with a custom classifier, and verifier support for required build warnings and promoted warning sets. A context with generation-time classifiers silences `SYSLIB1227` for all of its unions; the probe keeps that case visible.
- Added the opt-in `--native-aot` check, which publishes the tagged-union example with NativeAOT, rejects IL2xxx and IL3xxx warnings and runs the executable; CI uses it. The report upload no longer fails CI when the artifact storage quota is exhausted.
- Named this repository as the canonical source of the one-way export.
- Verify old-consumer/new-library behavior by replacing only the library DLL and checking that the consumer hash stays unchanged.
- Check local Markdown files and section anchors in CI.
- Add an explicit, drift-checked one-way exporter from the canonical Nami skill to standalone/plugin copies.
- Record which Roslyn union and closed-type APIs exist in the NuGet 5.9.0 packages (several only as RSEXPERIMENTAL006 experiments, no `UnionCaseTypes`) versus the RC3 SDK compiler 5.12.0, and that `GetClosedDerivedTypeInfo` returns direct derived types only.
- Limit the skill description to the C# 15 `union` keyword and `closed` modifier, excluding union conventions built on attributes the compiler does not recognize.

## 2026-10-26 — multi-level closed hierarchies

- Added a visible closed-hierarchy section and a self-contained example with a closed intermediate node and sealed leaves.
- Added runtime leaf/null checks and compiler checks for a missing leaf, an open external extension point and a closed intermediate boundary.
- Synchronized from the current Nami skill, retaining its RC3 pin and local verification workflow.

## 2026-10-25 — .NET 11 RC3 security update

- Updated the pinned SDK and verification runner to `11.0.100-rc.3.26522.148`.
- Revalidated the existing union examples, functional composition, compiler diagnostics, JSON behavior and polyfill boundaries on RC3.
- Retained the existing example and polyfill implementations; the RC3 release notes list no union-language changes.

## 2026-10-24 — functional result composition

- Added pure Map/Bind/Match composition with explicit error values and an invariant-culture pipeline.
- Verified success transformations, failure propagation, skipped callbacks and representative functional laws.
- Retained explicit rejection of invalid defaults/null callbacks and unchanged callback exceptions.

## 2026-10-24 — typed generic results

- Added a `Result<T>(Success<T>, Failure)` example with int/string success, failure and default checks.
- Added compiler rejections for the wrong generic case type and a missing failure arm.
- Distinguished SDK compilers and active language versions from separately referenced Roslyn packages.
- Refreshed the recorded verification results.

## 2026-10-24 — immutable examples and runtime proof

- Made the outcome and length unions readonly and explained default/null handling and allocation tradeoffs.
- Added executed checks for both outcome cases, both units, scalar boundaries, false/zero, empty states and consistent custom accessors.
- Measured the warmed scalar construction/matching path and retained its zero-managed-allocation check alongside C# 15.0 compilation.
- Retained per-check build binlogs next to the verification report.

## 2026-10-24

- Created the skill package from the local files and probes supplied by Alexander Nachtmann.
- Included union polyfills, local diagnostic explanations and compiler/runtime checks.
- Removed remote source dependencies, documentation lookups and commit/hash comparisons.
- Retained existing third-party license notices with the supplied code.
