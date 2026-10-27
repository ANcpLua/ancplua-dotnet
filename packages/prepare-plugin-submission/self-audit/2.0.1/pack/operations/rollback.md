# Rollback handoff

Target: prepare-plugin-submission 2.0.1

Source revision: `content-sha256:138cb12bca1eef736ea697f97e8b0865a4a5ff17cd613bfc64a6487f77fb808c`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

Retain the source/archive for assessed version 2.0.1 and its digest before applying changes. Re-run package checks on a chosen prior release. The creator uses the owning installation or directory process to restore it; this meta-tool does not change publication state.
