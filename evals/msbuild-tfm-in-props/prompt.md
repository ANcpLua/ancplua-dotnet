---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
tags: [positive]
---
In Directory.Build.props I have <PropertyGroup Condition="'$(TargetFramework)' == 'net8.0'"><DefineConstants>$(DefineConstants);LEGACY</DefineConstants></PropertyGroup>. Our projects each have a single <TargetFramework>net8.0</TargetFramework>, but LEGACY is never defined. Why?
