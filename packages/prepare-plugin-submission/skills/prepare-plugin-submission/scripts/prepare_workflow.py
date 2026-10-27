#!/usr/bin/env python3
"""Generate executable integration-specific preparation packs and assess their evidence."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import urlsplit, parse_qs

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("workflow_core", HERE / "workflow_core.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
ASSETS = HERE.parent / "assets/connector-kit"
MODES = ("readiness", "tests", "policy", "obligations", "postlaunch")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load(path):
    if path.is_symlink() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("Input must be a regular JSON file below 8 MiB")
    return json.loads(path.read_text())


def empty_output(path):
    if path.is_symlink() or (path.exists() and (not path.is_dir() or any(path.iterdir()))):
        raise ValueError("Output must be a new or empty directory; existing work is never overwritten")
    path.mkdir(parents=True, exist_ok=True)


def cell(value):
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("\n", "<br>")


def render(title, value):
    """A reviewable Markdown view of every machine-readable field, with no hidden decisions."""
    lines = ["# " + title, "", "Generated from the accompanying integration record. Supplied facts are not execution evidence.", ""]
    for key, item in value.items():
        lines.extend(["## " + key.replace("_", " ").title(), ""])
        if isinstance(item, list) and item and all(isinstance(x, dict) for x in item):
            keys = list(dict.fromkeys(k for row in item for k in row))
            lines += ["| " + " | ".join(cell(k) for k in keys) + " |", "| " + " | ".join("---" for _ in keys) + " |"]
            lines += ["| " + " | ".join(cell(row.get(k, "")) for k in keys) + " |" for row in item]
        elif isinstance(item, (dict, list)):
            lines += ["```json", json.dumps(item, indent=2, ensure_ascii=False).replace("```", "` ` `"), "```"]
        else:
            lines.append(cell(item))
        lines.append("")
    return "\n".join(lines)


def check_connection(connection):
    if connection.get("transport") not in (None, "stdio", "http", "sse"):
        raise ValueError("connection.transport must be stdio, http or sse")
    if "args" in connection and (not isinstance(connection["args"], list) or any(not isinstance(a, str) for a in connection["args"])):
        raise ValueError("connection.args must be an array of strings, never a shell command")
    for name in ("headers_from_env", "env_from"):
        mapping = connection.get(name, {})
        if not isinstance(mapping, dict) or any(not isinstance(v, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", v) for v in mapping.values()):
            raise ValueError(name + " maps field names to environment variable names")
    if connection.get("url"):
        url = urlsplit(connection["url"])
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
            raise ValueError("Endpoint must be HTTP(S) without embedded credentials")
        if set(k.lower() for k in parse_qs(url.query)) & {"token", "api_key", "key", "access_token", "secret"}:
            raise ValueError("Use environment references, not credentials in endpoint URLs")


def portable_evidence(facts, input_root, output):
    """Verify and copy supplied evidence, never treating a URL as a verified behavioral record."""
    for decisions in (facts.get("policy", {}), facts.get("publisher", {}).get("decisions", {})):
        for decision in decisions.values():
            if not isinstance(decision, dict):
                raise ValueError("Review decisions must be objects")
            for evidence in decision.get("evidence", []):
                evidence.pop("verified_sha256", None)
                if not evidence.get("path"):
                    continue
                path = input_root / evidence["path"]
                if not path.is_file() or path.is_symlink() or path.stat().st_size > 4 * 1024 * 1024:
                    evidence["verification"] = "Missing, symlink, or larger than 4 MiB"
                    continue
                if path.name in (".env", "credentials", "secrets.json") or path.suffix in (".pem", ".key"):
                    raise ValueError("Do not package secret files as review evidence")
                data = path.read_bytes()
                sha = hashlib.sha256(data).hexdigest()
                if evidence.get("sha256") and evidence["sha256"] != sha:
                    raise ValueError("Evidence hash mismatch: " + str(path))
                target = Path("evidence") / (sha[:16] + "-" + path.name)
                (output / target).parent.mkdir(exist_ok=True)
                (output / target).write_bytes(data)
                evidence.update(path=target.as_posix(), verified_sha256=sha)


def copy_runtime(output, starter=False):
    for path in ASSETS.rglob("*"):
        if path.is_symlink():
            raise ValueError("Runtime assets must not contain symlinks")
        if path.is_file() and not any(p in ("node_modules", "build", "__pycache__") for p in path.relative_to(ASSETS).parts):
            if path.name == "server.ts" and not starter:
                continue
            target = output / path.relative_to(ASSETS)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    if not starter:
        package = load(output / "package.json")
        package["scripts"].pop("start", None)
        write_json(output / "package.json", package)


def kit_readme():
    return """# Integration-specific connector test kit

