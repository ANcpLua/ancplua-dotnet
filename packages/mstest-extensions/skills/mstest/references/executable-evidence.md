# Executable capability evidence

Use this when implementing runner policies, optional hosting, or generated/AOT
consumers. It complements the API inspector: a signature does not establish what
the runner executes or disposes.

The packaged `scripts/verify_capabilities.py` copies `assets/runner-evidence`
into an isolated workspace. It changes only that copy's pins, restores from
nuget.org, and retains discovery, TRX, event journals, resolved API fingerprints,
generated C# and published binary hashes. Run it from the skill directory:

```sh
python3 scripts/verify_capabilities.py --mstest-sdk 4.5.1 --hosting --native-aot
```

Choose the consumer's actual SDK version. Optional hosting has independent
`--mstest-hosting-version` and `--platform-hosting-version` pins; their defaults
are the recorded 4.5.1-family prereleases. `--dotnet-sdk`, `--target-framework`
and `--rid` select explicit build inputs. Native publication requires the target
RID's native toolchain. Omit an optional capability when it is outside the task,
not to represent an unsuccessful check as a pass.

| Check | Independent evidence |
| --- | --- |
| Run, skip and drop | Exact reported outcomes, preserved skip reason, no dropped result, no construction/body for skipped or dropped classes |
| CLI selection and throwing filter | Only selected tests reach the provider; a provider exception preserves its original marker and becomes a failed result |
| Retry recovery and exhaustion | All real attempts, first failure, inconclusive attempt, bounded retries, final TRX outcome and original diagnostics |
| Cooperative retry cancellation | Both timed-out attempts observe cancellation and join their bodies before cleanup; fresh instances; failing final outcome |
| Optional real hosting | Two distinct data rows and two retry invocations each receive a separate service scope; async disposal follows cleanup; each process stops/disposes its own host |
| Published generated consumers | Actual managed and Native AOT artifacts execute data rows, a shared assertion library, async lifecycle and generated invocation; source navigation is checked against the original declarations |
| Negative assertion | Each published consumer deliberately fails one rounded-double-as-Int64 assertion; the verifier requires its exact failed result and original marker |

Verified on 16 October 2026 with MSTest SDK/framework/adapter 4.5.1, MTP 2.5.1,
.NET SDK 10.0.401 and Native AOT `osx-arm64`. Each published consumer has six
results: five passes and one owned rejection. Optional hosting resolves
`MSTest.Extensions.Hosting` 4.5.1-alpha.26507.8 and
`Microsoft.Testing.Extensions.Hosting` 1.0.0-alpha.26507.8. The verifier checks the
resolved versions rather than trusting these fixture defaults.

The hosting bootstrap runs in the checked controller and worker, and can run
during discovery. Factories must tolerate separate process-owned hosts; discovery
creates no invocation scopes in this probe. Its SDK-generated bootstrap requires
an explicit `TPEXP` acknowledgment confined to the optional Hosting project.
Handwritten experimental filter, retry and hosting calls use local `MSTESTEXP`
acknowledgments. Other analyzer warnings remain errors.

These are direct executable checks. They do not establish the separate MSBuild/TRX
controller integration, optional hosting under AOT, arbitrary custom attributes,
reflection-dependent data providers, Windows UI, browser execution or model
selection. Keep those claims separate and verify their actual consumer shapes.
The ordinary framework examples and five original failure probes remain separate
version-compatibility evidence in the source repository.
