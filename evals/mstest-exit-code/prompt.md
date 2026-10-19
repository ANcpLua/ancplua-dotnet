---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
tags: [positive]
---
Our CI step runs 'dotnet test --project tests/Orders.Tests --filter ClassName=OrdersTests' with MSTest on Microsoft.Testing.Platform and fails with exit code 8, but there are tests in that class. What's going on?
