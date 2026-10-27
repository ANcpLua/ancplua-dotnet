# Rollback handoff

Target: fixture-plugin 0.1.0

Source revision: `content-sha256:eaeb85f9cda524ca8f210b8c9dd493ce063d1520365d41583f2d49956f0bfb3a`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

Retain the source/archive for assessed version 0.1.0 and its digest before applying changes. Re-run package checks on a chosen prior release. The creator uses the owning installation or directory process to restore it; this meta-tool does not change publication state.
