# Per-run observability

Target: prepare-plugin-submission 2.0.1

Source revision: `content-sha256:138cb12bca1eef736ea697f97e8b0865a4a5ff17cd613bfc64a6487f77fb808c`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

The local checker and generator return structured JSON, check statuses and findings. Retain command, exit code and source digest. No server process or monitoring service was started. Captured evidence must exclude credentials and unrelated user data.
