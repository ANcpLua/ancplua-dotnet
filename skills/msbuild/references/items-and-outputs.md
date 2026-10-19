# Items and copied outputs

## Item identity

| Operation | Meaning |
| --- | --- |
| `Include` | Add an item; `Exclude` subtracts only from this inclusion. |
| `Update` | Change metadata on an existing item; it cannot create a missing item. |
| `Remove` | Remove matching existing items. |

SDK globs already include ordinary source/content: use `Update` for their metadata.
An evaluation-time glob cannot see a file generated later. Add generated items
inside the producing target, under `IntermediateOutputPath`, and track `FileWrites`.

Use `@(Items->'...%(Metadata)...')` transforms to keep sources and destinations
aligned. Metadata in task parameters can batch work; independent item lists can
change alignment or multiply executions. Target batching uses metadata in
`Outputs`; an item-level condition can instead filter individual items. Inspect
the actual identities and batches before rewriting them.

## Copy contract

| Mode | Use |
| --- | --- |
| `Never` | No runtime copy. |
| `PreserveNewest` | Copy when source is newer or destination missing. |
| `IfDifferent` | Reset an output that the application may modify, while skipping unchanged copies. Requires MSBuild 17.13+. |
| `Always` | Deliberately copy on every build, including same-size/same-timestamp edits. |

`IfDifferent` compares timestamp and size, not content hashes. For existing
`Always` items, `SkipUnchangedFilesOnCopyAlways=true` opts into that heuristic;
retain unconditional copying when its stronger contract is needed. Check the
actual SDK's common targets before introducing a mode to an older toolchain.

Use property-relative paths and preserve project/configuration/TFM/RID separation.
Isolating only `-o` leaves intermediates shared; use a distinct `ArtifactsPath`
when a nested build must not overwrite its caller's outputs.
