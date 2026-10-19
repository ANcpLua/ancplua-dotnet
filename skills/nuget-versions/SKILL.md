---
name: nuget-versions
description: Keeps .NET package and SDK versions correct across Central Package Management, Version.props truth chains, global.json (sdk pin, rollForward, msbuild-sdks) and Renovate. Use when adding or bumping a package, converting to CPM, fixing NU1008/NU1010/NU1102/NU1109/NU1605/NU190x, reviewing a Renovate PR that touched only part of a version, or deciding whether a local version override is still needed. MSTest runner/profile setup belongs to mstest-extensions.
license: Apache-2.0
---

# NuGet, CPM and version truth

Every package version lives in exactly one place. A change that moves a version moves every
place that has to agree with it in the same commit, or it is half a change.

Keep version-chain work here; route MSTest runner, profile and project semantics
through the [companion routing table](../audit/references/mstest-routing.md).

## 1. Where versions live

| Layer | File | Holds |
|---|---|---|
| SDK truth | the MSBuild SDK's packaged `Build/Common/Version.props` (for ANcpLua: `ANcpLua.NET.Sdk`) | variables such as `$(RoslynVersion)`, `$(ANcpLuaAnalyzersVersion)`, `$(DotNetRuntimeVersion)` that every consumer receives |
| Repo override | `Version.props` imported by `Directory.Packages.props` after the SDK copy | only values the SDK doesn't define, or values deliberately ahead of it |
| CPM | `Directory.Packages.props` | `<PackageVersion Include="X" Version="$(XVersion)"/>`; `Update=` for packages the SDK injects |
| Projects | `*.csproj` | `<PackageReference Include="X"/>` with no `Version` |
| SDK pins | `global.json` | `sdk.version`, `sdk.rollForward`, `msbuild-sdks` (real MSBuild SDKs only) |

Override invariant for a repo `Version.props` entry. Every entry is exactly one of:

- **SDK-UNDEFINED**: the SDK has no such variable. Deleting it breaks restore.
- **AHEAD**: the SDK ships an older value that this repo deliberately outruns. The comment
  names the SDK value. Delete the entry as soon as the SDK catches up.

An entry equal to SDK truth is a duplicate, and one below SDK truth is a silent downgrade. Both
get deleted. Audit by diffing against
`~/.nuget/packages/<sdk-id>/<version>/Build/Common/Version.props`.

## 2. global.json

```json
{
  "sdk": { "version": "10.0.402", "rollForward": "latestFeature", "allowPrerelease": false },
  "msbuild-sdks": { "ANcpLua.NET.Sdk": "3.4.50" }
}
```

- `rollForward` decides what happens when the exact SDK is missing:
  - `latestFeature`: any installed SDK of the same major.minor at or above the pin, so 10.0.402
    accepts 10.0.402 or 10.0.5xx but not 10.0.401.
  - `latestPatch`: the same feature band only.
  - `disable`: exact match only.
  - No `rollForward`: the default is `patch` when a version is given.
- Picking `disable` forces every machine and CI image to install that exact patch. Use it only
  when a repository needs byte-identical toolchains.
- `msbuild-sdks` resolves `<Project Sdk="Name">` and `<Sdk Name="Name"/>` only. A plain library
  package listed there does nothing for the build. All it does is give Renovate a second copy of
  the version to bump, which is how a PR ends up moving `global.json` while the restored version
  stays put. Check before keeping an entry: the package must contain `Sdk/Sdk.props`, and a
  project must reference it as an SDK.
- A pinned SDK that isn't installed fails every command with "A compatible .NET SDK was not
  found". Install the exact version the way the machine's tooling installs SDKs; never edit the
  pin down to what happens to be installed.
- When the SDK pin moves, keep the CI `setup-dotnet` (`global-json-file: global.json`), the
  template-stamped `DotNetSdkVersion`, and documentation that names the version in line with it.

## 3. CPM rules

- `ManagePackageVersionsCentrally=true` in `Directory.Packages.props`; one file at the first common
  ancestor. A nested `Directory.Packages.props` replaces the parent unless it imports it.
- `CentralPackageTransitivePinningEnabled=true` makes a `PackageVersion` also pin the package
  when it arrives transitively. Use it for security floors, and delete a floor once a direct
  dependency already brings that version or higher.
- Packages injected by an MSBuild SDK (`GlobalPackageReference`, implicit references) get `Update=`,
  never a second `Include=`: NU1009 forbids a `PackageVersion` for implicit references.
- `VersionOverride=` is a decision, not a habit. More than a couple means the central version
  is wrong.
- Conditional versions go on the `PackageVersion` (`Condition="'$(TargetFramework)' == 'net8.0'"`),
  not on duplicated references.
- `Version="$(X)"` requires `X` to be defined before `Directory.Packages.props` evaluates, so
  define it in `Version.props` (imported at its top) or in `Directory.Build.props`.

## 4. Errors and what they mean

| Code | Meaning | Fix |
|---|---|---|
| NU1008 | `Version=` on a `PackageReference` under CPM | delete it, or `VersionOverride` by decision |
| NU1010 | `PackageReference` without a `PackageVersion` | add the central entry |
| NU1009 | `PackageVersion` for an implicitly referenced package | use `Update=` or delete |
| NU1102 | the requested version doesn't exist on the feed | a truth variable points at an unpublished version; publish first or point back to the last published one |
| NU1109 / NU1605 | a downgrade: something requires a higher version than CPM pins | read the full dependency path in the message; raise the central version, never suppress |
| NU1507 | several package sources without `packageSourceMapping` | add source mapping |
| NU1901–NU1904 | NuGetAudit low to critical advisories | upgrade the vulnerable package, or pin a fixed transitive version with transitive pinning |
| NU1603 | the exact version was missing, a higher one resolved | pin the version that exists |

Listing commands: `dotnet package list --include-transitive` and `--vulnerable` on SDK 10;
`dotnet list package` is the pre-10 spelling.

## 5. Renovate

- Renovate sees `Directory.Packages.props`, csproj files, `global.json` (`sdk.version` and
  `msbuild-sdks`), and nothing inside `Version.props` unless a regex custom manager reads it.
  The ANcpLua shared preset (`github>ANcpLua/github-settings-automation`) reads this form:

  ```xml
  <!-- renovate: datasource=nuget depName=ANcpLua.Roslyn.Utilities -->
  <ANcpLuaRoslynUtilitiesVersion>3.0.0</ANcpLuaRoslynUtilitiesVersion>
  ```

  Every version property in a `Version.props` carries that comment, with the comment directly
  above the property line.
- First-party `ANcpLua.*` packages are grouped as `ancplua-sdk`. Minor and patch bumps automerge;
  majors need review and land on `renovate/major-ancplua-sdk`.
- Reviewing a Renovate PR: list every place the package's version lives (section 1). If the PR
  touched fewer places than that, it's incomplete. Finish it in one commit, or fix the
  annotations so the next PR is complete, then close the PR as superseded.
- A major bump of a library is a migration. Read the release notes for moved types and new
  package splits, then search the consumer for each moved type before declaring it a version-only
  change.

## 6. Converting a repository to CPM

1. Stop if any `packages.config` exists; migrate those projects to `PackageReference` first.
2. Capture a baseline: `dotnet package list --include-transitive > before.txt` and a binlog.
3. Create `Directory.Packages.props`, move each version into one `PackageVersion`, and pick the
   highest version currently in use per package (no upgrades during conversion).
4. Remove `Version=` from references, keeping conditions on the central entries.
5. Restore, build and diff the package list against the baseline; the only allowed differences
   are the deliberate unifications listed in the commit message.
