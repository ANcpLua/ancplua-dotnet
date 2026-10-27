# Rollback handoff

Target: review-prep-fixture 0.1.0

Source revision: `content-sha256:f0219fed7b1315ce685368c237f5aa8c8073067c838b46733dc984fa0392cb2c`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

Retain the source/archive for assessed version 0.1.0 and its digest before applying changes. Re-run package checks on a chosen prior release. The creator uses the owning installation or directory process to restore it; this meta-tool does not change publication state.
