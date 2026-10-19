---
type: llm
---
PASS if the plan stays read-only until a report exists and its output separates fixes that are safe to apply without asking from changes that need a decision.
FAIL if it proposes editing files or committing before reporting, or gives no such separation.
