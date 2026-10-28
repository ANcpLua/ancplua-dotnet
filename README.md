# ancplua-dotnet

One repository for the ANcpLua .NET plugin marketplace, source packages and verification. The catalog is `.agents/plugins/marketplace.json`.

| Plugin | Source | Current package |
| --- | --- | --- |
| `ancplua-dotnet` | [General .NET workflows](packages/ancplua-dotnet/README.md) | 0.7.4; seven skills |
| `nami` | [Unions, fixtures and Codex messaging](packages/nami/README.md) | 0.1.3; three skills |
| `mstest-extensions` | [Native MSTest/MTP execution and specialized testing](packages/mstest-extensions/README.md) | 4.0.0; two self-contained skills |
| `prepare-plugin-submission` | [Submission Studio](packages/prepare-plugin-submission/README.md) | 2.3.0; one skill, identical to the verified Account release |

The public plugins keep their existing names and responsibilities. Nami supplies union, fixture-ownership and Codex messaging guidance. General build/package work belongs to `ancplua-dotnet`; MSTest APIs, assertions, runner and extension workflows belong to `mstest-extensions`.

## Install

```sh
codex plugin marketplace add ANcpLua/ancplua-dotnet
codex plugin add ancplua-dotnet@ancplua-dotnet
codex plugin add nami@ancplua-dotnet
codex plugin add mstest-extensions@ancplua-dotnet
codex plugin add prepare-plugin-submission@ancplua-dotnet
```

These commands change installation and are separate from source verification. Existing registrations of the retired `ancplua-openai` catalog can still resolve its entries to this source after refreshing; switch registrations deliberately to avoid duplicate installed identities. Source migration does not automatically remove an installed plugin.

Submission Studio 2.3.0 was imported from the Account release with the owner's explicit authorization to publish its source. The old 1.6.0 repository is retired. The separate Account installation remains private and has the same 2.3.0 package version; a source move does not uninstall either installation. The [migration record](migration/README.md) records provenance and version alignment.

## Verify and maintain

```sh
make check
npm ci --ignore-scripts
make check-docs
make verify-nami
make verify-mstest
```

[Skill and documentation validation](docs/skill-validation.md) records the linter,
link checks and the limits of the upstream skill-validator experiment.

Each package retains its original tests, compiler pins and helpers. Root GitHub workflows run those checks with the appropriate package working directory. Package licenses remain in their respective directories.

For local development, `scripts/local_marketplace.py` accepts explicit `--source NAME=PATH` values for every catalog entry and produces an ignored `.local/marketplace` view. It links sources without copying them. Do not edit installed caches.

The C# union skill remains an export of the Nami product repository. To compare or refresh it, use `make -C packages/nami check-union-sync UNION_SOURCE=/absolute/path/to/nami/.agents/skills/csharp-union-types` or the corresponding `sync-union` target.

## Migration

The [source inventory](migration/source-inventory.json) records original commits, tracked-file hashes and the pre-existing user deletion omitted from the Nami package. The original source repositories are archived only after this tree and its consumers have been verified.
