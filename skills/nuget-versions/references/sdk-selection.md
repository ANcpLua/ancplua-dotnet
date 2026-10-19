# Project-local SDK selection

For an explicitly requested isolated SDK, use a repository-local `.dotnet/`.
`sdk.paths` needs a .NET 10+ **Host** in `dotnet --info`; `dotnet --version`
reports the selected SDK instead.

1. Resolve the requested SDK and architecture. Run the official `dotnet-install`
   script with that exact version, `--install-dir .dotnet` and `--no-path`
   (equivalent PowerShell options on Windows).
2. Merge SDK selection into the existing `global.json`, preserving other fields.
   For an isolated exact pin, set `sdk.version` to the installed version,
   `sdk.rollForward` to `disable`, and `sdk.paths` to `[".dotnet"]`.
   Permit prerelease resolution only when appropriate to the requested version.
3. Ignore `.dotnet/` in Git; record reproducible installation in normal setup/CI.
4. Run `dotnet --version` and `dotnet --info` from the repository: verify both the
   selected version and SDK base path, including the required subdirectory scope.

Paths are relative to `global.json`, not the working directory. Add `"$host$"`
after the local path only when system fallback is wanted. Older hosts ignore
`paths`; invoke the local host directly or update the host through its normal
channel. SDK selection does not select the runtime for `dotnet app.dll`.

Restore the previous SDK policy; remove only the task-owned installation.
Preserve machine PATH and other SDKs.

Source: [local SDKs and sdk.paths](https://learn.microsoft.com/en-us/dotnet/core/tools/test-prerelease-sdk-locally).
