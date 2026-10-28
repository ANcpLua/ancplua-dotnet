# Nami skill package

This repository packages one portable plugin and three skills: C# unions,
fixture scope, and native Codex messaging.
The only own marketplace is `ancplua-dotnet`; this repository owns the `nami` package, not another catalog.

- Edit skill guidance in `plugins/nami/skills/<name>/SKILL.md` and its own `references/`.
- The union skill is exported from the canonical Nami `.agents/skills/csharp-union-types` directory selected through `UNION_SOURCE`.
  Change the canonical source first, then use `make sync-union`; do not fork it here.
- Fixture examples use the public MSTest lifecycle API. Do not add background
  cleanup, guessed lifetimes, hidden null suppression or extra dependency injection.
- Use `make check` for package structure and links, `make test` for maintenance
  tests, `make verify-fixtures` for the C# example, and `make verify-union` for the
  pinned compiler/runtime probes. Reports stay in temporary directories.
- `make check` must verify exactly three skills, contained paths and the exported
  union fingerprints. Keep the plugin self-contained.
- Do not install the plugin or change marketplace registration unless explicitly asked.
  Do not add `.claude`, `.codex`, or legacy manifest overlays for unverified clients.
- Preserve unrelated work and the unified repository's existing remote. `.idea` belongs
  to Rider and must not be rewritten as part of packaging.
