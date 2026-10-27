"""Pure preparation rules. These assess evidence completeness, never legal approval."""
import copy
import hashlib
import json
import re
import openai_core
from datetime import datetime, timezone

SOURCES = {
    "server": "https://claude.com/docs/connectors/building/index",
    "starter": "https://claude.com/docs/connectors/building/quickstart",
    "testing": "https://claude.com/docs/connectors/building/testing",
    "policy": "https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy",
    "terms": "https://support.claude.com/en/articles/13145338-anthropic-software-directory-terms",
    "after": "https://claude.com/docs/connectors/building/after-publishing",
    "listing": "https://claude.com/docs/connectors/building/managing-your-listing",
    "sdk": "https://ts.sdk.modelcontextprotocol.io/v2/",
    "mcpdo": "https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/mcpdo",
}
SOURCE_DATE = "2026-10-13"
HOSTS = {
    "chatgpt": {"result_limit": None, "unit": "verify selected host", "timeout_ms": None},
    "codex": {"result_limit": None, "unit": "verify selected host", "timeout_ms": None},
    "responses-api": {"result_limit": None, "unit": "verify specific model and caller", "timeout_ms": None},
    "claude-ai": {"result_limit": 150000, "unit": "approximate characters", "timeout_ms": 240000},
    "claude-desktop": {"result_limit": 150000, "unit": "approximate characters", "timeout_ms": 240000},
    "claude-code": {"result_limit": 25000, "unit": "tokens; configurable", "timeout_ms": None},
    "cowork": {"result_limit": None, "unit": "verify current host settings", "timeout_ms": None},
    "claude-mobile": {"result_limit": None, "unit": "verify current host settings", "timeout_ms": None},
}
# Clause IDs map to the complete policy, including section 5, not just listing metadata.
POLICY = [
    ("0", "Continuing compliance", "owner"),
    ("1.A", "Usage, high-risk, supported regions", "owner"),
    ("1.B", "Safety boundaries", "behavior"),
    ("1.C", "Personal-data handling", "behavior"),
    ("1.D", "Context minimization", "behavior"),
    ("1.E", "Intellectual property", "owner"),
    ("1.F", "Memory/history/file extraction", "behavior"),
    ("2.A", "Unambiguous invocation", "behavior"),
    ("2.B", "Truthful capabilities", "behavior"),
    ("2.C", "Interoperability", "behavior"),
    ("2.D", "Intended external calls", "behavior"),
    ("2.E", "Other-tool independence", "behavior"),
    ("2.F", "Dynamic behavioral instructions", "behavior"),
    ("2.G", "Readable instructions", "behavior"),
    ("3.A", "Privacy disclosures", "behavior"),
    ("3.B", "Verified contacts", "owner"),
    ("3.C", "Usage and troubleshooting", "document"),
    ("3.D", "Populated review account", "behavior"),
    ("3.E", "Three working examples", "behavior"),
    ("3.F", "Resource control; connector exception", "owner"),
    ("3.G", "Maintenance", "owner"),
    ("3.H", "Terms and design guidelines", "owner"),
    ("4.A", "Financial transactions", "behavior"),
    ("4.B", "Generative media; design exception", "behavior"),
    ("4.C", "Advertising", "behavior"),
    ("5.A", "Actionable errors", "behavior"),
    ("5.B", "Response efficiency", "behavior"),
    ("5.C", "Tool-name length", "behavior"),
    ("5.D", "Remote authentication", "behavior"),
    ("5.E", "Applicable annotations", "behavior"),
    ("5.F", "Remote transport", "behavior"),
    ("5.G", "Current local dependencies", "document"),
]
TERMS = [
    ("1.i", "Distribution rights"), ("1.ii", "Law and policy"),
    ("1.iii", "Accurate information"), ("1.iv", "Own/third-party privacy"),
    ("2.i", "Indemnity"), ("2.ii", "Documentation/branding licenses"),
    ("2.iii", "Testing and metadata authorization"), ("3", "Listing discretion"),
    ("4", "Ongoing review"), ("5", "Security and quality maintenance"),
    ("6", "Vulnerability intake and investigation"), ("7", "No implied relationship or rights"),
    ("8", "Endorsements and trademarks"), ("9", "Changed terms"),
]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def problem(code, message, status="Blocked"):
    return {"code": code, "status": status, "message": message}


