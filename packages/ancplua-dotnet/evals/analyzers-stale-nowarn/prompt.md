---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
tags: [positive]
---
After upgrading ANcpLua.Analyzers from 1.x to 2.x our Directory.Build.props still has <NoWarn>$(NoWarn);AL0017;AL0018</NoWarn> and an .editorconfig line dotnet_diagnostic.AL1600.severity = none under [*.cs]. Do these still do anything?
