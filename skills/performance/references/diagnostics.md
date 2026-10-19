# Runtime evidence

Identify the actual process, runtime, architecture and diagnostic access before
choosing a tool. CoreCLR examples below assume available tools and a writable
artifact directory; replace `PID` and paths. Check the installed tool's help for
providers, profiles and duration syntax.

| Symptom | First useful evidence |
| --- | --- |
| CPU/GC/allocation pressure | Runtime counters, followed by a bounded trace around the symptom. |
| Slow requests or hangs | Thread/wait and contention evidence; elapsed time alone does not establish CPU cost. |
| Growing memory | Allocation rate plus retained-heap evidence at comparable workload points; distinguish managed heap from RSS/native memory. |
| Crash | OS/runtime crash collection configured before reproduction, preserving the matching binary and symbols. |

```sh
dotnet-counters monitor --process-id PID --counters System.Runtime
dotnet-trace collect --process-id PID --duration 00:00:00:20 --output artifacts/diagnostics/runtime.nettrace
dotnet-dump collect --process-id PID --type Heap --output artifacts/diagnostics/heap.dmp
```

Counter monitoring is interactive; stop after the agreed observation window.
Managed thread sampling includes waits: it is not an on-CPU profile. Select
allocation events when measuring allocations; choose an OS on-CPU profiler when
CPU attribution is required. On supported Linux systems, `collect-linux` can
provide kernel CPU samples; its defaults can include other processes, so select
the target explicitly. Never infer a leak from allocation rate alone.

For attach failures, inspect diagnostic settings, process identity and the
container's diagnostic socket; on Unix, target and tool may need the same
`TMPDIR`. A heap/full dump can increase memory pressure or pause the process.
Keep artifacts local unless sharing was requested; they can contain application data.

For Native AOT, verify `EventSourceSupport` for EventPipe and the runtime's
supported events. Use native dump capture: `gcore` on Linux, LLDB's `process save-core`
on macOS, or ProcDump on Windows, with matching binary and symbols. CoreCLR/SOS
support does not follow from a successful native capture. Scope automatic crash
collection to the target and undo temporary settings afterward. Confirm the
artifact captured the symptom; collection alone is not a root-cause finding.

Sources: [counters](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters),
[traces](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-trace),
[dumps](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-dump),
[Native AOT diagnostics](https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/diagnostics).
