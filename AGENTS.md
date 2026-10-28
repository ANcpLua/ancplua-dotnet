# ANcpLua plugin monorepo

This repository owns the marketplace in `.agents/plugins/marketplace.json` and the public source packages under `packages/`. Keep each plugin identity, license, assets and verification commands in its own package. The packages retain their own pinned toolchains.

- `packages/ancplua-dotnet`: seven general .NET skills and Claude agents.
- `packages/nami/plugins/nami`: three focused C# union, fixture and Codex messaging skills.
- `packages/mstest-extensions`: two self-contained MSTest and assertion skills and executable probes.
- `packages/prepare-plugin-submission`: Submission Studio, originally imported from Account release 2.3.0 with explicit public-publication authorization. Never restore the retired 1.6.0 tree over this source.

Edit the owning source, not installed caches, cloud files or generated local catalogs. All four personal cloud plugins are built from this repository. Preserve the fixed IDs in `cloud/plugins.json`; update existing releases with Plugin Creator and record verified receipts in `cloud/releases.json`. Read `docs/cloud-plugins.md` before cloud delivery, run `make check-cloud`, and never recreate a missing binding or reinstall duplicate Git identities. Nami's union source remains in the Nami product repository; use an explicit `UNION_SOURCE` for export. Run `make check`, `make check-docs` for Markdown changes, and each changed package's documented verification. Root workflows execute the package gates from their own working directories. Read package AGENTS.md files for their narrower instructions.

Preserve unrelated work. Commit and push authorized changes to main.
