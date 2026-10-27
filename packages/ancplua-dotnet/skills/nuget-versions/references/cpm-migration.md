# Conditional CPM migration

A version bump updates the existing ownership model. Adopt CPM only when that
conversion is requested; preserve independent nearest-file management scopes.

## Before moving versions

Inventory evaluated package references across each affected TFM, RID and
configuration, including imported props/targets, `VersionOverride`, property-based
versions and existing central files. Capture resolved direct/transitive versions
and a successful build for the affected targets from their applicable SDK directory.

| Finding | Preserve |
| --- | --- |
| Different versions by TFM or configuration | Their conditions; do not flatten them to the highest version by default. |
| `Version="$(X)"` | The definition/import order and other consumers of `X`; keep SDK-owned truth at its owner. |
| Nested central file | Its management boundary; import a parent explicitly only when that is the intended policy. |
| SDK-owned implicit package | Its SDK version mechanism; a new central entry can cause NU1009. |

Resolve a conflict by the requested policy; otherwise make the version decision
explicit before changing behavior. Preserve non-version reference metadata.
Use `Update` only for an existing central item, `Include` to create one.
`GlobalPackageReference` keeps its version on that item. A `PackageReference`
marked `IsImplicitlyDefined` does not accept a new `PackageVersion`; use the
SDK's documented override when one exists.

Restore/build the same affected targets after moving versions and compare the
resolved package graph. Explain each intentional difference. A condition or
shared property is removable only after its remaining consumers are accounted for.

Sources: [CPM](https://learn.microsoft.com/en-us/nuget/consume-packages/central-package-management),
[NU1009](https://learn.microsoft.com/en-us/nuget/reference/errors-and-warnings/nu1009).