Install with `npm ci`, then `npm run build`. Inspect `plan.json` before execution.
Fill missing cases in the source integration record and regenerate the pack.
Never replace real credentials in that record: use the named environment variables.

Run `npm test -- --engine sdk --era modern --report results/sdk.json`, then
`npm test -- --engine mcpdo --era modern --report results/mcpdo.json`.
Use `--era legacy` for legacy claims and `--era auto` to test fallback.
The mcpdo adapter uses the official Inspector 2.10.1 through npm exec.
Its first use may download that package; `--mcpdo /path/to/mcpdo` selects an existing binary.

Only read-only cases run by default. `--allow-writes` opts into cases explicitly
marked write; `--allow-destructive` separately enables destructive cases. Unknown
effects remain blocked. Use disposable, authorized sample data and inspect the
per-case setup and expected permissions. A pending elicitation remains pending
unless that case supplies an explicit `elicitation_response`.

For a real Claude Code call, use `--engine claude-code --allow-model-calls`.
This requires Claude Code and account access; it spends model usage, capped at
$2 per case by default (`--model-budget`). Only valid/workflow cases run there.
It uses per-command MCP configuration and disables built-in tools. Captured
tool-use and tool-result blocks, not the model's prose, determine the result.
Other Claude surfaces need their own real-host evidence and remain Not run here.

`--receipts /path/to/receipts.jsonl` correlates fresh server-side records containing
`timestamp`, `tool`, and `arguments` with executed cases. Without it, server-side
confirmation remains Not run. Invalid inputs rejected before the handler do not
produce handler receipts. Store these files with the same protection as test data.

