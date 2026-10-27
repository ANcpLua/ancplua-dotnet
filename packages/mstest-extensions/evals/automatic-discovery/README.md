# Fresh-chat automatic selection evaluation

The [3.0.1 audit](3.0.1.md) records the interrupted patch evaluation, including
the initial activation miss and corrected failures. Raw artifacts were removed
after retaining compact evidence. No new model run is claimed for 3.2.0.

The [3.0.0 evaluation](3.0.0.md) records five scenarios, including a retained
activation miss. Reusable prompts and expected checks are in [cases.json](cases.json).

This is a host evaluation of the installed plugin, separate from the deterministic
sample suite. The prompt and starter project stay outside the packaged skill.
The original run below kept account memory enabled. A separate
[memory-disabled run](without-memory.md) checks selection and navigation without
that context.
The method follows the official guidance to inspect activation, supporting
resource use, and output quality in a new conversation with the plugin enabled:
[Build skills](https://developers.openai.com/plugins/build/skills) and
[Connect and test](https://developers.openai.com/plugins/deploy/connect-chatgpt).

## Reproduce

1. Install and enable the plugin in the intended account. Verify the installed
   version and skill files; configuration alone is not evidence of selection.
2. Copy only [fixture](fixture) to a temporary project outside this repository.
   It contains a project file, SDK pins, two ordinary data rows, and ignore rules.
   There are no project instructions, skill files, wrapper implementations, or
   expected navigation answers in the fixture.
3. Start a fresh chat with [prompt.txt](prompt.txt), replacing
   `<fixture-directory>` with the absolute copy path. Keep the normal model and
   account settings. Do not invoke, mention, attach, or select the plugin in the
   request. Do not supply this report or a previous conversation's messages.
4. Inspect the chat's tool calls and resulting files. A statement that a skill
   was used is insufficient: require the actual installed skill/reference reads.
5. Check the generated wrapper factory, real JSON discovery locations, passing
   tests, and the failing child runner's outcomes. Preserve failed attempts and
   distinguish a retry from the first automatic selection.

## Recorded run: 2026-10-16

| Property | Observed value |
| --- | --- |
| Plugin version | 1.0.1 |
| Conversation | `01a14459-c8a9-7e80-ba6b-be6cdc8debd7`, Verify MSTest class diagnostics |
| Host | Local Codex task created through the desktop app |
| Model | Account default `gpt-6.1-sol`, effort `max`; no override supplied |
| Conversation history | Fresh task; no inherited turns or corrective follow-up |
| Account context | Normal installed skills and memory remained enabled |
| Consumer | MSTest.Sdk/framework/adapter 4.5.1, MTP 2.5.1, .NET SDK 10.0.401, net10.0 |
| Initial fixture | Two tests passed through its normal runner |
| OpenAI settings | Version 1.0.1, Uninstall button present, skill switch enabled |
| Package verification | All 11 installed skill files matched account release and source bytes |

The starter's explicit MSTest `using` directive was redundant with the SDK's
global using. It was removed from the checked-in fixture after inspection;
the resulting starter still passes both tests and has zero JetBrains findings.
The original prompt and input snapshot remain in the local evaluation artifacts.

Verified SHA-256 fingerprints:

| Installed file | SHA-256 |
| --- | --- |
| `SKILL.md` | `689fac6bfca46c9ee5805e8a1f89c475cc7e626f8f3e4d6da9e427777bca424f` |
| `references/execution.md` | `38bb21c16304373d58fbe196f014a6de92da483c6db7b681fbc9735fb563539b` |

The first command read
`created-by-me-remote/mstest-extensions/1.0.1/skills/mstest-extensions/SKILL.md`.
The agent then read `references/execution.md` and ran the bundled
`scripts/inspect_mstest.py --project Diagnostics.Tests.csproj --restore`.
The submitted prompt contained no plugin name or explicit skill invocation.

The agent also consulted existing account memory after opening the skill.
This demonstrates automatic selection in the user's configured host, with
fresh conversation history. It is not a memory-disabled comparison that isolates
the skill as the sole cause of the answer.

Independent inspection of the generated source and runner artifacts found:

| Check | Result |
| --- | --- |
| Automatic selection | The first command opened the installed 1.0.1 skill without a plugin mention in the prompt |
| Relevant guidance | Read the execution reference and ran the installed API inspector |
| Wrapper factory | `new TimingTestMethodAttribute(testMethodAttribute)`; no source-location arguments |
| Caller information | Optional constructor capture and base forwarding retained; no `ExplicitCallerInfoArgument` suppression |
| Normal runner | 6 tests passed, including the child-runner integration test |
| Failure probe | 7 cases: 4 passed, 2 failed, 1 inconclusive (`NotExecuted` in TRX); expected exit 2 |
| Result preservation | Original failure messages and method-policy logs retained; elapsed timing present on all 7 results |
| Source navigation | All 7 JSON locations matched original method attribute files and both line bounds |
| JetBrains inspection | Zero findings in both generated projects at `INFO` severity |

The evaluator parsed the generated TRX and discovery JSON, checked each source
location against the source files, and inspected the wrapper factory and
suppression search results. The normal runner command was
`dotnet test --project Diagnostics.Tests.csproj`; the child runner was invoked
through the same entrypoint with TRX enabled. Discovery used
`dotnet RunnerProbe/bin/Debug/net10.0/RunnerProbe.dll --list-tests json --no-ansi`.
No separate compilation claim substitutes for these runner results.

The agent encountered sandbox restrictions on the runner's local IPC and the
inspection tool's caches, then obtained the required execution access and reran
the checks. These were environment retries within the original task, with no
corrective prompt from the evaluator.
The observed result is one successful automatic selection and application of the
navigation guidance; the installed skill contents did not need another edit.

## Limits

This is one positive request on one host. It does not measure activation rates,
false positives, alternate wording, other models, or cloud-only ChatGPT chats.
Source navigation is checked through runner discovery metadata; opening each
test in Rider's UI is a separate check. Raw local tool traces, generated code and test reports were removed during the
3.2.0 cleanup. The compact recorded findings and conversation identities remain;
they are historical evidence rather than a new host evaluation.
