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

Build-time work uses [msbuild](../msbuild/SKILL.md). Native MSTest verification
uses [companion routing](../audit/references/mstest-routing.md); this skill owns
measurement, not another set of test instructions.
