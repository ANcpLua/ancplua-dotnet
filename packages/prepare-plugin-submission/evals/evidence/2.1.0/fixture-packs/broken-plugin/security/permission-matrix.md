# Permission matrix

Target: fixture-plugin not-semver

Source revision: `content-sha256:3880e1215cfeb2064d7e9207c1842f8b02b58fe43bc2215809958eaa06d58795`

Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.

| Surface | Observed declaration | Audit limit |
| --- | --- | --- |
| Listing capabilities |  | Presentation, not authorization |
| MCP service | 0 declarations | No service authority inferred |
| Portal | Human creator | No upload, attestations or publication |

Dependency and semantic secret-content review remain separate from the static package checker.
