# Permission matrix

Target: prepare-plugin-submission 2.0.1

Source revision: `content-sha256:138cb12bca1eef736ea697f97e8b0865a4a5ff17cd613bfc64a6487f77fb808c`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

| Surface | Observed declaration | Audit limit |
| --- | --- | --- |
| Listing capabilities | Read, Write | Presentation, not authorization |
| MCP service | 0 declarations | No service authority inferred |
| Portal | Human creator | No upload, attestations or publication |

Dependency and semantic secret-content review remain separate from the static package checker.
