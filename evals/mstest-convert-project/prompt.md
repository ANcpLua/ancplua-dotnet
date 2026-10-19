---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
tags: [positive]
---
My test project uses Microsoft.NET.Sdk with PackageReferences to MSTest 4.5.1, Microsoft.NET.Test.Sdk and coverlet.collector, and CI runs dotnet test --collect "XPlat Code Coverage". We're on the .NET 10 SDK. How do I move it to MSTest.Sdk on Microsoft.Testing.Platform with coverage that still produces Cobertura?
