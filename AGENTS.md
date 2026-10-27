# ANcpLua plugin monorepo

This repository owns the marketplace in `.agents/plugins/marketplace.json` and the public source packages under `packages/`. Keep each plugin identity, license, assets and verification commands in its own package. The packages retain their own pinned toolchains.

- `packages/ancplua-dotnet`: seven general .NET skills and Claude agents.
- `packages/nami/plugins/nami`: five focused C# union, MSTest, fixture and Codex messaging skills.
- `packages/mstest-extensions`: nine specialized MSTest skills and executable probes.
- `packages/prepare-plugin-submission`: Submission Studio 2.3.0, imported from the verified Account release with explicit public-publication authorization. Keep the account release identity separate from the Git marketplace distribution; never restore the retired 1.6.0 tree over this source.

Edit the owning source, not installed caches or generated local catalogs. Nami's union source remains in the Nami product repository; use an explicit `UNION_SOURCE` for export. Run `make check` and each changed package's documented verification. Root workflows execute the package gates from their own working directories. Read package AGENTS.md files for their narrower instructions.

Preserve unrelated work. Commit and push authorized changes to main.
