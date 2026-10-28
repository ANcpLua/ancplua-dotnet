"""Validate the portable package without installing or registering it."""
import hashlib
import json
import re
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/nami'
SKILLS = {'csharp-union-types', 'fixture-scope', 'codex-native-messaging'}


def validate(root=ROOT):
    root = Path(root).resolve()
    plugin = root / 'plugins/nami'
    errors = []
    if (root / '.agents/plugins/marketplace.json').exists():
        errors.append('Use the central ancplua-dotnet marketplace; no standalone catalog')
    manifest = json.loads((plugin / 'plugin.json').read_text())
    if manifest.get('name') != 'nami':
        errors.append('Plugin must be named nami')
    if manifest.get('$schema') != 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json':
        errors.append('Missing portable plugin schema')
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:[-+][0-9A-Za-z.-]+)?', str(manifest.get('version', ''))):
        errors.append('Invalid plugin version')
    interface = manifest.get('extensions', {}).get('com.openai', {}).get('interface', {})
    if not 0 < len(interface.get('shortDescription', '')) <= 30:
        errors.append('Listing subtitle must be 1 to 30 characters')
    for name in ('.codex', '.claude', '.codex-plugin', '.claude-plugin'):
        if (root / name).exists():
            errors.append(f'Unexpected compatibility tree: {name}')
    actual = {p.parent.name for p in (plugin / 'skills').glob('*/SKILL.md')}
    if actual != SKILLS or len(list((plugin / 'skills').rglob('SKILL.md'))) != len(SKILLS):
        errors.append(f'Expected exactly three skills, found {sorted(actual)}')
    for path in plugin.rglob('*'):
        if path.is_symlink():
            errors.append(f'Package contains a symlink: {path.relative_to(root)}')
        if any(part in {'.claude', '.codex', '.claude-plugin', '.codex-plugin', 'bin', 'obj', '__pycache__', '.venv'} for part in path.relative_to(plugin).parts):
            errors.append(f'Unexpected packaged directory: {path.relative_to(root)}')
    for name in SKILLS:
        skill = plugin / 'skills' / name
        text = (skill / 'SKILL.md').read_text()
        if not text.startswith('---\n'):
            errors.append(f'{name}: missing frontmatter')
            continue
        metadata = yaml.safe_load(text.split('---', 2)[1])
        if metadata.get('name') != name or not isinstance(metadata.get('description'), str) or not metadata['description'].strip():
            errors.append(f'{name}: invalid identity or description')
        if not (skill / 'references').is_dir():
            errors.append(f'{name}: missing references directory')
    sys.path.insert(0, str(plugin / 'skills/csharp-union-types/scripts'))
    from check_links import check
    errors.extend(check(root))
    union = plugin / 'skills/csharp-union-types'
    receipt = json.loads((union / '.sync-manifest.json').read_text())
    from sync import inventory
    if inventory(union) != receipt.get('files'):
        errors.append('Union export inventory differs from its source receipt')
    for name, expected in receipt['files'].items():
        path = (union / name).resolve()
        if not path.is_relative_to(union.resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f'Union export differs from its source receipt: {name}')
    return errors


if __name__ == '__main__':
    try:
        failures = validate()
    except (OSError, ValueError, KeyError) as error:
        failures = [str(error)]
    for failure in failures:
        print(failure)
    print(f'Package validation: {len(failures)} failure(s)')
    raise SystemExit(1 if failures else 0)
