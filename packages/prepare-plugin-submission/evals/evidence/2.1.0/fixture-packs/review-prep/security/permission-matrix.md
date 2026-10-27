# Permission matrix

Target: review-prep-fixture 0.1.0

Source revision: `content-sha256:f0219fed7b1315ce685368c237f5aa8c8073067c838b46733dc984fa0392cb2c`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

| Surface | Observed declaration | Audit limit |
| --- | --- | --- |
| Listing capabilities |  | Presentation, not authorization |
| MCP service | 1 declarations | No service authority inferred |
| Portal | Human creator | No upload, attestations or publication |

Dependency and semantic secret-content review remain separate from the static package checker.
