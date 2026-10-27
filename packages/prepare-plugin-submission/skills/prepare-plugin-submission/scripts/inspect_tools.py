#!/usr/bin/env python3
"""Inspect an exported tools/list response offline and start a per-tool review record."""
import argparse, hashlib, json, sys
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

_core_spec = spec_from_file_location(
    "submission_studio_core", Path(__file__).with_name("package_core.py")
)
_core = module_from_spec(_core_spec)
_core_spec.loader.exec_module(_core)
no_duplicates = _core.no_duplicates


def inspect_inventory(data, target, source_hash):
    tools = data.get("tools") if isinstance(data, dict) else None
    if not isinstance(tools, list):
        raise ValueError("Expected a tools/list export with a tools array")
    issues = []
    records = []
    seen = set()

    def issue(code, name, field):
        issues.append({"code": code, "tool": name, "field": field})

    for n, tool in enumerate(tools):
        if not isinstance(tool, dict):
            issue("tool_object_required", str(n), "tool")
            continue
        name = tool.get("name")
        label = name if isinstance(name, str) else str(n)
        if not isinstance(name, str) or not name or len(name) > 64:
            issue("tool_name", label, "name")
        elif name in seen:
            issue("tool_duplicate", label, "name")
        seen.add(label)
        if (
            not isinstance(tool.get("description"), str)
            or not tool["description"].strip()
        ):
            issue("description_required", label, "description")
        if target == "claude" and (
            not isinstance(tool.get("title"), str) or not tool["title"].strip()
        ):
            issue("title_required", label, "title")
        annotations = tool.get("annotations", {})
        if not isinstance(annotations, dict):
            annotations = {}
            issue("annotations_object", label, "annotations")
        required = (
            ["readOnlyHint", "destructiveHint", "openWorldHint"]
            if target == "openai"
            else []
        )
        for key in required:
            if type(annotations.get(key)) is not bool:
                issue("boolean_annotation", label, "annotations." + key)
        if target == "claude" and not any(
            annotations.get(k) is True for k in ["readOnlyHint", "destructiveHint"]
        ):
            issue("annotation_required", label, "annotations")
        for field in ["inputSchema", "outputSchema"]:
            if field == "outputSchema" and field not in tool:
                continue
            schema = tool.get(field)
            if not isinstance(schema, dict) or schema.get("type") != "object":
                issue("schema_object", label, field)
                continue
            props = schema.get("properties", {})
            required_fields = schema.get("required", [])
            if (
                not isinstance(props, dict)
                or not isinstance(required_fields, list)
                or any(
                    not isinstance(k, str) or k not in props for k in required_fields
                )
            ):
                issue("schema_required_properties", label, field)
        records.append(
            {
                "tool": label,
                "host": target,
                "inventory_sha256": source_hash,
                "static_metadata_inspected": True,
                "title": tool.get("title"),
                "annotations": {
                    k: v for k, v in annotations.items() if type(v) is bool
                },
                "security_scheme_types": (
                    [
                        s.get("type")
                        for s in tool.get("securitySchemes", [])
                        if isinstance(s, dict)
                    ]
                    if isinstance(tool.get("securitySchemes", []), list)
                    else []
                ),
                "schema_review": "not_run",
                "permissions_review": "not_run",
                "side_effects_review": "not_run",
                "returned_data_privacy_review": "not_run",
                "relevant_api_documentation": [],
                "host_metadata_review": "not_run",
                "valid_input_execution": "not_run",
                "invalid_input_execution": "not_run",
                "inspector_execution": "not_run",
                "live_host_execution": "not_run",
                "case_surface_revision_evidence": [],
            }
        )
    return {
        "target": target,
        "status": "static_inventory_failed" if issues else "static_inventory_inspected",
        "inventory_sha256": source_hash,
        "tool_count": len(tools),
        "issues": issues,
        "source": (
            "https://developers.openai.com/plugins/plugin-guidelines"
            if target == "openai"
            else "https://claude.com/docs/connectors/building/review-criteria"
        ),
        "retrieved": "2026-10-13",
        "records": records,
        "live_execution_performed": False,
        "ready_to_submit": False,
        "limits": "Checks selected metadata and schema shape only; annotation truth, permissions, returned data, and host execution need separate evidence.",
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inventory", type=Path)
    p.add_argument("--target", choices=["openai", "claude"], required=True)
    p.add_argument("--output", type=Path)
    a = p.parse_args(argv)
    try:
        raw = a.inventory.read_bytes()
        data = json.loads(raw, object_pairs_hook=no_duplicates)
        report = inspect_inventory(data, a.target, hashlib.sha256(raw).hexdigest())
        text = json.dumps(report, indent=2) + "\n"
        if a.output:
            if a.output.resolve() == a.inventory.resolve():
                raise ValueError("Output must not overwrite the inventory")
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(text)
        print(text, end="")
        return 1 if report["issues"] else 0
    except (OSError, ValueError) as e:
        print(json.dumps({"status": "input_error", "message": str(e)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

