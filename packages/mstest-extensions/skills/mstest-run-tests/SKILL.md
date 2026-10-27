---
name: mstest-run-tests
description: "Choose or execute native-MTP MSTest commands, discover/filter tests and collect TRX or coverage. Includes configuration-only runner identification and zero-test diagnosis. Excludes VSTest execution, test/project edits, custom filter providers and Native AOT publication."
---

# Run native MSTest tests

Use the repository's test entrypoint and its resolved native MTP configuration.
The [checked stack](../mstest-extensions/references/native-stack.md) is
MSTest.Sdk 4.5.1 / MTP 2.5.1 with `AllMicrosoft` and native Microsoft code coverage.
Inspect the selected project's SDK, imported settings and restored packages,
the effective `global.json`, and actual .NET SDK. Native `dotnet test` requires
.NET 10+ and `test.runner` set to `Microsoft.Testing.Platform`.
If the repository selects VSTest, report the mismatch; do not add a bridge,
switch runners or upgrade packages to satisfy an execution request.

For a command-only question, return the command without running it. For a run,
select the smallest requested project, solution or test set. Preserve a working
repository wrapper and CI entrypoint. With native .NET 10 MTP, use:

```sh
dotnet test --project Tests.csproj
dotnet test --solution Tests.slnx
dotnet test --project Tests.csproj --help
dotnet test --project Tests.csproj --list-tests
dotnet test --project Tests.csproj --filter 'FullyQualifiedName~ExampleTests'
dotnet test --project Tests.csproj --report-trx --results-directory TestResults
dotnet test --project Tests.csproj --coverage --coverage-output-format cobertura
```

Replace sample paths and filters with the actual scope. MSTest's `--filter`
supports `FullyQualifiedName`, `Name`, `ClassName`, `TestCategory` and `Priority`, with
`=`, `!=`, `~`, `!~`, `&`, `|` and parentheses. Quote the whole expression;
verify which methods/data rows matched. Do not borrow another framework's
filter flags. `ClassName` uses the namespace-qualified class name, for example
`--filter 'ClassName=Example.Tests.ExampleTests'`.
`--list-tests` proves discovery, not execution.

Use the selected application's help for extension options. `AllMicrosoft`
includes TRX reporting and `Microsoft.Testing.Extensions.CodeCoverage`; an unrecognized option
requires checking the actual registered profile/packages. Pass MTP options
directly, without VSTest `--logger` or `--collect` recipes. Collect reports only
when requested and confirm the resulting files exist. Before reporting coverage
percentages, check that the report contains the intended production assemblies
and classes; an empty report is not coverage evidence.

Let the first changed-code run build and restore normally. Reuse `--no-build`
only with matching binaries, assets, configuration and target framework;
it also skips restore. `--no-restore` requires current restore state.

Read the process result and test counts. Zero tests or all-skipped tests do not
establish a passing requested behavior. Diagnose the selected project, filter,
framework and [solution/CI inclusion](../mstest-extensions/references/test-projects.md)
before changing test code. A supported `--minimum-expected-tests` can enforce a
known minimum but includes skipped cases; do not invent a count or suppress
zero-test failures. Report the actual command, executed/passed/failed/skipped
counts and requested artifact paths. Leave test corrections and published AOT
verification to their focused skills.

Sources: [native MTP CLI](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-test-mtp)
and [MSTest filters](https://learn.microsoft.com/en-us/dotnet/core/testing/selective-unit-tests?pivots=mstest),
plus the selected application's version-specific help.
