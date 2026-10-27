# Fresh-chat evaluation with memory disabled

Archive note (3.2.0): the findings below are historical. Local raw artifacts
were removed at the owner's request; retained conversation records identify the
original runs.

This follow-up evaluates the installed 1.0.1 plugin with no injected memory,
inherited conversation turns, or supplied navigation answer. It uses the same
[coding request](prompt.txt) and [starter project](fixture) as the original
evaluation, with only the absolute project path replaced.

## Isolation and verification

The desktop task creation tool has no per-chat memory option. Before creating
the evaluated task, `memories.use_memories` and `memories.generate_memories`
were temporarily set to `false`. Both values were restored immediately after
creation; the complete global configuration was byte-identical to its earlier
contents. These settings control memory injection and generation, respectively.
See the current official [memory configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

The actual persisted startup input was inspected before accepting the run. It
contained the normal installed skill catalog, including MSTest Extensions 1.0.1,
and the coding request. It contained no memory summary or memory-use instructions,
no inherited turns, and no copied navigation guidance. The app includes the
source chat's routing ID when creating a task; this is routing metadata, not
the source chat's messages. The evaluator also audits tool calls for reads of
memory files or previous chat history.

The task prompt did not name, invoke, attach, or select the plugin. No corrective
follow-up was sent to the evaluated chat. All 11 installed skill files matched
the repository source, including the same entrypoint and execution-reference
fingerprints recorded in the [original report](README.md).

## Recorded run: 2026-10-16

| Property | Observed value |
| --- | --- |
| Chat | `01a14471-c47f-7fc2-964e-f3f1983430e7`, Verify MSTest with memory disabled |
| Host | Local Codex desktop task |
| Model | Account default `gpt-6.1-sol`, effort `max`; no override |
| Plugin | Installed account plugin, version 1.0.1 |
| Consumer | MSTest.Sdk/framework/adapter 4.5.1, MTP 2.5.1, .NET SDK 10.0.401, net10.0 |
| Startup memory | No memory summary or memory instructions in actual startup input |
| Memory/history access | No observed memory-file reads or previous-chat retrievals throughout the completed turn |
| Automatic selection | Second command opened the installed skill without a plugin mention in the prompt |
| Supporting resources | Read `references/execution.md` and ran the installed API inspector against the fixture |

The evaluator independently inspected the generated source, TRX, and discovery
JSON rather than accepting the agent's summary as the result:

| Check | Result |
| --- | --- |
| Normal runner | 6 tests passed through `dotnet test --project Diagnostics.Tests.csproj` |
| Child probe | 6 cases: 4 passed and 2 deliberately failed; expected runner exit 2 |
| Original results | Both original failure messages survived; all six results included elapsed timing |
| Navigation | All 6 `location.file`, `lineStart`, and `lineEnd` values matched the original test attributes |
| Wrapper factory | `new TimedTestMethodAttribute(testMethodAttribute)`; no copied `DeclaringFilePath` or `DeclaringLineNumber` |
| Caller-info handling | Optional constructor capture and base forwarding retained; no `ExplicitCallerInfoArgument` suppression |
| JetBrains inspection | Zero findings in both generated projects at `SUGGESTION` severity |
| Consumer versions | Original SDK pins unchanged; restored parent and probe assets still use framework 4.5.1 and MTP 2.5.1 |

The agent's wrapper comment correctly states that discovery reads source
locations from the declared method attribute and that the execution wrapper
needs no copied caller metadata. Its regression test launches the real child
runner, requires the expected failure exit status and TRX contents, then compares
JSON discovery locations against the source file's attribute lines.

## Excluded setup attempt

One earlier task, `01a1446f-3460-7b21-a928-ab25b02660bb`, was excluded. The app
created a suffixed directory instead of using the directory prepared with
project-local memory settings. Its startup record contained memory, and its
agent read memory. That task was stopped and archived; it is not a successful
memory-disabled trial. It made no implementation changes to the evaluated
fixture, which used a separate directory. CLI prompt checks and the excluded
task are setup diagnostics, not additional successful trials.

## Evidence and limits

Startup messages, configuration-restoration evidence, observable tool calls,
generated source, and runner reports are kept under ignored local
`artifacts/memory-free-20261016/`. They are not packaged with the plugin. Hidden
reasoning is excluded from the saved observable trace.

This is one positive request under the installed desktop configuration. It does
not measure trigger rates, false positives, alternate prompts, other models, or
cloud-only ChatGPT. The navigation check evaluates real runner file/line
metadata; manually opening each result in Rider remains a distinct check.
