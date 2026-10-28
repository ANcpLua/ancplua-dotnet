# Consolidation — 28 October 2026

Public source packages formerly maintained in `ANcpLua/opusfix`, `ANcpLua/mstest-extensions-plugin` and the root of `ANcpLua/ancplua-dotnet` now live under `packages/` in `ANcpLua/ancplua-dotnet`. The central catalog came from `ANcpLua/ancplua-openai`. The source inventory records the exact input revisions and file hashes. Package build roots are preserved, including Nami's internal `plugins/nami` distribution directory.

The uncommitted deletion of `nami-plugin/.github/agents/specification.agent.md` was preserved by omitting that file. No original working-tree deletion was committed on the user's behalf.

## Submission Studio: one current source version

The owner explicitly authorized publishing the Account release **2.3.0** into this repository on 28 October 2026. The source inventory records the release and archive SHA256. All imported package files are preserved byte-for-byte. The previous GitHub/local package **1.6.0** is superseded; its historical source and 2.0.0 planning documents remain recoverable from the archived repository history.

The Account installation remains private, version 2.3.0. This Git marketplace distributes the same source version publicly. There is no new 2.4.0 release claim: all 72 package tests and five workflow tests passed on the imported 2.3.0 source. Source identity, distribution channel and installed instance are separate; existing installed duplicates are not automatically uninstalled by this repository migration.

## Import diagnostics

The unchanged Account archive contains 34 text files with an extra blank line at EOF. The initial staged `git diff --check` reports those inherited formatting diagnostics. They are retained to preserve the exact verified 2.3.0 source; this is not reported as a clean whitespace check. The 72 package tests, five workflow tests and connector-kit TypeScript build pass.

On 2026-10-28, `mstest` and `mstest-assertions` moved from the Nami package to
`packages/mstest-extensions/skills/`, including their maintenance and verification.
The original source inventory remains an immutable import receipt, not the current layout.