Reports distinguish execution, assertions, pending/blocked work, and server receipt.
Raw local evidence is written beside the report with restricted permissions.
Exit 0 means all selected cases passed; 1 means a failure; 2 means blocked/not run.
No report means no completed test run. Running these tests does not submit or publish.
"""


def prepare(input_path, output, workflows):
    facts = core.validate_input(load(input_path))
    facts = copy.deepcopy(facts)
    if facts.get("platform", "openai") == "openai" and "requirement_catalog" not in facts:
        facts["requirement_catalog"] = load(HERE.parent / "references/requirements.json")["requirements"]
    connection = facts.get("server", {}).get("connection", {})
    check_connection(connection)
    facts["source_fingerprints"] = []
    for name in facts.get("source_files", []):
        path = (input_path.parent / name).resolve()
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing source file: " + name)
        facts["source_fingerprints"].append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    if connection.get("transport") == "stdio" and not facts.get("audit_observation"):
        connection["cwd"] = str((input_path.parent / connection.get("cwd", ".")).resolve())
    empty_output(output)
    portable_evidence(facts, input_path.parent, output)
    plan = core.test_plan(facts)
    write_json(output / "integration.json", facts)
    producers = {"readiness": lambda: core.readiness(facts, plan), "policy": lambda: core.policy_matrix(facts),
                 "obligations": lambda: core.obligations(facts), "postlaunch": lambda: core.release_plan(facts, plan)}
    for mode in workflows:
        folder = output / mode
        folder.mkdir()
        if mode == "tests":
            copy_runtime(folder)
            write_json(folder / "plan.json", plan)
            write_json(folder / "inventory.json", {"tools": facts.get("tools", [])})
            (folder / "README.md").write_text(kit_readme())
        else:
            report = producers[mode]()
            write_json(folder / "record.json", report)
            (folder / "review.md").write_text(render(mode, report))
            if mode == "postlaunch" and facts.get("platform", "openai") == "claude":
                shutil.copyfile(HERE / "check_health.py", folder / "check_health.py")
                shutil.copyfile(HERE / "workflow_core.py", folder / "workflow_core.py")
                shutil.copyfile(HERE / "openai_core.py", folder / "openai_core.py")
                write_json(folder / "health-input.json", {"scope": "portal-request-errors", "observed_at": None,
                    "window": "Supply portal measurement window", "requests": None, "request_errors": None, "preview": True})
                write_json(folder / "listing-update.json", facts.get("release", {}).get("after", {}).get("listing", {}))
    if facts.get("platform", "openai") == "openai":
        for name, data in core.openai_core.handoff_records(facts, plan).items():
            write_json(output / name, data)
        if facts.get("audit_observation"):
            import audit_target
            for name, content in audit_target.completed_documents(facts).items():
                target = output / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            if facts.get('workflow_schema_version')==2:
                draft=facts['understanding_draft'];choices=facts.get('confirmed_choices',{})
                selected=set(choices.get('task_ids',[]))
                notes=output/'submission/reviewer-notes.md'
                notes.write_text('# Intended workflows\n\n'+draft['summary']+'\n\n'+
                    '\n'.join('- '+t['label']+': '+t['expected'] for t in draft['tasks'] if t['id'] in selected)+
                    '\n\nSource: '+facts['source_revision']+'\n\nSelections: '+core.digest(choices)+
                    '\n\nThese notes describe confirmed intent. Actual host outcomes are recorded separately.\n')
            write_json(output / "evidence/source-inspection.json", {"binding": core.binding(facts), "observed": facts["audit_observation"], "files": facts["audit_inventory"]})
            write_json(output / "evidence/package-check.json", facts["audit_package_report"])
            for requirement in core.openai_core.requirements(facts):
                write_json(output / ("evidence/requirements/" + requirement["requirement_id"] + ".json"), requirement)
        for name in ("architecture/assessment.md", "security/auth-architecture.md", "security/authorization-architecture.md", "security/permission-matrix.md", "submission/listing.md", "submission/reviewer-access.md", "submission/demo-plan.md", "submission/release-notes.md", "operations/observability.md", "operations/health-checks.md", "operations/deployment.md", "operations/rollback.md", "operations/incident-response.md"):
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                continue
            target.write_text("# " + target.stem.replace("-", " ").title() + "\n\nStatus: Not run. Complete from inspected source and observed evidence.\nDo not put secrets or reviewer passwords in this file.\n")
    write_json(output / "plan.json", plan)
    manifest = {"schema_version": 1, "binding": core.binding(facts), "workflows": workflows,
                "status": "Generated; execution and publisher decisions are separate",
                "files": {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(output.rglob("*")) if p.is_file()}}
    write_json(output / "manifest.json", manifest)
    return manifest


def starter(output, name, platform="openai"):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", name):
        raise ValueError("Use a portable lowercase starter name")
    empty_output(output)
    copy_runtime(output, starter=True)
    facts = {"schema_version": 1, "id": name, "name": name, "source_revision": "starter-2.0.0", "platform": platform, "hosts": ["chatgpt", "codex"] if platform == "openai" else ["claude-code"],
        "server": {"hosting": "local", "distribution": "custom", "auth": {"mode": "none"},
                   "required_capabilities": ["tools"], "connection": {"transport": "stdio", "command": "node", "args": ["build/server.js"], "cwd": "."}},
        "tools": [{"name": "add_numbers", "title": "Add two numbers", "description": "Return the sum of two finite numbers.",
                   "inputSchema": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}, "required": ["a", "b"]},
                   "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}}],
        "sample_data": "Synthetic numeric values only", "permissions": "No external service or user data", "account_setup": ["No account for local protocol tests", "Intended product account for real-host verification"],
        "cases": [{"id": "sum-valid", "tool": "add_numbers", "kind": "valid", "effect": "read", "arguments": {"a": 2, "b": 3}, "expected": {"kind": "success", "structured": {"sum": 5}}},
                  {"id": "sum-invalid", "tool": "add_numbers", "kind": "invalid", "effect": "read", "arguments": {"a": "invalid", "b": 3}, "expected": {"kind": "tool_error"}}]}
    core.validate_input(facts)
    facts["source_fingerprints"] = [{"path": name, "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest()} for name in ("src/server.ts", "package-lock.json")]
    facts["source_revision"] = core.digest(facts["source_fingerprints"])
    write_json(output / "integration.json", facts)
    write_json(output / "plan.json", core.test_plan(facts))
    write_json(output / "production-gaps.json", {"status": "Local starter only", "remaining": ["Identity provider and authorization", "Public HTTPS hosting", "Intended hosted-surface tests", "Policy/publisher review", "Directory submission"], "runtime_verified": False})
    (output / "README.md").write_text(kit_readme() + "\nStart stdio with `npm start`; for loopback HTTP use `npm start -- --http` (port 3000).\nSet `SUBMISSION_RECEIPTS_FILE` for sample-data receipts. Public exposure is not configured.\n")
    return {"status": "Starter generated; run its acceptance commands", "binding": core.binding(facts)}


def check_bundle(output):
    manifest = load(output / "manifest.json")
    findings = []
    for name, sha in manifest["files"].items():
        path = output / name
        if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink() or not path.is_file():
            findings.append(core.problem("artifact_missing", name, "Failed"))
        elif hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            findings.append(core.problem("artifact_changed", name, "Failed"))
    return {"status": "Failed" if findings else "Artifact integrity passed", "findings": findings,
            "live_verification": "Not implied", "binding": manifest["binding"]}


def assess(output, reports):
    integrity = check_bundle(output)
    if integrity["findings"]:
        return integrity
    facts, plan = load(output / "integration.json"), load(output / "plan.json")
    findings, accepted, synthetic_rows = [], [], []
    if not facts.get("hosts"):
        findings.append(core.problem("hosts_missing", "Declare intended hosts before claiming coverage."))
    for path in reports:
        report = load(path)
        if report.get("report_kind") == "product-host":
            import host_reports
            try:
                rows = host_reports.validate_report(report, path, plan)
                if report["origin"] == "synthetic":
                    synthetic_rows.extend(rows)
                else:
                    accepted.extend(r for r in rows if r["status"] == "Passed")
                    if any(r["status"] == "Failed" for r in rows):
                        findings.append(core.problem("host_run_failed", str(path), "Failed"))
            except ValueError as exc:
                findings.append(core.problem("invalid_host_report", str(exc), "Failed"))
            continue
        if report.get("binding") != plan["binding"]:
            findings.append(core.problem("stale_evidence", str(path), "Failed")); continue
        allowed_surfaces = {"sdk": "direct-protocol", "mcpdo": "direct-protocol", "inspector": "direct-protocol", "claude-code": "claude-code"}
        if report.get("surface") != allowed_surfaces.get(report.get("engine")) or report.get("engine") not in allowed_surfaces:
            findings.append(core.problem("unverified_host_evidence", str(path), "Failed")); continue
        if report.get("status") == "Failed":
            findings.append(core.problem("run_failed", str(path), "Failed"))
        for row in report.get("cases", []):
            if row.get("status") != "Passed":
                continue
            evidence = row.get("evidence", {})
            file = path.parent / evidence.get("file", "")
            if not file.is_file() or file.is_symlink() or hashlib.sha256(file.read_bytes()).hexdigest() != evidence.get("sha256"):
                findings.append(core.problem("evidence_missing", row.get("id", "unknown"), "Failed")); continue
            artifact = load(file)
            case = next((c for c in plan["cases"] if c["id"] == row.get("id")), None)
            if not case or artifact.get("binding") != plan["binding"] or artifact.get("case_id") != case["id"] or artifact.get("arguments") != case["arguments"] or not artifact.get("assertions") or not all(a.get("passed") is True for a in artifact["assertions"]):
                findings.append(core.problem("evidence_mismatch", row.get("id", "unknown"), "Failed")); continue
            accepted.append({**row, "engine": report.get("engine"), "surface": report.get("surface"), "era": report.get("negotiated_era")})
    coverage = []
    for case in plan["cases"]:
        for engine in ("sdk", "mcpdo"):
            if case.get("engines") and engine not in case["engines"]:
                continue
            hits = [r for r in accepted if r["id"] == case["id"] and r["engine"] == engine]
            coverage.append({"case": case["id"], "tool": case["tool"], "surface": "direct-protocol", "engine": engine, "status": "Passed" if hits else "Not run"})
    for host in facts.get("hosts", []):
        for case in plan.get("host_cases", []):
            hits = [r for r in accepted if r["id"] == case["id"] and r["surface"] == host]
            coverage.append({"case": case["id"], "surface": host, "status": "Passed" if hits else "Not run",
                             "verification": "External observer claims with checked artifact integrity"})
        for tool in facts.get("tools", []):
            hits = [r for r in accepted if r.get("tool") == tool["name"] and r["surface"] == host and r.get("kind") in ("valid", "workflow")]
            coverage.append({"tool": tool["name"], "surface": host, "status": "Passed" if hits else "Not run"})
    for tool in facts.get("tools", []):
        coverage.append({"tool": tool["name"], "surface": "server-side confirmation", "status": "Passed" if any(r.get("tool") == tool["name"] and r.get("server_confirmation") == "Passed" for r in accepted) else "Not run"})
    ready = bool(coverage) and all(r["status"] == "Passed" for r in coverage) and not findings
    return {"binding": plan["binding"], "status": "Verified" if ready else "Incomplete", "coverage": coverage,
            "verified_scope": "Selected execution cases and declared surfaces; not overall submission approval",
            "findings": findings, "synthetic_cases_validated": len(synthetic_rows),
            "synthetic_is_host_verification": False,
            "host_report_provenance": "Externally supplied observations; observer identity and actual host execution are not independently authenticated",
            "submission_performed": False, "policy_and_publisher_decisions": "Review their separate records"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("audit", help="Inspect a loaded target; produce source-backed local preflight evidence")
    p.add_argument("--source", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    p.add_argument("--synthetic", action="store_true")
    p.add_argument("--profile", choices=("package", "submission"), default="package")
    p.add_argument("--submission-route", choices=("remote", "desktop-only"), default="remote")
    p.add_argument("--desktop-allowlist", type=Path)
    p = sub.add_parser("init")
    p.add_argument("--output", type=Path, required=True); p.add_argument("--id", required=True)
    p.add_argument("--inventory", type=Path)
    p.add_argument("--platform", choices=("openai", "claude"), default="openai")
    p = sub.add_parser("prepare")
    p.add_argument("--input", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workflow", choices=("all",) + MODES, default="all")
    p = sub.add_parser("starter"); p.add_argument("--output", type=Path, required=True); p.add_argument("--name", default="submission-starter"); p.add_argument("--platform", choices=("openai", "claude"), default="openai")
    p = sub.add_parser("check"); p.add_argument("bundle", type=Path)
    p = sub.add_parser("assess"); p.add_argument("bundle", type=Path); p.add_argument("--report", type=Path, action="append", default=[]); p.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "audit":
            source_root = args.source.resolve()
            if args.output.resolve() == source_root or (source_root.is_dir() and source_root in args.output.resolve().parents):
                raise ValueError("Write audit output outside the inspected target")
            import audit_target
            import check_package
            catalog = load(HERE.parent / "references/requirements.json")["requirements"]
            allowlist = None
            if args.desktop_allowlist:
                if args.desktop_allowlist.is_symlink() or not args.desktop_allowlist.is_file() or args.desktop_allowlist.stat().st_size > 65536:
                    raise ValueError("Allowlist record must be a regular JSON file below 64 KiB")
                allowlist = json.loads(args.desktop_allowlist.read_text(), object_pairs_hook=check_package.no_duplicates)
            facts = audit_target.inspect_target(args.source, catalog, submission_route=args.submission_route,
                                               allowlist=allowlist, synthetic=args.synthetic, profile=args.profile)
            # Use the ordinary generator on the inspected record. Its temp input is never published.
            import tempfile
            with tempfile.TemporaryDirectory() as directory:
                input_file = Path(directory) / "target.json"
                write_json(input_file, facts)
                result = prepare(input_file, args.output.resolve(), ["readiness", "policy", "obligations", "postlaunch"])
                result["target_preflight_status"] = facts["audit_package_report"]["status"]
                result["findings"] = [i for i in facts["audit_package_report"]["issues"] if i["severity"] == "error"]
        elif args.command == "init":
            if args.output.exists(): raise ValueError("Integration record already exists")
            inventory = load(args.inventory) if args.inventory else {"tools": []}
            facts = {"schema_version": 1, "id": args.id, "name": args.id, "source_revision": "UNRECORDED", "hosts": [],
                "server": {"connection": {}, "auth": {"mode": "unknown"}, "required_capabilities": []},
                "tools": inventory.get("tools", []), "cases": [], "boundary_tests": [], "account_setup": [],
                "sample_data": "Unknown", "permissions": "Unknown", "release": {},
                "policy": {c: {"applies": "unknown", "behavior": "", "rationale": "", "evidence": []} for c, _, _ in core.POLICY},
                "publisher": {"name": "Unknown", "decisions": {c: {"statement": "", "evidence": []} for c, _ in core.TERMS}}}
            facts["platform"] = args.platform
            if args.platform == "openai":
                facts["policy"] = {}
                facts["publisher"] = {"name": "Unknown", "decisions": {}}
                facts["components"] = {"mcp": None, "skills": None, "ui": None}
            core.validate_input(facts); write_json(args.output, facts)
            result = {"status": "Integration record initialized", "path": str(args.output)}
        elif args.command == "prepare": result = prepare(args.input.resolve(), args.output.resolve(), list(MODES) if args.workflow == "all" else [args.workflow])
        elif args.command == "starter": result = starter(args.output.resolve(), args.name, args.platform)
        elif args.command == "check": result = check_bundle(args.bundle)
        else:
            if args.output and args.output.exists(): raise ValueError("Assessment output already exists")
            result = assess(args.bundle, args.report)
            if args.output: write_json(args.output, result)
        print(json.dumps(result, indent=2))
        return 1 if result.get("findings") else 2 if result.get("status") == "Incomplete" else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "Input error", "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

