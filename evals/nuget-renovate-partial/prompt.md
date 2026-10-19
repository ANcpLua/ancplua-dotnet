---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
tags: [positive]
---
Renovate opened a PR that bumps 'ANcpLua.Roslyn.Utilities' from 2.2.48 to 3.0.0 in global.json msbuild-sdks, CI is green, but our Version.props still says <ANcpLuaRoslynUtilitiesVersion>2.2.48</ANcpLuaRoslynUtilitiesVersion> and Directory.Packages.props uses that property. Is this PR safe to merge?
