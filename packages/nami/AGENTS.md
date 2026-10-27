# Nami skill package

This repository packages one portable plugin and five skills: C# unions,
MSTest, MSTest assertions, fixture scope, and native Codex messaging.
The only own marketplace is `ancplua-dotnet`; this repository owns the `nami` package, not another catalog.

- Edit skill guidance in `plugins/nami/skills/<name>/SKILL.md` and its own `references/`.
- The union skill is exported from the canonical Nami `.agents/skills/csharp-union-types` directory selected through `UNION_SOURCE`.
  Change the canonical source first, then use `make sync-union`; do not fork it here.
- `public-api.md` is generated. Its source list and template belong to the MSTest
  skill's `scripts/`; use `make update-mstest-api` rather than editing the table.
- Fixture examples use the public MSTest lifecycle API. Do not add background
  cleanup, guessed lifetimes, hidden null suppression or extra dependency injection.
- Assertion guidance targets MSTest 4.5.1. Prefer the most specific assertion
  that preserves the complete test contract and gives useful failure evidence;
  do not recommend legacy APIs or weaker checks as compatibility fallbacks.
- Use `make check` for package structure and links, `make test` for maintenance
  tests, `make verify-assertions` for the standalone assertion examples and AOT
  analysis probes, `make verify-fixtures` for the C# example, and `make verify-union` for the
  pinned compiler/runtime probes. Reports stay in temporary directories.
- `make check` must verify exactly five skills, contained paths and the exported
  union fingerprints. Keep the plugin self-contained.
- Do not install the plugin or change marketplace registration unless explicitly asked.
  Do not add `.claude`, `.codex`, or legacy manifest overlays for unverified clients.
- Preserve unrelated work and the unified repository's existing remote. `.idea` belongs
  to Rider and must not be rewritten as part of packaging.
