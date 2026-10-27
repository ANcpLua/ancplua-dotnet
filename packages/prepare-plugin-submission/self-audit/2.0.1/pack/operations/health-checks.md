# Local health checks

Target: prepare-plugin-submission 2.0.1

Source revision: `content-sha256:138cb12bca1eef736ea697f97e8b0865a4a5ff17cd613bfc64a6487f77fb808c`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

Run check_package.py on the final archive, the Python regression suite, and TypeScript syntax/build checks where dependencies are available. Treat blocked dependency resolution separately from a failed source check. Fixture success measures the preflight workflow, not service uptime or directory eligibility.
