---
type: llm
---
PASS if the answer explains that Directory.Build.props evaluates before the project body sets TargetFramework in single-target projects, so the property condition is empty, and moves the condition to Directory.Build.targets or the project. FAIL if it blames DefineConstants syntax or suggests TargetFrameworks without explaining evaluation order.
