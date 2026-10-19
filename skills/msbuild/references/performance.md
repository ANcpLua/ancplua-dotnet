# Build performance evidence

## Baseline

Keep SDK, configuration, TFM/RID, command and restore/server-cache policy fixed.
Repeat each measured setup and report median plus range; setup is untimed.

| Scenario | Setup before each sample |
| --- | --- |
| Output-cold | Remove only confirmed disposable outputs for the measured graph, including custom artifact paths. This does not imply cold OS, compiler or NuGet caches. |
| Incremental | Build the same baseline, apply the same small source change, then time the build. Restore baseline contents before repeating. |
| No-op | Build successfully, then time an identical build with no input/property changes. |

Save a unique binlog outside outputs that cleaning removes. Separate restore
from compilation when attribution needs it; do not clear shared package caches.

## Attribute before tuning

| Evidence | Next step |
| --- | --- |
| Long evaluation before targets | Inspect import/glob scope, `DefaultItemExcludes`, repeated evaluation and property-function file I/O. Use `-preprocess` to trace ownership. |
| `ResolveProjectReferences` dominates | It includes dependency wait time. Inspect task self-time and the project timeline/critical path. Summed parallel durations are not elapsed time or CPU utilization. |
| Compiler/analyzers dominate | Use a diagnostic run with `-p:ReportAnalyzer=true`; keep analyzer enforcement in the fix. |
| Workers are idle | Check the dependency chain and independent project work before changing `-m`, graph builds or `BuildInParallel`. More workers cannot shorten a serial dependency. |
| Targets/copies repeat in no-op builds | Check inputs/outputs, volatile writes and [copy semantics](items-and-outputs.md). Distinguish IDE up-to-date checks from MSBuild execution. |

A surviving binlog can be replayed without rebuilding when no viewer is available:

```sh
dotnet msbuild build.binlog -noconlog -fl '-flp:logfile=build.log;verbosity=diagnostic;performancesummary'
```

## Restore boundary

Reuse `--no-restore` only after a successful restore for the same graph, SDK,
TFM/RID and restore-relevant properties. Publish flags can change that graph.
Inspect `Directory.Build.rsp` for an inherited `-restore`; an explicit CLI flag
alone may not remove repeated restores. Diagnose NETSDK1004/1047 from assets and
the effective graph rather than suppressing restore indefinitely.

Change one measured cause, repeat the same scenarios and retain the evidence.
Use the repository's distribution of timings instead of universal thresholds.
