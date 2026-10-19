---
name: release
description: Releases .NET NuGet packages through a layered chain (library, MSBuild SDK, analyzers, consumers) without breaking restore. Use when publishing a package, bumping a lower-layer dependency in its consumers, moving a .NET SDK pin across repositories, choosing tag-driven versus push-driven publishing, setting up NuGet trusted publishing, or waiting for nuget.org to index a version before consumers restore it.
license: Apache-2.0
compatibility: Needs git, gh, curl and the .NET SDK. scripts/wait-nuget.sh is POSIX shell.
---

# Layered NuGet release

A consumer can only restore a version nuget.org has indexed. Pointing a version variable (SDK
truth, `Version.props`, `global.json` `msbuild-sdks`) at a version that isn't published and indexed
fails every restore with NU1102. Release order follows the dependency graph, lowest layer first,
and each layer waits for the one below it.

ANcpLua chain (lowest first):

```text
ANcpLua.Roslyn.Utilities -> ANcpLua.Analyzers -> ANcpLua.NET.Sdk (injects the analyzers) -> consumers
```

Two relations point in opposite directions, and both are true. For *publishing* the analyzers come
before the SDK, as drawn above. For *building*, the analyzer repository uses the SDK, which is why
its own agent contract draws `Roslyn.Utilities -> NET.Sdk -> Analyzers`.

The SDK's `Version.props` names the analyzer version every consumer gets, so the analyzers publish
before the SDK points at them. The analyzer repository itself builds with the last published SDK
(a deliberate one-version lag that breaks the cycle), and its self-reference variables point at
its own last published version, never the one being built. Consumers move last, through
`global.json` `msbuild-sdks`.

## 1. Before touching versions

- Read how each repository publishes (`.github/workflows/*publish*.yml`, `release.sh`, `Makefile`):
  - **Tag-driven:** `on: push: tags: ['v*']`. You create and push the tag.
  - **Push-driven:** `on: push: branches: [main]`. CI bumps the patch from the latest `v*` tag
    and creates the tag itself. Don't tag by hand.
  - **Manual:** a `release.sh` with an API key read from a file. Run it from a clean tree.
- Look for a publish gate ("no publishable changes since <tag> — skipping"). A commit that changes
  only `global.json`, docs or CI is often skipped on purpose. Don't force an identical package
  through it.
- The new version string must not exist yet:
  `curl -s https://api.nuget.org/v3-flatcontainer/<id-lowercase>/index.json`.

## 2. Release one layer

1. Make the change, update `CHANGELOG.md` and anything else that names the old version: docs,
   templates, `global.json`, `Version.props`. Search for the old value across the repository.
2. Run the repository's build, pack and test entrypoints the way CI does. For MSTest
   execution, use the [companion routing table](../audit/references/mstest-routing.md).
   A broken commit must never reach a publishing branch or tag.
3. Commit, push, then tag if publishing is tag-driven:
   `git tag vX.Y.Z && git push origin vX.Y.Z`.
4. Watch the publish run: `gh run list --workflow <file> --limit 1`, then `gh run watch <id>`.
5. Wait for the index with `scripts/wait-nuget.sh <PackageId> <version>`. It requires both the
   flat container, which restore uses, and the registration leaf, which `PackageMetadataResource`
   and many tools use. The flat container goes live first, often minutes before the registration
   leaf.
6. Only then point the next layer at the new version.

A tag that points at a broken commit is never moved or deleted on the remote. Release the next
patch instead.

Pack before tests in CI. `dotnet pack --no-build` ships whatever sits in the build output when it
runs, and a test that builds or packs the repository's own projects (package-consumption tests,
MSBuild integration tests) writes into that same output unless it gets its own
`-p:ArtifactsPath=<temp>/`. ANcpLua.Roslyn.Utilities 3.0.0 and 3.0.1 shipped AssemblyVersion
0.0.0.0 that way: a test packed `src/` with `VersionPrefix=0.0.0` between build and pack. After
packing, check one assembly per package: the version inside must be the release version. A green
build plus correct `.nupkg` file names doesn't prove it.

## 3. NuGet client caching

The NuGet client caches HTTP responses for 30 minutes (`~/.local/share/NuGet/http-cache`). A
tool that queried a package before its version was indexed keeps answering "not found" after
the index catches up. Re-run it with a throwaway cache:

```bash
NUGET_HTTP_CACHE_PATH="$(mktemp -d)" dotnet run --project tools/Generator
```

`dotnet restore --no-http-cache` does the same for restore. Don't clear the user's caches to
get past this.

## 4. Publishing credentials

Order of preference:

1. **Trusted publishing (OIDC).** The workflow has `permissions: id-token: write` and a
   `NuGet/login` step that exchanges the GitHub token for a short-lived API key
   (`steps.login.outputs.NUGET_API_KEY`), configured on nuget.org per package owner,
   repository and workflow file. There's no long-lived secret to rotate. The workflow file name
   is part of the policy, so renaming the workflow breaks publishing.
2. **A scoped API key in a CI secret.** Glob-scoped to the package prefix, push-only, with an
   expiry.
3. **A manual key file for local `release.sh` runs.** Read from a file whose location the
   credential registry records (`vitals keys` on ANcpLua machines). Never paste a key into a
   chat, a commit or a command line that ends up in shell history.

When a publish fails with 403, check the key's glob and expiry, or the trusted-publishing policy's
repository and workflow name, before retrying.

## 5. Moving consumers

For each consumer repository in the chain:

1. `global.json`: `msbuild-sdks` to the new SDK version, `sdk.version` to the agreed .NET SDK.
2. Remove repo-local overrides that the new SDK truth made equal or stale (see the
   `nuget-versions` skill, section 1).
3. Direct dependencies on lower layers (for example `ANcpLua.Roslyn.Utilities`) go to the new
   version in their single central place. Read the release notes for moved or split packages.
4. Build and test, commit, push, then release according to that repository's own mechanism.
5. A repository with uncommitted work by someone else: work in a separate `git worktree` on
   `origin/main`, so the release commit contains only the version change.

## 6. .NET SDK pins across machines

- Install a new SDK through the machine's own channel (a dotfiles target, a package manager, or
  `dotnet-install.sh --install-dir <the existing root>`). Keep normal machine selection
  predictable. A deliberately isolated preview uses [project-local SDK selection](../nuget-versions/references/sdk-selection.md),
  preserving machine PATH and the release repository's stable pin.
- macOS: if an installer overwrites the `dotnet` host binary in place while the old one is still
  mapped, the kernel kills every new `dotnet` process (exit 137, "Killed: 9") because the cached
  code signature no longer matches the file. Delete the host binary and re-run the installer so
  the file is created fresh. Don't patch the signature.
- CI uses `actions/setup-dotnet` with `global-json-file: global.json`, so the pin is the single
  source.

## 7. Report

For every layer, give the repository, commit, tag or version, publish run conclusion and index
status, and for consumers the files changed. A layer whose gate skipped publishing is reported
as "committed, publish skipped by gate (<reason>)", not as released.
