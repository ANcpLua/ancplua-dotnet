---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
tags: [positive]
---
Our Roslyn analyzer NuGet package ships build/MyAnalyzers.props with <CompilerVisibleProperty Include="PublishAot" /> and also a buildTransitive/MyAnalyzers.props that only adds an editorconfig profile. In consumer projects the analyzer always reads an empty build_property.PublishAot, even in projects that set PublishAot=true. Our unit tests that set build_property.PublishAot through an editorconfig pass. What's wrong and how do we fix it and keep it fixed?