def validate_input(facts):
    if not isinstance(facts, dict) or facts.get("schema_version") != 1:
        raise ValueError("Expected an integration record with schema_version: 1")
    for key in ("id", "name", "source_revision"):
        if not isinstance(facts.get(key), str) or not facts[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", facts["id"]):
        raise ValueError("id must be a portable lowercase identifier")
    if not isinstance(facts.get("hosts", []), list) or any(h not in HOSTS for h in facts.get("hosts", [])):
        raise ValueError("hosts must use documented surface identifiers")
    platform = facts.get("platform", "openai")
    if platform not in ("openai", "claude"):
        raise ValueError("platform must be openai or claude; generate separate records for both")
    allowed = {"chatgpt", "codex", "responses-api"} if platform == "openai" else set(HOSTS) - {"chatgpt", "codex", "responses-api"}
    if set(facts.get("hosts", [])) - allowed:
        raise ValueError("hosts must match the explicitly selected platform")
    tools = facts.get("tools", [])
    if not isinstance(tools, list) or any(not isinstance(t, dict) or not isinstance(t.get("name"), str) for t in tools):
        raise ValueError("tools must be an exported tool inventory")
    if len({t["name"] for t in tools}) != len(tools):
        raise ValueError("Duplicate tool names")
    for key in ("cases", "boundary_tests"):
        if not isinstance(facts.get(key, []), list):
            raise ValueError(f"{key} must be a list")
    for section in ("server", "policy", "publisher", "release", "components"):
        if not isinstance(facts.get(section, {}), dict):
            raise ValueError(f"{section} must be an object")
    connection = facts.get("server", {}).get("connection", {})
    if not isinstance(connection, dict):
        raise ValueError("server.connection must be an object")
    for forbidden in ("headers", "env", "token", "password", "api_key"):
        if forbidden in connection:
            raise ValueError(f"Use environment-variable references, not connection.{forbidden}")
    host_cases = facts.get("host_cases", [])
    if not isinstance(host_cases, list) or any(not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"].strip() or "expected" not in c for c in host_cases):
        raise ValueError("host_cases require an id and expected result")
    if len({c["id"] for c in host_cases}) != len(host_cases) or set(c["id"] for c in host_cases) & set(c.get("id") for c in facts.get("cases", [])):
        raise ValueError("Host and tool case IDs must be unique across the plan")
    if facts.get("package_sha256") is not None and not re.fullmatch(r"[0-9a-f]{64}", str(facts["package_sha256"])):
        raise ValueError("package_sha256 must be a lowercase SHA-256 digest")
    return facts


def binding(facts):
    if facts.get('workflow_schema_version') == 2 and facts.get('platform','openai') == 'openai':
        return openai_core.binding(facts)
    return {"integration_id": facts["id"], "source_revision": facts["source_revision"],
            "input_sha256": digest(facts), "inventory_sha256": digest(facts.get("tools", []))}


def test_plan(facts):
    cases = copy.deepcopy(facts.get("cases", []))
    for boundary in facts.get("boundary_tests", []):
        # The creator supplies the field mapping and expectations; never guess tool semantics.
        for variant in boundary.get("variants", []):
            args = copy.deepcopy(boundary.get("arguments", {}))
            args[boundary["argument"]] = variant["value"]
            cases.append({"id": boundary["id"] + "-" + variant["name"], "tool": boundary["tool"],
                          "arguments": args, "expected": variant.get("expected"),
                          "kind": "boundary", "tags": [boundary["dimension"]],
                          "effect": boundary.get("effect", "unknown")})
    for tool in facts.get("tools", []):
        for kind in ("valid", "invalid"):
            if not any(c.get("tool") == tool["name"] and c.get("kind") == kind for c in cases):
                cases.append({"id": tool["name"] + "-" + kind, "tool": tool["name"], "kind": kind,
                              "arguments": None, "expected": None, "effect": "unknown",
                              "setup": "Supply authorized sample input, expected result, permissions and side effects."})
    ids = [c.get("id") for c in cases]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("Every test case needs a unique nonempty id")
    if any(c.get("tool") not in {t["name"] for t in facts.get("tools", [])} for c in cases):
        raise ValueError("A test case refers to a tool outside the supplied inventory")
    return {"schema_version": 1, "binding": binding(facts), "connection": facts.get("server", {}).get("connection", {}),
            "hosts": facts.get("hosts", []), "tools": facts.get("tools", []), "cases": cases,
            "source_files": facts.get("source_fingerprints", []),
            "account_setup": facts.get("account_setup", []), "sample_data": facts.get("sample_data", "Unknown"),
            "permissions": facts.get("permissions", "Unknown"), "receipt_file": facts.get("receipt_file"),
            "host_cases": copy.deepcopy(facts.get("host_cases", [])), "package_sha256": facts.get("package_sha256")}


def readiness(facts, plan):
    if facts.get("platform", "openai") == "openai":
        return openai_core.readiness(facts, plan)
    server = facts.get("server", {})
    connection = server.get("connection", {})
    findings = []
    if facts["source_revision"] == "UNRECORDED":
        findings.append(problem("source_revision_missing", "Record the actual source revision or source-file digest."))
    if not facts.get("hosts"):
        findings.append(problem("hosts_missing", "Declare intended surfaces."))
    if not connection.get("transport") or not (connection.get("url") or connection.get("command")):
        findings.append(problem("connection_missing", "Supply a real endpoint or stdio launch command."))
    if not facts.get("tools"):
        findings.append(problem("inventory_missing", "Capture the actual tools/list inventory."))
    if server.get("auth", {}).get("mode") not in ("none", "oauth", "organization-credential"):
        findings.append(problem("auth_unknown", "Record the authentication mode and its testable flow."))
    if server.get("hosting") not in ("local", "remote"):
        findings.append(problem("hosting_unknown", "Choose and record local or remote hosting."))
    if server.get("distribution") not in ("custom", "directory", "plugin", "desktop-extension"):
        findings.append(problem("distribution_unknown", "Record how users obtain this integration."))
    if server.get("hosting") == "local" and any(h in facts.get("hosts", []) for h in ("claude-ai", "claude-mobile")):
        findings.append(problem("local_unreachable", "Hosted Claude cannot connect to a local stdio process.", "Failed"))
    if server.get("hosting") == "remote" and server.get("distribution") == "directory" and not str(connection.get("url", "")).startswith("https://"):
        findings.append(problem("public_https_missing", "A directory endpoint needs public HTTPS.", "Failed"))
    unsupported = set(server.get("required_capabilities", [])) & {"sampling", "resource-subscriptions", "draft"}
    if unsupported:
        findings.append(problem("host_capability_unsupported", "Claude remote guide does not support: " + ", ".join(sorted(unsupported)), "Failed"))
    if connection.get("transport") == "sse":
        findings.append(problem("legacy_transport", "Prepare Streamable HTTP migration; verify current host support.", "Review"))
    auth = server.get("auth", {})
    auth_checks = []
    if auth.get("mode") == "oauth":
        for key in ("registration", "hosted_callback", "code_loopback", "refresh", "denied_consent", "audience", "tenant_isolation"):
            auth_checks.append({"check": key, "configured": auth.get(key, "Unknown"), "status": "Not run"})
    host_checks = []
    for host in facts.get("hosts", []):
        limit = copy.deepcopy(HOSTS[host])
        configured = server.get("host_settings", {}).get(host, {})
        limit.update(configured)
        for dimension in ("output", "timeout"):
            matched = [c["id"] for c in plan["cases"] if dimension in c.get("tags", [])]
            host_checks.append({"host": host, "dimension": dimension, "documented_settings": limit,
                                "case_ids": matched, "status": "Not run" if matched else "Blocked",
                                "reason": "Requires execution on this host; direct protocol results are separate."})
    return {"binding": binding(facts), "sources": SOURCES, "source_date": SOURCE_DATE,
            "server": server, "findings": findings, "auth_checks": auth_checks, "host_checks": host_checks,
            "readiness": "Not verified", "live_verification_performed": False,
            "next_actions": [f["message"] for f in findings] + ["Run the generated test kit and capture intended-host and server-side evidence."]}


def evidence_rows(decision, required_kind):
    evidence = decision.get("evidence", [])
    if not isinstance(evidence, list):
        return [], False
    # File verification is supplied by the I/O layer. URLs alone remain references.
    verified = [e for e in evidence if isinstance(e, dict) and e.get("verified_sha256")]
    return evidence, any(e.get("kind") == required_kind for e in verified)


def policy_matrix(facts):
    if facts.get("platform", "openai") == "openai":
        return openai_core.policy_matrix(facts)
    decisions = facts.get("policy", {})
    rows = []
    for clause, topic, kind in POLICY:
        decision = decisions.get(clause, {})
        evidence, verified = evidence_rows(decision, kind)
        applicability = decision.get("applies", "unknown")
        confirmed = bool(decision.get("confirmed_by") and decision.get("confirmed_at"))
        if applicability == "no" and decision.get("rationale") and confirmed and not decision.get("finding"):
            status = "Not applicable (creator confirmed)"
        elif applicability == "yes" and decision.get("behavior") and verified and confirmed and not decision.get("finding"):
            status = "Evidence documented"
        else:
            status = "Open"
        rows.append({"clause": clause, "topic": topic, "required_evidence_kind": kind, "applies": applicability,
                     "behavior": decision.get("behavior", "Unknown"), "rationale": decision.get("rationale", ""),
                     "evidence": evidence, "finding": decision.get("finding", ""), "status": status,
                     "confirmed_by": decision.get("confirmed_by"), "confirmed_at": decision.get("confirmed_at"),
                     "question": "Confirm applicability, actual behavior and supporting evidence for " + clause + "."})
    return {"binding": binding(facts), "source": SOURCES["policy"], "source_date": SOURCE_DATE,
            "rows": rows, "open_items": sum(r["status"] == "Open" for r in rows),
            "preparation_complete": all(r["status"] != "Open" for r in rows), "legal_compliance_certified": False}


def obligations(facts):
    if facts.get("platform", "openai") == "openai":
        return openai_core.obligations(facts)
    publisher = facts.get("publisher", {})
    rows = []
    for clause, topic in TERMS:
        decision = publisher.get("decisions", {}).get(clause, {})
        evidence, verified = evidence_rows(decision, "owner")
        complete = all(decision.get(k) for k in ("statement", "confirmed_by", "confirmed_at")) and verified
        rows.append({"clause": clause, "topic": topic, "statement": decision.get("statement", "Unknown"),
                     "confirmed_by": decision.get("confirmed_by"), "confirmed_at": decision.get("confirmed_at"),
                     "evidence": evidence, "status": "Creator confirmed" if complete else "Open"})
    return {"binding": binding(facts), "source": SOURCES["terms"], "source_date": SOURCE_DATE,
            "publisher": publisher.get("name", "Unknown"), "rows": rows,
            "preparation_complete": publisher.get("name") not in (None, "", "Unknown") and all(r["status"] != "Open" for r in rows),
            "terms_accepted_by_tool": False, "submission_performed": False}


def semver(v):
    match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", str(v))
    return tuple(map(int, match.groups())) if match else None


def release_plan(facts, plan):
    if facts.get("platform", "openai") == "openai":
        return openai_core.release_plan(facts, plan)
    release = facts.get("release", {})
    before, after = release.get("before", {}), release.get("after", {})
    changes, findings = [], []
    for unit in ("server", "package", "listing"):
        left, right = before.get(unit, {}), after.get(unit, {})
        for key in sorted(set(left) | set(right)):
            if left.get(key) != right.get(key):
                changes.append({"unit": unit, "field": key, "before": left.get(key), "after": right.get(key)})
    for unit, key in (("listing", "slug"), ("package", "name")):
        previous, following = before.get(unit, {}).get(key), after.get(unit, {}).get(key)
        if previous and following != previous:
            findings.append(problem("identity_changed", f"Preserve {unit}.{key}: {previous}.", "Failed"))
    if any(c["unit"] == "package" for c in changes):
        old, new = semver(before.get("package", {}).get("version")), semver(after.get("package", {}).get("version"))
        if old is None or new is None or new <= old:
            findings.append(problem("version_not_increased", "Raise the package version for changed files.", "Failed"))
    for key in ("owner", "support_contact", "vulnerability_contact", "rollout", "rollback", "health_source"):
        if not release.get(key):
            findings.append(problem("release_input_missing", "Supply release." + key))
    if not before or not after:
        findings.append(problem("release_identity_missing", "Record current and proposed server/package/listing identities."))
    for unit, keys in (("server", ("endpoint", "revision")), ("package", ("name", "version", "tracked_ref")), ("listing", ("kind", "slug"))):
        for label, state in (("before", before), ("after", after)):
            value = state.get(unit, {})
            if value.get("applicable") is False and value.get("reason"):
                continue
            for key in keys:
                if not value.get(key):
                    findings.append(problem("release_identity_missing", f"Supply {label}.{unit}.{key} or an explicit non-applicability reason."))
    server_changes = [c for c in changes if c["unit"] == "server"]
    listing_changes = [c for c in changes if c["unit"] == "listing"]
    package_changes = [c for c in changes if c["unit"] == "package"]
    listing_kind = after.get("listing", {}).get("kind", before.get("listing", {}).get("kind"))
    if any(c["field"] == "tracked_ref" for c in package_changes):
        findings.append(problem("tracked_ref_review", "Update the tracked branch/tag in the portal explicitly before relying on a push.", "Review"))
    listing_route = "package-metadata" if listing_kind == "plugin" else "portal-review"
    listing_action = ("Update plugin.json/README and publish a package version; inspect reviewer text overrides. Settings controls surfaces, contact and data collection."
                      if listing_kind == "plugin" else "Submit connector listing changes for review; display-name changes require re-review. Preserve the permanent slug.")
    if any(c["field"] == "tools" for c in server_changes) and not any(c["field"] == "tools" for c in listing_changes):
        findings.append(problem("listing_tools_review", "Reconcile displayed listing tools with the changed server inventory.", "Review"))
    return {"binding": binding(facts), "sources": {k: SOURCES[k] for k in ("after", "listing")}, "source_date": SOURCE_DATE,
            "before": before, "after": after, "changes": changes, "findings": findings,
            "actions": {
                "server": "Deploy server changes; prepare reviewed listing edits if displayed tools change." if server_changes else "No server change recorded.",
                "package": "Push tracked ref, inspect validation/security scan; keep last published version until replacement publishes." if package_changes else "No package change recorded.",
                "listing": listing_action if listing_changes else "No listing change recorded.",
            },
            "listing_update_route": listing_route,
            "health_plan": {"source": "Plugin Usage tab" if listing_kind == "plugin" else "Connector health and usage",
                            "checks": ["Reject Preview/sample figures", "Record UTC data-through date and window", "Compare version adoption, load errors, tool errors and latency"]
                            if listing_kind == "plugin" else ["Record request-error denominator and observation window", "Keep tool errors separate", "Treat suppressed/no-data values as unknown"],
                            "schedule": release.get("health_cadence", "Owner to configure explicitly"), "automation_configured": False},
            "regression_case_ids": [c["id"] for c in plan["cases"]],
            "rollout": release.get("rollout", []), "rollback": release.get("rollback", []),
            "owner": release.get("owner", "Unknown"), "support_contact": release.get("support_contact", "Unknown"),
            "vulnerability_contact": release.get("vulnerability_contact", "Unknown"),
            "health_source": release.get("health_source", "Unknown"),
            "delisting": {"plugin": "Portal: Delist plugin; Settings: Relist plugin to request restoration.",
                          "connector": "Prepare a delisting request to mcp-review@anthropic.com; sending requires authorization."},
            "ready_for_owner_review": not findings, "deployment_performed": False,
            "continuous_monitoring_configured": False}


def health(snapshot, now=None):
    now = now or datetime.now(timezone.utc)
    if not isinstance(snapshot, dict):
        raise ValueError("Health snapshot must be an object")
    if snapshot.get("preview") or snapshot.get("suppressed") or snapshot.get("requests") in (None, 0):
        return {"status": "Unknown", "reason": "Preview, suppressed or missing data is not zero errors."}
    if snapshot.get("scope") != "portal-request-errors":
        return {"status": "Unknown", "reason": "Use the portal request-error denominator; other metrics have different scopes."}
    requests, errors = snapshot.get("requests"), snapshot.get("request_errors")
    if type(requests) is not int or type(errors) is not int or requests <= 0 or not 0 <= errors <= requests:
        raise ValueError("Invalid request/error counts")
    try:
        observed = datetime.fromisoformat(snapshot["observed_at"].replace("Z", "+00:00"))
        if observed.tzinfo is None:
            raise ValueError("Timezone required")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("observed_at must be a timezone-aware timestamp") from exc
    age = (now - observed).total_seconds() / 3600
    if age < 0 or age > snapshot.get("max_age_hours", 48):
        return {"status": "Unknown", "reason": "Snapshot outside the configured freshness window (default 48h, local policy)."}
    rate = errors / requests * 100
    return {"status": "Degraded" if rate > 5 else "Attention" if rate > 2 else "Healthy",
            "request_error_percent": rate, "scope": snapshot["scope"], "window": snapshot.get("window", "Unknown"),
            "requests": requests, "observed_at": snapshot["observed_at"], "continuous_monitoring": False}

