"""Validate externally captured ChatGPT/Codex evidence without impersonating either host."""
import hashlib
import json
from datetime import datetime
from pathlib import Path, PurePosixPath

STATUSES = {'Passed', 'Failed', 'Blocked', 'Not run', 'Not applicable'}


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate capture field')
        result[key] = value
    return result


def validate_report(report, report_path, plan):
    """Return normalized rows. This verifies integrity/shape, not the observer's identity."""
    if not isinstance(report, dict) or type(report.get('schema_version')) is not int or report.get('schema_version') != 1 or report.get('report_kind') != 'product-host':
        raise ValueError('Expected schema_version 1 and report_kind product-host')
    if report.get('host') not in ('chatgpt', 'codex'):
        raise ValueError('host must be chatgpt or codex')
    allowed = {'schema_version','report_kind','host','origin','binding','package_sha256','observer','observed_at','environment','cases'}
    if set(report) - allowed:
        raise ValueError('Unknown product-host report field')
    if report['host'] not in plan.get('hosts', []):
        raise ValueError('Report host was not declared in the plan')
    if report.get('origin') not in ('observed', 'synthetic'):
        raise ValueError('origin must be observed or synthetic')
    if report.get('binding') != plan.get('binding'):
        raise ValueError('Host report binding is stale or mismatched')
    package_hash = plan.get('package_sha256') or plan.get('binding', {}).get('package_sha256')
    if not _nonempty(package_hash) or report.get('package_sha256') != package_hash:
        raise ValueError('An exact package_sha256 is required for product-host evidence')
    if len(package_hash) != 64 or any(c not in '0123456789abcdef' for c in package_hash):
        raise ValueError('Invalid package SHA-256')
    if not _nonempty(report.get('observer')) or not isinstance(report.get('environment'), dict):
        raise ValueError('Observer and environment are required')
    if not all(_nonempty(report['environment'].get(k)) for k in ('host_version', 'runner_version')):
        raise ValueError('Record host and runner versions, using unknown explicitly when unavailable')
    try:
        if datetime.fromisoformat(report['observed_at'].replace('Z', '+00:00')).tzinfo is None:
            raise ValueError('Timezone required')
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise ValueError('observed_at must be timezone-aware') from exc
    declared = {c['id']: c for c in plan.get('host_cases', [])}
    declared.update({c['id']: c for c in plan.get('cases', [])})
    rows = report.get('cases')
    if not isinstance(rows, list) or not rows:
        raise ValueError('A product-host report needs at least one case')
    accepted, seen = [], set()
    evidence_root = Path(report_path).resolve().parent
    for row in rows:
        if not isinstance(row, dict) or not _nonempty(row.get('id')) or row['id'] in seen:
            raise ValueError('Each host case needs a unique nonempty id')
        seen.add(row['id'])
        case = declared.get(row['id'])
        if case is None or row.get('status') not in STATUSES:
            raise ValueError('Unknown case or status')
        if row.get('expected') != case.get('expected'):
            raise ValueError('Case expectation differs from the source-bound plan')
        evidence = row.get('evidence')
        if not isinstance(evidence, dict) or not _nonempty(evidence.get('file')):
            raise ValueError('Every case needs a local evidence file and digest')
        rel = PurePosixPath(evidence['file'])
        if rel.is_absolute() or '..' in rel.parts or '\\' in str(rel):
            raise ValueError('Evidence paths must stay inside the report directory')
        path = evidence_root.joinpath(*rel.parts)
        if any(p.is_symlink() for p in [path, *path.parents] if p != evidence_root.parent):
            raise ValueError('Evidence must not use symlinks')
        if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError('Missing evidence or evidence exceeds 8 MiB')
        if evidence_root not in path.resolve().parents:
            raise ValueError('Evidence escaped its root')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != evidence.get('sha256'):
            raise ValueError('Evidence digest mismatch')
        try:
            capture = json.loads(data, object_pairs_hook=_unique_object)
        except (ValueError, UnicodeError) as exc:
            raise ValueError('Case capture must be structured JSON') from exc
        if not isinstance(capture, dict):
            raise ValueError('Case capture must be a JSON object')
        for key, expected in [('binding', report['binding']), ('package_sha256', package_hash), ('host', report['host']),
                              ('origin', report['origin']), ('case_id', row['id']), ('status', row['status']), ('expected', row['expected'])]:
            if capture.get(key) != expected:
                raise ValueError('Capture disagrees with its report: ' + key)
        if row['status'] == 'Passed' and (not _nonempty(capture.get('observed')) or not _nonempty(capture.get('assessment_rationale'))):
            raise ValueError('A passing case needs an observed result and observer rationale')
        if not isinstance(capture.get('tool_calls'), list) or not isinstance(capture.get('side_effects'), dict) or not {'expected','observed'} <= set(capture['side_effects']):
            raise ValueError('Capture tool calls and side effects explicitly')
        accepted.append({**row, 'tool': case.get('tool'), 'kind': case.get('kind', 'workflow'),
                         'surface': report['host'], 'engine': 'host-report', 'origin': report['origin'],
                         'observer': report['observer'], 'verification': 'External observer claim; file integrity checked',
                         'server_confirmation': 'Not run'})
    return accepted
