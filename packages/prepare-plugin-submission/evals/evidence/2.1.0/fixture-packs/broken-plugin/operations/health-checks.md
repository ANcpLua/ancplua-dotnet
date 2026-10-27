# Local health checks

Target: fixture-plugin not-semver

Source revision: `content-sha256:3880e1215cfeb2064d7e9207c1842f8b02b58fe43bc2215809958eaa06d58795`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

Run check_package.py on the final archive, the Python regression suite, and TypeScript syntax/build checks where dependencies are available. Treat blocked dependency resolution separately from a failed source check. Fixture success measures the preflight workflow, not service uptime or directory eligibility.
