# Local health checks

Target: fixture-plugin 0.1.0

Source revision: `content-sha256:eaeb85f9cda524ca8f210b8c9dd493ce063d1520365d41583f2d49956f0bfb3a`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

Run check_package.py on the final archive, the Python regression suite, and TypeScript syntax/build checks where dependencies are available. Treat blocked dependency resolution separately from a failed source check. Fixture success measures the preflight workflow, not service uptime or directory eligibility.
