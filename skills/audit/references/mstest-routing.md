# MSTest companion routing

The `mstest-extensions` plugin owns native MSTest/MTP guidance. Select the smallest
matching installed skill; the qualified names below are shown by Codex. Other
hosts may expose the skill name without the plugin prefix. Preserve the caller's
scope: a read-only audit remains read-only after delegation.

| Task | Companion skill |
| --- | --- |
| Test/project edits, built-in APIs, lifecycle, solution or CI inclusion | `mstest-extensions:mstest-writing-tests` |
| Commands, runner identification, discovery, filtering, TRX, coverage, zero tests | `mstest-extensions:mstest-run-tests` |
| Reusable data/assertions, execution attributes, policies, fixtures, custom filters | `mstest-extensions:mstest-extensions` |
| Practical report-only quality, flakiness and maintainability review | `mstest-extensions:mstest-test-review` |
| Assertion-only report | `mstest-extensions:mstest-assertion-review` |
| Formal named test-smell taxonomy | `mstest-extensions:mstest-test-smells` |
| Hypothetical behavior changes the suite would miss | `mstest-extensions:mstest-test-gaps` |
| Evidence for an identified fix, feature or change | `mstest-extensions:mstest-test-value` |
| Native AOT publication, trimming and generated discovery | `mstest-extensions:mstest-native-aot` |

Keep general MSBuild evaluation/imports, NuGet version chains, analyzer loading
and severities, and release artifact integrity in this plugin. For mixed tasks,
use those skills for their part and the companion for MSTest semantics. Do not
copy test instructions back here or preload all nine skills for every audit.

If the companion is unavailable, report the missing plugin and use the host's
supported installation flow. For Codex, install `mstest-extensions@ancplua-openai`
from [ANcpLua/ancplua-openai](https://github.com/ANcpLua/ancplua-openai). Follow the
[companion installation guide](https://github.com/ANcpLua/mstest-extensions-plugin#installation)
for other hosts. Do not claim an unavailable skill was invoked.
