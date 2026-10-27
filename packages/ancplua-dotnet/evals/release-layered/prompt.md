---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
tags: [positive]
---
I need to ship a new version of our analyzer package and then make every repository that gets it through our MSBuild SDK pick it up. The SDK's Version.props sets the analyzer version. In what order do I do this, and how do I know when consumers can restore?
