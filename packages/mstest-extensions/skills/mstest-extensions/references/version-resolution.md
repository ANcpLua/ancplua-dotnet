# Resolve versions before reusing API guidance

The consumer's resolved packages control implementation. Reference snippets are
known patterns, not a substitute for checking the current API. An unfamiliar
release does not require an entry in this skill before it can be used.

## Get current evidence

Inspect package/SDK pins, central versions, imports, `global.json`, and the
normal runner command. Evaluate the configuration, target framework and RID
used by the task. Never select the newest directory in a global package cache
as evidence for a consumer.

The bundled inspector evaluates MSBuild and reads resolved NuGet assets:

```sh
python3 <skill-directory>/scripts/inspect_mstest.py --project <consumer.csproj>
```

It records the SDK, framework, adapter, MTP/extensions, package source commits,
selected DLL/XML paths, and a fingerprint. Pass repeated `--property NAME=VALUE`
options for configuration/target/RID. Use `--restore` for implementation when a
restore is appropriate; it refreshes assets using existing package requests.
For read-only reviews, retain the default and report missing/stale resolution.
MSBuild evaluation can download the selected SDK on first use.

Exit 2 means missing evidence or mismatched evaluated/restore inputs. Unchanged
direct requests alone do not prove fresh transitive/floating resolution; restore
when that matters. Inspect each affected consumer, not just one project in a
solution. An absent global runner setting is not proof of VSTest; inspect the
SDK and actual entrypoint too.

Save the JSON outside the installed skill to cache evidence. `--previous` takes
that report. `requires_api_refresh` is true on first use, a changed fingerprint,
or stale inputs. False permits reuse of checked API evidence for that resolved
configuration; it does not prove compatibility or cover changed application code.
The helper does not upgrade pins or rewrite reference prose.

If evaluation is unavailable, inspect evaluated settings/assets directly and
state the missing evidence. Do not silently use the last known version.

## Refresh the relevant contract

Follow the package's `.nuspec` repository commit or a verified release tag.
Read shipped and unshipped public API files for the relevant assembly and target,
then the implementation when behavior matters. Check signature changes and
experimental annotations; hosted current docs may describe a later release.
Include obsolete annotations in that check; an API listing's member name alone
does not establish that the member is usable. Store downloaded source outside
the consumer's compile globs or as non-source text. The inspector uses MSBuild
and NuGet assets; runtime reflection is not needed to infer the build configuration.

Treat a user-supplied delta as a change index. Check its base/head and package
pins: a branch named for 4.5.1 can contain API notes while its projects still run
4.4.1. Compile against the resolved package to establish the actual contract.
Additive APIs do not establish unchanged runtime behavior.

For later releases, resolve the requested capability directly. Do not carry an
old restriction forward as a permanent prohibition or treat an introduction
version as a guarantee for every future release. Prefer a newly available
built-in capability when it meets the task. Preserve consumer versions unless
an upgrade was requested.

Report versions, target/runner, source revision and focused checks. When updating
the skill itself, replace stale wording in the relevant reference; record dated
evidence in [version notes](version-notes.md). Repository verification accepts
exact SDK versions and tests isolated copies, preserving consumer pins.
