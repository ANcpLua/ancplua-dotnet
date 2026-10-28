---
name: performance
description: Investigate .NET runtime performance using logs, metrics, traces, spans and profiles; collect crash/hang diagnostics. Use for CPU, GC, allocation or latency problems, hot-path reviews and BenchmarkDotNet comparisons. MSBuild timing belongs to msbuild; MSTest execution belongs to mstest-extensions.
license: Apache-2.0
---

# .NET runtime performance

## Process

1. **Name the question.** Establish the workload, symptom, runtime, OS and comparison:
   implementations, revisions, runtimes or input sizes. Keep source-review
   hypotheses separate from measured costs. A command-only request needs commands,
   not an unrequested collection session.
2. **Choose the evidence.** Load only the matching reference below. Reuse the
   repository's telemetry, tools and package policy. Correlate deployed revision,
   workload, time window and trace/span identifiers before collecting more data.
   Bound collection duration and benchmark
   case count to the question; keep investigative artifacts outside tracked source.
3. **Compare like with like.** Hold workload and environment constant. Check result
   equivalence before interpreting speedups. Report the measured scope, uncertainty
   and artifact paths; an inconclusive result is not an optimization claim.

| Question | Reference |
| --- | --- |
| Which implementation, runtime or revision is faster? | [Benchmarks](references/benchmarks.md) |
| Which production operation is slow, and where does its time go? | [Diagnostics](references/diagnostics.md): logs, metrics, traces/spans, then targeted profiles |
| Where does CPU, memory or waiting go; how do I capture a crash/hang? | [Diagnostics](references/diagnostics.md) |
| Which source patterns warrant a measured change? | [Hot paths](references/hot-paths.md) |

## Bounded collection example

When existing evidence leaves a trace-shaped gap, confirm the CoreCLR process,
tool support and writable output location before this 20-second capture:

```sh
dotnet-trace collect --process-id PID --duration 00:00:00:20 --output /tmp/runtime.nettrace
```

Choose a fresh artifact path outside tracked source; a capture alone is not a
root-cause finding. The diagnostics reference covers events and interpretation.

For build-time work, invoke `ancplua-dotnet:msbuild`; native MSTest verification
uses `mstest-extensions:mstest`. Check availability before the handoff and report
a missing specialist. This skill retains ownership of runtime measurement.
