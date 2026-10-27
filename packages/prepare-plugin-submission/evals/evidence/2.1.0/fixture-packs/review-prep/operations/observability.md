# Per-run observability

Target: review-prep-fixture 0.1.0

Source revision: `content-sha256:f0219fed7b1315ce685368c237f5aa8c8073067c838b46733dc984fa0392cb2c`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

The local checker and generator return structured JSON, check statuses and findings. Retain command, exit code and source digest. No server process or monitoring service was started. Captured evidence must exclude credentials and unrelated user data.
