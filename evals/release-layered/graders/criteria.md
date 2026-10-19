---
type: llm
---
PASS if the answer publishes the analyzer first, waits until nuget.org indexes it (flat container and registration), then points the SDK's Version.props at it and publishes the SDK, waits again, and only then bumps consumers' global.json msbuild-sdks; it warns that pointing truth at an unpublished version fails restore with NU1102. FAIL if it bumps the SDK before the analyzer is indexed.
