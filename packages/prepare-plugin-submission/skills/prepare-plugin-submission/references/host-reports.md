# ChatGPT and Codex report ingestion

This is an evidence-ingestion contract. It does not automate either product or
authenticate the identity of the external observer. Portal upload, review and
publication are human handoffs.

Use [host-report.schema.json](../schemas/host-report.schema.json). Each report
has `schema_version: 1`, `report_kind: product-host`, `host: chatgpt|codex`,
`origin: observed|synthetic`, the exact generated plan `binding`, the exact
archive `package_sha256`, observer, timezone-aware observation time, environment
versions and case rows. Use `unknown` explicitly for an unavailable version.

Declare skill workflows in the input's `host_cases` with unique `id`, `prompt`
and `expected`. Tool cases remain in `cases`; IDs cannot overlap. Declare the
intended hosts and actual package digest before creating the pack. A report is
accepted only for a declared host and case. Expectations must match the plan.

Each case supplies a local JSON capture via `evidence.file` plus its SHA-256.
Paths must remain within the report directory without symlinks. A capture
contains the same binding, package digest, host, origin, `case_id`, expected
result and status. Include observed behavior, an assessment rationale, actual
`tool_calls`, and `side_effects` with expected/observed values. Empty calls are
valid for a skill workflow using no tool. Never fabricate a capture from a plan.

Run:

```sh
python3 <skill>/scripts/prepare_workflow.py assess <pack> --report <host-report.json>
```

The assessor checks shape, binding, declared cases, expectations, artifact paths
and bytes. It retains externally supplied observation claims separately from
direct protocol runs. It does not establish that an observer really used the
claimed host. Treat capture authenticity and human grading as separate trust
boundaries. Use raw host exports or a human-reviewed trace as the underlying
observation; keep credentials and unrelated user data out of the shared capture.

Synthetic reports exercise ingestion and integrity only. They increment
`synthetic_cases_validated` and never satisfy actual-host coverage or publication
states. Failed, blocked, missing and stale observations remain visible. Passing
static preflight does not require a real host or a portal action.
