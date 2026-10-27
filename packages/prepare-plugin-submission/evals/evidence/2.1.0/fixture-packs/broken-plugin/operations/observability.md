# Per-run observability

Target: fixture-plugin not-semver

Source revision: `content-sha256:3880e1215cfeb2064d7e9207c1842f8b02b58fe43bc2215809958eaa06d58795`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

The local checker and generator return structured JSON, check statuses and findings. Retain command, exit code and source digest. No server process or monitoring service was started. Captured evidence must exclude credentials and unrelated user data.
