# Changelog

## 4.0.1 — 2026-10-28

- Keep the assertion entrypoint focused on choosing and correcting assertions;
  move graph-equality and Native AOT details into local, conditionally read references.
- Express the existing contract → edit → verify workflow as ordered steps.
  Preserve the executable examples, API semantics and validation rules.


## 4.0.0 — 2026-10-28

- Consolidate the eleven entrypoints into `mstest` and `mstest-assertions`.
  Former workflow entrypoints become local task references under `mstest`;
  explicit callers should invoke `$mstest` with their requested task.
- Move shared API/lifecycle/quality references, the inspector and executable runner
  fixtures to their single owner. Preserve the independent assertion examples.
- Require the unmodified upstream skill-validator, skill-local reference closure
  and archive resource checks. No traversal exemptions or duplicated reference trees.


## 3.5.0 — 2026-10-28

- Move `mstest` and `mstest-assertions` from Nami, including API generation, examples and verification.
- Distinguish API lookup, test implementation, assertion correction and report-only review.
- Keep package-local references and include the API generator template in upload archives.

## 3.4.3 — 2026-10-19

- Display Alexander Nachtmann consistently as the developer and maintainer.
- Preserve all nine skills and existing website, privacy and terms links.

## 3.4.2 — 2026-10-19

- Preserve SDK integration guidance while ancplua-dotnet delegates MSTest to this plugin.
- Distinguish native test-application markers from imported `IsTestProject` gates.
- Name the SDK-managed native coverage extension and qualify class filters.
- Keep all nine focused skills and their automatic invocation policies.

## 3.4.1 — 2026-10-19

- Publish privacy and terms pages for the plugin's actual data handling and MIT license.
- Include the policies in the package and configure their public submission URLs.
- Keep all nine skills and their native-MTP behavior unchanged.

## 3.4.0 — 2026-10-19

- Include MIT licensing, a public-listing icon and publisher metadata.
- Add a compact native-MTP execution skill for discovery, filtering, TRX and
  Microsoft.CodeCoverage, with explicit zero-test and skipped-test checks.
- Route built-in MSTest API questions and project/CI inclusion to test writing;
  keep the main skill focused on reusable extensions and their APIs.
- Share project-discovery guidance and remove duplicated CLI instructions.
- Keep the six review workflows separate and automatic invocation enabled.

## 3.3.0 — 2026-10-17

- Match synchronous and asynchronous lifecycle signatures to resource ownership;
  retain native setup/disposal without importing another framework's interfaces.
- Clarify resource-lock coverage of instance construction and lifecycle, reader
  participation, scheduler scope and process-global mutation restoration.
- Document MSTEST0074's helper-analysis limits, activation and default severity
  without treating reusable resource helpers as inherently incorrect.
- Use native per-test temporary directories with their actual ownership and
  retention contract; require a concrete oracle for configuration defaults.
- Make optional hosted injection's explicit MTP wiring, experimental status and
  generated/AOT test-execution restrictions visible in the relevant workflows.
- Preserve the eight skills, plugin identity, native stack and existing probes.

## 3.2.3 — 2026-10-17

- Make the native stack explicit in plugin metadata and all skill entrypoints:
  MSTest.Sdk 4.5.1, MSTest 4.5.1, MTP 2.5.1, AllMicrosoft and Microsoft.CodeCoverage.
- Remove older-version compilation branches and the copied invocation token;
  compare constructor injection directly with native TestContext.Current.
- Name workspace row values and shared file/setup strings with const fields.
- Use SDK-owned extension registration in AllMicrosoft examples and assets;
  retain Native AOT as an independently verified publication mode.
- Correct the argument-label verifier so it actually checks both display names.

## 3.2.2 — 2026-10-17

- Move project-specific producer, receiver and project-boundary guidance out of the
  portable plugin and into the consuming repository's local skill.
- Retain eight generic MSTest skills, including Native AOT and the six adapted
  test-quality workflows. Keep the unit-agent isolation advice scoped to units.
- Retain general telemetry contract lessons without a product dependency or naming
  a particular implementation in portable guidance.

## 3.2.1 — 2026-10-17

- Split the six adapted test-writing/review workflows into focused skills using
  native MSTest 4.5.1 / MTP 2.5.1 semantics and shared API references.
- Add dedicated Native AOT and project-specific telemetry skills alongside extension design.
- Generalize captured-field lessons into likely agent failures and distinguishing
  checks, independent of the original phase plan and scenario names.
- Use the consuming project's public host registration for application scenarios, preserving
  legitimate internal provider-owned SDK instrumentation.
- Package and optionally link every skill, checking all install destinations
  before creating any link. Preserve plugin identity and invocation settings.

## 3.2.0 — 2026-10-17

- Distinguish unit, integration, end-to-end and shared-helper scopes inside the
  existing plugin, with native MSTest composition and resource ownership.
- Prefer native execution/context and MSBuild metadata over reflection-based
  discovery or configuration lookup; retain public data-provider metadata contracts.
- Verify original declaration locations through the real runner, removing the
  reflective C# navigation harness and redundant direct provider test.
- Document source-glob, obsolete-API and custom reporter pitfalls observed in
  the 3.0.1 evaluation. Preserve its initial activation miss and corrected results.
- Remove obsolete local artifacts after retaining the useful evaluation record.

## 3.0.1 — 2026-10-17

- Expand skill activation to MSTest planning, explanations and API questions,
  including requests without a selected consumer project or package version.
- Keep conceptual answers read-only and distinguish unresolved API contracts
  from signatures verified against installed packages.
- Use the normal test entrypoint for changed-code compilation and restore;
  resolve assertion APIs and analyzer recommendations before writing tests.
- Retain the unchanged 3.0.0 evaluation prompts for regression comparisons.

## 3.0.0 — 2026-10-17

- Rename the repository to `ANcpLua/mstest-extensions-plugin` and update the
  manifest repository URL.
- Preserve the `mstest-extensions` plugin identifier, skill name and
  **MSTest Extensions** display name.
- Clarify the package boundary: one focused skill with 11 supporting references,
  scripts and executable fixtures. Keep the existing skill and runtime behavior.
- Publish a versioned plugin archive and record fresh evaluations separately
  from the existing compatibility and runner evidence.
