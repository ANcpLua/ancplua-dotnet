# Permission matrix

Target: fixture-plugin 0.1.0

Source revision: `content-sha256:eaeb85f9cda524ca8f210b8c9dd493ce063d1520365d41583f2d49956f0bfb3a`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

| Surface | Observed declaration | Audit limit |
| --- | --- | --- |
| Listing capabilities |  | Presentation, not authorization |
| MCP service | 1 declarations | No service authority inferred |
| Portal | Human creator | No upload, attestations or publication |

Dependency and semantic secret-content review remain separate from the static package checker.
