# BenchmarkDotNet comparisons

## Design

Reuse the benchmark project's resolved package and configuration; a temporary
investigation belongs in a separate task directory. Pick an explicit comparison
axis and representative inputs. Cases multiply across methods, parameters and
jobs, so inspect the selected case list before a long run.

| Concern | Decision |
| --- | --- |
| Optimizer removes the work | Return/consume results; store variable inputs in fields or parameters rather than foldable constants. |
| Setup hides the cost | Put unrelated construction in `GlobalSetup`; include initialization only when measuring it. Reset mutable state at the boundary the operation actually requires. |
| Manual repetitions distort results | Let BDN control invocation count. Use `OperationsPerInvoke` only when one invocation genuinely performs that many operations. |
| Runtime comparison | Configure explicit runtime jobs and inspect the runtime headers; the project's build TFM alone is not the comparison. |
| Allocation comparison | Use `MemoryDiagnoser`; allocated bytes per operation are different from retained heap, working set or native memory. |

## Run

Use Release outside the debugger. Confirm the entrypoint forwards arguments
(typically `BenchmarkSwitcher`); otherwise filters/jobs may be ignored.

```sh
dotnet run -c Release --project Benchmarks -- --filter '*Parser*' --job Dry
dotnet run -c Release --project Benchmarks -- --filter '*Parser*' --job Short
```

Replace the project/filter with the intended cases. `Dry` checks execution, not
performance. Use a marked baseline and suitable steady-state or cold-start job
for the final comparison. Retain BDN's environment, error and allocation reports;
interpret ratios against noise rather than declaring every mean difference a win.

Sources: [good practices](https://benchmarkdotnet.org/articles/guides/good-practices.html),
[jobs](https://benchmarkdotnet.org/articles/configs/jobs.html),
[run strategies](https://benchmarkdotnet.org/articles/guides/choosing-run-strategy.html).
