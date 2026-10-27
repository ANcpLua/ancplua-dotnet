# Rollback handoff

Target: fixture-plugin not-semver

Source revision: `content-sha256:3880e1215cfeb2064d7e9207c1842f8b02b58fe43bc2215809958eaa06d58795`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

Retain the source/archive for assessed version not-semver and its digest before applying changes. Re-run package checks on a chosen prior release. The creator uses the owning installation or directory process to restore it; this meta-tool does not change publication state.
