# Per-run observability

Target: fixture-plugin 0.1.0

Source revision: `content-sha256:eaeb85f9cda524ca8f210b8c9dd493ce063d1520365d41583f2d49956f0bfb3a`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

The local checker and generator return structured JSON, check statuses and findings. Retain command, exit code and source digest. No server process or monitoring service was started. Captured evidence must exclude credentials and unrelated user data.
