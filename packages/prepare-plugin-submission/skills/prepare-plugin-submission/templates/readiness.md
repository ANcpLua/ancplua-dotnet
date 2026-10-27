# Submission evidence

Integration / source revision / archive SHA-256:
Target(s) and intended surfaces:
Track these independently (attach evidence rather than deriving later states):
- Local checks: Not run / Passed / Failed / Blocked / Not applicable
- Behavioral evaluation: Not run / Passed / Failed / Blocked / Not applicable
- Live host verification: Not run / Passed / Failed / Blocked / Not applicable
- Review materials: Incomplete / Complete
- Draft / submission: Not uploaded / Draft uploaded / Submitted / Under review
- Approval: Not approved / Approved / Rejected
- Publication: Not published / Published
Source URLs checked and date:

| Requirement | Origin | Expected | Observed | Status | Evidence / version |
| --- | --- | --- | --- | --- | --- |

Use Observed, Creator confirmed, or Unknown for the origin of facts.
Use Passed, Failed, Blocked, Not run, or Not applicable for each check. Never store credentials.

## Artifacts

- Source and exact package:
- Listing and published policy/support pages:
- Review cases and real run evidence:
- Recording URL and playback/access check:
- Applicable screenshots and what they prove:
- Native validator and scan results for this version:
- Saved plugin ID/release ID, or directory draft/version:

## Remaining steps

State each concrete gap, who can resolve it, and which work is independent.
Keep public submission and publication distinct from preparation/private install.

## Functional coverage, separate from package validation

| Intended surface | Supported components | Loading observed | Workflow cases run | Plugin vs baseline result | Evidence / revision |
| --- | --- | --- | --- | --- | --- |

| Exposed connector tool | Valid-input success | Invalid-input error | MCP Inspector run | Intended product-host run | Evidence / revision |
| --- | --- | --- | --- | --- | --- |

Track every exposed tool, not just the three example use cases. Record expected
absence of unsupported components as not applicable. A passing package scan or
local eval score does not establish universal model/surface coverage or approval.

## Exact execution matrix

| Case ID | Submitted review case? | Intended host surface | Supported components | Source revision | Package SHA-256 | Expected | Observed | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Repeat rows for each case and supported surface. Changed artifacts invalidate
related claims until checked again. OpenAI functional verification requires
all applicable submitted cases to pass on each claimed intended surface as an
engineering gate; current submission case requirements are in O2. Claude
connector coverage requires evidence for every tool; its plugin testing covers
intended surfaces, not a universal all-models pass percentage. Blocked/missing
runs prevent a host-verified claim but do not prevent independent preparation.

Model and runner versions / grader version / fixture hash / tool grants:
Expected cases and repeats / executed / Passed / Failed / Blocked / Not run:
Per-tool details: [worksheet](tool-review.md).


## Requirement authority and modern protocol

| Requirement ID | Classification | Applicability | Source URL | Actually retrieved at | Protocol version | Transport/capability | Implementation revision | Case | Observed result | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Classify official requirements, engineering recommendations and unresolved claims
separately. Leave retrieval dates null until a page is actually read. Record SDK
package versions, requested era, observed era and exact protocol revision as
separate fields. A compatibility plugin manifest does not imply legacy MCP.

Lifecycle: Prepared / Locally validated / Host verified / Review-ready /
Submitted / Approved / Published. Never derive a later state from an earlier one.
