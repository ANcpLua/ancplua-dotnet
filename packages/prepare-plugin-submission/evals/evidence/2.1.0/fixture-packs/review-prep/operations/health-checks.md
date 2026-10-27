# Local health checks

Target: review-prep-fixture 0.1.0

Source revision: `content-sha256:f0219fed7b1315ce685368c237f5aa8c8073067c838b46733dc984fa0392cb2c`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

Run check_package.py on the final archive, the Python regression suite, and TypeScript syntax/build checks where dependencies are available. Treat blocked dependency resolution separately from a failed source check. Fixture success measures the preflight workflow, not service uptime or directory eligibility.
