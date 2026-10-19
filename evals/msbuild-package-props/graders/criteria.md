---
type: llm
---
PASS if the answer explains that when a package contains buildTransitive/, NuGet imports only the buildTransitive props (so the build/ props with CompilerVisibleProperty never reaches consumers), moves the CompilerVisibleProperty items into buildTransitive/<PackageId>.props (deleting the build/ copy), and suggests verifying from a real consumer (generated MSBuild editorconfig or nuget.g.props) or a regression test, noting that editorconfig-injected unit tests don't prove the wiring.
FAIL if it says both build/ and buildTransitive/ props are imported, or only suggests renaming files without moving the items.
