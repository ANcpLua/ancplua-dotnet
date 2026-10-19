---
type: llm
---
PASS if the answer uses Sdk="MSTest.Sdk" pinned through global.json msbuild-sdks, adds a global.json test runner of Microsoft.Testing.Platform, removes Microsoft.NET.Test.Sdk and coverlet, and replaces --collect with --coverage --coverage-output-format cobertura (Microsoft.Testing.Extensions.CodeCoverage through the profile). FAIL if it keeps Microsoft.NET.Test.Sdk or coverlet, suggests the VSTest bridge (TestingPlatformDotnetTestSupport), or claims MSTest.Sdk sets IsTestProject.
