# Cloud plugins from one source

The source packages in this repository produce four private personal plugins for the same account in ChatGPT web and Codex desktop. Git and cloud use the same package versions and skill files. The cloud entries are delivery targets, not independently maintained source trees.

| Plugin | Fixed account entry | Skills |
| --- | --- | --- |
| `ancplua-dotnet` | [ANcpLua .NET](https://chatgpt.com/plugins/plugins_6ae1523d4d2c8191b12ff1429d449f99) | 7 |
| `mstest-extensions` | [MSTest Extensions](https://chatgpt.com/plugins/plugins_6ae1524d41f08191b0368fe424070dee) | 2 |
| `nami` | [Nami](https://chatgpt.com/plugins/plugins_6ae15259f09c819182dda95ef7d5bada) | 3 |
| `prepare-plugin-submission` | [Submission Studio](https://chatgpt.com/plugins/plugins_6ae152677c68819185bec45f04492a9c) | 1 |

These links require the owner's account. They are not public directory listings. The public Git marketplace remains available for other users. The maintainer's four Git installations and their local marketplace registration were removed after verifying the cloud replacements.

## Build and verify

```sh
make check-cloud
```

`scripts/cloud_plugins.py` discovers all four package roots through the existing marketplace catalog. It packages Git-tracked skills, assets, manifests and package legal documents into deterministic ZIPs under `artifacts/cloud-plugins/`. Stage intended new files before building. Untracked files and build outputs are not implicitly published. Symlinks, invalid identities, missing icons and inconsistent compatibility manifests fail the build.

`packages.json` records versions, archive and per-file SHA-256 hashes, the source commit and whether the working tree was dirty. A dirty build's hashes describe its actual payload; its commit alone is not sufficient provenance. Build from a clean commit for releases. CI runs the packaging checks but does not authenticate to the personal account or upload releases.

## Update the existing entries

1. Edit the owning source package. Raise its stable three-part version for changed content and align any compatibility manifest. Run the applicable package checks, `make check-docs`, `make check-skills` and `make check-cloud`.
2. Use Plugin Creator to read each ID from `cloud/plugins.json`, its current metadata and every page of `get_plugin_files`. Preserve `USER` scope and `PRIVATE` visibility. A missing or inaccessible entry is a failure to investigate, not permission to create a replacement.
3. Save the fresh metadata and complete inventories to an ignored file such as `artifacts/cloud-plugins/remote.json`. Its `plugins` object is keyed by package name; each value contains `plugin_id`, `name`, `version`, `scope`, `discoverability`, `current_release_id`, `inventory_complete: true` and `files` as an array of relative paths.
4. Generate a guarded upload plan:

   ```sh
   python3 -B scripts/cloud_plugins.py plan \
     --remote-state artifacts/cloud-plugins/remote.json
   ```

5. For each `update`, call Plugin Creator `update_plugin` with the generated `archive`, unchanged `plugin_id`, `expected_release_id` and exact `delete_paths`. Uploads overlay files: omitted obsolete files must be explicitly deleted. Preserve backend-generated compatibility files. A verified unchanged receipt skips the upload; changed bytes at an unchanged version fail instead of allowing an invisible server-only version bump.
6. Read back the release and expected skill inventory. Compare the downloaded/materialized files with `packages.json`; OpenAI may normalize manifest formatting and account-owned author/developer metadata, but skills, scripts, references and assets must match. Record the returned release ID, source version and uploaded archive SHA-256 in `cloud/releases.json`, then commit and push the receipt.

The script performs packaging and planning only. Plugin Creator performs authenticated uploads. No tokens or cookies belong in this repository. Personal Pro currently has no workspace GitHub marketplace synchronization, so a Git push is followed by this upload step. Future updates reuse the four IDs and do not require uninstalling and reinstalling another distribution.

## Installation and troubleshooting

All four entries were verified installed and enabled in the account and locally on 2026-10-28. Web shows them in **Plugins → Personal** and under **Installed**. Codex uses the same remote IDs under `created-by-me-remote`; its caches are materialized copies, not new Git installations. A fresh chat reloads available skills. Executing .NET builds still requires repository access and the appropriate toolchain in that execution environment.

The basic `codex plugin list` command can omit personal cloud entries. Do not treat absence from that list as proof of an uninstall. The installed Codex app-server protocol supports `plugin/list` with `marketplaceKinds: ["created-by-me-remote"]` and `forceRefetch: true`, plus `plugin/installed` for the local inventory. Inspect the installed protocol schema before using these experimental APIs. `plugin/read` uses the backend plugin ID as `pluginName` for a remote entry; a display name produces a 404. `plugin/reconcile` refreshes materialization; its success alone does not prove every skill is ready, so also verify the resulting inventory and files.

Do not re-add `ancplua-dotnet@ancplua-dotnet` or the other three Git installations on this account. Do not edit `.codex/plugins/cache` directly. The retired private Submission Studio 2.3.0 entry is not a delivery target. Existing public-submission drafts in the developer portal have separate identities and are outside this migration.
