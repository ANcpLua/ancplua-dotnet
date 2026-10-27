# Revised fixture verification

All three raw fixtures were audited with the public submission profile in this fresh directory. Desktop used the desktop-only route and the supplied synthetic allowlist confirmation.

| Target | Audit exit | Local result | Integrity exit |
| --- | --- | --- | --- |
| broken-plugin.zip | 1 | Expected four package errors retained | 0 |
| desktop-stdio | 0 | Synthetic static preflight passed | 0 |
| review-prep | 0 | Synthetic static preflight passed | 0 |

The three generated packs retain source bindings and target facts. The targeted source/document comparisons all passed; see [comparisons.json](comparisons.json). The checks confirm exact stdio command/args/cwd retention, remote URL and declared anonymous auth retention, absence of false missing-connection blockers, conditional skill/desktop/remote requirement rows, copied five-positive/three-negative definitions, explicitly untested video access, and unchanged external lifecycle states.

## Requested handoff fixes confirmed

- Desktop demo guidance explicitly says remote recording and five/three review-case requirements do not apply. It calls for a clean local installation test without claiming one occurred.
- Desktop review-cases.json is Not applicable.
- Remote review-prep retains all eight definitions and the synthetic recording URL, with execution and playback unverified.
- Broken-package delivery requires repair and recheck before installation or submission.
- Demo sentence spacing is corrected.

## Remaining finding

One minor generic-text mismatch remains: broken-plugin-audit/submission/reviewer-access.md tells the creator to run a packaged scenario set, but the raw ZIP has only plugin.json and skills/broken/SKILL.md. Exact evidence and the suggested wording correction are in [findings.json](findings.json). This does not change the expected package rejection or the successful targeted fixes above.

## Evidence and scope

[executions.json](executions.json) preserves exact argument arrays, working directory, environment overrides, exit codes and raw stdout/stderr paths. [auditor-source-binding.json](auditor-source-binding.json) identifies the implementation inspected. All generated outputs remain outside the source package.

No fixture endpoint was contacted, target server executed, implementation edited, plugin installed, fixture uploaded, review submitted or publication performed. Synthetic confirmation does not establish real partner eligibility. Static checks and artifact integrity do not establish runtime negotiation, real tool behavior, host execution, authentication, accessible URLs/video, legal facts or directory acceptance. These were local synthetic checks; current policy pages were not independently refreshed.

Next action: the maintainer can replace the unconditional scenario-set wording with guidance based on the target’s observed test assets. Any real installation, portal upload, review and publication remain external human handoffs.
