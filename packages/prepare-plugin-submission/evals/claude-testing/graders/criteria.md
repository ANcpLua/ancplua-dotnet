---
type: llm
weight: 1
---

Must say three examples and a valid manifest do not prove complete functional testing. Require every exposed tool to succeed with valid inputs, input validation/useful errors, and tests in MCP Inspector and a real Claude connection. Require plugin loading and workflow testing on each intended supported surface and real-prompt comparison with and without the plugin. Respect capability differences such as ignored agents/local servers in Chat. Separate automated package/security gates from functional tests. Do not invent a universal 100% all-model/all-surface uploaded-suite rule or claim tests ran.
Grade semantic correctness, not exact wording.

Do not assume three prompts tested only three tools or that exactly nine tools remain: a prompt may call multiple tools. Coverage counts must come from per-tool evidence.

